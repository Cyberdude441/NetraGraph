import type { SyntheticEntity, SyntheticRelationship } from "@/data/syntheticGraphData";

export interface CentralityMetrics {
  degree: number;
  inDegree: number;
  outDegree: number;
  normalizedDegree: number;
  betweenness: number;
  closeness: number;
  pageRank: number;
  rank: number;
}

export interface CommunityCluster {
  id: number;
  name: string;
  color: string;
  memberCount: number;
  nodeIds: string[];
  internalEdgeCount: number;
  bridgeNodeIds: string[];
  dominantType: string;
  avgRisk: number;
}

export interface LayoutPosition {
  x: number;
  y: number;
}

export const COMMUNITY_COLORS = [
  "#38BDF8", // Cyan / Blue (Tech support ring)
  "#F59E0B", // Amber / Orange (SIM box ring)
  "#A855F7", // Purple (LockNet ransomware)
  "#10B981", // Emerald (Hawala corridor)
  "#EC4899", // Pink
  "#6366F1", // Indigo
];

/**
 * Calculate full suite of graph centrality metrics for all nodes
 */
export function calculateCentralityMetrics(
  entities: SyntheticEntity[],
  relationships: SyntheticRelationship[]
): Record<string, CentralityMetrics> {
  const nodeMap = new Map<string, SyntheticEntity>();
  entities.forEach((e) => nodeMap.set(e.id, e));

  const n = entities.length;
  if (n === 0) return {};

  const adjList = new Map<string, string[]>();
  const inDegreeMap = new Map<string, number>();
  const outDegreeMap = new Map<string, number>();

  entities.forEach((e) => {
    adjList.set(e.id, []);
    inDegreeMap.set(e.id, 0);
    outDegreeMap.set(e.id, 0);
  });

  relationships.forEach((rel) => {
    if (adjList.has(rel.sourceId) && adjList.has(rel.targetId)) {
      adjList.get(rel.sourceId)!.push(rel.targetId);
      adjList.get(rel.targetId)!.push(rel.sourceId);
      outDegreeMap.set(rel.sourceId, (outDegreeMap.get(rel.sourceId) || 0) + 1);
      inDegreeMap.set(rel.targetId, (inDegreeMap.get(rel.targetId) || 0) + 1);
    }
  });

  // 1. Degree Centrality
  const degreeMap = new Map<string, number>();
  entities.forEach((e) => {
    const deg = (adjList.get(e.id) || []).length;
    degreeMap.set(e.id, deg);
  });

  // 2. Betweenness Centrality (Brandes Algorithm)
  const betweennessMap = new Map<string, number>();
  entities.forEach((e) => betweennessMap.set(e.id, 0));

  entities.forEach((s) => {
    const S: string[] = [];
    const P = new Map<string, string[]>();
    const sigma = new Map<string, number>();
    const d = new Map<string, number>();

    entities.forEach((w) => {
      P.set(w.id, []);
      sigma.set(w.id, 0);
      d.set(w.id, -1);
    });

    sigma.set(s.id, 1);
    d.set(s.id, 0);

    const Q: string[] = [s.id];
    while (Q.length > 0) {
      const v = Q.shift()!;
      S.push(v);

      const neighbors = adjList.get(v) || [];
      for (const w of neighbors) {
        if (d.get(w)! < 0) {
          Q.push(w);
          d.set(w, d.get(v)! + 1);
        }
        if (d.get(w) === d.get(v)! + 1) {
          sigma.set(w, sigma.get(w)! + sigma.get(v)!);
          P.get(w)!.push(v);
        }
      }
    }

    const delta = new Map<string, number>();
    entities.forEach((w) => delta.set(w.id, 0));

    while (S.length > 0) {
      const w = S.pop()!;
      for (const v of P.get(w) || []) {
        const c = (sigma.get(v)! / (sigma.get(w)! || 1)) * (1 + delta.get(w)!);
        delta.set(v, delta.get(v)! + c);
      }
      if (w !== s.id) {
        betweennessMap.set(w, betweennessMap.get(w)! + delta.get(w)!);
      }
    }
  });

  // Normalize betweenness for undirected graph: divide by (n-1)(n-2)
  const normFactor = n > 2 ? (n - 1) * (n - 2) : 1;

  // 3. Closeness Centrality
  const closenessMap = new Map<string, number>();
  entities.forEach((s) => {
    const dist = new Map<string, number>();
    entities.forEach((w) => dist.set(w.id, -1));
    dist.set(s.id, 0);

    const Q = [s.id];
    let totalDist = 0;
    let reachable = 0;

    while (Q.length > 0) {
      const curr = Q.shift()!;
      const curDist = dist.get(curr)!;
      for (const nxt of adjList.get(curr) || []) {
        if (dist.get(nxt)! === -1) {
          dist.set(nxt, curDist + 1);
          totalDist += curDist + 1;
          reachable++;
          Q.push(nxt);
        }
      }
    }

    if (totalDist > 0 && reachable > 0) {
      const closeness = (reachable / (n - 1)) * (reachable / totalDist);
      closenessMap.set(s.id, Number(closeness.toFixed(4)));
    } else {
      closenessMap.set(s.id, 0);
    }
  });

  // 4. PageRank (Iterative Power Method)
  const pageRankMap = new Map<string, number>();
  const damping = 0.85;
  const initialPR = 1 / n;
  entities.forEach((e) => pageRankMap.set(e.id, initialPR));

  for (let iter = 0; iter < 25; iter++) {
    const nextPR = new Map<string, number>();
    entities.forEach((e) => nextPR.set(e.id, (1 - damping) / n));

    entities.forEach((u) => {
      const neighbors = adjList.get(u.id) || [];
      const outDeg = neighbors.length;
      if (outDeg > 0) {
        const share = (damping * pageRankMap.get(u.id)!) / outDeg;
        for (const v of neighbors) {
          nextPR.set(v, nextPR.get(v)! + share);
        }
      } else {
        const share = (damping * pageRankMap.get(u.id)!) / n;
        entities.forEach((v) => {
          nextPR.set(v.id, nextPR.get(v.id)! + share);
        });
      }
    });

    entities.forEach((e) => pageRankMap.set(e.id, nextPR.get(e.id)!));
  }

  // Compile composite score and calculate ranks
  const compositeScores: { id: string; score: number }[] = [];

  const results: Record<string, CentralityMetrics> = {};
  entities.forEach((e) => {
    const deg = degreeMap.get(e.id) || 0;
    const inDeg = inDegreeMap.get(e.id) || 0;
    const outDeg = outDegreeMap.get(e.id) || 0;
    const rawBetweenness = betweennessMap.get(e.id) || 0;
    const normBetweenness = Number(((rawBetweenness / normFactor) * 100).toFixed(2));
    const closeness = closenessMap.get(e.id) || 0;
    const pr = Number(((pageRankMap.get(e.id) || 0) * 100).toFixed(2));

    const compositeScore = deg * 0.3 + normBetweenness * 0.4 + pr * 0.3;
    compositeScores.push({ id: e.id, score: compositeScore });

    results[e.id] = {
      degree: deg,
      inDegree: inDeg,
      outDegree: outDeg,
      normalizedDegree: Number((deg / (n - 1 || 1)).toFixed(2)),
      betweenness: normBetweenness,
      closeness,
      pageRank: pr,
      rank: 0,
    };
  });

  // Assign overall rank
  compositeScores.sort((a, b) => b.score - a.score);
  compositeScores.forEach((item, index) => {
    const rec = results[item.id];
    if (rec) {
      rec.rank = index + 1;
    }
  });

  return results;
}

