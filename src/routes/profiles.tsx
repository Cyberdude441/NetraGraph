import { createFileRoute, useNavigate } from "@tanstack/react-router";
import React, { useState, useMemo } from "react";
import {
  Users,
  Search,
  Filter,
  Sparkles,
  GitMerge,
  ArrowRightLeft,
  History,
  ShieldAlert,
  ShieldCheck,
  Target,
  Flame,
  Layers,
  Database,
  Plus,
  Clock,
  FileText,
} from "lucide-react";
import { toast } from "sonner";

import { AppShell } from "@/components/AppShell";
import { EntitySearch } from "@/components/EntityExplorer/EntitySearch";
import { EntityFilters } from "@/components/EntityExplorer/EntityFilters";
import { EntityResults } from "@/components/EntityExplorer/EntityResults";
import { EntityProfile } from "@/components/EntityExplorer/EntityProfile";
import { EntityTimeline } from "@/components/EntityExplorer/EntityTimeline";
import { EntityComparison } from "@/components/EntityExplorer/EntityComparison";
import { ResolutionMatrix } from "@/components/EntityExplorer/ResolutionMatrix";
import { MergeWorkspace } from "@/components/EntityExplorer/MergeWorkspace";
import { AuditTrail } from "@/components/EntityExplorer/AuditTrail";
import { DataIngestionModal } from "@/components/ingestion/DataIngestionModal";

import {
  COMPREHENSIVE_ENTITIES,
  type ComprehensiveEntity,
} from "@/data/syntheticEntities";
import {
  DEFAULT_ENTITY_FILTERS,
  filterAndSearchEntities,
  findDuplicateCandidatePairs,
  type EntityFilterState,
  type DuplicatePair,
} from "@/utils/entityMatching";
import { INITIAL_AUDIT_LOGS, type AuditLogEntry } from "@/utils/entityResolver";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/profiles")({
  head: () => ({
    meta: [
      { title: "Entity Explorer & Resolution Engine — NetraGraph AI" },
      {
        name: "description",
        content:
          "Enterprise criminal entity intelligence workspace with multi-dimensional search, similarity matrix matching, and controlled identity merge engine.",
      },
    ],
  }),
  component: EntityExplorerPage,
});

type CenterTabMode = "results" | "resolution_queue" | "comparison" | "audit";

