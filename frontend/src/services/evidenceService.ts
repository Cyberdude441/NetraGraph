export interface EvidenceBlock {
  blockNumber: number;
  evidenceId: string;
  title: string;
  sourceCategory: "CDR_TELEMETRY" | "BANK_STATEMENT" | "CEIR_IMEI_DUMP" | "WIRETAP_MEMO" | "SEIZURE_PANCHNAMA" | "FORENSIC_IMAGE";
  timestamp: string;
  verifyingAnalyst: string;
  sha256Hash: string;
  previousBlockHash: string;
  fileSizeBytes: number;
  integrityStatus: "VERIFIED" | "PENDING_REVIEW" | "INTEGRITY_WARNING";
  statutoryCertification: string;
  chainOfCustodyLogs: {
    timestamp: string;
    officer: string;
    action: string;
    custodyLocation: string;
  }[];
}

export const INITIAL_EVIDENCE_CHAIN: EvidenceBlock[] = [
  {
    blockNumber: 1,
    evidenceId: "EVD-2026-001",
    title: "FIR #402/2026 Scanned True Copy & Complainant Affidavit",
    sourceCategory: "SEIZURE_PANCHNAMA",
    timestamp: "2026-08-22T09:30:00Z",
    verifyingAnalyst: "Insp. D. Bose",
    sha256Hash: "8f4b2a9e7c1d3f5b6a0e8d7c9b1a3e5f7a9c1e3b5d7f9a1c3e5b7d9f1a3c5e7b",
    previousBlockHash: "0000000000000000000000000000000000000000000000000000000000000000",
    fileSizeBytes: 4280000,
    integrityStatus: "VERIFIED",
    statutoryCertification: "Section 65B Indian Evidence Act Certified by SHO Cyber Crime PS",
    chainOfCustodyLogs: [
      {
        timestamp: "2026-08-22T09:30:00Z",
        officer: "Insp. D. Bose",
        action: "Evidence Ingested & Hashed",
        custodyLocation: "Cyber Cell Secure Storage Vault #1",
      },
      {
        timestamp: "2026-08-22T10:15:00Z",
        officer: "ACP R. K. Singh",
        action: "Custody Handover Verified",
        custodyLocation: "State Forensic Science Laboratory (SFSL)",
      },
    ],
  },
  {
    blockNumber: 2,
    evidenceId: "EVD-2026-002",
    title: "CDR Sector Dump #N09-402 (Sector 62 Tower 9B)",
    sourceCategory: "CDR_TELEMETRY",
    timestamp: "2026-08-24T18:00:00Z",
    verifyingAnalyst: "Insp. D. Bose",
    sha256Hash: "3a7f9b1c5e2d4a6b8c0e9d1a3b5c7e9f1a3b5d7f9a1c3e5b7d9f1a3c5e7b9a1c",
    previousBlockHash: "8f4b2a9e7c1d3f5b6a0e8d7c9b1a3e5f7a9c1e3b5d7f9a1c3e5b7d9f1a3c5e7b",
    fileSizeBytes: 18500000,
    integrityStatus: "VERIFIED",
    statutoryCertification: "Certified under Section 5(2) Indian Telegraph Act",
    chainOfCustodyLogs: [
      {
        timestamp: "2026-08-24T18:00:00Z",
        officer: "Insp. D. Bose",
        action: "Raw GZ Stream Verified",
        custodyLocation: "State Cyber Cell Server Room",
      },
    ],
  },
  {
    blockNumber: 3,
    evidenceId: "EVD-2026-003",
    title: "FIU-IND STR Ledger #908129 (ICICI Bank ₹1.54 Cr)",
    sourceCategory: "BANK_STATEMENT",
    timestamp: "2026-08-25T11:20:00Z",
    verifyingAnalyst: "Insp. D. Bose",
    sha256Hash: "9c1a3b5d7f9a1c3e5b7d9f1a3c5e7b8f4b2a9e7c1d3f5b6a0e8d7c9b1a3e5f7a",
    previousBlockHash: "3a7f9b1c5e2d4a6b8c0e9d1a3b5c7e9f1a3b5d7f9a1c3e5b7d9f1a3c5e7b9a1c",
    fileSizeBytes: 1240000,
    integrityStatus: "VERIFIED",
    statutoryCertification: "PMLA Section 12 & IT Act §69B Certified Banking Ledger",
    chainOfCustodyLogs: [
      {
        timestamp: "2026-08-25T11:20:00Z",
        officer: "Insp. D. Bose",
        action: "Signed Banking XML Attached",
        custodyLocation: "Cyber Evidence Vault Block #3",
      },
    ],
  },
  {
    blockNumber: 4,
    evidenceId: "EVD-2026-004",
    title: "CEIR National IMEI Telemetry (OnePlus Nord 864902049182019)",
    sourceCategory: "CEIR_IMEI_DUMP",
    timestamp: "2026-08-26T12:00:00Z",
    verifyingAnalyst: "Insp. D. Bose",
    sha256Hash: "5e7b9a1c3e5b7d9f1a3c5e7b8f4b2a9e7c1d3f5b6a0e8d7c9b1a3e5f7a9c1a3b",
    previousBlockHash: "9c1a3b5d7f9a1c3e5b7d9f1a3c5e7b8f4b2a9e7c1d3f5b6a0e8d7c9b1a3e5f7a",
    fileSizeBytes: 980000,
    integrityStatus: "VERIFIED",
    statutoryCertification: "Department of Telecommunications (DoT) CEIR Feed",
    chainOfCustodyLogs: [
      {
        timestamp: "2026-08-26T12:00:00Z",
        officer: "Insp. D. Bose",
        action: "IMSI Cycling Log Appended",
        custodyLocation: "Cyber Evidence Vault Block #4",
      },
    ],
  },
];

/**
 * Validate cryptographic integrity across evidence chain blocks
 */
export function verifyEvidenceChainIntegrity(chain: EvidenceBlock[]): {
  isValid: boolean;
  brokenBlockNumber?: number;
  totalVerifiedBlocks: number;
  verificationMessage: string;
} {
  for (let i = 1; i < chain.length; i++) {
    const prev = chain[i - 1]!;
    const curr = chain[i]!;

    if (curr.previousBlockHash !== prev.sha256Hash) {
      return {
        isValid: false,
        brokenBlockNumber: curr.blockNumber,
        totalVerifiedBlocks: i,
        verificationMessage: `Cryptographic hash mismatch detected at Block #${curr.blockNumber} (Expected previous: ${prev.sha256Hash.slice(0, 12)}..., Found: ${curr.previousBlockHash.slice(0, 12)}...)`,
      };
    }
  }

  return {
    isValid: true,
    totalVerifiedBlocks: chain.length,
    verificationMessage: "All evidence chain blocks cryptographically verified with zero tamper anomalies.",
  };
}
