import type { SyntheticEntity, SyntheticRelationship } from "@/data/syntheticGraphData";

export interface PathStep {
  stepIndex: number;
  fromEntity: SyntheticEntity;
  toEntity: SyntheticEntity;
  relationship: SyntheticRelationship;
}

export interface ShortestPathResult {
  sourceEntityId: string;
  targetEntityId: string;
  found: boolean;
  hopCount: number;
  pathNodes: SyntheticEntity[];
  pathEdges: SyntheticRelationship[];
  steps: PathStep[];
  pathConfidence: number; // 0 to 100
  averageRisk: number;
  dominantModality: string;
  timeSpan: {
    start: string;
    end: string;
  };
  explanation: string;
}

/**
 * Multi-Path Dijkstra / BFS Shortest Path Tracer
 */
export function findShortestPath(
  sourceId: string,
  targetId: string,
  entities: SyntheticEntity[],
  relationships: SyntheticRelationship[]
): {
  primaryPath: ShortestPathResult | null;
  alternativePaths: ShortestPathResult[];
} {
  const entityMap = new Map(entities.map((e) => [e.id, e]));
  const src = entityMap.get(sourceId);
  const tgt = entityMap.get(targetId);

  if (!src || !tgt || sourceId === targetId) {
    return { primaryPath: null, alternativePaths: [] };
  }

  // Build adjacency list
  const adj = new Map<string, { neighborId: string; edge: SyntheticRelationship }[]>();
  entities.forEach((e) => adj.set(e.id, []));

  relationships.forEach((r) => {
    if (adj.has(r.sourceId) && adj.has(r.targetId)) {
      adj.get(r.sourceId)!.push({ neighborId: r.targetId, edge: r });
      adj.get(r.targetId)!.push({ neighborId: r.sourceId, edge: r });
    }
  });

  // BFS Queue for Shortest Path
  const queue: { nodeId: string; path: string[]; edges: SyntheticRelationship[] }[] = [
    { nodeId: sourceId, path: [sourceId], edges: [] },
  ];
  const visited = new Set<string>([sourceId]);
  const discoveredPaths: { path: string[]; edges: SyntheticRelationship[] }[] = [];

  while (queue.length > 0 && discoveredPaths.length < 3) {
    const current = queue.shift()!;

    if (current.nodeId === targetId) {
      discoveredPaths.push({ path: current.path, edges: current.edges });
      continue;
    }

    const neighbors = adj.get(current.nodeId) || [];
    for (const { neighborId, edge } of neighbors) {
      if (!current.path.includes(neighborId)) {
        if (!visited.has(neighborId) || neighborId === targetId) {
          visited.add(neighborId);
          queue.push({
            nodeId: neighborId,
            path: [...current.path, neighborId],
            edges: [...current.edges, edge],
          });
        }
      }
    }
  }

  if (discoveredPaths.length === 0) {
    return { primaryPath: null, alternativePaths: [] };
  }

  // Format Path Result Object
  const formatPath = (pNodes: string[], pEdges: SyntheticRelationship[]): ShortestPathResult => {
    const nodes = pNodes.map((id) => entityMap.get(id)!).filter(Boolean);
    const steps: PathStep[] = [];
    const relTypes: Record<string, number> = {};
    let totalConf = 0;
    let totalRisk = 0;

    for (let i = 0; i < pEdges.length; i++) {
      const edge = pEdges[i]!;
      const u = nodes[i]!;
      const v = nodes[i + 1]!;
      steps.push({
        stepIndex: i + 1,
        fromEntity: u,
        toEntity: v,
        relationship: edge,
      });

      relTypes[edge.type] = (relTypes[edge.type] || 0) + 1;
      totalConf += edge.confidence;
    }

    nodes.forEach((n) => (totalRisk += n.riskScore));

    const dominant =
      Object.entries(relTypes).sort((a, b) => b[1] - a[1])[0]?.[0] || "ASSOCIATION";

    const avgConf = Math.round((totalConf / (pEdges.length || 1)) * 100);
    const avgRisk = Math.round(totalRisk / (nodes.length || 1));

    const timestamps = pEdges
      .map((e) => new Date(e.timestamp).getTime())
      .filter((t) => !isNaN(t));
    const minT = timestamps.length > 0 ? new Date(Math.min(...timestamps)).toISOString().slice(0, 10) : "2024-01-01";
    const maxT = timestamps.length > 0 ? new Date(Math.max(...timestamps)).toISOString().slice(0, 10) : "2026-08-25";

    const intermediateNodes = nodes.slice(1, -1);
    const bridgeText =
      intermediateNodes.length > 0
        ? intermediateNodes.map((n) => `${n.name} (${n.label})`).join(" → ")
        : "Direct Link";

    return {
      sourceEntityId: sourceId,
      targetEntityId: targetId,
      found: true,
      hopCount: pEdges.length,
      pathNodes: nodes,
      pathEdges: pEdges,
      steps,
      pathConfidence: avgConf,
      averageRisk: avgRisk,
      dominantModality: dominant,
      timeSpan: { start: minT, end: maxT },
      explanation: `${nodes[0]?.name} reaches ${nodes[nodes.length - 1]?.name} in ${pEdges.length} hops via ${bridgeText}.`,
    };
  };

  const primaryPath = formatPath(discoveredPaths[0]!.path, discoveredPaths[0]!.edges);
  const alternativePaths = discoveredPaths.slice(1).map((p) => formatPath(p.path, p.edges));

  return { primaryPath, alternativePaths };
}
