"""Dedicated NCRB Dynamic Synchronization Service with Deterministic MERGE and Full Provenance."""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from database.neo4j import neo4j_db
    from app.connectors.ogd_ncrb_connector import ogd_connector, OGD_DATASET_CONFIGS, normalize_state_name
except ImportError:
    from ..database.neo4j import neo4j_db
    from ..app.connectors.ogd_ncrb_connector import ogd_connector, OGD_DATASET_CONFIGS, normalize_state_name

logger = logging.getLogger("NCRBSyncService")


class NCRBSyncService:
    """
    Dedicated NCRB Synchronization Service.
    
    Data Path:
      NCRB / data.gov.in -> Validation -> Normalization -> Provenance -> Deterministic IDs -> Neo4j MERGE -> Graph
    """

    def generate_deterministic_id(self, prefix: str, *components: Any) -> str:
        """Generates deterministic, collision-resistant identifier for graph entities."""
        raw_str = ":".join(str(c).strip().upper() for c in components)
        digest = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:12].upper()
        return f"{prefix}-{digest}"

    async def synchronize_ncrb_datasets(self) -> Dict[str, Any]:
        """
        Executes full deterministic synchronization of all 6 NCRB datasets.
        Guarantees 100% idempotency across repeated runs.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        stats = {
            "status": "success",
            "datasets_processed": 0,
            "records_processed": 0,
            "nodes_created": 0,
            "nodes_updated": 0,
            "relationships_created": 0,
            "duplicates_skipped": 0,
            "errors": 0,
            "synced_at": now_iso,
        }

        try:
            # 1. Base Dataset & Year Nodes
            neo4j_db.add_ncrb_node(
                node_id="DATASET-NCRB-CORE",
                label="Dataset",
                name="NCRB Open Government Data (data.gov.in)",
                source="NCRB",
                source_url="https://data.gov.in/catalogs/?sector=Crime",
                dataset_name="NCRB Crime in India Official Catalog",
                dataset_year=2025,
                resource_id="ncrb-core-catalog",
                retrieved_at=now_iso,
                jurisdiction="National (India)",
            )
            stats["nodes_created"] += 1

            for yr in [2023, 2024, 2025]:
                neo4j_db.add_ncrb_node(
                    node_id=f"YEAR-{yr}",
                    label="Year",
                    name=f"Year {yr}",
                    year=yr,
                    source="NCRB",
                    source_url="https://data.gov.in",
                    dataset_name="NCRB Annual Survey",
                    dataset_year=yr,
                    resource_id=f"year-{yr}",
                    retrieved_at=now_iso,
                    jurisdiction="National (India)",
                )
                stats["nodes_created"] += 1

            # 2. Iterate through all configured OGD datasets
            for cfg in OGD_DATASET_CONFIGS:
                dataset_id = cfg["id"]
                records = await ogd_connector.fetch_dataset_live(cfg)
                stats["datasets_processed"] += 1
                stats["records_processed"] += len(records)

                # Process specific dataset schemas
                if dataset_id == "ogd-it-act":
                    self._process_it_act_records(records, cfg, now_iso, stats)
                elif dataset_id in ["ogd-motives-2019", "ogd-motives-2020"]:
                    self._process_motive_records(records, cfg, now_iso, stats)
                elif dataset_id == "ogd-police-disposal":
                    self._process_police_disposal_records(records, cfg, now_iso, stats)
                elif dataset_id == "ogd-court-disposal":
                    self._process_court_disposal_records(records, cfg, now_iso, stats)
                elif dataset_id == "ogd-arrest-disposal":
                    self._process_arrest_records(records, cfg, now_iso, stats)

            # Record timestamp in Neo4j database instance
            neo4j_db.ncrb_last_sync = now_iso

        except Exception as e:
            logger.error(f"[NCRBSyncService] Synchronization error: {e}", exc_info=True)
            stats["errors"] += 1
            stats["status"] = "error"
            stats["error_detail"] = str(e)

        return stats

    def _process_it_act_records(self, records: List[Dict[str, Any]], cfg: Dict[str, Any], now_iso: str, stats: Dict[str, Any]):
        for r in records:
            sec_name = r.get("Section") or r.get("Offense") or "IT Act Section"
            cat_id = self.generate_deterministic_id("CAT", sec_name)

            neo4j_db.add_ncrb_node(
                node_id=cat_id,
                label="CrimeCategory",
                name=sec_name,
                act=r.get("Act", "IT Act"),
                cases2023=r.get("Cases_2023", 0),
                cases2024=r.get("Cases_2024", 0),
                cases2025=r.get("Cases_2025", 0),
                chargesheet_rate=r.get("Chargesheet_Rate", 0.0),
                conviction_rate=r.get("Conviction_Rate", 0.0),
                source="NCRB",
                source_url=cfg["source_url"],
                dataset_name=cfg["name"],
                dataset_year=2025,
                resource_id=cfg["resource_id"],
                retrieved_at=now_iso,
                jurisdiction="National (India)",
            )
            stats["nodes_created"] += 1

            # Connect Dataset -> CONTAINS -> CrimeCategory
            rel_id = f"REL-DS-CAT-{cat_id}"
            neo4j_db.add_ncrb_relationship(
                rel_id=rel_id,
                source_id="DATASET-NCRB-CORE",
                target_id=cat_id,
                rel_type="CONTAINS_CATEGORY",
                metadata={"cases_2025": r.get("Cases_2025", 0)},
            )
            stats["relationships_created"] += 1

            # Connect CrimeCategory -> FOR_YEAR -> Year 2025
            rel_yr_id = f"REL-CAT-YR-{cat_id}-2025"
            neo4j_db.add_ncrb_relationship(
                rel_id=rel_yr_id,
                source_id=cat_id,
                target_id="YEAR-2025",
                rel_type="FOR_YEAR",
                metadata={"cases": r.get("Cases_2025", 0)},
            )
            stats["relationships_created"] += 1

    def _process_motive_records(self, records: List[Dict[str, Any]], cfg: Dict[str, Any], now_iso: str, stats: Dict[str, Any]):
        for r in records:
            motive_name = r.get("Motive") or r.get("Crime_Motive") or "General Motive"
            motive_id = self.generate_deterministic_id("MOTIVE", motive_name)

            neo4j_db.add_ncrb_node(
                node_id=motive_id,
                label="CrimeMotive",
                name=motive_name,
                category=r.get("Category", "General"),
                cases=r.get("Cases", 0),
                percentage=r.get("Percentage", 0.0),
                risk_level=r.get("Risk_Level", "MODERATE"),
                source="NCRB",
                source_url=cfg["source_url"],
                dataset_name=cfg["name"],
                dataset_year=int(cfg.get("year", 2025)) if cfg.get("year", "2025").isdigit() else 2025,
                resource_id=cfg["resource_id"],
                retrieved_at=now_iso,
                jurisdiction="National (India)",
            )
            stats["nodes_created"] += 1

            rel_id = f"REL-DS-MOTIVE-{motive_id}"
            neo4j_db.add_ncrb_relationship(
                rel_id=rel_id,
                source_id="DATASET-NCRB-CORE",
                target_id=motive_id,
                rel_type="CLASSIFIES_MOTIVE",
                metadata={"percentage": r.get("Percentage", 0.0)},
            )
            stats["relationships_created"] += 1

    def _process_police_disposal_records(self, records: List[Dict[str, Any]], cfg: Dict[str, Any], now_iso: str, stats: Dict[str, Any]):
        for r in records:
            head = r.get("Crime_Head") or "Cyber Crime Head"
            disp_id = self.generate_deterministic_id("POLICE", head)

            neo4j_db.add_ncrb_node(
                node_id=disp_id,
                label="PoliceDisposal",
                name=f"Police Disposal: {head}",
                crime_head=head,
                total_investigated=r.get("Total_Investigated", 0),
                disposed_by_police=r.get("Disposed_By_Police", 0),
                chargesheeted=r.get("Chargesheeted", 0),
                pending_investigation=r.get("Pending_Investigation", 0),
                chargesheet_rate=r.get("Chargesheet_Rate", 0.0),
                source="NCRB",
                source_url=cfg["source_url"],
                dataset_name=cfg["name"],
                dataset_year=2025,
                resource_id=cfg["resource_id"],
                retrieved_at=now_iso,
                jurisdiction="National (India)",
            )
            stats["nodes_created"] += 1

    def _process_court_disposal_records(self, records: List[Dict[str, Any]], cfg: Dict[str, Any], now_iso: str, stats: Dict[str, Any]):
        for r in records:
            head = r.get("Crime_Head") or "Cyber Crime Head"
            court_id = self.generate_deterministic_id("COURT", head)

            neo4j_db.add_ncrb_node(
                node_id=court_id,
                label="CourtOutcome",
                name=f"Judicial Outcomes: {head}",
                crime_head=head,
                total_trials=r.get("Total_Trials", 0),
                disposed_by_courts=r.get("Disposed_By_Courts", 0),
                convicted=r.get("Convicted", 0),
                acquitted=r.get("Acquitted", 0),
                pending_trial=r.get("Pending_Trial", 0),
                conviction_rate=r.get("Conviction_Rate", 0.0),
                source="NCRB",
                source_url=cfg["source_url"],
                dataset_name=cfg["name"],
                dataset_year=2025,
                resource_id=cfg["resource_id"],
                retrieved_at=now_iso,
                jurisdiction="National (India)",
            )
            stats["nodes_created"] += 1

    def _process_arrest_records(self, records: List[Dict[str, Any]], cfg: Dict[str, Any], now_iso: str, stats: Dict[str, Any]):
        for r in records:
            head = r.get("Crime_Head") or "Cyber Crime Head"
            arr_id = self.generate_deterministic_id("ARREST", head)

            neo4j_db.add_ncrb_node(
                node_id=arr_id,
                label="CrimeStatistic",
                name=f"Arrest Breakdown: {head}",
                crime_head=head,
                persons_arrested=r.get("Persons_Arrested", 0),
                persons_chargesheeted=r.get("Persons_Chargesheeted", 0),
                persons_convicted=r.get("Persons_Convicted", 0),
                persons_acquitted=r.get("Persons_Acquitted", 0),
                source="NCRB",
                source_url=cfg["source_url"],
                dataset_name=cfg["name"],
                dataset_year=2025,
                resource_id=cfg["resource_id"],
                retrieved_at=now_iso,
                jurisdiction="National (India)",
            )
            stats["nodes_created"] += 1


# Global Singleton Instance
ncrb_sync_service = NCRBSyncService()
