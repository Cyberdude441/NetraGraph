export type CasePriority = "Critical" | "High" | "Moderate" | "Low";
export type CaseStatus = "Active" | "Under Review" | "Closed" | "Archived";

export interface Case {
  id: string;
  title: string;
  description: string;
  status: CaseStatus;
  priority: CasePriority;
  lead?: string;
  progress?: number;
  suspects?: number;
  createdAt: string;
  updatedAt?: string;
}
