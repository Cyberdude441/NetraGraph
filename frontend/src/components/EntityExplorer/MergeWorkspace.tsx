import React, { useState } from "react";
import {
  GitMerge,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  UserCheck,
  Layers,
  History,
  Sparkles,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import type { ComprehensiveEntity } from "@/data/syntheticEntities";
import { mergeEntityProfiles, type AuditLogEntry } from "@/utils/entityResolver";

interface MergeWorkspaceProps {
  entityA: ComprehensiveEntity;
  entityB: ComprehensiveEntity;
  onMergeComplete: (merged: ComprehensiveEntity, audit: AuditLogEntry) => void;
  onCancel: () => void;
}

export function MergeWorkspace({
  entityA,
  entityB,
  onMergeComplete,
  onCancel,
}: MergeWorkspaceProps) {
  const [primaryId, setPrimaryId] = useState<string>(entityA.id);
  const [analystName, setAnalystName] = useState<string>("Insp. D. Bose");
  const [mergeNotes, setMergeNotes] = useState<string>(
    "Corroborated identity via matched CDR IMEI logs and Aadhaar e-KYC forgery evidence."
  );

  const primary = primaryId === entityA.id ? entityA : entityB;
  const secondary = primaryId === entityA.id ? entityB : entityA;

  const handleExecuteMerge = () => {
    const { mergedEntity, auditEntry } = mergeEntityProfiles(primary, secondary, {
      userName: analystName,
      userRole: "Inspector / Senior Analyst",
    });

    toast.success("Identity Records Consolidated", {
      description: `Unified profile ${mergedEntity.id} (${mergedEntity.name}) generated with audit log entry.`,
    });

    onMergeComplete(mergedEntity, auditEntry);
  };

  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
        <div className="flex items-center gap-2">
          <GitMerge className="size-4 text-purple-400" />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-900">
              Identity Merge & Profile Consolidation Workspace
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">
              Consolidating: <strong>{entityA.name}</strong> + <strong>{entityB.name}</strong>
            </span>
          </div>
        </div>

        <button
          onClick={onCancel}
          className="text-slate-400 hover:text-slate-800 p-1 rounded cursor-pointer"
        >
          <X className="size-4" />
        </button>
      </div>

      {/* Before / After Consolidation Banner */}
      <div className="rounded border border-[#E2E8F0] bg-white p-3 flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
        <div className="flex items-center gap-2">
          <span className="rounded bg-slate-100 px-2 py-0.5 text-slate-700 font-bold">
            CURRENT: 2 Separate Entities
          </span>
          <ArrowRight className="size-3.5 text-slate-500" />
          <span className="rounded bg-purple-950/60 border border-purple-800 text-purple-300 font-bold px-2 py-0.5">
            MERGED: 1 Unified Dossier
          </span>
        </div>

        <span className="text-[10px] text-emerald-400 flex items-center gap-1 font-bold">
          <ShieldCheck className="size-3.5" /> Full Audit Trail Preserved
        </span>
      </div>

      {/* 1. Primary Profile Selection */}
      <div className="space-y-2">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
          Step 1: Designate Master Primary Profile (Target of Consolidation)
        </label>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[entityA, entityB].map((ent) => {
            const isPrimary = primaryId === ent.id;
            return (
              <div
                key={ent.id}
                onClick={() => setPrimaryId(ent.id)}
                className={cn(
                  "rounded-lg border p-3 transition-all cursor-pointer",
                  isPrimary
                    ? "border-emerald-500 bg-emerald-50 shadow-md ring-1 ring-emerald-400/50"
                    : "border-[#E2E8F0] bg-[#10161E] hover:border-slate-300"
                )}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-slate-900 text-xs uppercase">
                    {ent.name}
                  </span>
                  <span
                    className={cn(
                      "font-mono text-[9px] font-bold px-1.5 py-0.5 rounded border",
                      isPrimary
                        ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                        : "bg-slate-100 text-slate-400 border-slate-300"
                    )}
                  >
                    {isPrimary ? "PRIMARY MASTER" : "SECONDARY MERGE CANDIDATE"}
                  </span>
                </div>

                <p className="text-[10px] font-mono text-slate-400">
                  ID: {ent.id} · Risk: {ent.riskScore} · Connections: {ent.degreeCount || 1}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. Unified Preview Breakdown */}
      <div className="rounded border border-[#E2E8F0] bg-white p-3 space-y-2 font-mono text-[11px]">
        <span className="text-[10px] uppercase font-bold text-slate-400 block">
          Step 2: Unified Dossier Attributes Preview
        </span>

        <div className="space-y-1.5 text-slate-700">
          <div className="flex items-center justify-between border-b border-[#E2E8F0]/80 pb-1">
            <span className="text-slate-500">Consolidated Name:</span>
            <strong className="text-slate-900">{primary.name}</strong>
          </div>
          <div className="flex items-center justify-between border-b border-[#E2E8F0]/80 py-1">
            <span className="text-slate-500">Unified Aliases List:</span>
            <span className="text-amber-300 truncate max-w-[280px]">
              {Array.from(new Set([...(primary.metadata.alias || []), secondary.name, ...(secondary.metadata.alias || [])])).join(", ")}
            </span>
          </div>
          <div className="flex items-center justify-between border-b border-[#E2E8F0]/80 py-1">
            <span className="text-slate-500">Unified Chronological Events:</span>
            <span className="text-emerald-300 font-bold">
              {primary.timeline.length + secondary.timeline.length + 1} Total Forensic Events
            </span>
          </div>
          <div className="flex items-center justify-between py-1">
            <span className="text-slate-500">Recalibrated Risk Score:</span>
            <span className="text-red-400 font-bold">
              {Math.max(primary.riskScore, secondary.riskScore)}/100 (Max-Bound Weighted)
            </span>
          </div>
        </div>
      </div>

      {/* 3. Analyst Verification & Authorization Signature */}
      <div className="space-y-2 rounded border border-[#E2E8F0] bg-white p-3">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
          Step 3: Forensic Authorization & Audit Memo
        </label>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div>
            <span className="text-[9px] font-mono text-slate-500 block mb-1">
              Authorizing Officer:
            </span>
            <input
              type="text"
              value={analystName}
              onChange={(e) => setAnalystName(e.target.value)}
              className="w-full rounded border border-[#E2E8F0] bg-[#F8FAFC] px-2.5 py-1 text-xs text-slate-800 font-mono outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <span className="text-[9px] font-mono text-slate-500 block mb-1">
              Case Docket Reference:
            </span>
            <input
              type="text"
              readOnly
              value={primary.caseId}
              className="w-full rounded border border-[#E2E8F0] bg-[#F8FAFC] px-2.5 py-1 text-xs text-emerald-300 font-mono outline-none"
            />
          </div>
        </div>

        <div>
          <span className="text-[9px] font-mono text-slate-500 block mb-1">
            Reason for Consolidation:
          </span>
          <textarea
            rows={2}
            value={mergeNotes}
            onChange={(e) => setMergeNotes(e.target.value)}
            className="w-full rounded border border-[#E2E8F0] bg-[#F8FAFC] p-2 text-xs text-slate-800 font-mono outline-none focus:border-emerald-500"
          />
        </div>
      </div>

      {/* Execution Footer */}
      <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
        <button
          onClick={onCancel}
          className="rounded border border-[#E2E8F0] bg-[#F8FAFC] px-3.5 py-1.5 text-xs font-mono text-slate-400 hover:text-slate-800 cursor-pointer"
        >
          Cancel
        </button>
        <button
          onClick={handleExecuteMerge}
          className="flex items-center gap-1.5 rounded border border-purple-500/60 bg-purple-950/60 px-5 py-2 text-xs font-mono font-bold text-purple-200 hover:bg-purple-900/80 transition-all cursor-pointer shadow-lg"
        >
          <UserCheck className="size-4" />
          <span>Confirm & Execute Profile Consolidation</span>
        </button>
      </div>
    </div>
  );
}
