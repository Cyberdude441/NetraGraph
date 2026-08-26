import React from "react";
import {
  MapPin,
  Radio,
  Building2,
  Cpu,
  Flame,
  ShieldAlert,
  Users,
  Clock,
  Share2,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import type { SyntheticLocation, SpatialTimelineEvent } from "@/data/syntheticSpatialData";
import { calculateLocationMetrics } from "@/utils/spatialAnalysis";

interface LocationPanelProps {
  location: SyntheticLocation | null;
  events: SpatialTimelineEvent[];
  onSelectEntity?: (id: string) => void;
}

export function LocationPanel({
  location,
  events,
  onSelectEntity,
}: LocationPanelProps) {
  const navigate = useNavigate();

  if (!location) {
    return (
      <div className="rounded-lg border border-dashed border-slate-800 bg-[#0E1318] p-10 text-center text-slate-500 font-mono text-xs">
        Select a facility or cell tower marker on the tactical map to inspect spatial intelligence.
      </div>
    );
  }

  const metrics = calculateLocationMetrics(location.id, [location], events);
  const isCrit = location.threatLevel === "CRITICAL";

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-3 flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span
            className={cn(
              "flex size-8 shrink-0 items-center justify-center rounded-lg border",
              isCrit
                ? "bg-red-950/60 border-red-800 text-red-300"
                : "bg-amber-950/60 border-amber-800 text-amber-300"
            )}
          >
            <MapPin className="size-4" />
          </span>

          <div>
            <h3 className="font-bold text-slate-100 text-sm uppercase">
              {location.name}
            </h3>
            <p className="text-[10px] font-mono text-slate-400">
              {location.city}, {location.state} · ID: <strong>{location.id}</strong>
            </p>
          </div>
        </div>

        <span
          className={cn(
            "rounded px-2 py-0.5 font-mono text-[9px] font-bold uppercase",
            isCrit
              ? "bg-red-950/80 text-red-300 border border-red-500/60"
              : "bg-amber-950/80 text-amber-300 border border-amber-500/50"
          )}
        >
          {location.threatLevel}
        </span>
      </div>

      {/* Spatial Metrics HUD */}
      <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
        <div className="rounded bg-[#121820] p-2.5 border border-slate-800">
          <span className="text-[9px] text-slate-500 block">COORDINATES</span>
          <strong className="text-sky-300 text-xs">{location.latitude}, {location.longitude}</strong>
        </div>
        <div className="rounded bg-[#121820] p-2.5 border border-slate-800">
          <span className="text-[9px] text-slate-500 block">CORROBORATED EVENTS</span>
          <strong className="text-amber-400 text-xs">{location.totalEventsCount} Recorded</strong>
        </div>
      </div>

      {/* Facility Role Description */}
      <div className="rounded border border-slate-800 bg-[#121820] p-3 space-y-1">
        <span className="text-[9px] font-mono uppercase font-bold text-slate-400 block">
          Tactical Facility Function
        </span>
        <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
          {location.description}
        </p>
      </div>

      {/* Connected Entities & Suspects */}
      <div className="rounded border border-slate-800 bg-[#121820] p-3 space-y-2">
        <span className="text-[10px] font-mono uppercase font-bold text-slate-300 flex items-center justify-between">
          <span>Connected Suspect Profiles ({location.connectedEntityIds.length})</span>
        </span>

        <div className="flex flex-wrap gap-1.5 font-mono text-[10px]">
          {location.connectedEntityIds.map((eId) => (
            <button
              key={eId}
              onClick={() => onSelectEntity && onSelectEntity(eId)}
              className="rounded bg-[#161D24] px-2 py-1 text-slate-200 border border-slate-800 hover:border-sky-500 hover:text-sky-300 transition-colors cursor-pointer font-bold"
            >
              {eId}
            </button>
          ))}
        </div>
      </div>

      {/* Explainable Spatial Observation */}
      <div className="rounded border border-sky-900/40 bg-sky-950/20 p-3 space-y-1 font-mono text-[10px]">
        <span className="font-bold text-sky-300 uppercase block">
          Spatial Observation:
        </span>
        <p className="text-slate-300 leading-relaxed font-sans">
          {location.connectedEntityIds.length} synthetic profiles and {location.totalEventsCount} multi-source events converge on this tactical coordinate.
        </p>
        <div className="text-[9px] text-slate-500 pt-1">
          Requires analyst verification under IT Act Section 69B.
        </div>
      </div>
    </div>
  );
}
