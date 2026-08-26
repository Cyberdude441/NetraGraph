import { createFileRoute, useNavigate } from "@tanstack/react-router";
import React, { useState, useMemo } from "react";
import {
  TrendingUp,
  Award,
  Share2,
  PieChart,
  GitFork,
  Flame,
  Clock,
  Layers,
  Filter,
  ShieldAlert,
  ShieldCheck,
  Zap,
  Activity,
  BarChart3,
} from "lucide-react";
import { toast } from "sonner";

import { AppShell } from "@/components/AppShell";
import { AnalyticsDashboard } from "@/components/NetworkAnalytics/AnalyticsDashboard";
import { CentralityPanel } from "@/components/NetworkAnalytics/CentralityPanel";
import { CommunityDetection } from "@/components/NetworkAnalytics/CommunityDetection";
import { ShortestPathTracer } from "@/components/NetworkAnalytics/ShortestPathTracer";
import { BridgeAnalyzer } from "@/components/NetworkAnalytics/BridgeAnalyzer";
import { RiskHeatmap } from "@/components/NetworkAnalytics/RiskHeatmap";
import { NetworkEvolution } from "@/components/NetworkAnalytics/NetworkEvolution";
import { ExplainabilityPanel } from "@/components/NetworkAnalytics/ExplainabilityPanel";

import {
  SYNTHETIC_ENTITIES,
  SYNTHETIC_RELATIONSHIPS,
  type SyntheticEntity,
  type SyntheticRelationship,
} from "@/data/syntheticGraphData";
import { computeAdvancedCentralities } from "@/utils/centralityAlgorithms";
import { analyzeCommunitiesAndModularity } from "@/utils/communityDetection";
import {
  calculateNetworkTopology,
  calculateRiskHeatmap,
} from "@/utils/networkMetrics";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/analytics")({
  head: () => ({
    meta: [
      { title: "Network Analytics & Graph Algorithms — NetraGraph AI" },
      {
        name: "description",
        content:
          "Advanced graph intelligence analytics: Centrality rankings, Louvain modularity clustering, shortest path tracing, bridge node discovery, and explainable AI insights.",
      },
    ],
  }),
  component: NetworkAnalyticsPage,
});

type AnalyticsTab =
  | "dashboard"
  | "centrality"
  | "communities"
  | "shortest_path"
  | "bridges"
  | "heatmap"
  | "evolution";