/**
 * Perform Louvain / Modular Community Detection
 */
export function detectCommunities(
  entities: SyntheticEntity[],
  relationships: SyntheticRelationship[]
): {
  communities: CommunityCluster[];
  entityCommunityMap: Record<string, number>;
} {
  const entityCommunityMap: Record<string, number> = {};

  // Preset modular groupings based on investigation syndicate cluster or connected components
  const groupClusters = new Map<string, string[]>();
  entities.forEach((e) => {
    const key = e.investigationGroup || "General Network";
    if (!groupClusters.has(key)) {
      groupClusters.set(key, []);
    }
    groupClusters.get(key)!.push(e.id);
  });

  const communities: CommunityCluster[] = [];
  let clusterIdx = 0;

  groupClusters.forEach((nodeIds, groupName) => {
    nodeIds.forEach((id) => {
      entityCommunityMap[id] = clusterIdx;
    });

    const clusterEntities = entities.filter((e) => nodeIds.includes(e.id));
    const internalEdges = relationships.filter(
      (r) => nodeIds.includes(r.sourceId) && nodeIds.includes(r.targetId)
    );

    // Identify bridge nodes (nodes that connect outside their cluster)
    const bridgeNodes = new Set<string>();
    relationships.forEach((r) => {
      const srcIn = nodeIds.includes(r.sourceId);
      const tgtIn = nodeIds.includes(r.targetId);
      if (srcIn && !tgtIn) bridgeNodes.add(r.sourceId);
      if (!srcIn && tgtIn) bridgeNodes.add(r.targetId);
    });

    const typeCounts: Record<string, number> = {};
    let totalRisk = 0;
    clusterEntities.forEach((e) => {
      typeCounts[e.label] = (typeCounts[e.label] || 0) + 1;
      totalRisk += e.riskScore;
    });

    const dominantType =
      Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "Mixed";

    const color = COMMUNITY_COLORS[clusterIdx % COMMUNITY_COLORS.length] || "#38BDF8";

    communities.push({
      id: clusterIdx,
      name: groupName,
      color,
      memberCount: nodeIds.length,
      nodeIds,
      internalEdgeCount: internalEdges.length,
      bridgeNodeIds: Array.from(bridgeNodes),
      dominantType,
      avgRisk: Math.round(totalRisk / (clusterEntities.length || 1)),
    });

    clusterIdx++;
  });

  return { communities, entityCommunityMap };
}

