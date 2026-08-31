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
import { api } from "@/services/api";

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
    queryFn: () => api.getPublicGraph(),
    enabled: graphSource === "ncrb_public",
  });

  // Layer 2 Case Evidence Graph Data
  const {
    data: evidenceNodesData,
    refetch: refetchEvidenceNodes,
  } = useQuery({
    queryKey: ["graph-nodes-evidence"],
    queryFn: () => api.getGraphNodes({ graph_source: "investigation_evidence" }),
    enabled: graphSource === "investigation_evidence",
  });

  const {
    data: evidenceRelsData,
    refetch: refetchEvidenceRels,
  } = useQuery({
    queryKey: ["graph-rels-evidence"],
    queryFn: () => api.getGraphRelationships({ graph_source: "investigation_evidence" }),
    enabled: graphSource === "investigation_evidence",
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

    if (graphSource === "investigation_evidence" && evidenceNodesData?.nodes && evidenceNodesData.nodes.length > 0) {
      return evidenceNodesData.nodes.map((n: any) => ({
        id: n.id,
        name: n.name || n.id,
        label: (n.label || "Person") as any,
        role: n.role || n.label,
        riskScore: n.risk_score || n.riskScore || 75,
        confidenceScore: n.confidence_score || 0.98,
        caseId: n.case_id || "CASE-ACTIVE",
        investigationGroup: n.case_id || "Verified Case Evidence",
        firstSeen: n.timestamp || "2024-01-01",
        lastSeen: n.timestamp || "2026-08-31",
        sourceDocument: n.source_document || "Police Docket",
        metadata: {
          description: n.source_document || "Forensically verified case asset",
          jurisdiction: n.jurisdiction,
          ipAddress: n.ipAddress || n.ip,
          accountNumber: n.accountNumber,
          tags: ["Case Evidence", n.label],
        },
      }));
    }

    return SYNTHETIC_ENTITIES;
  }, [graphSource, ncrbData, evidenceNodesData]);

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

    if (graphSource === "investigation_evidence" && evidenceRelsData?.relationships && evidenceRelsData.relationships.length > 0) {
      return evidenceRelsData.relationships.map((r: any) => ({
        id: r.id,
        sourceId: r.source_id || r.sourceId,
        targetId: r.target_id || r.targetId,
        type: r.type || "ASSOCIATION",
        label: r.type || "LINK",
        weight: 9,
        confidence: 0.99,
        timestamp: r.metadata?.timestamp || "2024-01-01T00:00:00Z",
        detail: r.source_document || "Verified Forensic Edge",
      }));
    }

    return SYNTHETIC_RELATIONSHIPS;
  }, [graphSource, ncrbData, evidenceRelsData]);

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
      title="Knowledge Graph"
      subtitle="Visual Network Graph: Suspect Associations, Financial Trails, Communications & Link Expansion"
    >
      <div className="flex min-h-[calc(100vh-130px)] flex-col rounded-md border border-[#E5E7EB] bg-white shadow-xs overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP GRAPH ACTION BAR & SIMPLE CONTROLS
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E5E7EB] bg-[#F8FAF8] px-4 py-2.5 z-20">
          {/* Simple Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setHopDistance((prev) => (prev >= 3 ? 1 : prev + 1));
                toast.info(`Connection Scope: ${hopDistance + 1} Degrees of Separation`);
              }}
              className="flex items-center gap-1.5 rounded-md bg-[#064E3B] hover:bg-[#04382A] px-3.5 py-1.5 text-xs font-semibold text-white transition-colors cursor-pointer shadow-xs"
            >
              <span>+ Expand Connections ({hopDistance || "All"})</span>
            </button>

            <button
              onClick={() => {
                if (focalNodeId) {
                  setHopDistance(1);
                  toast.success(`Showing directly connected entities for ${selectedEntity?.name || "selected suspect"}`);
                } else {
                  toast.info("Click an entity on the graph first to show its related contacts");
                }
              }}
              className="flex items-center gap-1.5 rounded-md border border-[#E5E7EB] bg-white hover:bg-[#F3F4F6] px-3.5 py-1.5 text-xs font-semibold text-[#111827] transition-colors cursor-pointer shadow-xs"
            >
              <span>+ Show Related Entities</span>
            </button>

            <button
              onClick={() => {
                window.location.href = "/geo-timeline";
              }}
              className="flex items-center gap-1.5 rounded-md border border-[#E5E7EB] bg-white hover:bg-[#F3F4F6] px-3.5 py-1.5 text-xs font-semibold text-[#111827] transition-colors cursor-pointer shadow-xs"
            >
              <span>+ View Timeline</span>
            </button>
          </div>

          {/* Right Action Tools */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setBottomTab((prev) => (prev === "collapsed" ? "centrality" : "collapsed"))}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-3.5 py-1.5 text-xs font-semibold transition-colors cursor-pointer border",
                bottomTab !== "collapsed"
                  ? "bg-emerald-50 text-[#064E3B] border-[#16A34A]"
                  : "bg-white text-[#4B5563] border-[#E5E7EB] hover:bg-[#F3F4F6]"
              )}
            >
              <TrendingUp className="size-3.5 text-[#16A34A]" />
              <span>{bottomTab !== "collapsed" ? "Hide Advanced Analysis ▲" : "Advanced Analysis ▼"}</span>
            </button>

            {/* Refresh */}
            <button
              onClick={() => {
                if (graphSource === "ncrb_public") refetchNcrb();
                toast.success("Knowledge Graph Refreshed");
              }}
              className="flex items-center gap-1.5 rounded-md border border-[#E5E7EB] bg-white px-3.5 py-1.5 text-xs font-semibold text-[#4B5563] hover:bg-[#F3F4F6] transition-colors cursor-pointer shadow-xs"
            >
              <RefreshCw className={cn("size-3.5 text-[#064E3B]", isNcrbLoading && "animate-spin")} />
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
        <div className="flex min-h-0 flex-1 overflow-hidden relative">
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
          <div className="flex-1 h-full flex flex-col relative overflow-hidden bg-white">
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
            <div className="pointer-events-none absolute top-3 left-3 z-10 rounded-md border border-[#E2E8F0] bg-white/95 p-3 backdrop-blur-md text-xs space-y-1 shadow-xs">
              <div className="flex items-center gap-2 font-bold">
                <span className="text-[#064E3B] flex items-center gap-1.5">
                  <FolderLock className="size-4 text-[#16A34A]" /> CASE EVIDENCE GRAPH: OPERATION NETRA-VIGIL
                </span>
              </div>
              <p className="text-xs text-[#64748B] max-w-xs leading-tight">
                Multi-source intelligence: CDR logs, bank account transfers, and suspect associations.
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
            4. BOTTOM ANALYTICS DRAWER (COLLAPSIBLE)
           ========================================================================= */}
        {bottomTab !== "collapsed" && (
          <div className="border-t border-[#E2E8F0] bg-white z-20 shadow-lg transition-all duration-200">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] px-4 py-2 bg-[#F8FAFC]">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[#0F172A]">
                  Advanced Analysis:
                </span>
                <button
                  onClick={() => setBottomTab("centrality")}
                  className={cn(
                    "flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer",
                    bottomTab === "centrality"
                      ? "bg-[#064E3B] text-white shadow-xs"
                      : "text-[#64748B] hover:text-[#0F172A]"
                  )}
                >
                  <TrendingUp className="size-3" /> Suspect Importance
                </button>
                <button
                  onClick={() => setBottomTab("communities")}
                  className={cn(
                    "flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer",
                    bottomTab === "communities"
                      ? "bg-[#064E3B] text-white shadow-xs"
                      : "text-[#64748B] hover:text-[#0F172A]"
                  )}
                >
                  <PieChart className="size-3" /> Crime Syndicate Cells ({communities.length})
                </button>
              </div>

              <button
                onClick={() => setBottomTab("collapsed")}
                className="text-xs text-[#64748B] hover:text-[#0F172A] cursor-pointer font-medium"
              >
                Hide Drawer ▲
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
            5. BOTTOM STATUS STRIP
           ========================================================================= */}
        <div className="border-t border-[#D9E2EC] bg-[#F8FAFC] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs text-[#64748B] z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-[#065F46] flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-[#198754]" />
              NETRA KNOWLEDGE GRAPH
            </span>

            <span>
              Visible: <strong className="text-[#065F46]">{filteredEntities.length}</strong> / {rawEntities.length} Entities
            </span>

            <span>
              Connections: <strong className="text-[#0F172A]">{filteredRelationships.length}</strong> Links
            </span>

            <span>
              Syndicate Cells: <strong className="text-[#065F46]">{communities.length} Groups</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-xs text-[#64748B]">
            <ShieldCheck className="size-3.5 text-[#198754]" />
            <span>IT Act Section 65B Certified Forensic Graph</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
