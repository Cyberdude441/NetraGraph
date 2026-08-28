from typing import Any, Dict


def clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        str(key).strip().lower().replace(" ", "_"): str(value).strip()
        for key, value in record.items()
        if value is not None and str(value).strip()
    }


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    normalized = clean_record(record)
    normalized["_record_id"] = str(record.get("_record_id", "unknown"))
    normalized["_source_file"] = str(record.get("_source_file", "unknown"))
    return normalized
