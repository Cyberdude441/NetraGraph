import React from "react";
import { Search, Sparkles, Filter, X, CheckSquare, Square } from "lucide-react";
import { cn } from "@/lib/utils";
import type { EntityFilterState } from "@/utils/entityMatching";

interface EntitySearchProps {
  filters: EntityFilterState;
  onFilterChange: (updater: (prev: EntityFilterState) => EntityFilterState) => void;
  resultCount: number;
}

export function EntitySearch({
  filters,
  onFilterChange,
  resultCount,
}: EntitySearchProps) {
  const toggleField = (field: keyof EntityFilterState["searchFields"]) => {
    onFilterChange((prev) => ({
      ...prev,
      searchFields: {
        ...prev.searchFields,
        [field]: !prev.searchFields[field],
      },
    }));
  };

  return (
    <div className="space-y-2 select-none">
      {/* Search Input Bar */}
      <div className="relative">
        <div className="flex items-center gap-2 rounded border border-slate-800 bg-[#161D24] px-3 py-2 text-xs text-slate-200 focus-within:border-sky-500 transition-all shadow-inner">
          <Search className="size-3.5 text-slate-400 shrink-0" />
          <input
            type="text"
            placeholder="Search entity name, alias, phone, IMEI, case..."
            value={filters.searchQuery}
            onChange={(e) =>
              onFilterChange((prev) => ({ ...prev, searchQuery: e.target.value }))
            }
            className="w-full bg-transparent text-xs text-slate-100 placeholder:text-slate-500 outline-none font-mono"
          />
          {filters.searchQuery && (
            <button
              onClick={() => onFilterChange((prev) => ({ ...prev, searchQuery: "" }))}
              className="text-slate-400 hover:text-slate-200 p-0.5 rounded cursor-pointer"
            >
              <X className="size-3" />
            </button>
          )}
        </div>
      </div>

      {/* Search Scope Toggles */}
      <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
        <span className="text-[9px] font-mono uppercase font-bold text-slate-500">
          Match Scope:
        </span>
        {[
          { key: "name", label: "Name" },
          { key: "alias", label: "Alias" },
          { key: "phone", label: "Phone/IMEI" },
          { key: "location", label: "Jurisdiction" },
          { key: "caseId", label: "Case Docket" },
        ].map((f) => {
          const active = filters.searchFields[f.key as keyof EntityFilterState["searchFields"]];
          return (
            <button
              key={f.key}
              onClick={() => toggleField(f.key as keyof EntityFilterState["searchFields"])}
              className={cn(
                "rounded px-1.5 py-0.5 font-mono text-[9px] font-medium transition-all cursor-pointer border",
                active
                  ? "border-sky-500/40 bg-sky-950/40 text-sky-300"
                  : "border-slate-800 bg-[#121820] text-slate-500 hover:border-slate-700"
              )}
            >
              {f.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
