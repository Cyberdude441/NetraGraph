export interface FIRIngestPayload {
  caseNumber: string;
  policeStation?: string;
  dateOfIncident?: string;
  actsAndSections?: string[];
  rawText?: string;
  extractedPersons?: string[];
  extractedOrgs?: string[];
  extractedLocations?: string[];
  leadOfficer?: string;
}

export interface CDRRecord {
  caller_number: string;
  receiver_number: string;
  timestamp: string;
  duration: number;
  tower_location?: string;
  imei?: string;
  imsi?: string;
  caller_name?: string;
  receiver_name?: string;
}

export interface CDRIngestPayload {
  caseReference?: string;
  records: CDRRecord[];
}

export interface FinanceRecord {
  sender_account: string;
  receiver_account: string;
  amount: number;
  timestamp: string;
  transaction_type?: string;
  bank?: string;
  sender_name?: string;
  receiver_name?: string;
  reference_number?: string;
}

export interface FinanceIngestPayload {
  caseReference?: string;
  transactions: FinanceRecord[];
}

export interface CyberComplaintPayload {
  complaint_id: string;
  victim: string;
  attack_type: string;
  email?: string;
  phone?: string;
  ip_address?: string;
  loss_amount?: number;
  date?: string;
  suspect_account?: string;
  suspect_phone?: string;
  narrative?: string;
}

export interface DigitalEvidencePayload {
  exhibit_id?: string;
  file_name: string;
  file_type?: string;
  hash_sha256: string;
  case_reference: string;
  ip_address?: string;
  domain?: string;
  device_model?: string;
  email_headers?: Record<string, string>;
  seizure_location?: string;
  officer_in_charge?: string;
  size_mb?: number;
  custody_status?: "PROCESSING" | "VERIFIED" | "SEALED";
}

export interface IngestionResponse {
  status: string;
  module: string;
  message: string;
  nodesCreated: number;
  edgesCreated: number;
  entities: string[];
  relationships: string[];
  timestamp: string;
}

export interface DashboardMetrics {
  summary: {
    totalEntities: number;
    totalRelationships: number;
    totalCases: number;
    totalEvidence: number;
    highRiskTargets: number;
  };
  threatMatrix: Array<{ name: string; value: number; key: string }>;
  syndicates: Array<{
    network: string;
    nodes: number;
    links: number;
    risk: number;
  }>;
  totalRecords: number;
}
