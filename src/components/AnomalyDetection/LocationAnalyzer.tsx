import React from "react";
import { MapPin, Clock, Users, ShieldAlert, Flame, Radio } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LocationCoLocationPattern } from "@/utils/patternAnalysis";

interface LocationAnalyzerProps {
  location: LocationCoLocationPattern;
  onSelectEntity?: (id: string) => void;
}

export function LocationAnalyzer({ location, onSelectEntity }: LocationAnalyzerProps) {
  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Radio className="size-4 text-red-400 animate-pulse" />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
              Cellular Tower Sector Physical Co-Location
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              Multiple independent suspect devices pinged tower <strong>{location.towerId}</strong> during overlapping nocturnal windows.
            </p>
          </div>
        </div>

        <span className="rounded bg-red-950/60 border border-red-800 px-2.5 py-1 text-xs font-mono font-bold text-red-300">
          {location.coLocationConfidence}% Spatial Confidence
        </span>
      </div>

      {/* Tower Metadata Box */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-[11px]">
        <div className="rounded border border-slate-800 bg-[#121820] p-2.5">
          <span className="text-[9px] uppercase text-slate-500 block">Tower Location</span>
          <span className="text-slate-200 font-bold block mt-0.5 truncate">{location.locationName}</span>
        </div>
        <div className="rounded border border-slate-800 bg-[#121820] p-2.5">
          <span className="text-[9px] uppercase text-slate-500 block">Coordinates</span>
          <span className="text-sky-300 font-bold block mt-0.5">
            {location.latitude}, {location.longitude}
          </span>
        </div>
        <div className="rounded border border-slate-800 bg-[#121820] p-2.5">
          <span className="text-[9px] uppercase text-slate-500 block">Time Horizon</span>
          <span className="text-amber-300 font-bold block mt-0.5">22:00 — 04:00 (Night-Shift)</span>
        </div>
      </div>

      {/* Co-Located Suspects Table */}
      <div className="rounded border border-slate-800 bg-[#121820] overflow-hidden">
        <div className="border-b border-slate-800 bg-[#141A21] px-3 py-2 text-[10px] font-mono uppercase font-bold text-slate-300">
          Co-Located Suspect Devices ({location.coLocatedEntities.length} Targets)
        </div>
        <table className="w-full text-left font-mono text-[11px]">
          <thead className="border-b border-slate-800/80 bg-[#161D24] text-slate-500 text-[9px] uppercase">
            <tr>
              <th className="px-3 py-1.5">Target Name</th>
              <th className="px-3 py-1.5">Role</th>
              <th className="px-3 py-1.5">Active Phone / IMEI</th>
              <th className="px-3 py-1.5 text-right">Risk Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {location.coLocatedEntities.map((ent) => (
              <tr
                key={ent.entityId}
                onClick={() => onSelectEntity && onSelectEntity(ent.entityId)}
                className="hover:bg-[#161D24] transition-colors cursor-pointer"
              >
                <td className="px-3 py-2 font-bold text-slate-100">
                  {ent.name} <span className="text-[9px] text-slate-500 font-normal">({ent.entityId})</span>
                </td>
                <td className="px-3 py-2 text-slate-300">{ent.role}</td>
                <td className="px-3 py-2 text-sky-300">{ent.phoneOrImei}</td>
                <td className="px-3 py-2 text-right">
                  <span className="font-bold text-red-400">Risk {ent.riskScore}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
