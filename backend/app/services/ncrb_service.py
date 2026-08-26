import csv
import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Base directory for NCRB CSV datasets
BASE_DIR = Path(__file__).resolve().parent.parent.parent
NCRB_DATA_DIR = BASE_DIR / "data" / "ncrb"


class NCRBService:
    """
    Service for parsing, normalizing, and calculating real-time statistics
    from National Crime Records Bureau (NCRB) datasets.
    """

    def __init__(self):
        self.statewise_file = NCRB_DATA_DIR / "ncrb_cyber_crime_statewise.csv"
        self.categories_file = NCRB_DATA_DIR / "ncrb_cyber_crime_categories.csv"
        self.sections_file = NCRB_DATA_DIR / "ncrb_it_act_sections.csv"
        self._custom_datasets: List[Dict[str, Any]] = []

    def get_statewise_data(self) -> List[Dict[str, Any]]:
        """Parse state/UT cyber crime statistics."""
        if not self.statewise_file.exists():
            return []

        results = []
        with open(self.statewise_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append({
                    "state": row.get("State_UT", "").strip(),
                    "incidents2023": int(row.get("Incidents_2023", 0) or 0),
                    "incidents2024": int(row.get("Incidents_2024", 0) or 0),
                    "incidents2025": int(row.get("Incidents_2025", 0) or 0),
                    "ratePerLakh": float(row.get("Rate_Per_Lakh", 0.0) or 0.0),
                    "chargesheetRate": float(row.get("Chargesheet_Rate", 0.0) or 0.0),
                    "convictionRate": float(row.get("Conviction_Rate", 0.0) or 0.0),
                    "personsArrested": int(row.get("Persons_Arrested", 0) or 0),
                })
        return results

    def get_categories_data(self) -> List[Dict[str, Any]]:
        """Parse cyber crime offense categories."""
        if not self.categories_file.exists():
            return []

        results = []
        with open(self.categories_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append({
                    "category": row.get("Category", "").strip(),
                    "count": int(row.get("Incident_Count", 0) or 0),
                    "percentage": float(row.get("Percentage", 0.0) or 0.0),
                    "financialLossCr": float(row.get("Financial_Loss_Cr", 0.0) or 0.0),
                    "motive": row.get("Primary_Motive", "").strip(),
                    "riskLevel": row.get("Risk_Level", "HIGH").strip(),
                })
        return results

    def get_it_act_sections_data(self) -> List[Dict[str, Any]]:
        """Parse statutory offenses under IT Act & IPC."""
        if not self.sections_file.exists():
            return []

        results = []
        with open(self.sections_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append({
                    "sectionCode": row.get("Section_Code", "").strip(),
                    "act": row.get("Act", "").strip(),
                    "description": row.get("Description", "").strip(),
                    "totalCases": int(row.get("Total_Cases", 0) or 0),
                    "convictions": int(row.get("Convictions", 0) or 0),
                    "chargesheetRate": float(row.get("Chargesheet_Rate", 0.0) or 0.0),
                })
        return results

    def get_overview_metrics(self) -> Dict[str, Any]:
        """Aggregate national-level NCRB intelligence telemetry."""
        states = self.get_statewise_data()
        categories = self.get_categories_data()

        total_2023 = sum(s["incidents2023"] for s in states)
        total_2024 = sum(s["incidents2024"] for s in states)
        total_2025 = sum(s["incidents2025"] for s in states)
        total_arrested = sum(s["personsArrested"] for s in states)
        total_loss_cr = sum(c["financialLossCr"] for c in categories)

        avg_chargesheet = (
            sum(s["chargesheetRate"] for s in states) / max(1, len(states))
        )
        avg_conviction = (
            sum(s["convictionRate"] for s in states) / max(1, len(states))
        )

        # YoY Growth Rate
        yoy_growth = (
            ((total_2025 - total_2024) / max(1, total_2024)) * 100
            if total_2024
            else 0.0
        )

        # Top 5 State Hotspots
        top_states = sorted(states, key=lambda s: s["incidents2025"], reverse=True)[:5]

        return {
            "nationalTotal2025": total_2025,
            "nationalTotal2024": total_2024,
            "nationalTotal2023": total_2023,
            "yoyGrowthPercent": round(yoy_growth, 1),
            "totalFinancialLossCr": round(total_loss_cr, 2),
            "totalPersonsArrested": total_arrested,
            "avgChargesheetRate": round(avg_chargesheet, 1),
            "avgConvictionRate": round(avg_conviction, 1),
            "topHotspots": [
                {"state": s["state"], "cases": s["incidents2025"], "rate": s["ratePerLakh"]}
                for s in top_states
            ],
            "totalStatesTracked": len(states),
            "totalCategoriesTracked": len(categories),
        }

    def process_custom_csv(self, csv_content: str, filename: str = "custom.csv") -> Dict[str, Any]:
        """Parse and ingest custom user-uploaded NCRB CSV datasets."""
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        if not rows:
            raise ValueError("Uploaded CSV file is empty or invalid.")

        parsed_rows = len(rows)
        headers = reader.fieldnames or []

        self._custom_datasets.append({
            "filename": filename,
            "headers": headers,
            "rowCount": parsed_rows,
        })

        return {
            "status": "SUCCESS",
            "filename": filename,
            "rowsParsed": parsed_rows,
            "headers": headers,
            "message": f"Successfully ingested {parsed_rows} records from {filename}.",
        }


ncrb_service = NCRBService()
