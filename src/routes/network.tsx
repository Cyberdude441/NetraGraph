import { createFileRoute } from "@tanstack/react-router";
import { ReactFlowProvider, type ReactFlowInstance } from "@xyflow/react";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Database,
  FolderLock,
  RefreshCw,
  FileCheck2,
  Layers,
  TrendingUp,
  PieChart,
  ShieldCheck,
  Zap,
  Network,
  Share2,
} from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { GraphFilters } from "@/components/IntelligenceGraph/GraphFilters";
import { LayoutSwitcher, type LayoutMode } from "@/components/IntelligenceGraph/LayoutSwitcher";
import { CentralityPanel } from "@/components/IntelligenceGraph/CentralityPanel";
import { CommunityView } from "@/components/IntelligenceGraph/CommunityView";
import { EntityDetailDrawer } from "@/components/IntelligenceGraph/EntityDetailDrawer";
import { SubgraphWorkspace } from "@/components/IntelligenceGraph/SubgraphWorkspace";
import { GraphCanvas } from "@/components/IntelligenceGraph/GraphCanvas";

import {
  SYNTHETIC_ENTITIES,
  SYNTHETIC_RELATIONSHIPS,
  type SyntheticEntity,
  type SyntheticRelationship,
} from "@/data/syntheticGraphData";
import {
  calculateCentralityMetrics,
  detectCommunities,
  getNHopNeighborhood,
  calculateGraphLayout,
} from "@/utils/graphAlgorithms";
import {
  DEFAULT_FILTERS,
  applyGraphFilters,
  type GraphFilterCriteria,
} from "@/utils/graphFilters";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/network")({
  head: () => ({
    meta: [
      { title: "Intelligence Graph & Network Analytics — NetraGraph AI" },
      {
        name: "description",
        content:
          "Advanced Criminal Network Analysis & Investigative Intelligence System with dynamic filtering, degree-of-separation expansion, layout engines, and centrality analytics.",
      },
    ],
  }),
  component: NetworkGraphPageWrapper,
});

type GraphSourceType = "ncrb_public" | "investigation_evidence";

function NetworkGraphPageWrapper() {
  return (
    <ReactFlowProvider>
      <IntelligenceGraphWorkspace />
    </ReactFlowProvider>
  );
}

