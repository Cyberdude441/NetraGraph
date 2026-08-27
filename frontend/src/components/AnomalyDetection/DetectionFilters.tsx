import React from "react";
import {
  Filter,
  ShieldAlert,
  Flame,
  Activity,
  CheckSquare,
  Square,
  RotateCcw,
  Layers,
  Sparkles,
  PhoneCall,
  CreditCard,
  Cpu,
  TrendingUp,
  MapPin,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { AnomalyCategory, AnomalySeverity, AnomalyStatus } from "@/utils/anomalyRules";

export interface AnomalyFilterState {
  searchQuery: string;
  categories: Set<AnomalyCategory>;
  severities: Set<AnomalySeverity>;
  statuses: Set<AnomalyStatus>;
  minConfidence: number;
}

export const DEFAULT_ANOMALY_FILTERS: AnomalyFilterState = {
  searchQuery: "",
  categories: new Set([
    "CIRCULAR_FINANCIAL_LOOP",
    "DEVICE_HOPPING",
    "COMMUNICATION_BURST",
    "NETWORK_EXPANSION_SURGE",
    "GEOSPATIAL_CO_LOCATION",
  ]),
  severities: new Set(["CRITICAL", "HIGH", "MEDIUM", "LOW"]),
  statuses: new Set(["DETECTED", "UNDER_REVIEW", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"]),
  minConfidence: 0,
};

interface DetectionFiltersProps {
  filters: AnomalyFilterState;
  onFilterChange: (updater: (prev: AnomalyFilterState) => AnomalyFilterState) => void;
  onReset: () => void;
}

const CATEGORY_META: Record<
  AnomalyCategory,
  { label: string; icon: React.ElementType }
> = {
  CIRCULAR_FINANCIAL_LOOP: { label: "Circular Financial Loops", icon: CreditCard },
  DEVICE_HOPPING: { label: "Burner / Device Hopping", icon: Cpu },
  COMMUNICATION_BURST: { label: "Call Volume Spikes", icon: PhoneCall },
  NETWORK_EXPANSION_SURGE: { label: "Network Growth Surges", icon: TrendingUp },
  GEOSPATIAL_CO_LOCATION: { label: "Geospatial Co-Location", icon: MapPin },
};

export function DetectionFilters({
  filters,
  onFilterChange,
  onReset,
}: DetectionFiltersProps) {
  const toggleCategory = (cat: AnomalyCategory) => {
    onFilterChange((prev) => {
      const next = new Set(prev.categories);
      if (next.has(cat)) {
        if (next.size > 1) next.delete(cat);
      } else {
        next.add(cat);
      }
      return { ...prev, categories: next };
    });
  };

  const toggleSeverity = (sev: AnomalySeverity) => {
    onFilterChange((prev) => {
      const next = new Set(prev.severities);
      if (next.has(sev)) {
        if (next.size > 1) next.delete(sev);
      } else {
        next.add(sev);
      }
      return { ...prev, severities: next };
    });
  };

  const toggleStatus = (st: AnomalyStatus) => {
    onFilterChange((prev) => {
      const next = new Set(prev.statuses);
      if (next.has(st)) {
        if (next.size > 1) next.delete(st);
      } else {
        next.add(st);
      }
      return { ...prev, statuses: next };
    });
  };

  return (
    <div className="space-y-4 text-xs select-none font-sans">
      {/* 1. Anomaly Categories */}
      <div className="rounded border border-[#E2E8F0]/80 bg-white p-3 space-y-2">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
          <Layers className="size-3 text-emerald-400" /> Behavioral Pattern Category
        </label>

        <div className="space-y-1">
          {(Object.keys(CATEGORY_META) as AnomalyCategory[]).map((cat) => {
            const active = filters.categories.has(cat);
            const meta = CATEGORY_META[cat];
            const Icon = meta.icon;

            return (
              <button
                key={cat}
                onClick={() => toggleCategory(cat)}
                className={cn(
                  "w-full flex items-center gap-2 rounded border px-2 py-1.5 text-[11px] font-mono transition-all text-left cursor-pointer",
                  active
                    ? "border-emerald-500/50 bg-emerald-50 text-emerald-200"
                    : "border-[#E2E8F0] bg-[#F8FAFC] text-slate-500 hover:border-slate-300"
                )}
              >
                <Icon className={cn("size-3.5", active ? "text-emerald-400" : "text-slate-600")} />
                <span className="truncate">{meta.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. Severity Tier */}
      <div className="rounded border border-[#E2E8F0]/80 bg-white p-3 space-y-2">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
          <ShieldAlert className="size-3 text-red-400" /> Alert Severity Filter
        </label>

        <div className="grid grid-cols-2 gap-1 font-mono text-[10px]">
          {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((sev) => {
            const active = filters.severities.has(sev);
            return (
              <button
                key={sev}
                onClick={() => toggleSeverity(sev)}
                className={cn(
                  "rounded border py-1 text-center font-bold transition-all cursor-pointer",
                  active
                    ? sev === "CRITICAL"
                      ? "bg-red-950/60 text-red-300 border-red-500/60"
                      : sev === "HIGH"
                      ? "bg-amber-950/60 text-amber-300 border-amber-500/60"
                      : sev === "MEDIUM"
                      ? "bg-emerald-950/60 text-emerald-300 border-emerald-500/60"
                      : "bg-slate-100 text-slate-700 border-slate-300"
                    : "border-[#E2E8F0] bg-[#F8FAFC] text-slate-600"
                )}
              >
                {sev}
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Investigation Status */}
      <div className="rounded border border-[#E2E8F0]/80 bg-white p-3 space-y-2">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
          <Activity className="size-3 text-emerald-400" /> Lifecycle Status
        </label>

        <div className="grid grid-cols-2 gap-1 font-mono text-[10px]">
          {(["DETECTED", "UNDER_REVIEW", "INVESTIGATING", "RESOLVED"] as const).map((st) => {
            const active = filters.statuses.has(st);
            return (
              <button
                key={st}
                onClick={() => toggleStatus(st)}
                className={cn(
                  "rounded border px-2 py-1 text-left transition-all cursor-pointer truncate",
                  active
                    ? "border-emerald-500/40 bg-emerald-950/20 text-emerald-300"
                    : "border-[#E2E8F0] bg-[#F8FAFC] text-slate-600"
                )}
              >
                {st.replace("_", " ")}
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. Confidence Threshold Slider */}
      <div className="rounded border border-[#E2E8F0]/80 bg-white p-3 space-y-2">
        <div className="flex items-center justify-between font-mono text-[10px]">
          <span className="uppercase text-slate-400 font-bold">Min Confidence</span>
          <span className="text-amber-400 font-bold">{filters.minConfidence}%+</span>
        </div>
        <input
          type="range"
          min="0"
          max="95"
          step="5"
          value={filters.minConfidence}
          onChange={(e) =>
            onFilterChange((prev) => ({ ...prev, minConfidence: Number(e.target.value) }))
          }
          className="w-full accent-emerald-500 cursor-pointer h-1.5 bg-slate-100 rounded-lg appearance-none"
        />
      </div>

      {/* Reset */}
      <button
        onClick={onReset}
        className="w-full flex items-center justify-center gap-1.5 rounded border border-[#E2E8F0] bg-[#F8FAFC] py-1.5 text-[11px] font-mono font-semibold text-slate-400 hover:text-emerald-400 transition-colors cursor-pointer"
      >
        <RotateCcw className="size-3" />
        <span>Reset Detection Filters</span>
      </button>
    </div>
  );
}
