import type { SyntheticEntity, SyntheticRelationship } from "@/data/syntheticGraphData";

export interface CommunityDetail {
  id: number;
  name: string;
  color: string;
  memberCount: number;
  members: SyntheticEntity[];
  density: number; // 0.0 to 1.0
  internalEdgeCount: number;
  externalEdgeCount: number;
  bridgeNodes: { entityId: string; name: string; connectedClusterIds: number[]; externalLinksCount: number }[];
  dominantType: string;
  avgRisk: number;
  topInfluencer: { name: string; id: string; role?: string; risk: number };
}

export interface ModularityMetrics {
  modularityScore: number; // Q-Score (-1 to +1, usually 0.3 to 0.7 for high modularity)
  communityCount: number;
  totalInternalEdges: number;
  totalExternalEdges: number;
  networkFragmentationScore: number; // 0.0 to 1.0
  interactionMatrix: { sourceCluster: string; targetCluster: string; linkCount: number; amountINR?: number }[];
}

export const CLUSTER_PALETTE = [
  "#38BDF8", // Cyan / Blue (Noida Tech Support Scam)
  "#F59E0B", // Amber / Gold (Bhubaneswar SIM Box Ring)
  "#A855F7", // Purple (LockNet Ransomware Group)
  "#10B981", // Emerald (Inter-State Hawala Network)
  "#EC4899", // Pink (Mule Ledger Syndicate Tier-2)
  "#6366F1", // Indigo
];

/**
 * Advanced Community Detection & Modularity Engine
 */
