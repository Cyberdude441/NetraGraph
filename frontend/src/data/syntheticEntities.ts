export interface EntityTimelineEvent {
  id: string;
  type: "COMMUNICATION" | "FINANCIAL" | "LOCATION" | "CASE_MENTION" | "RELATIONSHIP_CHANGE";
  title: string;
  timestamp: string;
  description: string;
  severity: "critical" | "high" | "medium" | "info";
  sourceRef: string;
  metadata?: Record<string, string | number>;
}

export interface ComprehensiveEntity {
  id: string;
  name: string;
  label: "Person" | "Phone" | "Device" | "Location" | "Vehicle" | "Organization" | "BankAccount" | "Event";
  role?: string;
  riskScore: number;
  confidenceScore: number;
  verificationStatus: "Verified" | "High Confidence" | "Probable" | "Unknown";
  caseId: string;
  investigationGroup: string;
  communityId: number;
  firstSeen: string;
  lastSeen: string;
  activityStatus: "Recent" | "Historical" | "Dormant";
  centralityRank?: number;
  pageRankScore?: number;
  betweennessScore?: number;
  degreeCount?: number;
  relationshipsCount?: number;
  timeline: EntityTimelineEvent[];
  metadata: {
    category?: string;
    description: string;
    alias?: string[];
    jurisdiction?: string;
    financialLossINR?: number;
    phoneImei?: string;
    accountNumber?: string;
    ifscCode?: string;
    ipAddress?: string;
    coordinates?: [number, number];
    tags?: string[];
    attributes?: Record<string, string | number>;
    statutoryOffenses?: string[];
    duplicateCandidateOf?: string; // Links to intended duplicate candidate ID
  };
}

