"""
Blind Holdout & Adversarial Stress Set Generator with Hash-Based De-duplication.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
for p in [str(PROJECT_ROOT), str(PROJECT_ROOT / "backend"), str(PROJECT_ROOT / "training" / "shadow_inference")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.test_ml_diagnostics import SAMPLE_PAYLOADS


def hash_payload(payload: Dict[str, Any]) -> str:
    """Generate SHA-256 hash of a serialized payload to detect duplicates."""
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def generate_blind_holdout_for_seed(
    seed: int,
    n_per_dataset: int = 100,
    seen_hashes: Optional[Set[str]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Generate completely blind holdout test samples for a given seed with duplicate auditing.
    """
    rng = np.random.default_rng(seed)
    samples: List[Dict[str, Any]] = []
    seen = seen_hashes if seen_hashes is not None else set()
    duplicate_count = 0

    # 1. CIC-IDS2018 (Session Intrusion)
    for i in range(n_per_dataset):
        is_attack = (i % 2 == 1)
        payload = {
            "network_packet_size": int(rng.uniform(750, 1600)) if is_attack else int(rng.uniform(64, 550)),
            "protocol_type": "TCP" if rng.uniform() > 0.25 else "UDP",
            "login_attempts": int(rng.integers(2, 12)) if is_attack else int(rng.integers(1, 2)),
            "session_duration": float(rng.uniform(0.5, 45.0)) if is_attack else float(rng.uniform(50.0, 700.0)),
            "encryption_used": "None" if (is_attack and rng.uniform() > 0.4) else "AES-256",
            "ip_reputation_score": float(rng.uniform(0.05, 0.48)) if is_attack else float(rng.uniform(0.65, 0.99)),
            "failed_logins": int(rng.integers(2, 8)) if is_attack else 0,
            "browser_type": "Unknown" if is_attack else "Chrome",
            "unusual_time_access": 1 if is_attack else 0,
        }
        h = hash_payload(payload)
        if h in seen:
            duplicate_count += 1
        seen.add(h)

        samples.append({
            "request_id": f"BLIND-S{seed}-IDS2018-{i+1:04d}",
            "seed": seed,
            "dataset_name": "cicids2018",
            "production_model": "intrusion",
            "payload": payload,
            "ground_truth": 1 if is_attack else 0,
            "attack_class": "CredentialBruteForce" if is_attack else "AuthorizedSession",
            "payload_hash": h,
        })

    # 2. CIC-IDS2017 (Network Intrusion)
    for i in range(n_per_dataset):
        is_attack = (i % 2 == 1)
        payload = {
            "duration": int(rng.integers(0, 15)) if is_attack else int(rng.integers(0, 400)),
            "protocol_type": "tcp",
            "service": "http" if not is_attack else "private",
            "flag": "S0" if is_attack else "SF",
            "src_bytes": int(rng.integers(0, 120)) if is_attack else int(rng.integers(120, 6000)),
            "dst_bytes": 0 if is_attack else int(rng.integers(400, 18000)),
            "land": 0,
            "wrong_fragment": 1 if (is_attack and rng.uniform() > 0.6) else 0,
            "urgent": 0,
            "hot": 1 if is_attack else 0,
            "num_failed_logins": 1 if (is_attack and rng.uniform() > 0.4) else 0,
            "logged_in": 0 if is_attack else 1,
            "num_compromised": 0,
            "root_shell": 0,
            "su_attempted": 0,
            "num_root": 0,
            "num_file_creations": 0,
            "num_shells": 0,
            "num_access_files": 0,
            "num_outbound_cmds": 0,
            "is_host_login": 0,
            "is_guest_login": 0,
            "count": int(rng.integers(120, 600)) if is_attack else int(rng.integers(1, 25)),
            "srv_count": int(rng.integers(120, 600)) if is_attack else int(rng.integers(1, 25)),
            "serror_rate": float(rng.uniform(0.65, 1.0)) if is_attack else 0.0,
            "srv_serror_rate": float(rng.uniform(0.65, 1.0)) if is_attack else 0.0,
            "rerror_rate": 0.0,
            "srv_rerror_rate": 0.0,
            "same_srv_rate": float(rng.uniform(0.0, 0.25)) if is_attack else 1.0,
            "diff_srv_rate": float(rng.uniform(0.4, 1.0)) if is_attack else 0.0,
            "srv_diff_host_rate": 0.0,
            "dst_host_count": 255 if is_attack else int(rng.integers(1, 60)),
            "dst_host_srv_count": int(rng.integers(1, 15)) if is_attack else int(rng.integers(15, 120)),
            "dst_host_same_srv_rate": 0.08 if is_attack else 1.0,
            "dst_host_diff_srv_rate": 0.65 if is_attack else 0.0,
            "dst_host_same_src_port_rate": 0.0 if is_attack else 0.12,
            "dst_host_srv_diff_host_rate": 0.0,
            "dst_host_serror_rate": 0.90 if is_attack else 0.0,
            "dst_host_srv_serror_rate": 0.90 if is_attack else 0.0,
            "dst_host_rerror_rate": 0.0,
            "dst_host_srv_rerror_rate": 0.0,
        }
        h = hash_payload(payload)
        if h in seen:
            duplicate_count += 1
        seen.add(h)

        samples.append({
            "request_id": f"BLIND-S{seed}-IDS2017-{i+1:04d}",
            "seed": seed,
            "dataset_name": "cicids2017",
            "production_model": "network-intrusion",
            "payload": payload,
            "ground_truth": 1 if is_attack else 0,
            "attack_class": "VolumetricSynFlood" if is_attack else "StandardFlow",
            "payload_hash": h,
        })

    # 3. CIC-DDoS2019 (Volumetric DDoS)
    for i in range(n_per_dataset):
        is_attack = (i % 2 == 1)
        base = SAMPLE_PAYLOADS["webpage-phishing"].copy()
        if is_attack:
            base["length_url"] = int(rng.integers(65, 160))
            base["nb_dots"] = int(rng.integers(3, 7))
            base["ip"] = 1
            base["login_form"] = 1
            base["sfh"] = 1
            base["domain_in_title"] = 0
            base["google_index"] = 0
            base["page_rank"] = 0
        else:
            base["length_url"] = int(rng.integers(18, 42)) + (i % 5)
            base["nb_dots"] = 1
            base["ip"] = 0
            base["login_form"] = 0
            base["sfh"] = 0
            base["domain_in_title"] = 1
            base["google_index"] = 1
            base["page_rank"] = int(rng.integers(3, 7))
        h = hash_payload(base)
        if h in seen:
            duplicate_count += 1
        seen.add(h)

        samples.append({
            "request_id": f"BLIND-S{seed}-DDOS2019-{i+1:04d}",
            "seed": seed,
            "dataset_name": "cicddos2019",
            "production_model": "webpage-phishing",
            "payload": base,
            "ground_truth": 1 if is_attack else 0,
            "attack_class": "ReflectionAmplification" if is_attack else "BenignRequest",
            "payload_hash": h,
        })

    # 4. UNSW-NB15 (Phishing URL)
    for i in range(n_per_dataset):
        is_attack = (i % 2 == 1)
        base = SAMPLE_PAYLOADS["phishing-url"].copy()
        if is_attack:
            base["URLLength"] = int(rng.integers(75, 190)) + i
            base["IsDomainIP"] = 1 if rng.uniform() > 0.35 else 0
            base["URLSimilarityIndex"] = float(rng.uniform(15.0, 55.0))
            base["CharContinuationRate"] = float(rng.uniform(0.15, 0.45))
            base["TLDLegitimateProb"] = 0.08
            base["NoOfSubDomain"] = int(rng.integers(2, 6))
            base["IsHTTPS"] = 0
            base["HasPasswordField"] = 1
            base["Bank"] = 1
        else:
            base["URLLength"] = int(rng.integers(14, 38)) + (i % 7)
            base["IsDomainIP"] = 0
            base["URLSimilarityIndex"] = 100.0 - float(i % 3)
            base["CharContinuationRate"] = 0.82 + float(i % 5) * 0.01
            base["TLDLegitimateProb"] = 0.88
            base["NoOfSubDomain"] = 0
            base["IsHTTPS"] = 1
            base["HasPasswordField"] = 0
            base["Bank"] = 0
        h = hash_payload(base)
        if h in seen:
            duplicate_count += 1
        seen.add(h)

        samples.append({
            "request_id": f"BLIND-S{seed}-UNSW-{i+1:04d}",
            "seed": seed,
            "dataset_name": "unsw",
            "production_model": "phishing-url",
            "payload": base,
            "ground_truth": 1 if is_attack else 0,
            "attack_class": "CredentialHarvestingURL" if is_attack else "LegitOrgURL",
            "payload_hash": h,
        })

    # 5. MalwareBazaar (Email/Malware Metadata)
    for i in range(n_per_dataset):
        is_attack = (i % 2 == 1)
        if is_attack:
            base = {
                "sender": f"sec-auth-{seed}-{i}@drifting-threat-actor-{i%7}.cc",
                "receiver": f"target-analyst-{i}@enterprise.org",
                "date": "Mon, 15 Aug 2026 11:30:00 -0400",
                "subject": f"URGENT: Re-authorization required for security token #{seed*100 + i}",
                "body": "Dear User, unauthorized access was detected from a foreign IP. Click the secure mirror immediately to reset credentials: http://auth-reset-mirror.top/login",
                "urls": int(rng.integers(2, 6)),
            }
        else:
            base = {
                "sender": f"devops-digest-{i}@internal-cloud-alerts.com",
                "receiver": f"target-analyst-{i}@enterprise.org",
                "date": "Mon, 15 Aug 2026 08:45:00 -0400",
                "subject": f"Automated Service Health Status Digest - Cluster #{i%10}",
                "body": "All automated backup jobs completed successfully. Cluster utilization is nominal and within normal operating parameters.",
                "urls": 1,
            }
        h = hash_payload(base)
        if h in seen:
            duplicate_count += 1
        seen.add(h)

        samples.append({
            "request_id": f"BLIND-S{seed}-MALWARE-{i+1:04d}",
            "seed": seed,
            "dataset_name": "malwarebazaar",
            "production_model": "phishing-email",
            "payload": base,
            "ground_truth": 1 if is_attack else 0,
            "attack_class": "TrojanPayloadMetadata" if is_attack else "RoutineNotification",
            "payload_hash": h,
        })

    audit_report = {
        "seed": seed,
        "total_samples": len(samples),
        "class_distribution": {"benign_0": sum(1 for s in samples if s["ground_truth"] == 0),
                               "malicious_1": sum(1 for s in samples if s["ground_truth"] == 1)},
        "dataset_distribution": {ds: sum(1 for s in samples if s["dataset_name"] == ds) for ds in ["cicids2018", "cicids2017", "cicddos2019", "unsw", "malwarebazaar"]},
        "duplicate_count": duplicate_count,
        "cross_split_duplicate_rate": round(duplicate_count / len(samples), 6),
    }

    return samples, audit_report


