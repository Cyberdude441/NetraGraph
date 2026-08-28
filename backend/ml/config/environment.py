"""Centralized, portable paths for local, Colab, and Kaggle execution."""
from __future__ import annotations

import os
import sys
from enum import Enum
from pathlib import Path


class RuntimeEnvironment(str, Enum):
    LOCAL_PROJECT = "LOCAL_PROJECT"
    GOOGLE_COLAB = "GOOGLE_COLAB"
    KAGGLE = "KAGGLE"


def detect_environment() -> RuntimeEnvironment:
    if os.environ.get("KAGGLE_KERNEL_RUN_TYPE") or Path("/kaggle/input").is_dir():
        return RuntimeEnvironment.KAGGLE
    if "google.colab" in sys.modules or os.environ.get("COLAB_RELEASE_TAG"):
        return RuntimeEnvironment.GOOGLE_COLAB
    return RuntimeEnvironment.LOCAL_PROJECT


def project_root() -> Path:
    configured = os.environ.get("NETRAGRAPH_PROJECT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    here = Path(__file__).resolve()
    return next((parent for parent in here.parents if (parent / "backend").is_dir()), Path.cwd())


def data_root() -> Path:
    env = detect_environment()
    if env == RuntimeEnvironment.KAGGLE:
        return Path("/kaggle/input")
    if env == RuntimeEnvironment.GOOGLE_COLAB:
        return Path("content/data")
    return project_root() / "backend" / "datasets"


def output_root() -> Path:
    env = detect_environment()
    if env == RuntimeEnvironment.KAGGLE:
        return Path("/kaggle/working")
    if env == RuntimeEnvironment.GOOGLE_COLAB:
        return Path("content/artifacts")
    return project_root() / "artifacts"


def registry_root() -> Path:
    return project_root() / "backend" / "models" / "registry"
