import React, { useState } from "react";
import {
  Award,
  Share2,
  TrendingUp,
  Zap,
  Flame,
  Info,
  BarChart3,
  ChevronRight,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { cn } from "@/lib/utils";
import type { CentralityScore, MetricDistribution } from "@/utils/centralityAlgorithms";

interface CentralityPanelProps {
  scores: Record<string, CentralityScore>;
  sortedByPageRank: CentralityScore[];
  sortedByBetweenness: CentralityScore[];
  sortedByDegree: CentralityScore[];
  sortedByCloseness: CentralityScore[];
  distributions: {
    degree: MetricDistribution;
    betweenness: MetricDistribution;
    closeness: MetricDistribution;
    pageRank: MetricDistribution;
  };
  selectedEntityId: string | null;
  onSelectEntity: (id: string) => void;
}

type MetricMode = "pagerank" | "betweenness" | "degree" | "closeness";

export function CentralityPanel({
  scores,
  sortedByPageRank,
  sortedByBetweenness,
  sortedByDegree,
  sortedByCloseness,
  distributions,
  selectedEntityId,
  onSelectEntity,
}: CentralityPanelProps) {
  const [metricMode, setMetricMode] = useState<MetricMode>("pagerank");

  let activeList: CentralityScore[] = sortedByPageRank;
  let dist = distributions.pageRank;
  let metricTitle = "PageRank (Eigenvector Influence)";
  let metricDescription = "Identifies authoritative syndicate controllers and kingpins based on iterative link authority.";

  if (metricMode === "betweenness") {
    activeList = sortedByBetweenness;
    dist = distributions.betweenness;
    metricTitle = "Betweenness Centrality (Brandes Algorithm)";
    metricDescription = "Identifies critical hawala conduits and intermediaries that bridge otherwise disjoint communities.";
  } else if (metricMode === "degree") {
    activeList = sortedByDegree;
    dist = distributions.degree;
    metricTitle = "Degree Centrality (Connection Volume)";
    metricDescription = "Measures high-volume communication hubs, master PBX dispatchers, and frequent mule accounts.";
  } else if (metricMode === "closeness") {
    activeList = sortedByCloseness;
    dist = distributions.closeness;
    metricTitle = "Closeness Centrality (Geodesic Reachability)";
    metricDescription = "Measures how fast an entity can disseminate instructions or malware payloads to all nodes in the network.";
  }

  // Bar Chart Top 8 Data
  const chartData = activeList.slice(0, 8).map((s) => ({
    name: s.name.length > 14 ? s.name.slice(0, 12) + "..." : s.name,
    score:
      metricMode === "pagerank"
        ? s.pageRank
        : metricMode === "betweenness"
        ? s.betweenness
        : metricMode === "degree"
        ? s.degree
        : s.closeness,
    fullName: s.name,
    role: s.role,
    id: s.entityId,
  }));

  return (
    <div className="space-y-4 font-sans select-none">
      {/* Metric Mode Selector Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-[#0E1318] p-3 rounded-lg">
        <div className="flex items-center gap-2">
          <Award className="size-4 text-sky-400" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
            Select Centrality Algorithm:
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-1 rounded bg-[#161D24] p-1 border border-slate-800 font-mono text-xs">
          {[
            { id: "pagerank", label: "PageRank (Influence)", icon: Award },
            { id: "betweenness", label: "Betweenness (Bridges)", icon: Share2 },
            { id: "degree", label: "Degree (Connectivity)", icon: TrendingUp },
            { id: "closeness", label: "Closeness (Reach)", icon: Zap },
          ].map((m) => {
            const Icon = m.icon;
            const active = metricMode === m.id;
            return (
              <button
                key={m.id}
                onClick={() => setMetricMode(m.id as MetricMode)}
                className={cn(
                  "flex items-center gap-1.5 rounded px-3 py-1 font-bold transition-all cursor-pointer",
                  active
                    ? "bg-[#1E293B] text-sky-300 border border-sky-500/50 shadow-xs"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                <Icon className="size-3" />
                <span>{m.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Algorithm Overview & Histogram */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Left: Top 8 Bar Chart */}
        <div className="lg:col-span-2 rounded-lg border border-slate-800 bg-[#0E1318] p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="font-mono text-xs font-bold uppercase text-slate-100">
              Top Ranked Entities — {metricTitle}
            </h4>
            <span className="text-[10px] font-mono text-slate-500">
              Mean: {dist.mean} · Max: {dist.max}
            </span>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid stroke="#1E293B" strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="name"
                  stroke="#64748B"
                  fontSize={10}
                  fontFamily="Inter, sans-serif"
                  angle={-15}
                  textAnchor="end"
                />
                <YAxis stroke="#64748B" fontSize={10} fontFamily="monospace" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#11161B",
                    borderColor: "#334155",
                    borderRadius: "6px",
                    color: "#E2E8F0",
                    fontSize: "11px",
                    fontFamily: "monospace",
                  }}
                />
                <Bar
                  dataKey="score"
                  fill="#38BDF8"
                  radius={[4, 4, 0, 0]}
                  onClick={(data: any) => data?.id && onSelectEntity(data.id)}
                  cursor="pointer"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Distribution & Algorithm Insight */}
        <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-4 space-y-3 flex flex-col justify-between">
          <div>
            <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-sky-400 block mb-1">
              Metric Explainability
            </span>
            <h4 className="font-bold text-slate-100 text-xs mb-1.5">{metricTitle}</h4>
            <p className="text-[11px] text-slate-400 leading-relaxed">{metricDescription}</p>
          </div>

          <div className="rounded border border-slate-800 bg-[#121820] p-3 space-y-1.5 font-mono text-[11px]">
            <span className="text-[9px] uppercase text-slate-500 font-bold block">
              Population Statistics
            </span>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Total Analyzed:</span>
              <strong className="text-slate-200">{Object.keys(scores).length} Nodes</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Highest Score:</span>
              <strong className="text-sky-300">{dist.max}</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Median Threshold:</span>
              <strong className="text-slate-300">{dist.median}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Full Centrality Ranking Table */}
      <div className="rounded-lg border border-slate-800 bg-[#0E1318] overflow-hidden">
        <div className="border-b border-slate-800 bg-[#121820] px-4 py-2.5 flex items-center justify-between">
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
            Centrality Intelligence Leaderboard ({activeList.length} Ranked Profiles)
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            Click row to center focus in intelligence canvas
          </span>
        </div>

        <div className="overflow-x-auto max-h-72 custom-scrollbar">
          <table className="w-full text-left font-mono text-[11px]">
            <thead className="border-b border-slate-800 bg-[#141A21] text-slate-400 uppercase text-[9px] sticky top-0">
              <tr>
                <th className="px-3 py-2">Rank</th>
                <th className="px-3 py-2">Entity Name</th>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2 text-right">Metric Score</th>
                <th className="px-3 py-2">Syndicate Group</th>
                <th className="px-3 py-2 text-center">Threat Level</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {activeList.map((item, idx) => {
                const isSelected = selectedEntityId === item.entityId;
                const risk = item.riskScore;

                let scoreVal = `${item.pageRank}%`;
                if (metricMode === "betweenness") scoreVal = `${item.betweenness}%`;
                else if (metricMode === "degree") scoreVal = `${item.degree} links`;
                else if (metricMode === "closeness") scoreVal = `${item.closeness}`;

                return (
                  <tr
                    key={item.entityId}
                    onClick={() => onSelectEntity(item.entityId)}
                    className={cn(
                      "transition-colors cursor-pointer",
                      isSelected
                        ? "bg-[#172330] text-sky-200"
                        : "hover:bg-[#121820] text-slate-300"
                    )}
                  >
                    <td className="px-3 py-2 font-bold text-amber-400">#{idx + 1}</td>
                    <td className="px-3 py-2 font-bold text-slate-100">
                      {item.name} <span className="text-[9px] text-slate-500 font-normal">({item.entityId})</span>
                    </td>
                    <td className="px-3 py-2 text-slate-400">{item.label}</td>
                    <td className="px-3 py-2 text-right font-bold text-sky-400">{scoreVal}</td>
                    <td className="px-3 py-2 text-slate-300 truncate max-w-[180px]">{item.communityName}</td>
                    <td className="px-3 py-2 text-center">
                      <span
                        className={cn(
                          "rounded px-2 py-0.5 text-[9px] font-bold",
                          risk >= 85
                            ? "bg-red-950/60 text-red-300 border border-red-500/50"
                            : risk >= 70
                            ? "bg-amber-950/60 text-amber-300 border border-amber-500/50"
                            : "bg-slate-800 text-slate-400"
                        )}
                      >
                        {risk >= 85 ? "CRITICAL" : risk >= 70 ? "HIGH" : "MODERATE"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
