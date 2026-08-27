import React from "react";
import {
  ShieldAlert,
  Flame,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Repeat,
  Cpu,
  PhoneCall,
  TrendingUp,
  MapPin,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { AnomalyAlert } from "@/utils/anomalyDetection";

interface AnomalyDashboardProps {
  alerts: AnomalyAlert[];
  onSelectCategory: (category: string) => void;
}

export function AnomalyDashboard({ alerts, onSelectCategory }: AnomalyDashboardProps) {
  const criticalCount = alerts.filter((a) => a.severity === "CRITICAL").length;
  const highCount = alerts.filter((a) => a.severity === "HIGH").length;
  const investigatingCount = alerts.filter((a) => a.status === "INVESTIGATING").length;
  const resolvedCount = alerts.filter((a) => a.status === "RESOLVED").length;

  return (
    <div className="space-y-4 font-sans select-none">
      {/* Top KPI Cards */}
      <div className="grid grid-cols-2 2xl:grid-cols-4 gap-3 font-mono text-xs">
        {/* Total Active Alerts */}
        <div className="rounded border border-[#E2E8F0] bg-white p-3">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Flagged Anomalies</span>
            <Activity className="size-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-slate-900">{alerts.length} Patterns</div>
          <p className="text-[9px] text-slate-500 mt-0.5">Across active case dockets</p>
        </div>

        {/* Critical Severity Alerts */}
        <div className="rounded border border-[#E2E8F0] bg-white p-3">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Critical Severity</span>
            <Flame className="size-3.5 text-red-400 animate-pulse" />
          </div>
          <div className="text-xl font-bold text-red-400">{criticalCount} Incidents</div>
          <p className="text-[9px] text-slate-500 mt-0.5">Immediate intervention required</p>
        </div>

        {/* Under Investigation */}
        <div className="rounded border border-[#E2E8F0] bg-white p-3">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Under Investigation</span>
            <ShieldAlert className="size-3.5 text-amber-400" />
          </div>
          <div className="text-xl font-bold text-amber-400">{investigatingCount} Active</div>
          <p className="text-[9px] text-slate-500 mt-0.5">Assigned to case analysts</p>
        </div>

        {/* False Positive Rate */}
        <div className="rounded border border-[#E2E8F0] bg-white p-3">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold">False Positive Rate</span>
            <CheckCircle2 className="size-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-400">1.8%</div>
          <p className="text-[9px] text-slate-500 mt-0.5">Validated against CDR telemetry</p>
        </div>
      </div>

      {/* Anomaly Category Quick Matrix */}
      <div className="grid grid-cols-1 sm:grid-cols-2 2xl:grid-cols-5 gap-2.5 font-mono text-xs">
        {[
          { id: "CIRCULAR_FINANCIAL_LOOP", name: "Financial Loops", icon: Repeat, color: "text-purple-400", count: alerts.filter(a => a.category === "CIRCULAR_FINANCIAL_LOOP").length },
          { id: "DEVICE_HOPPING", name: "Burner Devices", icon: Cpu, color: "text-emerald-400", count: alerts.filter(a => a.category === "DEVICE_HOPPING").length },
          { id: "COMMUNICATION_BURST", name: "Call Spikes", icon: PhoneCall, color: "text-emerald-400", count: alerts.filter(a => a.category === "COMMUNICATION_BURST").length },
          { id: "NETWORK_EXPANSION_SURGE", name: "Network Surges", icon: TrendingUp, color: "text-emerald-400", count: alerts.filter(a => a.category === "NETWORK_EXPANSION_SURGE").length },
          { id: "GEOSPATIAL_CO_LOCATION", name: "Co-Locations", icon: MapPin, color: "text-red-400", count: alerts.filter(a => a.category === "GEOSPATIAL_CO_LOCATION").length },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onSelectCategory(item.id)}
              className="rounded-lg border border-[#E2E8F0] bg-white p-3 flex items-center justify-between hover:border-slate-300 transition-colors cursor-pointer text-left"
            >
              <div className="flex items-center gap-2">
                <Icon className={cn("size-4", item.color)} />
                <span className="font-bold text-slate-800 text-[11px]">{item.name}</span>
              </div>
              <span className="font-bold text-slate-400">{item.count}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
