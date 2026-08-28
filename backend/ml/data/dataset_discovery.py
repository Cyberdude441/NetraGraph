"""Format-aware recursive dataset discovery and safe ZIP extraction."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

SUPPORTED = {".csv", ".json", ".jsonl", ".txt"}


def extract_zips(root: Path) -> list[Path]:
    extracted: list[Path] = []
    for archive in root.rglob("*.zip"):
        destination = archive.with_suffix("")
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as handle:
            base = destination.resolve()
            for member in handle.infolist():
                target = (destination / member.filename).resolve()
                if target != base and base not in target.parents:
                    raise ValueError(f"Unsafe ZIP member: {member.filename}")
            handle.extractall(destination)
        extracted.append(destination)
    return extracted


def discover_files(root: str | Path, extract_archives: bool = True) -> list[Path]:
    path = Path(root)
    if extract_archives:
        extract_zips(path)
    return sorted(file for file in path.rglob("*") if file.is_file() and file.suffix.lower() in SUPPORTED)


def fingerprint(files: list[Path]) -> str:
    digest = hashlib.sha256()
    for file in files:
        digest.update(str(file.name).encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()


def detect_encoding(path: Path) -> str:
    sample = path.read_bytes()[:100_000]
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "latin-1"):
        try:
            sample.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "latin-1"


def read_records(path: Path) -> list[dict[str, Any]]:
    import pandas as pd
    encoding = detect_encoding(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, encoding=encoding).to_dict(orient="records")
    if suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding=encoding).splitlines() if line.strip()]
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding=encoding))
        return payload if isinstance(payload, list) else [payload]
    return [{"text": line.rstrip("\n")} for line in path.read_text(encoding=encoding).splitlines() if line.strip()]
