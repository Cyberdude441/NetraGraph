export interface GlobalAuditRecord {
  id: string;
  timestamp: string;
  officerName: string;
  officerRole: string;
  module: "GRAPH_CORE" | "ENTITY_RESOLUTION" | "NETWORK_ANALYTICS" | "ANOMALY_ENGINE" | "EVIDENCE_VAULT" | "REPORT_BUILDER" | "NETRA_AI";
  action: string;
  details: string;
  ipAddress: string;
  verificationHash: string;
}

export const INITIAL_GLOBAL_AUDIT_LOGS: GlobalAuditRecord[] = [
  {
    id: "AUD-GLB-001",
    timestamp: "2026-08-27T10:15:00Z",
    officerName: "Insp. D. Bose",
    officerRole: "Senior Cyber Forensic Analyst",
    module: "REPORT_BUILDER",
    action: "Judicial Intelligence Report Compiled",
    details: "Generated Case Dossier NCRB-CYBER-2026-N09-REP-01 with 7 certified sections.",
    ipAddress: "10.42.18.91 (Cyber HQ Secure VPN)",
    verificationHash: "4f9b1c3e5b7d9f1a3c5e7b8f4b2a9e7c1d3f5b6a0e8d7c9b1a3e5f7a9c1a3b5d",
  },
  {
    id: "AUD-GLB-002",
    timestamp: "2026-08-27T09:40:00Z",
    officerName: "Insp. D. Bose",
    officerRole: "Senior Cyber Forensic Analyst",
    module: "EVIDENCE_VAULT",
    action: "Evidence Block #4 Cryptographically Sealed",
    details: "Appended CEIR National IMEI Telemetry to immutable SHA-256 evidence chain.",
    ipAddress: "10.42.18.91 (Cyber HQ Secure VPN)",
    verificationHash: "5e7b9a1c3e5b7d9f1a3c5e7b8f4b2a9e7c1d3f5b6a0e8d7c9b1a3e5f7a9c1a3b",
  },
  {
    id: "AUD-GLB-003",
    timestamp: "2026-08-26T16:20:00Z",
    officerName: "Insp. D. Bose",
    officerRole: "Senior Cyber Forensic Analyst",
    module: "ANOMALY_ENGINE",
    action: "Circular Fund Loop ALT-2026-001 Flagged",
    details: "Status transitioned to INVESTIGATING. Issued Section 91 CrPC notice to bank.",
    ipAddress: "10.42.18.91 (Cyber HQ Secure VPN)",
    verificationHash: "9c1a3b5d7f9a1c3e5b7d9f1a3c5e7b8f4b2a9e7c1d3f5b6a0e8d7c9b1a3e5f7a",
  },
  {
    id: "AUD-GLB-004",
    timestamp: "2026-08-25T14:30:00Z",
    officerName: "Insp. D. Bose",
    officerRole: "Senior Cyber Forensic Analyst",
    module: "ENTITY_RESOLUTION",
    action: "Duplicate Profile Consolidated",
    details: "Merged secondary subscriber profile 'D. Mohanty' into primary POS operator dossier ENT-011.",
    ipAddress: "10.42.18.91 (Cyber HQ Secure VPN)",
    verificationHash: "3a7f9b1c5e2d4a6b8c0e9d1a3b5c7e9f1a3b5d7f9a1c3e5b7d9f1a3c5e7b9a1c",
  },
];
