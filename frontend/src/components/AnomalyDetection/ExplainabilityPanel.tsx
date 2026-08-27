import React from "react";
import { Info, AlertTriangle, CheckCircle2, ShieldCheck, Flame } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AnomalyAlert } from "@/utils/anomalyDetection";

interface ExplainabilityPanelProps {
  alert: AnomalyAlert | null;
}

export function ExplainabilityPanel({ alert }: ExplainabilityPanelProps) {
  if (!alert) return null;

  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-4 text-xs select-none space-y-3 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-[#E2E8F0] pb-2 flex items-center justify-between">
        <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase font-bold text-emerald-400">
          <Info className="size-3.5" />
          <span>Explainable Anomaly Breakdown</span>
        </div>

        <span className="font-mono text-[10px] text-emerald-400">
          Confidence: {alert.confidenceScore}%
        </span>
      </div>

      {/* 3-Tier Explainability Chain */}
      <div className="space-y-2.5">
        {/* Tier 1: Observation */}
        <div className="rounded border border-[#E2E8F0] bg-white p-2.5 space-y-1">
          <span className="text-[9px] font-mono uppercase font-bold text-slate-400 block">
            1. Empirical Observation (Raw Telemetry)
          </span>
          <p className="text-[11px] text-slate-800 leading-relaxed font-sans">
            {alert.observation}
          </p>
        </div>

        {/* Tier 2: Analysis */}
        <div className="rounded border border-emerald-900/50 bg-emerald-50 p-2.5 space-y-1">
          <span className="text-[9px] font-mono uppercase font-bold text-emerald-400 block">
            2. Algorithmic Pattern Inference
          </span>
          <p className="text-[11px] text-slate-700 leading-relaxed font-sans">
            {alert.analysis}
          </p>
        </div>

        {/* Tier 3: Assessment */}
        <div className="rounded border border-amber-900/50 bg-amber-950/20 p-2.5 space-y-1">
          <span className="text-[9px] font-mono uppercase font-bold text-amber-400 block flex items-center gap-1">
            <AlertTriangle className="size-3" /> 3. Investigative Action Plan
          </span>
          <p className="text-[11px] text-slate-700 leading-relaxed font-sans">
            {alert.assessment}
          </p>
        </div>
      </div>
    </div>
  );
}
