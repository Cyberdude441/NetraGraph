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
      <div className="rounded-md border border-[#D9E2EC] bg-white p-3 space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-[#0F172A] flex items-center gap-1.5">
            <Layers className="size-3.5 text-[#065F46]" /> Entity Classification
          </label>
          <button
            onClick={() =>
              onFilterChange((prev) => ({
                ...prev,
                entityTypes: new Set(DEFAULT_ENTITY_FILTERS.entityTypes),
              }))
            }
            className="text-xs text-[#065F46] font-semibold hover:underline cursor-pointer"
          >
            Select All
          </button>
        </div>

        <div className="grid grid-cols-2 gap-1.5">
          {Array.from(DEFAULT_ENTITY_FILTERS.entityTypes).map((type) => {
            const active = filters.entityTypes.has(type);
            const Icon = TYPE_ICONS[type] || User;
            return (
              <button
                key={type}
                onClick={() => toggleType(type)}
                className={cn(
                  "flex items-center gap-1.5 rounded-md border px-2 py-1.5 text-xs transition-all text-left cursor-pointer",
                  active
                    ? "border-emerald-300 bg-emerald-50 text-[#065F46] font-semibold"
                    : "border-[#D9E2EC] bg-[#F8FAFC] text-[#64748B] hover:bg-[#F1F5F9]"
                )}
              >
                <Icon className={cn("size-3.5", active ? "text-[#065F46]" : "text-[#94A3B8]")} />
                <span className="truncate">{type}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. Risk Severity */}
      <div className="rounded-md border border-[#D9E2EC] bg-white p-3 space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-[#0F172A] flex items-center gap-1.5">
            <ShieldAlert className="size-3.5 text-[#DC3545]" /> Risk Score Threshold
          </label>
          <span className="text-xs font-bold text-[#065F46]">
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
          className="w-full accent-[#065F46] cursor-pointer h-1.5 bg-[#E2E8F0] rounded-lg appearance-none"
        />

        <div className="grid grid-cols-4 gap-1">
          {(["Low", "Medium", "High", "Critical"] as const).map((r) => {
            const active = filters.riskLevels.has(r);
            return (
              <button
                key={r}
                onClick={() => toggleRisk(r)}
                className={cn(
                  "rounded-md border py-1 text-center text-xs font-semibold transition-all cursor-pointer",
                  active
                    ? r === "Critical"
                      ? "bg-red-50 text-[#DC3545] border-red-200"
                      : r === "High"
                      ? "bg-amber-50 text-[#F59E0B] border-amber-200"
                      : r === "Medium"
                      ? "bg-slate-100 text-[#475569] border-slate-300"
                      : "bg-emerald-50 text-[#198754] border-emerald-200"
                    : "border-[#D9E2EC] bg-[#F8FAFC] text-[#64748B]"
                )}
              >
                {r}
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Verification & Evidence Confidence */}
      <div className="rounded-md border border-[#D9E2EC] bg-white p-3 space-y-2">
        <label className="text-xs font-bold text-[#0F172A] flex items-center gap-1.5">
          <ShieldCheck className="size-3.5 text-[#198754]" /> Verification Status
        </label>
        <div className="grid grid-cols-2 gap-1.5 text-xs">
          {(["Verified", "High Confidence", "Probable", "Unknown"] as const).map((c) => {
            const active = filters.confidenceLevels.has(c);
            return (
              <button
                key={c}
                onClick={() => toggleConfidence(c)}
                className={cn(
                  "rounded-md border px-2 py-1 text-left transition-all cursor-pointer truncate",
                  active
                    ? "border-emerald-200 bg-emerald-50 text-[#198754] font-semibold"
                    : "border-[#D9E2EC] bg-[#F8FAFC] text-[#64748B]"
                )}
              >
                {c}
              </button>
            );
          })}
        </div>
      </div>

      {/* Reset Button */}
      <button
        onClick={onReset}
        className="w-full flex items-center justify-center gap-1.5 rounded-md border border-[#D9E2EC] bg-white py-2 text-xs font-semibold text-[#475569] hover:bg-[#F8FAFC] transition-colors cursor-pointer shadow-xs"
      >
        <RotateCcw className="size-3.5" />
        <span>Reset Filters</span>
      </button>
    </div>
  );
}
