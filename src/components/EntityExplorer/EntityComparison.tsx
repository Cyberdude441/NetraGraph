import React from "react";
import {
  ArrowRightLeft,
  Users,
  ShieldAlert,
  Flame,
  TrendingUp,
  MapPin,
  Building2,
  Calendar,
  X,
  Share2,
  GitMerge,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ComprehensiveEntity } from "@/data/syntheticEntities";

interface EntityComparisonProps {
  entities: ComprehensiveEntity[];
  onRemoveEntity: (id: string) => void;
  onOpenResolution: (a: ComprehensiveEntity, b: ComprehensiveEntity) => void;
  onClose: () => void;
}

export function EntityComparison({
  entities,
  onRemoveEntity,
  onOpenResolution,
  onClose,
}: EntityComparisonProps) {
  if (entities.length === 0) return null;

  const entityA = entities[0];
  const entityB = entities[1];

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <ArrowRightLeft className="size-4 text-sky-400" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
            Multi-Entity Comparative Intelligence Matrix ({entities.length} Profiles)
          </span>
        </div>

        <div className="flex items-center gap-2">
          {entityA && entityB && (
            <button
              onClick={() => onOpenResolution(entityA, entityB)}
              className="flex items-center gap-1.5 rounded border border-purple-500/50 bg-purple-950/40 px-2.5 py-1 text-[11px] font-mono font-bold text-purple-300 hover:bg-purple-900/50 transition-colors cursor-pointer"
            >
              <GitMerge className="size-3" /> Check Duplicate Resolution
            </button>
          )}
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded cursor-pointer"
          >
            <X className="size-4" />
          </button>
        </div>
      </div>

      {/* Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {entities.map((ent) => {
          const risk = ent.riskScore;
          const isHigh = risk >= 85;

          return (
            <div
              key={ent.id}
              className="rounded-lg border border-slate-800 bg-[#121820] p-3 space-y-3 relative"
            >
              <button
                onClick={() => onRemoveEntity(ent.id)}
                className="absolute top-2.5 right-2.5 text-slate-500 hover:text-slate-200 p-0.5 rounded cursor-pointer"
                title="Remove from comparison"
              >
                <X className="size-3.5" />
              </button>

              {/* Title & Role */}
              <div className="pr-6">
                <h3 className="font-sans text-xs font-bold text-slate-100 uppercase tracking-wide truncate">
                  {ent.name}
                </h3>
                <span className="text-[10px] font-mono text-slate-400 truncate block">
                  {ent.id} · {ent.role || ent.label}
                </span>
              </div>

              {/* Threat Pill */}
              <div className="flex items-center justify-between border-t border-b border-slate-800/80 py-1.5 font-mono text-[11px]">
                <span className="text-slate-500">Risk Score:</span>
                <span
                  className={cn(
                    "font-bold flex items-center gap-1",
                    isHigh ? "text-red-400" : risk >= 70 ? "text-amber-400" : "text-slate-300"
                  )}
                >
                  {isHigh && <Flame className="size-2.5 text-red-400 animate-pulse" />}
                  {risk}/100
                </span>
              </div>

              {/* Technical Metrics Table */}
              <div className="space-y-1.5 font-mono text-[11px]">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Type:</span>
                  <strong className="text-slate-200">{ent.label}</strong>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Confidence:</span>
                  <span className="text-emerald-400 font-bold">{(ent.confidenceScore * 100).toFixed(0)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Centrality Rank:</span>
                  <span className="text-amber-400 font-bold">#{ent.centralityRank || "—"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">PageRank:</span>
                  <span className="text-sky-400">{ent.pageRankScore ? `${ent.pageRankScore}%` : "—"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Betweenness:</span>
                  <span className="text-emerald-400">{ent.betweennessScore ? `${ent.betweennessScore}%` : "—"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Connected Links:</span>
                  <span className="text-slate-200 font-bold">{ent.degreeCount || 1}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Jurisdiction:</span>
                  <span className="text-slate-300 truncate max-w-[150px]">{ent.metadata.jurisdiction || "—"}</span>
                </div>
              </div>

              {/* Aliases */}
              {ent.metadata.alias && ent.metadata.alias.length > 0 && (
                <div className="border-t border-slate-800/80 pt-1.5 text-[10px] font-mono">
                  <span className="text-slate-500 block mb-1">Aliases:</span>
                  <div className="flex flex-wrap gap-1">
                    {ent.metadata.alias.map((a, i) => (
                      <span key={i} className="rounded bg-[#161D24] px-1.5 py-0.5 text-slate-300 border border-slate-800">
                        "{a}"
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
