import React from "react";
import {
  FileText,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Share2,
  Users,
  Repeat,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface InvestigationSummaryProps {
  onNavigateModule?: (route: string) => void;
}

export function InvestigationSummary({ onNavigateModule }: InvestigationSummaryProps) {
  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="size-4 text-sky-400" />
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
            Executive Investigative Summary & Cross-Module Intelligence
          </h3>
        </div>

        <span className="rounded bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 font-mono text-[10px] text-emerald-300 font-bold">
          85% Case Maturity
        </span>
      </div>

      {/* Synthesis Narrative */}
      <div className="rounded border border-sky-900/40 bg-sky-950/20 p-3.5 text-slate-200 leading-relaxed font-sans text-xs">
        <strong className="text-sky-300">Lead Case Synopsis: </strong>
        Case <strong>CASE-2026-N09</strong> centers on an inter-state cyber extortion and hawala syndicate. Operatives operated illegal VoIP call-center infrastructure in Sector 62 Noida, synchronized OTP relays via a 128-channel GSM SIM farm in Bhubaneswar, and layered ₹1.54 Cr in extortion proceeds through ICICI mule accounts and Mumbai OTC crypto desks.
      </div>

      {/* Findings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-[11px]">
        {/* Finding 1 */}
        <div className="rounded border border-slate-800 bg-[#121820] p-3 space-y-1.5">
          <div className="flex items-center gap-1.5 text-purple-400 font-bold uppercase text-[10px]">
            <Share2 className="size-3.5" /> Graph Centrality
          </div>
          <p className="text-slate-300 font-sans text-xs leading-tight">
            Vikramaditya Rawat confirmed as primary kingpin (PageRank: 24.8%, Rank #1).
          </p>
        </div>

        {/* Finding 2 */}
        <div className="rounded border border-slate-800 bg-[#121820] p-3 space-y-1.5">
          <div className="flex items-center gap-1.5 text-red-400 font-bold uppercase text-[10px]">
            <Repeat className="size-3.5" /> Anomaly Cycles
          </div>
          <p className="text-slate-300 font-sans text-xs leading-tight">
            4-hop circular fund recycling loop ALT-2026-001 verified with 9% return haircut.
          </p>
        </div>

        {/* Finding 3 */}
        <div className="rounded border border-slate-800 bg-[#121820] p-3 space-y-1.5">
          <div className="flex items-center gap-1.5 text-emerald-400 font-bold uppercase text-[10px]">
            <ShieldCheck className="size-3.5" /> Evidence Chain
          </div>
          <p className="text-slate-300 font-sans text-xs leading-tight">
            4 SHA-256 evidence blocks sealed and verified under Section 65B compliance.
          </p>
        </div>
      </div>
    </div>
  );
}
