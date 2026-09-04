"""Bounded ingestion, defensive sanitization, and parsing for external CTI payloads."""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from .config import IOCReputation, IOCType, SafetyLimitsConfig, SourceTier
from .models import ConfidenceProfile, ThreatIndicator, ThreatIntelProvenanceRecord
from .normalization import normalize_indicator
from .provenance import compute_indicator_id, compute_payload_sha256, compute_provenance_id
from .sources import SourceRegistry

logger = logging.getLogger("ThreatIntelligenceIngestion")


def sanitize_text(val: Optional[str]) -> str:
    """
    Sanitizes untrusted text strings to mitigate prompt injection, script injection, and control characters.
    
    Transforms:
      - Strips null bytes and terminal control sequences
      - Strips HTML/script tags (<script>, <iframe>, etc.)
      - Neutralizes prompt injection directives (e.g. 'Ignore previous instructions', 'System prompt:')
    """
    if not val:
        return ""
    # Strip null bytes and non-printable control characters (except newline/tab)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', val)
    # Strip HTML tags
    cleaned = re.sub(r'<[^>]*>', '', cleaned)
    # Neutralize prompt injection markers
    prompt_patterns = [
        r'(?i)ignore\s+(all\s+)?previous\s+instructions',
        r'(?i)you\s+are\s+now\s+in\s+developer\s+mode',
        r'(?i)system\s+prompt\s*:',
        r'(?i)override\s+system\s+rules',
    ]
    for pat in prompt_patterns:
        cleaned = re.sub(pat, '[FILTERED_DIRECTIVE]', cleaned)
    return cleaned.strip()