function NetworkAnalyticsPage() {
  const navigate = useNavigate();

  // Active Dataset State
  const [entities] = useState<SyntheticEntity[]>(SYNTHETIC_ENTITIES);
  const [relationships] = useState<SyntheticRelationship[]>(SYNTHETIC_RELATIONSHIPS);

  // Filters State
  const [selectedGroup, setSelectedGroup] = useState<string>("ALL");
  const [minRiskScore, setMinRiskScore] = useState<number>(0);
  const [selectedEntityTypes, setSelectedEntityTypes] = useState<Set<string>>(
    new Set(["Person", "Phone", "Location", "Vehicle", "Organization", "BankAccount", "Device", "Event"])
  );

  // Navigation & Selection
  const [activeTab, setActiveTab] = useState<AnalyticsTab>("dashboard");
  const [selectedEntityId, setSelectedEntityId] = useState<string>("ENT-P-01");
  const [selectedCommunityId, setSelectedCommunityId] = useState<number | null>(null);

  // Filtered dataset based on left-panel filters
  const filteredEntities = useMemo(() => {
    return entities.filter((e) => {
      if (selectedGroup !== "ALL" && e.investigationGroup !== selectedGroup) return false;
      if (e.riskScore < minRiskScore) return false;
      if (!selectedEntityTypes.has(e.label)) return false;
      return true;
    });
  }, [entities, selectedGroup, minRiskScore, selectedEntityTypes]);

  const validEntityIds = useMemo(() => new Set(filteredEntities.map((e) => e.id)), [filteredEntities]);

  const filteredRelationships = useMemo(() => {
    return relationships.filter(
      (r) => validEntityIds.has(r.sourceId) && validEntityIds.has(r.targetId)
    );
  }, [relationships, validEntityIds]);

  // Algorithmic Calculations
  const {
    scores: centralityScores,
    sortedByDegree,
    sortedByBetweenness,
    sortedByCloseness,
    sortedByPageRank,
    distributions,
  } = useMemo(() => {
    return computeAdvancedCentralities(filteredEntities, filteredRelationships);
  }, [filteredEntities, filteredRelationships]);

  const { communities, modularity } = useMemo(() => {
    return analyzeCommunitiesAndModularity(filteredEntities, filteredRelationships);
  }, [filteredEntities, filteredRelationships]);

  const topology = useMemo(() => {
    return calculateNetworkTopology(filteredEntities, filteredRelationships);
  }, [filteredEntities, filteredRelationships]);

  const riskZones = useMemo(() => {
    return calculateRiskHeatmap(filteredEntities);
  }, [filteredEntities]);

  const selectedEntityScore = centralityScores[selectedEntityId] || sortedByPageRank[0] || null;

  const toggleEntityType = (type: string) => {
    setSelectedEntityTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        if (next.size > 1) next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  const groupOptions = useMemo(() => {
    return Array.from(new Set(entities.map((e) => e.investigationGroup)));
  }, [entities]);

  return (
    <AppShell
      title="Network Analytics & Graph Algorithms"
      subtitle="Decision-Support Intelligence: Centrality Metrics, Community Detection, Shortest Paths & Bridge Analysis"
    >
      <div className="flex flex-col h-[calc(100vh-130px)] rounded border border-slate-800 bg-[#0B0F14] shadow-2xl overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP ANALYTICS NAVIGATION & TAB SELECTOR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-[#0E1318] px-4 py-2 z-20">
          {/* Main Tab Controls */}
          <div className="flex items-center gap-1 font-mono text-xs overflow-x-auto custom-scrollbar">
            {[
              { id: "dashboard", label: "Overview", icon: Activity },
              { id: "centrality", label: "Centrality Rankings", icon: Award },
              { id: "communities", label: "Community Clusters", icon: PieChart },
              { id: "shortest_path", label: "Shortest Path Tracer", icon: Share2 },
              { id: "bridges", label: "Bridge Analyzer", icon: GitFork },
              { id: "heatmap", label: "Threat Heatmap", icon: Flame },
              { id: "evolution", label: "Network Evolution", icon: Clock },
            ].map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as AnalyticsTab)}
                  className={cn(
                    "flex items-center gap-1.5 rounded px-2.5 py-1 font-bold transition-all cursor-pointer whitespace-nowrap",
                    active
                      ? "bg-[#1E293B] text-sky-400 border border-sky-500/40 shadow-xs"
                      : "text-slate-400 hover:text-slate-200"
                  )}
                >
                  <Icon className="size-3" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate({ to: "/network" })}
              className="flex items-center gap-1 rounded border border-sky-500/50 bg-sky-950/40 px-2.5 py-1 text-xs font-mono font-semibold text-sky-300 hover:bg-sky-900/50 transition-colors cursor-pointer"
            >
              <Share2 className="size-3" />
              <span>Explore on Graph</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. THREE-PANEL ANALYTICAL WORKSPACE
           ========================================================================= */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* LEFT PANEL: Analytics Controls */}
          <aside className="w-72 border-r border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-slate-800 bg-[#141A21] px-4 py-3">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 flex items-center gap-1.5">
                <Filter className="size-3.5 text-sky-400" />
                Analytics Controls
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4 custom-scrollbar text-xs">
              {/* Syndicate Group Filter */}
              <div className="rounded border border-slate-800 bg-[#121820] p-2.5 space-y-1.5">
                <label className="text-[10px] font-mono uppercase font-bold text-slate-400 block">
                  Syndicate Cluster Filter
                </label>
                <select
                  value={selectedGroup}
                  onChange={(e) => setSelectedGroup(e.target.value)}
                  className="w-full rounded border border-slate-800 bg-[#161D24] px-2 py-1 text-xs text-sky-300 font-mono outline-none cursor-pointer"
                >
                  <option value="ALL">All Network Clusters</option>
                  {groupOptions.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
              </div>

              {/* Entity Type Matrix */}
              <div className="rounded border border-slate-800 bg-[#121820] p-2.5 space-y-1.5">
                <label className="text-[10px] font-mono uppercase font-bold text-slate-400 block">
                  Entity Scope Filter
                </label>
                <div className="grid grid-cols-2 gap-1 font-mono text-[10px]">
                  {["Person", "Phone", "Location", "Vehicle", "Organization", "BankAccount", "Device", "Event"].map(
                    (type) => {
                      const active = selectedEntityTypes.has(type);
                      return (
                        <button
                          key={type}
                          onClick={() => toggleEntityType(type)}
                          className={cn(
                            "rounded border px-1.5 py-0.5 text-left transition-all cursor-pointer truncate",
                            active
                              ? "border-sky-500/50 bg-[#1A2634] text-sky-200"
                              : "border-slate-800 bg-[#141A21] text-slate-500"
                          )}
                        >
                          {type}
                        </button>
                      );
                    }
                  )}
                </div>
              </div>

              {/* Min Risk Slider */}
              <div className="rounded border border-slate-800 bg-[#121820] p-2.5 space-y-2">
                <div className="flex items-center justify-between font-mono text-[10px]">
                  <span className="uppercase text-slate-400 font-bold">Min Threat Score</span>
                  <span className="text-amber-400 font-bold">{minRiskScore}+</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="90"
                  step="5"
                  value={minRiskScore}
                  onChange={(e) => setMinRiskScore(Number(e.target.value))}
                  className="w-full accent-sky-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg appearance-none"
                />
              </div>

              {/* Reset Controls */}
              <button
                onClick={() => {
                  setSelectedGroup("ALL");
                  setMinRiskScore(0);
                  setSelectedEntityTypes(
                    new Set(["Person", "Phone", "Location", "Vehicle", "Organization", "BankAccount", "Device", "Event"])
                  );
                  toast.info("Analytics Filters Reset to Default");
                }}
                className="w-full rounded border border-slate-800 bg-[#161D24] py-1.5 text-[11px] font-mono font-semibold text-slate-400 hover:text-sky-400 transition-colors cursor-pointer"
              >
                Reset All Controls
              </button>
            </div>
          </aside>

          {/* CENTER PANEL: Active Visualization & Dashboard */}
          <main className="flex-1 h-full overflow-y-auto p-4 custom-scrollbar bg-[#0B0F14]">
            {activeTab === "dashboard" && (
              <AnalyticsDashboard
                topology={topology}
                modularity={modularity}
                onNavigateTab={(tab) => setActiveTab(tab as AnalyticsTab)}
              />
            )}

            {activeTab === "centrality" && (
              <CentralityPanel
                scores={centralityScores}
                sortedByPageRank={sortedByPageRank}
                sortedByBetweenness={sortedByBetweenness}
                sortedByDegree={sortedByDegree}
                sortedByCloseness={sortedByCloseness}
                distributions={distributions}
                selectedEntityId={selectedEntityId}
                onSelectEntity={(id) => setSelectedEntityId(id)}
              />
            )}

            {activeTab === "communities" && (
              <CommunityDetection
                communities={communities}
                modularity={modularity}
                selectedCommunityId={selectedCommunityId}
                onSelectCommunity={setSelectedCommunityId}
                onSelectEntity={(id) => setSelectedEntityId(id)}
              />
            )}

            {activeTab === "shortest_path" && (
              <ShortestPathTracer
                entities={filteredEntities}
                relationships={filteredRelationships}
                onSelectEntity={(id) => setSelectedEntityId(id)}
              />
            )}

            {activeTab === "bridges" && (
              <BridgeAnalyzer
                bridgeEntities={sortedByBetweenness}
                communities={communities}
                onSelectEntity={(id) => setSelectedEntityId(id)}
              />
            )}

            {activeTab === "heatmap" && (
              <RiskHeatmap zones={riskZones} />
            )}

            {activeTab === "evolution" && (
              <NetworkEvolution
                entities={filteredEntities}
                relationships={filteredRelationships}
              />
            )}
          </main>

          {/* RIGHT PANEL: Explainability and Ranked Insights */}
          <aside className="w-88 border-l border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-slate-800 bg-[#141A21] px-4 py-3">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 flex items-center gap-1.5">
                <Zap className="size-3.5 text-amber-400" />
                Explainability & Ranked Insights
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4 custom-scrollbar">
              <ExplainabilityPanel
                score={selectedEntityScore}
                onNavigateToGraph={(id) => navigate({ to: "/network" })}
              />

              {/* Quick Top 3 Influencers List */}
              <div className="rounded-lg border border-slate-800 bg-[#121820] p-3 space-y-2">
                <span className="text-[10px] font-mono uppercase font-bold text-slate-400 block">
                  Top Kingpin Influencers
                </span>
                <div className="space-y-1.5">
                  {sortedByPageRank.slice(0, 3).map((inf, i) => (
                    <div
                      key={inf.entityId}
                      onClick={() => setSelectedEntityId(inf.entityId)}
                      className={cn(
                        "rounded border p-2 flex items-center justify-between transition-colors cursor-pointer",
                        selectedEntityId === inf.entityId
                          ? "border-sky-500 bg-[#172330]"
                          : "border-slate-800 bg-[#161D24] hover:border-slate-700"
                      )}
                    >
                      <div>
                        <strong className="text-slate-100 text-[11px] block">{inf.name}</strong>
                        <span className="text-[9px] font-mono text-slate-400">{inf.role || inf.label}</span>
                      </div>
                      <span className="font-mono text-xs font-bold text-sky-400">{inf.pageRank}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </aside>
        </div>

        {/* =========================================================================
            3. BOTTOM HIGH-DENSITY STATUS STRIP
           ========================================================================= */}
        <div className="border-t border-slate-800 bg-[#0B0F14] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-400 z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-purple-400 animate-pulse" />
              NETRA GRAPH ANALYTICS ENGINE
            </span>
            <span>
              Analyzed Scope: <strong className="text-slate-100">{filteredEntities.length} Nodes</strong> / {filteredRelationships.length} Links
            </span>
            <span>
              Modularity Q: <strong className="text-purple-400">{modularity.modularityScore}</strong>
            </span>
            <span>
              Network Diameter: <strong className="text-amber-400">{topology.networkDiameter} Hops</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-slate-400">
            <ShieldCheck className="size-3.5 text-emerald-400" />
            <span>Algorithmic Determinism Certified · Zero Hallucination</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
