import React from "react";
import { TrendingUp, Flame, ShieldAlert, AlertTriangle, ArrowRight, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import { calculateDynamicRiskImpact, type DynamicRiskAssessment } from "@/utils/riskCalculator";
import type { AnomalyAlert } from "@/utils/anomalyDetection";

interface RiskImpactPanelProps {
  alert: AnomalyAlert | null;
}

export function RiskImpactPanel({ alert }: RiskImpactPanelProps) {
  if (!alert) return null;

  // Compute dynamic risk delta
  const baseline = 42;
  const assessment: DynamicRiskAssessment = calculateDynamicRiskImpact(
    baseline,
    alert.primaryEntityId,
    alert.primaryEntityName,
    [alert.category]
  );

  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-4 text-xs select-none space-y-3 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-[#E2E8F0] pb-2 flex items-center justify-between">
        <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase font-bold text-amber-400">
          <TrendingUp className="size-3.5" />
          <span>Dynamic Risk Impact Recalibration</span>
        </div>

        <span className="font-mono text-[10px] text-slate-400">
          Baseline + Delta Model
        </span>
      </div>

      {/* Before vs After Score Box */}
      <div className="rounded border border-[#E2E8F0] bg-white p-3 flex items-center justify-between font-mono">
        <div>
          <span className="text-[9px] uppercase text-slate-500 block">Baseline Risk</span>
          <span className="text-base font-bold text-slate-700">{assessment.baselineRiskScore}/100</span>
        </div>

        <ArrowRight className="size-4 text-amber-400" />

        <div className="text-right">
          <span className="text-[9px] uppercase text-amber-400 font-bold block">
            Recalibrated Risk (+{assessment.delta} pts)
          </span>
          <span className="text-lg font-bold text-red-400">
            {assessment.recalibratedRiskScore}/100 ({assessment.threatTier})
          </span>
        </div>
      </div>

      {/* Factor Breakdown */}
      <div className="space-y-1.5 font-mono text-[10px]">
        <span className="text-slate-400 font-bold uppercase block">
          Anomaly Penalty Weight:
        </span>
        {assessment.contributions.map((c, i) => (
          <div
            key={i}
            className="rounded border border-[#E2E8F0] bg-[#F8FAFC] p-2 flex items-center justify-between"
          >
            <div>
              <strong className="text-slate-800 block text-[11px]">{c.factorName}</strong>
              <p className="text-[9px] text-slate-400 font-sans">{c.description}</p>
            </div>
            <span className="text-red-400 font-bold shrink-0 ml-2">+{c.pointsAdded} Pts</span>
          </div>
        ))}
      </div>

      {/* Mandatory Regulatory Disclaimer */}
      <div className="rounded border border-[#E2E8F0]/80 bg-[#10161E] p-2 text-[9px] font-mono text-slate-500 flex items-start gap-1.5 leading-tight">
        <ShieldCheck className="size-3 text-emerald-400 shrink-0 mt-0.5" />
        <span>{assessment.disclaimer}</span>
      </div>
    </div>
  );
}
