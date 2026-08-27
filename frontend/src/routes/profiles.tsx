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
      title="Entities & Profiles"
      subtitle="Comprehensive Target Dossiers, Multi-Attribute Search & Record Matching"
    >
      <div className="flex min-h-[calc(100vh-130px)] flex-col rounded-md border border-[#E5E7EB] bg-white shadow-xs overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP WORKSPACE TOOLBAR & MODE SELECTOR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E5E7EB] bg-[#F8FAF8] px-4 py-2.5 z-20">
          {/* Center Tabs */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[#64748B]">
              View Mode:
            </span>
            <div className="flex items-center gap-1 rounded-md bg-[#E5E7EB] p-0.5 text-xs">
              <button
                onClick={() => setCenterTab("results")}
                className={cn(
                  "flex items-center gap-1.5 rounded px-3 py-1 font-semibold transition-all cursor-pointer",
                  centerTab === "results"
                    ? "bg-[#064E3B] text-white shadow-xs"
                    : "text-[#4B5563] hover:text-[#111827]"
                )}
              >
                <Users className="size-3.5" />
                <span>Entity Directory ({searchResults.length})</span>
              </button>

              <button
                onClick={() => setCenterTab("resolution_queue")}
                className={cn(
                  "flex items-center gap-1.5 rounded px-3 py-1 font-semibold transition-all cursor-pointer",
                  centerTab === "resolution_queue"
                    ? "bg-[#064E3B] text-white shadow-xs"
                    : "text-[#4B5563] hover:text-[#111827]"
                )}
              >
                <Sparkles className="size-3.5" />
                <span>Duplicate Records ({duplicatePairs.length})</span>
              </button>

              <button
                onClick={() => setCenterTab("comparison")}
                className={cn(
                  "flex items-center gap-1.5 rounded px-3 py-1 font-semibold transition-all cursor-pointer",
                  centerTab === "comparison"
                    ? "bg-[#064E3B] text-white shadow-xs"
                    : "text-[#4B5563] hover:text-[#111827]"
                )}
              >
                <ArrowRightLeft className="size-3.5" />
                <span>Comparison ({compareIds.size})</span>
              </button>

              <button
                onClick={() => setCenterTab("audit")}
                className={cn(
                  "flex items-center gap-1.5 rounded px-3 py-1 font-semibold transition-all cursor-pointer",
                  centerTab === "audit"
                    ? "bg-[#064E3B] text-white shadow-xs"
                    : "text-[#4B5563] hover:text-[#111827]"
                )}
              >
                <History className="size-3.5" />
                <span>Audit Logs ({auditLogs.length})</span>
              </button>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIngestModalOpen(true)}
              className="flex items-center gap-1.5 rounded-md bg-[#064E3B] hover:bg-[#04382A] px-3.5 py-1.5 text-xs font-semibold text-white transition-colors cursor-pointer shadow-xs"
            >
              <Plus className="size-3.5" />
              <span>Import Entity List</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. THREE-PANEL INVESTIGATION WORKSPACE
           ========================================================================= */}
        <div className="flex min-h-0 flex-1 overflow-hidden relative">
          {/* LEFT PANEL: Advanced Search & Faceted Filters */}
          <aside className="w-80 shrink-0 border-r border-[#E5E7EB] bg-[#F8FAF8] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-[#E5E7EB] bg-white px-4 py-3">
              <span className="text-xs font-bold text-[#111827] flex items-center gap-1.5">
                <Search className="size-4 text-[#064E3B]" />
                Filter & Search Entities
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4">
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
          <main className="min-w-0 flex-1 h-full flex flex-col overflow-hidden relative bg-white">
            {/* Modal Overlay: Resolution Matrix */}
            {activeResolutionPair && !activeMergePair && (
              <div className="absolute inset-0 z-30 bg-black/50 backdrop-blur-xs p-4 flex items-center justify-center overflow-y-auto">
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
              <div className="absolute inset-0 z-30 bg-black/50 backdrop-blur-xs p-4 flex items-center justify-center overflow-y-auto">
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
              <div className="flex-1 overflow-y-auto p-4 space-y-3 select-none bg-[#F5F8FC]">
                <div className="border-b border-[#D9E2EC] pb-2">
                  <h3 className="text-sm font-bold text-[#0F172A] flex items-center gap-2">
                    <Sparkles className="size-4 text-[#065F46]" />
                    Potential Duplicate Records ({duplicatePairs.length} Candidate Matches)
                  </h3>
                  <p className="text-xs text-[#64748B] mt-0.5">
                    Automated scanner identified records with matching phone numbers, accounts, or aliases for review.
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-3">
                  {duplicatePairs.map((pair) => (
                    <div
                      key={pair.id}
                      className="rounded-md border border-[#D9E2EC] bg-white p-4 transition-all hover:border-[#065F46] shadow-xs space-y-3"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <span
                          className={cn(
                            "rounded px-2.5 py-0.5 text-xs font-semibold border",
                            pair.matrix.overallConfidence >= 90
                              ? "bg-emerald-50 text-[#198754] border-emerald-200"
                              : "bg-amber-50 text-[#F59E0B] border-amber-200"
                          )}
                        >
                          {pair.matrix.confidenceCategory}: {pair.matrix.overallConfidence}% Match Confidence
                        </span>

                        <button
                          onClick={() => setActiveResolutionPair({ a: pair.sourceEntity, b: pair.candidateEntity })}
                          className="flex items-center gap-1.5 rounded-md bg-[#065F46] hover:bg-[#047857] px-3 py-1.5 text-xs font-semibold text-white transition-colors cursor-pointer shadow-xs"
                        >
                          <GitMerge className="size-3.5" />
                          <span>Review & Merge Records</span>
                        </button>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                        <div className="rounded-md bg-[#F8FAFC] p-3 border border-[#D9E2EC]">
                          <span className="text-[11px] font-semibold text-[#64748B] block mb-0.5">Record A</span>
                          <strong className="text-[#0F172A] text-sm">{pair.sourceEntity.name}</strong>
                          <span className="text-[#64748B] block text-xs mt-0.5">ID: {pair.sourceEntity.id} · {pair.sourceEntity.role}</span>
                        </div>
                        <div className="rounded-md bg-[#F8FAFC] p-3 border border-[#D9E2EC]">
                          <span className="text-[11px] font-semibold text-[#64748B] block mb-0.5">Record B</span>
                          <strong className="text-[#0F172A] text-sm">{pair.candidateEntity.name}</strong>
                          <span className="text-[#64748B] block text-xs mt-0.5">ID: {pair.candidateEntity.id} · {pair.candidateEntity.role}</span>
                        </div>
                      </div>

                      <div className="text-xs text-[#475569] space-y-1">
                        {pair.matrix.reasons.map((r, idx) => (
                          <div key={idx} className="flex items-center gap-1.5">
                            <span className="text-[#065F46]">•</span>
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
              <div className="flex-1 overflow-y-auto p-4 bg-[#F5F8FC]">
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
              <div className="flex-1 overflow-y-auto p-4 bg-[#F5F8FC]">
                <AuditTrail logs={auditLogs} />
              </div>
            )}
          </main>

          {/* RIGHT PANEL: Selected Entity Intelligence Profile & Timeline */}
          {selectedEntity && (
            <aside className="w-80 shrink-0 border-l border-[#D9E2EC] bg-white flex flex-col h-full overflow-hidden select-none 2xl:w-[420px]">
              {/* Right Panel Sub-tab Toggle */}
              <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] px-4 py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs">
                  <button
                    onClick={() => setRightTab("profile")}
                    className={cn(
                      "flex items-center gap-1.5 rounded-md px-3 py-1 font-semibold transition-all cursor-pointer",
                      rightTab === "profile"
                        ? "bg-white text-[#065F46] border border-[#D9E2EC] shadow-xs"
                        : "text-[#64748B] hover:text-[#0F172A]"
                    )}
                  >
                    <Target className="size-3.5" /> Entity Dossier
                  </button>

                  <button
                    onClick={() => setRightTab("timeline")}
                    className={cn(
                      "flex items-center gap-1.5 rounded-md px-3 py-1 font-semibold transition-all cursor-pointer",
                      rightTab === "timeline"
                        ? "bg-white text-[#065F46] border border-[#D9E2EC] shadow-xs"
                        : "text-[#64748B] hover:text-[#0F172A]"
                    )}
                  >
                    <Clock className="size-3.5" /> Timeline ({selectedEntity.timeline.length})
                  </button>
                </div>
              </div>

              {/* Right Panel Content */}
              <div className="flex-1 overflow-y-auto">
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
        <div className="border-t border-[#D9E2EC] bg-[#F8FAFC] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs text-[#64748B] z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-[#065F46] flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-[#198754]" />
              Record Register
            </span>
            <span>
              Total Database: <strong className="text-[#0F172A]">{entities.length} Profiles</strong>
            </span>
            <span>
              Filtered: <strong className="text-[#065F46]">{searchResults.length} Entities</strong>
            </span>
            <span>
              Possible Duplicates: <strong className="text-[#F59E0B]">{duplicatePairs.length} Records</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-xs text-[#64748B]">
            <ShieldCheck className="size-3.5 text-[#198754]" />
            <span>Certified under IT Act §69B & §65B</span>
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
