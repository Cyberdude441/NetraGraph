import React, { useState } from "react";
import {
  TrendingUp,
  Award,
  Share2,
  Zap,
  Target,
  ChevronRight,
  ShieldAlert,
  Flame,
  ArrowUpRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { SyntheticEntity } from "@/data/syntheticGraphData";
import type { CentralityMetrics } from "@/utils/graphAlgorithms";

interface CentralityPanelProps {
  entities: SyntheticEntity[];
  centrality: Record<string, CentralityMetrics>;
  focalNodeId: string;
  onSelectEntity: (id: string) => void;
}

type CentralityTab = "pagerank" | "betweenness" | "degree" | "closeness";

export function CentralityPanel({
  entities,
  centrality,
  focalNodeId,
  onSelectEntity,
}: CentralityPanelProps) {
  const [activeTab, setActiveTab] = useState<CentralityTab>("pagerank");

  const tabs: { id: CentralityTab; label: string; icon: React.ElementType; desc: string }[] = [
    {
      id: "pagerank",
      label: "Influence (PageRank)",
      icon: Award,
      desc: "Key syndicates & kingpins",
    },
    {
      id: "betweenness",
      label: "Bridge (Betweenness)",
      icon: Share2,
      desc: "Hawala conduits & intermediaries",
    },
    {
      id: "degree",
      label: "Connectivity (Degree)",
      icon: TrendingUp,
      desc: "High volume hubs",
    },
    {
      id: "closeness",
      label: "Dissemination (Closeness)",
      icon: Zap,
      desc: "Fast broadcast nodes",
    },
  ];

  // Sort entities by active metric
  const sortedEntities = [...entities].sort((a, b) => {
    const ma = centrality[a.id];
    const mb = centrality[b.id];
    if (!ma || !mb) return 0;

    if (activeTab === "pagerank") return mb.pageRank - ma.pageRank;
    if (activeTab === "betweenness") return mb.betweenness - ma.betweenness;
    if (activeTab === "degree") return mb.degree - ma.degree;
    return mb.closeness - ma.closeness;
  });

  return (
    <div className="flex flex-col h-full bg-white border-t border-[#E2E8F0] text-xs select-none">
      {/* Tab Navigation Header */}
      <div className="flex items-center justify-between border-b border-[#E2E8F0] bg-[#F8FAFC] px-4 py-2">
        <div className="flex items-center gap-2">
          <TrendingUp className="size-4 text-emerald-400" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-900">
            Network Centrality & Influence Rankings
          </span>
        </div>

        {/* Tab Buttons */}
        <div className="flex items-center gap-1 rounded bg-[#F8FAFC] p-0.5 border border-[#E2E8F0]">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex items-center gap-1.5 rounded px-2.5 py-1 font-mono text-[10px] font-bold transition-all cursor-pointer",
                  active
                    ? "bg-emerald-100 text-emerald-300 border border-emerald-500/40 shadow-xs"
                    : "text-slate-400 hover:text-slate-800"
                )}
                title={tab.desc}
              >
                <Icon className="size-3" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Leaderboard Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2.5 p-3 overflow-y-auto max-h-48 custom-scrollbar">
        {sortedEntities.slice(0, 8).map((entity, idx) => {
          const metrics = centrality[entity.id] || {
            degree: 0,
            betweenness: 0,
            closeness: 0,
            pageRank: 0,
            rank: 99,
          };
          const isSelected = focalNodeId === entity.id;

          let scoreDisplay = "";
          let scoreLabel = "";
          if (activeTab === "pagerank") {
            scoreDisplay = `${metrics.pageRank}%`;
            scoreLabel = "PageRank Authority";
          } else if (activeTab === "betweenness") {
            scoreDisplay = `${metrics.betweenness}%`;
            scoreLabel = "Intermediary Bridge";
          } else if (activeTab === "degree") {
            scoreDisplay = `${metrics.degree} Links`;
            scoreLabel = "Total Degrees";
          } else {
            scoreDisplay = `${metrics.closeness}`;
            scoreLabel = "Closeness Index";
          }

          return (
            <div
              key={entity.id}
              onClick={() => onSelectEntity(entity.id)}
              className={cn(
                "flex items-center justify-between gap-2.5 rounded border p-2.5 transition-all cursor-pointer hover:border-emerald-500",
                isSelected
                  ? "border-emerald-500/80 bg-emerald-50 shadow-md ring-1 ring-emerald-400/40"
                  : "border-[#E2E8F0] bg-white hover:bg-[#F8FAFC]"
              )}
            >
              {/* Rank Badge & Identity */}
              <div className="flex items-center gap-2.5 min-w-0">
                <span
                  className={cn(
                    "flex size-6 shrink-0 items-center justify-center rounded font-mono text-[10px] font-bold",
                    idx === 0
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/50"
                      : idx === 1
                      ? "bg-slate-700 text-slate-800 border border-slate-600"
                      : idx === 2
                      ? "bg-amber-900/30 text-amber-400 border border-amber-800"
                      : "bg-[#1A232E] text-slate-400 border border-[#E2E8F0]"
                  )}
                >
                  #{idx + 1}
                </span>

                <div className="min-w-0">
                  <div className="font-semibold text-slate-900 truncate text-[11px]">
                    {entity.name}
                  </div>
                  <div className="text-[9px] font-mono text-slate-400 truncate">
                    {entity.role || entity.label}
                  </div>
                </div>
              </div>

              {/* Metric Value */}
              <div className="text-right shrink-0">
                <div className="font-mono text-xs font-bold text-emerald-400">
                  {scoreDisplay}
                </div>
                <div className="text-[8px] font-mono text-slate-500">
                  {scoreLabel}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
