/**
 * NetraGraph Cyber Threat & Network Intelligence Schema & Starter Telemetry.
 * Strictly adheres to verified public NCRB categories and authorized case structures.
 */

export interface SyntheticEntity {
  id: string;
  name: string;
  label: "Person" | "Phone" | "Location" | "Vehicle" | "Organization" | "BankAccount" | "Device" | "Event" | "State" | "CrimeCategory" | "CrimeMotive" | "Evidence" | "MLPrediction" | "IP" | "Domain" | "Email" | "Hash";
  role?: string;
  riskScore: number;
  confidenceScore: number;
  caseId: string;
  investigationGroup?: string;
  communityId?: number;
  firstSeen: string;
  lastSeen: string;
  sourceDocument?: string;
  metadata: {
    category?: string;
    description: string;
    jurisdiction?: string;
    statutorySection?: string;
    ipAddress?: string;
    accountNumber?: string;
    phoneDeviceId?: string;
    tags?: string[];
    attributes?: Record<string, string | number>;
  };
}

export interface SyntheticRelationship {
  id: string;
  sourceId: string;
  targetId: string;
  type: string;
  label: string;
  weight: number;
  confidence: number;
  timestamp: string;
  detail: string;
  metadata?: Record<string, any>;
}

export const SYNTHETIC_ENTITIES: SyntheticEntity[] = [
  // 1. Authorized Case CASE-2024-DEL-0891 Entities
  {
    id: "PER-05",
    name: "Amit Joshi",
    label: "Person",
    role: "Technical Support Coordinator",
    riskScore: 93,
    confidenceScore: 0.98,
    caseId: "CASE-2024-DEL-0891",
    firstSeen: "2024-01-15",
    lastSeen: "2026-08-24",
    sourceDocument: "FIR-2024-DEL-0891 (Cyber Crime PS Central Delhi)",
    metadata: {
      category: "Suspect Operative",
      description: "Operated unauthorized technical support dialer facility.",
      jurisdiction: "Delhi / NCR",
      tags: ["Suspect", "Arrested", "VoIP Fraud"],
    },
  },
  {
    id: "ORG-03",
    name: "TechGlobal Support Services",
    label: "Organization",
    role: "Front Company",
    riskScore: 90,
    confidenceScore: 0.96,
    caseId: "CASE-2024-DEL-0891",
    firstSeen: "2023-11-10",
    lastSeen: "2026-08-20",
    sourceDocument: "MCA Company Master Data / Bank KYC",
    metadata: {
      category: "Corporate Shell Entity",
      description: "Business enterprise registered in Noida Sector-62.",
      jurisdiction: "Uttar Pradesh",
      tags: ["Front Entity", "Premises Sealed"],
    },
  },
  {
    id: "DEV-03",
    name: "VoIP SIP Trunk #0912",
    label: "Device",
    role: "VoIP Gateway",
    riskScore: 84,
    confidenceScore: 0.95,
    caseId: "CASE-2024-DEL-0891",
    firstSeen: "2024-02-01",
    lastSeen: "2026-08-22",
    sourceDocument: "DoT Telecom Subpoena #8819",
    metadata: {
      category: "Telecommunication Intercept",
      description: "VoIP line spoofing overseas toll-free numbers.",
      phoneDeviceId: "SIP-TRUNK-1800-449-102",
      tags: ["VoIP", "Subpoenaed"],
    },
  },
  {
    id: "FIN-03",
    name: "Axis Overseas Escrow #77192",
    label: "BankAccount",
    role: "Escrow Account",
    riskScore: 86,
    confidenceScore: 0.99,
    caseId: "CASE-2024-DEL-0891",
    firstSeen: "2024-01-20",
    lastSeen: "2026-08-25",
    sourceDocument: "Axis Bank Statement / 1930 Freeze Order",
    metadata: {
      category: "Financial Flow",
      description: "Wire transfer escrow holding illicit call center proceeds.",
      accountNumber: "AXIS-77192 (Connaught Place)",
      tags: ["Frozen", "Financial Forensic"],
    },
  },

  // 2. Authorized Case CASE-2024-OD-0412 Entities
  {
    id: "PER-09",
    name: "Debabrata Nayak",
    label: "Person",
    role: "Transit Coordinator",
    riskScore: 88,
    confidenceScore: 0.97,
    caseId: "CASE-2024-OD-0412",
    firstSeen: "2024-03-01",
    lastSeen: "2026-08-20",
    sourceDocument: "FIR-2024-OD-0412 (Bhubaneswar Cyber Police Station)",
    metadata: {
      category: "Suspect Operative",
      description: "Coordinated illicit SIM Box SMS gateways across Odisha transit corridor.",
      jurisdiction: "Odisha",
      tags: ["In Custody", "SIM Box Operator"],
    },
  },
  {
    id: "DEV-07",
    name: "SIM Box 16-Channel #16",
    label: "Device",
    role: "GSM Gateway",
    riskScore: 86,
    confidenceScore: 0.99,
    caseId: "CASE-2024-OD-0412",
    firstSeen: "2024-03-10",
    lastSeen: "2026-08-20",
    sourceDocument: "CFSL Physical Seizure Memo #0412",
    metadata: {
      category: "Physical Seizure",
      description: "16-channel automated GSM gateway blasting phishing links.",
      phoneDeviceId: "SIMBOX-16PORT (Cuttack)",
      tags: ["Hardware Seized", "CFSL Forensic"],
    },
  },
  {
    id: "FIN-06",
    name: "Canara Transit Acct #19802",
    label: "BankAccount",
    role: "Transit Account",
    riskScore: 79,
    confidenceScore: 0.95,
    caseId: "CASE-2024-OD-0412",
    firstSeen: "2024-03-15",
    lastSeen: "2026-08-22",
    sourceDocument: "Canara Bank Statement (Cuttack Branch)",
    metadata: {
      category: "Financial Flow",
      description: "Regional transit account receiving ATM card clone withdrawals.",
      accountNumber: "CANARA-19802",
      tags: ["Lien Marked", "Bank Intercept"],
    },
  },

  // 3. Authorized Case CASE-2024-TG-1044 Entities
  {
    id: "PER-07",
    name: "Karthik Reddy",
    label: "Person",
    role: "Malware Author",
    riskScore: 96,
    confidenceScore: 0.99,
    caseId: "CASE-2024-TG-1044",
    firstSeen: "2023-08-10",
    lastSeen: "2026-08-15",
    sourceDocument: "FIR-2024-TG-1044 (Cyberabad Cyber Crime PS) / Interpol Red Notice",
    metadata: {
      category: "Suspect Operative",
      description: "Author of LockNet ransomware variant targeting healthcare networks.",
      jurisdiction: "Telangana",
      tags: ["Red Corner Notice", "Ransomware Developer"],
    },
  },
  {
    id: "DEV-05",
    name: "C2 Command Server Frankfurt",
    label: "Device",
    role: "C2 Server",
    riskScore: 91,
    confidenceScore: 0.98,
    caseId: "CASE-2024-TG-1044",
    firstSeen: "2023-09-01",
    lastSeen: "2026-08-18",
    sourceDocument: "Europol Server Mirror Image #9912",
    metadata: {
      category: "Network Infrastructure",
      description: "Botnet command & control server hosting decryption master keys.",
      ipAddress: "185.220.101.5",
      tags: ["Takedown Completed", "C2 Node"],
    },
  },
];

