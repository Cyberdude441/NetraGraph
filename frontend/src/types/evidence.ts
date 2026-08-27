import type { Entity } from "./entity";
import type { Relationship } from "./relationship";

export type EvidenceType = "Audio" | "Video" | "Document" | "Data" | "Image";
export type VerificationStatus = "Verified" | "Processing" | "Sealed" | "Flagged";

export interface Evidence {
  id: string;
  fileName: string;
  fileType: EvidenceType;
  hash: string;
  uploadedBy: string;
  timestamp: string;
  verificationStatus: VerificationStatus;
  case?: string;
  size?: string;
  extractedEntitiesCount?: number;
}

export interface DocumentAnalysisResult {
  documentId: string;
  fileName: string;
  extractedEntities: Entity[];
  extractedRelationships: Relationship[];
  summary: string;
  riskIndicators: string[];
}