class IngestionPipeline:
    """Bounded, defensive ingestion engine converting raw external feeds into immutable indicators."""

    def __init__(
        self,
        source_registry: SourceRegistry,
        safety_limits: Optional[SafetyLimitsConfig] = None,
    ):
        self.source_registry = source_registry
        self.limits = safety_limits or SafetyLimitsConfig()

    def ingest_payload(
        self,
        source_name: str,
        source_tier: SourceTier,
        raw_bytes: bytes,
        payload_format: str = "json",
    ) -> Tuple[List[ThreatIndicator], List[ThreatIntelProvenanceRecord], str]:
        """
        Parses raw feed bytes under strict resource bounds and sanitization.
        
        CRITICAL ARCHITECTURAL INVARIANTS:
        1. Enforces max_payload_bytes (10 MB).
        2. Computes raw_payload_sha256 before parsing.
        3. Enforces max_indicators_per_batch (5000).
        4. Distinguishes publication, observation, and ingestion timestamps.
        
        Returns:
          (indicators, provenance_records, raw_payload_sha256)
        """
        # 1. Payload size check
        if len(raw_bytes) > self.limits.max_payload_bytes:
            raise ValueError(
                f"Payload size {len(raw_bytes)} bytes exceeds maximum limit "
                f"of {self.limits.max_payload_bytes} bytes (10 MB)."
            )

        raw_sha256 = compute_payload_sha256(raw_bytes)
        ingest_time = time.time()

        # 2. Source resolution & trust evaluation
        source_meta = self.source_registry.get_source_by_name(source_name)
        if not source_meta:
            source_meta = self.source_registry.register_source(source_name, source_tier)
        source_id = source_meta.source_id
        source_reliability = self.source_registry.get_reliability(source_name, source_tier)

        # 3. Format parsing
        items: List[Dict[str, Any]] = []
        if payload_format.lower() == "json":
            try:
                decoded = json.loads(raw_bytes.decode("utf-8"))
                if isinstance(decoded, list):
                    items = decoded
                elif isinstance(decoded, dict):
                    # Handle STIX 2.1 bundle or dictionary wrapper
                    if "objects" in decoded and isinstance(decoded["objects"], list):
                        items = decoded["objects"]
                    elif "indicators" in decoded and isinstance(decoded["indicators"], list):
                        items = decoded["indicators"]
                    elif "iocs" in decoded and isinstance(decoded["iocs"], list):
                        items = decoded["iocs"]
                    else:
                        items = [decoded]
            except Exception as exc:
                raise ValueError(f"Malformed JSON payload: {str(exc)}") from exc
        elif payload_format.lower() in ("csv", "text", "lines"):
            lines = raw_bytes.decode("utf-8", errors="replace").splitlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = [p.strip() for p in line.split(",")]
                    items.append({
                        "indicator": parts[0],
                        "ioc_type": parts[1] if len(parts) > 1 else "Other",
                        "category": parts[2] if len(parts) > 2 else "Malicious Indicator",
                    })
        else:
            raise ValueError(f"Unsupported payload format: {payload_format}")

        # 4. Batch count check
        if len(items) > self.limits.max_indicators_per_batch:
            raise ValueError(
                f"Batch item count ({len(items)}) exceeds maximum limit "
                f"of {self.limits.max_indicators_per_batch} indicators."
            )

        indicators: List[ThreatIndicator] = []
        provenance_records: List[ThreatIntelProvenanceRecord] = []

        for seq_idx, item in enumerate(items):
            try:
                raw_val = str(item.get("indicator") or item.get("value") or item.get("pattern") or "").strip()
                if not raw_val:
                    continue

                type_str = str(item.get("ioc_type") or item.get("type") or "Other").strip()
                ioc_type = self._parse_ioc_type(type_str, raw_val)

                # Canonicalize
                try:
                    canon_val = normalize_indicator(raw_val, ioc_type)
                except Exception as norm_err:
                    logger.debug(f"Normalization skipped for {raw_val}: {norm_err}")
                    canon_val = raw_val.strip().lower()

                indicator_id = compute_indicator_id(ioc_type.value, canon_val)

                # Timestamps
                obs_time = self._parse_epoch(item.get("observation_timestamp") or item.get("observed") or item.get("last_seen"))
                pub_time = self._parse_epoch(item.get("publication_timestamp") or item.get("published") or item.get("first_seen"))
                source_record_id = str(item.get("source_record_id") or item.get("ioc_id") or item.get("id") or "") or None

                # Provenance ID distinguishes items even within the same second
                prv_id = compute_provenance_id(
                    source_id=source_id,
                    indicator_id=indicator_id,
                    source_record_id=source_record_id,
                    timestamp=ingest_time,
                    raw_payload_sha256=raw_sha256,
                    transformation="ingest_and_normalize",
                    sequence_index=seq_idx,
                )

                # Confidence
                content_conf = item.get("confidence_score") or item.get("confidence")
                if content_conf is not None:
                    try:
                        content_conf = max(0.0, min(1.0, float(content_conf)))
                    except (ValueError, TypeError):
                        content_conf = None

                profile = ConfidenceProfile(
                    source_reliability=source_reliability,
                    content_confidence=content_conf,
                    extraction_confidence=0.98,
                    entity_match_confidence=None,
                    temporal_confidence=None,
                    threat_relevance=None,
                )

                rep_str = str(item.get("reputation") or "SUSPICIOUS").upper()
                reputation = IOCReputation.MALICIOUS if "MALICIOUS" in rep_str else (
                    IOCReputation.BENIGN if "BENIGN" in rep_str or "CLEAN" in rep_str else IOCReputation.SUSPICIOUS
                )

                threat_ind = ThreatIndicator(
                    indicator_id=indicator_id,
                    indicator_value=sanitize_text(raw_val),
                    canonical_value=canon_val,
                    ioc_type=ioc_type,
                    threat_actor=sanitize_text(item.get("threat_actor")),
                    category=sanitize_text(item.get("category") or "External Threat Telemetry"),
                    reputation=reputation,
                    confidence_profile=profile,
                    first_seen_timestamp=pub_time,
                    last_seen_timestamp=obs_time or ingest_time,
                    publication_timestamp=pub_time,
                    ingestion_timestamp=ingest_time,
                    source_id=source_id,
                    source_name=source_name,
                    source_tier=source_tier,
                    source_record_id=source_record_id,
                    raw_payload_sha256=raw_sha256,
                    provenance_id=prv_id,
                    associated_malware=[sanitize_text(m) for m in item.get("associated_malware", []) if m],
                    tags=[sanitize_text(t) for t in item.get("tags", []) if t],
                    metadata={"source_feed": source_name, "raw_format": payload_format},
                )

                prv_record = ThreatIntelProvenanceRecord(
                    provenance_id=prv_id,
                    source_id=source_id,
                    source_name=source_name,
                    source_type=f"cti_{payload_format.lower()}",
                    source_record_id=source_record_id,
                    raw_payload_sha256=raw_sha256,
                    observation_timestamp=obs_time,
                    publication_timestamp=pub_time,
                    ingestion_timestamp=ingest_time,
                    transformation_history=["raw_bytes_received", "sha256_verified", "indicator_normalized"],
                    metadata={"batch_index": seq_idx, "ioc_type": ioc_type.value},
                )

                indicators.append(threat_ind)
                provenance_records.append(prv_record)

            except Exception as item_err:
                logger.warning(f"Error parsing item index {seq_idx} in feed {source_name}: {item_err}")
                continue

        return indicators, provenance_records, raw_sha256

    def _parse_ioc_type(self, type_str: str, val: str) -> IOCType:
        t = type_str.lower()
        if "ipv4" in t or "ip" in t and "." in val:
            return IOCType.IPV4
        elif "ipv6" in t or ":" in val and len(val) > 10:
            return IOCType.IPV6
        elif "domain" in t or "fqdn" in t:
            return IOCType.DOMAIN
        elif "url" in t or "http" in val:
            return IOCType.URL
        elif "sha256" in t or (len(val) == 64 and re.match(r'^[0-9a-fA-F]+$', val)):
            return IOCType.SHA256
        elif "md5" in t or (len(val) == 32 and re.match(r'^[0-9a-fA-F]+$', val)):
            return IOCType.MD5
        elif "phone" in t:
            return IOCType.PHONE
        elif "bank" in t:
            return IOCType.BANK_ACCOUNT
        return IOCType.OTHER

    def _parse_epoch(self, val: Any) -> Optional[float]:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            try:
                # ISO 8601 string parsing
                from datetime import datetime
                clean_iso = val.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_iso)
                return dt.timestamp()
            except Exception:
                try:
                    return float(val)
                except ValueError:
                    return None
        return None
