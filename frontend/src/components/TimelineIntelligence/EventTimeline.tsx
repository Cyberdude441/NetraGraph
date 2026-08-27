import React from "react";
import {
  CreditCard,
  PhoneCall,
  Radio,
  MapPin,
  FileText,
  Sparkles,
  Users,
  Clock,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { SpatialTimelineEvent } from "@/data/syntheticSpatialData";

interface EventTimelineProps {
  events: SpatialTimelineEvent[];
  onSelectEvent?: (event: SpatialTimelineEvent) => void;
  onSelectEntity?: (entityId: string) => void;
}

const EVENT_TYPE_ICONS: Record<string, React.ElementType> = {
  FINANCIAL_TRANSFER: CreditCard,
  COMMUNICATION: PhoneCall,
  PHYSICAL_MEETING: Users,
  SIM_SWITCH: Radio,
  CASE_ACTION: FileText,
  AI_DETECTION: Sparkles,
};

export function EventTimeline({
  events,
  onSelectEvent,
  onSelectEntity,
}: EventTimelineProps) {
  return (
    <div className="space-y-4 font-sans select-none">
      <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-100">
        {events.length === 0 ? (
          <div className="rounded border border-dashed border-[#E2E8F0] p-8 text-center text-slate-500 font-mono text-xs">
            No events match the active chronological filters.
          </div>
        ) : (
          events.map((evt, idx) => {
            const Icon = EVENT_TYPE_ICONS[evt.eventType] || Clock;
            const isCrit = evt.severity === "critical";
            const isHigh = evt.severity === "high";

            return (
              <div key={evt.id || idx} className="relative group">
                {/* Node Bullet */}
                <div
                  className={cn(
                    "absolute -left-6 top-1.5 flex size-5 items-center justify-center rounded-full border shadow-sm transition-all",
                    isCrit
                      ? "border-red-500 bg-red-950 text-red-300 ring-2 ring-red-500/40"
                      : isHigh
                      ? "border-amber-500 bg-amber-950 text-amber-300"
                      : "border-slate-300 bg-[#F8FAFC] text-slate-400"
                  )}
                >
                  <Icon className="size-2.5" />
                </div>

                {/* Event Card */}
                <div
                  onClick={() => onSelectEvent && onSelectEvent(evt)}
                  className={cn(
                    "rounded-lg border p-3.5 space-y-2 transition-all cursor-pointer",
                    isCrit
                      ? "border-red-900/60 bg-[#1A1215] hover:border-red-500"
                      : isHigh
                      ? "border-amber-900/50 bg-[#191512] hover:border-amber-500"
                      : "border-[#E2E8F0] bg-white hover:border-slate-300"
                  )}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          "font-mono text-[9px] font-bold uppercase rounded px-1.5 py-0.2 border",
                          evt.eventType === "FINANCIAL_TRANSFER"
                            ? "bg-purple-950/60 border-purple-800 text-purple-300"
                            : evt.eventType === "COMMUNICATION"
                            ? "bg-emerald-950/60 border-emerald-800 text-emerald-300"
                            : evt.eventType === "SIM_SWITCH"
                            ? "bg-emerald-950/60 border-emerald-800 text-emerald-300"
                            : "bg-slate-100 border-slate-300 text-slate-700"
                        )}
                      >
                        {evt.eventType.replace("_", " ")}
                      </span>

                      <h4 className="font-semibold text-slate-900 text-xs">
                        {evt.title}
                      </h4>
                    </div>

                    <span className="font-mono text-[10px] text-slate-400">
                      {new Date(evt.timestamp).toLocaleString()}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-700 leading-relaxed font-sans">
                    {evt.description}
                  </p>

                  {/* Metadata Row */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#E2E8F0]/80 pt-2 text-[10px] font-mono text-slate-400">
                    <div className="flex items-center gap-1.5">
                      <MapPin className="size-3 text-emerald-400 shrink-0" />
                      <span className="text-slate-700 truncate max-w-xs">{evt.locationName}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span>Ref: <strong className="text-slate-700">{evt.sourceReference}</strong></span>
                      <span className="text-emerald-400 font-bold">{evt.confidenceScore}% Conf</span>
                    </div>
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
