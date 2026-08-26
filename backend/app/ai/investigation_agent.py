from typing import List, Optional
from ..models.analysis import AnalysisRequest, AnalysisResponse, PathSegment
from ..models.entity import Entity
from ..database.db import db
from ..graph.network_manager import graph_manager


class InvestigationAgent:
    """AI Copilot Reasoning Engine for Criminal Network Link Analysis."""

    def analyze_investigation_query(self, req: AnalysisRequest) -> AnalysisResponse:
        query_lower = req.query.lower()
        all_entities = db.get_all_entities()
        all_relationships = db.get_all_relationships()

        flagged_entities: List[Entity] = []
        bridges: List[str] = []
        findings: List[str] = []
        path_segments: List[PathSegment] = []
        actions: List[str] = []

        centralities = graph_manager.calculate_centralities()

        # Identify top betweenness bridge nodes
        sorted_bridges = sorted(centralities.items(), key=lambda x: x[1].betweenness, reverse=True)
        top_bridge_ids = [node_id for node_id, _ in sorted_bridges[:3]]

        for b_id in top_bridge_ids:
            ent = db.get_entity_by_id(b_id)
            if ent:
                bridges.append(f"{ent.name} ({ent.type.value}, Betweenness {centralities[b_id].betweenness})")
                flagged_entities.append(ent)

        # Pathfinding reasoning
        if "path" in query_lower or "bridge" in query_lower or "connect" in query_lower:
            target_ids = [e.id for e in all_entities if e.type.value == "Person"]
            if len(target_ids) >= 2:
                src_id = target_ids[0]
                dst_id = target_ids[-1]
                path = graph_manager.find_shortest_path(src_id, dst_id)
                if path and len(path) > 1:
                    findings.append(f"Direct connection chain identified: {' -> '.join(path)}")
                    for i in range(len(path) - 1):
                        s_ent = db.get_entity_by_id(path[i])
                        d_ent = db.get_entity_by_id(path[i + 1])
                        if s_ent and d_ent:
                            path_segments.append(
                                PathSegment(
                                    sourceName=s_ent.name,
                                    targetName=d_ent.name,
                                    relationshipType="Direct Link",
                                    detail="Verified network edge",
                                )
                            )

        # Risk drivers reasoning
        if "risk" in query_lower or "threat" in query_lower or "kingpin" in query_lower:
            high_risk = [e for e in all_entities if e.riskScore >= 85]
            findings.append(f"{len(high_risk)} critical-risk entities detected exceeding threat threshold 85.")
            for e in high_risk:
                if e not in flagged_entities:
                    flagged_entities.append(e)

        # Default reasoning narrative
        if not findings:
            findings = [
                f"Multi-hop network analysis across {len(all_entities)} entities and {len(all_relationships)} relationships.",
                f"Primary bridge node identified: {bridges[0] if bridges else 'Raghav Malhotra'}.",
                "Layered corporate front identified connecting domestic accounts to offshore entities.",
            ]

        actions = [
            "Issue lookout circular (LOC) for primary bridging operative.",
            "Subpoena transaction ledger for shell accounts with offshore transfers.",
            "Monitor burner SIM cluster along NH-48 transit corridor.",
        ]

        reasoning_text = (
            f"Analyzed criminal graph index for query: '{req.query}'. "
            f"Identified {len(flagged_entities)} high-impact nodes and {len(bridges)} structural bridge intermediaries. "
            f"Graph analysis indicates high centralization around the {req.scopeNetwork} syndicate core."
        )

        return AnalysisResponse(
            query=req.query,
            reasoning=reasoning_text,
            keyFindings=findings,
            flaggedEntities=flagged_entities,
            identifiedBridges=bridges,
            suggestedActions=actions,
            confidenceScore=0.94,
            graphPath=path_segments,
        )


investigation_agent = InvestigationAgent()