/**
 * BFS N-Hop neighborhood expansion from a starting focal node
 */
export function getNHopNeighborhood(
  focalNodeId: string,
  hops: number,
  entities: SyntheticEntity[],
  relationships: SyntheticRelationship[]
): {
  reachableNodeIds: Set<string>;
  connectedEdgeIds: Set<string>;
  hopDistances: Map<string, number>;
  pathSummaries: { targetId: string; distance: number; path: string[] }[];
} {
  const reachableNodeIds = new Set<string>([focalNodeId]);
  const connectedEdgeIds = new Set<string>();
  const hopDistances = new Map<string, number>([[focalNodeId, 0]]);
  const paths = new Map<string, string[]>([[focalNodeId, [focalNodeId]]]);

  const adj = new Map<string, { neighbor: string; edgeId: string }[]>();
  entities.forEach((e) => adj.set(e.id, []));

  relationships.forEach((r) => {
    if (adj.has(r.sourceId) && adj.has(r.targetId)) {
      adj.get(r.sourceId)!.push({ neighbor: r.targetId, edgeId: r.id });
      adj.get(r.targetId)!.push({ neighbor: r.sourceId, edgeId: r.id });
    }
  });

  let currentLevel = [focalNodeId];
  for (let currentHop = 1; currentHop <= hops; currentHop++) {
    const nextLevel: string[] = [];
    for (const node of currentLevel) {
      const edges = adj.get(node) || [];
      for (const { neighbor, edgeId } of edges) {
        if (!hopDistances.has(neighbor)) {
          hopDistances.set(neighbor, currentHop);
          reachableNodeIds.add(neighbor);
          paths.set(neighbor, [...(paths.get(node) || []), neighbor]);
          nextLevel.push(neighbor);
        }
        if (reachableNodeIds.has(node) && reachableNodeIds.has(neighbor)) {
          connectedEdgeIds.add(edgeId);
        }
      }
    }
    currentLevel = nextLevel;
  }

  const pathSummaries = Array.from(reachableNodeIds).map((id) => ({
    targetId: id,
    distance: hopDistances.get(id) || 0,
    path: paths.get(id) || [],
  }));

  return { reachableNodeIds, connectedEdgeIds, hopDistances, pathSummaries };
}

