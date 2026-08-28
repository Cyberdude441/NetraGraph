import re
from collections import deque
from typing import Any, Dict, List

from database.neo4j import neo4j_db


class CyberReasoningService:
    def answer(self, question: str) -> Dict[str, Any]:
        graph = neo4j_db.query_cyber_graph()
        terms = {term.lower() for term in re.findall(r"[\w.-]+", question) if len(term) > 2}
        matches = [node for node in graph["nodes"] if any(term in node["name"].lower() for term in terms)]
        if not matches:
            return {
                "question": question,
                "observation": "No matching cyber intelligence entity was found in the unified graph.",
                "evidence": [],
                "graph_path": [],
                "confidence": 0.0,
                "analyst_verification_required": True,
            }
        root = matches[0]
        adjacency: Dict[str, List[str]] = {}
        for rel in graph["relationships"]:
            adjacency.setdefault(rel["source_id"], []).append(rel["target_id"])
            adjacency.setdefault(rel["target_id"], []).append(rel["source_id"])
        visited = {root["id"]}
        queue = deque([(root["id"], [root["id"]])])
        path = [root["id"]]
        while queue:
            current, current_path = queue.popleft()
            if current != root["id"] and current in {node["id"] for node in matches[1:]}:
                path = current_path
                break
            for neighbor in adjacency.get(current, []):
                if neighbor not in visited and len(current_path) < 5:
                    visited.add(neighbor)
                    queue.append((neighbor, current_path + [neighbor]))
        node_map = {node["id"]: node for node in graph["nodes"]}
        return {
            "question": question,
            "observation": f"{root['name']} is present in the unified cyber intelligence graph with {len(adjacency.get(root['id'], []))} observed connections.",
            "evidence": [
                {"source_dataset": root["source_dataset"], "record_id": root["source_record_id"], "entity": root["name"]}
            ],
            "graph_path": [node_map[node_id] for node_id in path if node_id in node_map],
            "confidence": root.get("confidence", 0.0),
            "analyst_verification_required": True,
        }


cyber_reasoning_service = CyberReasoningService()