// Generate rich criminal network dataset with 105 entities
export const COMPREHENSIVE_ENTITIES: ComprehensiveEntity[] = [
  // 1. Core Primary Mastermind
  {
    id: "ENT-001",
    name: "Vikramaditya Rawat",
    label: "Person",
    role: "Syndicate Mastermind / Controller",
    riskScore: 96,
    confidenceScore: 0.98,
    verificationStatus: "Verified",
    caseId: "CASE-2024-DEL-0891",
    investigationGroup: "Noida Tech Support Scam Ring",
    communityId: 0,
    firstSeen: "2024-01-15",
    lastSeen: "2026-08-24",
    activityStatus: "Recent",
    centralityRank: 1,
    pageRankScore: 24.8,
    betweennessScore: 38.4,
    degreeCount: 16,
    relationshipsCount: 16,
    timeline: [
      {
        id: "EVT-101",
        type: "CASE_MENTION",
        title: "FIR 412/2024 Registered at Cyber Cell",
        timestamp: "2024-01-15T10:00:00Z",
        description: "Subject named in preliminary investigation report for orchestrating cross-border tech support fraud.",
        severity: "critical",
        sourceRef: "FIR-412-DEL",
      },
      {
        id: "EVT-102",
        type: "FINANCIAL",
        title: "₹4.25 Cr Hawala Cash Settlement",
        timestamp: "2024-04-20T16:00:00Z",
        description: "Coordinated physical currency handover with Mukesh Seth via Burrabazar trading counter.",
        severity: "critical",
        sourceRef: "FIU-STR-99120",
      },
      {
        id: "EVT-103",
        type: "COMMUNICATION",
        title: "Encrypted PBX Dispatch Established",
        timestamp: "2026-08-22T19:30:00Z",
        description: "Active Telegram session instructing Asterisk server restart after overseas IP blacklist alert.",
        severity: "high",
        sourceRef: "Signal Wiretap Log",
      },
    ],
    metadata: {
      category: "Mastermind",
      description: "Directs overseas VoIP routing, fraudulent call center operations in Sector 62 Noida, and manages hawala payout channels.",
      alias: ["Vikram Rawat", "Boss-V", "Vicky Bhai", "V. A. Rawat"],
      jurisdiction: "Delhi NCR / Noida",
      financialLossINR: 42500000,
      tags: ["Kingpin", "Hawala", "Red Notice Candidate", "Section 66D IT Act"],
      statutoryOffenses: ["IT Act 66D", "IT Act 66C", "IPC 420", "IPC 120B"],
      attributes: {
        "Passport": "Z-8919021-IN",
        "Known Assets": "3 Luxury Penthouses (Expedia Towers)",
        "Criminal Precedents": "2 FIRs in Haryana, 1 in Delhi Cyber Cell",
      },
    },
  },

  // 2. Intentional Duplicate Candidates for Vikramaditya Rawat
  {
    id: "ENT-002",
    name: "Vikram Rawat",
    label: "Person",
    role: "Proprietor (Front ROC Entity)",
    riskScore: 92,
    confidenceScore: 0.88,
    verificationStatus: "High Confidence",
    caseId: "CASE-2024-DEL-0891",
    investigationGroup: "Noida Tech Support Scam Ring",
    communityId: 0,
    firstSeen: "2024-02-01",
    lastSeen: "2026-08-20",
    activityStatus: "Recent",
    centralityRank: 5,
    pageRankScore: 18.2,
    betweennessScore: 22.0,
    degreeCount: 8,
    relationshipsCount: 8,
    timeline: [
      {
        id: "EVT-104",
        type: "FINANCIAL",
        title: "ROC Filing under Apex Global LLP",
        timestamp: "2024-02-01T11:00:00Z",
        description: "Registered as designated partner with matching residential address in Rohini.",
        severity: "medium",
        sourceRef: "MCA-ROC-2024",
      },
    ],
    metadata: {
      category: "Mastermind (Duplicate)",
      description: "Appears in MCA company filings for Apex Global InfoTech LLP with identical phone contact and jurisdiction.",
      alias: ["Vicky", "Vikram R."],
      jurisdiction: "Delhi NCR",
      duplicateCandidateOf: "ENT-001",
      tags: ["ROC Target", "Probable Duplicate"],
      statutoryOffenses: ["IT Act 66D", "IPC 420"],
    },
  },
  {
    id: "ENT-003",
    name: "V. A. Rawat",
    label: "Person",
    role: "Commercial Lease Signatory",
    riskScore: 85,
    confidenceScore: 0.76,
    verificationStatus: "Probable",
    caseId: "CASE-2024-DEL-0891",
    investigationGroup: "Noida Tech Support Scam Ring",
    communityId: 0,
    firstSeen: "2024-01-10",
    lastSeen: "2026-06-15",
    activityStatus: "Historical",
    centralityRank: 12,
    pageRankScore: 11.5,
    betweennessScore: 14.2,
    degreeCount: 4,
    relationshipsCount: 4,
    timeline: [
      {
        id: "EVT-105",
        type: "LOCATION",
        title: "Lease Execution at Logix Cyber Park",
        timestamp: "2024-01-10T14:00:00Z",
        description: "Signed 3-year commercial rental agreement for 3rd floor office suite.",
        severity: "info",
        sourceRef: "Noida Authority Lease Record",
      },
    ],
    metadata: {
      category: "Leaseholder",
      description: "Signatory on lease agreement for illegal call center facility in Sector 62.",
      alias: ["Vikramaditya A. Rawat"],
      jurisdiction: "Gautam Buddha Nagar",
      duplicateCandidateOf: "ENT-001",
      tags: ["Lease Document", "Similarity Candidate"],
    },
  },

  // 3. Tech Specialist & Intentional Duplicate
  {
    id: "ENT-004",
    name: "Sameer Khan",
    label: "Person",
    role: "Technical Operations Lead",
    riskScore: 89,
    confidenceScore: 0.95,
    verificationStatus: "Verified",
    caseId: "CASE-2024-DEL-0891",
    investigationGroup: "Noida Tech Support Scam Ring",
    communityId: 0,
    firstSeen: "2024-02-10",
    lastSeen: "2026-08-22",
    activityStatus: "Recent",
    centralityRank: 4,
    pageRankScore: 19.4,
    betweennessScore: 31.2,
    degreeCount: 11,
    relationshipsCount: 11,
    timeline: [
      {
        id: "EVT-106",
        type: "COMMUNICATION",
        title: "SIP Interconnect with Bhubaneswar SIM Box",
        timestamp: "2024-03-02T19:40:00Z",
        description: "Direct IP routing established between Noida Vicidial server and Tariq Ansari's GSM gateway.",
        severity: "critical",
        sourceRef: "Server Access Log",
      },
    ],
    metadata: {
      category: "Tech Specialist",
      description: "Manages Asterisk PBX servers, malicious remote desktop utilities, and overseas spoofed Caller ID gateways.",
      alias: ["Sam VoIP", "TechGod_99", "Sammy Khan"],
      jurisdiction: "Ghaziabad / Delhi NCR",
      phoneImei: "358921098451201",
      tags: ["VoIP Admin", "Malware Deployment", "PBX Spoofing"],
      statutoryOffenses: ["IT Act 66", "IT Act 66D"],
    },
  },
  {
    id: "ENT-005",
    name: "Samir K. (VoIP Admin)",
    label: "Person",
    role: "Asterisk PBX Consultant",
    riskScore: 84,
    confidenceScore: 0.79,
    verificationStatus: "Probable",
    caseId: "CASE-2024-DEL-0891",
    investigationGroup: "Noida Tech Support Scam Ring",
    communityId: 0,
    firstSeen: "2024-03-01",
    lastSeen: "2026-07-28",
    activityStatus: "Historical",
    centralityRank: 15,
    pageRankScore: 9.8,
    betweennessScore: 12.0,
    degreeCount: 5,
    relationshipsCount: 5,
    timeline: [
      {
        id: "EVT-107",
        type: "COMMUNICATION",
        title: "VoIP Trunk Purchase on Dark Forum",
        timestamp: "2024-03-01T04:20:00Z",
        description: "Acquired 10,000 DID phone minutes with cryptocurrency payment.",
        severity: "high",
        sourceRef: "Dark Web Telegram Scrape",
      },
    ],
    metadata: {
      category: "Tech Operator",
      description: "Freelance VoIP administrator listed on developer forum using identical Telegram handle @SamVoIP.",
      alias: ["Samir Khan", "Sam_Sysadmin"],
      jurisdiction: "Delhi NCR",
      duplicateCandidateOf: "ENT-004",
      tags: ["Probable Duplicate", "Tech Lead"],
    },
  },

  // 4. Financial Mule Recruiter & Duplicate
  {
    id: "ENT-006",
    name: "Rahul Kumar",
    label: "Person",
    role: "Tier-2 Mule Recruiter & Cashier",
    riskScore: 87,
    confidenceScore: 0.93,
    verificationStatus: "Verified",
    caseId: "CASE-2024-DEL-0891",
    investigationGroup: "Noida Tech Support Scam Ring",
    communityId: 0,
    firstSeen: "2024-03-10",
    lastSeen: "2026-08-23",
    activityStatus: "Recent",
    centralityRank: 7,
    pageRankScore: 15.2,
    betweennessScore: 21.4,
    degreeCount: 9,
    relationshipsCount: 9,
    timeline: [
      {
        id: "EVT-108",
        type: "FINANCIAL",
        title: "ATM Cash Withdrawal of ₹18.5 Lakh",
        timestamp: "2024-04-12T14:15:00Z",
        description: "Withdrew cash across 6 ATM kiosks in Rohini using multiple debit cards.",
        severity: "critical",
        sourceRef: "CCTV & ATM Switch Logs",
      },
    ],
    metadata: {
      category: "Mule Agent",
      description: "Coordinates recruitment of student bank accounts in Jaipur and Delhi for fast cash extraction.",
      alias: ["Rahul K.", "R. Kumar", "Rahul Bhai Rohini"],
      jurisdiction: "New Delhi / Jaipur",
      financialLossINR: 18500000,
      tags: ["ATM Runner", "Mule Recruiter", "Section 420 IPC"],
      statutoryOffenses: ["IPC 420", "IPC 468", "IT Act 66D"],
    },
  },
  {
    id: "ENT-007",
    name: "Rahul K.",
    label: "Person",
    role: "Account Holder (Mule A/C)",
    riskScore: 82,
    confidenceScore: 0.81,
    verificationStatus: "High Confidence",
    caseId: "CASE-2024-DEL-0891",
    investigationGroup: "Noida Tech Support Scam Ring",
    communityId: 0,
    firstSeen: "2024-03-15",
    lastSeen: "2026-07-19",
    activityStatus: "Historical",
    centralityRank: 18,
    pageRankScore: 8.4,
    betweennessScore: 9.1,
    degreeCount: 3,
    relationshipsCount: 3,
    timeline: [
      {
        id: "EVT-109",
        type: "FINANCIAL",
        title: "Aadhaar e-KYC Account Opened",
        timestamp: "2024-03-15T09:30:00Z",
        description: "Opened savings account with forged local proof of address in Rohini.",
        severity: "medium",
        sourceRef: "Bank KYC Ledger",
      },
    ],
    metadata: {
      category: "Mule Account Holder",
      description: "Indexed in FIU suspicious transaction report for sudden 40x surge in account velocity.",
      alias: ["R. Kumar"],
      jurisdiction: "New Delhi",
      duplicateCandidateOf: "ENT-006",
      tags: ["AI-Assisted Similarity Match", "Probable Duplicate"],
    },
  },
  {
    id: "ENT-008",
    name: "R. Kumar",
    label: "Person",
    role: "UPI Remittance Beneficiary",
    riskScore: 78,
    confidenceScore: 0.74,
    verificationStatus: "Probable",
    caseId: "CASE-2024-DEL-0891",
    investigationGroup: "Noida Tech Support Scam Ring",
    communityId: 0,
    firstSeen: "2024-04-02",
    lastSeen: "2026-05-14",
    activityStatus: "Dormant",
    centralityRank: 22,
    pageRankScore: 6.2,
    betweennessScore: 5.4,
    degreeCount: 2,
    relationshipsCount: 2,
    timeline: [
      {
        id: "EVT-110",
        type: "FINANCIAL",
        title: "UPI Split Transfer of ₹4,90,000",
        timestamp: "2024-04-02T16:22:00Z",
        description: "Received structured UPI deposits from victim ledger within 10 minutes.",
        severity: "high",
        sourceRef: "NPCI UPI Switch Log",
      },
    ],
    metadata: {
      category: "UPI Layering",
      description: "UPI VPA handle rkumar99@paytm flagged for receiving scam disbursements.",
      alias: ["Rahul Kumar"],
      jurisdiction: "New Delhi",
      duplicateCandidateOf: "ENT-006",
      tags: ["UPI VPA", "Candidate Match"],
    },
  },

  // 5. Cross-Syndicate Hawala Bridge & Duplicate
  {
    id: "ENT-009",
    name: "Mukesh 'Kolkata' Seth",
    label: "Person",
    role: "Cross-Border Hawala Intermediary",
    riskScore: 94,
    confidenceScore: 0.97,
    verificationStatus: "Verified",
    caseId: "CASE-2024-DEL-0891",
    investigationGroup: "Inter-State Hawala Network",
    communityId: 3,
    firstSeen: "2023-08-01",
    lastSeen: "2026-08-25",
    activityStatus: "Recent",
    centralityRank: 2,
    pageRankScore: 23.1,
    betweennessScore: 44.9,
    degreeCount: 14,
    relationshipsCount: 14,
    timeline: [
      {
        id: "EVT-111",
        type: "FINANCIAL",
        title: "USDT Liquidity Escrow Swap ₹6.8 Cr",
        timestamp: "2024-05-30T15:00:00Z",
        description: "Converted physical currency bundles to OTC USDT for LockNet ransomware operator.",
        severity: "critical",
        sourceRef: "Crypto Intelligence Report",
      },
      {
        id: "EVT-112",
        type: "LOCATION",
        title: "Surveillance Sighting in Burrabazar",
        timestamp: "2026-08-24T18:00:00Z",
        description: "Undercover team monitored cash drop meeting at textile wholesale shop.",
        severity: "high",
        sourceRef: "Field Intelligence Log",
      },
    ],
    metadata: {
      category: "Hawala Operator",
      description: "Key broker bridging Noida scam proceeds with LockNet crypto conversion networks and Odisha SIM sourcing logistics.",
      alias: ["Mukesh Sethi", "Sethji-KOL", "M. Seth"],
      jurisdiction: "Kolkata Burrabazar / New Delhi",
      financialLossINR: 76000000,
      tags: ["Bridge Entity", "Hawala Kingpin", "High Betweenness Node"],
      statutoryOffenses: ["FEMA Violation", "PMLA Section 3", "IPC 120B"],
    },
  },
  {
    id: "ENT-010",
    name: "Mukesh Sethi (Burrabazar)",
    label: "Person",
    role: "Textile Merchant / Cash Courier",
    riskScore: 90,
    confidenceScore: 0.86,
    verificationStatus: "High Confidence",
    caseId: "CASE-2024-DEL-0891",
    investigationGroup: "Inter-State Hawala Network",
    communityId: 3,
    firstSeen: "2023-09-05",
    lastSeen: "2026-08-21",
    activityStatus: "Recent",
    centralityRank: 6,
    pageRankScore: 16.7,
    betweennessScore: 28.5,
    degreeCount: 7,
    relationshipsCount: 7,
    timeline: [
      {
        id: "EVT-113",
        type: "FINANCIAL",
        title: "Trade Invoicing Clearance of ₹1.2 Cr",
        timestamp: "2024-01-15T12:00:00Z",
        description: "Cleared unbacked textile purchase orders as cover for cash distribution.",
        severity: "high",
        sourceRef: "GST Audit Discrepancy",
      },
    ],
    metadata: {
      category: "Hawala Merchant",
      description: "Merchant registration at Burrabazar with matching telephone contact and token exchange logs.",
      alias: ["M. Sethi"],
      jurisdiction: "Kolkata, WB",
      duplicateCandidateOf: "ENT-009",
      tags: ["Probable Duplicate", "Hawala Conduit"],
    },
  },

  // 6. SIM Box Ring Lead & Duplicate
  {
    id: "ENT-011",
    name: "Deepak Kumar Mohanty",
    label: "Person",
    role: "Pre-Activated SIM Dealer",
    riskScore: 84,
    confidenceScore: 0.90,
    verificationStatus: "Verified",
    caseId: "CASE-2024-OD-0412",
    investigationGroup: "Bhubaneswar SIM Box Ring",
    communityId: 1,
    firstSeen: "2024-03-15",
    lastSeen: "2026-08-21",
    activityStatus: "Recent",
    centralityRank: 9,
    pageRankScore: 13.6,
    betweennessScore: 18.0,
    degreeCount: 8,
    relationshipsCount: 8,
    timeline: [
      {
        id: "EVT-114",
        type: "RELATIONSHIP_CHANGE",
        title: "Seizure of 2,400 SIM Cards by Odisha STF",
        timestamp: "2024-04-18T08:00:00Z",
        description: "Vehicle intercepted with bulk fraudulent SIM bundles during transit from Cuttack.",
        severity: "critical",
        sourceRef: "STF Seizure Memo 88/24",
      },
    ],
    metadata: {
      category: "Telecom POS Agent",
      description: "Telecom Point of Sale retailer who fraudulently activated 2,400+ SIMs using stolen biometric scans.",
      alias: ["D. K. Mohanty", "Deepak Mohanty", "Deepu SIM"],
      jurisdiction: "Cuttack / Khordha",
      tags: ["Biometric Forgery", "POS Agent", "DoT Blacklist"],
      statutoryOffenses: ["IT Act 66", "Indian Telegraph Act Sec 20", "IPC 468"],
    },
  },
  {
    id: "ENT-012",
    name: "D. K. Mohanty",
    label: "Person",
    role: "Retail POS Franchisee",
    riskScore: 80,
    confidenceScore: 0.82,
    verificationStatus: "High Confidence",
    caseId: "CASE-2024-OD-0412",
    investigationGroup: "Bhubaneswar SIM Box Ring",
    communityId: 1,
    firstSeen: "2024-03-20",
    lastSeen: "2026-07-10",
    activityStatus: "Historical",
    centralityRank: 20,
    pageRankScore: 7.1,
    betweennessScore: 8.5,
    degreeCount: 4,
    relationshipsCount: 4,
    timeline: [
      {
        id: "EVT-115",
        type: "LOCATION",
        title: "Toll Plaza Fastag Trigger on NH-16",
        timestamp: "2024-04-10T07:45:00Z",
        description: "Registered vehicle crossed Manguli toll plaza matching delivery timings.",
        severity: "info",
        sourceRef: "NHAI Fastag Log",
      },
    ],
    metadata: {
      category: "Telecom Franchise",
      description: "Official CAF subscriber registration agent ID registered in Cuttack circle.",
      alias: ["Deepak Kumar"],
      jurisdiction: "Odisha Telecom Circle",
      duplicateCandidateOf: "ENT-011",
      tags: ["CAF Agent", "Candidate Match"],
    },
  },

  // 7. LockNet Ransomware Developer & Duplicate
  {
    id: "ENT-013",
    name: "Arjun Menon",
    label: "Person",
    role: "Ransomware Developer & Crypto Broker",
    riskScore: 97,
    confidenceScore: 0.99,
    verificationStatus: "Verified",
    caseId: "CASE-2024-TG-1044",
    investigationGroup: "LockNet Ransomware Group",
    communityId: 2,
    firstSeen: "2023-09-01",
    lastSeen: "2026-08-25",
    activityStatus: "Recent",
    centralityRank: 3,
    pageRankScore: 21.8,
    betweennessScore: 33.7,
    degreeCount: 12,
    relationshipsCount: 12,
    timeline: [
      {
        id: "EVT-116",
        type: "CASE_MENTION",
        title: "Power Utility SCADA Intrusion",
        timestamp: "2024-06-12T02:15:00Z",
        description: "Deployed custom LockNet payload targeting substation backup servers.",
        severity: "critical",
        sourceRef: "CERT-In Incident Ref 9042",
      },
    ],
    metadata: {
      category: "Malware Author",
      description: "Author of LockNet Ransomware variant targeting state power utilities and healthcare IT infrastructure.",
      alias: ["CipherX", "0xDarkLord", "A. Menon", "Arjun M."],
      jurisdiction: "Hyderabad / Bengaluru",
      financialLossINR: 89000000,
      tags: ["Ransomware Dev", "Crypto Laundering", "Critical Infrastructure"],
      statutoryOffenses: ["IT Act 66F (Cyber Terrorism)", "IT Act 66", "IPC 384"],
    },
  },
  {
    id: "ENT-014",
    name: "A. Menon (CipherX)",
    label: "Person",
    role: "Cryptocurrency Liquidity Provider",
    riskScore: 92,
    confidenceScore: 0.85,
    verificationStatus: "High Confidence",
    caseId: "CASE-2024-TG-1044",
    investigationGroup: "LockNet Ransomware Group",
    communityId: 2,
    firstSeen: "2023-11-10",
    lastSeen: "2026-08-15",
    activityStatus: "Recent",
    centralityRank: 8,
    pageRankScore: 14.1,
    betweennessScore: 19.3,
    degreeCount: 6,
    relationshipsCount: 6,
    timeline: [
      {
        id: "EVT-117",
        type: "FINANCIAL",
        title: "Monero (XMR) Privacy Pool Mixing",
        timestamp: "2024-02-14T23:00:00Z",
        description: "Laundered 450 XMR through cross-chain bridge to decentralized USDT pools.",
        severity: "high",
        sourceRef: "Chainalysis Block Trace",
      },
    ],
    metadata: {
      category: "Crypto Mixer",
      description: "Identified through PGP key signatures linked to exploit proof-of-concepts on GitHub.",
      alias: ["CipherX", "Arjun Menon"],
      jurisdiction: "Bengaluru",
      duplicateCandidateOf: "ENT-013",
      tags: ["PGP Matched", "Probable Duplicate"],
    },
  },

  // 8. Shell Company & Duplicate
  {
    id: "ENT-015",
    name: "Apex Global InfoTech LLP",
    label: "Organization",
    role: "Front Shell Company",
    riskScore: 88,
    confidenceScore: 0.92,
    verificationStatus: "Verified",
    caseId: "CASE-2024-DEL-0891",
    investigationGroup: "Noida Tech Support Scam Ring",
    communityId: 0,
    firstSeen: "2023-11-20",
    lastSeen: "2026-08-22",
    activityStatus: "Recent",
    centralityRank: 10,
    pageRankScore: 12.8,
    betweennessScore: 17.5,
    degreeCount: 7,
    relationshipsCount: 7,
    timeline: [
      {
        id: "EVT-118",
        type: "FINANCIAL",
        title: "Bank Account Frozen by Cyber Cell",
        timestamp: "2024-06-01T10:00:00Z",
        description: "Debit freeze placed on HDFC corporate account holding ₹3.84 Cr balance.",
        severity: "critical",
        sourceRef: "Section 102 CrPC Notice",
      },
    ],
    metadata: {
      description: "Registered ROC dummy entity with no commercial turnover other than fraudulent tech support inward remittances.",
      alias: ["Apex Global Technologies", "Apex Infotech India"],
      jurisdiction: "Delhi ROC",
      tags: ["Shell Firm", "MCA Blacklisted", "Bogus Audits"],
      statutoryOffenses: ["PMLA Section 4", "Companies Act 447"],
    },
  },
  {
    id: "ENT-016",
    name: "Apex Global Technologies",
    label: "Organization",
    role: "BPO / Telemarketing Trade Name",
    riskScore: 83,
    confidenceScore: 0.80,
    verificationStatus: "High Confidence",
    caseId: "CASE-2024-DEL-0891",
    investigationGroup: "Noida Tech Support Scam Ring",
    communityId: 0,
    firstSeen: "2024-01-05",
    lastSeen: "2026-07-20",
    activityStatus: "Historical",
    centralityRank: 19,
    pageRankScore: 7.9,
    betweennessScore: 9.0,
    degreeCount: 3,
    relationshipsCount: 3,
    timeline: [
      {
        id: "EVT-119",
        type: "COMMUNICATION",
        title: "Domain Host Registered: apex-globalsupport.net",
        timestamp: "2024-01-05T08:00:00Z",
        description: "Registered phishing domain mimicking Microsoft Helpdesk with Cloudflare proxy.",
        severity: "high",
        sourceRef: "WHOIS Domain Record",
      },
    ],
    metadata: {
      description: "Commercial trade style used in phishing popups presented to foreign victims.",
      alias: ["Apex Global InfoTech"],
      jurisdiction: "Noida / Delhi",
      duplicateCandidateOf: "ENT-015",
      tags: ["Trade Name", "Probable Duplicate"],
    },
  },
];

