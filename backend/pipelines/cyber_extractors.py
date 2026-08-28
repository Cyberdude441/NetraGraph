import hashlib
import re
from typing import Any, Dict, Iterable, List

from app.models.cyber_intelligence import CyberEntity, CyberEntityType

PATTERNS = {
    CyberEntityType.IP_ADDRESS: re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    CyberEntityType.DOMAIN: re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b", re.I),
    CyberEntityType.URL: re.compile(r"https?://[^\s,<>\"]+", re.I),
    CyberEntityType.EMAIL_ADDRESS: re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b", re.I),
    CyberEntityType.VULNERABILITY: re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I),
    CyberEntityType.HASH: re.compile(r"\b[a-f0-9]{32}\b|\b[a-f0-9]{40}\b|\b[a-f0-9]{64}\b", re.I),
}

KEYWORD_TYPES = {
    "malware": CyberEntityType.MALWARE,
    "ransomware": CyberEntityType.MALWARE,
    "trojan": CyberEntityType.MALWARE,
    "phishing": CyberEntityType.ATTACK_TYPE,
    "ddos": CyberEntityType.ATTACK_TYPE,
    "credential theft": CyberEntityType.ATTACK_TYPE,
}


def _entity_id(entity_type: CyberEntityType, value: str) -> str:
    digest = hashlib.sha1(value.lower().encode("utf-8")).hexdigest()[:12].upper()
    return f"CYBER-{entity_type.value.upper()}-{digest}"


def extract_entities(record: Dict[str, Any], dataset: str) -> List[CyberEntity]:
    text = " ".join(str(value) for key, value in record.items() if not key.startswith("_"))
    found: Dict[tuple[CyberEntityType, str], CyberEntity] = {}
    for entity_type, pattern in PATTERNS.items():
        for match in pattern.findall(text):
            value = match.rstrip(".,)")
            found[(entity_type, value.lower())] = CyberEntity(
                id=_entity_id(entity_type, value),
                name=value,
                type=entity_type,
                risk_score=80 if entity_type in {CyberEntityType.URL, CyberEntityType.DOMAIN, CyberEntityType.HASH} else 60,
                confidence=0.9,
                source_dataset=dataset,
                source_record_id=str(record["_record_id"]),
                attributes={"source_file": record["_source_file"]},
            )
    lowered = text.lower()
    for keyword, entity_type in KEYWORD_TYPES.items():
        if keyword in lowered:
            found[(entity_type, keyword)] = CyberEntity(
                id=_entity_id(entity_type, keyword),
                name=keyword.title(),
                type=entity_type,
                risk_score=75,
                confidence=0.72,
                source_dataset=dataset,
                source_record_id=str(record["_record_id"]),
                attributes={"source_file": record["_source_file"], "extraction": "keyword"},
            )
    return list(found.values())
