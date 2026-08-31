"""Schema and target discovery, with a report suitable for training reports."""
from __future__ import annotations

from collections import Counter
from typing import Any

TARGET_NAMES = ("target", "label", "class", "y", "is_malicious", "malicious", "category", "attack_detected", "status")


def detect_target(columns: list[str], explicit: str | None = None) -> str:
    if explicit:
        if explicit not in columns:
            raise ValueError(f"Target column not found: {explicit}")
        return explicit
    lowered = {column.lower(): column for column in columns}
    for candidate in TARGET_NAMES:
        if candidate in lowered:
            return lowered[candidate]
    raise ValueError("No target column detected; pass --target explicitly")


def schema_report(records: list[dict[str, Any]], target: str | None = None) -> dict[str, Any]:
    if not records:
        raise ValueError("Dataset contains no records")
    columns = sorted({key for record in records for key in record})
    target_column = detect_target(columns, target)
    values = [record.get(target_column) for record in records]
    return {
        "columns": columns,
        "target_column": target_column,
        "missing_values": {column: sum(record.get(column) in (None, "") for record in records) for column in columns},
        "duplicates": len(records) - len({jsonable(record) for record in records}),
        "class_distribution": dict(Counter(str(value) for value in values)),
    }


def jsonable(record: dict[str, Any]) -> str:
    import json
    return json.dumps(record, sort_keys=True, default=str)
