from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from database.neo4j import neo4j_db
from pipelines.cyber_extractors import extract_entities
from pipelines.dataset_loader import iter_dataset_records
from pipelines.graph_converter import build_relationships
from pipelines.normalizer import normalize_record

DATASET_NAMES = ("intrusion", "network", "phishing", "email", "threat_reports", "global_threats")
DATASET_ALIASES = {
    "cybersecurity_intrusion": "intrusion",
    "network_intrusion": "network",
    "phishing_url": "phishing",
    "phishing_email": "email",
    "nlp_security": "threat_reports",
    "global_cybersecurity_threats": "global_threats",
}


class CyberDatasetPipeline:
    def __init__(self, dataset_root: Path | None = None):
        self.dataset_root = dataset_root or Path(__file__).resolve().parents[1] / "datasets"

    def ingest(self, dataset: str) -> Dict[str, Any]:
        dataset = DATASET_ALIASES.get(dataset, dataset)
        if dataset not in DATASET_NAMES:
            raise ValueError(f"Unsupported dataset: {dataset}. Choose from {', '.join(DATASET_NAMES)}")
        records_read = records_processed = skipped = 0
        warnings: List[str] = []
        entity_count = relationship_count = 0
        processed_records: List[Dict[str, Any]] = []
        for record in iter_dataset_records(self.dataset_root, dataset):
            records_read += 1
            record = normalize_record(record)
            entities = extract_entities(record, dataset)
            if not entities:
                skipped += 1
                continue
            relationships = build_relationships(entities, dataset, str(record["_record_id"]))
            for entity in entities:
                neo4j_db.add_cyber_node(entity.model_dump(mode="json"))
            for relationship in relationships:
                neo4j_db.add_cyber_relationship(relationship.model_dump(mode="json"))
            records_processed += 1
            processed_records.append(record)
            entity_count += len(entities)
            relationship_count += len(relationships)
        neo4j_db.cyber_last_sync = datetime.utcnow().isoformat() + "Z"
        processed_path = self.dataset_root / "processed" / f"{dataset}.json"
        processed_path.parent.mkdir(parents=True, exist_ok=True)
        processed_path.write_text(json.dumps(processed_records, indent=2), encoding="utf-8")
        return {
            "dataset": dataset,
            "records_read": records_read,
            "records_processed": records_processed,
            "entities_created": entity_count,
            "relationships_created": relationship_count,
            "skipped_records": skipped,
            "warnings": warnings,
        }

    def ingest_all(self) -> Dict[str, Any]:
        results = [self.ingest(dataset) for dataset in DATASET_NAMES]
        return {
            "datasets": results,
            "records_read": sum(item["records_read"] for item in results),
            "entities_created": sum(item["entities_created"] for item in results),
            "relationships_created": sum(item["relationships_created"] for item in results),
        }


cyber_dataset_pipeline = CyberDatasetPipeline()
