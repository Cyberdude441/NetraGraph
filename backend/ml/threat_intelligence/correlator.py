"""Deterministic correlation engine linking case entities to external threat intelligence."""
from __future__ import annotations

import ipaddress
import logging
from typing import Any, Dict, List, Optional, Tuple

try:
    from services.investigation_graph import investigation_graph_service
except ImportError:
    from ...services.investigation_graph import investigation_graph_service

from .config import (
    IOCReputation,
    IOCType,
    MatchMethod,
    ResolutionStatus,
    ReviewStatus,
)
from .models import CandidateCorrelation, ThreatIndicator
from .normalization import (
    canonicalize_domain,
    canonicalize_ipv4,
    canonicalize_ipv6,
    mask_sensitive_identifier,
    normalize_indicator,
)
from .provenance import compute_correlation_id
from .scoring import ThreatScoringEngine

logger = logging.getLogger("ThreatIntelligenceCorrelator")


class EntityCorrelator:
    """Matches case entities against indexed external threat indicators."""

    def __init__(self, scoring_engine: Optional[ThreatScoringEngine] = None):
        self.scoring_engine = scoring_engine or ThreatScoringEngine()

    def correlate_entity(
        self,
        case_id: str,
        entity_dict: Dict[str, Any],
        indicator_index: Dict[str, List[ThreatIndicator]],
        reference_time: Optional[float] = None,
    ) -> List[CandidateCorrelation]:
        """
        Correlates a single case entity dictionary against indexed threat indicators.
        
        CRITICAL ARCHITECTURAL INVARIANTS:
        1. Reuses investigation_graph_service.generate_entity_id() for 100% ID compatibility.
        2. Never automatically merges identities; emits CandidateCorrelation in REVIEW_REQUIRED state.
        3. Fuzzy and person alias matches are strictly marked UNRESOLVED with capped confidence.
        """
        raw_val = str(entity_dict.get("value") or entity_dict.get("identifier") or entity_dict.get("name") or "").strip()
        ent_type = str(entity_dict.get("entity_type") or entity_dict.get("type") or "Unknown").strip()
        if not raw_val:
            return []

        # Canonical entity ID from official service
        canonical_ent_id = entity_dict.get("canonical_entity_id") or investigation_graph_service.generate_entity_id(ent_type, raw_val)

        correlations: List[CandidateCorrelation] = []
        norm_type = ent_type.lower()

        # 1. IP Address matching (Exact & CIDR subnet)
        if norm_type in ("ip", "ipaddress", "ipv4", "ipv6"):
            correlations.extend(self._match_ip(case_id, canonical_ent_id, ent_type, raw_val, indicator_index, reference_time))

        # 2. Domain matching (Exact & Hierarchy)
        elif norm_type in ("domain", "fqdn", "hostname"):
            correlations.extend(self._match_domain(case_id, canonical_ent_id, ent_type, raw_val, indicator_index, reference_time))

        # 3. Hash matching (Exact)
        elif norm_type in ("hash", "filehash", "sha256", "md5"):
            correlations.extend(self._match_hash(case_id, canonical_ent_id, ent_type, raw_val, indicator_index, reference_time))

        # 4. Phone matching (Masked PII)
        elif norm_type in ("phone", "phonenumber", "mobile"):
            correlations.extend(self._match_phone(case_id, canonical_ent_id, ent_type, raw_val, indicator_index, reference_time))

        # 5. Bank Account matching (Masked PII)
        elif norm_type in ("bank", "bankaccount"):
            correlations.extend(self._match_bank(case_id, canonical_ent_id, ent_type, raw_val, indicator_index, reference_time))

        # 6. Person / Threat Actor Alias matching (Strict UNRESOLVED gate)
        elif norm_type in ("person", "threat_actor", "actor", "alias"):
            correlations.extend(self._match_person_alias(case_id, canonical_ent_id, ent_type, raw_val, indicator_index, reference_time))

        return correlations

    def _create_candidate(
        self,
        case_id: str,
        entity_id: str,
        entity_type: str,
        entity_value: str,
        indicator: ThreatIndicator,
        match_method: MatchMethod,
        resolution_status: ResolutionStatus,
        reference_time: Optional[float],
        explanation: str,
    ) -> CandidateCorrelation:
        """Constructs CandidateCorrelation with complete multi-dimensional confidence."""
        profile, effective_relevance, is_stale, stale_warning = self.scoring_engine.evaluate_profile(
            source_reliability=indicator.confidence_profile.source_reliability,
            content_confidence=indicator.confidence_profile.content_confidence,
            extraction_method="CTI_CORRELATOR",
            match_method=match_method,
            last_seen_timestamp=indicator.last_seen_timestamp,
            reputation=indicator.reputation,
            reference_time=reference_time,
        )

        cor_id = compute_correlation_id(case_id, entity_id, indicator.indicator_id, indicator.provenance_id)

        return CandidateCorrelation(
            correlation_id=cor_id,
            case_id=case_id,
            entity_id=entity_id,
            entity_type=entity_type,
            entity_value=entity_value,
            indicator_id=indicator.indicator_id,
            indicator_value=indicator.indicator_value,
            ioc_type=indicator.ioc_type,
            match_method=match_method,
            entity_match_confidence=profile.entity_match_confidence or 0.85,
            resolution_status=resolution_status,
            confidence_profile=profile,
            effective_threat_relevance=effective_relevance,
            provenance_id=indicator.provenance_id,
            explanation=explanation,
            review_status=ReviewStatus.REVIEW_REQUIRED,
            is_stale=is_stale,
            stale_warning=stale_warning,
            has_conflict=indicator.has_conflict,
        )

    def _match_ip(
        self,
        case_id: str,
        ent_id: str,
        ent_type: str,
        raw_val: str,
        indicator_index: Dict[str, List[ThreatIndicator]],
        ref_time: Optional[float],
    ) -> List[CandidateCorrelation]:
        results: List[CandidateCorrelation] = []
        try:
            canon_ip = canonicalize_ipv4(raw_val)
        except Exception:
            try:
                canon_ip = canonicalize_ipv6(raw_val)
            except Exception:
                return []

        # Exact match
        if canon_ip in indicator_index:
            for ind in indicator_index[canon_ip]:
                results.append(
                    self._create_candidate(
                        case_id=case_id,
                        entity_id=ent_id,
                        entity_type=ent_type,
                        entity_value=canon_ip,
                        indicator=ind,
                        match_method=MatchMethod.EXACT,
                        resolution_status=ResolutionStatus.VERIFIED,
                        reference_time=ref_time,
                        explanation=f"Exact IP match with {ind.source_name} indicator ({ind.category}).",
                    )
                )

        # CIDR Subnet match: iterate over indexed indicators that define subnets
        try:
            ip_obj = ipaddress.ip_address(canon_ip)
            for key, indicators in indicator_index.items():
                if '/' in key:
                    try:
                        net_obj = ipaddress.ip_network(key, strict=False)
                        if ip_obj in net_obj:
                            for ind in indicators:
                                results.append(
                                    self._create_candidate(
                                        case_id=case_id,
                                        entity_id=ent_id,
                                        entity_type=ent_type,
                                        entity_value=canon_ip,
                                        indicator=ind,
                                        match_method=MatchMethod.CIDR_SUBNET,
                                        resolution_status=ResolutionStatus.PROBABLE,
                                        reference_time=ref_time,
                                        explanation=f"IP falls within malicious subnet {key} ({ind.source_name}).",
                                    )
                                )
                    except ValueError:
                        continue
        except ValueError:
            pass

        return results

    def _match_domain(
        self,
        case_id: str,
        ent_id: str,
        ent_type: str,
        raw_val: str,
        indicator_index: Dict[str, List[ThreatIndicator]],
        ref_time: Optional[float],
    ) -> List[CandidateCorrelation]:
        results: List[CandidateCorrelation] = []
        try:
            canon_dom = canonicalize_domain(raw_val)
        except Exception:
            return []

        # Exact match
        if canon_dom in indicator_index:
            for ind in indicator_index[canon_dom]:
                results.append(
                    self._create_candidate(
                        case_id=case_id,
                        entity_id=ent_id,
                        entity_type=ent_type,
                        entity_value=canon_dom,
                        indicator=ind,
                        match_method=MatchMethod.EXACT,
                        resolution_status=ResolutionStatus.VERIFIED,
                        reference_time=ref_time,
                        explanation=f"Exact domain match with {ind.source_name} indicator ({ind.category}).",
                    )
                )

        # Domain hierarchy match (subdomain check)
        parts = canon_dom.split('.')
        if len(parts) > 2:
            for i in range(1, len(parts) - 1):
                parent_dom = '.'.join(parts[i:])
                if parent_dom in indicator_index:
                    for ind in indicator_index[parent_dom]:
                        results.append(
                            self._create_candidate(
                                case_id=case_id,
                                entity_id=ent_id,
                                entity_type=ent_type,
                                entity_value=canon_dom,
                                indicator=ind,
                                match_method=MatchMethod.DOMAIN_HIERARCHY,
                                resolution_status=ResolutionStatus.PROBABLE,
                                reference_time=ref_time,
                                explanation=f"Subdomain of malicious infrastructure '{parent_dom}' ({ind.source_name}).",
                            )
                        )

        return results

    def _match_hash(
        self,
        case_id: str,
        ent_id: str,
        ent_type: str,
        raw_val: str,
        indicator_index: Dict[str, List[ThreatIndicator]],
        ref_time: Optional[float],
    ) -> List[CandidateCorrelation]:
        results: List[CandidateCorrelation] = []
        canon_hash = raw_val.strip().lower()
        if canon_hash in indicator_index:
            for ind in indicator_index[canon_hash]:
                results.append(
                    self._create_candidate(
                        case_id=case_id,
                        entity_id=ent_id,
                        entity_type=ent_type,
                        entity_value=canon_hash,
                        indicator=ind,
                        match_method=MatchMethod.HASH_EXACT,
                        resolution_status=ResolutionStatus.VERIFIED,
                        reference_time=ref_time,
                        explanation=f"Exact cryptographic hash match with malware payload ({ind.source_name}).",
                    )
                )
        return results

    def _match_phone(
        self,
        case_id: str,
        ent_id: str,
        ent_type: str,
        raw_val: str,
        indicator_index: Dict[str, List[ThreatIndicator]],
        ref_time: Optional[float],
    ) -> List[CandidateCorrelation]:
        results: List[CandidateCorrelation] = []
        masked, digest = mask_sensitive_identifier(raw_val, "phone")
        if digest in indicator_index:
            for ind in indicator_index[digest]:
                results.append(
                    self._create_candidate(
                        case_id=case_id,
                        entity_id=ent_id,
                        entity_type=ent_type,
                        entity_value=masked,
                        indicator=ind,
                        match_method=MatchMethod.PHONE_E164,
                        resolution_status=ResolutionStatus.PROBABLE,
                        reference_time=ref_time,
                        explanation=f"Phone matched reported dialer/scam infrastructure ({ind.source_name}).",
                    )
                )
        return results

    def _match_bank(
        self,
        case_id: str,
        ent_id: str,
        ent_type: str,
        raw_val: str,
        indicator_index: Dict[str, List[ThreatIndicator]],
        ref_time: Optional[float],
    ) -> List[CandidateCorrelation]:
        results: List[CandidateCorrelation] = []
        masked, digest = mask_sensitive_identifier(raw_val, "bank")
        if digest in indicator_index:
            for ind in indicator_index[digest]:
                results.append(
                    self._create_candidate(
                        case_id=case_id,
                        entity_id=ent_id,
                        entity_type=ent_type,
                        entity_value=masked,
                        indicator=ind,
                        match_method=MatchMethod.BANK_EXACT,
                        resolution_status=ResolutionStatus.PROBABLE,
                        reference_time=ref_time,
                        explanation=f"Account matched flagged mule registry ({ind.source_name}).",
                    )
                )
        return results

    def _match_person_alias(
        self,
        case_id: str,
        ent_id: str,
        ent_type: str,
        raw_val: str,
        indicator_index: Dict[str, List[ThreatIndicator]],
        ref_time: Optional[float],
    ) -> List[CandidateCorrelation]:
        results: List[CandidateCorrelation] = []
        norm_name = raw_val.strip().lower()
        if norm_name in indicator_index:
            for ind in indicator_index[norm_name]:
                results.append(
                    self._create_candidate(
                        case_id=case_id,
                        entity_id=ent_id,
                        entity_type=ent_type,
                        entity_value=raw_val,
                        indicator=ind,
                        match_method=MatchMethod.FUZZY_ALIAS,
                        resolution_status=ResolutionStatus.UNRESOLVED,  # Mandatory human review
                        reference_time=ref_time,
                        explanation=(
                            f"Heuristic name match against actor alias '{ind.indicator_value}' ({ind.source_name}). "
                            f"Requires explicit investigator confirmation."
                        ),
                    )
                )
        return results