function EntityExplorerPage() {
  const navigate = useNavigate();

  // Active Entity Database State
  const [entities, setEntities] = useState<ComprehensiveEntity[]>(COMPREHENSIVE_ENTITIES);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>(INITIAL_AUDIT_LOGS);

  // Search & Filter State
  const [filters, setFilters] = useState<EntityFilterState>(DEFAULT_ENTITY_FILTERS);
  const [selectedEntityId, setSelectedEntityId] = useState<string>("ENT-001");
  const [rightTab, setRightTab] = useState<"profile" | "timeline">("profile");

  // Center View Modes
  const [centerTab, setCenterTab] = useState<CenterTabMode>("results");
  const [sortBy, setSortBy] = useState<"risk" | "confidence" | "rank" | "name" | "activity">("risk");

  // Comparison State
  const [compareIds, setCompareIds] = useState<Set<string>>(new Set(["ENT-001", "ENT-002"]));

  // Resolution / Merge Active Modals
  const [activeResolutionPair, setActiveResolutionPair] = useState<{
    a: ComprehensiveEntity;
    b: ComprehensiveEntity;
  } | null>(null);

  const [activeMergePair, setActiveMergePair] = useState<{
    a: ComprehensiveEntity;
    b: ComprehensiveEntity;
  } | null>(null);

  const [ingestModalOpen, setIngestModalOpen] = useState(false);

  // Execute Search & Filters
  const searchResults = useMemo(() => {
    return filterAndSearchEntities(entities, filters);
  }, [entities, filters]);

  // Selected Entity
  const selectedEntity = useMemo(() => {
    return entities.find((e) => e.id === selectedEntityId) || entities[0] || null;
  }, [entities, selectedEntityId]);

  // Detected Duplicate Candidates
  const duplicatePairs = useMemo(() => {
    return findDuplicateCandidatePairs(entities);
  }, [entities]);

  // Entities in Comparison
  const comparedEntities = useMemo(() => {
    return entities.filter((e) => compareIds.has(e.id));
  }, [entities, compareIds]);

  const handleToggleCompare = (id: string) => {
    setCompareIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        if (next.size < 4) next.add(id);
        else toast.warning("Maximum 4 entities can be compared simultaneously.");
      }
      return next;
    });
  };

  // Open Resolution Matrix
  const handleOpenResolutionMatrix = (entity: ComprehensiveEntity) => {
    const candidateId = entity.metadata.duplicateCandidateOf;
    const candidate = entities.find((e) => e.id === candidateId);
    if (candidate) {
      setActiveResolutionPair({ a: entity, b: candidate });
    } else {
      // Find highest confidence duplicate pair matching this entity
      const pair = duplicatePairs.find(
        (p) => p.sourceEntity.id === entity.id || p.candidateEntity.id === entity.id
      );
      if (pair) {
        setActiveResolutionPair({ a: pair.sourceEntity, b: pair.candidateEntity });
      } else {
        toast.info("No active duplicate candidates detected for this profile.");
      }
    }
  };

  // Execute Merge Callback
  const handleMergeComplete = (merged: ComprehensiveEntity, audit: AuditLogEntry) => {
    setEntities((prev) => {
      // Replace primary and remove secondary
      const secondaryId = audit.previousValue?.secondary?.id;
      return prev
        .filter((e) => e.id !== secondaryId)
        .map((e) => (e.id === merged.id ? merged : e));
    });

    setAuditLogs((prev) => [audit, ...prev]);
    setActiveMergePair(null);
    setActiveResolutionPair(null);
    setSelectedEntityId(merged.id);
    setCenterTab("audit");
  };

  const networkGroupOptions = useMemo(() => {
    return Array.from(new Set(entities.map((e) => e.investigationGroup)));
  }, [entities]);

  return (
    <AppShell
      title="Entity Explorer & Resolution Engine"
      subtitle="Identity Disambiguation, Multi-Attribute Matching Matrix & Forensic Consolidation"
    >
      <div className="flex flex-col h-[calc(100vh-130px)] rounded border border-slate-800 bg-[#0B0F14] shadow-2xl overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP WORKSPACE NAVIGATION & MODE SELECTOR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-[#0E1318] px-4 py-2 z-20">
          {/* Center Tabs */}
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-mono uppercase font-bold text-slate-400">
              Workspace View:
            </span>
            <div className="flex items-center gap-1 rounded bg-[#161D24] p-0.5 border border-slate-800 font-mono text-xs">
              <button
                onClick={() => setCenterTab("results")}
                className={cn(
                  "flex items-center gap-1.5 rounded px-3 py-1 font-semibold transition-all cursor-pointer",
                  centerTab === "results"
                    ? "bg-[#1E293B] text-sky-400 border border-sky-500/40 shadow-xs"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                <Users className="size-3.5" />
                <span>Entity Explorer ({searchResults.length})</span>
              </button>

              <button
                onClick={() => setCenterTab("resolution_queue")}
                className={cn(
                  "flex items-center gap-1.5 rounded px-3 py-1 font-semibold transition-all cursor-pointer",
                  centerTab === "resolution_queue"
                    ? "bg-purple-950/50 text-purple-300 border border-purple-500/50 shadow-xs"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                <Sparkles className="size-3.5 text-purple-400" />
                <span>Resolution Queue ({duplicatePairs.length} Pairs)</span>
              </button>

              <button
                onClick={() => setCenterTab("comparison")}
                className={cn(
                  "flex items-center gap-1.5 rounded px-3 py-1 font-semibold transition-all cursor-pointer",
                  centerTab === "comparison"
                    ? "bg-amber-950/50 text-amber-300 border border-amber-500/50 shadow-xs"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                <ArrowRightLeft className="size-3.5 text-amber-400" />
                <span>Comparison Matrix ({compareIds.size})</span>
              </button>

              <button
                onClick={() => setCenterTab("audit")}
                className={cn(
                  "flex items-center gap-1.5 rounded px-3 py-1 font-semibold transition-all cursor-pointer",
                  centerTab === "audit"
                    ? "bg-emerald-950/50 text-emerald-300 border border-emerald-500/50 shadow-xs"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                <History className="size-3.5 text-emerald-400" />
                <span>Audit Trail ({auditLogs.length})</span>
              </button>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIngestModalOpen(true)}
              className="flex items-center gap-1 rounded border border-slate-800 bg-[#161D24] px-3 py-1 text-xs font-mono font-semibold text-slate-200 hover:border-sky-500 transition-colors cursor-pointer"
            >
              <Plus className="size-3.5 text-sky-400" />
              <span>Ingest Suspect List</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. THREE-PANEL INVESTIGATION WORKSPACE
           ========================================================================= */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* LEFT PANEL: Advanced Search & Faceted Filters */}
          <aside className="w-80 border-r border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-slate-800 bg-[#141A21] px-4 py-3">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 flex items-center gap-1.5">
                <Search className="size-3.5 text-sky-400" />
                Faceted Intelligence Search
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4 custom-scrollbar">
              <EntitySearch
                filters={filters}
                onFilterChange={setFilters}
                resultCount={searchResults.length}
              />

              <EntityFilters
                filters={filters}
                onFilterChange={setFilters}
                onReset={() => setFilters(DEFAULT_ENTITY_FILTERS)}
                networkGroupOptions={networkGroupOptions}
              />
            </div>
          </aside>

          {/* CENTER PANEL: Main Results / Resolution Queue / Comparison / Audit */}
          <main className="flex-1 h-full flex flex-col overflow-hidden relative bg-[#0B0F14]">
            {/* Modal Overlay: Resolution Matrix */}
            {activeResolutionPair && !activeMergePair && (
              <div className="absolute inset-0 z-30 bg-black/70 backdrop-blur-xs p-4 flex items-center justify-center overflow-y-auto">
                <div className="w-full max-w-2xl">
                  <ResolutionMatrix
                    entityA={activeResolutionPair.a}
                    entityB={activeResolutionPair.b}
                    onOpenMerge={(a, b) => setActiveMergePair({ a, b })}
                    onClose={() => setActiveResolutionPair(null)}
                  />
                </div>
              </div>
            )}

            {/* Modal Overlay: Merge Workspace */}
            {activeMergePair && (
              <div className="absolute inset-0 z-30 bg-black/75 backdrop-blur-xs p-4 flex items-center justify-center overflow-y-auto">
                <div className="w-full max-w-2xl">
                  <MergeWorkspace
                    entityA={activeMergePair.a}
                    entityB={activeMergePair.b}
                    onMergeComplete={handleMergeComplete}
                    onCancel={() => setActiveMergePair(null)}
                  />
                </div>
              </div>
            )}

            {/* Sub-view 1: Standard Entity Explorer Results */}
            {centerTab === "results" && (
              <EntityResults
                results={searchResults}
                selectedEntityId={selectedEntityId}
                onSelectEntity={(id) => setSelectedEntityId(id)}
                compareIds={compareIds}
                onToggleCompare={handleToggleCompare}
                sortBy={sortBy}
                onSortChange={setSortBy}
                onOpenResolutionMatrix={handleOpenResolutionMatrix}
              />
            )}

            {/* Sub-view 2: Entity Resolution Queue */}
            {centerTab === "resolution_queue" && (
              <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar select-none">
                <div className="border-b border-slate-800 pb-2">
                  <h3 className="font-mono text-xs font-bold uppercase text-slate-100 flex items-center gap-2">
                    <Sparkles className="size-4 text-purple-400" />
                    AI Duplicate Resolution & Merge Queue ({duplicatePairs.length} Candidate Matches)
                  </h3>
                  <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                    Automated multi-attribute scanner identified probable duplicate records requiring analyst validation.
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-3">
                  {duplicatePairs.map((pair) => (
                    <div
                      key={pair.id}
                      className="rounded-lg border border-slate-800 bg-[#121820] p-3.5 transition-all hover:border-purple-500/60"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
                        <span
                          className={cn(
                            "rounded px-2 py-0.5 font-mono text-[10px] font-bold border",
                            pair.matrix.overallConfidence >= 90
                              ? "bg-emerald-950/60 text-emerald-300 border-emerald-500/50"
                              : "bg-amber-950/60 text-amber-300 border-amber-500/50"
                          )}
                        >
                          {pair.matrix.confidenceCategory}: {pair.matrix.overallConfidence}% Match Confidence
                        </span>

                        <button
                          onClick={() => setActiveResolutionPair({ a: pair.sourceEntity, b: pair.candidateEntity })}
                          className="flex items-center gap-1 rounded border border-purple-500/50 bg-purple-950/40 px-3 py-1 text-xs font-mono font-bold text-purple-200 hover:bg-purple-900/60 transition-colors cursor-pointer"
                        >
                          <GitMerge className="size-3.5" />
                          <span>Review & Merge Profiles</span>
                        </button>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                        <div className="rounded bg-[#161D24] p-2 border border-slate-800">
                          <span className="text-[9px] uppercase text-slate-500 block">Record A</span>
                          <strong className="text-slate-100 text-[11px]">{pair.sourceEntity.name}</strong>
                          <span className="text-slate-400 block text-[10px]">ID: {pair.sourceEntity.id} · {pair.sourceEntity.role}</span>
                        </div>
                        <div className="rounded bg-[#161D24] p-2 border border-slate-800">
                          <span className="text-[9px] uppercase text-slate-500 block">Record B</span>
                          <strong className="text-slate-100 text-[11px]">{pair.candidateEntity.name}</strong>
                          <span className="text-slate-400 block text-[10px]">ID: {pair.candidateEntity.id} · {pair.candidateEntity.role}</span>
                        </div>
                      </div>

                      <div className="mt-2 text-[10px] font-mono text-slate-400 space-y-0.5">
                        {pair.matrix.reasons.map((r, idx) => (
                          <div key={idx} className="flex items-center gap-1 text-slate-300">
                            <span className="text-purple-400">•</span>
                            <span>{r}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sub-view 3: Comparative Analysis */}
            {centerTab === "comparison" && (
              <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                <EntityComparison
                  entities={comparedEntities}
                  onRemoveEntity={(id) => handleToggleCompare(id)}
                  onOpenResolution={(a, b) => setActiveResolutionPair({ a, b })}
                  onClose={() => setCenterTab("results")}
                />
              </div>
            )}

            {/* Sub-view 4: Forensic Audit Trail */}
            {centerTab === "audit" && (
              <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                <AuditTrail logs={auditLogs} />
              </div>
            )}
          </main>

          {/* RIGHT PANEL: Selected Entity Intelligence Profile & Timeline */}
          {selectedEntity && (
            <aside className="w-[420px] border-l border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none">
              {/* Right Panel Sub-tab Toggle */}
              <div className="border-b border-slate-800 bg-[#121820] px-4 py-2 flex items-center justify-between">
                <div className="flex items-center gap-1 font-mono text-xs">
                  <button
                    onClick={() => setRightTab("profile")}
                    className={cn(
                      "flex items-center gap-1.5 rounded px-2.5 py-1 font-bold transition-all cursor-pointer",
                      rightTab === "profile"
                        ? "bg-sky-500/20 text-sky-300 border border-sky-500/50"
                        : "text-slate-400 hover:text-slate-200"
                    )}
                  >
                    <Target className="size-3.5" /> Intelligence Dossier
                  </button>

                  <button
                    onClick={() => setRightTab("timeline")}
                    className={cn(
                      "flex items-center gap-1.5 rounded px-2.5 py-1 font-bold transition-all cursor-pointer",
                      rightTab === "timeline"
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/50"
                        : "text-slate-400 hover:text-slate-200"
                    )}
                  >
                    <Clock className="size-3.5" /> Forensic Timeline ({selectedEntity.timeline.length})
                  </button>
                </div>
              </div>

              {/* Right Panel Content */}
              <div className="flex-1 overflow-y-auto custom-scrollbar">
                {rightTab === "profile" ? (
                  <EntityProfile
                    entity={selectedEntity}
                    onNavigateToGraph={(id) => navigate({ to: "/network" })}
                    onOpenResolutionMatrix={handleOpenResolutionMatrix}
                  />
                ) : (
                  <div className="p-3">
                    <EntityTimeline
                      timeline={selectedEntity.timeline}
                      entityName={selectedEntity.name}
                    />
                  </div>
                )}
              </div>
            </aside>
          )}
        </div>

        {/* =========================================================================
            3. BOTTOM STATUS BAR
           ========================================================================= */}
        <div className="border-t border-slate-800 bg-[#0B0F14] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-400 z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-sky-400 animate-pulse" />
              NETRA ENTITY RESOLUTION ENGINE
            </span>
            <span>
              Total Database: <strong className="text-slate-100">{entities.length} Profiles</strong>
            </span>
            <span>
              Matches: <strong className="text-sky-300">{searchResults.length} Filtered</strong>
            </span>
            <span>
              Pending Duplicates: <strong className="text-purple-400">{duplicatePairs.length} Pairs</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-slate-400">
            <ShieldCheck className="size-3.5 text-emerald-400" />
            <span>IT Act §69B & §65B Chain of Custody Verified</span>
          </div>
        </div>
      </div>

      {/* Ingestion Modal */}
      <DataIngestionModal
        isOpen={ingestModalOpen}
        onClose={() => setIngestModalOpen(false)}
        onSuccess={() => toast.success("New evidence entities synchronized")}
      />
    </AppShell>
  );
}
