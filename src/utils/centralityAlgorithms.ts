import type { SyntheticEntity, SyntheticRelationship } from "@/data/syntheticGraphData";

export interface CentralityScore {
  entityId: string;
  name: string;
  label: string;
  role?: string;
  riskScore: number;
  communityId: number;
  communityName: string;
  degree: number;
  inDegree: number;
  outDegree: number;
  normalizedDegree: number;
  betweenness: number;
  betweennessRank: number;
  closeness: number;
  closenessRank: number;
  pageRank: number;
  pageRankRank: number;
  overallRank: number;
  compositeScore: number;
  explanation: string;
}

export interface MetricDistribution {
  bins: { range: string; count: number; entityIds: string[] }[];
  mean: number;
  median: number;
  max: number;
  min: number;
}

/**
 * Advanced Centrality Algorithm Engine
 */
export function computeAdvancedCentralities(
  entities: SyntheticEntity[],
  relationships: SyntheticRelationship[]
): {
  scores: Record<string, CentralityScore>;
  sortedByDegree: CentralityScore[];
  sortedByBetweenness: CentralityScore[];
  sortedByCloseness: CentralityScore[];
  sortedByPageRank: CentralityScore[];
  distributions: {
    degree: MetricDistribution;
    betweenness: MetricDistribution;
    closeness: MetricDistribution;
    pageRank: MetricDistribution;
  };
} {
  const n = entities.length;
  const scores: Record<string, CentralityScore> = {};
  if (n === 0) {
    const emptyDist: MetricDistribution = { bins: [], mean: 0, median: 0, max: 0, min: 0 };
    return {
      scores: {},
      sortedByDegree: [],
      sortedByBetweenness: [],
      sortedByCloseness: [],
      sortedByPageRank: [],
      distributions: { degree: emptyDist, betweenness: emptyDist, closeness: emptyDist, pageRank: emptyDist },
    };
  }

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

  // 4. PageRank Centrality (Power iteration)
  const pageRankMap = new Map<string, number>();
  const damping = 0.85;
  entities.forEach((e) => pageRankMap.set(e.id, 1 / n));

  for (let iter = 0; iter < 30; iter++) {
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

  // Compile Initial Scores
  entities.forEach((e) => {
    const deg = degreeMap.get(e.id) || 0;
    const inDeg = inDegreeMap.get(e.id) || 0;
    const outDeg = outDegreeMap.get(e.id) || 0;
    const rawBetweenness = betweennessMap.get(e.id) || 0;
    const normBetweenness = Number(((rawBetweenness / normFactor) * 100).toFixed(2));
    const closeness = closenessMap.get(e.id) || 0;
    const pr = Number(((pageRankMap.get(e.id) || 0) * 100).toFixed(2));

    const compositeScore = deg * 0.3 + normBetweenness * 0.4 + pr * 0.3;

    let explanation = `Entity has ${deg} direct connections across network.`;
    if (normBetweenness > 20) {
      explanation = `Critical bridge entity funneling ${normBetweenness}% of all shortest inter-cluster communication paths.`;
    } else if (pr > 15) {
      explanation = `Authoritative syndicate controller with high PageRank authority score (${pr}%).`;
    }

    scores[e.id] = {
      entityId: e.id,
      name: e.name,
      label: e.label,
      role: e.role,
      riskScore: e.riskScore,
      communityId: e.communityId || 0,
      communityName: e.investigationGroup || "Syndicate Cell",
      degree: deg,
      inDegree: inDeg,
      outDegree: outDeg,
      normalizedDegree: Number((deg / (n - 1 || 1)).toFixed(2)),
      betweenness: normBetweenness,
      betweennessRank: 0,
      closeness,
      closenessRank: 0,
      pageRank: pr,
      pageRankRank: 0,
      overallRank: 0,
      compositeScore,
      explanation,
    };
  });

  const list = Object.values(scores);

  // Sorted Lists & Ranks
  const sortedByDegree = [...list].sort((a, b) => b.degree - a.degree);
  sortedByDegree.forEach((item, idx) => {
    const s = scores[item.entityId];
    if (s) s.normalizedDegree = Number((item.degree / (n - 1 || 1)).toFixed(2));
  });

  const sortedByBetweenness = [...list].sort((a, b) => b.betweenness - a.betweenness);
  sortedByBetweenness.forEach((item, idx) => {
    const s = scores[item.entityId];
    if (s) s.betweennessRank = idx + 1;
  });

  const sortedByCloseness = [...list].sort((a, b) => b.closeness - a.closeness);
  sortedByCloseness.forEach((item, idx) => {
    const s = scores[item.entityId];
    if (s) s.closenessRank = idx + 1;
  });

  const sortedByPageRank = [...list].sort((a, b) => b.pageRank - a.pageRank);
  sortedByPageRank.forEach((item, idx) => {
    const s = scores[item.entityId];
    if (s) s.pageRankRank = idx + 1;
  });

  const sortedOverall = [...list].sort((a, b) => b.compositeScore - a.compositeScore);
  sortedOverall.forEach((item, idx) => {
    const s = scores[item.entityId];
    if (s) s.overallRank = idx + 1;
  });

  // Calculate Distributions
  const buildDistribution = (values: { id: string; val: number }[], binCount = 5): MetricDistribution => {
    if (values.length === 0) return { bins: [], mean: 0, median: 0, max: 0, min: 0 };
    const nums = values.map((v) => v.val);
    const min = Math.min(...nums);
    const max = Math.max(...nums);
    const mean = Number((nums.reduce((acc, c) => acc + c, 0) / nums.length).toFixed(2));
    const sortedNums = [...nums].sort((a, b) => a - b);
    const median = sortedNums[Math.floor(sortedNums.length / 2)] || 0;

    const step = (max - min) / binCount || 1;
    const bins = Array.from({ length: binCount }, (_, i) => {
      const bMin = min + i * step;
      const bMax = bMin + step;
      const range = `${bMin.toFixed(1)} - ${bMax.toFixed(1)}`;
      const matches = values.filter((v) => (i === binCount - 1 ? v.val >= bMin && v.val <= bMax : v.val >= bMin && v.val < bMax));
      return {
        range,
        count: matches.length,
        entityIds: matches.map((m) => m.id),
      };
    });

    return { bins, mean, median, max, min };
  };

  const distributions = {
    degree: buildDistribution(list.map((s) => ({ id: s.entityId, val: s.degree }))),
    betweenness: buildDistribution(list.map((s) => ({ id: s.entityId, val: s.betweenness }))),
    closeness: buildDistribution(list.map((s) => ({ id: s.entityId, val: s.closeness }))),
    pageRank: buildDistribution(list.map((s) => ({ id: s.entityId, val: s.pageRank }))),
  };

  return {
    scores,
    sortedByDegree,
    sortedByBetweenness,
    sortedByCloseness,
    sortedByPageRank,
    distributions,
  };
}
