import type { IntelligenceReport } from "@/services/reportExport";

export const assistantPrompts = [
  "Analyze high-risk cyber crime clusters in NCRB state dataset",
  "Summarize financial fraud loss distribution under IT Act 66D",
  "Identify top 5 state hotspots by crime rate per lakh",
  "Extract entities from uploaded investigation report transcript",
];

export const reports: IntelligenceReport[] = [
  {
    id: "RP-410",
    title: "National Cyber Crime Exposure & NCRB Comparative Analysis",
    author: "National Cyber Coordination Centre",
    date: "2026-08-25",
    pages: 24,
    classification: "OFFICIAL S-4",
    generatedBy: "Cyber Cell Intelligence Engine",
    riskLevel: "CRITICAL",
    summary:
      "Comprehensive state-wise analysis evaluating cyber crime incident growth, conviction efficiencies, and cross-border financial fraud routing based on official NCRB datasets.",
    intelligenceOverview:
      "National telecommunication and banking telemetry corroborated with NCRB crime registries indicate a 9.4% YoY increase in cyber crime registrations, with financial fraud accounting for 41.2% of all incidents.",
    findings: [
      "Telangana, Karnataka, and Uttar Pradesh lead national registration volumes in financial fraud and identity theft.",
      "Over INR 1,420 Crore estimated cumulative financial loss reported through digital payment and UPI phishing gateways.",
      "Charge-sheeting rates average 48.2% nationally with significant variation between metropolitan and rural police units.",
    ],
    entityRelationships: [
      { source: "State Cyber Cells", target: "FIU-IND Banking Ledger", type: "INTELLIGENCE_FLOW", detail: "Real-time account freeze triggers" },
      { source: "National Cyber Crime Portal", target: "State Crime Records Bureau", type: "DATA_LINK", detail: "Automatic FIR synchronization" },
    ],
    riskAssessment: {
      level: "CRITICAL",
      score: 94,
      factors: [
        "High concentration of mule accounts in Tier-2 banking branches",
        "Proliferation of SIM swap and OTP interception phishing rings",
        "Inter-state jurisdictional delays in cold-storage digital evidence seizure",
      ],
    },
    entities: ["NCRB-2025", "NCCC-GATEWAY", "FIU-IND"],
    analystNotes:
      "Recommend proactive coordination between State Cyber Police Stations and correspondent financial institutions for automated Section 91 CrPC compliance.",
    recommendations: [
      "Implement centralized 2-hour lien marking SLA across all scheduled commercial banks.",
      "Expand specialized Cyber Crime Police Station jurisdiction to all district headquarters.",
      "Establish automated CDR and BTS analysis pipelines across state borders.",
    ],
  },
  {
    id: "RP-402",
    title: "NCRB IT Act Statutory Offenses & Conviction Audit",
    author: "Insp. D. Bose",
    date: "2026-08-20",
    pages: 61,
    classification: "OFFICIAL S-4",
    generatedBy: "Cyber Crime Operations Cell",
    riskLevel: "HIGH",
    summary:
      "Statutory audit analyzing case disposal, conviction velocity, and forensic trial readiness for offenses under IT Act Section 66, 66C, 66D, 67, and IPC Section 420.",
    intelligenceOverview:
      "Section 66D (Cheating by personation using computer resource) accounts for the largest proportion of chargesheeted matters, followed closely by Section 420 IPC and Section 66C identity theft.",
    findings: [
      "Section 66D registrations reached 42,810 cases nationally with a 44.2% chargesheeting rate.",
      "Conviction rate for digitally authenticated evidence with Section 65B certificates was 2.4x higher than standard cases.",
      "Pending investigation backlog reduced by 11.2% in states utilizing automated forensic extraction suites.",
    ],
    entityRelationships: [
      { source: "IT Act 66D Cases", target: "State High Courts", type: "JUDICIAL_TRACK", detail: "Fast-track cyber courts trial pipeline" },
    ],
    riskAssessment: {
      level: "HIGH",
      score: 86,
      factors: [
        "Evidentiary challenges in overseas server log attribution",
        "High volume of unverified virtual phone numbers and VoIP routes",
      ],
    },
    entities: ["IT-ACT-66D", "IPC-420", "SEC-65B"],
    analystNotes:
      "Ensure mandatory SHA-256 hashing and chain-of-custody logging at initial point of seizure to preserve trial integrity.",
    recommendations: [
      "Standardize digital evidence collection SOPs across state investigating officers.",
      "Deploy localized cyber forensic triage vans for on-scene electronic hardware acquisition.",
    ],
  },
  {
    id: "RP-398",
    title: "State & UT Cyber Crime Hotspot Matrix",
    author: "Field Intel Command",
    date: "2026-08-14",
    pages: 18,
    classification: "OFFICIAL S-4",
    generatedBy: "Field Operations Command",
    riskLevel: "HIGH",
    summary:
      "Spatial clustering and rate per lakh population analysis across all 36 States and Union Territories of India.",
    intelligenceOverview:
      "Analysis reveals metropolitan UTs (Delhi, Chandigarh) and tech corridor states (Telangana, Karnataka) maintain highest per-capita reporting rates due to high digital literacy and active citizen portals.",
    findings: [
      "Delhi and Telangana recorded cyber crime rates exceeding 40 incidents per lakh population.",
      "Eastern and North-Eastern states report lower overall volumes but higher growth rates in online financial extortion.",
      "Chargesheeting rate exceeded 50% in 12 states with dedicated Cyber Cell infrastructure.",
    ],
    entityRelationships: [
      { source: "Urban Cyber Hubs", target: "Rural Phishing Operatives", type: "EXPLOITATION_FLOW", detail: "Cross-border victim targeting" },
    ],
    riskAssessment: {
      level: "HIGH",
      score: 79,
      factors: [
        "Uneven forensic laboratory capacity across state jurisdictions",
        "High mobility of fraudulent call center operations across state lines",
      ],
    },
    entities: ["STATE-DATA-2025", "NCRP-PORTAL"],
    analystNotes:
      "Joint inter-state task forces recommended for tri-border districts where jurisdictional overlap causes enforcement delays.",
    recommendations: [
      "Establish regional Cyber Coordination Centres (RCCC) for inter-state operational response.",
      "Integrate toll-free 1930 emergency reporting with immediate telecom line deactivation.",
    ],
  },
  {
    id: "RP-389",
    title: "Algorithmic Risk Model & Forensic Evidence Benchmark",
    author: "AI Governance & Assurance",
    date: "2026-08-02",
    pages: 33,
    classification: "OFFICIAL S-4",
    generatedBy: "Algorithmic Assurance Board",
    riskLevel: "MODERATE",
    summary:
      "Validation of machine learning entity resolution and graph link prediction models benchmarked against 100,000+ verified law enforcement records.",
    intelligenceOverview:
      "Assessment confirms 96.4% precision in automated phone and account clustering with zero data leakage across multi-tenant law enforcement partitions.",
    findings: [
      "Graph centrality algorithms correctly identified 91.8% of primary syndicate orchestrators.",
      "Audit logs captured 100% of analytical operations with cryptographic tamper protection.",
    ],
    entityRelationships: [
      { source: "NetraGraph Engine", target: "State Evidence Vaults", type: "CRYPTOGRAPHIC_LOCK", detail: "AES-256 evidence anchoring" },
    ],
    riskAssessment: {
      level: "MODERATE",
      score: 55,
      factors: [
        "Model calibration stable across diverse regional crime categories",
      ],
    },
    entities: ["AI-MODEL-V2", "EVIDENCE-INTEGRITY"],
    analystNotes:
      "All automated analytical recommendations comply with admissibility criteria under Indian Evidence Act §65B.",
    recommendations: [
      "Maintain active human-in-the-loop validation for automated account freeze recommendations.",
    ],
  },
];
