import React from "react";
import {
  Layers,
  ShieldAlert,
  ShieldCheck,
  Activity,
  Users,
  RotateCcw,
  CheckSquare,
  Square,
  Flame,
  User,
  Smartphone,
  Cpu,
  MapPin,
  Car,
  Building2,
  CreditCard,
  CalendarDays,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { EntityFilterState } from "@/utils/entityMatching";
import { DEFAULT_ENTITY_FILTERS } from "@/utils/entityMatching";

interface EntityFiltersProps {
  filters: EntityFilterState;
  onFilterChange: (updater: (prev: EntityFilterState) => EntityFilterState) => void;
  onReset: () => void;
  networkGroupOptions: string[];
}

const TYPE_ICONS: Record<string, React.ElementType> = {
  Person: User,
  Phone: Smartphone,
  Device: Cpu,
  Location: MapPin,
  Vehicle: Car,
  Organization: Building2,
  BankAccount: CreditCard,
  Event: CalendarDays,
};

export function EntityFilters({
  filters,
  onFilterChange,
  onReset,
  networkGroupOptions,
}: EntityFiltersProps) {
  const toggleType = (type: string) => {
    onFilterChange((prev) => {
      const next = new Set(prev.entityTypes);
      if (next.has(type)) {
        if (next.size > 1) next.delete(type);
      } else {
        next.add(type);
      }
      return { ...prev, entityTypes: next };
    });
  };

  const toggleRisk = (risk: "Critical" | "High" | "Medium" | "Low") => {
    onFilterChange((prev) => {
      const next = new Set(prev.riskLevels);
      if (next.has(risk)) {
        if (next.size > 1) next.delete(risk);
      } else {
        next.add(risk);
      }
      return { ...prev, riskLevels: next };
    });
  };

  const toggleConfidence = (conf: "Verified" | "High Confidence" | "Probable" | "Unknown") => {
    onFilterChange((prev) => {
      const next = new Set(prev.confidenceLevels);
      if (next.has(conf)) {
        if (next.size > 1) next.delete(conf);
      } else {
        next.add(conf);
      }
      return { ...prev, confidenceLevels: next };
    });
  };

  const toggleActivity = (act: "Recent" | "Historical" | "Dormant") => {
    onFilterChange((prev) => {
      const next = new Set(prev.activityStatuses);
      if (next.has(act)) {
        if (next.size > 1) next.delete(act);
      } else {
        next.add(act);
      }
      return { ...prev, activityStatuses: next };
    });
  };

  return (
    <div className="space-y-4 text-xs select-none">
      {/* 1. Entity Classification */}
      <div className="rounded border border-slate-800/80 bg-[#121922] p-2.5 space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
            <Layers className="size-3 text-sky-400" /> Entity Classification
          </label>
          <button
            onClick={() =>
              onFilterChange((prev) => ({
                ...prev,
                entityTypes: new Set(DEFAULT_ENTITY_FILTERS.entityTypes),
              }))
            }
            className="text-[9px] font-mono text-sky-400 hover:underline cursor-pointer"
          >
            All
          </button>
        </div>

        <div className="grid grid-cols-2 gap-1">
          {Array.from(DEFAULT_ENTITY_FILTERS.entityTypes).map((type) => {
            const active = filters.entityTypes.has(type);
            const Icon = TYPE_ICONS[type] || User;
            return (
              <button
                key={type}
                onClick={() => toggleType(type)}
                className={cn(
                  "flex items-center gap-1.5 rounded border px-2 py-1 text-[10px] font-mono transition-all text-left cursor-pointer",
                  active
                    ? "border-sky-500/50 bg-[#1A2634] text-sky-200"
                    : "border-slate-800 bg-[#141A21] text-slate-500 hover:border-slate-700"
                )}
              >
                <Icon className={cn("size-3", active ? "text-sky-400" : "text-slate-600")} />
                <span className="truncate">{type}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. Risk Severity */}
      <div className="rounded border border-slate-800/80 bg-[#121922] p-2.5 space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
            <ShieldAlert className="size-3 text-red-400" /> Risk Severity Threshold
          </label>
          <span className="font-mono text-[10px] font-bold text-amber-400">
            {filters.minRisk}+
          </span>
        </div>

        <input
          type="range"
          min="0"
          max="95"
          step="5"
          value={filters.minRisk}
          onChange={(e) =>
            onFilterChange((prev) => ({ ...prev, minRisk: Number(e.target.value) }))
          }
          className="w-full accent-sky-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg appearance-none"
        />

        <div className="grid grid-cols-4 gap-1">
          {(["Low", "Medium", "High", "Critical"] as const).map((r) => {
            const active = filters.riskLevels.has(r);
            return (
              <button
                key={r}
                onClick={() => toggleRisk(r)}
                className={cn(
                  "rounded border py-0.5 text-center font-mono text-[9px] font-bold transition-all cursor-pointer",
                  active
                    ? r === "Critical"
                      ? "bg-red-950/40 text-red-300 border-red-500/50"
                      : r === "High"
                      ? "bg-amber-950/40 text-amber-300 border-amber-500/50"
                      : r === "Medium"
                      ? "bg-slate-800 text-slate-300 border-slate-600"
                      : "bg-emerald-950/40 text-emerald-300 border-emerald-500/50"
                    : "border-slate-800 bg-[#141A21] text-slate-600"
                )}
              >
                {r}
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Verification & Forensic Confidence */}
      <div className="rounded border border-slate-800/80 bg-[#121922] p-2.5 space-y-1.5">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
          <ShieldCheck className="size-3 text-emerald-400" /> Evidence Confidence
        </label>
        <div className="grid grid-cols-2 gap-1 font-mono text-[10px]">
          {(["Verified", "High Confidence", "Probable", "Unknown"] as const).map((c) => {
            const active = filters.confidenceLevels.has(c);
            return (
              <button
                key={c}
                onClick={() => toggleConfidence(c)}
                className={cn(
                  "rounded border px-2 py-1 text-left transition-all cursor-pointer truncate",
                  active
                    ? "border-emerald-500/40 bg-emerald-950/20 text-emerald-300"
                    : "border-slate-800 bg-[#141A21] text-slate-600"
                )}
              >
                {c}
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. Activity Recency */}
      <div className="rounded border border-slate-800/80 bg-[#121922] p-2.5 space-y-1.5">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
          <Activity className="size-3 text-sky-400" /> Activity Horizon
        </label>
        <div className="grid grid-cols-3 gap-1 font-mono text-[10px]">
          {(["Recent", "Historical", "Dormant"] as const).map((act) => {
            const active = filters.activityStatuses.has(act);
            return (
              <button
                key={act}
                onClick={() => toggleActivity(act)}
                className={cn(
                  "rounded border py-1 text-center transition-all cursor-pointer font-bold",
                  active
                    ? "border-sky-500/40 bg-sky-950/30 text-sky-300"
                    : "border-slate-800 bg-[#141A21] text-slate-600"
                )}
              >
                {act}
              </button>
            );
          })}
        </div>
      </div>

      {/* Reset Button */}
      <button
        onClick={onReset}
        className="w-full flex items-center justify-center gap-1.5 rounded border border-slate-800 bg-[#161D24] py-1.5 text-[11px] font-mono font-semibold text-slate-400 hover:text-sky-400 transition-colors cursor-pointer"
      >
        <RotateCcw className="size-3" />
        <span>Reset Filters to Baseline</span>
      </button>
    </div>
  );
}
