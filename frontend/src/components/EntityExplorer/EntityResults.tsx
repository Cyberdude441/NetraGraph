import React from "react";
import {
  Sparkles,
  ArrowRight,
  Target,
  Flame,
  ShieldCheck,
  Share2,
  Calendar,
  Layers,
  CheckSquare,
  Square,
  ArrowUpDown,
  FileCheck2,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { FilteredEntityResult } from "@/utils/entityMatching";
import type { ComprehensiveEntity } from "@/data/syntheticEntities";

interface EntityResultsProps {
  results: FilteredEntityResult[];
  selectedEntityId: string | null;
  onSelectEntity: (id: string) => void;
  compareIds: Set<string>;
  onToggleCompare: (id: string) => void;
  sortBy: "risk" | "confidence" | "rank" | "name" | "activity";
  onSortChange: (sort: "risk" | "confidence" | "rank" | "name" | "activity") => void;
  onOpenResolutionMatrix: (entity: ComprehensiveEntity) => void;
}

export function EntityResults({
  results,
  selectedEntityId,
  onSelectEntity,
  compareIds,
  onToggleCompare,
  sortBy,
  onSortChange,
  onOpenResolutionMatrix,
}: EntityResultsProps) {
  // Sort results
  const sorted = [...results].sort((a, b) => {
    if (sortBy === "risk") return b.entity.riskScore - a.entity.riskScore;
    if (sortBy === "confidence") return b.entity.confidenceScore - a.entity.confidenceScore;
    if (sortBy === "rank") return (a.entity.centralityRank || 99) - (b.entity.centralityRank || 99);
    if (sortBy === "activity") return new Date(b.entity.lastSeen).getTime() - new Date(a.entity.lastSeen).getTime();
    return a.entity.name.localeCompare(b.entity.name);
  });

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden select-none bg-[#F8FAFC]">
      {/* Top Results Control Bar */}
      <div className="border-b border-[#E2E8F0] bg-white px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs shadow-xs">
        <div className="flex items-center gap-2 text-xs">
          <span className="text-[#64748B]">Matching Entities:</span>
          <span className="font-bold text-[#064E3B]">{results.length} records</span>
          {compareIds.size > 0 && (
            <span className="rounded bg-amber-50 border border-amber-200 px-2 py-0.5 text-xs text-[#F59E0B] font-semibold">
              {compareIds.size} Selected for Comparison
            </span>
          )}
        </div>

        {/* Sort Controls */}
        <div className="flex items-center gap-1.5 text-xs">
          <ArrowUpDown className="size-3.5 text-[#64748B]" />
          <span className="text-[#64748B]">Sort:</span>
          <select
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value as any)}
            className="rounded-md border border-[#E2E8F0] bg-[#F8FAFC] px-2.5 py-1 text-xs text-[#0F172A] font-semibold outline-none cursor-pointer focus:border-[#16A34A]"
          >
            <option value="risk">Risk Severity Score</option>
            <option value="confidence">Evidence Confidence</option>
            <option value="rank">Network Influence Rank</option>
            <option value="activity">Recent Activity</option>
            <option value="name">Alphabetical (A-Z)</option>
          </select>
        </div>
      </div>

      {/* Results List */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-2.5">
        {sorted.length === 0 ? (
          <div className="rounded-md border border-dashed border-[#E2E8F0] bg-white p-8 text-center text-[#64748B] text-xs">
            No entities match the active search criteria.
          </div>
        ) : (
          sorted.map(({ entity, isSimilarityMatch, matchScore, matchField, duplicateCount }) => {
            const isSelected = selectedEntityId === entity.id;
            const isComparing = compareIds.has(entity.id);
            const risk = entity.riskScore;

            return (
              <div
                key={entity.id}
                onClick={() => onSelectEntity(entity.id)}
                className={cn(
                  "rounded-md border p-4 transition-all cursor-pointer relative bg-white shadow-xs",
                  isSelected
                    ? "border-[#16A34A] ring-2 ring-[#16A34A]/20"
                    : "border-[#E2E8F0] hover:border-[#94A3B8] hover:bg-[#F8FAFC]"
                )}
              >
                {/* Top Identity Row */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2.5 min-w-0">
                    {/* Compare Checkbox */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleCompare(entity.id);
                      }}
                      className="mt-0.5 text-[#94A3B8] hover:text-[#064E3B] transition-colors cursor-pointer"
                      title="Select for comparative analysis"
                    >
                      {isComparing ? (
                        <CheckSquare className="size-4 text-[#064E3B]" />
                      ) : (
                        <Square className="size-4 text-[#CBD5E1]" />
                      )}
                    </button>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-sans text-xs font-bold text-[#0F172A] truncate">
                          {entity.name}
                        </h3>

                        {/* Duplicate Alert Pill */}
                        {duplicateCount > 0 && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onOpenResolutionMatrix(entity);
                            }}
                            className="rounded bg-amber-50 border border-amber-200 px-2 py-0.5 text-[11px] font-semibold text-[#F59E0B] hover:bg-amber-100 transition-colors"
                          >
                            Possible Duplicate
                          </button>
                        )}
                      </div>

                      <p className="mt-0.5 text-xs text-[#64748B] truncate">
                        ID: <span className="text-[#064E3B] font-semibold font-mono">{entity.id}</span> · {entity.role || entity.label} · {entity.metadata.jurisdiction || "National Cyber Cell"}
                      </p>
                    </div>
                  </div>

                  {/* Risk Score Pill */}
                  <div className="shrink-0 flex items-center gap-1.5">
                    <span
                      className={cn(
                        "flex items-center gap-1 rounded-md px-2.5 py-0.5 text-xs font-bold",
                        risk >= 85
                          ? "bg-red-50 text-[#DC2626] border border-red-200"
                          : risk >= 70
                          ? "bg-orange-50 text-[#EA580C] border border-orange-200"
                          : risk >= 50
                          ? "bg-amber-50 text-[#F59E0B] border border-amber-200"
                          : "bg-emerald-50 text-[#16A34A] border border-emerald-200"
                      )}
                    >
                      {risk >= 85 && <Flame className="size-3 text-[#DC2626]" />}
                      Risk {risk}/100
                    </span>
                  </div>
                </div>

                {/* Metrics Line */}
                <div className="mt-2.5 grid grid-cols-2 2xl:grid-cols-4 gap-2 border-t border-[#E2E8F0] pt-2 text-xs text-[#64748B]">
                  <div>
                    <span className="text-[#94A3B8]">Type: </span>
                    <strong className="text-[#0F172A]">{entity.label}</strong>
                  </div>
                  <div>
                    <span className="text-[#94A3B8]">Confidence: </span>
                    <strong className="text-[#16A34A]">{(entity.confidenceScore * 100).toFixed(0)}%</strong>
                  </div>
                  <div>
                    <span className="text-[#94A3B8]">Connections: </span>
                    <strong className="text-[#064E3B]">{entity.degreeCount || entity.relationshipsCount || 12} links</strong>
                  </div>
                  <div>
                    <span className="text-[#94A3B8]">Last Seen: </span>
                    <strong className="text-[#0F172A]">{entity.lastSeen}</strong>
                  </div>
                </div>

                {/* Aliases */}
                {entity.metadata.alias && entity.metadata.alias.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap items-center gap-1 text-xs text-[#64748B]">
                    <span className="text-[#94A3B8]">Aliases:</span>
                    {entity.metadata.alias.slice(0, 3).map((a, i) => (
                      <span key={i} className="rounded bg-[#F1F5F9] px-1.5 py-0.5 border border-[#E2E8F0] text-[#0F172A]">
                        "{a}"
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
