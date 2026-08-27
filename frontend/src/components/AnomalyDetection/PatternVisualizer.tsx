import React from "react";
import { Cpu, Smartphone, ShieldAlert, Sparkles, User } from "lucide-react";
import type { AnomalyAlert } from "@/utils/anomalyDetection";
import { TransactionAnalyzer } from "./TransactionAnalyzer";
import { CommunicationAnalyzer } from "./CommunicationAnalyzer";
import { NetworkGrowthAnalyzer } from "./NetworkGrowthAnalyzer";
import { LocationAnalyzer } from "./LocationAnalyzer";

interface PatternVisualizerProps {
  alert: AnomalyAlert | null;
  onSelectEntity?: (id: string) => void;
}

export function PatternVisualizer({ alert, onSelectEntity }: PatternVisualizerProps) {
  if (!alert) {
    return (
      <div className="rounded-lg border border-dashed border-[#E2E8F0] bg-white p-12 text-center text-slate-500 font-mono text-xs">
        Select a behavioral anomaly from the alert queue to inspect its forensic pattern.
      </div>
    );
  }

  if (alert.category === "CIRCULAR_FINANCIAL_LOOP" && alert.circularLoop) {
    return <TransactionAnalyzer loop={alert.circularLoop} onSelectEntity={onSelectEntity} />;
  }

  if (alert.category === "COMMUNICATION_BURST" && alert.communicationBurst) {
    return <CommunicationAnalyzer burst={alert.communicationBurst} />;
  }

  if (alert.category === "NETWORK_EXPANSION_SURGE" && alert.networkGrowth) {
    return <NetworkGrowthAnalyzer growth={alert.networkGrowth} />;
  }

  if (alert.category === "GEOSPATIAL_CO_LOCATION" && alert.locationCoLocation) {
    return <LocationAnalyzer location={alert.locationCoLocation} onSelectEntity={onSelectEntity} />;
  }

  if (alert.category === "DEVICE_HOPPING" && alert.burnerDevice) {
    const dev = alert.burnerDevice;
    return (
      <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
        {/* Header */}
        <div className="border-b border-[#E2E8F0] pb-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Cpu className="size-4 text-purple-400" />
            <div>
              <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-900">
                Burner Device Hardware Fingerprint & IMSI Cycling
              </h3>
              <p className="text-[10px] text-slate-400 font-mono">
                Hardware IMEI <strong>{dev.imei}</strong> cycled across {dev.associatedSimCards.length} distinct SIM IMSI registrations.
              </p>
            </div>
          </div>

          <span className="rounded bg-purple-950/60 border border-purple-800 px-2.5 py-1 text-xs font-mono font-bold text-purple-300">
            {dev.concurrentIdentitiesCount} Identities Linked
          </span>
        </div>

        {/* Suspect Info */}
        <div className="rounded border border-[#E2E8F0] bg-white p-3 flex items-center justify-between text-xs font-mono">
          <div>
            <span className="text-[10px] text-slate-500 block">PRIMARY SUSPECT TARGET</span>
            <strong className="text-slate-900 text-sm">{dev.primarySuspectName}</strong>
          </div>
          <div className="text-right">
            <span className="text-[10px] text-slate-500 block">HARDWARE MODEL</span>
            <span className="text-emerald-300 font-bold">{dev.deviceName}</span>
          </div>
        </div>

        {/* SIMs Table */}
        <div className="rounded border border-[#E2E8F0] bg-white overflow-hidden">
          <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] px-3 py-2 text-[10px] font-mono uppercase font-bold text-slate-700">
            Chronological IMSI SIM Subscriptions
          </div>
          <table className="w-full text-left font-mono text-[11px]">
            <thead className="border-b border-[#E2E8F0]/80 bg-[#F8FAFC] text-slate-500 text-[9px] uppercase">
              <tr>
                <th className="px-3 py-1.5">IMSI Identifier</th>
                <th className="px-3 py-1.5">Phone MSISDN</th>
                <th className="px-3 py-1.5">Telecom Circle</th>
                <th className="px-3 py-1.5 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {dev.associatedSimCards.map((sim, i) => (
                <tr key={i} className="hover:bg-[#F8FAFC] transition-colors">
                  <td className="px-3 py-2 text-slate-700">{sim.imsi}</td>
                  <td className="px-3 py-2 font-bold text-slate-900">{sim.phoneNumber}</td>
                  <td className="px-3 py-2 text-slate-400">{sim.carrier}</td>
                  <td className="px-3 py-2 text-right">
                    <span
                      className={cn(
                        "rounded px-1.5 py-0.5 text-[9px] font-bold uppercase",
                        sim.isCurrentActive
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-500/50"
                          : "bg-slate-100 text-slate-500"
                      )}
                    >
                      {sim.isCurrentActive ? "Active" : "Burned"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return null;
}
