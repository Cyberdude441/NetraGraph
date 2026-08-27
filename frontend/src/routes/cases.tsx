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
      title="Case Investigation Workspace"
      subtitle="Operation Netra-Vigil · Case Docket CASE-2026-N09 · Lead: Insp. D. Bose"
    >
      <div className="flex min-h-[calc(100vh-130px)] flex-col rounded-md border border-[#E5E7EB] bg-white shadow-xs overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP CASE HEADER BAR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E5E7EB] bg-[#F8FAF8] px-5 py-3 z-20">
          <div className="flex flex-wrap items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-[#064E3B] font-bold">
              <FolderSearch className="size-4 text-[#16A34A]" />
              <span className="text-sm text-[#111827]">Operation Netra-Vigil</span>
              <span className="font-mono text-xs bg-white px-2 py-0.5 rounded border border-[#E5E7EB] text-[#064E3B] font-semibold">
                {activeCaseId}
              </span>
            </span>
            <span className="text-[#D1D5DB]">|</span>
            <span className="inline-flex items-center gap-1 rounded bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[#16A34A] text-xs font-semibold">
              <span className="size-1.5 rounded-full bg-[#16A34A]" />
              Status: Under Analysis
            </span>
            <span className="rounded bg-red-50 border border-red-200 px-2 py-0.5 text-[#DC2626] text-xs font-semibold">
              Priority: Critical
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setIngestModalOpen(true)}
              className="flex items-center gap-1.5 rounded-md bg-[#064E3B] hover:bg-[#04382A] px-3.5 py-1.5 text-xs font-semibold text-white transition-colors cursor-pointer shadow-xs"
            >
              <Plus className="size-3.5 text-white" />
              <span>Attach Exhibit</span>
            </button>

            <button
              onClick={() => navigate({ to: "/network" })}
              className="flex items-center gap-1.5 rounded-md border border-[#E5E7EB] bg-white hover:bg-[#F3F4F6] px-3.5 py-1.5 text-xs font-semibold text-[#111827] transition-colors cursor-pointer shadow-xs"
            >
              <Share2 className="size-3.5 text-[#064E3B]" />
              <span>Knowledge Graph</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. THREE-COLUMN CASE WORKSPACE
           ========================================================================= */}
        <div className="grid min-h-0 flex-1 grid-cols-1 overflow-hidden relative xl:grid-cols-[14rem_minmax(0,1fr)_18rem]">
          {/* LEFT PANEL: Case Navigation */}
          <aside className="hidden border-r border-[#E5E7EB] bg-[#F8FAF8] xl:flex xl:min-h-0 xl:flex-col select-none">
            <div className="min-h-0 flex-1 overflow-y-auto p-3 space-y-3 [scrollbar-color:#10B981_transparent] [scrollbar-width:thin]">
              <CaseNavigation activeTab={activeTab} onSelectTab={handleNavigateTab} />
            </div>
          </aside>

          {/* CENTER PANEL: Main Active Module View */}
          <main className="min-w-0 min-h-0 overflow-y-auto bg-white p-5 space-y-5 [scrollbar-color:#10B981_transparent] [scrollbar-width:thin]">
            {/* View 1: Case Overview & Summary */}
            {activeTab === "overview" && (
              <div className="space-y-5">
                <CaseDashboard caseId={activeCaseId} onNavigateTab={handleNavigateTab} />
              </div>
            )}

            {/* View 2: Cryptographic Evidence Chain */}
            {activeTab === "evidence_chain" && <EvidenceChain />}

            {/* View 3: Intelligence Report Builder */}
            {activeTab === "report_builder" && <ReportBuilder caseId={activeCaseId} />}

            {/* View 4: Audit Log Register */}
            {activeTab === "audit_history" && (
              <div className="rounded-md border border-[#D9E2EC] bg-white p-5 text-xs select-none space-y-4 font-sans shadow-sm">
                <div className="border-b border-[#E2E8F0] pb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <History className="size-4 text-[#065F46]" />
                    <div>
                      <h3 className="font-bold text-sm text-[#0F172A]">
                        Forensic Audit Log Register
                      </h3>
                      <p className="text-xs text-[#64748B]">
                        Every system modification, entity merge, and dossier export is logged under Section 65B.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-[#D9E2EC] bg-[#F8FAFC] text-[#64748B] font-semibold">
                      <tr>
                        <th className="px-3.5 py-2.5">Timestamp</th>
                        <th className="px-3.5 py-2.5">Module</th>
                        <th className="px-3.5 py-2.5">Investigator</th>
                        <th className="px-3.5 py-2.5">Action Performed</th>
                        <th className="px-3.5 py-2.5">SHA-256 Hash</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E2E8F0] text-[#0F172A]">
                      {INITIAL_GLOBAL_AUDIT_LOGS.map((log) => (
                        <tr key={log.id} className="hover:bg-[#F8FAFC] transition-colors">
                          <td className="px-3.5 py-2.5 text-[#64748B] whitespace-nowrap">
                            {new Date(log.timestamp).toLocaleString()}
                          </td>
                          <td className="px-3.5 py-2.5 text-[#065F46] font-medium">{log.module}</td>
                          <td className="px-3.5 py-2.5 font-semibold text-[#0F172A]">{log.officerName}</td>
                          <td className="px-3.5 py-2.5 text-[#475569]">{log.action}</td>
                          <td className="px-3.5 py-2.5 text-[#198754] font-mono text-[11px] truncate max-w-xs" title={log.verificationHash}>
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

          {/* RIGHT PANEL: Context and action rail */}
          <aside className="hidden min-h-0 overflow-y-auto border-l border-[#E5E7EB] bg-[#F8FAFC] p-4 space-y-4 xl:block [scrollbar-color:#10B981_transparent] [scrollbar-width:thin]">
            <InvestigationSummary onNavigateModule={handleNavigateTab} />
            <CollaborationPanel />
          </aside>
        </div>

        {/* =========================================================================
            3. BOTTOM STATUS STRIP
           ========================================================================= */}
        <div className="border-t border-[#D9E2EC] bg-[#F8FAFC] px-5 py-2.5 flex flex-wrap items-center justify-between gap-4 text-xs text-[#64748B] z-20">
          <div className="flex items-center gap-6">
            <span className="font-semibold text-[#0F172A] flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-[#198754]" />
              Case Workspace Active
            </span>
            <span>
              Docket: <strong className="font-mono text-[#065F46]">{activeCaseId}</strong>
            </span>
            <span>
              Evidence: <strong className="text-[#198754]">4 Sealed Records</strong>
            </span>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-[#64748B]">
            <ShieldCheck className="size-4 text-[#198754]" />
            <span>Compliant with Indian Evidence Act §65B & IT Act §69B</span>
          </div>
        </div>
      </div>

      {/* Exhibit Ingestion Modal */}
      <DataIngestionModal
        isOpen={ingestModalOpen}
        onClose={() => setIngestModalOpen(false)}
        onSuccess={() => toast.success("New Exhibit Attached & Sealed")}
      />
    </AppShell>
  );
}