export const SYNTHETIC_RELATIONSHIPS: SyntheticRelationship[] = [
  {
    id: "REL-EV-101",
    sourceId: "PER-05",
    targetId: "ORG-03",
    type: "BENEFICIAL_OWNER",
    label: "OWNERSHIP",
    weight: 9,
    confidence: 0.98,
    timestamp: "2024-01-15T10:00:00Z",
    detail: "100% Shareholder & Director",
  },
  {
    id: "REL-EV-102",
    sourceId: "PER-05",
    targetId: "DEV-03",
    type: "COMMUNICATION_LINK",
    label: "OPERATES",
    weight: 8,
    confidence: 0.95,
    timestamp: "2024-02-01T12:00:00Z",
    detail: "VoIP Dialing Logs & Active Trunking",
  },
  {
    id: "REL-EV-103",
    sourceId: "ORG-03",
    targetId: "FIN-03",
    type: "FINANCIAL_TRANSFER",
    label: "ESCROW_FLOW",
    weight: 9,
    confidence: 0.99,
    timestamp: "2024-01-20T14:30:00Z",
    detail: "₹12.4 Cr Frozen Wire Transfer Account",
  },
  {
    id: "REL-EV-202",
    sourceId: "PER-09",
    targetId: "DEV-07",
    type: "OPERATES",
    label: "OPERATES",
    weight: 9,
    confidence: 0.99,
    timestamp: "2024-03-10T08:00:00Z",
    detail: "SIM Box hardware confiscated in physical raid",
  },
  {
    id: "REL-EV-203",
    sourceId: "PER-09",
    targetId: "FIN-06",
    type: "FINANCIAL_TRANSFER",
    label: "ATM_WITHDRAWALS",
    weight: 8,
    confidence: 0.95,
    timestamp: "2024-03-15T11:00:00Z",
    detail: "₹1.4 Cr ATM withdrawals",
  },
  {
    id: "REL-EV-302",
    sourceId: "PER-07",
    targetId: "DEV-05",
    type: "COMMAND_CONTROL",
    label: "C2_HEARTBEAT",
    weight: 9,
    confidence: 0.98,
    timestamp: "2023-09-01T16:00:00Z",
    detail: "C2 Server Heartbeat & Decryption Keys",
  },
];