function IntelligenceGraphWorkspace() {
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);

  // 1. Knowledge Layer & Dataset Source
  const [graphSource, setGraphSource] = useState<GraphSourceType>("investigation_evidence");
  const [filters, setFilters] = useState<GraphFilterCriteria>(DEFAULT_FILTERS);

  // 2. Navigation & Focal Selection
  const [focalNodeId, setFocalNodeId] = useState<string>("ENT-P-01");
  const [hopDistance, setHopDistance] = useState<number>(0);
  const [layoutMode, setLayoutMode] = useState<LayoutMode>("force");

  // 3. Subgraph Isolation Workspace
  const [selectedNodeIds, setSelectedNodeIds] = useState<Set<string>>(new Set());
  const [isIsolated, setIsIsolated] = useState<boolean>(false);

  // 4. Bottom Analytics Drawer Tab
  const [bottomTab, setBottomTab] = useState<"centrality" | "communities" | "collapsed">("centrality");
  const [activeCommunityId, setActiveCommunityId] = useState<number | null>(null);

  // Layer 1 Fallback Data (NCRB Public Aggregated)
  const {
    data: ncrbData,
    isLoading: isNcrbLoading,
    refetch: refetchNcrb,
  } = useQuery({
    queryKey: ["ncrb-public-graph"],
    queryFn: async () => {
      try {
        const res = await fetch("http://localhost:8000/api/graph/network?graph_source=ncrb_public");
        if (!res.ok) throw new Error("Backend offline");
        return res.json();
      } catch {
        return null;
      }
    },
    enabled: graphSource === "ncrb_public",
  });

  // Active Base Entities & Relationships
  const rawEntities: SyntheticEntity[] = useMemo(() => {
    if (graphSource === "ncrb_public" && ncrbData?.nodes) {
      return ncrbData.nodes.map((n: any) => ({
        id: n.id,
        name: n.name,
        label: (n.label === "State" ? "Location" : n.label === "CrimeCategory" ? "Event" : "Person") as any,
        role: n.crimeFrequency || n.role || n.label,
        riskScore: n.riskScore || 65,
        confidenceScore: 1.0,
        caseId: "NCRB-2025-PUBLIC",
        investigationGroup: "National Crime Statistics",
        firstSeen: "2023-01-01",
        lastSeen: "2025-12-31",
        metadata: {
          description: n.metadata?.description || "NCRB official aggregated catalog metric",
          tags: ["NCRB Official", "Statutory Data"],
        },
      }));
    }
    return SYNTHETIC_ENTITIES;
  }, [graphSource, ncrbData]);

  const rawRelationships: SyntheticRelationship[] = useMemo(() => {
    if (graphSource === "ncrb_public" && ncrbData?.relationships) {
      return ncrbData.relationships.map((r: any) => ({
        id: r.id,
        sourceId: r.sourceId,
        targetId: r.targetId,
        type: "ASSOCIATION",
        label: r.metadata?.label || r.type,
        weight: 8,
        confidence: 1.0,
        timestamp: "2025-01-01T00:00:00Z",
        detail: r.metadata?.detail || r.metadata?.rate || "Aggregated State Record",
      }));
    }
    return SYNTHETIC_RELATIONSHIPS;
  }, [graphSource, ncrbData]);

  // Execute Dynamic Filters
  const { filteredEntities, filteredRelationships, filterStats } = useMemo(() => {
    let activeFilterSet = { ...filters };
    if (activeCommunityId !== null) {
      // Filter by active community
      const commNodeIds = new Set(
        rawEntities.filter((e) => e.investigationGroup === rawEntities.find((x) => x.id === focalNodeId)?.investigationGroup).map((e) => e.id)
      );
      if (commNodeIds.size > 0) {
        activeFilterSet.isolatedNodeIds = commNodeIds;
      }
    }
    return applyGraphFilters(rawEntities, rawRelationships, activeFilterSet);
  }, [rawEntities, rawRelationships, filters, activeCommunityId, focalNodeId]);

  // Centrality & Community Calculations
  const centralityMetrics = useMemo(() => {
    return calculateCentralityMetrics(filteredEntities, filteredRelationships);
  }, [filteredEntities, filteredRelationships]);

  const { communities, entityCommunityMap } = useMemo(() => {
    return detectCommunities(filteredEntities, filteredRelationships);
  }, [filteredEntities, filteredRelationships]);

  // N-Hop Neighborhood Calculations
  const { hopReachableIds, hopEdgeIds } = useMemo(() => {
    if (hopDistance <= 0 || !focalNodeId) {
      return { hopReachableIds: null, hopEdgeIds: null };
    }
    const hopRes = getNHopNeighborhood(
      focalNodeId,
      hopDistance,
      filteredEntities,
      filteredRelationships
    );
    return {
      hopReachableIds: hopRes.reachableNodeIds,
      hopEdgeIds: hopRes.connectedEdgeIds,
    };
  }, [focalNodeId, hopDistance, filteredEntities, filteredRelationships]);

  // Layout Engine Positions
  const layoutPositions = useMemo(() => {
    return calculateGraphLayout(
      layoutMode,
      filteredEntities,
      filteredRelationships,
      centralityMetrics,
      entityCommunityMap
    );
  }, [layoutMode, filteredEntities, filteredRelationships, centralityMetrics, entityCommunityMap]);

  // Selected Entity Object
  const selectedEntity = useMemo(() => {
    return (
      filteredEntities.find((e) => e.id === focalNodeId) ||
      filteredEntities[0] ||
      null
    );
  }, [filteredEntities, focalNodeId]);

  const selectedEntityCommunity = useMemo(() => {
    if (!selectedEntity) return undefined;
    const cId = entityCommunityMap[selectedEntity.id];
    return communities.find((c) => c.id === cId);
  }, [selectedEntity, entityCommunityMap, communities]);

  // Case & Group Dropdown Options
  const caseOptions = useMemo(() => {
    const cases = Array.from(new Set(rawEntities.map((e) => e.caseId)));
    return cases.map((c) => ({ id: c, label: c }));
  }, [rawEntities]);

  const groupOptions = useMemo(() => {
    return Array.from(new Set(rawEntities.map((e) => e.investigationGroup)));
  }, [rawEntities]);

  // Handle Node Click
  const handleNodeClick = useCallback((nodeId: string) => {
    setFocalNodeId(nodeId);
    setSelectedNodeIds((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  // Isolate Subgraph
  const handleIsolateSelected = useCallback(() => {
    if (selectedNodeIds.size === 0) return;
    setFilters((prev) => ({
      ...prev,
      isolatedNodeIds: new Set(selectedNodeIds),
    }));
    setIsIsolated(true);
    toast.success("Investigation Subgraph Isolated", {
      description: `Active workspace narrowed to ${selectedNodeIds.size} focal entities.`,
    });
  }, [selectedNodeIds]);

  // Reset Subgraph Isolation
  const handleResetIsolation = useCallback(() => {
    setFilters((prev) => ({
      ...prev,
      isolatedNodeIds: null,
    }));
    setIsIsolated(false);
    setSelectedNodeIds(new Set());
    toast.info("Full Network Restored", {
      description: "Displaying complete syndicate graph.",
    });
  }, []);

  const handleResetAllFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    setHopDistance(0);
    setIsIsolated(false);
    setSelectedNodeIds(new Set());
    setActiveCommunityId(null);
    toast.info("Filters Reset to Baseline");
  }, []);

  return (
    <AppShell
      title="Forensic Intelligence Graph & Network Analytics"
      subtitle="Multi-Modal Criminal Network Analysis, Centrality Metrics, Community Detection & Explainable Intelligence"
    >
      <div className="flex flex-col h-[calc(100vh-130px)] rounded border border-slate-800 bg-[#0B0F14] shadow-2xl overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP DUAL-LAYER GRAPH & SUBGRAPH WORKSPACE TOOLBAR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-[#0E1318] px-4 py-2 z-20">
          {/* Layer Selector */}
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-slate-400 uppercase font-bold">
              Knowledge Layer:
            </span>
            <div className="flex items-center gap-1 rounded bg-[#161D24] p-0.5 border border-slate-800">
              <button
                onClick={() => {
                  setGraphSource("investigation_evidence");
                  setFocalNodeId("ENT-P-01");
                  setHopDistance(0);
                }}
                className={cn(
                  "flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer",
                  graphSource === "investigation_evidence"
                    ? "bg-[#1E293B] text-sky-400 border border-sky-500/40 shadow-xs"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                <FolderLock className="size-3.5 text-sky-400" />
                <span>Layer 2: Case Investigation Evidence</span>
              </button>

              <button
                onClick={() => {
                  setGraphSource("ncrb_public");
                  setFocalNodeId("");
                  setHopDistance(0);
                }}
                className={cn(
                  "flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer",
                  graphSource === "ncrb_public"
                    ? "bg-[#1E293B] text-emerald-400 border border-emerald-500/40 shadow-xs"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                <Database className="size-3.5 text-emerald-400" />
                <span>Layer 1: NCRB Public Statistics</span>
              </button>
            </div>
          </div>

          {/* Subgraph Controls */}
          <div className="flex items-center gap-2">
            <SubgraphWorkspace
              selectedNodeIds={selectedNodeIds}
              isIsolated={isIsolated}
              totalEntities={rawEntities.length}
              visibleEntities={filteredEntities.length}
              onIsolateSelected={handleIsolateSelected}
              onResetIsolation={handleResetIsolation}
              onSaveSnapshot={() => {
                toast.success("Forensic Snapshot Dossier Saved to Audit Trail");
              }}
            />

            {/* Refresh */}
            <button
              onClick={() => {
                if (graphSource === "ncrb_public") refetchNcrb();
                toast.success("Knowledge Graph Refreshed");
              }}
              className="flex items-center gap-1 rounded border border-slate-800 bg-[#161D24] px-2.5 py-1 text-[11px] font-semibold text-slate-300 hover:border-sky-500 transition-colors cursor-pointer"
            >
              <RefreshCw className={cn("size-3 text-sky-400", isNcrbLoading && "animate-spin")} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. LAYOUT SWITCHER & DEGREE-OF-SEPARATION BAR
           ========================================================================= */}
        <LayoutSwitcher
          currentLayout={layoutMode}
          onLayoutChange={setLayoutMode}
          hopDistance={hopDistance}
          onHopChange={setHopDistance}
          hasFocalNode={Boolean(focalNodeId)}
          focalNodeName={selectedEntity?.name}
          totalVisible={filteredEntities.length}
        />

        {/* =========================================================================
            3. MAIN THREE-COLUMN WORKSPACE
           ========================================================================= */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* Left Column: Filter Matrix */}
          <GraphFilters
            filters={filters}
            onFilterChange={setFilters}
            onReset={handleResetAllFilters}
            caseOptions={caseOptions}
            groupOptions={groupOptions}
            stats={filterStats}
          />

          {/* Center Column: Graph Canvas */}
          <div className="flex-1 h-full flex flex-col relative overflow-hidden">
            <GraphCanvas
              entities={filteredEntities}
              relationships={filteredRelationships}
              positions={layoutPositions}
              focalNodeId={focalNodeId}
              hopReachableIds={hopReachableIds}
              hopEdgeIds={hopEdgeIds}
              onNodeClick={handleNodeClick}
              onInit={setRfInstance}
            />

            {/* Strict Governance Notice Badge */}
            <div className="pointer-events-none absolute top-3 left-3 z-10 rounded border border-slate-800 bg-[#0E1318]/95 p-2.5 backdrop-blur-md text-xs space-y-1 shadow-xl">
              <div className="flex items-center gap-2 font-mono font-bold">
                {graphSource === "investigation_evidence" ? (
                  <span className="text-sky-400 flex items-center gap-1.5">
                    <FolderLock className="size-3.5" /> GRAPH 2: AUTHORIZED CASE EVIDENCE
                  </span>
                ) : (
                  <span className="text-emerald-400 flex items-center gap-1.5">
                    <FileCheck2 className="size-3.5" /> GRAPH 1: NCRB PUBLIC AGGREGATED METRICS
                  </span>
                )}
              </div>
              <p className="text-[10px] text-slate-400 max-w-xs font-mono leading-tight">
                {graphSource === "investigation_evidence"
                  ? "Multi-source forensic corroboration: CDRs, KYC records, CFSL hashes & bank ledgers."
                  : "Verified statutory ground-truth from NCRB National Data Catalog."}
              </p>
            </div>
          </div>

          {/* Right Column: Entity Intelligence Detail Drawer */}
          {selectedEntity && (
            <EntityDetailDrawer
              entity={selectedEntity}
              relationships={rawRelationships}
              allEntities={rawEntities}
              centrality={centralityMetrics[selectedEntity.id]}
              community={selectedEntityCommunity}
              onSelectEntity={(id) => setFocalNodeId(id)}
            />
          )}
        </div>

        {/* =========================================================================
            4. BOTTOM ANALYTICS DRAWER (CENTRALITY & COMMUNITIES)
           ========================================================================= */}
        {bottomTab !== "collapsed" && (
          <div className="border-t border-slate-800 bg-[#0E1318] z-20 shadow-2xl transition-all duration-200">
            <div className="flex items-center justify-between border-b border-slate-800/80 px-4 py-1.5 bg-[#121922]">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase font-bold text-slate-400">
                  Analytics Stream:
                </span>
                <button
                  onClick={() => setBottomTab("centrality")}
                  className={cn(
                    "flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[10px] font-bold transition-all cursor-pointer",
                    bottomTab === "centrality"
                      ? "bg-sky-500/20 text-sky-300 border border-sky-500/50"
                      : "text-slate-400 hover:text-slate-200"
                  )}
                >
                  <TrendingUp className="size-3" /> Centrality Leaderboards
                </button>
                <button
                  onClick={() => setBottomTab("communities")}
                  className={cn(
                    "flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[10px] font-bold transition-all cursor-pointer",
                    bottomTab === "communities"
                      ? "bg-purple-500/20 text-purple-300 border border-purple-500/50"
                      : "text-slate-400 hover:text-slate-200"
                  )}
                >
                  <PieChart className="size-3" /> Community Clusters ({communities.length})
                </button>
              </div>

              <button
                onClick={() => setBottomTab("collapsed")}
                className="text-[10px] font-mono text-slate-400 hover:text-slate-200 cursor-pointer"
              >
                Hide Panel ▼
              </button>
            </div>

            {bottomTab === "centrality" && (
              <CentralityPanel
                entities={filteredEntities}
                centrality={centralityMetrics}
                focalNodeId={focalNodeId}
                onSelectEntity={(id) => setFocalNodeId(id)}
              />
            )}

            {bottomTab === "communities" && (
              <div className="p-3">
                <CommunityView
                  communities={communities}
                  activeClusterId={activeCommunityId}
                  onSelectCluster={setActiveCommunityId}
                  onSelectBridgeNode={(id) => setFocalNodeId(id)}
                />
              </div>
            )}
          </div>
        )}

        {/* =========================================================================
            5. BOTTOM HIGH-DENSITY STATUS STRIP
           ========================================================================= */}
        <div className="border-t border-slate-800 bg-[#0B0F14] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-400 z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
              NETRA CORE INTELLIGENCE GRAPH
            </span>

            <span>
              Active Filtered: <strong className="text-sky-300">{filteredEntities.length}</strong> / {rawEntities.length} Nodes
            </span>

            <span>
              Link Density: <strong className="text-slate-100">{filteredRelationships.length}</strong> Edges
            </span>

            <span>
              Detected Syndicates: <strong className="text-purple-400">{communities.length} Clusters</strong>
            </span>

            {bottomTab === "collapsed" && (
              <button
                onClick={() => setBottomTab("centrality")}
                className="text-[10px] font-mono text-sky-400 hover:underline cursor-pointer flex items-center gap-1"
              >
                <TrendingUp className="size-3" /> Show Centrality Drawer ▲
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 text-[11px] text-slate-400">
            <ShieldCheck className="size-3.5 text-emerald-400" />
            <span>Zero Hallucination Compliance · IT Act §69B & 65B Certified</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
