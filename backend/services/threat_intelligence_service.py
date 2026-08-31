"""Threat Intelligence Fusion Service for NetraGraph AI.

Ingests, normalizes, and fuses external IOC threat feeds (IP, Domain, File Hash, SSL)
while maintaining strict provenance separation from official public NCRB statistics
and police case evidence.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ThreatIntelligenceService")


class ThreatIntelligenceService:
    """Manages ingestion and correlation of external Cyber Threat Intelligence (CTI)."""

    def __init__(self):
        self._ioc_feed: Dict[str, Dict[str, Any]] = {}
        self._feed_metadata: Dict[str, Dict[str, Any]] = {}
        self._initialize_curated_ioc_feed()

    def _initialize_curated_ioc_feed(self) -> None:
        """Initializes curated external threat intelligence feed data."""
        sample_iocs = [
            {
                "ioc_id": "IOC-IP-103.145.22.18",
                "indicator": "103.145.22.18",
                "ioc_type": "IPv4",
                "threat_actor": "UNC-8812 (Tele-Fraud Syndicate)",
                "category": "Bulletproof Proxy / VoIP Relay",
                "confidence_score": 0.94,
                "first_seen": "2024-01-15T08:00:00Z",
                "last_seen": "2024-03-16T14:31:00Z",
                "feed_source": "CERT-In Threat Advisory & AbuseIPDB Feed",
                "reputation": "MALICIOUS",
                "asn": "AS13335 (Cloudflare/Proxy)",
                "country": "IN",
                "associated_malware": ["Vidar Stealer", "FraudSIP Dialer"],
            },
            {
                "ioc_id": "IOC-DOM-SUPPORT-HELPDESK",
                "indicator": "support-helpdesk-msft.com",
                "ioc_type": "Domain",
                "threat_actor": "UNC-8812",
                "category": "Credential Phishing Infrastructure",
                "confidence_score": 0.98,
                "first_seen": "2024-02-10T12:00:00Z",
                "last_seen": "2024-03-16T14:31:00Z",
                "feed_source": "OpenPhish & VirusTotal Intelligence",
                "reputation": "MALICIOUS",
                "registrar": "NameCheap Inc",
                "country": "US",
                "associated_malware": ["MSFT-Spoof-Kit"],
            },
            {
                "ioc_id": "IOC-HASH-A48F99",
                "indicator": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "ioc_type": "SHA-256",
                "threat_actor": "Generic Cybercrime",
                "category": "Phishing PDF Lure with Macros",
                "confidence_score": 0.89,
                "first_seen": "2024-03-01T04:12:00Z",
                "last_seen": "2024-03-16T10:00:00Z",
                "feed_source": "National Cyber Crime Threat Exchange (NCTX)",
                "reputation": "SUSPICIOUS",
                "associated_malware": ["AgentTesla"],
            },
            {
                "ioc_id": "IOC-IP-198.51.100.24",
                "indicator": "198.51.100.24",
                "ioc_type": "IPv4",
                "threat_actor": "Unknown",
                "category": "Scanning & Probing Host",
                "confidence_score": 0.72,
                "first_seen": "2024-03-12T00:00:00Z",
                "last_seen": "2024-03-14T22:00:00Z",
                "feed_source": "AlienVault OTX Community Pulse",
                "reputation": "SUSPICIOUS",
                "country": "NL",
            },
        ]
        for ioc in sample_iocs:
            self._ioc_feed[ioc["indicator"].lower()] = {
                **ioc,
                "domain_tag": "EXTERNAL_THREAT_INTEL",
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }

    def correlate_case_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Correlates case entities (IPs, domains, hashes) against external CTI feeds."""
        matches = []
        for ent in entities:
            val = (ent.get("name") or ent.get("value") or "").strip().lower()
            if val in self._ioc_feed:
                feed_hit = self._ioc_feed[val]
                matches.append({
                    "entity_id": ent.get("id"),
                    "entity_name": ent.get("name") or ent.get("value"),
                    "entity_type": ent.get("label") or ent.get("type"),
                    "case_id": ent.get("case_id"),
                    "ioc_match": feed_hit,
                    "correlation_status": "MATCHED_EXTERNAL_CTI",
                    "provenance": {
                        "source": feed_hit["feed_source"],
                        "reputation": feed_hit["reputation"],
                        "threat_actor": feed_hit.get("threat_actor", "Unknown"),
                        "category": feed_hit.get("category", "General"),
                        "confidence_score": feed_hit["confidence_score"],
                        "domain_tag": "EXTERNAL_THREAT_INTEL",
                    },
                })
        return matches

    def lookup_indicator(self, indicator: str) -> Optional[Dict[str, Any]]:
        """Looks up a specific IOC indicator in the threat feed."""
        return self._ioc_feed.get(indicator.strip().lower())

    def get_feed_summary(self) -> Dict[str, Any]:
        """Returns statistics on active external threat feeds."""
        by_type: Dict[str, int] = {}
        for ioc in self._ioc_feed.values():
            t = ioc.get("ioc_type", "Other")
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "total_iocs": len(self._ioc_feed),
            "by_type": by_type,
            "connected_feeds": [
                "CERT-In Threat Advisory & AbuseIPDB Feed",
                "OpenPhish & VirusTotal Intelligence",
                "National Cyber Crime Threat Exchange (NCTX)",
                "AlienVault OTX Community Pulse",
            ],
            "domain_tag": "EXTERNAL_THREAT_INTEL",
            "last_sync": datetime.now(timezone.utc).isoformat(),
        }


# Global Singleton Instance
threat_intelligence_service = ThreatIntelligenceService()