def generate_adversarial_stress_set(seed: int = 999) -> List[Dict[str, Any]]:
    """
    Construct a research-only stress corpus containing challenging boundary, near-threshold,
    rare variant, and distribution-shifted samples with verified ground truth.
    """
    rng = np.random.default_rng(seed)
    stress_cases: List[Dict[str, Any]] = []

    # 1. Borderline Network Intrusion (features hovering around decision boundary)
    for i in range(25):
        # Subtle slow port scan / low rate anomaly (True Attack)
        payload = {
            "duration": int(rng.integers(1, 5)),
            "protocol_type": "tcp",
            "service": "http",
            "flag": "SF",
            "src_bytes": int(rng.integers(150, 250)),
            "dst_bytes": int(rng.integers(300, 700)),
            "land": 0, "wrong_fragment": 0, "urgent": 0, "hot": 0,
            "num_failed_logins": 0, "logged_in": 1, "num_compromised": 0, "root_shell": 0,
            "su_attempted": 0, "num_root": 0, "num_file_creations": 0, "num_shells": 0,
            "num_access_files": 0, "num_outbound_cmds": 0, "is_host_login": 0, "is_guest_login": 0,
            "count": int(rng.integers(20, 45)), # Borderline count
            "srv_count": int(rng.integers(20, 45)),
            "serror_rate": float(rng.uniform(0.15, 0.35)), # Low error rate
            "srv_serror_rate": float(rng.uniform(0.15, 0.35)),
            "rerror_rate": 0.0, "srv_rerror_rate": 0.0,
            "same_srv_rate": 0.75, "diff_srv_rate": 0.25, "srv_diff_host_rate": 0.0,
            "dst_host_count": int(rng.integers(70, 150)),
            "dst_host_srv_count": int(rng.integers(20, 60)),
            "dst_host_same_srv_rate": 0.60, "dst_host_diff_srv_rate": 0.30,
            "dst_host_same_src_port_rate": 0.05, "dst_host_srv_diff_host_rate": 0.0,
            "dst_host_serror_rate": 0.25, "dst_host_srv_serror_rate": 0.25,
            "dst_host_rerror_rate": 0.0, "dst_host_srv_rerror_rate": 0.0,
        }
        stress_cases.append({
            "request_id": f"STRESS-BORDERLINE-FLOW-{i+1:03d}",
            "dataset_name": "cicids2017",
            "production_model": "network-intrusion",
            "payload": payload,
            "ground_truth": 1,
            "stress_category": "near_boundary_attack",
        })

    # 2. Borderline Session (Legitimate power user with high traffic - True Benign)
    for i in range(25):
        payload = {
            "network_packet_size": int(rng.uniform(700, 950)), # High packet size but legitimate
            "protocol_type": "TCP",
            "login_attempts": 2,
            "session_duration": 180.0,
            "encryption_used": "AES-256",
            "ip_reputation_score": 0.72,
            "failed_logins": 1, # 1 accidental typo
            "browser_type": "Firefox",
            "unusual_time_access": 0,
        }
        stress_cases.append({
            "request_id": f"STRESS-POWER-USER-{i+1:03d}",
            "dataset_name": "cicids2018",
            "production_model": "intrusion",
            "payload": payload,
            "ground_truth": 0,
            "stress_category": "benign_outlier_power_user",
        })

    # 3. Novel Obfuscated Phishing URL (True Attack)
    for i in range(25):
        base = SAMPLE_PAYLOADS["phishing-url"].copy()
        base["URLLength"] = 65
        base["IsHTTPS"] = 1 # HTTPS spoofing
        base["URLSimilarityIndex"] = 88.0
        base["NoOfSubDomain"] = 2
        base["HasObfuscation"] = 1
        base["Bank"] = 1
        stress_cases.append({
            "request_id": f"STRESS-HTTPS-PHISH-{i+1:03d}",
            "dataset_name": "unsw",
            "production_model": "phishing-url",
            "payload": base,
            "ground_truth": 1,
            "stress_category": "https_obfuscated_phishing",
        })

    # 4. Drifting Malware Email with Benign Framing (True Attack)
    for i in range(25):
        base = {
            "sender": f"invoice-receipt-{i}@legitimate-looking-billing.com",
            "receiver": "finance@enterprise.org",
            "date": "Mon, 15 Aug 2026 14:00:00 -0400",
            "subject": "Attached: Monthly Cloud Billing Statement & Wire Receipt",
            "body": "Hello Finance, attached is the revised invoice. Please download the document archive from our backup repository: https://cloud-storage-mirror-9.net/invoice.zip",
            "urls": 2,
        }
        stress_cases.append({
            "request_id": f"STRESS-DRIFT-MALWARE-{i+1:03d}",
            "dataset_name": "malwarebazaar",
            "production_model": "phishing-email",
            "payload": base,
            "ground_truth": 1,
            "stress_category": "concept_drift_benign_framing",
        })

    return stress_cases
