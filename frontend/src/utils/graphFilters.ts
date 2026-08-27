import type { SyntheticEntity, SyntheticRelationship } from "@/data/syntheticGraphData";

export interface GraphFilterCriteria {
  entityTypes: Set<string>;
  riskLevels: Set<string>; // "low" | "medium" | "high" | "critical"
  minRiskScore: number;
  caseId: string; // "ALL" or specific
  investigationGroup: string; // "ALL" or specific
  relationshipTypes: Set<string>;
  temporalWindowDays: number; // 0 = all time, 30, 90, 180, 365
  dateRange: {
    start: string;
    end: string;
  };
  isolatedNodeIds?: Set<string> | null;
  searchQuery?: string;
}

export const ALL_ENTITY_TYPES = [
  "Person",
  "Phone",
  "Location",
  "Vehicle",
  "Organization",
  "BankAccount",
  "Device",
  "Event",
] as const;

export const ALL_RELATIONSHIP_TYPES = [
  "COMMUNICATION",
  "FINANCIAL_TRANSFER",
  "ASSOCIATION",
  "LOCATION_OVERLAP",
  "OWNERSHIP",
  "EVENT_PARTICIPATION",
] as const;

export const DEFAULT_FILTERS: GraphFilterCriteria = {
  entityTypes: new Set(ALL_ENTITY_TYPES),
  riskLevels: new Set(["low", "medium", "high", "critical"]),
  minRiskScore: 0,
  caseId: "ALL",
  investigationGroup: "ALL",
  relationshipTypes: new Set(ALL_RELATIONSHIP_TYPES),
  temporalWindowDays: 0,
  dateRange: {
    start: "2023-01-01",
    end: "2026-12-31",
  },
  isolatedNodeIds: null,
  searchQuery: "",
};

export function getRiskCategory(score: number): "low" | "medium" | "high" | "critical" {
  if (score >= 85) return "critical";
  if (score >= 70) return "high";
  if (score >= 50) return "medium";
  return "low";
}

/**
 * Pure filter pipeline evaluated on graph updates
 */
export function applyGraphFilters(
  entities: SyntheticEntity[],
  relationships: SyntheticRelationship[],
  filters: GraphFilterCriteria
): {
  filteredEntities: SyntheticEntity[];
  filteredRelationships: SyntheticRelationship[];
  filterStats: {
    totalEntities: number;
    matchedEntities: number;
    totalRelationships: number;
    matchedRelationships: number;
  };
} {
  const query = (filters.searchQuery || "").trim().toLowerCase();

  // 1. Filter Entities
  const filteredEntities = entities.filter((entity) => {
    // Isolated Subgraph constraint
    if (filters.isolatedNodeIds && filters.isolatedNodeIds.size > 0) {
      if (!filters.isolatedNodeIds.has(entity.id)) return false;
    }

    // Entity Type filter
    if (!filters.entityTypes.has(entity.label)) {
      return false;
    }

    // Min Risk Score filter
    if (entity.riskScore < filters.minRiskScore) {
      return false;
    }

    // Risk category filter
    const riskCat = getRiskCategory(entity.riskScore);
    if (!filters.riskLevels.has(riskCat)) {
      return false;
    }

    // Case ID filter
    if (filters.caseId !== "ALL" && entity.caseId !== filters.caseId) {
      return false;
    }

    // Investigation group filter
    if (
      filters.investigationGroup !== "ALL" &&
      entity.investigationGroup !== filters.investigationGroup
    ) {
      return false;
    }

    // Date range filter
    if (filters.dateRange.start && entity.lastSeen < filters.dateRange.start) {
      return false;
    }
    if (filters.dateRange.end && entity.firstSeen > filters.dateRange.end) {
      return false;
    }

    // Search query
    if (query) {
      const matchName = entity.name.toLowerCase().includes(query);
      const matchRole = (entity.role || "").toLowerCase().includes(query);
      const matchId = entity.id.toLowerCase().includes(query);
      const matchAlias = (entity.metadata.alias || []).some((a) =>
        a.toLowerCase().includes(query)
      );
      const matchTag = (entity.metadata.tags || []).some((t) =>
        t.toLowerCase().includes(query)
      );
      if (!matchName && !matchRole && !matchId && !matchAlias && !matchTag) {
        return false;
      }
    }

    return true;
  });

  const validEntityIds = new Set(filteredEntities.map((e) => e.id));

  // 2. Filter Relationships
  const filteredRelationships = relationships.filter((rel) => {
    // Both endpoints must exist in filtered entity set
    if (!validEntityIds.has(rel.sourceId) || !validEntityIds.has(rel.targetId)) {
      return false;
    }

    // Relationship type filter
    if (!filters.relationshipTypes.has(rel.type)) {
      return false;
    }

    // Date range filter
    if (filters.dateRange.start && rel.timestamp < filters.dateRange.start) {
      return false;
    }

    return true;
  });

  return {
    filteredEntities,
    filteredRelationships,
    filterStats: {
      totalEntities: entities.length,
      matchedEntities: filteredEntities.length,
      totalRelationships: relationships.length,
      matchedRelationships: filteredRelationships.length,
    },
  };
}
