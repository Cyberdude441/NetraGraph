import React from "react";
import {
  Network,
  GitFork,
  PieChart,
  ShieldAlert,
  Flame,
  Activity,
  Share2,
  TrendingUp,
  Zap,
  Award,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { GlobalNetworkTopology } from "@/utils/networkMetrics";
import type { ModularityMetrics } from "@/utils/communityDetection";

interface AnalyticsDashboardProps {
  topology: GlobalNetworkTopology;
  modularity: ModularityMetrics;
  onNavigateTab: (tabId: string) => void;
}

export function AnalyticsDashboard({
  topology,
  modularity,
  onNavigateTab,
}: AnalyticsDashboardProps) {
  return (
    <div className="space-y-4 font-sans select-none">
      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
        {/* Network Density */}
        <div className="rounded border border-slate-800 bg-[#121820] p-3">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Network Density</span>
            <Activity className="size-3.5 text-sky-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">{topology.networkDensity}</div>
          <p className="text-[9px] text-slate-500 mt-0.5">
            Ratio of observed links to potential connections
          </p>
        </div>

        {/* Modularity Q-Score */}
        <div className="rounded border border-slate-800 bg-[#121820] p-3">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Modularity Q</span>
            <PieChart className="size-3.5 text-purple-400" />
          </div>
          <div className="text-xl font-bold text-purple-400">{modularity.modularityScore}</div>
          <p className="text-[9px] text-slate-500 mt-0.5">
            Strong cluster segregation ($Q &gt; 0.4$)
          </p>
        </div>

        {/* Network Diameter */}
        <div className="rounded border border-slate-800 bg-[#121820] p-3">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Syndicate Diameter</span>
            <GitFork className="size-3.5 text-amber-400" />
          </div>
          <div className="text-xl font-bold text-amber-400">{topology.networkDiameter} Hops</div>
          <p className="text-[9px] text-slate-500 mt-0.5">
            Max geodesic distance between any 2 nodes
          </p>
        </div>

        {/* High Threat Entities */}
        <div className="rounded border border-slate-800 bg-[#121820] p-3">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Critical Entities</span>
            <Flame className="size-3.5 text-red-400" />
          </div>
          <div className="text-xl font-bold text-red-400">{topology.criticalEntitiesCount} Nodes</div>
          <p className="text-[9px] text-slate-500 mt-0.5">
            Entities with Risk Score $\ge 85$
          </p>
        </div>
      </div>

      {/* Quick Launch Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Card 1: Centrality & Influence */}
        <div
          onClick={() => onNavigateTab("centrality")}
          className="rounded-lg border border-slate-800 bg-[#141A21] p-4 transition-all hover:border-sky-500 hover:bg-[#16202A] cursor-pointer"
        >
          <div className="flex items-center gap-2 mb-2">
            <Award className="size-4 text-sky-400" />
            <h3 className="font-bold text-slate-100 text-xs uppercase">
              Centrality & Kingpin Ranking
            </h3>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Algorithmic ranking across PageRank, Betweenness (Brandes), Degree, and Closeness reachability.
          </p>
        </div>

        {/* Card 2: Shortest Path Tracer */}
        <div
          onClick={() => onNavigateTab("shortest_path")}
          className="rounded-lg border border-slate-800 bg-[#141A21] p-4 transition-all hover:border-amber-500 hover:bg-[#1A1813] cursor-pointer"
        >
          <div className="flex items-center gap-2 mb-2">
            <Share2 className="size-4 text-amber-400" />
            <h3 className="font-bold text-slate-100 text-xs uppercase">
              Shortest Path & Intermediary Explorer
            </h3>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Trace multi-hop relationship chains between any two suspects to identify conduits and mules.
          </p>
        </div>

        {/* Card 3: Community & Bridge Analyzer */}
        <div
          onClick={() => onNavigateTab("communities")}
          className="rounded-lg border border-slate-800 bg-[#141A21] p-4 transition-all hover:border-purple-500 hover:bg-[#1A1320] cursor-pointer"
        >
          <div className="flex items-center gap-2 mb-2">
            <PieChart className="size-4 text-purple-400" />
            <h3 className="font-bold text-slate-100 text-xs uppercase">
              Community Modularity & Bridge Nodes
            </h3>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Detect hidden clusters, calculate density, and expose brokers funneling cross-border assets.
          </p>
        </div>
      </div>
    </div>
  );
}
