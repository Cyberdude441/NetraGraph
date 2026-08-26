import React from "react";
import {
  Filter,
  RotateCcw,
  ShieldAlert,
  Calendar,
  Layers,
  FolderSearch,
  CheckSquare,
  Square,
  Search,
  Activity,
  Flame,
  User,
  Smartphone,
  MapPin,
  Car,
  Building2,
  CreditCard,
  Cpu,
  CalendarDays,
  ArrowRightLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { GraphFilterCriteria } from "@/utils/graphFilters";
import { ALL_ENTITY_TYPES, ALL_RELATIONSHIP_TYPES } from "@/utils/graphFilters";

interface GraphFiltersProps {
  filters: GraphFilterCriteria;
  onFilterChange: (updater: (prev: GraphFilterCriteria) => GraphFilterCriteria) => void;
  onReset: () => void;
  caseOptions: { id: string; label: string }[];
  groupOptions: string[];
  stats: {
    totalEntities: number;
    matchedEntities: number;
    totalRelationships: number;
    matchedRelationships: number;
  };
}

const ENTITY_ICONS: Record<string, React.ElementType> = {
  Person: User,
  Phone: Smartphone,
  Location: MapPin,
  Vehicle: Car,
  Organization: Building2,
  BankAccount: CreditCard,
  Device: Cpu,
  Event: CalendarDays,
};

export function GraphFilters({
  filters,
  onFilterChange,
  onReset,
  caseOptions,
  groupOptions,
  stats,
}: GraphFiltersProps) {
  const toggleEntityType = (type: string) => {
    onFilterChange((prev) => {
      const nextTypes = new Set(prev.entityTypes);
      if (nextTypes.has(type)) {
        if (nextTypes.size > 1) nextTypes.delete(type);
      } else {
        nextTypes.add(type);
      }
      return { ...prev, entityTypes: nextTypes };
    });
  };

  const selectAllEntities = () => {
    onFilterChange((prev) => ({
      ...prev,
      entityTypes: new Set(ALL_ENTITY_TYPES),
    }));
  };

  const toggleRiskLevel = (level: string) => {
    onFilterChange((prev) => {
      const nextRisk = new Set(prev.riskLevels);
      if (nextRisk.has(level)) {
        if (nextRisk.size > 1) nextRisk.delete(level);
      } else {
        nextRisk.add(level);
      }
      return { ...prev, riskLevels: nextRisk };
    });
  };

  const toggleRelType = (type: string) => {
    onFilterChange((prev) => {
      const nextRels = new Set(prev.relationshipTypes);
      if (nextRels.has(type)) {
        if (nextRels.size > 1) nextRels.delete(type);
      } else {
        nextRels.add(type);
      }
      return { ...prev, relationshipTypes: nextRels };
    });
  };

  return (
    <aside className="w-80 border-r border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none">
      {/* Header */}
      <div className="border-b border-slate-800 bg-[#141A21] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="size-4 text-sky-400" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
            Investigation Filters
          </span>
        </div>
        <button
          onClick={onReset}
          className="flex items-center gap-1 text-[10px] font-mono text-slate-400 hover:text-sky-400 transition-colors cursor-pointer"
          title="Reset all filters to default"
        >
          <RotateCcw className="size-3" />
          <span>Reset</span>
        </button>
      </div>

      {/* Filter Stats HUD */}
      <div className="bg-[#10171F] px-4 py-2 border-b border-slate-800/80 flex items-center justify-between text-[11px] font-mono">
        <span className="text-slate-400">Showing Entities:</span>
        <span className="font-bold text-sky-400">
          {stats.matchedEntities} / {stats.totalEntities}
        </span>
      </div>

      {/* Filter Body */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-4 text-xs text-slate-300 custom-scrollbar">
        {/* 1. Keyword / Identifier Search */}
        <div className="space-y-1.5">
          <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
            <Search className="size-3 text-sky-400" /> Search Keyword / ID
          </label>
          <div className="relative">
            <input
              type="text"
              placeholder="Name, alias, phone, IMEI..."
              value={filters.searchQuery || ""}
              onChange={(e) =>
                onFilterChange((prev) => ({ ...prev, searchQuery: e.target.value }))
              }
              className="w-full rounded border border-slate-800 bg-[#161D24] px-2.5 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 outline-none focus:border-sky-500 font-mono"
            />
          </div>
        </div>

        {/* 2. Entity Type Matrix */}
        <div className="space-y-2 rounded border border-slate-800/80 bg-[#121922] p-2.5">
          <div className="flex items-center justify-between">
            <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
              <Layers className="size-3 text-sky-400" /> Entity Classification
            </label>
            <button
              onClick={selectAllEntities}
              className="text-[9px] font-mono text-sky-400 hover:underline cursor-pointer"
            >
              Select All
            </button>
          </div>

          <div className="grid grid-cols-2 gap-1.5">
            {ALL_ENTITY_TYPES.map((type) => {
              const active = filters.entityTypes.has(type);
              const Icon = ENTITY_ICONS[type] || User;
              return (
                <button
                  key={type}
                  onClick={() => toggleEntityType(type)}
                  className={cn(
                    "flex items-center gap-2 rounded border px-2 py-1 text-[11px] font-mono transition-all text-left cursor-pointer",
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

        {/* 3. Risk Threshold & Severity Tiers */}
        <div className="space-y-2.5 rounded border border-slate-800/80 bg-[#121922] p-2.5">
          <div className="flex items-center justify-between">
            <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
              <ShieldAlert className="size-3 text-red-400" /> Risk Severity
            </label>
            <span className="font-mono text-[10px] font-bold text-amber-400">
              Min: {filters.minRiskScore}+
            </span>
          </div>

          {/* Min Slider */}
          <input
            type="range"
            min="0"
            max="95"
            step="5"
            value={filters.minRiskScore}
            onChange={(e) =>
              onFilterChange((prev) => ({
                ...prev,
                minRiskScore: Number(e.target.value),
              }))
            }
            className="w-full accent-sky-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg appearance-none"
          />

          {/* Risk Badges Multi-select */}
          <div className="grid grid-cols-4 gap-1">
            {[
              { id: "low", label: "Low", color: "text-emerald-400 border-emerald-500/40 bg-emerald-950/20" },
              { id: "medium", label: "Med", color: "text-slate-300 border-slate-600 bg-slate-800/30" },
              { id: "high", label: "High", color: "text-amber-400 border-amber-500/40 bg-amber-950/20" },
              { id: "critical", label: "Crit", color: "text-red-400 border-red-500/40 bg-red-950/30" },
            ].map((r) => {
              const active = filters.riskLevels.has(r.id);
              return (
                <button
                  key={r.id}
                  onClick={() => toggleRiskLevel(r.id)}
                  className={cn(
                    "rounded border py-1 text-center font-mono text-[10px] font-bold transition-all cursor-pointer",
                    active
                      ? r.color
                      : "border-slate-800 bg-[#141A21] text-slate-600 hover:border-slate-700"
                  )}
                >
                  {r.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* 4. Case Docket & Syndicate Cluster */}
        <div className="space-y-2 rounded border border-slate-800/80 bg-[#121922] p-2.5">
          <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
            <FolderSearch className="size-3 text-sky-400" /> Case Docket Filter
          </label>
          <select
            value={filters.caseId}
            onChange={(e) =>
              onFilterChange((prev) => ({ ...prev, caseId: e.target.value }))
            }
            className="w-full rounded border border-slate-800 bg-[#161D24] px-2 py-1.5 text-xs text-sky-300 font-mono outline-none"
          >
            <option value="ALL">All Active Investigation Dockets</option>
            {caseOptions.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>

          <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block pt-1">
            Syndicate Cluster
          </label>
          <select
            value={filters.investigationGroup}
            onChange={(e) =>
              onFilterChange((prev) => ({ ...prev, investigationGroup: e.target.value }))
            }
            className="w-full rounded border border-slate-800 bg-[#161D24] px-2 py-1.5 text-xs text-slate-200 font-mono outline-none"
          >
            <option value="ALL">All Network Groups</option>
            {groupOptions.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </div>

        {/* 5. Temporal Slice & Activity Window */}
        <div className="space-y-2 rounded border border-slate-800/80 bg-[#121922] p-2.5">
          <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
            <Calendar className="size-3 text-sky-400" /> Temporal Range
          </label>

          <div className="space-y-1.5 font-mono text-[10px]">
            <div className="flex items-center justify-between gap-2">
              <span className="text-slate-400">From:</span>
              <input
                type="date"
                value={filters.dateRange.start}
                onChange={(e) =>
                  onFilterChange((prev) => ({
                    ...prev,
                    dateRange: { ...prev.dateRange, start: e.target.value },
                  }))
                }
                className="rounded border border-slate-800 bg-[#161D24] px-1.5 py-0.5 text-slate-200 outline-none text-[10px]"
              />
            </div>
            <div className="flex items-center justify-between gap-2">
              <span className="text-slate-400">To:</span>
              <input
                type="date"
                value={filters.dateRange.end}
                onChange={(e) =>
                  onFilterChange((prev) => ({
                    ...prev,
                    dateRange: { ...prev.dateRange, end: e.target.value },
                  }))
                }
                className="rounded border border-slate-800 bg-[#161D24] px-1.5 py-0.5 text-slate-200 outline-none text-[10px]"
              />
            </div>
          </div>
        </div>

        {/* 6. Relationship Types */}
        <div className="space-y-1.5 rounded border border-slate-800/80 bg-[#121922] p-2.5">
          <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
            <ArrowRightLeft className="size-3 text-sky-400" /> Link Modalities ({stats.matchedRelationships} links)
          </label>
          <div className="space-y-1">
            {ALL_RELATIONSHIP_TYPES.map((rType) => {
              const active = filters.relationshipTypes.has(rType);
              return (
                <button
                  key={rType}
                  onClick={() => toggleRelType(rType)}
                  className={cn(
                    "flex w-full items-center justify-between rounded border px-2 py-1 text-[10px] font-mono transition-all cursor-pointer",
                    active
                      ? "border-sky-500/40 bg-[#182330] text-sky-300"
                      : "border-slate-800 bg-[#141A21] text-slate-500"
                  )}
                >
                  <span className="truncate">{rType.replace("_", " ")}</span>
                  {active ? (
                    <CheckSquare className="size-3 text-sky-400 shrink-0" />
                  ) : (
                    <Square className="size-3 text-slate-600 shrink-0" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </aside>
  );
}
