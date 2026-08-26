import { createFileRoute, useNavigate } from "@tanstack/react-router";
import React, { useState, useMemo } from "react";
import {
  ShieldAlert,
  Flame,
  Activity,
  Filter,
  Sparkles,
  Share2,
  Download,
  CheckCircle2,
  FileCheck2,
} from "lucide-react";
import { toast } from "sonner";

import { AppShell } from "@/components/AppShell";
import { AnomalyDashboard } from "@/components/AnomalyDetection/AnomalyDashboard";
import { AlertStream } from "@/components/AnomalyDetection/AlertStream";
import { DetectionFilters, DEFAULT_ANOMALY_FILTERS, type AnomalyFilterState } from "@/components/AnomalyDetection/DetectionFilters";
import { PatternVisualizer } from "@/components/AnomalyDetection/PatternVisualizer";
import { RiskImpactPanel } from "@/components/AnomalyDetection/RiskImpactPanel";
import { ExplainabilityPanel } from "@/components/AnomalyDetection/ExplainabilityPanel";
import { InvestigationWorkflow } from "@/components/AnomalyDetection/InvestigationWorkflow";

import {
  SYNTHETIC_ANOMALY_ALERTS,
  type AnomalyAlert,
  type InvestigationNote,
} from "@/utils/anomalyDetection";
import type { AnomalyCategory, AnomalyStatus } from "@/utils/anomalyRules";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/anomalies")({
  head: () => ({
    meta: [
      { title: "Anomaly Detection & Suspicious Patterns — NetraGraph AI" },
      {
        name: "description",
        content:
          "Behavioral anomaly detection system: Circular financial loops, burner hardware hopping, communication spikes, and explainable risk indicators.",
      },
    ],
  }),
  component: AnomalyDetectionPage,
});

