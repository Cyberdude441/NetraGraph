import React from "react";
import {
  FolderSearch,
  ShieldCheck,
  Flame,
  Users,
  Share2,
  Clock,
  FileText,
  Activity,
  CheckCircle2,
  AlertTriangle,
  ArrowUpRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface CaseDashboardProps {
  caseId: string;
  onNavigateTab: (tabId: string) => void;
}

export function CaseDashboard({ caseId, onNavigateTab }: CaseDashboardProps) {
  return (
    <div className="space-y-4 font-sans select-none">
      {/* Case Header Card */}
      <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 space-y-3 shadow-2xl">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-start gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-sky-950/60 border border-sky-800 text-sky-300">
              <FolderSearch className="size-5" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-slate-100 text-base uppercase tracking-wide">
                  Operation Netra-Vigil: Inter-State Cyber Extortion Syndicate
                </h2>
                <span className="rounded bg-red-950/80 text-red-300 border border-red-500/60 px-2 py-0.5 font-mono text-[9px] font-bold uppercase">
                  CRITICAL PRIORITY
                </span>
              </div>
              <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                Docket: <strong className="text-slate-200">{caseId}</strong> · Lead Investigator:{" "}
                <strong className="text-sky-300">Insp. D. Bose</strong> · Agency: State Cyber Crime PS
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="rounded bg-[#161D24] px-3 py-1 text-slate-300 border border-slate-800">
              Status: <strong className="text-emerald-400">UNDER ANALYSIS</strong>
            </span>
          </div>
        </div>

        {/* Investigation Progress Bar */}
        <div className="space-y-1.5 font-mono text-[10px]">
          <div className="flex items-center justify-between text-slate-400">
            <span className="uppercase font-bold">Investigation Lifecycle Completion</span>
            <span className="text-sky-400 font-bold">85% Complete (Evidence Sealed)</span>
          </div>
          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
            <div className="bg-gradient-to-r from-sky-500 to-emerald-400 h-full rounded-full w-[85%]" />
          </div>
        </div>
      </div>

      {/* Case Telemetry KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 font-mono text-xs">
        <div
          onClick={() => onNavigateTab("entities")}
          className="rounded border border-slate-800 bg-[#121820] p-3 hover:border-sky-500 transition-colors cursor-pointer"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Suspects</span>
            <Users className="size-3.5 text-sky-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">105 Entities</div>
          <p className="text-[9px] text-slate-500 mt-0.5">4 Primary Kingpins</p>
        </div>

        <div
          onClick={() => onNavigateTab("network")}
          className="rounded border border-slate-800 bg-[#121820] p-3 hover:border-purple-500 transition-colors cursor-pointer"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Graph Links</span>
            <Share2 className="size-3.5 text-purple-400" />
          </div>
          <div className="text-xl font-bold text-purple-400">148 Edges</div>
          <p className="text-[9px] text-slate-500 mt-0.5">4 Syndicate Clusters</p>
        </div>

        <div
          onClick={() => onNavigateTab("anomalies")}
          className="rounded border border-slate-800 bg-[#121820] p-3 hover:border-red-500 transition-colors cursor-pointer"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Anomalies</span>
            <Flame className="size-3.5 text-red-400" />
          </div>
          <div className="text-xl font-bold text-red-400">5 Detected</div>
          <p className="text-[9px] text-slate-500 mt-0.5">Circular Loops & IMEI</p>
        </div>

        <div
          onClick={() => onNavigateTab("evidence")}
          className="rounded border border-slate-800 bg-[#121820] p-3 hover:border-emerald-500 transition-colors cursor-pointer"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Evidence Blocks</span>
            <ShieldCheck className="size-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-400">4 Sealed</div>
          <p className="text-[9px] text-slate-500 mt-0.5">SHA-256 Verified</p>
        </div>

        <div
          onClick={() => onNavigateTab("timeline")}
          className="rounded border border-slate-800 bg-[#121820] p-3 hover:border-amber-500 transition-colors cursor-pointer"
        >
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Events</span>
            <Clock className="size-3.5 text-amber-400" />
          </div>
          <div className="text-xl font-bold text-amber-400">200+ Events</div>
          <p className="text-[9px] text-slate-500 mt-0.5">Surveillance Timeline</p>
        </div>
      </div>
    </div>
  );
}
