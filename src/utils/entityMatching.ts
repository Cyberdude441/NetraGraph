import type { ComprehensiveEntity } from "@/data/syntheticEntities";
import { calculateResolutionMatrix, type MatchBreakdown, calculateNameSimilarity } from "./similarityScore";

export interface EntityFilterState {
  searchQuery: string;
  searchFields: {
    name: boolean;
    alias: boolean;
    id: boolean;
    phone: boolean;
    device: boolean;
    location: boolean;
    organization: boolean;
    caseId: boolean;
  };
  entityTypes: Set<string>;
  riskLevels: Set<"Critical" | "High" | "Medium" | "Low">;
  confidenceLevels: Set<"Verified" | "High Confidence" | "Probable" | "Unknown">;
  networkGroups: Set<string>;
  activityStatuses: Set<"Recent" | "Historical" | "Dormant">;
  minRisk: number;
}

export const DEFAULT_ENTITY_FILTERS: EntityFilterState = {
  searchQuery: "",
  searchFields: {
    name: true,
    alias: true,
    id: true,
    phone: true,
    device: true,
    location: true,
    organization: true,
    caseId: true,
  },
  entityTypes: new Set([
    "Person",
    "Phone",
    "Device",
    "Location",
    "Vehicle",
    "Organization",
    "BankAccount",
    "Event",
  ]),
  riskLevels: new Set(["Critical", "High", "Medium", "Low"]),
  confidenceLevels: new Set(["Verified", "High Confidence", "Probable", "Unknown"]),
  networkGroups: new Set(),
  activityStatuses: new Set(["Recent", "Historical", "Dormant"]),
  minRisk: 0,
};

export interface FilteredEntityResult {
  entity: ComprehensiveEntity;
  isSimilarityMatch: boolean;
  matchScore: number;
  matchField?: string;
  duplicateCount: number;
}

export function filterAndSearchEntities(
  entities: ComprehensiveEntity[],
  filters: EntityFilterState
): FilteredEntityResult[] {
  const query = (filters.searchQuery || "").trim().toLowerCase();

  return entities
    .filter((e) => {
      // 1. Entity Type
      if (!filters.entityTypes.has(e.label)) return false;

      // 2. Risk Level
      let rLevel: "Critical" | "High" | "Medium" | "Low" = "Low";
      if (e.riskScore >= 85) rLevel = "Critical";
      else if (e.riskScore >= 70) rLevel = "High";
      else if (e.riskScore >= 50) rLevel = "Medium";

      if (!filters.riskLevels.has(rLevel)) return false;
      if (e.riskScore < filters.minRisk) return false;

      // 3. Confidence Level
      if (!filters.confidenceLevels.has(e.verificationStatus)) return false;

      // 4. Activity Status
      if (!filters.activityStatuses.has(e.activityStatus)) return false;

      // 5. Network Group
      if (filters.networkGroups.size > 0 && !filters.networkGroups.has(e.investigationGroup)) {
        return false;
      }

      return true;
    })
    .map((e) => {
      if (!query) {
        return {
          entity: e,
          isSimilarityMatch: false,
          matchScore: 100,
          duplicateCount: e.metadata.duplicateCandidateOf ? 1 : 0,
        };
      }

      let isMatch = false;
      let isFuzzy = false;
      let matchScore = 0;
      let matchField = "name";

      const nameSim = calculateNameSimilarity(query, e.name, [], e.metadata.alias || []);
      if (nameSim >= 70) {
        isMatch = true;
        matchScore = nameSim;
        matchField = "name / alias";
        if (nameSim < 95) isFuzzy = true;
      }

      // ID check
      if (filters.searchFields.id && e.id.toLowerCase().includes(query)) {
        isMatch = true;
        matchScore = 100;
        matchField = "Entity ID";
      }

      // Phone / IMEI check
      if (
        filters.searchFields.phone &&
        (e.name.toLowerCase().includes(query) || (e.metadata.phoneImei && e.metadata.phoneImei.includes(query)))
      ) {
        isMatch = true;
        matchScore = 100;
        matchField = "Phone / IMEI";
      }

      // Location check
      if (
        filters.searchFields.location &&
        e.metadata.jurisdiction &&
        e.metadata.jurisdiction.toLowerCase().includes(query)
      ) {
        isMatch = true;
        matchScore = Math.max(matchScore, 85);
        matchField = "Jurisdiction";
      }

      // Case ID check
      if (filters.searchFields.caseId && e.caseId.toLowerCase().includes(query)) {
        isMatch = true;
        matchScore = Math.max(matchScore, 90);
        matchField = "Case Docket";
      }

      return {
        entity: e,
        isSimilarityMatch: isFuzzy,
        matchScore,
        matchField,
        duplicateCount: e.metadata.duplicateCandidateOf ? 1 : 0,
        _keep: isMatch,
      };
    })
    .filter((res) => (query ? res._keep : true))
    .sort((a, b) => b.matchScore - a.matchScore);
}

export interface DuplicatePair {
  id: string;
  sourceEntity: ComprehensiveEntity;
  candidateEntity: ComprehensiveEntity;
  matrix: MatchBreakdown;
}

/**
 * Scan database to find all high-confidence duplicate pairs
 */
export function findDuplicateCandidatePairs(entities: ComprehensiveEntity[]): DuplicatePair[] {
  const pairs: DuplicatePair[] = [];
  const n = entities.length;

  for (let i = 0; i < n; i++) {
    const a = entities[i]!;
    for (let j = i + 1; j < n; j++) {
      const b = entities[j]!;

      // Compare same or related types (e.g. Person vs Person, Org vs Org)
      if (a.label !== b.label) continue;

      const matrix = calculateResolutionMatrix(a, b);
      if (matrix.overallConfidence >= 65 || a.metadata.duplicateCandidateOf === b.id || b.metadata.duplicateCandidateOf === a.id) {
        pairs.push({
          id: `PAIR-${a.id}-${b.id}`,
          sourceEntity: a,
          candidateEntity: b,
          matrix,
        });
      }
    }
  }

  return pairs.sort((x, y) => y.matrix.overallConfidence - x.matrix.overallConfidence);
}
