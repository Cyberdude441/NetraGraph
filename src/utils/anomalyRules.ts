export type AnomalyCategory =
  | "COMMUNICATION_BURST"
  | "DEVICE_HOPPING"
  | "CIRCULAR_FINANCIAL_LOOP"
  | "NETWORK_EXPANSION_SURGE"
  | "GEOSPATIAL_CO_LOCATION";

export type AnomalySeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type AnomalyStatus =
  | "DETECTED"
  | "UNDER_REVIEW"
  | "INVESTIGATING"
  | "RESOLVED"
  | "FALSE_POSITIVE"
  | "ARCHIVED";

export interface AnomalyRule {
  id: string;
  category: AnomalyCategory;
  name: string;
  description: string;
  defaultSeverity: AnomalySeverity;
  thresholdMetric: string;
  thresholdValue: number | string;
  indicatorExplanation: string;
}

export const ANOMALY_RULES: AnomalyRule[] = [
  {
    id: "RULE-COMM-01",
    category: "COMMUNICATION_BURST",
    name: "Sudden Telephony / VoIP Call Volume Surge",
    description: "Triggers when an entity's outgoing or incoming communication events exceed 300% of historical 30-day baseline within a 48-hour window.",
    defaultSeverity: "HIGH",
    thresholdMetric: "Call Volume Surge",
    thresholdValue: "+300%",
    indicatorExplanation: "Indicates coordinated tactical deployment, extortion wave, or pre-raid burner destruction.",
  },
  {
    id: "RULE-DEV-02",
    category: "DEVICE_HOPPING",
    name: "Burner Hardware & Rapid SIM Card Cycling",
    description: "Triggers when a single IMEI hardware identifier is linked to 4+ new IMSI SIM cards within 72 hours, or multiple entities share a single burner device.",
    defaultSeverity: "CRITICAL",
    thresholdMetric: "SIMs per IMEI",
    thresholdValue: ">= 4 SIMs in 72h",
    indicatorExplanation: "Signature burner hardware hopping used to evade Section 91 CrPC lawful interception orders.",
  },
  {
    id: "RULE-FIN-03",
    category: "CIRCULAR_FINANCIAL_LOOP",
    name: "Circular Layering & Mule Account Recycling",
    description: "Triggers when funds dispersed from Source Account A route through 2+ intermediate mule/POS accounts and return to Origin Node A or associated crypto on-ramp within 48 hours.",
    defaultSeverity: "CRITICAL",
    thresholdMetric: "Loop Cycle Length",
    thresholdValue: "3 to 5 Hops",
    indicatorExplanation: "Classic money laundering layering mechanism designed to obfuscate proceeds of cyber fraud.",
  },
  {
    id: "RULE-NET-04",
    category: "NETWORK_EXPANSION_SURGE",
    name: "Rapid Community Expansion & Covert Link Formation",
    description: "Triggers when a syndicate cluster gains >= 10 new relationships to a previously disconnected syndicate within a 7-day period.",
    defaultSeverity: "HIGH",
    thresholdMetric: "Inter-Cluster Links",
    thresholdValue: ">= 10 Links in 7d",
    indicatorExplanation: "Indicates merger of criminal networks, new vendor acquisition (e.g. SIM box supplier), or cross-border expansion.",
  },
  {
    id: "RULE-GEO-05",
    category: "GEOSPATIAL_CO_LOCATION",
    name: "Multi-Suspect Cell Tower Co-Location",
    description: "Triggers when 3 or more independent suspect devices register on the same cellular tower sector during an active fraud or extortive campaign.",
    defaultSeverity: "MEDIUM",
    thresholdMetric: "Temporal Co-Location",
    thresholdValue: "< 30 min window, same tower",
    indicatorExplanation: "Identifies physical call center operational hubs, safe houses, or clandestine SIM farm facilities.",
  },
];