// Helper to expand the dataset to >100 realistic investigative entities
function populateRemainingEntities(): void {
  const types: ComprehensiveEntity["label"][] = [
    "Phone",
    "Device",
    "Location",
    "Vehicle",
    "BankAccount",
    "Event",
    "Person",
    "Organization",
  ];

  const cities = [
    "Noida Sector 62",
    "Rohini Sector 14, Delhi",
    "Burrabazar, Kolkata",
    "Khandagiri, Bhubaneswar",
    "Hitec City, Hyderabad",
    "Indiranagar, Bengaluru",
    "Cuttack STF Zone",
    "Gurugram Cyber Hub",
    "Jaipur Vaishali Nagar",
    "Ghaziabad Crossings",
  ];

  const groups = [
    "Noida Tech Support Scam Ring",
    "Bhubaneswar SIM Box Ring",
    "LockNet Ransomware Group",
    "Inter-State Hawala Network",
    "Mule Ledger Syndicate Tier-2",
  ];

  for (let i = 17; i <= 105; i++) {
    const type = types[i % types.length]!;
    const group = groups[i % groups.length]!;
    const city = cities[i % cities.length]!;
    const communityId = i % 4;

    const baseRisk = 45 + ((i * 13) % 52);
    const conf = 0.70 + ((i * 7) % 28) / 100;
    const status: ComprehensiveEntity["verificationStatus"] =
      conf >= 0.92 ? "Verified" : conf >= 0.82 ? "High Confidence" : "Probable";

    let name = "";
    let role = "";
    const metadata: ComprehensiveEntity["metadata"] = {
      description: `Investigated forensic entity connected to ${group}.`,
      jurisdiction: city,
      tags: ["Cyber Crime Evidence", "Indexed Docket"],
    };

    if (type === "Phone") {
      name = `+91 ${98000 + i} ${10000 + i * 3}`;
      role = i % 2 === 0 ? "Burner SIM (Fake KYC)" : "C2 SMS Gateway Relay";
      metadata.phoneImei = `35990102148${1000 + i}`;
      metadata.tags?.push("CDR Monitored");
    } else if (type === "BankAccount") {
      name = `HDFC/ICICI Mule A/C: 50100${40000 + i * 7}`;
      role = "Layering Mule Account";
      metadata.accountNumber = `50100${40000 + i * 7}`;
      metadata.ifscCode = "HDFC0001208";
      metadata.financialLossINR = 1500000 + i * 85000;
      metadata.tags?.push("FIU-IND Suspicious");
    } else if (type === "Device") {
      name = `Hardware Gateway Appliance [SN: HW-${9000 + i}]`;
      role = "VoIP / SIM Box Hardware";
      metadata.ipAddress = `103.45.120.${i % 250}`;
      metadata.tags?.push("CFSL Forensic Seizure");
    } else if (type === "Location") {
      name = `Premises Unit #${100 + i}, ${city}`;
      role = "Physical Call Center / Safehouse";
      metadata.tags?.push("Surveillance Active");
    } else if (type === "Vehicle") {
      name = `Transport Vehicle [DL-${(i % 12) + 1}-CA-${1000 + i}]`;
      role = "Mule Cash Transport / Fastag Monitored";
      metadata.tags?.push("Fastag Log");
    } else if (type === "Event") {
      name = `Incident Wave #${i}: Coordinated Phishing Surge`;
      role = "Cyber Extortion Campaign";
      metadata.tags?.push("Incident Event");
    } else if (type === "Organization") {
      name = `Shell Firm #${i} Consulting Pvt Ltd`;
      role = "Mule Invoicing Entity";
      metadata.tags?.push("MCA Dummy Firm");
    } else {
      name = `Suspect Agent #${i} (${city.split(" ")[0]})`;
      role = "Syndicate Field Associate";
      metadata.alias = [`Alias-${i}`, `Agent-${i}`];
      metadata.tags?.push("Surveillance Target");
    }

    COMPREHENSIVE_ENTITIES.push({
      id: `ENT-${String(i).padStart(3, "0")}`,
      name,
      label: type,
      role,
      riskScore: baseRisk,
      confidenceScore: Number(conf.toFixed(2)),
      verificationStatus: status,
      caseId: `CASE-2024-DEL-0891`,
      investigationGroup: group,
      communityId,
      firstSeen: `2024-0${(i % 8) + 1}-10`,
      lastSeen: `2026-08-${(i % 20) + 5}`,
      activityStatus: i % 3 === 0 ? "Recent" : i % 3 === 1 ? "Historical" : "Dormant",
      centralityRank: i,
      pageRankScore: Number((30 / Math.sqrt(i)).toFixed(1)),
      betweennessScore: Number((25 / Math.sqrt(i)).toFixed(1)),
      degreeCount: Math.max(1, Math.round(15 / Math.sqrt(i))),
      relationshipsCount: Math.max(1, Math.round(15 / Math.sqrt(i))),
      timeline: [
        {
          id: `EVT-${i}-1`,
          type: type === "BankAccount" ? "FINANCIAL" : type === "Phone" ? "COMMUNICATION" : "CASE_MENTION",
          title: `Forensic Activity Logged: ${name}`,
          timestamp: `2024-0${(i % 8) + 1}-15T10:00:00Z`,
          description: `Intelligence extraction matched telemetry in ${city} for ${group}.`,
          severity: baseRisk >= 85 ? "critical" : baseRisk >= 70 ? "high" : "medium",
          sourceRef: `DOCKET-REF-${i}`,
        },
      ],
      metadata,
    });
  }
}

populateRemainingEntities();
