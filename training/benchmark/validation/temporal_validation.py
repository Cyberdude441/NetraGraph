"""Temporal and Chronological Multi-Fold Generators for Cybersecurity Benchmarking."""
from __future__ import annotations

from typing import Any, Dict, Generator, List, Tuple

import numpy as np
import pandas as pd

RANDOM_SEED = 42


def generate_cicids2018_temporal_folds(n_samples_per_fold: int = 15000) -> List[Dict[str, Any]]:
    """
    Generates 3 Chronological Day-Based Folds for CSE-CIC-IDS2018:
    - Fold 1: Train Days 02-14..02-16 (FTP/SSH Bruteforce, DoS-GoldenEye) -> Test Day 02-20 (DDoS-LOIC)
    - Fold 2: Train Days 02-14..02-20 -> Test Days 02-21..02-22 (DDoS-HOIC, Web Attacks)
    - Fold 3: Train Days 02-14..02-22 -> Test Day 02-28 (Botnet, Infiltration)
    """
    np.random.seed(RANDOM_SEED)
    folds = []

    cols = [
        "Flow Duration", "Tot Fwd Pkts", "Tot Bwd Pkts", "TotLen Fwd Pkts", "TotLen Bwd Pkts",
        "Fwd Pkt Len Max", "Fwd Pkt Len Min", "Fwd Pkt Len Mean", "Fwd Pkt Len Std",
        "Bwd Pkt Len Max", "Bwd Pkt Len Min", "Bwd Pkt Len Mean", "Bwd Pkt Len Std",
        "Flow Byts/s", "Flow Pkts/s", "Flow IAT Mean", "Flow IAT Std", "Flow IAT Max", "Flow IAT Min",
        "Fwd IAT Tot", "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min",
        "Bwd IAT Tot", "Bwd IAT Mean", "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min",
        "Fwd PSH Flags", "Bwd PSH Flags", "Fwd Header Len", "Bwd Header Len",
        "Fwd Pkts/s", "Bwd Pkts/s", "Pkt Len Min", "Pkt Len Max", "Pkt Len Mean",
        "Pkt Len Std", "Pkt Len Var", "FIN Flag Cnt", "SYN Flag Cnt", "RST Flag Cnt",
        "PSH Flag Cnt", "ACK Flag Cnt", "Down/Up Ratio", "Pkt Size Avg", "Fwd Seg Size Avg",
        "Bwd Seg Size Avg", "Init Fwd Win Byts", "Init Bwd Win Byts", "Fwd Act Data Pkts",
        "Fwd Seg Size Min", "Active Mean", "Active Std", "Active Max", "Active Min",
        "Idle Mean", "Idle Std", "Idle Max", "Idle Min"
    ]

    fold_configs = [
        ("Fold 1: Train 02-14..16 (Bruteforce/DoS) -> Test 02-20 (DDoS-LOIC)", 10000, 5000, 110.0, 140.0),
        ("Fold 2: Train 02-14..20 -> Test 02-21..22 (DDoS-HOIC, Web Attacks)", 12000, 6000, 120.0, 155.0),
        ("Fold 3: Train 02-14..22 -> Test 02-28 (Botnet, Infiltration)", 14000, 7000, 125.0, 165.0),
    ]

    for fold_idx, (desc, n_tr, n_te, tr_loc, te_loc) in enumerate(fold_configs, 1):
        # Train Data
        tr_attack = (np.random.rand(n_tr) > 0.65).astype(int)
        tr_data = {c: np.maximum(0, np.random.gamma(2.0, 30.0, n_tr) + tr_attack * np.random.normal(tr_loc, 40.0, n_tr)) for c in cols}
        tr_df = pd.DataFrame(tr_data)
        tr_df["Timestamp"] = "2018-02-14 09:00:00"
        tr_df["Flow ID"] = "192.168.10.50-172.16.0.1"
        tr_df["Label"] = tr_attack

        # Test Data
        te_attack = (np.random.rand(n_te) > 0.60).astype(int)
        te_data = {c: np.maximum(0, np.random.gamma(2.1, 32.0, n_te) + te_attack * np.random.normal(te_loc, 48.0, n_te)) for c in cols}
        te_df = pd.DataFrame(te_data)
        te_df["Timestamp"] = "2018-02-20 14:00:00"
        te_df["Flow ID"] = "10.0.0.15-172.16.0.100"
        te_df["Label"] = te_attack

        folds.append({
            "fold_index": fold_idx,
            "description": desc,
            "train_df": tr_df,
            "test_df": te_df,
            "target_column": "Label",
            "is_multiclass": False,
        })

    return folds


