import React, { useState } from "react";
import {
  Clock,
  Calendar,
  Filter,
  Flame,
  ShieldAlert,
  PhoneCall,
  CreditCard,
  MapPin,
  FileText,
  ArrowRightLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { EntityTimelineEvent } from "@/data/syntheticEntities";

interface EntityTimelineProps {
  timeline: EntityTimelineEvent[];
  entityName: string;
}

type EventFilterType = "ALL" | "COMMUNICATION" | "FINANCIAL" | "LOCATION" | "CASE_MENTION" | "RELATIONSHIP_CHANGE";

const EVENT_TYPE_ICONS: Record<string, React.ElementType> = {
  COMMUNICATION: PhoneCall,
  FINANCIAL: CreditCard,
  LOCATION: MapPin,
  CASE_MENTION: FileText,
  RELATIONSHIP_CHANGE: ArrowRightLeft,
};

export function EntityTimeline({ timeline, entityName }: EntityTimelineProps) {
  const [activeFilter, setActiveFilter] = useState<EventFilterType>("ALL");

  const filteredEvents = timeline.filter((e) => {
    if (activeFilter === "ALL") return true;
    return e.type === activeFilter;
  });

  return (
    <div className="rounded border border-slate-800 bg-[#0E1318] p-4 text-xs select-none space-y-4 font-sans">
      {/* Header & Filter Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Clock className="size-4 text-sky-400" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
            Chronological Forensic Timeline ({timeline.length} Events)
          </span>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1 bg-[#141A21] p-1 rounded border border-slate-800 font-mono text-[10px]">
          {(
            [
              { id: "ALL", label: "All Events" },
              { id: "FINANCIAL", label: "Financial" },
              { id: "COMMUNICATION", label: "Calls / Wiretaps" },
              { id: "LOCATION", label: "Locations" },
              { id: "CASE_MENTION", label: "Case Mentions" },
              { id: "RELATIONSHIP_CHANGE", label: "Network Changes" },
            ] as const
          ).map((f) => {
            const active = activeFilter === f.id;
            return (
              <button
                key={f.id}
                onClick={() => setActiveFilter(f.id)}
                className={cn(
                  "rounded px-2 py-0.5 font-bold transition-all cursor-pointer",
                  active
                    ? "bg-sky-500/20 text-sky-300 border border-sky-500/50"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                {f.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Timeline Stream */}
      <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {filteredEvents.length === 0 ? (
          <div className="text-slate-500 font-mono text-center py-4">
            No events match the selected timeline category.
          </div>
        ) : (
          filteredEvents.map((evt, idx) => {
            const Icon = EVENT_TYPE_ICONS[evt.type] || FileText;
            const isCrit = evt.severity === "critical";
            const isHigh = evt.severity === "high";

            return (
              <div key={evt.id || idx} className="relative group">
                {/* Node Bullet */}
                <div
                  className={cn(
                    "absolute -left-6 top-1 flex size-5 items-center justify-center rounded-full border shadow-sm transition-all",
                    isCrit
                      ? "border-red-500 bg-red-950 text-red-300 ring-2 ring-red-500/40"
                      : isHigh
                      ? "border-amber-500 bg-amber-950 text-amber-300"
                      : "border-slate-700 bg-[#161D24] text-slate-400"
                  )}
                >
                  <Icon className="size-2.5" />
                </div>

                {/* Event Card */}
                <div
                  className={cn(
                    "rounded-lg border p-3 transition-all",
                    isCrit
                      ? "border-red-900/60 bg-[#1A1215]"
                      : isHigh
                      ? "border-amber-900/50 bg-[#191512]"
                      : "border-slate-800 bg-[#121820]"
                  )}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          "font-mono text-[9px] font-bold uppercase rounded px-1.5 py-0.2 border",
                          evt.type === "FINANCIAL"
                            ? "bg-amber-950/40 border-amber-800 text-amber-300"
                            : evt.type === "COMMUNICATION"
                            ? "bg-sky-950/40 border-sky-800 text-sky-300"
                            : evt.type === "CASE_MENTION"
                            ? "bg-purple-950/40 border-purple-800 text-purple-300"
                            : "bg-slate-800 border-slate-700 text-slate-300"
                        )}
                      >
                        {evt.type.replace("_", " ")}
                      </span>
                      <h4 className="font-semibold text-slate-200 text-xs">
                        {evt.title}
                      </h4>
                    </div>

                    <span className="font-mono text-[10px] text-slate-400">
                      {new Date(evt.timestamp).toLocaleString()}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-300 leading-relaxed font-sans mt-1">
                    {evt.description}
                  </p>

                  <div className="mt-2 flex items-center justify-between border-t border-slate-800/80 pt-1.5 text-[10px] font-mono text-slate-500">
                    <span>Source Reference: <strong className="text-slate-300">{evt.sourceRef}</strong></span>
                    <span className="capitalize text-slate-400">Severity: {evt.severity}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
