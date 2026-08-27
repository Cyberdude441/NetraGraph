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
      {/* 4 Main Summary KPI Cards */}
      <div className="grid grid-cols-2 2xl:grid-cols-4 gap-3 text-xs">
        {/* Network Density */}
        <div className="rounded-md border border-[#E2E8F0] bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between text-[#64748B] mb-1.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#64748B]">Network Density</span>
            <span className="p-1 rounded bg-emerald-50 text-[#16A34A]">
              <Activity className="size-4" />
            </span>
          </div>
          <div className="text-2xl font-bold text-[#0F172A]">{topology.networkDensity || "0.09"}</div>
          <p className="text-xs text-[#64748B] mt-1">
            Observed links vs potential connections
          </p>
        </div>

        {/* Community Groups */}
        <div className="rounded-md border border-[#E2E8F0] bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between text-[#64748B] mb-1.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#64748B]">Community Groups</span>
            <span className="p-1 rounded bg-emerald-50 text-[#047857]">
              <PieChart className="size-4" />
            </span>
          </div>
          <div className="text-2xl font-bold text-[#047857]">{modularity.communityCount || 4} Clusters</div>
          <p className="text-xs text-[#64748B] mt-1">
            Separated syndicates & cell groups
          </p>
        </div>

        {/* Critical Entities */}
        <div className="rounded-md border border-[#E2E8F0] bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between text-[#64748B] mb-1.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#64748B]">Critical Entities</span>
            <span className="p-1 rounded bg-red-50 text-[#DC2626]">
              <Flame className="size-4" />
            </span>
          </div>
          <div className="text-2xl font-bold text-[#DC2626]">{topology.criticalEntitiesCount || 19} Suspects</div>
          <p className="text-xs text-[#64748B] mt-1">
            Entities with Risk Score &ge; 85
          </p>
        </div>

        {/* Maximum Distance */}
        <div className="rounded-md border border-[#E2E8F0] bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between text-[#64748B] mb-1.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#64748B]">Maximum Distance</span>
            <span className="p-1 rounded bg-amber-50 text-[#F59E0B]">
              <GitFork className="size-4" />
            </span>
          </div>
          <div className="text-2xl font-bold text-[#F59E0B]">{topology.networkDiameter || 4} Hops</div>
          <p className="text-xs text-[#64748B] mt-1">
            Max separation between any 2 nodes
          </p>
        </div>
      </div>

      {/* Quick Launch Cards */}
      <div className="grid grid-cols-1 2xl:grid-cols-3 gap-3">
        {/* Card 1: Influence Ranking */}
        <div
          onClick={() => onNavigateTab("centrality")}
          className="rounded-md border border-[#E2E8F0] bg-white p-4 transition-all hover:border-[#16A34A] hover:bg-[#F8FAFC] cursor-pointer shadow-xs"
        >
          <div className="flex items-center gap-2 mb-2">
            <Award className="size-4 text-[#16A34A]" />
            <h3 className="font-bold text-[#0F172A] text-xs">
              Influence Ranking
            </h3>
          </div>
          <p className="text-xs text-[#64748B] leading-relaxed">
            Algorithmic ranking across PageRank, Bridge Betweenness, and reachability to identify kingpins.
          </p>
        </div>

        {/* Card 2: Shortest Path Tracer */}
        <div
          onClick={() => onNavigateTab("shortest_path")}
          className="rounded-md border border-[#E2E8F0] bg-white p-4 transition-all hover:border-[#047857] hover:bg-[#F8FAFC] cursor-pointer shadow-xs"
        >
          <div className="flex items-center gap-2 mb-2">
            <Share2 className="size-4 text-[#047857]" />
            <h3 className="font-bold text-[#0F172A] text-xs">
              Connection Path Tracer
            </h3>
          </div>
          <p className="text-xs text-[#64748B] leading-relaxed">
            Trace multi-hop relationship chains between any two suspects to identify conduits and mules.
          </p>
        </div>

        {/* Card 3: Community & Bridge Analyzer */}
        <div
          onClick={() => onNavigateTab("communities")}
          className="rounded-md border border-[#E2E8F0] bg-white p-4 transition-all hover:border-[#9333EA] hover:bg-[#F8FAFC] cursor-pointer shadow-xs"
        >
          <div className="flex items-center gap-2 mb-2">
            <PieChart className="size-4 text-[#9333EA]" />
            <h3 className="font-bold text-[#0F172A] text-xs">
              Criminal Cell Groups
            </h3>
          </div>
          <p className="text-xs text-[#64748B] leading-relaxed">
            Detect hidden clusters, calculate density, and expose bridge brokers funneling cross-border assets.
          </p>
        </div>
      </div>
    </div>
  );
}
