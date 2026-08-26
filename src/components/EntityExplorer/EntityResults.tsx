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
    <div className="flex-1 flex flex-col h-full overflow-hidden select-none bg-[#0B0F14]">
      {/* Top Results Control Bar */}
      <div className="border-b border-slate-800 bg-[#121820] px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 font-mono">
          <span className="text-slate-400">Indexed Matches:</span>
          <span className="font-bold text-sky-400">{results.length} Entities</span>
          {compareIds.size > 0 && (
            <span className="rounded bg-amber-950/40 border border-amber-800/60 px-2 py-0.5 text-[10px] text-amber-300">
              {compareIds.size} Selected for Comparison
            </span>
          )}
        </div>

        {/* Sort Controls */}
        <div className="flex items-center gap-1.5 font-mono text-[11px]">
          <ArrowUpDown className="size-3 text-slate-400" />
          <span className="text-slate-400">Sort By:</span>
          <select
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value as any)}
            className="rounded border border-slate-800 bg-[#161D24] px-2 py-1 text-xs text-sky-300 outline-none cursor-pointer"
          >
            <option value="risk">Risk Severity Score</option>
            <option value="confidence">Evidence Confidence</option>
            <option value="rank">Network Influence Rank</option>
            <option value="activity">Recent Activity Date</option>
            <option value="name">Alphabetical (A-Z)</option>
          </select>
        </div>
      </div>

      {/* Results List */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-2.5 custom-scrollbar">
        {sorted.length === 0 ? (
          <div className="rounded border border-dashed border-slate-800 p-8 text-center text-slate-500 font-mono text-xs">
            No criminal entities or dockets match the active search criteria.
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
                  "rounded-lg border p-3 transition-all cursor-pointer relative",
                  isSelected
                    ? "border-sky-500 bg-[#14202C] shadow-lg ring-1 ring-sky-400/50"
                    : "border-slate-800 bg-[#10161E] hover:border-slate-700 hover:bg-[#131A24]"
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
                      className="mt-0.5 text-slate-400 hover:text-sky-400 transition-colors cursor-pointer"
                      title="Select for comparative analysis"
                    >
                      {isComparing ? (
                        <CheckSquare className="size-4 text-sky-400" />
                      ) : (
                        <Square className="size-4 text-slate-600" />
                      )}
                    </button>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-sans text-xs font-bold text-slate-100 uppercase tracking-wide truncate">
                          {entity.name}
                        </h3>

                        {/* AI-Assisted Similarity Match Tag */}
                        {isSimilarityMatch && (
                          <span className="flex items-center gap-1 rounded bg-purple-950/60 border border-purple-800/80 px-1.5 py-0.2 font-mono text-[9px] font-bold text-purple-300">
                            <Sparkles className="size-2.5 text-purple-400" /> AI Similarity ({matchScore}%)
                          </span>
                        )}

                        {/* Duplicate Alert Pill */}
                        {duplicateCount > 0 && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onOpenResolutionMatrix(entity);
                            }}
                            className="rounded bg-amber-950/40 border border-amber-800/60 px-1.5 py-0.2 font-mono text-[9px] font-bold text-amber-300 hover:border-amber-400 transition-colors"
                          >
                            Potential Duplicate Exists
                          </button>
                        )}
                      </div>

                      <p className="mt-0.5 text-[10px] font-mono text-slate-400 truncate">
                        ID: <span className="text-slate-300 font-semibold">{entity.id}</span> · {entity.role || entity.label} · {entity.metadata.jurisdiction || "National Cyber Cell"}
                      </p>
                    </div>
                  </div>

                  {/* Risk Score Pill */}
                  <div className="shrink-0 flex items-center gap-1.5">
                    <span
                      className={cn(
                        "flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[10px] font-bold",
                        risk >= 85
                          ? "bg-red-950/80 text-red-300 border border-red-500/60"
                          : risk >= 70
                          ? "bg-amber-950/80 text-amber-300 border border-amber-500/50"
                          : "bg-slate-800 text-slate-300 border border-slate-700"
                      )}
                    >
                      {risk >= 85 && <Flame className="size-2.5 text-red-400 animate-pulse" />}
                      Risk {risk}
                    </span>
                  </div>
                </div>

                {/* Metrics HUD Line */}
                <div className="mt-2.5 grid grid-cols-2 sm:grid-cols-4 gap-2 border-t border-slate-800/80 pt-2 text-[10px] font-mono text-slate-400">
                  <div>
                    <span className="text-slate-500">TYPE: </span>
                    <strong className="text-slate-200">{entity.label}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500">CONFIDENCE: </span>
                    <strong className="text-emerald-400">{(entity.confidenceScore * 100).toFixed(0)}%</strong>
                  </div>
                  <div>
                    <span className="text-slate-500">LINKS: </span>
                    <strong className="text-sky-300">{entity.degreeCount || entity.relationshipsCount || 1} Connected</strong>
                  </div>
                  <div>
                    <span className="text-slate-500">LAST SEEN: </span>
                    <strong className="text-slate-300">{entity.lastSeen}</strong>
                  </div>
                </div>

                {/* Aliases & Tags */}
                {entity.metadata.alias && entity.metadata.alias.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap items-center gap-1 text-[9px] font-mono text-slate-400">
                    <span className="text-slate-500">Aliases:</span>
                    {entity.metadata.alias.slice(0, 3).map((a, i) => (
                      <span key={i} className="rounded bg-[#161D24] px-1.5 py-0.5 border border-slate-800 text-slate-300">
                        "{a}"
                      </span>
                    ))}
                    {entity.metadata.alias.length > 3 && (
                      <span className="text-slate-500">+{entity.metadata.alias.length - 3} more</span>
                    )}
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
