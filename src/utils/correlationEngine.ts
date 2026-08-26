export interface SpatialTemporalCorrelation {
  id: string;
  title: string;
  triggerEvent: string;
  triggerTimestamp: string;
  correlatedLocationName: string;
  correlatedLocationId: string;
  lagDurationHours: number;
  correlationConfidence: number; // 0 to 100
  observation: string;
  analysis: string;
  investigativeAdvice: string;
  disclaimer: string;
}

export const SYNTHETIC_CORRELATIONS: SpatialTemporalCorrelation[] = [
  {
    id: "CORR-01",
    title: "Nocturnal Telephony Surge Followed by RTGS Mule Transfer",
    triggerEvent: "VoIP Extortion Call Burst (+350% Surge)",
    triggerTimestamp: "2026-08-25T20:10:00Z",
    correlatedLocationName: "Sector 62 Electronic City Tower 9B, Noida",
    correlatedLocationId: "LOC-NCR-01",
    lagDurationHours: 18,
    correlationConfidence: 89,
    observation: "A 54-call overseas telephony surge at Sector 62 preceded a ₹1.54 Cr RTGS transfer from the primary ICICI mule account by 18 hours.",
    analysis: "Strong temporal correlation (89%) indicates call-center operators harvested banking credentials and notified the money-mule controller for rapid liquidation.",
    investigativeAdvice: "Coordinate with Cyber Police Station Noida to synchronize server logs with bank clearing timestamps.",
    disclaimer: "Statistical and temporal correlation does not prove causation; requires Section 65B certified server transcript verification.",
  },
  {
    id: "CORR-02",
    title: "Physical Handshake at Cyber Hub Preceding Cryptocurrency OTC Liquidation",
    triggerEvent: "Hawala Cash Drop Rendezvous at DLF Phase 2",
    triggerTimestamp: "2026-08-25T18:20:00Z",
    correlatedLocationName: "Bandra-Kurla Complex Financial Vault, Mumbai",
    correlatedLocationId: "LOC-MH-01",
    lagDurationHours: 17,
    correlationConfidence: 93,
    observation: "Physical meeting between Vikramaditya Rawat and Arjun Menon in Gurugram occurred 17 hours prior to on-chain liquidation of ₹1.42 Cr USDT in Mumbai.",
    analysis: "Multi-cluster Hawala bridge pattern: Cash delivered in NCR triggered automated release of offshore cryptocurrency liquidity in Mumbai.",
    investigativeAdvice: "Serve Section 91 CrPC notice on OTC trading desk and subpoena CCTV footage from DLF Cyber Hub gateway.",
    disclaimer: "Temporal proximity indicator based on synthetic surveillance telemetry.",
  },
  {
    id: "CORR-03",
    title: "Bulk SIM Card Activation Immediately Preceding Ransomware Phishing Wave",
    triggerEvent: "128 SIM Cards Bulk Activated on Chandrasekharpur Farm",
    triggerTimestamp: "2026-08-24T14:10:00Z",
    correlatedLocationName: "Andheri East Cloud Hosting Server Farm, Mumbai",
    correlatedLocationId: "LOC-MH-02",
    lagDurationHours: 8,
    correlationConfidence: 86,
    observation: "SIM Farm activation of 128 GSM channels in Bhubaneswar preceded reverse-proxy payload distribution from Andheri East server by 8 hours.",
    analysis: "SIM box infrastructure was utilized as 2FA SMS bypass relays during phishing credential verification.",
    investigativeAdvice: "Liaise with Odisha Cyber Crime Cell for physical raid on Chandrasekharpur facility.",
    disclaimer: "Algorithmic correlation telemetry. Requires forensic confirmation.",
  },
];
