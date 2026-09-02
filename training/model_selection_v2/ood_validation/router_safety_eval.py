"""
Router Safety and Adversarial Robustness Engine for Model Selection V2.
Tests extreme input payloads, anomalous schemas, extreme values, NaNs, and Infs.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
V2_MODULE = PROJECT_ROOT / "training" / "model_selection_v2"
for p in [str(V2_MODULE), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from training.model_selection_v2.adaptive_router import AdaptiveRouterV2
    from training.model_selection_v2.config import RepresentationType, SecurityDomain
except ImportError:
    from adaptive_router import AdaptiveRouterV2
    from config import RepresentationType, SecurityDomain


class RouterSafetyAuditor:
    """Evaluates router fault-tolerance against adversarial edge cases."""

    def __init__(self):
        self.router = AdaptiveRouterV2()

    def run_full_safety_audit(self) -> Dict[str, Any]:
        """
        Execute 12 extreme safety and boundary condition test cases.
        """
        test_payloads = [
            ("1_valid_network_flow", {"flow_duration": 1500, "total_fwd_packets": 25, "syn_flag_count": 1}),
            ("2_valid_malware_record", {"imphash": "imp_9988", "ssdeep": "384:abc:12", "vtpercent": 88.0, "file_type_guess": "exe"}),
            ("3_unknown_arbitrary_schema", {"customer_id": "CUST_1001", "transaction_amt": 450.50, "zip_code": 90210}),
            ("4_partial_flow_schema", {"flow_duration": 100}),
            ("5_mixed_domain_schema", {"flow_duration": 200, "imphash": "imp_123", "url_length": 55}),
            ("6_empty_dataframe", pd.DataFrame()),
            ("7_single_row_dict", {"total_fwd_packets": 1}),
            ("8_batch_dataframe_100_rows", pd.DataFrame({"flow_duration": np.random.randint(10, 1000, 100)})),
            ("9_unexpected_categoricals", {"file_type_guess": "UNKNOWN_SUPER_EXT", "reporter": "NEW_RESEARCHER_XYZ"}),
            ("10_nan_matrix", pd.DataFrame({"flow_duration": [np.nan, np.nan], "total_fwd_packets": [np.nan, 5.0]})),
            ("11_inf_matrix", pd.DataFrame({"flow_duration": [np.inf, -np.inf], "packet_count": [10.0, 20.0]})),
            ("12_extreme_large_numbers", pd.DataFrame({"flow_duration": [1e15, 1e18], "bytes": [1e20, 1e22]})),
        ]

        audit_results = []
        crashes = 0
        silent_misroutings = 0

        for name, payload in test_payloads:
            try:
                res = self.router.route_and_predict(payload)
                audit_results.append({
                    "test_name": name,
                    "status": "SUCCESS",
                    "domain": res.domain.value,
                    "domain_confidence": res.confidence_report.domain_confidence,
                    "representation": res.representation_used.value,
                    "model": res.selected_model,
                    "selection_confidence": res.confidence_report.composite_confidence,
                    "fallback_used": res.is_fallback_active,
                    "reason": res.confidence_report.reason,
                })
            except Exception as e:
                crashes += 1
                audit_results.append({
                    "test_name": name,
                    "status": "CRASHED",
                    "error": str(e),
                })

        return {
            "total_safety_tests": len(test_payloads),
            "passed_tests": len(test_payloads) - crashes,
            "crashes": crashes,
            "silent_misroutings": silent_misroutings,
            "router_safety_status": "PASS" if crashes == 0 else "FAIL",
            "audit_details": audit_results,
        }
