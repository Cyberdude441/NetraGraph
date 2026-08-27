import React from "react";
import { TrendingUp, Users, GitFork, ArrowRight, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import type { NetworkGrowthPattern } from "@/utils/patternAnalysis";

interface NetworkGrowthAnalyzerProps {
  growth: NetworkGrowthPattern;
}

export function NetworkGrowthAnalyzer({ growth }: NetworkGrowthAnalyzerProps) {
  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-[#E2E8F0] pb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="size-4 text-emerald-400" />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-900">
              Syndicate Network Expansion & Link Surge
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              Cluster <strong>{growth.communityName}</strong> gained +{growth.netNewConnections} relationships in {growth.timeWindowDays} days (+{growth.growthRatePercentage}% growth).
            </p>
          </div>
        </div>

        <span className="rounded bg-emerald-950/60 border border-emerald-800 px-2.5 py-1 text-xs font-mono font-bold text-emerald-300">
          +{growth.growthRatePercentage}% Expansion Rate
        </span>
      </div>

      {/* Before / After Comparison Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
        <div className="rounded border border-[#E2E8F0] bg-white p-3 space-y-2">
          <span className="text-[10px] uppercase font-bold text-slate-400 block">
            Baseline Community Size
          </span>
          <div className="text-xl font-bold text-slate-800">
            {growth.priorSize} Entities
          </div>
          <p className="text-[10px] text-slate-500 font-sans">
            Stable historical cluster size prior to current surge window.
          </p>
        </div>

        <div className="rounded border border-emerald-900/50 bg-[#102018] p-3 space-y-2">
          <span className="text-[10px] uppercase font-bold text-emerald-400 block">
            Current Expanded Topology
          </span>
          <div className="text-xl font-bold text-emerald-300">
            {growth.currentSize} Entities (+{growth.netNewConnections} Net New)
          </div>
          <p className="text-[10px] text-slate-400 font-sans">
            Rapid assimilation of external mule handlers and SIM suppliers.
          </p>
        </div>
      </div>

      {/* Newly Activated Bridge Nodes */}
      <div className="rounded border border-[#E2E8F0] bg-white p-3 space-y-2">
        <span className="text-[10px] font-mono uppercase font-bold text-amber-400 block flex items-center gap-1.5">
          <GitFork className="size-3.5" /> Newly Formed Inter-Cluster Bridge Nodes:
        </span>
        <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
          {growth.newBridgeNodes.map((b) => (
            <span
              key={b.id}
              className="rounded bg-[#F8FAFC] px-2 py-1 text-slate-800 border border-[#E2E8F0] font-bold"
            >
              {b.name} <span className="text-slate-500 font-normal">({b.id})</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
