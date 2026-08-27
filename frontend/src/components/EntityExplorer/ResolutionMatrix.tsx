import React from "react";
import {
  Sparkles,
  GitMerge,
  ShieldAlert,
  ShieldCheck,
  Flame,
  ArrowRight,
  Info,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ComprehensiveEntity } from "@/data/syntheticEntities";
import { calculateResolutionMatrix, type MatchBreakdown } from "@/utils/similarityScore";

interface ResolutionMatrixProps {
  entityA: ComprehensiveEntity;
  entityB: ComprehensiveEntity;
  onOpenMerge: (a: ComprehensiveEntity, b: ComprehensiveEntity) => void;
  onClose?: () => void;
}

export function ResolutionMatrix({
  entityA,
  entityB,
  onOpenMerge,
  onClose,
}: ResolutionMatrixProps) {
  const matrix: MatchBreakdown = calculateResolutionMatrix(entityA, entityB);

  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-4 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="size-4 text-purple-400" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-900">
            Entity Resolution & Identity Matching Matrix
          </span>
        </div>

        <span
          className={cn(
            "rounded px-2.5 py-1 font-mono text-[11px] font-bold border",
            matrix.overallConfidence >= 90
              ? "bg-emerald-950/80 text-emerald-300 border-emerald-500/60"
              : matrix.overallConfidence >= 70
              ? "bg-amber-950/80 text-amber-300 border-amber-500/50"
              : "bg-slate-100 text-slate-700 border-slate-300"
          )}
        >
          {matrix.confidenceCategory}: {matrix.overallConfidence}% Match
        </span>
      </div>

      {/* Side-by-Side Comparison Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Record A */}
        <div className="rounded border border-[#E2E8F0] bg-white p-3 space-y-2">
          <div className="flex items-center justify-between border-b border-[#E2E8F0]/80 pb-1.5">
            <span className="text-[10px] font-mono uppercase font-bold text-emerald-400">
              Record A (Primary / Baseline)
            </span>
            <span className="font-mono text-[10px] text-slate-400">{entityA.id}</span>
          </div>

          <div className="space-y-1 font-mono text-[11px]">
            <div>
              <span className="text-slate-500">Name: </span>
              <strong className="text-slate-900">{entityA.name}</strong>
            </div>
            <div>
              <span className="text-slate-500">Role: </span>
              <span className="text-slate-700">{entityA.role || entityA.label}</span>
            </div>
            <div>
              <span className="text-slate-500">Jurisdiction: </span>
              <span className="text-slate-700">{entityA.metadata.jurisdiction || "—"}</span>
            </div>
            <div>
              <span className="text-slate-500">Aliases: </span>
              <span className="text-amber-300">
                {(entityA.metadata.alias || []).join(", ") || "None"}
              </span>
            </div>
          </div>
        </div>

        {/* Record B */}
        <div className="rounded border border-[#E2E8F0] bg-white p-3 space-y-2">
          <div className="flex items-center justify-between border-b border-[#E2E8F0]/80 pb-1.5">
            <span className="text-[10px] font-mono uppercase font-bold text-purple-400">
              Record B (Candidate Record)
            </span>
            <span className="font-mono text-[10px] text-slate-400">{entityB.id}</span>
          </div>

          <div className="space-y-1 font-mono text-[11px]">
            <div>
              <span className="text-slate-500">Name: </span>
              <strong className="text-slate-900">{entityB.name}</strong>
            </div>
            <div>
              <span className="text-slate-500">Role: </span>
              <span className="text-slate-700">{entityB.role || entityB.label}</span>
            </div>
            <div>
              <span className="text-slate-500">Jurisdiction: </span>
              <span className="text-slate-700">{entityB.metadata.jurisdiction || "—"}</span>
            </div>
            <div>
              <span className="text-slate-500">Aliases: </span>
              <span className="text-amber-300">
                {(entityB.metadata.alias || []).join(", ") || "None"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Confidence Matrix Score Breakdown */}
      <div className="rounded border border-[#E2E8F0] bg-[#F8FAFC] p-3 space-y-2.5">
        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
          Attribute Resolution Breakdown
        </span>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px]">
          <div className="rounded bg-[#F8FAFC] p-2 border border-[#E2E8F0]">
            <span className="text-[9px] text-slate-500 block">NAME SIMILARITY</span>
            <span className="text-sm font-bold text-emerald-400">{matrix.nameSimilarity}%</span>
          </div>
          <div className="rounded bg-[#F8FAFC] p-2 border border-[#E2E8F0]">
            <span className="text-[9px] text-slate-500 block">IDENTIFIERS / IMEI</span>
            <span className="text-sm font-bold text-emerald-400">{matrix.sharedIdentifiers}%</span>
          </div>
          <div className="rounded bg-[#F8FAFC] p-2 border border-[#E2E8F0]">
            <span className="text-[9px] text-slate-500 block">LOCATION CORRELATION</span>
            <span className="text-sm font-bold text-amber-400">{matrix.locationCorrelation}%</span>
          </div>
          <div className="rounded bg-[#F8FAFC] p-2 border border-[#E2E8F0]">
            <span className="text-[9px] text-slate-500 block">NETWORK OVERLAP</span>
            <span className="text-sm font-bold text-purple-400">{matrix.relationshipOverlap}%</span>
          </div>
        </div>

        {/* Explainability Reasons */}
        <div className="pt-2 border-t border-[#E2E8F0]/80 space-y-1">
          <span className="text-[9px] font-mono text-slate-400 uppercase font-bold block">
            Resolution Signals Detected:
          </span>
          {matrix.reasons.map((r, i) => (
            <div key={i} className="flex items-center gap-1.5 text-[11px] text-slate-700">
              <CheckCircle2 className="size-3 text-emerald-400 shrink-0" />
              <span>{r}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Governance & Disclaimer Notice */}
      <div className="rounded border border-amber-900/60 bg-amber-950/20 p-2.5 text-[10px] font-mono text-amber-300 flex items-start gap-2">
        <AlertTriangle className="size-3.5 shrink-0 mt-0.5" />
        <div>
          <strong>Strict Governance Disclaimer:</strong> AI-generated similarity recommendation. Analyst verification and Section 65B corroboration required prior to profile consolidation.
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
        {onClose && (
          <button
            onClick={onClose}
            className="rounded border border-[#E2E8F0] bg-[#F8FAFC] px-3 py-1.5 text-xs font-mono text-slate-400 hover:text-slate-800 cursor-pointer"
          >
            Cancel
          </button>
        )}
        <button
          onClick={() => onOpenMerge(entityA, entityB)}
          className="flex items-center gap-1.5 rounded border border-purple-500/50 bg-purple-950/50 px-4 py-1.5 text-xs font-mono font-bold text-purple-200 hover:bg-purple-900/60 transition-all cursor-pointer shadow-md"
        >
          <GitMerge className="size-3.5" />
          <span>Open Identity Merge Workspace</span>
        </button>
      </div>
    </div>
  );
}
