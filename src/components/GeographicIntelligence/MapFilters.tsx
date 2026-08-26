import React from "react";
import {
  Filter,
  Layers,
  Flame,
  Radio,
  Building2,
  Cpu,
  MapPin,
  RotateCcw,
  Eye,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface MapFilterState {
  facilityTypes: Set<string>;
  threatLevels: Set<"CRITICAL" | "HIGH" | "MEDIUM" | "LOW">;
  showHotspots: boolean;
  showVectors: boolean;
  selectedCity: string;
}

export const DEFAULT_MAP_FILTERS: MapFilterState = {
  facilityTypes: new Set([
    "CELL_TOWER",
    "SAFEHOUSE",
    "SHELL_OFFICE",
    "ATM_CDM_KIOSK",
    "SERVER_FARM",
    "MEETING_POINT",
  ]),
  threatLevels: new Set(["CRITICAL", "HIGH", "MEDIUM", "LOW"]),
  showHotspots: true,
  showVectors: true,
  selectedCity: "ALL",
};

interface MapFiltersProps {
  filters: MapFilterState;
  onFilterChange: (updater: (prev: MapFilterState) => MapFilterState) => void;
  onReset: () => void;
  cityOptions: string[];
}

export function MapFilters({
  filters,
  onFilterChange,
  onReset,
  cityOptions,
}: MapFiltersProps) {
  const toggleType = (type: string) => {
    onFilterChange((prev) => {
      const next = new Set(prev.facilityTypes);
      if (next.has(type)) {
        if (next.size > 1) next.delete(type);
      } else {
        next.add(type);
      }
      return { ...prev, facilityTypes: next };
    });
  };

  const toggleThreat = (threat: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW") => {
    onFilterChange((prev) => {
      const next = new Set(prev.threatLevels);
      if (next.has(threat)) {
        if (next.size > 1) next.delete(threat);
      } else {
        next.add(threat);
      }
      return { ...prev, threatLevels: next };
    });
  };

  return (
    <div className="space-y-4 text-xs select-none font-sans">
      {/* 1. Map Layers Toggle */}
      <div className="rounded border border-slate-800/80 bg-[#121922] p-3 space-y-2">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
          <Eye className="size-3 text-sky-400" /> Tactical Layer Controls
        </label>

        <div className="grid grid-cols-2 gap-1.5 font-mono text-[10px]">
          <button
            onClick={() =>
              onFilterChange((prev) => ({ ...prev, showHotspots: !prev.showHotspots }))
            }
            className={cn(
              "rounded border px-2 py-1.5 text-left transition-all cursor-pointer font-bold",
              filters.showHotspots
                ? "border-red-500/50 bg-red-950/30 text-red-300"
                : "border-slate-800 bg-[#141A21] text-slate-500"
            )}
          >
            Threat Hotspots
          </button>

          <button
            onClick={() =>
              onFilterChange((prev) => ({ ...prev, showVectors: !prev.showVectors }))
            }
            className={cn(
              "rounded border px-2 py-1.5 text-left transition-all cursor-pointer font-bold",
              filters.showVectors
                ? "border-sky-500/50 bg-sky-950/30 text-sky-300"
                : "border-slate-800 bg-[#141A21] text-slate-500"
            )}
          >
            Transfer Vectors
          </button>
        </div>
      </div>

      {/* 2. City Hub Selector */}
      <div className="rounded border border-slate-800/80 bg-[#121922] p-3 space-y-1.5">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
          Jurisdiction Cluster
        </label>
        <select
          value={filters.selectedCity}
          onChange={(e) =>
            onFilterChange((prev) => ({ ...prev, selectedCity: e.target.value }))
          }
          className="w-full rounded border border-slate-800 bg-[#161D24] px-2 py-1 text-xs text-sky-300 font-mono outline-none cursor-pointer"
        >
          <option value="ALL">All Hubs (National View)</option>
          {cityOptions.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* 3. Facility Classifications */}
      <div className="rounded border border-slate-800/80 bg-[#121922] p-3 space-y-2">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
          Facility Type Scope
        </label>

        <div className="space-y-1 font-mono text-[10px]">
          {[
            { id: "CELL_TOWER", label: "Cell Towers & BTS Sites" },
            { id: "SAFEHOUSE", label: "Safehouses & Call Centers" },
            { id: "SHELL_OFFICE", label: "Shell Corp ROC Offices" },
            { id: "ATM_CDM_KIOSK", label: "Cash CDM Kiosks" },
            { id: "SERVER_FARM", label: "SIM Box / GSM Farms" },
            { id: "MEETING_POINT", label: "Hawala Drop Points" },
          ].map((t) => {
            const active = filters.facilityTypes.has(t.id);
            return (
              <button
                key={t.id}
                onClick={() => toggleType(t.id)}
                className={cn(
                  "w-full rounded border px-2 py-1 text-left transition-all cursor-pointer truncate",
                  active
                    ? "border-sky-500/50 bg-[#1A2634] text-sky-200 font-bold"
                    : "border-slate-800 bg-[#141A21] text-slate-500"
                )}
              >
                {t.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. Threat Level Filter */}
      <div className="rounded border border-slate-800/80 bg-[#121922] p-3 space-y-2">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
          Facility Threat Tier
        </label>
        <div className="grid grid-cols-2 gap-1 font-mono text-[10px]">
          {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((thr) => {
            const active = filters.threatLevels.has(thr);
            return (
              <button
                key={thr}
                onClick={() => toggleThreat(thr)}
                className={cn(
                  "rounded border py-1 text-center font-bold transition-all cursor-pointer",
                  active
                    ? thr === "CRITICAL"
                      ? "bg-red-950/60 text-red-300 border-red-500/60"
                      : thr === "HIGH"
                      ? "bg-amber-950/60 text-amber-300 border-amber-500/60"
                      : "bg-slate-800 text-slate-300 border-slate-700"
                    : "border-slate-800 bg-[#141A21] text-slate-600"
                )}
              >
                {thr}
              </button>
            );
          })}
        </div>
      </div>

      {/* Reset */}
      <button
        onClick={onReset}
        className="w-full flex items-center justify-center gap-1.5 rounded border border-slate-800 bg-[#161D24] py-1.5 text-[11px] font-mono font-semibold text-slate-400 hover:text-sky-400 transition-colors cursor-pointer"
      >
        <RotateCcw className="size-3" />
        <span>Reset Map Filters</span>
      </button>
    </div>
  );
}
