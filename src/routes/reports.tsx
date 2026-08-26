import { createFileRoute } from "@tanstack/react-router";
import React, { useState } from "react";
import { FileText, Download, ShieldCheck, FolderSearch } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { ReportBuilder } from "@/components/CaseWorkspace/ReportBuilder";

export const Route = createFileRoute("/reports")({
  head: () => ({
    meta: [
      { title: "Intelligence Reports & Dossier Builder — NetraGraph AI" },
      {
        name: "description",
        content:
          "Court-admissible judicial intelligence dossiers, Section 65B forensic reports, and customizable investigation briefs.",
      },
    ],
  }),
  component: ReportsPage,
});

function ReportsPage() {
  const [selectedCaseId, setSelectedCaseId] = useState<string>("CASE-2026-N09");

  return (
    <AppShell
      title="Intelligence Reports & Dossier Builder"
      subtitle="Judicial Intelligence Report Composition, Section 65B Statutory Certification & Multi-Format Dossier Export"
    >
      <div className="space-y-4 font-sans select-none">
        {/* Case Selection Strip */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 bg-[#0E1318] p-3.5 shadow-xl">
          <div className="flex items-center gap-2 font-mono text-xs">
            <FolderSearch className="size-4 text-sky-400" />
            <span className="text-slate-400 font-bold uppercase">Select Investigation Docket:</span>
            <select
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              className="rounded border border-slate-800 bg-[#161D24] px-2.5 py-1 text-xs text-sky-300 font-mono outline-none cursor-pointer"
            >
              <option value="CASE-2026-N09">CASE-2026-N09 (Operation Netra-Vigil)</option>
              <option value="CASE-2026-B12">CASE-2026-B12 (Bhubaneswar SIM Box Ring)</option>
              <option value="CASE-2026-R44">CASE-2026-R44 (LockNet Ransomware Group)</option>
              <option value="CASE-2026-H88">CASE-2026-H88 (Inter-State Hawala Conduits)</option>
            </select>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-emerald-400">
            <ShieldCheck className="size-4" />
            <span>Indian Evidence Act Section 65B Certified Export</span>
          </div>
        </div>

        {/* Full Report Builder Workspace */}
        <ReportBuilder caseId={selectedCaseId} />
      </div>
    </AppShell>
  );
}
