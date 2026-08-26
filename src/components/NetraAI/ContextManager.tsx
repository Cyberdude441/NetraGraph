import React from "react";
import { FolderSearch, Users, Pin, Activity, Sparkles, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ContextManagerProps {
  activeCaseId: string;
  onSelectCase: (caseId: string) => void;
  pinnedEntities: { id: string; name: string }[];
  onRemovePinnedEntity: (id: string) => void;
  focusArea: string;
  onSelectFocusArea: (area: string) => void;
}

export function ContextManager({
  activeCaseId,
  onSelectCase,
  pinnedEntities,
  onRemovePinnedEntity,
  focusArea,
  onSelectFocusArea,
}: ContextManagerProps) {
  return (
    <div className="space-y-4 text-xs font-sans select-none">
      {/* 1. Active Case Context */}
      <div className="rounded border border-slate-800 bg-[#121820] p-3 space-y-1.5">
        <label className="text-[10px] font-mono uppercase font-bold text-slate-400 block flex items-center gap-1">
          <FolderSearch className="size-3 text-sky-400" /> Active Investigation Docket
        </label>
        <select
          value={activeCaseId}
          onChange={(e) => onSelectCase(e.target.value)}
          className="w-full rounded border border-slate-800 bg-[#161D24] px-2 py-1 text-xs text-sky-300 font-mono outline-none cursor-pointer"
        >
          <option value="CASE-2026-N09">CASE-2026-N09 (Noida Tech Support Scam)</option>
          <option value="CASE-2026-B12">CASE-2026-B12 (Bhubaneswar SIM Box Ring)</option>
          <option value="CASE-2026-R44">CASE-2026-R44 (LockNet Ransomware Group)</option>
          <option value="CASE-2026-H88">CASE-2026-H88 (Inter-State Hawala Conduits)</option>
        </select>
      </div>

      {/* 2. Pinned Suspect Targets */}
      <div className="rounded border border-slate-800 bg-[#121820] p-3 space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-[10px] font-mono uppercase font-bold text-slate-400 flex items-center gap-1">
            <Pin className="size-3 text-amber-400" /> Pinned Working Targets
          </label>
          <span className="text-[9px] font-mono text-slate-500">{pinnedEntities.length} Pinned</span>
        </div>

        <div className="space-y-1 font-mono text-[11px]">
          {pinnedEntities.map((ent) => (
            <div
              key={ent.id}
              className="rounded bg-[#161D24] px-2 py-1 border border-slate-800 flex items-center justify-between"
            >
              <span className="text-slate-200 truncate">{ent.name}</span>
              <button
                onClick={() => onRemovePinnedEntity(ent.id)}
                className="text-slate-500 hover:text-slate-200 cursor-pointer"
              >
                <X className="size-3" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Focus Scope Filter */}
      <div className="rounded border border-slate-800 bg-[#121820] p-3 space-y-1.5 font-mono text-[10px]">
        <label className="text-[10px] uppercase font-bold text-slate-400 block flex items-center gap-1">
          <Activity className="size-3 text-purple-400" /> Analysis Focus Area
        </label>
        <div className="grid grid-cols-2 gap-1">
          {["All Telemetry", "Fund Transfers", "Call Records", "Burner Devices"].map((f) => {
            const active = focusArea === f;
            return (
              <button
                key={f}
                onClick={() => onSelectFocusArea(f)}
                className={cn(
                  "rounded border py-1 text-left px-2 transition-all cursor-pointer truncate",
                  active
                    ? "border-purple-500/50 bg-[#1A202A] text-purple-300 font-bold"
                    : "border-slate-800 bg-[#141A21] text-slate-500"
                )}
              >
                {f}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
