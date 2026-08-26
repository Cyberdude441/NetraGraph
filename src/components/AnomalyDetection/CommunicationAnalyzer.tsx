import React from "react";
import { PhoneCall, TrendingUp, Flame, Clock, AlertTriangle } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { cn } from "@/lib/utils";
import type { CommunicationBurstPattern } from "@/utils/patternAnalysis";

interface CommunicationAnalyzerProps {
  burst: CommunicationBurstPattern;
}

export function CommunicationAnalyzer({ burst }: CommunicationAnalyzerProps) {
  const chartData = burst.history.map((h) => ({
    date: h.date.slice(5), // MM-DD
    calls: h.callCount,
    baseline: h.baseline,
    isSpike: h.isSpike,
  }));

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <PhoneCall className="size-4 text-sky-400" />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
              Communication Frequency Burst & Surge Analysis
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              Entity <strong>{burst.entityName}</strong> experienced a +{burst.surgePercentage}% call volume surge over 48 hours.
            </p>
          </div>
        </div>

        <span className="rounded bg-sky-950/60 border border-sky-800 px-2.5 py-1 text-xs font-mono font-bold text-sky-300">
          +{burst.surgePercentage}% Volume Surge
        </span>
      </div>

      {/* KPI Stats Line */}
      <div className="grid grid-cols-3 gap-3 font-mono text-[11px]">
        <div className="rounded border border-slate-800 bg-[#121820] p-2.5">
          <span className="text-[9px] uppercase text-slate-500 block">Baseline Daily Avg</span>
          <span className="text-base font-bold text-slate-200">{burst.baselineDailyAvg} Calls</span>
        </div>
        <div className="rounded border border-slate-800 bg-[#121820] p-2.5">
          <span className="text-[9px] uppercase text-slate-500 block">Peak Observed Surge</span>
          <span className="text-base font-bold text-red-400">{burst.peakDailyCount} Calls/Day</span>
        </div>
        <div className="rounded border border-slate-800 bg-[#121820] p-2.5">
          <span className="text-[9px] uppercase text-slate-500 block">Target Operatives</span>
          <span className="text-base font-bold text-sky-400">{burst.targetEntities.length} Entities</span>
        </div>
      </div>

      {/* Recharts Call Volume Bar Chart */}
      <div className="rounded-lg border border-slate-800 bg-[#121820] p-3 space-y-2">
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 border-b border-slate-800/80 pb-1.5">
          <span>7-Day Communication Timeline (Calls / Day)</span>
          <span className="text-amber-400 font-bold">--- Baseline: {burst.baselineDailyAvg} calls</span>
        </div>

        <div className="h-48 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="#1E293B" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="date" stroke="#64748B" fontSize={10} fontFamily="monospace" />
              <YAxis stroke="#64748B" fontSize={10} fontFamily="monospace" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#11161B",
                  borderColor: "#334155",
                  borderRadius: "6px",
                  color: "#E2E8F0",
                  fontSize: "11px",
                  fontFamily: "monospace",
                }}
              />
              <ReferenceLine y={burst.baselineDailyAvg} stroke="#F59E0B" strokeDasharray="3 3" />
              <Bar
                dataKey="calls"
                fill="#38BDF8"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
