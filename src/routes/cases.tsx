import { createFileRoute, useNavigate } from "@tanstack/react-router";
import React, { useState } from "react";
import {
  FolderSearch,
  Plus,
  Share2,
  ShieldCheck,
  FileText,
  Lock,
  History,
  Download,
  Users,
  TrendingUp,
  MapPin,
  Flame,
} from "lucide-react";
import { toast } from "sonner";

import { AppShell } from "@/components/AppShell";
import { CaseDashboard } from "@/components/CaseWorkspace/CaseDashboard";
import { CaseNavigation } from "@/components/CaseWorkspace/CaseNavigation";
import { InvestigationSummary } from "@/components/CaseWorkspace/InvestigationSummary";
import { EvidenceChain } from "@/components/CaseWorkspace/EvidenceChain";
import { ReportBuilder } from "@/components/CaseWorkspace/ReportBuilder";
import { CollaborationPanel } from "@/components/CaseWorkspace/CollaborationPanel";
import { SecurityPanel } from "@/components/CaseWorkspace/SecurityPanel";
import { INITIAL_GLOBAL_AUDIT_LOGS } from "@/services/auditService";
import { DataIngestionModal } from "@/components/ingestion/DataIngestionModal";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/cases")({
  head: () => ({
    meta: [
      { title: "Investigation Case Workspace — NetraGraph AI" },
      {
        name: "description",
        content:
          "Enterprise Cyber Investigation Workspace: Case lifecycle management, cryptographic SHA-256 evidence chain, Section 65B compliance, and judicial dossier compilation.",
      },
    ],
  }),
  component: CaseWorkspacePage,
});

