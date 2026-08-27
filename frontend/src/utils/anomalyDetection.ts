import type {
  AnomalyCategory,
  AnomalySeverity,
  AnomalyStatus,
} from "./anomalyRules";
import type {
  CircularLoopPattern,
  CommunicationBurstPattern,
  BurnerDevicePattern,
  NetworkGrowthPattern,
  LocationCoLocationPattern,
} from "./patternAnalysis";

export interface InvestigationNote {
  id: string;
  author: string;
  timestamp: string;
  content: string;
}

export interface AnomalyAlert {
  id: string;
  ruleId: string;
  category: AnomalyCategory;
  title: string;
  severity: AnomalySeverity;
  confidenceScore: number; // 0 to 100
  timestamp: string;
  caseId: string;
  status: AnomalyStatus;
  assignedAnalyst?: string;
  primaryEntityId: string;
  primaryEntityName: string;
  relatedEntityIds: string[];
  notes: InvestigationNote[];
  // Structured Pattern Details
  circularLoop?: CircularLoopPattern;
  communicationBurst?: CommunicationBurstPattern;
  burnerDevice?: BurnerDevicePattern;
  networkGrowth?: NetworkGrowthPattern;
  locationCoLocation?: LocationCoLocationPattern;
  // 3-Tier Explainability Breakdown
  observation: string;
  analysis: string;
  assessment: string;
}

