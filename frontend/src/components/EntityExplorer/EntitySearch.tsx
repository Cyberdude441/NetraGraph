import React from "react";
import { Search, X } from "lucide-react";
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
        <div className="flex items-center gap-2 rounded-md border border-[#D9E2EC] bg-white px-3 py-2 text-xs text-[#0F172A] focus-within:border-[#065F46] focus-within:ring-1 focus-within:ring-[#065F46] transition-all shadow-xs">
          <Search className="size-4 text-[#64748B] shrink-0" />
          <input
            type="text"
            placeholder="Search name, phone number, IMEI, account..."
            value={filters.searchQuery}
            onChange={(e) =>
              onFilterChange((prev) => ({ ...prev, searchQuery: e.target.value }))
            }
            className="w-full bg-transparent text-xs text-[#0F172A] placeholder:text-[#94A3B8] outline-none"
          />
          {filters.searchQuery && (
            <button
              onClick={() => onFilterChange((prev) => ({ ...prev, searchQuery: "" }))}
              className="text-[#64748B] hover:text-[#0F172A] p-0.5 rounded cursor-pointer"
            >
              <X className="size-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Search Scope Toggles */}
      <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
        <span className="text-[11px] font-semibold text-[#64748B]">
          Scope:
        </span>
        {[
          { key: "name", label: "Name" },
          { key: "alias", label: "Alias" },
          { key: "phone", label: "Phone / IMEI" },
          { key: "location", label: "Jurisdiction" },
          { key: "caseId", label: "Case ID" },
        ].map((f) => {
          const active = filters.searchFields[f.key as keyof EntityFilterState["searchFields"]];
          return (
            <button
              key={f.key}
              onClick={() => toggleField(f.key as keyof EntityFilterState["searchFields"])}
              className={cn(
                "rounded-md px-2 py-0.5 text-xs font-medium transition-all cursor-pointer border",
                active
                  ? "border-emerald-300 bg-emerald-50 text-[#065F46] font-semibold"
                  : "border-[#D9E2EC] bg-white text-[#64748B] hover:bg-[#F8FAFC]"
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
