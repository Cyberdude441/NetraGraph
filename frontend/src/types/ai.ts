import type { EntityType, RelationshipType } from "./index";

export type AIProvider = "nemotron" | "gemini" | "auto";

export type AITaskType =
  | "entity_extraction"
  | "relationship_analysis"
  | "risk_assessment"
  | "investigation_summary"
  | "analyze_document"
  | "generate_report";

export interface AIEntity {
  name: string;
  type: EntityType;
  confidence: number;
  role?: string;
  riskScore?: number;
}

export interface AIRelationship {
  source: string;
  target: string;
  type: RelationshipType | string;
  confidence: number;
  detail?: string;
}

export interface AIAnalysisResult {
  summary: string;
  entities?: AIEntity[];
  relationships?: AIRelationship[];
  riskExplanation?: string;
  keyFindings?: string[];
  timeline?: Array<{ date: string; event: string }>;
  confidenceScore?: number;
  overallThreatScore?: number;
  threatLevel?: string;
  threatDrivers?: string[];
  recommendedInterventions?: string[];
  provider?: string;
  task?: string;
  raw?: string;
}

export interface AIAnalyzeResponse {
  provider: string;
  task: string;
  status: "success" | "error";
  result: AIAnalysisResult;
}

export interface AIProviderStatus {
  name: string;
  status: "connected" | "not_connected";
  model: string;
  capabilities: string[];
}

export interface AIStatusResponse {
  default_provider: AIProvider;
  providers: {
    nemotron: AIProviderStatus;
    gemini: AIProviderStatus;
  };
}
