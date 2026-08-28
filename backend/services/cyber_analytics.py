from collections import Counter
from typing import Any, Dict, List

from database.neo4j import neo4j_db


class CyberAnalyticsService:
    def _graph(self) -> Dict[str, Any]:
        return neo4j_db.query_cyber_graph()

    def overview(self) -> Dict[str, Any]:
        graph = self._graph()
        counts = Counter(node["type"] for node in graph["nodes"])
        return {
            "graph_source": graph["graph_source"],
            "total_nodes": graph["totalNodes"],
            "total_relationships": graph["totalRelationships"],
            "entity_counts": dict(counts),
            "datasets": sorted({node["source_dataset"] for node in graph["nodes"]}),
            "last_sync": graph["lastSync"],
        }

    def risk_assessment(self, entity_id: str) -> Dict[str, Any]:
        graph = self._graph()
        entity = next((node for node in graph["nodes"] if node["id"] == entity_id), None)
        if not entity:
            raise KeyError(entity_id)
        degree = sum(entity_id in (rel["source_id"], rel["target_id"]) for rel in graph["relationships"])
        malicious_links = sum(
            entity_id in (rel["source_id"], rel["target_id"])
            and rel["type"] in {"TARGETED", "ATTACKED", "HOSTED", "SENT_FROM"}
            for rel in graph["relationships"]
        )
        score = min(100, round(entity.get("risk_score", 50) * 0.7 + min(degree * 3, 20) + malicious_links * 5))
        return {
            "entity_id": entity_id,
            "risk_score": score,
            "reasons": [
                f"Connected to {degree} observed intelligence entities",
                f"Associated with {malicious_links} high-signal threat relationships",
                f"Source confidence is {entity.get('confidence', 0):.0%}",
            ],
            "graph_features": {"degree": degree, "malicious_connections": malicious_links},
        }

    def anomalies(self) -> List[Dict[str, Any]]:
        graph = self._graph()
        degrees: Counter[str] = Counter()
        for rel in graph["relationships"]:
            degrees[rel["source_id"]] += 1
            degrees[rel["target_id"]] += 1
        if not degrees:
            return []
        baseline = sum(degrees.values()) / len(degrees)
        return [
            {
                "entity_id": entity_id,
                "anomaly_score": round(min(1.0, degree / max(1, baseline * 2)), 3),
                "reasons": [f"Observed degree {degree} exceeds graph baseline {baseline:.1f}"],
            }
            for entity_id, degree in degrees.most_common()
            if degree > baseline * 1.5
        ]

    def link_predictions(self) -> List[Dict[str, Any]]:
        graph = self._graph()
        neighbors: Dict[str, set[str]] = {}
        for rel in graph["relationships"]:
            neighbors.setdefault(rel["source_id"], set()).add(rel["target_id"])
            neighbors.setdefault(rel["target_id"], set()).add(rel["source_id"])
        predictions = []
        ids = list(neighbors)
        for index, source_id in enumerate(ids):
            for target_id in ids[index + 1 :]:
                shared = neighbors[source_id] & neighbors[target_id]
                if shared:
                    confidence = min(0.95, 0.5 + 0.1 * len(shared))
                    predictions.append({
                        "source_id": source_id,
                        "target_id": target_id,
                        "predicted_relationship": "ASSOCIATED_WITH",
                        "confidence": confidence,
                        "reasons": [f"Shared neighbors: {len(shared)}"],
                    })
        return sorted(predictions, key=lambda item: item["confidence"], reverse=True)[:50]


cyber_analytics_service = CyberAnalyticsService()