export function analyzeCommunitiesAndModularity(
  entities: SyntheticEntity[],
  relationships: SyntheticRelationship[]
): {
  communities: CommunityDetail[];
  modularity: ModularityMetrics;
} {
  const n = entities.length;
  const m = relationships.length;

  if (n === 0 || m === 0) {
    return {
      communities: [],
      modularity: {
        modularityScore: 0,
        communityCount: 0,
        totalInternalEdges: 0,
        totalExternalEdges: 0,
        networkFragmentationScore: 0,
        interactionMatrix: [],
      },
    };
  }

  // 1. Group entities by cluster
  const clusterMap = new Map<string, SyntheticEntity[]>();
  entities.forEach((e) => {
    const key = e.investigationGroup || "Independent Cell";
    if (!clusterMap.has(key)) clusterMap.set(key, []);
    clusterMap.get(key)!.push(e);
  });

  const entityToClusterId = new Map<string, number>();
  const clusterNames = Array.from(clusterMap.keys());
  clusterNames.forEach((name, idx) => {
    const mems = clusterMap.get(name) || [];
    mems.forEach((e) => entityToClusterId.set(e.id, idx));
  });

  // 2. Count internal & external links per community and for the interaction matrix
  const internalEdgesPerCluster = new Map<number, number>();
  const externalEdgesPerCluster = new Map<number, number>();
  const clusterInteractions = new Map<string, number>();

  clusterNames.forEach((_, idx) => {
    internalEdgesPerCluster.set(idx, 0);
    externalEdgesPerCluster.set(idx, 0);
  });

  let totalInternal = 0;
  let totalExternal = 0;

  relationships.forEach((rel) => {
    const srcC = entityToClusterId.get(rel.sourceId);
    const tgtC = entityToClusterId.get(rel.targetId);

    if (srcC !== undefined && tgtC !== undefined) {
      if (srcC === tgtC) {
        internalEdgesPerCluster.set(srcC, (internalEdgesPerCluster.get(srcC) || 0) + 1);
        totalInternal++;
      } else {
        externalEdgesPerCluster.set(srcC, (externalEdgesPerCluster.get(srcC) || 0) + 1);
        externalEdgesPerCluster.set(tgtC, (externalEdgesPerCluster.get(tgtC) || 0) + 1);
        totalExternal++;

        const pairKey = [clusterNames[srcC], clusterNames[tgtC]].sort().join(" <-> ");
        clusterInteractions.set(pairKey, (clusterInteractions.get(pairKey) || 0) + 1);
      }
    }
  });

  // 3. Compute Louvain-style Modularity Q
  // Q = sum_c [ (l_c / m) - (d_c / (2m))^2 ]
  let modularityQ = 0;
  clusterNames.forEach((_, cIdx) => {
    const l_c = internalEdgesPerCluster.get(cIdx) || 0;
    const ext_c = externalEdgesPerCluster.get(cIdx) || 0;
    const d_c = 2 * l_c + ext_c; // total degree of community
    const qPart = l_c / m - Math.pow(d_c / (2 * m), 2);
    modularityQ += qPart;
  });

  modularityQ = Number(modularityQ.toFixed(3));

  // 4. Build Community Details
  const communities: CommunityDetail[] = [];
  clusterNames.forEach((name, cIdx) => {
    const members = clusterMap.get(name) || [];
    const memCount = members.length;
    const possibleEdges = (memCount * (memCount - 1)) / 2 || 1;
    const internalCount = internalEdgesPerCluster.get(cIdx) || 0;
    const externalCount = externalEdgesPerCluster.get(cIdx) || 0;
    const density = Number((internalCount / possibleEdges).toFixed(2));

    // Find bridge nodes in this community
    const bridgeMap = new Map<string, { connectedClusterIds: Set<number>; count: number }>();
    relationships.forEach((rel) => {
      const srcC = entityToClusterId.get(rel.sourceId);
      const tgtC = entityToClusterId.get(rel.targetId);

      if (srcC === cIdx && tgtC !== undefined && tgtC !== cIdx) {
        if (!bridgeMap.has(rel.sourceId)) {
          bridgeMap.set(rel.sourceId, { connectedClusterIds: new Set(), count: 0 });
        }
        bridgeMap.get(rel.sourceId)!.connectedClusterIds.add(tgtC);
        bridgeMap.get(rel.sourceId)!.count++;
      } else if (tgtC === cIdx && srcC !== undefined && srcC !== cIdx) {
        if (!bridgeMap.has(rel.targetId)) {
          bridgeMap.set(rel.targetId, { connectedClusterIds: new Set(), count: 0 });
        }
        bridgeMap.get(rel.targetId)!.connectedClusterIds.add(srcC);
        bridgeMap.get(rel.targetId)!.count++;
      }
    });

    const bridgeNodes = Array.from(bridgeMap.entries()).map(([eId, val]) => {
      const ent = entities.find((e) => e.id === eId);
      return {
        entityId: eId,
        name: ent?.name || eId,
        connectedClusterIds: Array.from(val.connectedClusterIds),
        externalLinksCount: val.count,
      };
    });

    // Dominant class & Risk
    const typeCount: Record<string, number> = {};
    let totalRisk = 0;
    let topInf = members[0] || { name: "None", id: "", riskScore: 0 };

    members.forEach((m) => {
      typeCount[m.label] = (typeCount[m.label] || 0) + 1;
      totalRisk += m.riskScore;
      if (m.riskScore > topInf.riskScore) topInf = m;
    });

    const dominantType =
      Object.entries(typeCount).sort((a, b) => b[1] - a[1])[0]?.[0] || "Mixed";

    communities.push({
      id: cIdx,
      name,
      color: CLUSTER_PALETTE[cIdx % CLUSTER_PALETTE.length] || "#38BDF8",
      memberCount: memCount,
      members,
      density: Math.min(1.0, density),
      internalEdgeCount: internalCount,
      externalEdgeCount: externalCount,
      bridgeNodes,
      dominantType,
      avgRisk: Math.round(totalRisk / (memCount || 1)),
      topInfluencer: {
        name: topInf.name,
        id: topInf.id,
        role: topInf.role,
        risk: topInf.riskScore,
      },
    });
  });

  // Interaction Matrix for Modularity Table
  const interactionMatrix = Array.from(clusterInteractions.entries()).map(([pair, count]) => {
    const [c1, c2] = pair.split(" <-> ");
    return {
      sourceCluster: c1 || "Cluster A",
      targetCluster: c2 || "Cluster B",
      linkCount: count,
    };
  });

  const fragmentationScore = Number(
    (totalExternal / (totalInternal + totalExternal || 1)).toFixed(2)
  );

  return {
    communities,
    modularity: {
      modularityScore: modularityQ,
      communityCount: communities.length,
      totalInternalEdges: totalInternal,
      totalExternalEdges: totalExternal,
      networkFragmentationScore: fragmentationScore,
      interactionMatrix,
    },
  };
}
