import React from "react";
import {
  Flame,
  ShieldAlert,
  Clock,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  CreditCard,
  PhoneCall,
  Cpu,
  TrendingUp,
  MapPin,
  ArrowRight,
  User,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { AnomalyAlert } from "@/utils/anomalyDetection";

interface AlertStreamProps {
  alerts: AnomalyAlert[];
  selectedAlertId: string | null;
  onSelectAlert: (id: string) => void;
}

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  CIRCULAR_FINANCIAL_LOOP: CreditCard,
  DEVICE_HOPPING: Cpu,
  COMMUNICATION_BURST: PhoneCall,
  NETWORK_EXPANSION_SURGE: TrendingUp,
  GEOSPATIAL_CO_LOCATION: MapPin,
};

export function AlertStream({
  alerts,
  selectedAlertId,
  onSelectAlert,
}: AlertStreamProps) {
  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden select-none bg-[#0B0F14] font-sans">
      {/* Top Header */}
      <div className="border-b border-slate-800 bg-[#121820] px-4 py-2 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 font-mono">
          <span className="text-slate-400 uppercase font-bold text-[10px]">
            Active Alert Stream:
          </span>
          <span className="font-bold text-sky-400">{alerts.length} Flagged Anomalies</span>
        </div>

        <span className="text-[10px] font-mono text-slate-500">
          Ranked by algorithmic severity & confidence
        </span>
      </div>

      {/* Alert Cards Stream */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-2.5 custom-scrollbar">
        {alerts.length === 0 ? (
          <div className="rounded border border-dashed border-slate-800 p-8 text-center text-slate-500 font-mono text-xs">
            No behavioral anomaly patterns match the active filter criteria.
          </div>
        ) : (
          alerts.map((alert) => {
            const isSelected = selectedAlertId === alert.id;
            const Icon = CATEGORY_ICONS[alert.category] || ShieldAlert;
            const isCrit = alert.severity === "CRITICAL";
            const isHigh = alert.severity === "HIGH";

            return (
              <div
                key={alert.id}
                onClick={() => onSelectAlert(alert.id)}
                className={cn(
                  "rounded-lg border p-3.5 transition-all cursor-pointer space-y-2.5 relative",
                  isSelected
                    ? "border-sky-500 bg-[#14202C] shadow-lg ring-1 ring-sky-400/50"
                    : "border-slate-800 bg-[#10161E] hover:border-slate-700 hover:bg-[#131A24]"
                )}
              >
                {/* Header Line */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2.5 min-w-0">
                    <span
                      className={cn(
                        "flex size-7 shrink-0 items-center justify-center rounded border shadow-xs mt-0.5",
                        isCrit
                          ? "border-red-500/60 bg-red-950/60 text-red-300"
                          : isHigh
                          ? "border-amber-500/60 bg-amber-950/60 text-amber-300"
                          : "border-slate-700 bg-slate-800 text-sky-300"
                      )}
                    >
                      <Icon className="size-3.5" />
                    </span>

                    <div className="min-w-0">
                      <h4 className="font-bold text-slate-100 text-xs truncate">
                        {alert.title}
                      </h4>
                      <p className="text-[10px] font-mono text-slate-400 truncate">
                        ID: <span className="text-slate-300 font-semibold">{alert.id}</span> · Case:{" "}
                        <span className="text-sky-300 font-semibold">{alert.caseId}</span> · Target:{" "}
                        <span className="text-slate-200 font-bold">{alert.primaryEntityName}</span>
                      </p>
                    </div>
                  </div>

                  {/* Severity Badge */}
                  <span
                    className={cn(
                      "shrink-0 flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[9px] font-bold uppercase",
                      isCrit
                        ? "bg-red-950/80 text-red-300 border border-red-500/60"
                        : isHigh
                        ? "bg-amber-950/80 text-amber-300 border border-amber-500/50"
                        : "bg-slate-800 text-slate-300 border border-slate-700"
                    )}
                  >
                    {isCrit && <Flame className="size-2.5 text-red-400 animate-pulse" />}
                    {alert.severity}
                  </span>
                </div>

                {/* Metrics HUD Line */}
                <div className="grid grid-cols-3 gap-2 border-t border-slate-800/80 pt-2 font-mono text-[10px] text-slate-400">
                  <div>
                    <span className="text-slate-500">CONFIDENCE: </span>
                    <strong className="text-emerald-400">{alert.confidenceScore}%</strong>
                  </div>
                  <div>
                    <span className="text-slate-500">STATUS: </span>
                    <strong className="text-sky-300">{alert.status.replace("_", " ")}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500">TIME: </span>
                    <strong className="text-slate-300">
                      {new Date(alert.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </strong>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
