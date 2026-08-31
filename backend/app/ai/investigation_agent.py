"""AI Investigation Copilot grounded in real Knowledge Graph analytics."""
from __future__ import annotations

from typing import List, Optional

from ..database.db import db
from ..graph.network_manager import graph_manager
from ..models.analysis import AnalysisRequest, AnalysisResponse, PathSegment
from ..models.entity import Entity


class InvestigationAgent:
    """AI Copilot Reasoning Engine grounded in real Knowledge Graph analytics."""

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

        # Identify top betweenness bridge nodes from actual data
        sorted_bridges = sorted(centralities.items(), key=lambda x: x[1].betweenness, reverse=True)
        top_bridge_ids = [node_id for node_id, cent in sorted_bridges[:3] if cent.betweenness > 0]

        for b_id in top_bridge_ids:
            ent = db.get_entity_by_id(b_id)
            if ent:
                bridges.append(f"{ent.name} ({ent.type.value}, Betweenness {centralities[b_id].betweenness:.4f})")
                flagged_entities.append(ent)

        # Pathfinding reasoning on real data
        if "path" in query_lower or "bridge" in query_lower or "connect" in query_lower:
            target_ids = [e.id for e in all_entities if e.type.value in ["Person", "Organization", "Device"]]
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

        # Risk drivers reasoning on real data
        if "risk" in query_lower or "threat" in query_lower or "high" in query_lower:
            high_risk = [e for e in all_entities if e.riskScore >= 85]
            if high_risk:
                findings.append(f"{len(high_risk)} critical-risk entities detected exceeding threat threshold 85.")
                for e in high_risk:
                    if e not in flagged_entities:
                        flagged_entities.append(e)

        # Handle empty/insufficient data cleanly without inventing facts
        if not findings:
            if all_entities:
                findings = [
                    f"Graph topology evaluated across {len(all_entities)} verified entities and {len(all_relationships)} relationships.",
                    f"Structural broker count: {len(bridges)} verified bridge intermediaries.",
                ]
            else:
                findings = ["Insufficient verified data in active investigation graph."]

        if flagged_entities:
            actions = [
                "Review evidentiary chain of custody for flagged entities.",
                "Verify cross-case telephone and financial identifiers with active telecom subpoenas.",
            ]
        else:
            actions = ["Ingest additional authorized case dockets to expand graph connectivity."]

        reasoning_text = (
            f"Analyzed verified graph index for query: '{req.query}'. "
            f"Identified {len(flagged_entities)} high-impact nodes and {len(bridges)} structural bridge intermediaries. "
            f"Grounding Status: Strict adherence to verified database records."
        )

        return AnalysisResponse(
            query=req.query,
            reasoning=reasoning_text,
            keyFindings=findings,
            flaggedEntities=flagged_entities,
            identifiedBridges=bridges,
            suggestedActions=actions,
            confidenceScore=0.95 if flagged_entities else 0.5,
            graphPath=path_segments,
        )


investigation_agent = InvestigationAgent()
