"""Hardware, Memory, and Safe ZIP Inspection Utilities for UNSW-NB15."""
from __future__ import annotations

import hashlib
import os
import platform
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil


def detect_hardware(requested_device: str = "auto") -> Dict[str, any]:
    """Inspects NVIDIA CUDA availability and determines optimal training device."""
    requested_device = requested_device.lower()
    cuda_available = False
    gpu_name = "None"
    device_count = 0

    # 1. Try PyTorch CUDA if available
    try:
        import torch
        if torch.cuda.is_available():
            cuda_available = True
            device_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
    except ImportError:
        pass

    # 2. Try nvidia-smi fallback
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
    """Prints formatted hardware status banner as required by pipeline specs."""
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


def inspect_and_extract_zip(
    zip_path: Path,
    target_extract_dir: Optional[Path] = None,
    extract_csv_only: bool = True,
) -> List[Path]:
    """Inspects ZIP archive without extracting PCAP files.
    Safely extracts only tabular CSV files to conserve disk and RAM.
    """
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        raise FileNotFoundError(f"ZIP archive not found: {zip_path}")

    extract_dir = target_extract_dir or zip_path.with_suffix("")
    extract_dir.mkdir(parents=True, exist_ok=True)

    extracted_csvs: List[Path] = []

    print(f"\n[ZIP Audit] Inspecting archive: {zip_path.name} ({zip_path.stat().st_size / (1024**2):.1f} MB)")
    with zipfile.ZipFile(zip_path, "r") as archive:
        all_members = archive.infolist()
        csv_members = [m for m in all_members if m.filename.lower().endswith(".csv")]
        pcap_members = [m for m in all_members if m.filename.lower().endswith((".pcap", ".cap", ".bin"))]

        print(f"  Found {len(all_members)} total files in archive:")
        print(f"    - {len(csv_members)} CSV dataset files")
        print(f"    - {len(pcap_members)} PCAP / Packet Capture files (Skipping extraction to save RAM)")

        for member in csv_members:
            dest_file = extract_dir / Path(member.filename).name
            if not dest_file.exists():
                print(f"  Extracting CSV: {member.filename} ({member.file_size / (1024**2):.2f} MB)...")
                with archive.open(member) as source, open(dest_file, "wb") as target:
                    target.write(source.read())
            extracted_csvs.append(dest_file)

    return sorted(extracted_csvs)


def calculate_sha256(file_path: str | Path) -> str:
    """Calculates SHA-256 checksum of a file."""
    path = Path(file_path)
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()