function CaseWorkspacePage() {
  const navigate = useNavigate();

  const [activeCaseId, setActiveCaseId] = useState<string>("CASE-2026-N09");
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [ingestModalOpen, setIngestModalOpen] = useState<boolean>(false);

  const handleNavigateTab = (tabId: string) => {
    if (tabId === "entities") navigate({ to: "/profiles" });
    else if (tabId === "network") navigate({ to: "/network" });
    else if (tabId === "analytics") navigate({ to: "/analytics" });
    else if (tabId === "geo_timeline") navigate({ to: "/geo-timeline" });
    else if (tabId === "anomalies") navigate({ to: "/anomalies" });
    else setActiveTab(tabId);
  };

  return (
    <AppShell
      title="Investigation Case Workspace"
      subtitle="Case Lifecycle Management, Cryptographic Evidence Vault (§65B) & Judicial Dossier Compilation"
    >
      <div className="flex flex-col h-[calc(100vh-130px)] rounded border border-slate-800 bg-[#0B0F14] shadow-2xl overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP CASE HEADER BAR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-[#0E1318] px-4 py-2 z-20">
          <div className="flex items-center gap-3 font-mono text-xs">
            <span className="flex items-center gap-1.5 text-sky-400 font-bold">
              <FolderSearch className="size-3.5" />
              <span>DOCKET: {activeCaseId}</span>
            </span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400">
              State Police HQ Cyber Cell · Lead: <strong className="text-slate-200">Insp. D. Bose</strong>
            </span>
            <span className="rounded bg-red-950/60 border border-red-800 px-2 py-0.5 text-red-300 text-[10px] font-bold">
              CRITICAL PRIORITY
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIngestModalOpen(true)}
              className="flex items-center gap-1 rounded border border-slate-800 bg-[#161D24] px-2.5 py-1 text-xs font-mono font-semibold text-slate-200 hover:border-sky-500 transition-colors cursor-pointer"
            >
              <Plus className="size-3.5 text-sky-400" />
              <span>Attach New Exhibit</span>
            </button>

            <button
              onClick={() => navigate({ to: "/network" })}
              className="flex items-center gap-1 rounded border border-sky-500/50 bg-sky-950/40 px-2.5 py-1 text-xs font-mono font-semibold text-sky-300 hover:bg-sky-900/50 transition-colors cursor-pointer"
            >
              <Share2 className="size-3.5" />
              <span>Knowledge Graph</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. THREE-PANEL CASE WORKSPACE
           ========================================================================= */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* LEFT PANEL: Case Navigation */}
          <aside className="w-64 border-r border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none">
            <div className="flex-1 overflow-y-auto p-3.5 space-y-4 custom-scrollbar">
              <CaseNavigation activeTab={activeTab} onSelectTab={handleNavigateTab} />
            </div>
          </aside>

          {/* CENTER PANEL: Main Active Module View */}
          <main className="flex-1 h-full overflow-y-auto p-4 custom-scrollbar bg-[#0B0F14] space-y-4">
            {/* View 1: Case Overview & Summary */}
            {activeTab === "overview" && (
              <div className="space-y-4">
                <CaseDashboard caseId={activeCaseId} onNavigateTab={handleNavigateTab} />
                <InvestigationSummary onNavigateModule={handleNavigateTab} />
                <CollaborationPanel />
              </div>
            )}

            {/* View 2: Cryptographic Evidence Chain */}
            {activeTab === "evidence_chain" && <EvidenceChain />}

            {/* View 3: Intelligence Report Builder */}
            {activeTab === "report_builder" && <ReportBuilder caseId={activeCaseId} />}

            {/* View 4: Audit Log Register */}
            {activeTab === "audit_history" && (
              <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
                <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <History className="size-4 text-emerald-400" />
                    <div>
                      <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
                        Immutable Global Forensic Audit Log Register
                      </h3>
                      <p className="text-[10px] text-slate-400 font-mono">
                        Every system modification, merge, and export is cryptographically sealed under Section 65B.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left font-mono text-[11px]">
                    <thead className="border-b border-slate-800 bg-[#121820] text-slate-400 uppercase text-[9px]">
                      <tr>
                        <th className="px-3 py-2">Timestamp</th>
                        <th className="px-3 py-2">Module</th>
                        <th className="px-3 py-2">Officer</th>
                        <th className="px-3 py-2">Action Performed</th>
                        <th className="px-3 py-2">Verification SHA-256 Hash</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80 text-slate-300">
                      {INITIAL_GLOBAL_AUDIT_LOGS.map((log) => (
                        <tr key={log.id} className="hover:bg-[#121820] transition-colors">
                          <td className="px-3 py-2 text-slate-400 whitespace-nowrap">
                            {new Date(log.timestamp).toLocaleString()}
                          </td>
                          <td className="px-3 py-2 text-sky-300">{log.module}</td>
                          <td className="px-3 py-2 font-bold text-slate-100">{log.officerName}</td>
                          <td className="px-3 py-2 text-slate-200">{log.action}</td>
                          <td className="px-3 py-2 text-emerald-400 text-[10px] truncate max-w-xs" title={log.verificationHash}>
                            {log.verificationHash.slice(0, 16)}...
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* View 5: Security & RBAC */}
            {activeTab === "security" && <SecurityPanel />}
          </main>
        </div>

        {/* =========================================================================
            3. BOTTOM STATUS STRIP
           ========================================================================= */}
        <div className="border-t border-slate-800 bg-[#0B0F14] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-400 z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
              NETRA CASE WORKSPACE
            </span>
            <span>
              Active Case: <strong className="text-slate-100">{activeCaseId}</strong>
            </span>
            <span>
              Chain Status: <strong className="text-emerald-400">4 Blocks Cryptographically Sealed</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-slate-400">
            <ShieldCheck className="size-3.5 text-emerald-400" />
            <span>IT Act §69B & Indian Evidence Act §65B Certified</span>
          </div>
        </div>
      </div>

      {/* Exhibit Ingestion Modal */}
      <DataIngestionModal
        isOpen={ingestModalOpen}
        onClose={() => setIngestModalOpen(false)}
        onSuccess={() => toast.success("New Exhibit Ingested & Hashed")}
      />
    </AppShell>
  );
}