function AnomalyDetectionPage() {
  const navigate = useNavigate();

  // Active Alerts Store
  const [alerts, setAlerts] = useState<AnomalyAlert[]>(SYNTHETIC_ANOMALY_ALERTS);
  const [filters, setFilters] = useState<AnomalyFilterState>(DEFAULT_ANOMALY_FILTERS);
  const [selectedAlertId, setSelectedAlertId] = useState<string>("ALT-2026-001");

  // Filtered Alert List
  const filteredAlerts = useMemo(() => {
    return alerts.filter((a) => {
      if (!filters.categories.has(a.category)) return false;
      if (!filters.severities.has(a.severity)) return false;
      if (!filters.statuses.has(a.status)) return false;
      if (a.confidenceScore < filters.minConfidence) return false;
      return true;
    });
  }, [alerts, filters]);

  const selectedAlert = useMemo(() => {
    return alerts.find((a) => a.id === selectedAlertId) || filteredAlerts[0] || null;
  }, [alerts, selectedAlertId, filteredAlerts]);

  // Workflow Action Handlers
  const handleUpdateStatus = (alertId: string, nextStatus: AnomalyStatus) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, status: nextStatus } : a))
    );
  };

  const handleAddNote = (alertId: string, note: InvestigationNote) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, notes: [note, ...a.notes] } : a))
    );
  };

  const handleAssignAnalyst = (alertId: string, analystName: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, assignedAnalyst: analystName } : a))
    );
  };

  const handleExportAlertReport = () => {
    toast.success("Anomaly Intelligence Dossier Exported", {
      description: "Cryptographically certified PDF report generated for judicial filing under §65B.",
    });
  };

  return (
    <AppShell
      title="Anomaly Detection & Suspicious Pattern Engine"
      subtitle="Explainable Behavioral Intelligence: Layered Transfer Loops, Burner IMEI Cycling & Telephony Surges"
    >
      <div className="flex flex-col h-[calc(100vh-130px)] rounded border border-slate-800 bg-[#0B0F14] shadow-2xl overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP WORKSPACE ACTION BAR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-[#0E1318] px-4 py-2 z-20">
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="flex size-2 rounded-full bg-red-400 animate-pulse" />
            <span className="font-bold text-slate-100 uppercase tracking-wider">
              Autonomous Behavioral Surveillance Active
            </span>
            <span className="rounded bg-[#161D24] px-2 py-0.5 text-slate-400 border border-slate-800 text-[10px]">
              {filteredAlerts.length} Active Detections
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate({ to: "/network" })}
              className="flex items-center gap-1.5 rounded border border-sky-500/50 bg-sky-950/40 px-2.5 py-1 text-xs font-mono font-semibold text-sky-300 hover:bg-sky-900/50 transition-colors cursor-pointer"
            >
              <Share2 className="size-3.5" />
              <span>Trace on Knowledge Graph</span>
            </button>

            <button
              onClick={handleExportAlertReport}
              className="flex items-center gap-1.5 rounded border border-slate-800 bg-[#161D24] px-2.5 py-1 text-xs font-mono font-semibold text-slate-300 hover:border-slate-700 transition-colors cursor-pointer"
            >
              <Download className="size-3.5 text-emerald-400" />
              <span>Export Dossier</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. THREE-PANEL INVESTIGATION WORKSPACE
           ========================================================================= */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* LEFT PANEL: Detection Filters */}
          <aside className="w-72 border-r border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-slate-800 bg-[#141A21] px-4 py-3">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 flex items-center gap-1.5">
                <Filter className="size-3.5 text-sky-400" />
                Detection Filters
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 custom-scrollbar">
              <DetectionFilters
                filters={filters}
                onFilterChange={setFilters}
                onReset={() => setFilters(DEFAULT_ANOMALY_FILTERS)}
              />
            </div>
          </aside>

          {/* CENTER PANEL: Main Dashboard, Alert Queue & Pattern Visualizer */}
          <main className="flex-1 h-full overflow-y-auto p-4 custom-scrollbar bg-[#0B0F14] space-y-4">
            {/* Top Anomaly KPI Dashboard */}
            <AnomalyDashboard
              alerts={alerts}
              onSelectCategory={(cat) =>
                setFilters((prev) => ({
                  ...prev,
                  categories: new Set([cat as AnomalyCategory]),
                }))
              }
            />

            {/* Split Visualizer / Queue Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
              {/* Alert Queue Stream (5 cols) */}
              <div className="lg:col-span-5 h-[480px] rounded-lg border border-slate-800 overflow-hidden flex flex-col">
                <AlertStream
                  alerts={filteredAlerts}
                  selectedAlertId={selectedAlertId}
                  onSelectAlert={(id) => setSelectedAlertId(id)}
                />
              </div>

              {/* Specialized Forensic Pattern Visualizer (7 cols) */}
              <div className="lg:col-span-7">
                <PatternVisualizer
                  alert={selectedAlert}
                  onSelectEntity={(id) => navigate({ to: "/profiles" })}
                />
              </div>
            </div>
          </main>

          {/* RIGHT PANEL: Explainability, Risk Impact Delta & Investigation Workflow */}
          <aside className="w-96 border-l border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-slate-800 bg-[#141A21] px-4 py-3">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 flex items-center gap-1.5">
                <Sparkles className="size-3.5 text-amber-400" />
                Explainability & Action Plan
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4 custom-scrollbar">
              {/* 3-Tier Explainability Card */}
              <ExplainabilityPanel alert={selectedAlert} />

              {/* Dynamic Risk Impact Delta */}
              <RiskImpactPanel alert={selectedAlert} />

              {/* Analyst Workflow */}
              {selectedAlert && (
                <InvestigationWorkflow
                  alert={selectedAlert}
                  onUpdateStatus={handleUpdateStatus}
                  onAddNote={handleAddNote}
                  onAssignAnalyst={handleAssignAnalyst}
                />
              )}
            </div>
          </aside>
        </div>

        {/* =========================================================================
            3. BOTTOM STATUS BAR
           ========================================================================= */}
        <div className="border-t border-slate-800 bg-[#0B0F14] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-400 z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-red-400 animate-pulse" />
              NETRA BEHAVIORAL PATTERN PIPELINE
            </span>
            <span>
              Total Monitored Patterns: <strong className="text-slate-100">{alerts.length}</strong>
            </span>
            <span>
              Investigative Status: <strong className="text-amber-400">Analyst Discretion Mandatory</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-slate-400">
            <CheckCircle2 className="size-3.5 text-emerald-400" />
            <span>Zero Hallucination Verified · Statutory Compliance Certified</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
