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
      title="Investigation Insights"
      subtitle="Network Structure Intelligence: Influence Ranking, Important Bridges, Criminal Cell Groups & Path Tracing"
    >
      <div className="flex flex-col h-[calc(100vh-130px)] rounded-md border border-[#E5E7EB] bg-white shadow-xs overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP ANALYTICS NAVIGATION & TAB SELECTOR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E5E7EB] bg-[#F8FAF8] px-4 py-2.5 z-20">
          {/* Main Tab Controls */}
          <div className="flex items-center gap-1 text-xs overflow-x-auto">
            {[
              { id: "dashboard", label: "Overview", icon: Activity },
              { id: "centrality", label: "Influence Ranking", icon: Award },
              { id: "bridges", label: "Important Network Bridges", icon: GitFork },
              { id: "communities", label: "Criminal Cell Groups", icon: PieChart },
              { id: "shortest_path", label: "Connection Path Tracer", icon: Share2 },
              { id: "heatmap", label: "Threat Heatmap", icon: Flame },
              { id: "evolution", label: "Timeline Evolution", icon: Clock },
            ].map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as AnalyticsTab)}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-3.5 py-1.5 text-xs font-semibold transition-all cursor-pointer whitespace-nowrap",
                    active
                      ? "bg-[#064E3B] text-white shadow-xs"
                      : "text-[#4B5563] hover:text-[#111827] hover:bg-white"
                  )}
                >
                  <Icon className="size-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate({ to: "/network" })}
              className="flex items-center gap-1.5 rounded-md bg-[#064E3B] hover:bg-[#04382A] px-3.5 py-1.5 text-xs font-semibold text-white transition-colors cursor-pointer shadow-xs"
            >
              <Share2 className="size-3.5" />
              <span>Explore on Graph</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. THREE-PANEL ANALYTICAL WORKSPACE
           ========================================================================= */}
        <div className="flex min-h-0 flex-1 overflow-hidden relative">
          {/* LEFT PANEL: Analytics Controls */}
          <aside className="w-72 shrink-0 border-r border-[#E5E7EB] bg-[#F8FAF8] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-[#E5E7EB] bg-white px-4 py-3">
              <span className="text-xs font-bold text-[#111827] flex items-center gap-1.5">
                <Filter className="size-4 text-[#064E3B]" />
                Analysis Filters
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4 text-xs">
              {/* Syndicate Group Filter */}
              <div className="rounded-md border border-[#D9E2EC] bg-white p-3 space-y-1.5">
                <label className="text-xs font-bold text-[#0F172A] block">
                  Syndicate Cluster
                </label>
                <select
                  value={selectedGroup}
                  onChange={(e) => setSelectedGroup(e.target.value)}
                  className="w-full rounded-md border border-[#D9E2EC] bg-[#F8FAFC] px-2.5 py-1 text-xs text-[#0F172A] font-semibold outline-none cursor-pointer focus:border-[#065F46]"
                >
                  <option value="ALL">All Syndicate Clusters</option>
                  {groupOptions.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
              </div>

              {/* Entity Type Matrix */}
              <div className="rounded-md border border-[#D9E2EC] bg-white p-3 space-y-1.5">
                <label className="text-xs font-bold text-[#0F172A] block">
                  Target Entity Scope
                </label>
                <div className="grid grid-cols-2 gap-1 text-xs">
                  {["Person", "Phone", "Location", "Vehicle", "Organization", "BankAccount", "Device", "Event"].map(
                    (type) => {
                      const active = selectedEntityTypes.has(type);
                      return (
                        <button
                          key={type}
                          onClick={() => toggleEntityType(type)}
                          className={cn(
                            "rounded-md border px-2 py-1 text-left transition-all cursor-pointer truncate text-xs",
                            active
                              ? "border-emerald-300 bg-emerald-50 text-[#065F46] font-semibold"
                              : "border-[#D9E2EC] bg-[#F8FAFC] text-[#64748B] hover:bg-[#F1F5F9]"
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
              <div className="rounded-md border border-[#D9E2EC] bg-white p-3 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-xs font-bold text-[#0F172A]">Minimum Threat Score</span>
                  <span className="text-[#065F46] font-bold">{minRiskScore}+</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="90"
                  step="5"
                  value={minRiskScore}
                  onChange={(e) => setMinRiskScore(Number(e.target.value))}
                  className="w-full accent-[#065F46] cursor-pointer h-1.5 bg-[#E2E8F0] rounded-lg appearance-none"
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
                className="w-full rounded-md border border-[#D9E2EC] bg-white py-2 text-xs font-semibold text-[#475569] hover:bg-[#F8FAFC] transition-colors cursor-pointer shadow-xs"
              >
                Reset All Filters
              </button>
            </div>
          </aside>

          {/* CENTER PANEL: Active Visualization & Dashboard */}
          <main className="flex-1 h-full overflow-y-auto p-4 bg-[#F5F8FC]">
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
          <aside className="w-88 border-l border-[#D9E2EC] bg-white flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] px-4 py-3">
              <span className="text-xs font-bold text-[#0F172A] flex items-center gap-1.5">
                <Zap className="size-4 text-[#065F46]" />
                Suspect Attribution & Notes
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4">
              <ExplainabilityPanel
                score={selectedEntityScore}
                onNavigateToGraph={(id) => navigate({ to: "/network" })}
              />

              {/* Quick Top 3 Influencers List */}
              <div className="rounded-md border border-[#D9E2EC] bg-white p-3.5 space-y-2 shadow-xs">
                <span className="text-xs font-bold text-[#0F172A] block">
                  Top Influential Suspects
                </span>
                <div className="space-y-1.5">
                  {sortedByPageRank.slice(0, 3).map((inf, i) => (
                    <div
                      key={inf.entityId}
                      onClick={() => setSelectedEntityId(inf.entityId)}
                      className={cn(
                        "rounded-md border p-2.5 flex items-center justify-between transition-colors cursor-pointer",
                        selectedEntityId === inf.entityId
                          ? "border-[#065F46] bg-emerald-50"
                          : "border-[#D9E2EC] bg-[#F8FAFC] hover:border-[#94A3B8]"
                      )}
                    >
                      <div>
                        <strong className="text-[#0F172A] text-xs block">{inf.name}</strong>
                        <span className="text-xs text-[#64748B]">{inf.role || inf.label}</span>
                      </div>
                      <span className="text-xs font-bold text-[#065F46]">{inf.pageRank}%</span>
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
        <div className="border-t border-[#D9E2EC] bg-[#F8FAFC] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs text-[#64748B] z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-[#065F46] flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-[#198754]" />
              Analysis Registry
            </span>
            <span>
              Scope: <strong className="text-[#0F172A]">{filteredEntities.length} Entities</strong> / {filteredRelationships.length} Connections
            </span>
            <span>
              Network Clusters: <strong className="text-[#065F46]">{communities.length} Groups</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-xs text-[#64748B]">
            <ShieldCheck className="size-3.5 text-[#198754]" />
            <span>Deterministic Graph Calculations · Section 65B Certified</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
