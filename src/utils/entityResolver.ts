import type { ComprehensiveEntity, EntityTimelineEvent } from "@/data/syntheticEntities";

export interface AuditLogEntry {
  id: string;
  action: "ENTITY_MERGED" | "ALIAS_ADDED" | "CONFIDENCE_UPDATED" | "RISK_RECALIBRATED" | "STATUS_CHANGED";
  entityId: string;
  entityName: string;
  userRole: string;
  userName: string;
  timestamp: string;
  details: string;
  previousValue?: string | number | Record<string, any>;
  newValue?: string | number | Record<string, any>;
}

export const INITIAL_AUDIT_LOGS: AuditLogEntry[] = [
  {
    id: "AUD-901",
    action: "ALIAS_ADDED",
    entityId: "ENT-001",
    entityName: "Vikramaditya Rawat",
    userRole: "Inspector / Senior Analyst",
    userName: "Insp. D. Bose",
    timestamp: "2026-08-25T14:20:00Z",
    details: "Added alias 'Boss-V' based on wiretap transcript corroboration.",
    previousValue: '["Vikram Rawat", "Vicky Bhai"]',
    newValue: '["Vikram Rawat", "Vicky Bhai", "Boss-V"]',
  },
  {
    id: "AUD-902",
    action: "CONFIDENCE_UPDATED",
    entityId: "ENT-009",
    entityName: "Mukesh 'Kolkata' Seth",
    userRole: "Cyber Forensic Officer",
    userName: "Insp. D. Bose",
    timestamp: "2026-08-24T18:45:00Z",
    details: "Attribution confidence raised to 97% following Section 65B certified surveillance logs.",
    previousValue: "88%",
    newValue: "97%",
  },
  {
    id: "AUD-903",
    action: "ENTITY_MERGED",
    entityId: "ENT-011",
    entityName: "Deepak Kumar Mohanty",
    userRole: "Inspector / Senior Analyst",
    userName: "Insp. D. Bose",
    timestamp: "2026-08-23T11:10:00Z",
    details: "Merged secondary subscriber profile 'D. Mohanty' into primary POS operator dossier.",
    previousValue: "2 Separate Records",
    newValue: "1 Unified Dossier (ENT-011)",
  },
];

/**
 * Execute merge of secondary candidate profile into primary profile
 */
export function mergeEntityProfiles(
  primaryEntity: ComprehensiveEntity,
  secondaryEntity: ComprehensiveEntity,
  options: {
    userName?: string;
    userRole?: string;
    customAliasList?: string[];
  }
): {
  mergedEntity: ComprehensiveEntity;
  auditEntry: AuditLogEntry;
} {
  const allAliases = Array.from(
    new Set([
      ...(primaryEntity.metadata.alias || []),
      secondaryEntity.name,
      ...(secondaryEntity.metadata.alias || []),
      ...(options.customAliasList || []),
    ])
  ).filter((a) => a !== primaryEntity.name);

  const allTags = Array.from(
    new Set([...(primaryEntity.metadata.tags || []), ...(secondaryEntity.metadata.tags || []), "Resolved & Merged"])
  );

  const allOffenses = Array.from(
    new Set([
      ...(primaryEntity.metadata.statutoryOffenses || []),
      ...(secondaryEntity.metadata.statutoryOffenses || []),
    ])
  );

  // Unified chronological timeline
  const combinedTimeline: EntityTimelineEvent[] = [
    ...primaryEntity.timeline,
    ...secondaryEntity.timeline,
    {
      id: `EVT-MERGE-${Date.now()}`,
      type: "RELATIONSHIP_CHANGE",
      title: `Identity Resolution Merge: ${secondaryEntity.name}`,
      timestamp: new Date().toISOString(),
      description: `Secondary profile record [${secondaryEntity.id}: ${secondaryEntity.name}] successfully unified into primary dossier under audit oversight.`,
      severity: "info",
      sourceRef: `AUDIT-MERGE-${primaryEntity.id}`,
    },
  ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  const mergedLoss =
    (primaryEntity.metadata.financialLossINR || 0) +
    (secondaryEntity.metadata.financialLossINR || 0);

  const mergedEntity: ComprehensiveEntity = {
    ...primaryEntity,
    riskScore: Math.max(primaryEntity.riskScore, secondaryEntity.riskScore),
    confidenceScore: Math.max(primaryEntity.confidenceScore, secondaryEntity.confidenceScore),
    degreeCount: (primaryEntity.degreeCount || 0) + (secondaryEntity.degreeCount || 0),
    relationshipsCount: (primaryEntity.relationshipsCount || 0) + (secondaryEntity.relationshipsCount || 0),
    timeline: combinedTimeline,
    metadata: {
      ...primaryEntity.metadata,
      alias: allAliases,
      tags: allTags,
      statutoryOffenses: allOffenses,
      financialLossINR: mergedLoss > 0 ? mergedLoss : undefined,
      phoneImei: primaryEntity.metadata.phoneImei || secondaryEntity.metadata.phoneImei,
      accountNumber: primaryEntity.metadata.accountNumber || secondaryEntity.metadata.accountNumber,
      duplicateCandidateOf: undefined,
    },
  };

  const auditEntry: AuditLogEntry = {
    id: `AUD-${Date.now()}`,
    action: "ENTITY_MERGED",
    entityId: primaryEntity.id,
    entityName: primaryEntity.name,
    userRole: options.userRole || "Inspector / Senior Analyst",
    userName: options.userName || "Insp. D. Bose",
    timestamp: new Date().toISOString(),
    details: `Unified secondary record ${secondaryEntity.id} (${secondaryEntity.name}) into primary dossier ${primaryEntity.id}. Combined ${allAliases.length} aliases and unified ${combinedTimeline.length} chronological events.`,
    previousValue: {
      primary: { id: primaryEntity.id, name: primaryEntity.name },
      secondary: { id: secondaryEntity.id, name: secondaryEntity.name },
    },
    newValue: {
      unifiedId: primaryEntity.id,
      unifiedName: primaryEntity.name,
      totalAliases: allAliases,
    },
  };

  return { mergedEntity, auditEntry };
}
