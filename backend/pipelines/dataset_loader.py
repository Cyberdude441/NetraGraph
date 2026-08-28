import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

SUPPORTED_SUFFIXES = {".csv", ".json", ".jsonl", ".txt"}


def load_records(path: Path) -> Iterable[Dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            yield from csv.DictReader(handle)
        return
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    value = json.loads(line)
                    yield value if isinstance(value, dict) else {"text": str(value)}
        return
    if path.suffix.lower() == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, list):
            yield from (item if isinstance(item, dict) else {"text": str(item)} for item in value)
        elif isinstance(value, dict):
            yield value
        return
    yield {"text": path.read_text(encoding="utf-8", errors="replace")}


def iter_dataset_records(root: Path, dataset: str) -> Iterable[Dict[str, Any]]:
    directory = root / "raw" / dataset
    if not directory.exists():
        return
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            for index, record in enumerate(load_records(path), start=1):
                record.setdefault("_source_file", path.name)
                record.setdefault("_record_id", f"{path.stem}:{index}")
                yield record
