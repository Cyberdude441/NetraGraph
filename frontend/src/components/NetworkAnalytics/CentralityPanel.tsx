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
  let metricTitle = "Influential Key Suspects";
  let metricDescription = "Identifies commanding figures and controllers who have the highest indirect influence across the criminal syndicate.";

  if (metricMode === "betweenness") {
    activeList = sortedByBetweenness;
    dist = distributions.betweenness;
    metricTitle = "Important Network Bridges";
    metricDescription = "Identifies key couriers and intermediaries who link separate cells or coordinate transfers between groups.";
  } else if (metricMode === "degree") {
    activeList = sortedByDegree;
    dist = distributions.degree;
    metricTitle = "Most Connected Entities";
    metricDescription = "Measures high-volume communication hubs, frequent call-dispatchers, and accounts with the highest direct contacts.";
  } else if (metricMode === "closeness") {
    activeList = sortedByCloseness;
    dist = distributions.closeness;
    metricTitle = "Fast Information Spreaders";
    metricDescription = "Identifies actors positioned to rapidly relay alerts, OTP triggers, or instructions throughout the network.";
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
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#D9E2EC] bg-white p-3.5 rounded-md shadow-xs">
        <div className="flex items-center gap-2">
          <Award className="size-4 text-[#065F46]" />
          <span className="text-xs font-bold text-[#0F172A]">
            Insight Metric:
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-1 rounded-md bg-[#F1F5F9] p-1 border border-[#D9E2EC] text-xs">
          {[
            { id: "pagerank", label: "Influential Key Suspects", icon: Award },
            { id: "betweenness", label: "Important Network Bridges", icon: Share2 },
            { id: "degree", label: "Most Connected Entities", icon: TrendingUp },
            { id: "closeness", label: "Fast Information Spreaders", icon: Zap },
          ].map((m) => {
            const Icon = m.icon;
            const active = metricMode === m.id;
            return (
              <button
                key={m.id}
                onClick={() => setMetricMode(m.id as MetricMode)}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-semibold transition-all cursor-pointer",
                  active
                    ? "bg-[#065F46] text-white shadow-xs"
                    : "text-[#475569] hover:text-[#0F172A]"
                )}
              >
                <Icon className="size-3.5" />
                <span>{m.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Algorithm Overview & Histogram */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5">
        {/* Left: Top 8 Bar Chart */}
        <div className="lg:col-span-2 rounded-md border border-[#D9E2EC] bg-white p-4 space-y-3 shadow-xs">
          <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2.5">
            <h4 className="text-xs font-bold text-[#0F172A]">
              Top Ranked Targets — {metricTitle}
            </h4>
            <span className="text-xs text-[#64748B]">
              Average: {dist.mean} · Peak: {dist.max}
            </span>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid stroke="#E2E8F0" strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="name"
                  stroke="#64748B"
                  fontSize={11}
                  fontFamily="Inter, sans-serif"
                  angle={-15}
                  textAnchor="end"
                />
                <YAxis stroke="#64748B" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#FFFFFF",
                    borderColor: "#CBD5E1",
                    borderRadius: "6px",
                    color: "#0F172A",
                    fontSize: "12px",
                    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                  }}
                />
                <Bar
                  dataKey="score"
                  fill="#065F46"
                  radius={[4, 4, 0, 0]}
                  onClick={(data: any) => data?.id && onSelectEntity(data.id)}
                  cursor="pointer"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Distribution & Algorithm Insight */}
        <div className="rounded-md border border-[#D9E2EC] bg-white p-4 space-y-3 flex flex-col justify-between shadow-xs">
          <div>
            <span className="text-xs font-bold text-[#065F46] block mb-1">
              Plain-Language Interpretation
            </span>
            <h4 className="font-bold text-[#0F172A] text-sm mb-1.5">{metricTitle}</h4>
            <p className="text-xs text-[#475569] leading-relaxed">{metricDescription}</p>
          </div>

          <div className="rounded-md border border-[#D9E2EC] bg-[#F8FAFC] p-3 space-y-1.5 text-xs">
            <span className="text-xs uppercase text-[#64748B] font-bold block">
              Analysis Summary
            </span>
            <div className="flex items-center justify-between">
              <span className="text-[#64748B]">Total Entities Evaluated:</span>
              <strong className="text-[#0F172A]">{Object.keys(scores).length} entities</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#64748B]">Highest Score:</span>
              <strong className="text-[#065F46]">{dist.max}</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#64748B]">Median Value:</span>
              <strong className="text-[#0F172A]">{dist.median}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Full Centrality Ranking Table */}
      <div className="rounded-md border border-[#D9E2EC] bg-white overflow-hidden shadow-xs">
        <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] px-4 py-2.5 flex items-center justify-between">
          <span className="text-xs font-bold text-[#0F172A]">
            Ranked Target Leaderboard ({activeList.length} Entities)
          </span>
          <span className="text-xs text-[#64748B]">
            Click any row to view full details
          </span>
        </div>

        <div className="overflow-x-auto max-h-72">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-[#E2E8F0] bg-[#F8FAFC] text-[#64748B] text-[11px] font-semibold sticky top-0">
              <tr>
                <th className="px-3.5 py-2">Rank</th>
                <th className="px-3.5 py-2">Entity Name</th>
                <th className="px-3.5 py-2">Category</th>
                <th className="px-3.5 py-2 text-right">Score</th>
                <th className="px-3.5 py-2">Syndicate Group</th>
                <th className="px-3.5 py-2 text-center">Threat Level</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E8F0] text-[#0F172A]">
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
                        ? "bg-emerald-50 text-[#065F46]"
                        : "hover:bg-[#F8FAFC]"
                    )}
                  >
                    <td className="px-3.5 py-2 font-bold text-[#065F46]">#{idx + 1}</td>
                    <td className="px-3.5 py-2 font-bold text-[#0F172A]">
                      {item.name} <span className="text-xs text-[#64748B] font-normal font-mono">({item.entityId})</span>
                    </td>
                    <td className="px-3.5 py-2 text-[#64748B]">{item.label}</td>
                    <td className="px-3.5 py-2 text-right font-bold text-[#065F46]">{scoreVal}</td>
                    <td className="px-3.5 py-2 text-[#475569] truncate max-w-[180px]">{item.communityName}</td>
                    <td className="px-3.5 py-2 text-center">
                      <span
                        className={cn(
                          "rounded-md px-2 py-0.5 text-xs font-semibold",
                          risk >= 85
                            ? "bg-red-50 text-[#DC3545] border border-red-200"
                            : risk >= 70
                            ? "bg-amber-50 text-[#F59E0B] border border-amber-200"
                            : "bg-slate-100 text-[#475569]"
                        )}
                      >
                        {risk >= 85 ? "Critical" : risk >= 70 ? "High" : "Moderate"}
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