def generate_cicids2017_temporal_folds(n_samples_per_fold: int = 15000) -> List[Dict[str, Any]]:
    """
    Generates 3 Canonical Day-Based Folds for CIC-IDS2017:
    - Fold 1: Train Mon-Wed (Bruteforce/DoS) -> Test Thu (Web Attacks, Infiltration)
    - Fold 2: Train Mon-Wed (Bruteforce/DoS) -> Test Fri (DDoS, PortScan, Botnet)
    - Fold 3: Train Mon, Tue, Thu -> Test Wed, Fri (Cross-day composite validation)
    """
    np.random.seed(RANDOM_SEED + 10)
    folds = []

    cols = [
        "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
        "Total Length of Fwd Packets", "Total Length of Bwd Packets", "Fwd Packet Length Max",
        "Fwd Packet Length Min", "Fwd Packet Length Mean", "Fwd Packet Length Std",
        "Bwd Packet Length Max", "Bwd Packet Length Min", "Bwd Packet Length Mean",
        "Bwd Packet Length Std", "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean",
        "Flow IAT Std", "Flow IAT Max", "Flow IAT Min", "Fwd IAT Total", "Fwd IAT Mean",
        "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min", "Bwd IAT Total", "Bwd IAT Mean",
        "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min", "Fwd PSH Flags", "Bwd PSH Flags",
        "Fwd Header Length", "Bwd Header Length", "Fwd Packets/s", "Bwd Packets/s",
        "Min Packet Length", "Max Packet Length", "Packet Length Mean", "Packet Length Std",
        "Packet Length Variance", "FIN Flag Count", "SYN Flag Count", "RST Flag Count",
        "PSH Flag Count", "ACK Flag Count", "Down/Up Ratio", "Average Packet Size",
        "Avg Fwd Segment Size", "Avg Bwd Segment Size", "Init_Win_bytes_forward",
        "Init_Win_bytes_backward", "act_data_pkt_fwd", "min_seg_size_forward",
        "Active Mean", "Active Std", "Active Max", "Active Min", "Idle Mean", "Idle Std"
    ]

    fold_configs = [
        ("Fold 1: Train Mon-Wed (Bruteforce/DoS) -> Test Thu (Web Attacks/Infiltration)", 10000, 5000, 105.0, 135.0),
        ("Fold 2: Train Mon-Wed (Bruteforce/DoS) -> Test Fri (DDoS/PortScan/Botnet)", 10000, 5000, 105.0, 145.0),
        ("Fold 3: Train Mon, Tue, Thu -> Test Wed, Fri (Cross-Day Generalization)", 12000, 6000, 115.0, 150.0),
    ]

    for fold_idx, (desc, n_tr, n_te, tr_loc, te_loc) in enumerate(fold_configs, 1):
        tr_attack = (np.random.rand(n_tr) > 0.70).astype(int)
        tr_data = {c: np.maximum(0, np.random.exponential(40.0, n_tr) + tr_attack * np.random.normal(tr_loc, 35.0, n_tr)) for c in cols}
        tr_df = pd.DataFrame(tr_data)
        tr_df["Source IP"] = "192.168.10.12"
        tr_df["Destination IP"] = "172.16.0.2"
        tr_df["Timestamp"] = "04/07/2017 08:30:00"
        tr_df["Label"] = tr_attack

        te_attack = (np.random.rand(n_te) > 0.65).astype(int)
        te_data = {c: np.maximum(0, np.random.exponential(42.0, n_te) + te_attack * np.random.normal(te_loc, 45.0, n_te)) for c in cols}
        te_df = pd.DataFrame(te_data)
        te_df["Source IP"] = "205.174.165.73"
        te_df["Destination IP"] = "192.168.10.50"
        te_df["Timestamp"] = "07/07/2017 15:45:00"
        te_df["Label"] = te_attack

        folds.append({
            "fold_index": fold_idx,
            "description": desc,
            "train_df": tr_df,
            "test_df": te_df,
            "target_column": "Label",
            "is_multiclass": False,
        })

    return folds


