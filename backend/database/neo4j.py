import os
import threading
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("Neo4jDatabase")


class Neo4jDualGraphDatabase:
    """
    Forensic Dual-Layer Neo4j Graph Engine for NetraGraph AI.
    
    GRAPH 1: NCRB PUBLIC INTELLIGENCE GRAPH
      - Source: data.gov.in official NCRB APIs
      - Allowed: State, UT, Year, CrimeCategory, CrimeMotive, PoliceDisposal, CourtDisposal, ArrestStatistics
      - Strict Rule: NEVER contains person names, phone numbers, IMEIs, bank accounts, or private organizations.

    GRAPH 2: INVESTIGATION EVIDENCE GRAPH
      - Source: Authorized uploaded case evidence (FIR, CDR, Bank Records, Forensics)
      - Allowed: Person, Phone, Device, BankAccount, Organization, Location, Vehicle
      - Strict Rule: Every entity MUST have case_id, source_document, timestamp, confidence_score.
    """

    def __init__(self):
        self._lock = threading.RLock()
        
        # Graph 1: NCRB Public Statistical Knowledge Graph
        self._ncrb_nodes: Dict[str, Dict[str, Any]] = {}
        self._ncrb_relationships: Dict[str, Dict[str, Any]] = {}
        self.ncrb_last_sync: Optional[str] = None

        # Graph 2: Case Investigation Evidence Graph
        self._evidence_nodes: Dict[str, Dict[str, Any]] = {}
        self._evidence_relationships: Dict[str, Dict[str, Any]] = {}
        self.evidence_last_sync: Optional[str] = None

        # Graph 3: Unified Cyber Threat Intelligence Graph
        self._cyber_nodes: Dict[str, Dict[str, Any]] = {}
        self._cyber_relationships: Dict[str, Dict[str, Any]] = {}
        self.cyber_last_sync: Optional[str] = None

    def clear_ncrb_graph(self):
        with self._lock:
            self._ncrb_nodes.clear()
            self._ncrb_relationships.clear()

    def clear_evidence_graph(self):
        with self._lock:
            self._evidence_nodes.clear()
            self._evidence_relationships.clear()

    # --- GRAPH 3: UNIFIED CYBER THREAT INTELLIGENCE GRAPH ---
    def add_cyber_node(self, node: Dict[str, Any]) -> None:
        with self._lock:
            self._cyber_nodes[node["id"]] = node

    def add_cyber_relationship(self, relationship: Dict[str, Any]) -> None:
        with self._lock:
            self._cyber_relationships[relationship["id"]] = relationship

    def query_cyber_graph(
        self,
        search: Optional[str] = None,
        node_type: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            query = search.lower() if search else None
            nodes = [
                node for node in self._cyber_nodes.values()
                if (not query or query in node["name"].lower() or query in node["id"].lower())
                and (not node_type or node_type == "ALL" or node["type"] == node_type)
            ]
            node_ids = {node["id"] for node in nodes}
            relationships = [
                rel for rel in self._cyber_relationships.values()
                if rel["source_id"] in node_ids
                and rel["target_id"] in node_ids
                and (not relationship_type or relationship_type == "ALL" or rel["type"] == relationship_type)
            ]
            return {
                "graph_source": "UNIFIED_CYBER_THREAT_INTELLIGENCE",
                "nodes": nodes,
                "relationships": relationships,
                "totalNodes": len(nodes),
                "totalRelationships": len(relationships),
                "lastSync": self.cyber_last_sync or datetime.utcnow().isoformat() + "Z",
            }

    # --- GRAPH 1: NCRB PUBLIC GRAPH METHODS ---
    def add_ncrb_node(self, node_id: str, label: str, name: str, **attributes):
        with self._lock:
            self._ncrb_nodes[node_id] = {
                "id": node_id,
                "label": label,
                "name": name,
                "graph_source": "NCRB_PUBLIC_OGD",
                **attributes,
            }

    def add_ncrb_relationship(self, rel_id: str, source_id: str, target_id: str, rel_type: str, metadata: Optional[Dict[str, Any]] = None):
        with self._lock:
            self._ncrb_relationships[rel_id] = {
                "id": rel_id,
                "sourceId": source_id,
                "targetId": target_id,
                "type": rel_type,
                "graph_source": "NCRB_PUBLIC_OGD",
                "metadata": metadata or {},
            }

    def query_ncrb_graph(
        self,
        search: Optional[str] = None,
        state: Optional[str] = None,
        crime_category: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            filtered: Dict[str, Dict[str, Any]] = {}
            for nid, node in self._ncrb_nodes.items():
                if search:
                    q = search.lower()
                    if q not in node.get("name", "").lower() and q not in node.get("id", "").lower():
                        continue
                if state and state != "ALL":
                    if node.get("label") == "State" and node.get("name", "").lower() != state.lower() and node.get("stateCode", "").lower() != state.lower():
                        continue
                if crime_category and crime_category != "ALL":
                    if node.get("label") == "CrimeCategory" and crime_category.lower() not in node.get("name", "").lower():
                        continue
                filtered[nid] = node

            valid_ids = set(filtered.keys())
            filtered_rels = [
                r for r in self._ncrb_relationships.values()
                if r["sourceId"] in valid_ids and r["targetId"] in valid_ids
            ]

            return {
                "graph_source": "NCRB_PUBLIC_OGD",
                "nodes": list(filtered.values()),
                "relationships": filtered_rels,
                "totalNodes": len(filtered),
                "totalRelationships": len(filtered_rels),
                "sourceDataset": "data.gov.in NCRB Official Catalog",
                "lastSync": self.ncrb_last_sync or datetime.utcnow().isoformat() + "Z",
            }

    # --- GRAPH 2: INVESTIGATION EVIDENCE GRAPH METHODS ---
    def add_evidence_node(self, node_id: str, label: str, name: str, case_id: str, source_document: str, confidence_score: float = 0.95, **attributes):
        with self._lock:
            self._evidence_nodes[node_id] = {
                "id": node_id,
                "label": label,
                "name": name,
                "case_id": case_id,
                "source_document": source_document,
                "confidence_score": confidence_score,
                "graph_source": "AUTHORIZED_CASE_EVIDENCE",
                **attributes,
            }

    def add_evidence_relationship(self, rel_id: str, source_id: str, target_id: str, rel_type: str, case_id: str, source_document: str, metadata: Optional[Dict[str, Any]] = None):
        with self._lock:
            self._evidence_relationships[rel_id] = {
                "id": rel_id,
                "sourceId": source_id,
                "targetId": target_id,
                "type": rel_type,
                "case_id": case_id,
                "source_document": source_document,
                "graph_source": "AUTHORIZED_CASE_EVIDENCE",
                "metadata": metadata or {},
            }

    def query_evidence_graph(
        self,
        search: Optional[str] = None,
        case_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        node_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            filtered: Dict[str, Dict[str, Any]] = {}
            for nid, node in self._evidence_nodes.items():
                if search:
                    q = search.lower()
                    if q not in node.get("name", "").lower() and q not in node.get("id", "").lower() and q not in str(node.get("role", "")).lower():
                        continue
                if case_id and case_id != "ALL":
                    if node.get("case_id") != case_id:
                        continue
                if node_type and node_type != "ALL":
                    if node.get("label") != node_type:
                        continue
                if risk_level and risk_level != "ALL":
                    risk = node.get("riskScore", 50)
                    if risk_level == "CRITICAL" and risk < 85:
                        continue
                    elif risk_level == "HIGH" and (risk < 70 or risk >= 85):
                        continue
                    elif risk_level == "MEDIUM" and (risk < 50 or risk >= 70):
                        continue
                    elif risk_level == "LOW" and risk >= 50:
                        continue
                filtered[nid] = node

            valid_ids = set(filtered.keys())
            filtered_rels = [
                r for r in self._evidence_relationships.values()
                if r["sourceId"] in valid_ids and r["targetId"] in valid_ids
            ]

            return {
                "graph_source": "AUTHORIZED_CASE_EVIDENCE",
                "nodes": list(filtered.values()),
                "relationships": filtered_rels,
                "totalNodes": len(filtered),
                "totalRelationships": len(filtered_rels),
                "sourceDataset": "Authorized Case Investigation Files (FIRs / CDRs / Bank Statements)",
                "lastSync": self.evidence_last_sync or datetime.utcnow().isoformat() + "Z",
            }

    # General Unified Query with graph_source parameter
    def query(self, graph_source: str = "ncrb_public", **kwargs) -> Dict[str, Any]:
        if graph_source == "investigation_evidence" or kwargs.get("node_type") in ["Person", "Device", "Financial", "Phone", "BankAccount"]:
            return self.query_evidence_graph(
                search=kwargs.get("search"),
                case_id=kwargs.get("case_id"),
                risk_level=kwargs.get("risk_level"),
                node_type=kwargs.get("node_type"),
            )
        else:
            return self.query_ncrb_graph(
                search=kwargs.get("search"),
                state=kwargs.get("state"),
                crime_category=kwargs.get("crime_type") or kwargs.get("category"),
            )

    def find_shortest_path(self, source_id: str, target_id: str, graph_source: str = "investigation_evidence") -> List[str]:
        with self._lock:
            nodes_store = self._evidence_nodes if graph_source == "investigation_evidence" else self._ncrb_nodes
            rels_store = self._evidence_relationships if graph_source == "investigation_evidence" else self._ncrb_relationships

            if source_id not in nodes_store or target_id not in nodes_store:
                return []
            if source_id == target_id:
                return [source_id]

            queue = [[source_id]]
            visited = {source_id}

            while queue:
                path = queue.pop(0)
                current = path[-1]

                if current == target_id:
                    return path

                neighbors = []
                for rel in rels_store.values():
                    if rel["sourceId"] == current and rel["targetId"] not in visited:
                        neighbors.append(rel["targetId"])
                    elif rel["targetId"] == current and rel["sourceId"] not in visited:
                        neighbors.append(rel["sourceId"])

                for neighbor in neighbors:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)

            return []

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._evidence_nodes.get(node_id) or self._ncrb_nodes.get(node_id)


neo4j_db = Neo4jDualGraphDatabase()
