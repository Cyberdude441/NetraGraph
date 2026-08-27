import React from "react";
import {
  Sparkles,
  Clock,
  MapPin,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  ShieldAlert,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { SYNTHETIC_CORRELATIONS, type SpatialTemporalCorrelation } from "@/utils/correlationEngine";

interface CorrelationPanelProps {
  correlations?: SpatialTemporalCorrelation[];
  onSelectLocation?: (locationId: string) => void;
}

export function CorrelationPanel({
  correlations = SYNTHETIC_CORRELATIONS,
  onSelectLocation,
}: CorrelationPanelProps) {
  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-[#E2E8F0] pb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Sparkles className="size-4 text-purple-400" />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-900">
              Spatial-Temporal Correlation & Lag Pipeline
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              Detects synchronized activity bursts across geographical facilities following relationship changes.
            </p>
          </div>
        </div>

        <span className="rounded bg-purple-950/60 border border-purple-800 px-2.5 py-1 text-xs font-mono font-bold text-purple-300">
          {correlations.length} Correlated Sequences
        </span>
      </div>

      {/* Correlation Cards Grid */}
      <div className="space-y-3">
        {correlations.map((corr) => (
          <div
            key={corr.id}
            onClick={() => onSelectLocation && onSelectLocation(corr.correlatedLocationId)}
            className="rounded-lg border border-[#E2E8F0] bg-white p-4 space-y-3 hover:border-purple-500/60 transition-all cursor-pointer"
          >
            {/* Title & Lag */}
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <h4 className="font-bold text-slate-900 text-xs truncate">
                  {corr.title}
                </h4>
                <p className="text-[10px] font-mono text-slate-400">
                  Trigger: <strong className="text-slate-700">{corr.triggerEvent}</strong>
                </p>
              </div>

              <div className="flex items-center gap-2 font-mono text-[10px]">
                <span className="rounded bg-slate-100 px-2 py-0.5 text-slate-700">
                  Lag: {corr.lagDurationHours} Hours
                </span>
                <span className="rounded bg-purple-950/60 border border-purple-800 px-2 py-0.5 text-purple-300 font-bold">
                  {corr.correlationConfidence}% Confidence
                </span>
              </div>
            </div>

            {/* Observation & Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="rounded bg-[#F8FAFC] p-2.5 border border-[#E2E8F0] space-y-1">
                <span className="text-[9px] uppercase font-bold text-emerald-400 block">
                  Temporal Observation
                </span>
                <p className="text-slate-700 font-sans leading-relaxed text-[11px]">
                  {corr.observation}
                </p>
              </div>

              <div className="rounded bg-[#F8FAFC] p-2.5 border border-[#E2E8F0] space-y-1">
                <span className="text-[9px] uppercase font-bold text-purple-400 block">
                  Behavioral Inference
                </span>
                <p className="text-slate-700 font-sans leading-relaxed text-[11px]">
                  {corr.analysis}
                </p>
              </div>
            </div>

            {/* Mandatory Regulatory Warning */}
            <div className="rounded border border-amber-900/40 bg-amber-950/20 p-2 text-[9px] font-mono text-amber-300 flex items-start gap-1.5 leading-tight">
              <AlertTriangle className="size-3 text-amber-400 shrink-0 mt-0.5" />
              <span>
                <strong>Statutory Notice:</strong> {corr.disclaimer}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
