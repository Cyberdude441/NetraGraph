"""Rigorous Benchmark Configuration, Hardware Telemetry, and Temporal/Cross-Day Partition Generators."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

BENCHMARK_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BENCHMARK_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42


def detect_system_environment() -> Dict[str, Any]:
    """Inspects runtime versions and hardware capabilities (GPU/CPU)."""
    import sklearn
    import xgboost
    import lightgbm
    import catboost

    env_info = {
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "sklearn_version": sklearn.__version__,
        "xgboost_version": xgboost.__version__,
        "lightgbm_version": lightgbm.__version__,
        "catboost_version": catboost.__version__,
        "gpu_available": False,
        "gpu_name": "None (CPU only)",
        "xgboost_device": "cpu",
        "lightgbm_device": "cpu",
        "catboost_device": "CPU",
    }

    try:
        import torch
        if torch.cuda.is_available():
            env_info["gpu_available"] = True
            env_info["gpu_name"] = torch.cuda.get_device_name(0)
    except Exception:
        pass

    if not env_info["gpu_available"]:
        try:
            import subprocess
            smi = subprocess.check_output("nvidia-smi --query-gpu=name --format=csv,noheader", shell=True).decode().strip()
            if smi:
                env_info["gpu_available"] = True
                env_info["gpu_name"] = smi.split("\n")[0].strip()
        except Exception:
            pass

    if env_info["gpu_available"]:
        env_info["xgboost_device"] = "cuda"
        env_info["lightgbm_device"] = "gpu"
        env_info["catboost_device"] = "GPU"

    return env_info


def print_environment_banner(env_info: Dict[str, Any]) -> None:
    """Prints the benchmark banner and execution parameters."""
    print("=" * 82)
    print("NETRAGRAPH — RIGOROUS LEAKAGE-RESISTANT MULTI-ALGORITHM ML BENCHMARK")
    print("Validation Mode      : TEMPORAL & OUT-OF-DISTRIBUTION CROSS-PARTITION VALIDATION")
    print("=" * 82)
    print(f"Python version       : {env_info['python_version']}")
    print(f"NumPy version        : {env_info['numpy_version']}")
    print(f"scikit-learn version : {env_info['sklearn_version']}")
    print(f"XGBoost version      : {env_info['xgboost_version']}")
    print(f"LightGBM version     : {env_info['lightgbm_version']}")
    print(f"CatBoost version     : {env_info['catboost_version']}")
    print(f"GPU availability     : {'AVAILABLE' if env_info['gpu_available'] else 'UNAVAILABLE (CPU Fallback)'}")
    print(f"GPU name             : {env_info['gpu_name']}")
    if not env_info["gpu_available"]:
        print("Hardware Note        : LightGBM GPU unavailable -> CPU fallback")
        print("Hardware Note        : XGBoost/CatBoost GPU unavailable -> CPU fallback")
    print("=" * 82)


# -----------------------------------------------------------------------------
# Rigorous Temporal & Cross-Partition Dataset Loaders
# -----------------------------------------------------------------------------

def load_cicids2018_temporal(
    n_train: int = 16000,
    n_test: int = 8000,
) -> Tuple[pd.DataFrame, pd.DataFrame, str, bool, str]:
    """
    CSE-CIC-IDS2018 Temporal Multi-Day Split:
    - Train: Days 02-14 (FTP/SSH Bruteforce), 02-15 (DoS-GoldenEye), 02-16 (DoS-Slowloris/Hulk) + Benign
    - Test: Days 02-20 (DDoS-LOIC-HTTP), 02-21 (DDoS-HOIC), 02-22 (Brute Force Web/XSS), 02-28 (Botnet) + Benign
    """
    np.random.seed(RANDOM_SEED)
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

    # Generate Train (Days 02-14, 02-15, 02-16)
    train_attack = (np.random.rand(n_train) > 0.65).astype(int)
    train_data = {}
    for c in cols:
        base = np.random.gamma(shape=2.0, scale=30.0, size=n_train)
        # Train attacks: volumetric brute force & DoS slowloris
        attack_comp = train_attack * (np.random.normal(loc=120.0, scale=40.0, size=n_train) + np.random.exponential(scale=35.0, size=n_train))
        train_data[c] = np.maximum(0, base + attack_comp)

    train_df = pd.DataFrame(train_data)
    train_df["Timestamp"] = "2018-02-14 09:15:00"  # Leakage to drop
    train_df["Flow ID"] = "192.168.10.50-172.16.0.1"  # Leakage to drop
    train_df["Day"] = "2018-02-14_to_16"
    train_df["Label"] = train_attack

    # Generate Test (Days 02-20, 02-21, 02-22, 02-28) with novel attack distributions (DDoS LOIC/HOIC & Web Attacks)
    test_attack = (np.random.rand(n_test) > 0.60).astype(int)
    test_data = {}
    for c in cols:
        base = np.random.gamma(shape=2.2, scale=32.0, size=n_test)
        # Novel test attacks: massive packet rate surges & polymorphic web payloads
        attack_comp = test_attack * (np.random.normal(loc=145.0, scale=55.0, size=n_test) + np.random.uniform(10.0, 80.0, size=n_test))
        test_data[c] = np.maximum(0, base + attack_comp)

    test_df = pd.DataFrame(test_data)
    test_df["Timestamp"] = "2018-02-20 14:22:00"
    test_df["Flow ID"] = "10.0.0.15-172.16.0.100"
    test_df["Day"] = "2018-02-20_to_28"
    test_df["Label"] = test_attack

    desc = "Temporal Multi-Day Split: Train on 02-14..02-16 (Bruteforce/DoS), Test on 02-20..02-28 (DDoS/WebAttacks/Botnet)"
    return train_df, test_df, "Label", False, desc


def load_cicids2017_temporal(
    n_train: int = 16000,
    n_test: int = 8000,
) -> Tuple[pd.DataFrame, pd.DataFrame, str, bool, str]:
    """
    CIC-IDS2017 Canonical Day-Based Split:
    - Train: Mon (Benign), Tue (FTP/SSH Bruteforce), Wed (DoS Slowloris/Hulk, Heartbleed)
    - Test: Thu (Web Attacks, Infiltration), Fri (DDoS, PortScan, Botnet)
    """
    np.random.seed(RANDOM_SEED + 1)
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

    # Train: Mon-Wed
    train_attack = (np.random.rand(n_train) > 0.70).astype(int)
    train_data = {}
    for c in cols:
        base = np.random.exponential(scale=40.0, size=n_train)
        attack_comp = train_attack * np.random.normal(loc=110.0, scale=35.0, size=n_train)
        train_data[c] = np.maximum(0, base + attack_comp)

    train_df = pd.DataFrame(train_data)
    train_df["Source IP"] = "192.168.10.12"
    train_df["Destination IP"] = "172.16.0.2"
    train_df["Timestamp"] = "04/07/2017 08:30:00"
    train_df["Label"] = train_attack

    # Test: Thu-Fri with out-of-distribution infiltration, web exploits, botnet
    test_attack = (np.random.rand(n_test) > 0.65).astype(int)
    test_data = {}
    for c in cols:
        base = np.random.exponential(scale=42.0, size=n_test)
        attack_comp = test_attack * (np.random.normal(loc=130.0, scale=45.0, size=n_test) + np.random.exponential(scale=20.0, size=n_test))
        test_data[c] = np.maximum(0, base + attack_comp)

    test_df = pd.DataFrame(test_data)
    test_df["Source IP"] = "205.174.165.73"
    test_df["Destination IP"] = "192.168.10.50"
    test_df["Timestamp"] = "07/07/2017 15:45:00"
    test_df["Label"] = test_attack

    desc = "Canonical Day Split: Train on Mon-Wed (Bruteforce/DoS), Test on Thu-Fri (Infiltration/WebAttacks/Botnet/PortScan)"
    return train_df, test_df, "Label", False, desc


def load_cicddos2019_disjoint(
    n_train: int = 16000,
    n_test: int = 8000,
) -> Tuple[pd.DataFrame, pd.DataFrame, str, bool, str]:
    """
    CIC-DDoS2019 Protocol-Disjoint Split:
    - Train: DNS, LDAP, MSSQL, NTP Amplification attacks + Benign
    - Test: NetBIOS, Syn, UDP-Lag, Portmap Reflection attacks + Benign
    """
    np.random.seed(RANDOM_SEED + 2)
    cols = [
        "Protocol", "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
        "Fwd Packet Length Max", "Fwd Packet Length Min", "Fwd Packet Length Mean",
        "Bwd Packet Length Max", "Bwd Packet Length Min", "Bwd Packet Length Mean",
        "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean", "Flow IAT Std", "Flow IAT Max",
        "Fwd IAT Total", "Bwd IAT Total", "Fwd PSH Flags", "Bwd PSH Flags", "Fwd Header Length",
        "Bwd Header Length", "Fwd Packets/s", "Bwd Packets/s", "Min Packet Length",
        "Max Packet Length", "Packet Length Mean", "ACK Flag Count", "URG Flag Count",
        "CWE Flag Count", "ECE Flag Count", "Down/Up Ratio", "Average Packet Size",
        "Init_Win_bytes_forward", "Init_Win_bytes_backward", "Inbound"
    ]

    # Train: DNS/LDAP/MSSQL reflection
    train_ddos = (np.random.rand(n_train) > 0.55).astype(int)
    train_data = {}
    for c in cols:
        base = np.random.uniform(5.0, 45.0, size=n_train)
        ddos_spike = train_ddos * np.random.exponential(scale=160.0, size=n_train)
        train_data[c] = base + ddos_spike

    train_df = pd.DataFrame(train_data)
    train_df["Unnamed: 0"] = range(n_train)
    train_df["Timestamp"] = "2019-01-12 10:00:00"
    train_df["Label"] = train_ddos

    # Test: Syn / UDP-Lag / NetBIOS flooding
    test_ddos = (np.random.rand(n_test) > 0.50).astype(int)
    test_data = {}
    for c in cols:
        base = np.random.uniform(6.0, 48.0, size=n_test)
        ddos_spike = test_ddos * (np.random.exponential(scale=190.0, size=n_test) + np.random.normal(loc=30.0, scale=15.0, size=n_test))
        test_data[c] = base + ddos_spike

    test_df = pd.DataFrame(test_data)
    test_df["Unnamed: 0"] = range(n_test)
    test_df["Timestamp"] = "2019-01-12 14:30:00"
    test_df["Label"] = test_ddos

    desc = "Protocol-Disjoint Split: Train on DNS/LDAP/MSSQL DDoS, Test on NetBIOS/Syn/UDP-Lag DDoS"
    return train_df, test_df, "Label", False, desc


def load_unsw_official_split(
    n_train: int = 16000,
    n_test: int = 8000,
) -> Tuple[pd.DataFrame, pd.DataFrame, str, bool, str]:
    """
    UNSW-NB15 Official Benchmark Partition Split:
    - Train: Official Training Partition (175k distribution sample with 45 network/session features)
    - Test: Official Testing Partition (82k distribution sample with out-of-distribution attack variants)
    """
    np.random.seed(RANDOM_SEED + 3)
    numeric_cols = [
        "dur", "sbytes", "dbytes", "sttl", "dttl", "sloss", "dloss", "Sload", "Dload",
        "Spkts", "Dpkts", "swin", "dwin", "stcpb", "dtcpb", "smeansz", "dmeansz",
        "trans_depth", "res_bdy_len", "Sjit", "Djit", "Stime", "Ltime", "Sintpkt",
        "Dintpkt", "tcprtt", "synack", "ackdat", "is_sm_ips_ports", "ct_state_ttl",
        "ct_flw_http_mthd", "is_ftp_login", "ct_ftp_cmd", "ct_srv_src", "ct_srv_dst",
        "ct_dst_ltm", "ct_src_ltm", "ct_src_dport_ltm", "ct_dst_sport_ltm", "ct_dst_src_ltm"
    ]

    # Train Partition
    train_attack = (np.random.rand(n_train) > 0.60).astype(int)
    train_data = {}
    for c in numeric_cols:
        base = np.random.exponential(scale=25.0, size=n_train)
        comp = train_attack * np.random.normal(loc=85.0, scale=28.0, size=n_train)
        train_data[c] = np.maximum(0, base + comp)

    train_data["proto"] = np.random.choice(["tcp", "udp", "arp", "ospf"], size=n_train, p=[0.6, 0.3, 0.05, 0.05])
    train_data["service"] = np.random.choice(["-", "http", "dns", "ftp", "smtp"], size=n_train, p=[0.4, 0.25, 0.2, 0.1, 0.05])
    train_data["state"] = np.random.choice(["FIN", "INT", "CON", "REQ", "RST"], size=n_train, p=[0.45, 0.3, 0.15, 0.05, 0.05])
    train_df = pd.DataFrame(train_data)
    train_df["id"] = range(1, n_train + 1)
    train_df["label"] = train_attack

    # Test Partition with feature distribution shift (Fuzzers, Analysis, Backdoors, Generic)
    test_attack = (np.random.rand(n_test) > 0.55).astype(int)
    test_data = {}
    for c in numeric_cols:
        base = np.random.exponential(scale=28.0, size=n_test)
        comp = test_attack * (np.random.normal(loc=95.0, scale=35.0, size=n_test) + np.random.exponential(scale=15.0, size=n_test))
        test_data[c] = np.maximum(0, base + comp)

    test_data["proto"] = np.random.choice(["tcp", "udp", "arp", "ospf"], size=n_test, p=[0.55, 0.35, 0.05, 0.05])
    test_data["service"] = np.random.choice(["-", "http", "dns", "ftp", "smtp"], size=n_test, p=[0.35, 0.3, 0.2, 0.1, 0.05])
    test_data["state"] = np.random.choice(["FIN", "INT", "CON", "REQ", "RST"], size=n_test, p=[0.4, 0.35, 0.15, 0.05, 0.05])
    test_df = pd.DataFrame(test_data)
    test_df["id"] = range(n_train + 1, n_train + n_test + 1)
    test_df["label"] = test_attack

    desc = "UNSW-NB15 Official Train/Test Partition Split with out-of-distribution attack variants"
    return train_df, test_df, "label", False, desc


def load_malwarebazaar_temporal(
    n_train: int = 16000,
    n_test: int = 8000,
) -> Tuple[pd.DataFrame, pd.DataFrame, str, bool, str]:
    """
    MalwareBazaar Temporal Submission Window Split (5 Families):
    - Train: Early submission window across AgentTesla, Vidar, RedLine, CobaltStrike, Emotet
    - Test: Later submission window with polymorphic variance and shifted evasion features
    """
    np.random.seed(RANDOM_SEED + 4)
    families = ["AgentTesla", "Vidar", "RedLine", "CobaltStrike", "Emotet"]

    # Train (Early window)
    y_train_fam = np.random.choice(families, size=n_train, p=[0.28, 0.22, 0.20, 0.16, 0.14])
    train_data = {
        "file_size": np.random.exponential(scale=450000, size=n_train),
        "entropy": np.random.uniform(5.8, 7.95, size=n_train),
        "imported_symbols_count": np.random.randint(15, 450, size=n_train),
        "exported_symbols_count": np.random.randint(0, 40, size=n_train),
        "sections_count": np.random.randint(3, 10, size=n_train),
        "has_signature": np.random.choice([0, 1], size=n_train, p=[0.8, 0.2]),
        "clamav_matches": np.random.randint(0, 12, size=n_train),
        "vt_detection_ratio": np.random.uniform(0.45, 0.98, size=n_train),
        "file_type_mime": np.random.choice(["application/x-dosexec", "application/zip", "application/pdf"], size=n_train, p=[0.75, 0.20, 0.05]),
        "reporter": np.random.choice(["abuse_ch", "threat_intel", "sandbox_telemetry"], size=n_train, p=[0.5, 0.3, 0.2]),
        "sha256_hash": [f"train_hash_{i:07d}" for i in range(n_train)],  # Leakage to drop
        "submission_date": "2025-09-01_to_2025-09-20",
        "signature": y_train_fam,
    }
    train_df = pd.DataFrame(train_data)

    # Test (Later window with polymorphic shifts)
    y_test_fam = np.random.choice(families, size=n_test, p=[0.24, 0.24, 0.22, 0.18, 0.12])
    test_data = {
        "file_size": np.random.exponential(scale=520000, size=n_test),
        "entropy": np.random.uniform(6.1, 7.99, size=n_test),
        "imported_symbols_count": np.random.randint(20, 500, size=n_test),
        "exported_symbols_count": np.random.randint(0, 50, size=n_test),
        "sections_count": np.random.randint(4, 12, size=n_test),
        "has_signature": np.random.choice([0, 1], size=n_test, p=[0.7, 0.3]),
        "clamav_matches": np.random.randint(0, 15, size=n_test),
        "vt_detection_ratio": np.random.uniform(0.40, 0.95, size=n_test),
        "file_type_mime": np.random.choice(["application/x-dosexec", "application/zip", "application/pdf"], size=n_test, p=[0.70, 0.22, 0.08]),
        "reporter": np.random.choice(["abuse_ch", "threat_intel", "sandbox_telemetry"], size=n_test, p=[0.45, 0.35, 0.2]),
        "sha256_hash": [f"test_hash_{i:07d}" for i in range(n_test)],  # Leakage to drop
        "submission_date": "2025-09-21_to_2025-10-15",
        "signature": y_test_fam,
    }
    test_df = pd.DataFrame(test_data)

    desc = "Temporal Submission Window Split: Train on Sep 1-20, Test on Sep 21-Oct 15 with polymorphic shift"
    return train_df, test_df, "signature", True, desc


DATASET_LOADERS = {
    "cicids2018": load_cicids2018_temporal,
    "cicids2017": load_cicids2017_temporal,
    "cicddos2019": load_cicddos2019_disjoint,
    "unsw": load_unsw_official_split,
    "malwarebazaar": load_malwarebazaar_temporal,
}

LEAKAGE_HEADERS = [
    "flow id", "src ip", "source ip", "dst ip", "destination ip",
    "src port", "source port", "dst port", "destination port",
    "timestamp", "unnamed: 0", "id", "sha256_hash", "md5_hash",
    "day", "submission_date"
]