export const SYNTHETIC_ANOMALY_ALERTS: AnomalyAlert[] = [
  {
    id: "ALT-2026-001",
    ruleId: "RULE-FIN-03",
    category: "CIRCULAR_FINANCIAL_LOOP",
    title: "Layered 4-Hop Circular Fund Recycling Detected",
    severity: "CRITICAL",
    confidenceScore: 96,
    timestamp: "2026-08-26T14:32:00Z",
    caseId: "CASE-2026-N09",
    status: "INVESTIGATING",
    assignedAnalyst: "Insp. D. Bose",
    primaryEntityId: "ENT-P-01",
    primaryEntityName: "Vikramaditya Rawat",
    relatedEntityIds: ["ENT-B-01", "ENT-O-01", "ENT-P-06"],
    notes: [
      {
        id: "NOTE-1",
        author: "Insp. D. Bose",
        timestamp: "2026-08-26T16:00:00Z",
        content: "Flagged ICICI Current Account #908129. Issued Section 91 notice to bank Nodal Officer.",
      },
    ],
    circularLoop: {
      loopId: "LOOP-901",
      originEntityId: "ENT-B-01",
      originEntityName: "ICICI Mule Account #908129",
      totalTransferredINR: 15400000, // ₹1.54 Cr
      hopCount: 4,
      confidence: 96,
      hops: [
        {
          hopIndex: 1,
          fromEntityId: "ENT-B-01",
          fromEntityName: "ICICI Mule Account (Rawat Syndicate)",
          toEntityId: "ENT-O-01",
          toEntityName: "Apex Global Infotech (Shell Corp)",
          amountINR: 15400000,
          timestamp: "2026-08-25T10:15:00Z",
          channel: "RTGS Commercial Transfer",
        },
        {
          hopIndex: 2,
          fromEntityId: "ENT-O-01",
          fromEntityName: "Apex Global Infotech",
          toEntityId: "ENT-P-06",
          toEntityName: "Arjun Menon (Hawala Broker)",
          amountINR: 14850000,
          timestamp: "2026-08-25T13:40:00Z",
          channel: "Sub-Vendor Consulting Invoice",
        },
        {
          hopIndex: 3,
          fromEntityId: "ENT-P-06",
          fromEntityName: "Arjun Menon",
          toEntityId: "ENT-P-01",
          toEntityName: "Vikramaditya Rawat",
          amountINR: 14200000,
          timestamp: "2026-08-25T18:20:00Z",
          channel: "Angadia Courier / USDT OTC Cash",
        },
        {
          hopIndex: 4,
          fromEntityId: "ENT-P-01",
          fromEntityName: "Vikramaditya Rawat",
          toEntityId: "ENT-B-01",
          toEntityName: "ICICI Mule Account #908129",
          amountINR: 14000000,
          timestamp: "2026-08-26T09:05:00Z",
          channel: "Cash Deposit via CDM Terminal",
        },
      ],
    },
    observation: "4 distinct entity accounts transacted ₹1.54 Cr across 4 hops within 23 hours, returning funds to the origin controller with 9% haircut margin.",
    analysis: "Topology and transaction velocity match classic money-laundering smurfing and circular layering patterns designed to evade FIU-IND STR thresholds.",
    assessment: "High-priority candidate for Section 102 CrPC account debit freeze and FIU-IND Finnet corroboration.",
  },
  {
    id: "ALT-2026-002",
    ruleId: "RULE-DEV-02",
    category: "DEVICE_HOPPING",
    title: "Burner Hardware & Rapid SIM Card Cycling (8 IMSIs)",
    severity: "CRITICAL",
    confidenceScore: 94,
    timestamp: "2026-08-26T11:15:00Z",
    caseId: "CASE-2026-N09",
    status: "DETECTED",
    assignedAnalyst: undefined,
    primaryEntityId: "ENT-D-01",
    primaryEntityName: "OnePlus Nord Burner (IMEI: 864902049182019)",
    relatedEntityIds: ["ENT-P-01", "ENT-P-02"],
    notes: [],
    burnerDevice: {
      imei: "864902049182019",
      deviceName: "OnePlus Nord 5G (Burner Handset)",
      primarySuspectId: "ENT-P-01",
      primarySuspectName: "Vikramaditya Rawat",
      concurrentIdentitiesCount: 8,
      associatedSimCards: [
        {
          imsi: "404450918230192",
          phoneNumber: "+91-98710-44912",
          carrier: "Airtel Delhi",
          firstSeen: "2026-08-20T08:00:00Z",
          lastSeen: "2026-08-21T18:00:00Z",
          isCurrentActive: false,
        },
        {
          imsi: "404450918230881",
          phoneNumber: "+91-98110-33821",
          carrier: "Vi NCR",
          firstSeen: "2026-08-22T09:30:00Z",
          lastSeen: "2026-08-23T14:15:00Z",
          isCurrentActive: false,
        },
        {
          imsi: "404450918231902",
          phoneNumber: "+91-99201-88402",
          carrier: "Jio Mumbai",
          firstSeen: "2026-08-24T11:00:00Z",
          lastSeen: "2026-08-26T11:00:00Z",
          isCurrentActive: true,
        },
        {
          imsi: "404450918232410",
          phoneNumber: "+91-97114-55091",
          carrier: "BSNL Odisha",
          firstSeen: "2026-08-26T12:00:00Z",
          lastSeen: "2026-08-26T15:30:00Z",
          isCurrentActive: true,
        },
      ],
    },
    observation: "A single handset IMEI was linked to 8 distinct IMSI SIM registrations within 6 days across multiple state telecom circles.",
    analysis: "Evidences deliberate anti-forensic operational security (OPSEC) to thwart cell-site triangulation and CDR warrants.",
    assessment: "Submit IMEI tracker request to National Equipment Identity Register (CEIR) and deploy IMSI-catcher surveillance.",
  },
  {
    id: "ALT-2026-003",
    ruleId: "RULE-COMM-01",
    category: "COMMUNICATION_BURST",
    title: "High-Frequency VoIP/Cellular Burst (+350% Surge)",
    severity: "HIGH",
    confidenceScore: 88,
    timestamp: "2026-08-25T20:10:00Z",
    caseId: "CASE-2026-B12",
    status: "UNDER_REVIEW",
    assignedAnalyst: "Insp. D. Bose",
    primaryEntityId: "ENT-P-02",
    primaryEntityName: "Pooja Sharma",
    relatedEntityIds: ["ENT-P-01", "ENT-P-03"],
    notes: [
      {
        id: "NOTE-2",
        author: "Insp. D. Bose",
        timestamp: "2026-08-25T22:00:00Z",
        content: "Call burst coincided with victim complaint FIR #402/2026 filed at Cyber Police Station Noida.",
      },
    ],
    communicationBurst: {
      entityId: "ENT-P-02",
      entityName: "Pooja Sharma",
      baselineDailyAvg: 12,
      peakDailyCount: 54,
      surgePercentage: 350,
      targetEntities: ["ENT-P-01", "ENT-P-03", "ENT-P-04"],
      history: [
        { date: "2026-08-20", callCount: 10, baseline: 12, isSpike: false },
        { date: "2026-08-21", callCount: 14, baseline: 12, isSpike: false },
        { date: "2026-08-22", callCount: 11, baseline: 12, isSpike: false },
        { date: "2026-08-23", callCount: 18, baseline: 12, isSpike: false },
        { date: "2026-08-24", callCount: 42, baseline: 12, isSpike: true },
        { date: "2026-08-25", callCount: 54, baseline: 12, isSpike: true },
        { date: "2026-08-26", callCount: 38, baseline: 12, isSpike: true },
      ],
    },
    observation: "Call frequency escalated from a 12-call daily baseline to 54 calls/day (+350%) focused on 3 core operatives.",
    analysis: "Corresponds with active coordination during multi-victim fraudulent tech support credential harvesting operations.",
    assessment: "Correlate with CDR tower pings and obtain Section 5(2) Telegraph Act lawful interception authorization.",
  },
  {
    id: "ALT-2026-004",
    ruleId: "RULE-NET-04",
    category: "NETWORK_EXPANSION_SURGE",
    title: "Inter-Syndicate Bridge Link Surge (+14 New Edges)",
    severity: "HIGH",
    confidenceScore: 89,
    timestamp: "2026-08-24T18:45:00Z",
    caseId: "CASE-2026-R44",
    status: "INVESTIGATING",
    assignedAnalyst: "Insp. D. Bose",
    primaryEntityId: "ENT-P-06",
    primaryEntityName: "Arjun Menon",
    relatedEntityIds: ["ENT-P-01", "ENT-P-05"],
    notes: [],
    networkGrowth: {
      communityId: 0,
      communityName: "Noida Tech Support Scam Ring",
      priorSize: 18,
      currentSize: 32,
      netNewConnections: 14,
      growthRatePercentage: 77.8,
      timeWindowDays: 5,
      newBridgeNodes: [
        { id: "ENT-P-06", name: "Arjun Menon" },
        { id: "ENT-O-01", name: "Apex Global Infotech" },
      ],
    },
    observation: "Cluster connectivity surged with 14 new relationship edges connecting to the LockNet Ransomware Syndicate within 5 days.",
    analysis: "Indicates strategic partnership where tech-support extortion infrastructure is being leveraged for ransomware payload distribution.",
    assessment: "Escalate to National Critical Information Infrastructure Protection Centre (NCIIPC) and CERT-In.",
  },
  {
    id: "ALT-2026-005",
    ruleId: "RULE-GEO-05",
    category: "GEOSPATIAL_CO_LOCATION",
    title: "Suspect Tower Co-Location at Sector 62 Safe House",
    severity: "MEDIUM",
    confidenceScore: 82,
    timestamp: "2026-08-23T23:15:00Z",
    caseId: "CASE-2026-N09",
    status: "DETECTED",
    assignedAnalyst: undefined,
    primaryEntityId: "ENT-L-01",
    primaryEntityName: "Sector 62 Telecom Hub, Noida",
    relatedEntityIds: ["ENT-P-01", "ENT-P-02", "ENT-P-03"],
    notes: [],
    locationCoLocation: {
      towerId: "TWR-NOIDA-62-09B",
      cellSector: "Sector 62, Electronic City, Noida",
      locationName: "C-Block Commercial Complex (Illicit Call Center)",
      latitude: 28.628,
      longitude: 77.3649,
      timeWindow: {
        start: "2026-08-23T22:00:00Z",
        end: "2026-08-24T04:00:00Z",
      },
      coLocationConfidence: 82,
      coLocatedEntities: [
        {
          entityId: "ENT-P-01",
          name: "Vikramaditya Rawat",
          role: "Master Syndicate Controller",
          riskScore: 94,
          phoneOrImei: "+91-98710-44912",
        },
        {
          entityId: "ENT-P-02",
          name: "Pooja Sharma",
          role: "Operations Supervisor",
          riskScore: 82,
          phoneOrImei: "+91-98110-33821",
        },
        {
          entityId: "ENT-P-03",
          name: "Rohan Verma",
          role: "Mule Account Handler",
          riskScore: 78,
          phoneOrImei: "+91-98200-11223",
        },
      ],
    },
    observation: "3 primary suspects registered simultaneous CDR tower pings within a 200m radius of Sector 62 Noida between 22:00 and 04:00.",
    analysis: "Indicates physical co-presence at suspected call-center night-shift facility during active extortion campaigns.",
    assessment: "Dispatch physical surveillance team to verify commercial lease records and electricity consumption profiles.",
  },
];
