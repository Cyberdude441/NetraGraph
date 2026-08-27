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
      title="Alerts & Anomalies"
      subtitle="Automated Suspicious Pattern Detection: Circular Transactions, Burner Hardware Hopping & Activity Surges"
    >
      <div className="flex min-h-[calc(100vh-130px)] flex-col rounded-md border border-[#E5E7EB] bg-white shadow-xs overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP WORKSPACE ACTION BAR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E5E7EB] bg-[#F8FAF8] px-4 py-2.5 z-20">
          <div className="flex items-center gap-2 text-xs">
            <span className="flex size-2 rounded-full bg-[#16A34A] animate-pulse" />
            <span className="font-bold text-[#111827]">
              Automated Anomaly Scanner Active
            </span>
            <span className="rounded-md bg-white px-2.5 py-0.5 text-[#064E3B] font-semibold border border-[#E5E7EB] text-xs">
              {filteredAlerts.length} Flagged Anomalies
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate({ to: "/network" })}
              className="flex items-center gap-1.5 rounded-md bg-[#064E3B] hover:bg-[#04382A] px-3.5 py-1.5 text-xs font-semibold text-white transition-colors cursor-pointer shadow-xs"
            >
              <Share2 className="size-3.5" />
              <span>Trace on Knowledge Graph</span>
            </button>

            <button
              onClick={handleExportAlertReport}
              className="flex items-center gap-1.5 rounded-md border border-[#E5E7EB] bg-white px-3.5 py-1.5 text-xs font-semibold text-[#111827] hover:bg-[#F3F4F6] transition-colors cursor-pointer shadow-xs"
            >
              <Download className="size-3.5 text-[#16A34A]" />
              <span>Export Evidence Report</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. THREE-PANEL INVESTIGATION WORKSPACE
           ========================================================================= */}
        <div className="flex min-h-0 flex-1 overflow-hidden relative">
          {/* LEFT PANEL: Detection Filters */}
          <aside className="w-72 shrink-0 border-r border-[#E5E7EB] bg-[#F8FAF8] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-[#E5E7EB] bg-white px-4 py-3">
              <span className="text-xs font-bold text-[#111827] flex items-center gap-1.5">
                <Filter className="size-4 text-[#064E3B]" />
                Anomaly Filters
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5">
              <DetectionFilters
                filters={filters}
                onFilterChange={setFilters}
                onReset={() => setFilters(DEFAULT_ANOMALY_FILTERS)}
              />
            </div>
          </aside>

          {/* CENTER PANEL: Main Dashboard, Alert Queue & Pattern Visualizer */}
          <main className="min-w-0 flex-1 h-full overflow-y-auto p-4 bg-[#F8FAF8] space-y-4">
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
              <div className="lg:col-span-5 h-[480px] rounded-md border border-[#D9E2EC] overflow-hidden flex flex-col bg-white shadow-xs">
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
          <aside className="w-72 shrink-0 border-l border-[#D9E2EC] bg-white flex flex-col h-full overflow-hidden select-none 2xl:w-96">
            <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] px-4 py-3">
              <span className="text-xs font-bold text-[#0F172A] flex items-center gap-1.5">
                <Sparkles className="size-4 text-[#065F46]" />
                Explanation & Actions
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4">
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
        <div className="border-t border-[#D9E2EC] bg-[#F8FAFC] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs text-[#64748B] z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-[#065F46] flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-[#198754]" />
              Pattern Analysis Stream
            </span>
            <span>
              Total Tracked Patterns: <strong className="text-[#0F172A]">{alerts.length}</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-xs text-[#64748B]">
            <CheckCircle2 className="size-3.5 text-[#198754]" />
            <span>Cryptographically Verified Evidentiary Ledger</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
