export type EntityType =
  | "Person"
  | "Organization"
  | "Location"
  | "Phone"
  | "Vehicle"
  | "BankAccount"
  | "Device"
  | "IPAddress"
  | "Domain";

export interface EntityMetadata {
  alias?: string;
  role?: string;
  status?: string;
  network?: string;
  location?: string;
  offenses?: string[];
  lastSeen?: string;
  associates?: number;
  position?: { x: number; y: number };
  subtitle?: string;
  details?: Array<[string, string]>;
  imei?: string;
  imsi?: string;
  ip?: string;
  bank?: string;
  accountNumber?: string;
  [key: string]: unknown;
}

export interface Entity {
  id: string;
  name: string;
  type: EntityType;
  riskScore: number;
  source?: string;
  confidence?: number;
  metadata: EntityMetadata;
  createdAt: string;
}
