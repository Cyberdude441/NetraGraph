import { SYNTHETIC_ENTITIES, type SyntheticEntity } from "@/data/syntheticGraphData";

export type QueryIntent =
  | "RELATIONSHIP_PATH"
  | "CENTRALITY_INFLUENCE"
  | "RISK_EXPLANATION"
  | "ANOMALY_PATTERNS"
  | "COMMUNITY_STRUCTURE"
  | "CASE_BRIEFING"
  | "BURNER_DEVICE_TRACKING"
  | "GENERAL_INVESTIGATION";

export interface ParsedQuery {
  rawQuery: string;
  intent: QueryIntent;
  intentLabel: string;
  confidenceScore: number;
  extractedEntities: SyntheticEntity[];
  extractedEntityIds: string[];
  targetCaseId?: string;
  targetCommunity?: string;
  extractedKeywords: string[];
  suggestedCypherQuery: string;
}

/**
 * Natural Language Query Parser & NER Extractor for GraphRAG
 */
export function parseInvestigationQuery(query: string): ParsedQuery {
  const q = query.trim().toLowerCase();
  const keywords: string[] = [];

  // 1. Entity Recognition against Synthetic Entity Base
  const matchedEntities: SyntheticEntity[] = [];
  SYNTHETIC_ENTITIES.forEach((e) => {
    const nameMatch = q.includes(e.name.toLowerCase());
    const idMatch = q.includes(e.id.toLowerCase());
    const roleMatch = e.role && q.includes(e.role.toLowerCase());

    if (nameMatch || idMatch) {
      matchedEntities.push(e);
      keywords.push(e.name);
    }
  });

  // Default entity if none detected
  if (matchedEntities.length === 0) {
    const defaultE = SYNTHETIC_ENTITIES[0];
    if (defaultE) matchedEntities.push(defaultE);
  }

  // 2. Intent Classification
  let intent: QueryIntent = "GENERAL_INVESTIGATION";
  let intentLabel = "General Graph Investigation";
  let cypher = "MATCH (n:Entity) RETURN n LIMIT 25";

  if (q.includes("connection") || q.includes("path") || q.includes("between") || q.includes("link") || q.includes("connect")) {
    intent = "RELATIONSHIP_PATH";
    intentLabel = "Multi-Hop Relationship Path Discovery";
    const src = matchedEntities[0]?.name || "Vikramaditya Rawat";
    const tgt = matchedEntities[1]?.name || "Arjun Menon";
    cypher = `MATCH (a:Entity {name: '${src}'}), (b:Entity {name: '${tgt}'})\nMATCH path = shortestPath((a)-[r:RELATIONSHIP*1..4]-(b))\nRETURN path, r.confidence, r.type`;
  } else if (q.includes("influential") || q.includes("influence") || q.includes("kingpin") || q.includes("pagerank") || q.includes("centrality") || q.includes("top")) {
    intent = "CENTRALITY_INFLUENCE";
    intentLabel = "Network Centrality & Kingpin Authority Analysis";
    cypher = `MATCH (n:Entity)\nWHERE n.riskScore >= 70\nRETURN n.name, n.role, n.pageRankScore, n.betweennessScore\nORDER BY n.pageRankScore DESC\nLIMIT 10`;
  } else if (q.includes("risk") || q.includes("why") || q.includes("score") || q.includes("explain") || q.includes("threat")) {
    intent = "RISK_EXPLANATION";
    intentLabel = "Explainable Risk Attribution & Score Breakdown";
    const ent = matchedEntities[0]?.name || "Vikramaditya Rawat";
    cypher = `MATCH (e:Entity {name: '${ent}'})-[r]-(neighbor)\nOPTIONAL MATCH (e)-[:ASSOCIATED_WITH]->(c:CaseDocket)\nRETURN e.name, e.riskScore, count(neighbor) AS degree, collect(neighbor.name) AS associates`;
  } else if (q.includes("anomaly") || q.includes("unusual") || q.includes("loop") || q.includes("circular") || q.includes("spike") || q.includes("burst")) {
    intent = "ANOMALY_PATTERNS";
    intentLabel = "Behavioral Anomaly & Financial Layering Detection";
    cypher = `MATCH (a:BankAccount)-[r1:TRANSFERRED_TO]->(b:Entity)-[r2:TRANSFERRED_TO]->(c:Entity)-[r3:TRANSFERRED_TO]->(a)\nWHERE r1.amountINR > 1000000\nRETURN a, b, c, r1.amountINR, r2.amountINR, r3.amountINR`;
  } else if (q.includes("burner") || q.includes("imei") || q.includes("sim") || q.includes("device") || q.includes("phone")) {
    intent = "BURNER_DEVICE_TRACKING";
    intentLabel = "Burner Hardware IMEI & SIM Card Hopping";
    cypher = `MATCH (d:Device)-[r:OPERATED_BY]->(p:Person)\nMATCH (d)-[:HAS_SIM]->(s:Phone)\nRETURN d.imei, p.name, count(s) AS totalSims\nHAVING totalSims >= 3`;
  } else if (q.includes("community") || q.includes("cluster") || q.includes("syndicate") || q.includes("group")) {
    intent = "COMMUNITY_STRUCTURE";
    intentLabel = "Louvain Community Cluster & Modularity Analysis";
    cypher = `MATCH (e:Entity)\nRETURN e.investigationGroup AS cluster, count(e) AS memberCount, avg(e.riskScore) AS avgClusterRisk\nORDER BY memberCount DESC`;
  } else if (q.includes("briefing") || q.includes("summarize") || q.includes("summary") || q.includes("report") || q.includes("dossier")) {
    intent = "CASE_BRIEFING";
    intentLabel = "Full Case Intelligence Briefing Synthesis";
    cypher = `MATCH (c:CaseDocket {id: 'CASE-2026-N09'})<-[:LINKED_TO_CASE]-(e:Entity)\nMATCH (e)-[r]-(neighbor)\nRETURN c, collect(DISTINCT e) AS suspects, count(r) AS totalLinks`;
  }

  return {
    rawQuery: query,
    intent,
    intentLabel,
    confidenceScore: 94,
    extractedEntities: matchedEntities,
    extractedEntityIds: matchedEntities.map((e) => e.id),
    targetCaseId: "CASE-2026-N09",
    targetCommunity: matchedEntities[0]?.investigationGroup || "Noida Tech Support Scam Ring",
    extractedKeywords: Array.from(new Set(keywords)),
    suggestedCypherQuery: cypher,
  };
}
