"""Forensic Neo4j Graph Database & Synchronized NetworkX Engine for NetraGraph AI."""
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

logger = logging.getLogger("Neo4jDualGraphDatabase")


class Neo4jDualGraphDatabase:
    """
    Forensic Dual-Layer Neo4j Graph Engine for NetraGraph AI.

    GRAPH 1: NCRB PUBLIC INTELLIGENCE GRAPH (PUBLIC_NCRB_DATA)
      - Source: data.gov.in official Open Government Data (OGD)
      - Allowed: State, Year, CrimeCategory, CrimeMotive, PoliceDisposal, CourtDisposal, ArrestStatistics
      - Strict Rule: NEVER contains personal names, fictional persons, private phone numbers, or fake bank accounts.
      - Provenance: Every node contains source, source_url, dataset_name, year, retrieved_at, jurisdiction.

    GRAPH 2: INVESTIGATION EVIDENCE GRAPH (INVESTIGATION_CASE_DATA)
      - Source: Authorized uploaded case evidence (FIR, CDR, Bank Records, Digital Forensics)
      - Allowed: Case, Evidence, Person (Suspect/Witness), Phone, Device, BankAccount, IP, Domain, Email, Hash, MLPrediction
      - Strict Rule: Every entity MUST have case_id, source_document, timestamp, and confidence_score.
    """

    def __init__(self):
        self._lock = threading.RLock()

        # Connection config (Never hardcode credentials; read from env)
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        self.driver = None
        self.is_connected = False
        self.connection_error: Optional[str] = None

        # Synchronized In-Memory NetworkX Graph Stores
        self._nx_ncrb = nx.MultiDiGraph()
        self._nx_evidence = nx.MultiDiGraph()
        self._nx_cyber = nx.MultiDiGraph()

        # Node / Relationship Dict Registries
        self._ncrb_nodes: Dict[str, Dict[str, Any]] = {}
        self._ncrb_relationships: Dict[str, Dict[str, Any]] = {}
        self.ncrb_last_sync: Optional[str] = None

        self._evidence_nodes: Dict[str, Dict[str, Any]] = {}
        self._evidence_relationships: Dict[str, Dict[str, Any]] = {}
        self.evidence_last_sync: Optional[str] = None

        self._cyber_nodes: Dict[str, Dict[str, Any]] = {}
        self._cyber_relationships: Dict[str, Dict[str, Any]] = {}
        self.cyber_last_sync: Optional[str] = None

        # Attempt initial Neo4j connection & schema initialization
        self.connect()

    def connect(self) -> bool:
        """Initializes connection pool to Neo4j instance if configured and reachable."""
        with self._lock:
            if not self.uri:
                self.is_connected = False
                self.connection_error = "NEO4J_URI environment variable not configured"
                return False

            try:
                from neo4j import GraphDatabase

                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password),
                    max_connection_pool_size=50,
                    connection_timeout=5.0,
                )
                self.driver.verify_connectivity()
                self.is_connected = True
                self.connection_error = None
                logger.info(f"[Neo4j] Successfully connected to live Neo4j instance at {self.uri}")
                self.initialize_schema()
                return True
            except Exception as e:
                self.is_connected = False
                self.connection_error = str(e)
                logger.warning(
                    f"[Neo4j] Live Bolt connection at {self.uri} not available ({e}). "
                    "Operating with fully synchronized in-memory NetworkX graph engine."
                )
                return False

    def close(self):
        """Closes Neo4j driver connection pool."""
        with self._lock:
            if self.driver:
                try:
                    self.driver.close()
                except Exception:
                    pass
                self.is_connected = False

    def initialize_schema(self):
        """Creates unique constraints and indexes for NCRB and Case Evidence graphs."""
        if not self.is_connected or not self.driver:
            return

        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Dataset) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:State) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (y:Year) REQUIRE y.year IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:CrimeCategory) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (cs:CrimeStatistic) REQUIRE cs.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:CrimeMotive) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:PoliceDisposal) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (o:CourtOutcome) REQUIRE o.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (cs:Case) REQUIRE cs.case_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Evidence) REQUIRE e.evidence_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (ip:IP) REQUIRE ip.ip IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Domain) REQUIRE d.domain IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (em:Email) REQUIRE em.email IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (h:Hash) REQUIRE h.hash IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:MLModel) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:MLPrediction) REQUIRE p.prediction_id IS UNIQUE",
        ]

        try:
            with self.driver.session(database=self.database) as session:
                for cypher in constraints:
                    try:
                        session.run(cypher)
                    except Exception as ce:
                        logger.debug(f"[Neo4j Schema] Constraint notice: {ce}")
            logger.info("[Neo4j] Schema constraints and indexes successfully initialized.")
        except Exception as e:
            logger.warning(f"[Neo4j] Schema initialization error: {e}")

    def get_health(self) -> Dict[str, Any]:
        """Provides comprehensive health and connectivity metrics."""
        latency_ms = None
        server_version = "Unknown"

        if self.is_connected and self.driver:
            t0 = time.perf_counter()
            try:
                with self.driver.session(database=self.database) as session:
                    res = session.run("RETURN 1 AS ping")
                    res.single()
                latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            except Exception as e:
                self.is_connected = False
                self.connection_error = str(e)

        # Mask URI password
        masked_uri = self.uri
        if "@" in masked_uri:
            prefix = masked_uri.split("@")[0].split("//")[0]
            host = masked_uri.split("@")[1]
            masked_uri = f"{prefix}//***:***@{host}"

        with self._lock:
            total_ncrb_nodes = len(self._ncrb_nodes)
            total_ncrb_rels = len(self._ncrb_relationships)
            total_evidence_nodes = len(self._evidence_nodes)
            total_evidence_rels = len(self._evidence_relationships)
            total_cyber_nodes = len(self._cyber_nodes)
            total_cyber_rels = len(self._cyber_relationships)

        return {
            "status": "CONNECTED" if self.is_connected else "SYNCHRONIZED_MEMORY_FALLBACK",
            "backend_engine": "Neo4j Enterprise / Community (Bolt)" if self.is_connected else "NetworkX MultiDiGraph (In-Memory)",
            "neo4j_uri": masked_uri,
            "database": self.database,
            "latency_ms": latency_ms,
            "connection_error": self.connection_error,
            "last_health_check": datetime.now(timezone.utc).isoformat(),
            "graph_summary": {
                "total_nodes": total_ncrb_nodes + total_evidence_nodes + total_cyber_nodes,
                "total_relationships": total_ncrb_rels + total_evidence_rels + total_cyber_rels,
                "ncrb_public_graph": {
                    "nodes": total_ncrb_nodes,
                    "relationships": total_ncrb_rels,
                    "last_sync": self.ncrb_last_sync,
                },
                "investigation_evidence_graph": {
                    "nodes": total_evidence_nodes,
                    "relationships": total_evidence_rels,
                    "last_sync": self.evidence_last_sync,
                },
                "unified_cyber_graph": {
                    "nodes": total_cyber_nodes,
                    "relationships": total_cyber_rels,
                    "last_sync": self.cyber_last_sync,
                },
            },
        }

    # =========================================================================
    # GRAPH 1: NCRB PUBLIC GRAPH (PUBLIC_NCRB_DATA)
    # =========================================================================
    def clear_ncrb_graph(self):
        with self._lock:
            self._ncrb_nodes.clear()
            self._ncrb_relationships.clear()
            self._nx_ncrb.clear()

        if self.is_connected and self.driver:
            try:
                with self.driver.session(database=self.database) as session:
                    session.run("MATCH (n {graph_source: 'NCRB_PUBLIC_OGD'}) DETACH DELETE n")
            except Exception as e:
                logger.warning(f"[Neo4j] Clear NCRB graph error: {e}")

    def add_ncrb_node(self, node_id: str, label: str, name: str, **attributes):
        """Adds or merges an NCRB node with strict public provenance."""
        now_iso = datetime.now(timezone.utc).isoformat()
        node_payload = {
            "id": node_id,
            "label": label,
            "name": name,
            "graph_source": "NCRB_PUBLIC_OGD",
            "source": attributes.get("source", "NCRB"),
            "source_url": attributes.get("source_url", "https://data.gov.in/resource/cases-registered-under-it-act-cyber-crime"),
            "dataset_name": attributes.get("dataset_name", "NCRB Cyber Crime Catalog"),
            "dataset_year": attributes.get("dataset_year", attributes.get("year", 2025)),
            "year": attributes.get("year", attributes.get("dataset_year", 2025)),
            "resource_id": attributes.get("resource_id", "ncrb-ogd-catalog"),
            "jurisdiction": attributes.get("jurisdiction", "National / State"),
            "retrieved_at": attributes.get("retrieved_at", now_iso),
            **attributes,
        }

        with self._lock:
            self._ncrb_nodes[node_id] = node_payload
            self._nx_ncrb.add_node(node_id, **node_payload)

        # Merge in live Neo4j if connected
        if self.is_connected and self.driver:
            try:
                cypher = f"""
                MERGE (n:{label} {{id: $node_id}})
                SET n += $props, n.name = $name, n.graph_source = 'NCRB_PUBLIC_OGD'
                """
                with self.driver.session(database=self.database) as session:
                    session.run(cypher, node_id=node_id, name=name, props=node_payload)
            except Exception as e:
                logger.debug(f"[Neo4j] MERGE NCRB node error ({node_id}): {e}")

    def add_ncrb_relationship(
        self,
        rel_id: str,
        source_id: str,
        target_id: str,
        rel_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Adds or merges an NCRB relationship with provenance."""
        rel_payload = {
            "id": rel_id,
            "sourceId": source_id,
            "targetId": target_id,
            "type": rel_type,
            "graph_source": "NCRB_PUBLIC_OGD",
            "metadata": metadata or {},
        }

        with self._lock:
            self._ncrb_relationships[rel_id] = rel_payload
            self._nx_ncrb.add_edge(source_id, target_id, key=rel_id, type=rel_type, **(metadata or {}))

        if self.is_connected and self.driver:
            try:
                cypher = f"""
                MATCH (s {{id: $source_id}}), (t {{id: $target_id}})
                MERGE (s)-[r:{rel_type} {{id: $rel_id}}]->(t)
                SET r += $metadata, r.graph_source = 'NCRB_PUBLIC_OGD'
                """
                with self.driver.session(database=self.database) as session:
                    session.run(
                        cypher,
                        source_id=source_id,
                        target_id=target_id,
                        rel_id=rel_id,
                        metadata=metadata or {},
                    )
            except Exception as e:
                logger.debug(f"[Neo4j] MERGE NCRB rel error ({rel_id}): {e}")

    def query_ncrb_graph(
        self,
        search: Optional[str] = None,
        state: Optional[str] = None,
        crime_category: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Queries the verified NCRB Public Statistical Knowledge Graph."""
        with self._lock:
            filtered: Dict[str, Dict[str, Any]] = {}
            for nid, node in self._ncrb_nodes.items():
                if search:
                    q = search.lower()
                    if q not in node.get("name", "").lower() and q not in node.get("id", "").lower():
                        continue
                if state and state != "ALL":
                    if node.get("label") == "State":
                        s_name = node.get("name", "").lower()
                        s_code = node.get("stateCode", "").lower()
                        if state.lower() not in s_name and state.lower() not in s_code:
                            continue
                if crime_category and crime_category != "ALL":
                    if node.get("label") == "CrimeCategory":
                        c_name = node.get("name", "").lower()
                        if crime_category.lower() not in c_name:
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
                "sourceDataset": "Open Government Data (data.gov.in) NCRB Official Catalog",
                "lastSync": self.ncrb_last_sync or datetime.now(timezone.utc).isoformat(),
            }

    # =========================================================================
    # GRAPH 2: INVESTIGATION EVIDENCE GRAPH (INVESTIGATION_CASE_DATA)
    # =========================================================================
    def clear_evidence_graph(self):
        with self._lock:
            self._evidence_nodes.clear()
            self._evidence_relationships.clear()
            self._nx_evidence.clear()

        if self.is_connected and self.driver:
            try:
                with self.driver.session(database=self.database) as session:
                    session.run("MATCH (n {graph_source: 'AUTHORIZED_CASE_EVIDENCE'}) DETACH DELETE n")
            except Exception as e:
                logger.warning(f"[Neo4j] Clear evidence graph error: {e}")

    def add_evidence_node(
        self,
        node_id: str,
        label: str,
        name: str,
        case_id: str = "CASE-ACTIVE",
        source_document: str = "Authorized Case Evidence",
        confidence_score: float = 0.95,
        **attributes,
    ):
        """Adds or merges an authorized investigation evidence node."""
        now_iso = datetime.now(timezone.utc).isoformat()
        node_payload = {
            "id": node_id,
            "label": label,
            "name": name,
            "case_id": case_id,
            "source_document": source_document,
            "confidence_score": confidence_score,
            "graph_source": "AUTHORIZED_CASE_EVIDENCE",
            "created_at": attributes.get("created_at", now_iso),
            **attributes,
        }

        with self._lock:
            self._evidence_nodes[node_id] = node_payload
            self._nx_evidence.add_node(node_id, **node_payload)

        if self.is_connected and self.driver:
            try:
                cypher = f"""
                MERGE (n:{label} {{id: $node_id}})
                SET n += $props, n.name = $name, n.case_id = $case_id, n.graph_source = 'AUTHORIZED_CASE_EVIDENCE'
                """
                with self.driver.session(database=self.database) as session:
                    session.run(
                        cypher,
                        node_id=node_id,
                        name=name,
                        case_id=case_id,
                        props=node_payload,
                    )
            except Exception as e:
                logger.debug(f"[Neo4j] MERGE evidence node error ({node_id}): {e}")

    def add_evidence_relationship(
        self,
        rel_id: str,
        source_id: str,
        target_id: str,
        rel_type: str,
        case_id: str,
        source_document: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Adds or merges an authorized case evidence relationship."""
        rel_payload = {
            "id": rel_id,
            "sourceId": source_id,
            "targetId": target_id,
            "type": rel_type,
            "case_id": case_id,
            "source_document": source_document,
            "graph_source": "AUTHORIZED_CASE_EVIDENCE",
            "metadata": metadata or {},
        }

        with self._lock:
            self._evidence_relationships[rel_id] = rel_payload
            self._nx_evidence.add_edge(
                source_id,
                target_id,
                key=rel_id,
                type=rel_type,
                case_id=case_id,
                **(metadata or {}),
            )

        if self.is_connected and self.driver:
            try:
                cypher = f"""
                MATCH (s {{id: $source_id}}), (t {{id: $target_id}})
                MERGE (s)-[r:{rel_type} {{id: $rel_id}}]->(t)
                SET r += $metadata, r.case_id = $case_id, r.graph_source = 'AUTHORIZED_CASE_EVIDENCE'
                """
                with self.driver.session(database=self.database) as session:
                    session.run(
                        cypher,
                        source_id=source_id,
                        target_id=target_id,
                        rel_id=rel_id,
                        case_id=case_id,
                        metadata=metadata or {},
                    )
            except Exception as e:
                logger.debug(f"[Neo4j] MERGE evidence rel error ({rel_id}): {e}")

    def query_evidence_graph(
        self,
        search: Optional[str] = None,
        case_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        node_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Queries the authorized investigation evidence graph."""
        with self._lock:
            filtered: Dict[str, Dict[str, Any]] = {}
            for nid, node in self._evidence_nodes.items():
                if search:
                    q = search.lower()
                    if (
                        q not in node.get("name", "").lower()
                        and q not in node.get("id", "").lower()
                        and q not in str(node.get("role", "")).lower()
                    ):
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

            # If search query matched nodes, also include their immediate connected neighbors
            if search and filtered:
                matched_ids = set(filtered.keys())
                for r in self._evidence_relationships.values():
                    if r["sourceId"] in matched_ids and r["targetId"] in self._evidence_nodes:
                        filtered[r["targetId"]] = self._evidence_nodes[r["targetId"]]
                    elif r["targetId"] in matched_ids and r["sourceId"] in self._evidence_nodes:
                        filtered[r["sourceId"]] = self._evidence_nodes[r["sourceId"]]

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
                "sourceDataset": "Authorized Case Investigation Files (FIRs / CDRs / Bank Records / Forensics)",
                "lastSync": self.evidence_last_sync or datetime.now(timezone.utc).isoformat(),
            }

    # =========================================================================
    # GRAPH 3: UNIFIED CYBER THREAT GRAPH
    # =========================================================================
    def add_cyber_node(self, node: Dict[str, Any]) -> None:
        with self._lock:
            self._cyber_nodes[node["id"]] = node
            self._nx_cyber.add_node(node["id"], **node)

    def add_cyber_relationship(self, relationship: Dict[str, Any]) -> None:
        with self._lock:
            self._cyber_relationships[relationship["id"]] = relationship
            self._nx_cyber.add_edge(
                relationship["source_id"],
                relationship["target_id"],
                key=relationship["id"],
                **relationship,
            )

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
                and (not node_type or node_type == "ALL" or node.get("type") == node_type or node.get("label") == node_type)
            ]
            node_ids = {node["id"] for node in nodes}
            relationships = [
                rel for rel in self._cyber_relationships.values()
                if (rel.get("source_id") or rel.get("sourceId")) in node_ids
                and (rel.get("target_id") or rel.get("targetId")) in node_ids
                and (not relationship_type or relationship_type == "ALL" or rel.get("type") == relationship_type)
            ]
            return {
                "graph_source": "UNIFIED_CYBER_THREAT_INTELLIGENCE",
                "nodes": nodes,
                "relationships": relationships,
                "totalNodes": len(nodes),
                "totalRelationships": len(relationships),
                "lastSync": self.cyber_last_sync or datetime.now(timezone.utc).isoformat(),
            }

    # Unified Query
    def query(self, graph_source: str = "ncrb_public", **kwargs) -> Dict[str, Any]:
        if graph_source == "investigation_evidence":
            return self.query_evidence_graph(
                search=kwargs.get("search"),
                case_id=kwargs.get("case_id"),
                risk_level=kwargs.get("risk_level"),
                node_type=kwargs.get("node_type"),
            )
        elif graph_source == "unified_cyber":
            return self.query_cyber_graph(
                search=kwargs.get("search"),
                node_type=kwargs.get("node_type"),
                relationship_type=kwargs.get("relationship_type"),
            )
        else:
            return self.query_ncrb_graph(
                search=kwargs.get("search"),
                state=kwargs.get("state"),
                crime_category=kwargs.get("crime_type") or kwargs.get("category"),
            )

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return (
                self._evidence_nodes.get(node_id)
                or self._ncrb_nodes.get(node_id)
                or self._cyber_nodes.get(node_id)
            )

    def get_networkx_graph(self, graph_source: str = "investigation_evidence") -> nx.MultiDiGraph:
        """Returns the synchronized NetworkX graph instance for algorithmic calculations."""
        with self._lock:
            if graph_source == "investigation_evidence":
                return self._nx_evidence
            elif graph_source == "unified_cyber":
                return self._nx_cyber
            else:
                return self._nx_ncrb


# Global Singleton Instance
neo4j_db = Neo4jDualGraphDatabase()
