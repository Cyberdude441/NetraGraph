export interface OGDDatasetMetadata {
  dataset_id: string;
  dataset_name: string;
  dataset_year: string;
  source_url: string;
  resource_id: string;
  description: string;
  last_sync_time: string | null;
  record_count: number;
  status: "READY" | "SYNCED" | "ERROR" | string;
}

export interface OGDPipelineStatus {
  pipeline: string;
  last_sync_timestamp: string;
  is_syncing: boolean;
  datasets: OGDDatasetMetadata[];
  total_datasets: number;
  total_records_stored: number;
}

export type Neo4jNodeType =
  | "State"
  | "Year"
  | "CyberCrimeCategory"
  | "CrimeMotive"
  | "PoliceDisposal"
  | "CourtOutcome"
  | "ArrestStatus";

export type Neo4jRelationType =
  | "STATE_HAS_CASES"
  | "STATE_HAS_MOTIVE"
  | "CRIME_HAS_POLICE_STATUS"
  | "CRIME_HAS_COURT_STATUS"
  | "CRIME_HAS_ARREST_STATUS"
  | "RECORDED_IN_YEAR";

export interface Neo4jGraphNode {
  id: string;
  label: Neo4jNodeType;
  name: string;
  sourceDataset?: string;
  updatedAt?: string;
  stateCode?: string;
  legalAct?: string;
  motiveCategory?: string;
  cases2025?: number;
  ratePerLakh?: number;
  populationLakhs?: number;
  percentage?: number;
  chargesheetRate?: number;
  convictionRate?: number;
  totalInvestigated?: number;
  pendingInvestigation?: number;
  totalTrials?: number;
  convicted?: number;
  pendingTrial?: number;
  personsArrested?: number;
  position?: { x: number; y: number };
  metadata?: {
    category?: string;
    riskScore?: number;
    description?: string;
    details?: Array<[string, string]>;
  };
}

export interface Neo4jGraphRelationship {
  id: string;
  type: Neo4jRelationType;
  sourceId: string;
  targetId: string;
  metadata?: {
    label?: string;
    weight?: number;
    detail?: string;
  };
}

export interface Neo4jGraphPayload {
  nodes: Neo4jGraphNode[];
  relationships: Neo4jGraphRelationship[];
  totalNodes: number;
  totalRelationships: number;
  lastUpdated: string;
  sourceDataset: string;
}

export interface DominantMotive {
  Motive: string;
  Category: string;
  Cases: number;
  Percentage: number;
  Risk_Level: string;
}

export interface NCRBMotiveRecord {
  state: string;
  year: number;
  crime_motive: string;
  motive_full?: string;
  cases: number;
  percentage?: number;
  category?: string;
  risk_level?: string;
}

export interface NCRBCyberCrime {
  state: string;
  year: number;
  incidents: number;
  incidents2023?: number;
  incidents2024?: number;
  incidents2025?: number;
  rate_per_lakh: number;
  chargesheet_rate: number;
  conviction_rate: number;
  persons_arrested: number;
  source?: string;
}

export interface NCRBInvestigationRecord {
  crime_head: string;
  total_investigated: number;
  disposed_by_police: number;
  chargesheeted: number;
  pending_investigation: number;
  chargesheet_rate: number;
  final_reports?: number;
}

export interface NCRBCourtRecord {
  crime_head: string;
  total_trials: number;
  disposed_by_courts: number;
  convicted: number;
  acquitted: number;
  pending_trial: number;
  conviction_rate: number;
}

export interface PoliceDisposalStat {
  Crime_Head: string;
  Total_Investigated: number;
  Disposed_By_Police: number;
  Chargesheeted: number;
  Pending_Investigation: number;
  Chargesheet_Rate: number;
}

export interface CourtDisposalStat {
  Crime_Head: string;
  Total_Trials: number;
  Disposed_By_Courts: number;
  Convicted: number;
  Acquitted: number;
  Pending_Trial: number;
  Conviction_Rate: number;
}

export interface ArrestDisposalStat {
  Crime_Head: string;
  Persons_Arrested: number;
  Persons_Chargesheeted: number;
  Persons_Convicted: number;
  Persons_Acquitted: number;
  Persons_In_Custody_Bail: number;
}

export interface NCRBOverview {
  nationalTotal2025: number;
  nationalTotal2024: number;
  nationalTotal2023: number;
  yoyGrowthPercent: number;
  totalFinancialLossCr: number;
  totalPersonsArrested: number;
  avgChargesheetRate: number;
  avgConvictionRate: number;
  topHotspots: Array<{
    state: string;
    cases: number;
    rate: number;
  }>;
  totalStatesTracked: number;
  totalCategoriesTracked: number;
}

export interface NCRBStateCrime {
  state: string;
  incidents2023: number;
  incidents2024: number;
  incidents2025: number;
  ratePerLakh: number;
  chargesheetRate: number;
  convictionRate: number;
  personsArrested: number;
}

export interface NCRBCategoryCrime {
  category: string;
  count: number;
  percentage: number;
  financialLossCr: number;
  motive: string;
  riskLevel: "CRITICAL" | "HIGH" | "MODERATE" | "LOW" | string;
}

export interface NCRBITActSection {
  sectionCode: string;
  act: string;
  description: string;
  totalCases: number;
  convictions: number;
  chargesheetRate: number;
}
