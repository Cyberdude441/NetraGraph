from fastapi import APIRouter
from ..database.db import db
from ..graph.network_manager import graph_manager

router = APIRouter(prefix="/analytics", tags=["Investigation Analytics"])


@router.get("/metrics")
async def get_dashboard_metrics():
    """Retrieve dynamic system-wide intelligence metrics and threat breakdown."""
    db_metrics = db.get_metrics()
    entities = db.get_all_entities()
    relationships = db.get_all_relationships()

    # Risk breakdown
    critical = sum(1 for e in entities if e.riskScore >= 85)
    high = sum(1 for e in entities if 70 <= e.riskScore < 85)
    moderate = sum(1 for e in entities if 50 <= e.riskScore < 70)
    low = sum(1 for e in entities if e.riskScore < 50)

    # Calculate syndicate/network clusters
    network_counts = {}
    for e in entities:
        net = e.metadata.network or "Unassigned Cluster"
        if net not in network_counts:
            network_counts[net] = {"nodes": 0, "riskSum": 0}
        network_counts[net]["nodes"] += 1
        network_counts[net]["riskSum"] += e.riskScore

    syndicates = []
    for net, data in network_counts.items():
        avg_risk = int(data["riskSum"] / max(1, data["nodes"]))
        syndicates.append({
            "network": net,
            "nodes": data["nodes"],
            "links": max(1, data["nodes"] - 1),
            "risk": avg_risk,
        })

    return {
        "summary": db_metrics,
        "threatMatrix": [
            {"name": "Critical", "value": critical, "key": "crit"},
            {"name": "High", "value": high, "key": "high"},
            {"name": "Moderate", "value": moderate, "key": "mod"},
            {"name": "Low", "value": low, "key": "low"},
        ],
        "syndicates": syndicates,
        "totalRecords": len(entities),
    }