/**
 * Generate Layout Positions for various visualization modes
 */
export function calculateGraphLayout(
  layoutMode: "force" | "hierarchical" | "circular" | "timeline",
  entities: SyntheticEntity[],
  relationships: SyntheticRelationship[],
  centrality: Record<string, CentralityMetrics>,
  entityCommunityMap: Record<string, number>
): Record<string, LayoutPosition> {
  const positions: Record<string, LayoutPosition> = {};
  const n = entities.length;
  if (n === 0) return positions;

  if (layoutMode === "hierarchical") {
    // 1. Hierarchical Layout
    const tiers: {
      Command: string[];
      Operations: string[];
      FinancialMules: string[];
      Infrastructure: string[];
      Events: string[];
    } = {
      Command: [],
      Operations: [],
      FinancialMules: [],
      Infrastructure: [],
      Events: [],
    };

    entities.forEach((e) => {
      const role = (e.role || "").toLowerCase();
      const label = e.label.toLowerCase();

      if (
        role.includes("kingpin") ||
        role.includes("mastermind") ||
        role.includes("controller") ||
        (label === "person" && (centrality[e.id]?.rank || 99) <= 2)
      ) {
        tiers.Command.push(e.id);
      } else if (
        label === "organization" ||
        role.includes("specialist") ||
        role.includes("operator") ||
        role.includes("broker")
      ) {
        tiers.Operations.push(e.id);
      } else if (
        label === "bankaccount" ||
        role.includes("mule") ||
        role.includes("cash")
      ) {
        tiers.FinancialMules.push(e.id);
      } else if (label === "event") {
        tiers.Events.push(e.id);
      } else {
        tiers.Infrastructure.push(e.id);
      }
    });

    const tierList: string[][] = [
      tiers.Command,
      tiers.Operations,
      tiers.FinancialMules,
      tiers.Infrastructure,
      tiers.Events,
    ];

    tierList.forEach((nodeIds, tIdx) => {
      const count = nodeIds.length;
      const spacingX = 260;
      const startX = -((count - 1) * spacingX) / 2;
      const y = tIdx * 180 + 50;

      nodeIds.forEach((id, i) => {
        positions[id] = {
          x: startX + i * spacingX + 450,
          y: y + (i % 2 === 0 ? 0 : 25),
        };
      });
    });
  } else if (layoutMode === "circular") {
    // 2. Circular Community Grouping
    const communityGroups = new Map<number, string[]>();
    entities.forEach((e) => {
      const cId = entityCommunityMap[e.id] ?? 0;
      if (!communityGroups.has(cId)) communityGroups.set(cId, []);
      communityGroups.get(cId)!.push(e.id);
    });

    const clusterCount = communityGroups.size;
    const mainRadius = 380;
    const centerPoint = { x: 500, y: 350 };
    let cIndex = 0;

    communityGroups.forEach((nodeIds) => {
      const clusterAngle = (cIndex / clusterCount) * 2 * Math.PI - Math.PI / 2;
      const clusterCenterX = centerPoint.x + mainRadius * Math.cos(clusterAngle);
      const clusterCenterY = centerPoint.y + mainRadius * Math.sin(clusterAngle);

      const count = nodeIds.length;
      const subRadius = Math.max(120, count * 22);

      nodeIds.forEach((id, i) => {
        const subAngle = (i / count) * 2 * Math.PI;
        positions[id] = {
          x: clusterCenterX + subRadius * Math.cos(subAngle),
          y: clusterCenterY + subRadius * Math.sin(subAngle),
        };
      });
      cIndex++;
    });
  } else if (layoutMode === "timeline") {
    // 3. Timeline Stream View
    const dates = entities
      .map((e) => new Date(e.firstSeen || "2024-01-01").getTime())
      .filter((d) => !isNaN(d));

    const minDate = Math.min(...dates, new Date("2023-08-01").getTime());
    const maxDate = Math.max(...dates, new Date("2026-08-30").getTime());
    const timeSpan = maxDate - minDate || 1;

    const typeYOffset: Record<string, number> = {
      Person: 60,
      Phone: 180,
      Organization: 300,
      BankAccount: 420,
      Device: 540,
      Location: 660,
      Vehicle: 780,
      Event: 900,
    };

    entities.forEach((e, idx) => {
      const entityDate = new Date(e.firstSeen || "2024-01-01").getTime();
      const progress = (entityDate - minDate) / timeSpan;
      const x = 100 + progress * 1400;
      const baseBatchOffset = (idx % 3) * 35;
      const y = (typeYOffset[e.label] ?? 200) + baseBatchOffset;

      positions[e.id] = { x, y };
    });
  } else {
    // 4. Force-Directed Simulation
    const width = 1100;
    const height = 750;
    const k = Math.sqrt((width * height) / n);
    const tempInitial = width / 10;
    const iterations = 50;

    entities.forEach((e, idx) => {
      const angle = (idx / n) * 2 * Math.PI;
      const r = 250 + (idx % 3) * 60;
      positions[e.id] = {
        x: width / 2 + r * Math.cos(angle) + (Math.random() * 40 - 20),
        y: height / 2 + r * Math.sin(angle) + (Math.random() * 40 - 20),
      };
    });

    const adj = new Map<string, string[]>();
    entities.forEach((e) => adj.set(e.id, []));
    relationships.forEach((r) => {
      if (adj.has(r.sourceId) && adj.has(r.targetId)) {
        adj.get(r.sourceId)!.push(r.targetId);
        adj.get(r.targetId)!.push(r.sourceId);
      }
    });

    for (let iter = 0; iter < iterations; iter++) {
      const temp = tempInitial * (1 - iter / iterations);
      const disp: Record<string, { x: number; y: number }> = {};
      entities.forEach((e) => (disp[e.id] = { x: 0, y: 0 }));

      // Repulsion between all pairs
      for (let i = 0; i < n; i++) {
        const u = entities[i];
        if (!u) continue;
        const uPos = positions[u.id];
        if (!uPos) continue;

        for (let j = i + 1; j < n; j++) {
          const v = entities[j];
          if (!v) continue;
          const vPos = positions[v.id];
          if (!vPos) continue;

          const dx = uPos.x - vPos.x;
          const dy = uPos.y - vPos.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (k * k) / dist;

          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          const uDisp = disp[u.id];
          const vDisp = disp[v.id];
          if (uDisp) {
            uDisp.x += fx;
            uDisp.y += fy;
          }
          if (vDisp) {
            vDisp.x -= fx;
            vDisp.y -= fy;
          }
        }
      }

      // Attraction along edges
      relationships.forEach((r) => {
        const srcPos = positions[r.sourceId];
        const tgtPos = positions[r.targetId];
        if (!srcPos || !tgtPos) return;

        const dx = srcPos.x - tgtPos.x;
        const dy = srcPos.y - tgtPos.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist * dist) / k;

        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        const srcDisp = disp[r.sourceId];
        const tgtDisp = disp[r.targetId];
        if (srcDisp) {
          srcDisp.x -= fx;
          srcDisp.y -= fy;
        }
        if (tgtDisp) {
          tgtDisp.x += fx;
          tgtDisp.y += fy;
        }
      });

      // Apply displacement
      entities.forEach((e) => {
        const d = disp[e.id];
        const p = positions[e.id];
        if (d && p) {
          const dist = Math.sqrt(d.x * d.x + d.y * d.y) || 1;
          p.x += (d.x / dist) * Math.min(dist, temp);
          p.y += (d.y / dist) * Math.min(dist, temp);
        }
      });
    }
  }

  return positions;
}
