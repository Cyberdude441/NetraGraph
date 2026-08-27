export type EntityType =
  | "person"
  | "organization"
  | "location"
  | "phone"
  | "vehicle"
  | "bank"
  | "device"
  | "ip"
  | "domain";

export type RelationType =
  | "calls"
  | "transaction"
  | "meeting"
  | "association"
  | "location"
  | "ownership";

export const ENTITY_META: Record<EntityType, { label: string; color: string }> = {
  person: { label: "Person", color: "var(--chart-1)" },
  organization: { label: "Organization", color: "var(--chart-3)" },
  location: { label: "Location", color: "var(--chart-2)" },
  phone: { label: "Phone Number", color: "var(--warning)" },
  vehicle: { label: "Vehicle", color: "var(--success)" },
  bank: { label: "Bank Account", color: "var(--critical)" },
  device: { label: "Digital Device", color: "var(--chart-4)" },
  ip: { label: "IP Address", color: "var(--chart-5)" },
  domain: { label: "Domain Host", color: "var(--chart-6)" },
};

export const RELATION_META: Record<
  RelationType,
  { label: string; color: string; dashed: boolean }
> = {
  calls: { label: "Calls", color: "var(--chart-2)", dashed: false },
  transaction: { label: "Transactions", color: "var(--critical)", dashed: false },
  meeting: { label: "Meetings", color: "var(--warning)", dashed: true },
  association: { label: "Association", color: "var(--chart-3)", dashed: true },
  location: { label: "Location Link", color: "var(--chart-1)", dashed: true },
  ownership: { label: "Ownership Link", color: "var(--success)", dashed: false },
};

export const entityNodes = [];
export const initialEdges = [];
