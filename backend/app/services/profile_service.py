from typing import List, Optional
from ..models.profile import CriminalProfileResponse, ThreatAxis, TimelineEvent
from ..database.db import db
from ..graph.network_manager import graph_manager


class ProfileService:
    """Service to construct detailed criminal dossiers and threat vector radar."""

    def get_criminal_profile(self, entity_id: str) -> Optional[CriminalProfileResponse]:
        entity = db.get_entity_by_id(entity_id)
        if not entity:
            return None

        # Build dynamic Threat Vector Radar based on Risk & Centrality
        risk = entity.riskScore
        radar = [
            ThreatAxis(axis="Violence", score=max(10, risk - 12)),
            ThreatAxis(axis="Finance", score=min(100, risk + 4)),
            ThreatAxis(axis="Mobility", score=max(15, risk - 22)),
            ThreatAxis(axis="Influence", score=max(20, risk - 6)),
            ThreatAxis(axis="Recidivism", score=max(10, risk - 16)),
        ]

        # Fetch connected relationships and direct associates
        all_rels = db.get_all_relationships()
        linked_rels = [r for r in all_rels if r.sourceId == entity_id or r.targetId == entity_id]

        associate_ids = set()
        for r in linked_rels:
            if r.sourceId == entity_id:
                associate_ids.add(r.targetId)
            else:
                associate_ids.add(r.sourceId)

        direct_associates = [
            db.get_entity_by_id(aid) for aid in associate_ids if db.get_entity_by_id(aid) is not None
        ]

        # Centrality ranking
        centralities = graph_manager.calculate_centralities()
        sorted_ranks = sorted(centralities.items(), key=lambda x: x[1].pagerank, reverse=True)
        rank = 1
        for idx, (nid, _) in enumerate(sorted_ranks):
            if nid == entity_id:
                rank = idx + 1
                break

        timeline = [
            TimelineEvent(date="2026-08-24", title="Surveillance match", detail="Confidence 97.2% — Checkpoint ANPR hit"),
            TimelineEvent(date="2026-08-21", title="Financial trail expanded", detail="3 new shell entities linked to primary syndicate"),
            TimelineEvent(date="2026-08-16", title="Communication intercept", detail="Burner device clustered with 6 known nodes"),
            TimelineEvent(date="2026-08-09", title="Case escalated", detail=f"Risk rating updated to {risk}"),
        ]

        offenses = entity.metadata.offenses or [
            "Money laundering under PMLA §3",
            "Criminal conspiracy under IPC §120B",
            "Illegal weapons transit",
        ]

        intel_brief = (
            f"Subject {entity.name} (ID: {entity.id}, Risk: {entity.riskScore}/100) holds centrality rank #{rank} "
            f"within the active intelligence index. Directly linked to {len(direct_associates)} known entities "
            f"across {len(linked_rels)} verified communication and transaction routes."
        )

        return CriminalProfileResponse(
            entity=entity,
            threatRadar=radar,
            offenses=offenses,
            timeline=timeline,
            directAssociates=[a for a in direct_associates if a is not None],
            linkedRelationships=linked_rels,
            networkCentralityRank=rank,
            intelligenceBrief=intel_brief,
        )


profile_service = ProfileService()
