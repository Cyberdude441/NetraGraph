"""End-to-End Diagnostics and Direct Verification Test for Models A–E."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from ml.config.environment import output_root, registry_root
from ml.inference.model_loader import LoadedModel, validate_bundle
from ml.registry.model_registry import ModelRegistry

REQUIRED_FILES = [
    "model.joblib",
    "preprocessor.joblib",
    "metadata.json",
    "feature_schema.json",
    "label_mapping.json",
    "metrics.json",
    "requirements_model.txt",
    "training_report.json",
]

MODELS_TO_VERIFY = [
    ("intrusion", "v1", "Model A: Session Intrusion Detection"),
    ("network-intrusion", "v1", "Model B: Network Intrusion Detection"),
    ("phishing-url", "v1", "Model C: Phishing URL Detection"),
    ("webpage-phishing", "v1", "Model D: Web Page Phishing Detection"),
    ("phishing-email", "v1", "Model E: Phishing Email Detection"),
]

# Sample realistic test payloads for each model
SAMPLE_PAYLOADS = {
    "intrusion": {
        "network_packet_size": 512,
        "protocol_type": "TCP",
        "login_attempts": 1,
        "session_duration": 120.5,
        "encryption_used": "AES-256",
        "ip_reputation_score": 0.95,
        "failed_logins": 0,
        "browser_type": "Chrome",
        "unusual_time_access": 0,
    },
    "network-intrusion": {
        "duration": 0,
        "protocol_type": "tcp",
        "service": "http",
        "flag": "SF",
        "src_bytes": 181,
        "dst_bytes": 5450,
        "land": 0,
        "wrong_fragment": 0,
        "urgent": 0,
        "hot": 0,
        "num_failed_logins": 0,
        "logged_in": 1,
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
        "count": 8,
        "srv_count": 8,
        "serror_rate": 0.0,
        "srv_serror_rate": 0.0,
        "rerror_rate": 0.0,
        "srv_rerror_rate": 0.0,
        "same_srv_rate": 1.0,
        "diff_srv_rate": 0.0,
        "srv_diff_host_rate": 0.0,
        "dst_host_count": 9,
        "dst_host_srv_count": 9,
        "dst_host_same_srv_rate": 1.0,
        "dst_host_diff_srv_rate": 0.0,
        "dst_host_same_src_port_rate": 0.11,
        "dst_host_srv_diff_host_rate": 0.0,
        "dst_host_serror_rate": 0.0,
        "dst_host_srv_serror_rate": 0.0,
        "dst_host_rerror_rate": 0.0,
        "dst_host_srv_rerror_rate": 0.0,
    },
    "phishing-url": {
        "URLLength": 24,
        "DomainLength": 12,
        "IsDomainIP": 0,
        "TLD": "com",
        "URLSimilarityIndex": 100.0,
        "CharContinuationRate": 0.8,
        "TLDLegitimateProb": 0.52,
        "URLCharProb": 0.05,
        "TLDLength": 3,
        "NoOfSubDomain": 1,
        "HasObfuscation": 0,
        "NoOfObfuscatedChar": 0,
        "ObfuscationRatio": 0.0,
        "NoOfLettersInURL": 18,
        "LetterRatioInURL": 0.75,
        "NoOfDegitsInURL": 0,
        "DegitRatioInURL": 0.0,
        "NoOfEqualsInURL": 0,
        "NoOfQMarkInURL": 0,
        "NoOfAmpersandInURL": 0,
        "NoOfOtherSpecialCharsInURL": 2,
        "SpacialCharRatioInURL": 0.08,
        "IsHTTPS": 1,
        "LineOfCode": 250,
        "LargestLineLength": 120,
        "HasTitle": 1,
        "DomainTitleMatchScore": 100.0,
        "URLTitleMatchScore": 100.0,
        "HasFavicon": 1,
        "Robots": 1,
        "IsResponsive": 1,
        "NoOfURLRedirect": 0,
        "NoOfSelfRedirect": 0,
        "HasDescription": 1,
        "NoOfPopup": 0,
        "NoOfiFrame": 0,
        "HasExternalFormSubmit": 0,
        "HasSocialNet": 1,
        "HasSubmitButton": 1,
        "HasHiddenFields": 0,
        "HasPasswordField": 0,
        "Bank": 0,
        "Pay": 0,
        "Crypto": 0,
        "HasCopyrightInfo": 1,
        "NoOfImage": 5,
        "NoOfCSS": 2,
        "NoOfJS": 4,
        "NoOfSelfRef": 10,
        "NoOfEmptyRef": 0,
        "NoOfExternalRef": 2,
    },
    "webpage-phishing": {
        "length_url": 35,
        "length_hostname": 15,
        "ip": 0,
        "nb_dots": 2,
        "nb_hyphens": 0,
        "nb_at": 0,
        "nb_qm": 0,
        "nb_and": 0,
        "nb_or": 0,
        "nb_eq": 0,
        "nb_underscore": 0,
        "nb_tilde": 0,
        "nb_percent": 0,
        "nb_slash": 3,
        "nb_star": 0,
        "nb_colon": 1,
        "nb_comma": 0,
        "nb_semicolumn": 0,
        "nb_dollar": 0,
        "nb_space": 0,
        "nb_www": 1,
        "nb_com": 1,
        "nb_dslash": 0,
        "http_in_path": 0,
        "https_token": 0,
        "ratio_digits_url": 0.0,
        "ratio_digits_host": 0.0,
        "punycode": 0,
        "port": 0,
        "tld_in_path": 0,
        "tld_in_subdomain": 0,
        "abnormal_subdomain": 0,
        "nb_subdomains": 1,
        "prefix_suffix": 0,
        "random_domain": 0,
        "shortening_service": 0,
        "path_extension": 0,
        "nb_redirection": 0,
        "nb_external_redirection": 0,
        "length_words_raw": 4,
        "char_repeat": 0,
        "shortest_words_raw": 3,
        "shortest_word_host": 3,
        "shortest_word_path": 4,
        "longest_words_raw": 8,
        "longest_word_host": 8,
        "longest_word_path": 6,
        "avg_words_raw": 5.0,
        "avg_word_host": 5.0,
        "avg_word_path": 5.0,
        "phish_hints": 0,
        "domain_in_brand": 0,
        "brand_in_subdomain": 0,
        "brand_in_path": 0,
        "suspecious_tld": 0,
        "statistical_report": 0,
        "nb_hyperlinks": 25,
        "ratio_intHyperlinks": 0.9,
        "ratio_extHyperlinks": 0.1,
        "ratio_nullHyperlinks": 0,
        "nb_extCSS": 1,
        "ratio_intRedirection": 0,
        "ratio_extRedirection": 0.0,
        "ratio_intErrors": 0,
        "ratio_extErrors": 0.0,
        "login_form": 0,
        "external_favicon": 0,
        "links_in_tags": 85.0,
        "submit_email": 0,
        "ratio_intMedia": 0.95,
        "ratio_extMedia": 0.05,
        "sfh": 0,
        "iframe": 0,
        "popup_window": 0,
        "safe_anchor": 90.0,
        "onmouseover": 0,
        "right_clic": 0,
        "empty_title": 0,
        "domain_in_title": 1,
        "domain_with_copyright": 1,
        "whois_registered_domain": 1,
        "domain_registration_length": 365,
        "domain_age": 1500,
        "web_traffic": 1000,
        "dns_record": 1,
        "google_index": 1,
        "page_rank": 5,
    },
    "phishing-email": {
        "sender": "alerts@chase-bank-security-center.com",
        "receiver": "victim@example.com",
        "date": "Mon, 15 Aug 2026 10:15:00 -0400",
        "subject": "URGENT: Your account has been temporarily restricted",
        "body": "Dear Customer, We detected unusual activity on your debit card. Click the link below to verify your login credentials immediately: http://chase-security-login.com/verify",
        "urls": 1,
    },
}


def run_diagnostics():
    print("================================================================")
    print("NETRAGRAPH MACHINE LEARNING DIAGNOSTICS & VERIFICATION SUITE")
    print("================================================================")

    results = {}

    for model_name, version, title in MODELS_TO_VERIFY:
        print(f"\n--- [DIAGNOSTIC] {title} ({model_name}/{version}) ---")
        loc = registry_root() / model_name / version
        if not loc.exists():
            loc = output_root() / model_name / version

        # 1. Check file existence
        missing = [f for f in REQUIRED_FILES if not (loc / f).exists()]
        if missing:
            print(f"  [FAIL] Missing artifact files: {missing}")
            results[model_name] = {"status": "FAIL", "reason": f"Missing files: {missing}"}
            continue
        print(f"  [PASS] All {len(REQUIRED_FILES)} required artifact companion files present.")

        # 2. SHA-256 Hash
        model_bytes = (loc / "model.joblib").read_bytes()
        sha256 = hashlib.sha256(model_bytes).hexdigest()
        print(f"  [PASS] model.joblib SHA-256: {sha256[:16]}...{sha256[-8:]} ({len(model_bytes):,} bytes)")

        # 3. Validate Bundle
        details = validate_bundle(loc)
        metadata = details["metadata"]
        schema = details["schema"]
        print(f"  [PASS] Metadata valid: {metadata['model_name']} ({metadata['model_type']})")
        print(f"  [PASS] Feature count declared in schema: {len(schema['feature_names'])}")

        # 4. Deserialization
        try:
            loaded = LoadedModel(loc)
            print(f"  [PASS] LoadedModel deserialization succeeded.")
            print(f"  [PASS] Estimator: {type(loaded.model).__name__}")
            print(f"  [PASS] Preprocessor: {type(loaded.preprocessor).__name__}")
            print(f"  [PASS] Label Mapping: {loaded.labels}")
        except Exception as exc:
            print(f"  [FAIL] Deserialization error: {exc}")
            results[model_name] = {"status": "FAIL", "reason": str(exc)}
            continue

        # 5. Direct Inference with Sample Payload
        sample = SAMPLE_PAYLOADS.get(model_name)
        if not sample:
            print(f"  [WARN] No sample payload defined for {model_name}")
            continue

        try:
            prediction_res = loaded.predict(sample)
            print(f"  [PASS] Direct Inference Succeeded:")
            print(f"         Prediction: {prediction_res['prediction']}")
            print(f"         Probability: {prediction_res['probability']}")
            print(f"         Features Validated: {prediction_res['features_validated']}")
            results[model_name] = {
                "status": "PASS",
                "sha256": sha256,
                "prediction": prediction_res["prediction"],
                "probability": prediction_res["probability"],
                "features_count": len(schema["feature_names"]),
            }
        except Exception as exc:
            print(f"  [FAIL] Direct inference execution failed: {exc}")
            results[model_name] = {"status": "FAIL", "reason": str(exc)}

    print("\n================================================================")
    print("DIAGNOSTIC SUMMARY REPORT")
    print("================================================================")
    all_passed = True
    for name, v in results.items():
        status = v["status"]
        if status == "PASS":
            print(f"  [OK] {name:<18} | Pred: {str(v['prediction']):<15} | Conf: {v['probability']:.4f} | Features: {v['features_count']}")
        else:
            all_passed = False
            print(f"  [FAIL] {name:<18} | Reason: {v['reason']}")

    if all_passed and len(results) == len(MODELS_TO_VERIFY):
        print("\nALL MODELS A–E PASSED VERIFICATION!")
    else:
        print("\nSOME MODELS FAILED VERIFICATION.")


if __name__ == "__main__":
    run_diagnostics()
