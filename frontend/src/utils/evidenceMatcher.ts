export interface EvidenceCitation {
  id: string;
  sourceType: "ENTITY_NODE" | "RELATIONSHIP_LINK" | "TIMELINE_EVENT" | "ANOMALY_RECORD";
  title: string;
  subtitle: string;
  confidenceScore: number;
  deepLinkRoute: "/network" | "/profiles" | "/anomalies" | "/analytics";
  deepLinkId: string;
  statutoryBasis?: string;
}

export function compileEvidenceCitations(
  entityIds: string[],
  intent: string
): EvidenceCitation[] {
  const citations: EvidenceCitation[] = [
    {
      id: "CITE-01",
      sourceType: "ENTITY_NODE",
      title: "Master Profile: Vikramaditya Rawat",
      subtitle: "ENT-P-01 · Cyber Cell Dossier · Risk Score 94/100",
      confidenceScore: 98,
      deepLinkRoute: "/profiles",
      deepLinkId: "ENT-P-01",
      statutoryBasis: "Section 65B Indian Evidence Act Certified Dossier",
    },
    {
      id: "CITE-02",
      sourceType: "RELATIONSHIP_LINK",
      title: "Direct Fund Flow: ICICI Mule → Apex Global Infotech",
      subtitle: "REL-004 · ₹1.54 Cr RTGS Commercial Transfer",
      confidenceScore: 95,
      deepLinkRoute: "/network",
      deepLinkId: "REL-004",
      statutoryBasis: "FIU-IND STR #908129 Banking Telemetry",
    },
    {
      id: "CITE-03",
      sourceType: "ANOMALY_RECORD",
      title: "Behavioral Detection: Circular Fund Recycling Loop",
      subtitle: "ALT-2026-001 · 4-Hop Closed Circuit Layering",
      confidenceScore: 96,
      deepLinkRoute: "/anomalies",
      deepLinkId: "ALT-2026-001",
      statutoryBasis: "Algorithmic Graph Cycle Detection Engine",
    },
    {
      id: "CITE-04",
      sourceType: "TIMELINE_EVENT",
      title: "Surveillance Intercept: VoIP Extortion Call Burst",
      subtitle: "EVT-102 · +350% Telephony Surge during victim campaign",
      confidenceScore: 88,
      deepLinkRoute: "/anomalies",
      deepLinkId: "ALT-2026-003",
      statutoryBasis: "Section 5(2) Indian Telegraph Act Intercept",
    },
  ];

  return citations;
}
