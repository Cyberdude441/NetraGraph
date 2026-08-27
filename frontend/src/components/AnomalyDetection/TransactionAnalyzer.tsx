import React from "react";
import {
  CreditCard,
  ArrowRight,
  Repeat,
  ShieldAlert,
  Flame,
  Clock,
  Building2,
  User,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { CircularLoopPattern } from "@/utils/patternAnalysis";

interface TransactionAnalyzerProps {
  loop: CircularLoopPattern;
  onSelectEntity?: (id: string) => void;
}

export function TransactionAnalyzer({ loop, onSelectEntity }: TransactionAnalyzerProps) {
  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-[#E2E8F0] pb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Repeat className="size-4 text-purple-400 animate-spin" style={{ animationDuration: "12s" }} />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-900">
              Circular Transaction Layering & Fund Recycling Loop
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              Automated cycle detection exposed ₹{(loop.totalTransferredINR / 10000000).toFixed(2)} Cr routed across {loop.hopCount} hops with 9% haircut margin.
            </p>
          </div>
        </div>

        <span className="rounded bg-purple-950/60 border border-purple-800 px-2.5 py-1 text-xs font-mono font-bold text-purple-300">
          {loop.confidence}% Pattern Confidence
        </span>
      </div>

      {/* Visual Loop Chain */}
      <div className="space-y-3 relative pl-6 before:absolute before:left-2.5 before:top-4 before:bottom-4 before:w-0.5 before:bg-purple-900/60">
        {loop.hops.map((hop, idx) => {
          const isFirst = idx === 0;
          const isLast = idx === loop.hops.length - 1;

          return (
            <div key={idx} className="relative group">
              {/* Step Bullet */}
              <div
                className={cn(
                  "absolute -left-6 top-2 flex size-5 items-center justify-center rounded-full border shadow-sm font-mono text-[9px] font-bold",
                  isFirst
                    ? "border-emerald-500 bg-emerald-950 text-emerald-300 ring-2 ring-emerald-500/40"
                    : isLast
                    ? "border-purple-500 bg-purple-950 text-purple-300 ring-2 ring-purple-500/40"
                    : "border-slate-300 bg-[#F8FAFC] text-slate-700"
                )}
              >
                {hop.hopIndex}
              </div>

              {/* Hop Transfer Card */}
              <div className="rounded-lg border border-[#E2E8F0] bg-white p-3 space-y-2 hover:border-purple-500/60 transition-all">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 text-xs">
                      {hop.fromEntityName}
                    </span>
                    <ArrowRight className="size-3 text-purple-400 shrink-0" />
                    <span className="font-bold text-slate-900 text-xs">
                      {hop.toEntityName}
                    </span>
                  </div>

                  <span className="font-mono text-xs font-bold text-amber-300">
                    ₹{(hop.amountINR / 100000).toFixed(2)} Lakhs
                  </span>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#E2E8F0]/80 pt-1.5 text-[10px] font-mono text-slate-500">
                  <span>Channel: <strong className="text-slate-700">{hop.channel}</strong></span>
                  <span>Timestamp: <strong className="text-slate-400">{new Date(hop.timestamp).toLocaleString()}</strong></span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Forensic Summary Box */}
      <div className="rounded border border-purple-900/40 bg-purple-950/20 p-3 text-[11px] font-mono text-purple-200 leading-relaxed">
        <strong>Forensic Finding: </strong> Closed-circuit fund recycling detected between origin node <code>{loop.originEntityId}</code> and intermediate mule POS terminals. Evidences structured structuring/smurfing designed to bypass banking CTR thresholds.
      </div>
    </div>
  );
}
