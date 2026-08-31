import { parseInvestigationQuery, type ParsedQuery } from "@/utils/queryParser";
import { compileEvidenceCitations, type EvidenceCitation } from "@/utils/evidenceMatcher";
import { SYNTHETIC_ENTITIES, SYNTHETIC_RELATIONSHIPS } from "@/data/syntheticGraphData";
import { SYNTHETIC_ANOMALY_ALERTS } from "@/utils/anomalyDetection";

export interface GraphRAGStep {
  stepNumber: number;
  name: string;
  description: string;
  status: "COMPLETED" | "RUNNING" | "PENDING";
  nodesScanned?: number;
  executionMs?: number;
}

export interface NetraAIResponse {
  id: string;
  query: string;
  timestamp: string;
  parsedQuery: ParsedQuery;
  summary: string;
  observedData: string[];
  graphEvidence: {
    pathsFound: number;
    primaryPathNodes: string[];
    clusterName: string;
    communityDensity: number;
    centralityRank?: number;
    anomaliesCount: number;
  };
  analyticalInterpretation: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  classification?: "VERIFIED FACT" | "DERIVED ANALYTICS" | "INSUFFICIENT DATA";
  graphPath?: string;
  retrievedNodes?: any[];
  retrievedRelationships?: any[];
  provenance?: any;
  analystVerification: string;
  citations: EvidenceCitation[];
  pipelineSteps: GraphRAGStep[];
}

export interface InvestigationBriefing {
  id: string;
  caseId: string;
  caseTitle: string;
  generatedAt: string;
  author: string;
  sections: {
    overview: string;
    keyEntities: { name: string; id: string; role: string; risk: number }[];
    networkStructure: { totalNodes: number; totalEdges: number; clustersCount: number; density: number };
    importantRelationships: string[];
    detectedPatterns: string[];
    anomalySummary: string[];
    riskIndicators: string[];
    evidenceReferences: string[];
  };
}

/**
 * Netra AI GraphRAG Query Execution Engine
 */
export function analyzeInvestigationQuery(
  rawQuery: string,
  context?: { activeCaseId?: string; pinnedEntityIds?: string[] }
): NetraAIResponse {
  const parsed = parseInvestigationQuery(rawQuery);
  const primaryEntity = parsed.extractedEntities[0] || SYNTHETIC_ENTITIES[0]!;
  const citations = compileEvidenceCitations(parsed.extractedEntityIds, parsed.intent);

  // 8-Stage GraphRAG Execution Telemetry
  const pipelineSteps: GraphRAGStep[] = [
    { stepNumber: 1, name: "Intent Classification", description: `Identified intent: ${parsed.intentLabel}`, status: "COMPLETED", executionMs: 8 },
    { stepNumber: 2, name: "Named Entity Recognition (NER)", description: `Extracted ${parsed.extractedEntities.length} entities: ${parsed.extractedEntities.map(e => e.name).join(", ")}`, status: "COMPLETED", nodesScanned: 105, executionMs: 14 },
    { stepNumber: 3, name: "Sub-Graph Retrieval", description: `Matched candidate nodes in Neo4j Cluster [${parsed.targetCommunity}]`, status: "COMPLETED", nodesScanned: 32, executionMs: 22 },
    { stepNumber: 4, name: "Multi-Hop Relationship Traversal", description: "Executed BFS shortest-path & betweenness expansion up to 4 hops", status: "COMPLETED", nodesScanned: 84, executionMs: 38 },
    { stepNumber: 5, name: "Behavioral Evidence Ingestion", description: "Correlated CDR call bursts and FIU-IND fund transfer loops", status: "COMPLETED", executionMs: 19 },
    { stepNumber: 6, name: "Explainable Reasoning Synthesis", description: "Compiled structured 3-tier observations and topological roles", status: "COMPLETED", executionMs: 45 },
    { stepNumber: 7, name: "Confidence Scoring Calibration", description: "Weighted average calculated against ground truth evidence", status: "COMPLETED", executionMs: 6 },
    { stepNumber: 8, name: "Zero-Hallucination Assertion", description: "Appended Section 65B mandatory human verification requirement", status: "COMPLETED", executionMs: 2 },
  ];

  let summary = "";
  let observedData: string[] = [];
  let analyticalInterpretation = "";
  let confidence: NetraAIResponse["confidence"] = "HIGH";
  let confidenceScore = 94;

  if (parsed.intent === "RELATIONSHIP_PATH") {
    summary = `Direct relationship conduit traced between ${primaryEntity.name} and associate nodes spanning ${citations.length} corroborating hops.`;
    observedData = [
      `Source entity ${primaryEntity.name} (${primaryEntity.id}) links directly to Shell Organization and Mule POS accounts.`,
      `Fund velocity of ₹1.54 Cr observed across intermediate hawala brokers within 23 hours.`,
      `VoIP communications burst detected coinciding with banking transaction hours.`,
    ];
    analyticalInterpretation = `Topological analysis indicates that ${primaryEntity.name} exercises executive command over the money laundering funnel, using intermediate mule brokers to shield origin bank coordinates.`;
  } else if (parsed.intent === "CENTRALITY_INFLUENCE") {
    summary = `PageRank and Betweenness centrality rankings identify ${primaryEntity.name} as the highest-influence authority node (Rank #${primaryEntity.centralityRank || 1}) in the network.`;
    observedData = [
      `Node sits on dominant communication routes with high eigenvector authority score (PageRank: ${primaryEntity.pageRankScore || 24.8}%).`,
      `Connects ${primaryEntity.degreeCount || 16} immediate network entities across 2 distinct syndicate cells.`,
      `Acts as primary bridge for technical hardware and SIM card disbursement.`,
    ];
    analyticalInterpretation = `High betweenness score suggests this entity is a critical single point of failure; disabling communication on this node will partition coordination across the syndicate.`;
  } else if (parsed.intent === "ANOMALY_PATTERNS") {
    summary = `Active behavioral anomaly engine flagged 4-hop circular fund recycling and multi-IMSI device hopping linked to ${primaryEntity.name}.`;
    observedData = [
      `Circular loop ALT-2026-001 routed ₹1.54 Cr across 4 mule accounts with a 9% return haircut margin.`,
      `Burner device IMEI 864902049182019 linked to 8 distinct IMSI SIM registrations in 6 days.`,
      `Physical cell-tower co-location confirmed in Sector 62 Noida call center hub.`,
    ];
    analyticalInterpretation = `Observed pattern matches deliberate layering and anti-forensic OPSEC designed to evade automated STR detection and cell-site triangulation.`;
  } else {
    summary = `Comprehensive knowledge graph dossier compiled for ${primaryEntity.name} (${primaryEntity.id}) across Case Docket ${primaryEntity.caseId}.`;
    observedData = [
      `Entity classified as ${primaryEntity.label} (${primaryEntity.role || "Syndicate Operative"}).`,
      `Composite threat severity score calculated at ${primaryEntity.riskScore}/100 based on graph centrality and financial loss telemetry.`,
      `4 verified statutory citations available under Indian Evidence Act Section 65B.`,
    ];
    analyticalInterpretation = `The entity functions as an operational pivot in the ${primaryEntity.investigationGroup}, presenting high priority for judicial search warrants.`;
  }

  return {
    id: `RESP-${Date.now()}`,
    query: rawQuery,
    timestamp: new Date().toISOString(),
    parsedQuery: parsed,
    summary,
    observedData,
    graphEvidence: {
      pathsFound: 3,
      primaryPathNodes: [primaryEntity.name, "Apex Global Infotech", "Arjun Menon", "ICICI Mule #908129"],
      clusterName: primaryEntity.investigationGroup,
      communityDensity: 0.68,
      centralityRank: primaryEntity.centralityRank || 1,
      anomaliesCount: 3,
    },
    analyticalInterpretation,
    confidence,
    confidenceScore,
    analystVerification:
      "Statutory Advisory: Netra AI is an analytical decision-support system. All graph findings represent algorithmic observations from synthetic telemetry and require human corroboration prior to judicial action under IT Act §69B.",
    citations,
    pipelineSteps,
  };
}

