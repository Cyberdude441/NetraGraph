import React from "react";
import { Flame, ShieldAlert, MapPin, TrendingUp, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RiskHeatmapZone } from "@/utils/networkMetrics";

interface RiskHeatmapProps {
  zones: RiskHeatmapZone[];
  onSelectZone?: (zoneName: string) => void;
}

export function RiskHeatmap({ zones, onSelectZone }: RiskHeatmapProps) {
  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Flame className="size-4 text-red-400 animate-pulse" />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
              Network Threat Density & Risk Concentration Heatmap
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              Spatial and organizational risk clustering based on synthetic telemetry and financial loss velocity.
            </p>
          </div>
        </div>

        <span className="rounded bg-red-950/40 border border-red-800/60 px-2.5 py-1 text-xs font-mono font-bold text-red-300">
          {zones.length} Analyzed Sector Zones
        </span>
      </div>

      {/* Heatmap Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {zones.map((z, idx) => {
          const isExtreme = z.concentrationLevel === "Extreme";
          const isHigh = z.concentrationLevel === "High";

          return (
            <div
              key={idx}
              onClick={() => onSelectZone && onSelectZone(z.zoneName)}
              className={cn(
                "rounded-lg border p-3.5 space-y-2.5 transition-all cursor-pointer",
                isExtreme
                  ? "border-red-600/70 bg-[#1C1215] shadow-lg hover:border-red-500"
                  : isHigh
                  ? "border-amber-600/60 bg-[#1A1612] hover:border-amber-500"
                  : "border-slate-800 bg-[#121820] hover:border-slate-700"
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-1.5 min-w-0">
                  <MapPin
                    className={cn(
                      "size-3.5 shrink-0",
                      isExtreme ? "text-red-400" : isHigh ? "text-amber-400" : "text-slate-400"
                    )}
                  />
                  <h4 className="font-bold text-slate-100 text-xs truncate">
                    {z.zoneName}
                  </h4>
                </div>

                <span
                  className={cn(
                    "font-mono text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase",
                    isExtreme
                      ? "bg-red-950 text-red-300 border-red-500/50"
                      : isHigh
                      ? "bg-amber-950 text-amber-300 border-amber-500/50"
                      : "bg-slate-800 text-slate-300 border-slate-700"
                  )}
                >
                  {z.concentrationLevel}
                </span>
              </div>

              <div className="space-y-1 font-mono text-[10px] text-slate-400 border-t border-slate-800/80 pt-2">
                <div className="flex items-center justify-between">
                  <span>Syndicate Group:</span>
                  <span className="text-slate-200 truncate max-w-[170px]">{z.clusterGroup}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Average Risk:</span>
                  <strong className={cn(z.averageRisk >= 85 ? "text-red-400" : "text-amber-400")}>
                    {z.averageRisk}/100
                  </strong>
                </div>
                <div className="flex items-center justify-between">
                  <span>Critical Nodes:</span>
                  <span className="text-slate-200">{z.criticalRiskCount} Entities</span>
                </div>
                {z.totalFinancialLoss > 0 && (
                  <div className="flex items-center justify-between">
                    <span>Financial Velocity:</span>
                    <span className="text-amber-300 font-bold">
                      ₹{(z.totalFinancialLoss / 10000000).toFixed(2)} Cr
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