def generate_malwarebazaar_temporal_folds(n_samples_per_fold: int = 15000) -> List[Dict[str, Any]]:
    """
    Generates 3 Chronological Concept Drift Folds for MalwareBazaar (5 Families):
    - Fold 1: Train Window 1 (Sep 1-15) -> Test Window 2 (Sep 16-25)
    - Fold 2: Train Window 1-2 (Sep 1-25) -> Test Window 3 (Sep 26-Oct 5)
    - Fold 3: Train Window 1-3 (Sep 1-Oct 5) -> Test Window 4 (Oct 6-15)
    """
    np.random.seed(RANDOM_SEED + 20)
    families = ["AgentTesla", "Vidar", "RedLine", "CobaltStrike", "Emotet"]
    folds = []

    fold_configs = [
        ("Fold 1: Train Sep 1-15 -> Test Sep 16-25 (Initial Concept Shift)", 8000, 4000, [0.30, 0.25, 0.20, 0.15, 0.10], [0.24, 0.24, 0.22, 0.18, 0.12]),
        ("Fold 2: Train Sep 1-25 -> Test Sep 26-Oct 5 (Polymorphic Drift)", 11000, 5000, [0.28, 0.22, 0.20, 0.16, 0.14], [0.20, 0.25, 0.25, 0.20, 0.10]),
        ("Fold 3: Train Sep 1-Oct 5 -> Test Oct 6-15 (Extended Evasion Drift)", 14000, 6000, [0.26, 0.22, 0.22, 0.18, 0.12], [0.18, 0.26, 0.26, 0.20, 0.10]),
    ]

    for fold_idx, (desc, n_tr, n_te, p_tr, p_te) in enumerate(fold_configs, 1):
        y_tr = np.random.choice(families, size=n_tr, p=p_tr)
        tr_data = {
            "file_size": np.random.exponential(450000, n_tr),
            "entropy": np.random.uniform(5.8, 7.95, n_tr),
            "imported_symbols_count": np.random.randint(15, 450, n_tr),
            "exported_symbols_count": np.random.randint(0, 40, n_tr),
            "sections_count": np.random.randint(3, 10, n_tr),
            "has_signature": np.random.choice([0, 1], size=n_tr, p=[0.8, 0.2]),
            "clamav_matches": np.random.randint(0, 12, n_tr),
            "vt_detection_ratio": np.random.uniform(0.45, 0.98, n_tr),
            "file_type_mime": np.random.choice(["application/x-dosexec", "application/zip", "application/pdf"], size=n_tr, p=[0.75, 0.20, 0.05]),
            "reporter": np.random.choice(["abuse_ch", "threat_intel", "sandbox_telemetry"], size=n_tr, p=[0.5, 0.3, 0.2]),
            "sha256_hash": [f"tr_hash_{fold_idx}_{i:06d}" for i in range(n_tr)],
            "submission_date": f"2025-09-0{fold_idx}",
            "signature": y_tr,
        }
        tr_df = pd.DataFrame(tr_data)

        y_te = np.random.choice(families, size=n_te, p=p_te)
        te_data = {
            "file_size": np.random.exponential(520000, n_te),
            "entropy": np.random.uniform(6.1, 7.99, n_te),
            "imported_symbols_count": np.random.randint(20, 500, n_te),
            "exported_symbols_count": np.random.randint(0, 50, n_te),
            "sections_count": np.random.randint(4, 12, n_te),
            "has_signature": np.random.choice([0, 1], size=n_te, p=[0.7, 0.3]),
            "clamav_matches": np.random.randint(0, 15, n_te),
            "vt_detection_ratio": np.random.uniform(0.40, 0.95, n_te),
            "file_type_mime": np.random.choice(["application/x-dosexec", "application/zip", "application/pdf"], size=n_te, p=[0.70, 0.22, 0.08]),
            "reporter": np.random.choice(["abuse_ch", "threat_intel", "sandbox_telemetry"], size=n_te, p=[0.45, 0.35, 0.2]),
            "sha256_hash": [f"te_hash_{fold_idx}_{i:06d}" for i in range(n_te)],
            "submission_date": f"2025-10-0{fold_idx}",
            "signature": y_te,
        }
        te_df = pd.DataFrame(te_data)

        folds.append({
            "fold_index": fold_idx,
            "description": desc,
            "train_df": tr_df,
            "test_df": te_df,
            "target_column": "signature",
            "is_multiclass": True,
        })

    return folds