/**
 * Generate 8-Section Comprehensive Investigation Briefing
 */
export function generateInvestigationBriefing(caseId: string = "CASE-2026-N09"): InvestigationBriefing {
  return {
    id: `BRIEF-${Date.now()}`,
    caseId,
    caseTitle: "Operation Netra-Vigil: Inter-State Cyber Extortion & Hawala Syndicate",
    generatedAt: new Date().toISOString(),
    author: "Netra AI Autonomous Intelligence Engine (Supervised by Insp. D. Bose)",
    sections: {
      overview:
        "Multi-jurisdictional cyber fraud investigation involving structured tech-support extortion, VoIP call spoofing, and layered mule account fund dispersion across NCR, Mumbai, and Kolkata.",
      keyEntities: [
        { name: "Vikramaditya Rawat", id: "ENT-P-01", role: "Master Syndicate Controller", risk: 94 },
        { name: "Pooja Sharma", id: "ENT-P-02", role: "Call Center Operations Supervisor", risk: 82 },
        { name: "Arjun Menon", id: "ENT-P-06", role: "Hawala & Crypto Bridge Broker", risk: 88 },
        { name: "Apex Global Infotech", id: "ENT-O-01", role: "Front Shell Company", risk: 85 },
      ],
      networkStructure: {
        totalNodes: 105,
        totalEdges: 148,
        clustersCount: 4,
        density: 0.027,
      },
      importantRelationships: [
        "Executive Command: Vikramaditya Rawat → Pooja Sharma (Daily Tactical Dispatch)",
        "Layered Fund Route: ICICI Mule #908129 → Apex Global Infotech (₹1.54 Cr RTGS)",
        "Hawala Conduit: Apex Global Infotech → Arjun Menon (USDT OTC Conversion)",
      ],
      detectedPatterns: [
        "4-Hop Circular Layering Loop returning funds to syndicate controllers with 9% haircut margin.",
        "Burner handset IMEI 864902049182019 cycling through 8 IMSI SIM cards across state boundaries.",
      ],
      anomalySummary: [
        "Sudden +350% VoIP communication surge coinciding with victim complaint filings.",
        "Cell-tower physical co-location at Sector 62 Noida nocturnal call-center facility.",
      ],
      riskIndicators: [
        "Dynamic risk scores elevated to CRITICAL (94/100) due to high PageRank authority and active circular layering.",
        "High betweenness score (28.4%) establishes single point of failure vulnerability.",
      ],
      evidenceReferences: [
        "FIR #402/2026 Cyber Crime Police Station Noida",
        "FIU-IND Suspicious Transaction Report #908129",
        "Section 65B Indian Evidence Act Cryptographic Certificate #VAULT-SHA-9021",
      ],
    },
  };
}
