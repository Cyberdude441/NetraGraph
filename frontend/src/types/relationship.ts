export type RelationshipType =
  | "CALL"
  | "TRANSACTION"
  | "LOGIN"
  | "OWNS"
  | "LOCATED_AT"
  | "ASSOCIATED_WITH"
  | "COMMUNICATED_WITH"
  | "CALLS"
  | "TRANSACTS"
  | "MEETS";

export interface RelationshipMetadata {
  weight?: number;
  label?: string;
  detail?: string;
  amount?: number | string;
  frequency?: number;
  duration?: number;
  bank?: string;
  towerLocation?: string;
  sourceReference?: string;
  [key: string]: unknown;
}

export interface Relationship {
  id: string;
  sourceId: string;
  targetId: string;
  type: RelationshipType;
  confidence: number;
  sourceReference?: string;
  timestamp?: string;
  createdAt?: string;
  metadata?: RelationshipMetadata;
}
