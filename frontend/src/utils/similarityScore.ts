/**
 * String and Multi-factor similarity algorithms for Entity Resolution
 */

// Levenshtein distance
export function levenshteinDistance(a: string, b: string): number {
  const an = a ? a.length : 0;
  const bn = b ? b.length : 0;
  if (an === 0) return bn;
  if (bn === 0) return an;

  const matrix: number[][] = [];
  for (let i = 0; i <= bn; ++i) matrix[i] = [i];
  for (let i = 0; i <= an; ++i) matrix[0]![i] = i;

  for (let i = 1; i <= bn; ++i) {
    for (let j = 1; j <= an; ++j) {
      if (b.charAt(i - 1).toLowerCase() === a.charAt(j - 1).toLowerCase()) {
        matrix[i]![j] = matrix[i - 1]![j - 1]!;
      } else {
        matrix[i]![j] = Math.min(
          matrix[i - 1]![j - 1]! + 1, // substitution
          matrix[i]![j - 1]! + 1, // insertion
          matrix[i - 1]![j]! + 1 // deletion
        );
      }
    }
  }

  return matrix[bn]![an]!;
}

// Normalized string similarity (0.0 to 1.0)
export function stringSimilarity(str1: string, str2: string): number {
  const s1 = (str1 || "").trim().toLowerCase();
  const s2 = (str2 || "").trim().toLowerCase();
  if (s1 === s2) return 1.0;
  if (!s1 || !s2) return 0.0;

  const maxLen = Math.max(s1.length, s2.length);
  if (maxLen === 0) return 1.0;

  const dist = levenshteinDistance(s1, s2);
  return Math.max(0, 1 - dist / maxLen);
}

// Name similarity with alias and initials expansion
export function calculateNameSimilarity(nameA: string, nameB: string, aliasesA: string[] = [], aliasesB: string[] = []): number {
  const poolA = [nameA, ...aliasesA].filter(Boolean);
  const poolB = [nameB, ...aliasesB].filter(Boolean);

  let maxScore = 0;
  for (const a of poolA) {
    for (const b of poolB) {
      const score = stringSimilarity(a, b);
      if (score > maxScore) maxScore = score;

      // Handle initials matching (e.g. "Rahul Kumar" vs "R. Kumar" or "R Kumar")
      const wordsA = a.split(/\s+/);
      const wordsB = b.split(/\s+/);
      if (wordsA.length > 1 && wordsB.length > 1) {
        const lastA = wordsA[wordsA.length - 1]!.toLowerCase();
        const lastB = wordsB[wordsB.length - 1]!.toLowerCase();
        const firstA = wordsA[0]!.toLowerCase();
        const firstB = wordsB[0]!.toLowerCase();

        if (lastA === lastB && (firstA[0] === firstB[0])) {
          maxScore = Math.max(maxScore, 0.88);
        }
      }
    }
  }

  return Math.round(maxScore * 100);
}

export interface MatchBreakdown {
  nameSimilarity: number;
  sharedIdentifiers: number;
  locationCorrelation: number;
  relationshipOverlap: number;
  overallConfidence: number;
  confidenceCategory: "Strong candidate" | "Probable match" | "Possible similarity" | "Low confidence";
  reasons: string[];
}

/**
 * Multi-Attribute Resolution Matrix Calculator
 */
export function calculateResolutionMatrix(
  entityA: {
    name: string;
    label: string;
    metadata: Record<string, any>;
    caseId?: string;
    investigationGroup?: string;
  },
  entityB: {
    name: string;
    label: string;
    metadata: Record<string, any>;
    caseId?: string;
    investigationGroup?: string;
  },
  connectedNeighborIdsA: string[] = [],
  connectedNeighborIdsB: string[] = []
): MatchBreakdown {
  const reasons: string[] = [];

  // 1. Name & Alias similarity
  const aliasesA = entityA.metadata?.alias ? (Array.isArray(entityA.metadata.alias) ? entityA.metadata.alias : [entityA.metadata.alias]) : [];
  const aliasesB = entityB.metadata?.alias ? (Array.isArray(entityB.metadata.alias) ? entityB.metadata.alias : [entityB.metadata.alias]) : [];
  const nameScore = calculateNameSimilarity(entityA.name, entityB.name, aliasesA, aliasesB);

  if (nameScore >= 90) reasons.push(`High phonetic/string match between names (${nameScore}%)`);
  else if (nameScore >= 75) reasons.push(`Partial alias or abbreviation alignment (${nameScore}%)`);

  // 2. Shared Identifiers (Phone IMEI, Bank Account prefixes, IPs)
  let idScore = 30;
  const imeiA = entityA.metadata?.phoneImei || entityA.metadata?.imei;
  const imeiB = entityB.metadata?.phoneImei || entityB.metadata?.imei;
  if (imeiA && imeiB && imeiA === imeiB) {
    idScore = 100;
    reasons.push("Identical hardware IMEI fingerprint detected");
  } else if (entityA.metadata?.accountNumber && entityB.metadata?.accountNumber && entityA.metadata.accountNumber === entityB.metadata.accountNumber) {
    idScore = 100;
    reasons.push("Exact bank account number match across dockets");
  } else if (entityA.caseId && entityB.caseId && entityA.caseId === entityB.caseId) {
    idScore = 75;
    reasons.push(`Both records indexed under case docket ${entityA.caseId}`);
  }

  // 3. Location Correlation
  let locScore = 40;
  const locA = entityA.metadata?.jurisdiction || entityA.metadata?.location;
  const locB = entityB.metadata?.jurisdiction || entityB.metadata?.location;
  if (locA && locB) {
    const locSim = stringSimilarity(locA, locB);
    locScore = Math.round(locSim * 100);
    if (locScore >= 80) reasons.push(`Operating in matching jurisdiction: ${locA}`);
  }

  // 4. Relationship overlap (Jaccard Index)
  let relScore = 20;
  const setA = new Set(connectedNeighborIdsA);
  const setB = new Set(connectedNeighborIdsB);
  let intersection = 0;
  setA.forEach((id) => {
    if (setB.has(id)) intersection++;
  });
  const union = new Set([...connectedNeighborIdsA, ...connectedNeighborIdsB]).size;

  if (union > 0) {
    const jaccard = intersection / union;
    relScore = Math.round(jaccard * 100);
    if (intersection > 0) {
      reasons.push(`Shares ${intersection} mutual direct network associate(s)`);
    }
  } else if (entityA.investigationGroup && entityB.investigationGroup && entityA.investigationGroup === entityB.investigationGroup) {
    relScore = 80;
    reasons.push(`Co-located in syndicate cluster: ${entityA.investigationGroup}`);
  }

  // Composite Weighted Score
  const overall = Math.round(
    nameScore * 0.35 +
    idScore * 0.25 +
    locScore * 0.15 +
    relScore * 0.25
  );

  let category: MatchBreakdown["confidenceCategory"] = "Low confidence";
  if (overall >= 90) category = "Strong candidate";
  else if (overall >= 70) category = "Probable match";
  else if (overall >= 40) category = "Possible similarity";

  return {
    nameSimilarity: nameScore,
    sharedIdentifiers: idScore,
    locationCorrelation: locScore,
    relationshipOverlap: relScore,
    overallConfidence: overall,
    confidenceCategory: category,
    reasons,
  };
}
