"""Hardware, Memory, and High-Performance Parquet Storage Utilities."""
from __future__ import annotations

import hashlib
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import psutil


def detect_hardware(requested_device: str = "auto") -> Dict[str, any]:
    """Inspects NVIDIA CUDA availability and determines optimal training device."""
    requested_device = requested_device.lower()
    cuda_available = False
    gpu_name = "None"
    device_count = 0

    # 1. Check PyTorch CUDA
    try:
        import torch
        if torch.cuda.is_available():
            cuda_available = True
            device_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
    except ImportError:
        pass

    # 2. Check nvidia-smi
    if not cuda_available:
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=gpu_name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout.strip():
                lines = res.stdout.strip().splitlines()
                gpu_name = lines[0].split(",")[0].strip()
                cuda_available = True
                device_count = len(lines)
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            pass

    # Determine execution device
    if requested_device == "gpu":
        if cuda_available:
            training_device = "GPU"
        else:
            print("  [WARN] GPU requested but no CUDA device detected. Falling back to CPU.")
            training_device = "CPU"
    elif requested_device == "cpu":
        training_device = "CPU"
    else:  # auto
        training_device = "GPU" if cuda_available else "CPU"

    return {
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
        "device_count": device_count,
        "training_device": training_device,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": psutil.cpu_count(logical=True),
    }


def print_hardware_status(info: Dict[str, any]) -> None:
    """Prints formatted hardware status banner."""
    print("--------------------------------------------------")
    print(f"GPU available    : {info['cuda_available']}")
    print(f"GPU name         : {info['gpu_name']}")
    print(f"CUDA availability: {info['cuda_available']}")
    print(f"training device  : {info['training_device']}")
    print(f"System CPU Cores : {info['cpu_count']}")
    print(f"RAM Available    : {get_memory_usage()}")
    print("--------------------------------------------------")


def get_memory_usage() -> str:
    """Returns human-readable RAM usage information."""
    mem = psutil.virtual_memory()
    total_gb = mem.total / (1024 ** 3)
    available_gb = mem.available / (1024 ** 3)
    used_gb = mem.used / (1024 ** 3)
    return f"{used_gb:.2f} GB used / {total_gb:.2f} GB total ({available_gb:.2f} GB available)"


def save_parquet_cache(df: pd.DataFrame, cache_path: Path) -> Path:
    """Caches large preprocessed DataFrame to snappy-compressed Parquet for ultra-fast reloading."""
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[Parquet Cache] Caching {len(df):,} rows to {cache_path}...")
    df.to_parquet(cache_path, engine="pyarrow", compression="snappy", index=False)
    print(f"[Parquet Cache] Cache persisted ({cache_path.stat().st_size / (1024**2):.1f} MB).")
    return cache_path


def load_parquet_cache(cache_path: Path) -> Optional[pd.DataFrame]:
    """Loads cached Parquet dataset if available."""
    cache_path = Path(cache_path)
    if cache_path.exists():
        print(f"[Parquet Cache] Loading cached Parquet dataset from: {cache_path}...")
        return pd.read_parquet(cache_path, engine="pyarrow")
    return None


def calculate_sha256(file_path: str | Path) -> str:
    """Calculates SHA-256 checksum of a file."""
    path = Path(file_path)
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()
