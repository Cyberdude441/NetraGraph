"""
Domain Profiler Engine for NetraGraph Model Selection V2.
Inspects unlabeled input schemas, feature statistics, and data signatures to classify security domain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

try:
    from training.model_selection_v2.config import (
        DOMAIN_PROFILES,
        MIN_DOMAIN_CONFIDENCE_THRESHOLD,
        RepresentationType,
        SecurityDomain,
    )
except ImportError:
    from config import (
        DOMAIN_PROFILES,
        MIN_DOMAIN_CONFIDENCE_THRESHOLD,
        RepresentationType,
        SecurityDomain,
    )


@dataclass
class DomainProfileResult:
    domain: SecurityDomain
    domain_probabilities: Dict[str, float]
    recommended_representation: RepresentationType
    confidence: float
    evidence: List[str]
    is_ambiguous: bool
    feature_count: int
    matched_signatures: List[str]


class DomainProfiler:
    """
    Infers cybersecurity domain and recommends optimal representation without labels.
    """

    FLOW_KEYWORDS = {
        "flow_duration", "total_fwd_packets", "total_backward_packets", "fwd_packet_length_max",
        "bwd_packet_length_min", "flow_iat_mean", "flow_iat_std", "fin_flag_count", "syn_flag_count",
        "rst_flag_count", "psh_flag_count", "ack_flag_count", "init_win_bytes_forward",
        "subflow_fwd_packets", "packet_count", "byte_count", "duration", "src_port", "dst_port",
    }

    DDOS_KEYWORDS = {
        "protocol", "reflection", "amplification", "inbound_burst", "udp_flood", "syn_flood",
        "dns_amp", "ntp_amp", "mss", "window_size", "flow_rate", "packet_rate",
    }

    URL_KEYWORDS = {
        "url", "domain", "url_length", "domain_length", "subdomain_count", "has_ip", "has_https",
        "has_at_symbol", "num_hyphens", "num_slashes", "tld_in_path", "domain_entropy",
    }

    MALWARE_KEYWORDS = {
        "imphash", "ssdeep", "tlsh", "reporter", "clamav", "vtpercent", "file_type_guess",
        "mime_type", "pe_sections", "dll_imports", "entropy", "executable_type", "antivirus_tags",
    }

    def profile_dataset(self, X: Union[pd.DataFrame, Dict[str, Any], np.ndarray]) -> DomainProfileResult:
        """
        Inspect input data and calculate domain classification probabilities.
        """
        evidence: List[str] = []
        matched_sigs: List[str] = []

        if isinstance(X, dict):
            df = pd.DataFrame([X])
        elif isinstance(X, np.ndarray):
            df = pd.DataFrame(X, columns=[f"feat_{i}" for i in range(X.shape[1])])
        elif isinstance(X, pd.DataFrame):
            df = X
        else:
            raise ValueError(f"Unsupported input type: {type(X)}")

        cols_lower = [str(c).lower().strip() for c in df.columns]
        n_features = len(cols_lower)

        # 1. Feature Name Match Scores
        flow_matches = sum(1 for c in cols_lower if any(kw in c for kw in self.FLOW_KEYWORDS))
        ddos_matches = sum(1 for c in cols_lower if any(kw in c for kw in self.DDOS_KEYWORDS))
        url_matches = sum(1 for c in cols_lower if any(kw in c for kw in self.URL_KEYWORDS))
        malware_matches = sum(1 for c in cols_lower if any(kw in c for kw in self.MALWARE_KEYWORDS))

        # 2. Data Type Inspection
        obj_cols = df.select_dtypes(include=["object", "string"]).columns
        num_cols = df.select_dtypes(include=[np.number]).columns
        obj_ratio = len(obj_cols) / max(1, n_features)
        num_ratio = len(num_cols) / max(1, n_features)

        # 3. Hash Pattern Inspection
        has_imphash = any("imphash" in c for c in cols_lower)
        has_ssdeep = any("ssdeep" in c for c in cols_lower)
        has_tlsh = any("tlsh" in c for c in cols_lower)
        has_vt = any("vtpercent" in c or "virustotal" in c for c in cols_lower)

        # 4. Domain Probability Calculation
        scores: Dict[str, float] = {
            SecurityDomain.NETWORK_INTRUSION.value: 0.1,
            SecurityDomain.DDOS_PROTECTION.value: 0.1,
            SecurityDomain.URL_PHISHING.value: 0.1,
            SecurityDomain.MALWARE_ATTRIBUTION.value: 0.1,
        }

        # Malware Scoring
        if malware_matches > 0 or has_imphash or has_ssdeep or has_tlsh or has_vt:
            malware_boost = (malware_matches * 2.0) + (3.0 if has_imphash else 0) + (3.0 if has_ssdeep else 0) + (2.0 if has_vt else 0)
            scores[SecurityDomain.MALWARE_ATTRIBUTION.value] += malware_boost
            evidence.append(f"Detected {malware_matches} malware metadata/hash columns")
            if has_imphash or has_ssdeep or has_tlsh:
                matched_sigs.append("fuzzy_structural_hash_signature")

        # URL Scoring
        if url_matches > 0:
            scores[SecurityDomain.URL_PHISHING.value] += (url_matches * 3.0)
            evidence.append(f"Detected {url_matches} URL/lexical phishing columns")
            matched_sigs.append("url_lexical_signature")

        # DDoS Scoring
        if ddos_matches > 0:
            scores[SecurityDomain.DDOS_PROTECTION.value] += (ddos_matches * 2.5)
            evidence.append(f"Detected {ddos_matches} DDoS/protocol columns")
            matched_sigs.append("ddos_protocol_signature")

        # Network Flow Scoring
        if flow_matches > 0:
            scores[SecurityDomain.NETWORK_INTRUSION.value] += (flow_matches * 2.0)
            evidence.append(f"Detected numerical flow matrix with {flow_matches} network indicators")
            matched_sigs.append("network_flow_matrix_signature")
        elif num_ratio >= 0.85 and n_features >= 8 and malware_matches == 0 and url_matches == 0:
            scores[SecurityDomain.NETWORK_INTRUSION.value] += 2.0
            evidence.append("Detected high-dimensional numerical feature matrix")
            matched_sigs.append("network_flow_matrix_signature")

        # Normalize to probabilities (Softmax)
        raw_vals = np.array(list(scores.values()))
        exp_vals = np.exp(raw_vals - np.max(raw_vals))
        probs_vec = exp_vals / np.sum(exp_vals)
        domain_keys = list(scores.keys())
        prob_dict = {domain_keys[i]: round(float(probs_vec[i]), 4) for i in range(len(domain_keys))}

        best_domain_str = max(prob_dict, key=prob_dict.get)
        best_prob = prob_dict[best_domain_str]

        # Ambiguity check
        is_ambiguous = (best_prob < MIN_DOMAIN_CONFIDENCE_THRESHOLD)

        if is_ambiguous:
            detected_domain = SecurityDomain.UNKNOWN_DOMAIN
            rec_repr = RepresentationType.FALLBACK_TABULAR_V1
            evidence.append(f"Confidence {best_prob:.2f} below safety threshold {MIN_DOMAIN_CONFIDENCE_THRESHOLD}")
        else:
            detected_domain = SecurityDomain(best_domain_str)
            rec_repr = DOMAIN_PROFILES[detected_domain]["preferred_representation"]
            evidence.append(f"High-confidence match for {DOMAIN_PROFILES[detected_domain]['domain_name']}")

        return DomainProfileResult(
            domain=detected_domain,
            domain_probabilities=prob_dict,
            recommended_representation=rec_repr,
            confidence=round(best_prob, 4),
            evidence=evidence,
            is_ambiguous=is_ambiguous,
            feature_count=n_features,
            matched_signatures=matched_sigs,
        )


def profile_dataset(X: Union[pd.DataFrame, Dict[str, Any], np.ndarray]) -> DomainProfileResult:
    """Convenience helper for domain profiling."""
    profiler = DomainProfiler()
    return profiler.profile_dataset(X)
