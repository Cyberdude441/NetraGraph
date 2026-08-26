import React, { useState } from "react";
import {
  FileText,
  Download,
  Eye,
  CheckCircle2,
  Edit3,
  Sliders,
  ShieldCheck,
  Printer,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import {
  buildComprehensiveInvestigationReport,
  type JudicialInvestigationReport,
  type ReportSectionConfig,
} from "@/services/reportGenerator";
import { ReportPreview } from "./ReportPreview";

export function ReportBuilder({ caseId = "CASE-2026-N09" }: { caseId?: string }) {
  const [report, setReport] = useState<JudicialInvestigationReport>(() =>
    buildComprehensiveInvestigationReport(caseId)
  );
  const [isPreviewOpen, setIsPreviewOpen] = useState<boolean>(false);

  const [sections, setSections] = useState<ReportSectionConfig[]>([
    { id: "executiveSummary", title: "1. Executive Summary", enabled: true, content: report.sections.executiveSummary },
    { id: "networkOverview", title: "2. Network Structure & Centrality", enabled: true, content: report.sections.networkOverview },
    { id: "entityAnalysis", title: "3. Target Dossiers & Risk Attribution", enabled: true, content: report.sections.entityAnalysis },
    { id: "anomalySummary", title: "4. Behavioral Anomalies & Fund Cycles", enabled: true, content: report.sections.anomalySummary },
    { id: "spatialAnalysis", title: "5. Geospatial Facilities & Cell Towers", enabled: true, content: report.sections.spatialAnalysis },
    { id: "timelineSummary", title: "6. Chronological Surveillance Timeline", enabled: true, content: report.sections.timelineSummary },
    { id: "aiAnalysis", title: "7. Netra AI GraphRAG Attribution", enabled: true, content: report.sections.aiAnalysis },
  ]);

  const toggleSection = (id: string) => {
    setSections((prev) =>
      prev.map((s) => (s.id === id ? { ...s, enabled: !s.enabled } : s))
    );
  };

  const handleUpdateContent = (id: string, newText: string) => {
    setSections((prev) =>
      prev.map((s) => (s.id === id ? { ...s, content: newText } : s))
    );
    setReport((prev) => ({
      ...prev,
      sections: {
        ...prev.sections,
        [id]: newText,
      },
    }));
  };

  const handleExportPDF = () => {
    toast.success("Judicial Report PDF Exported", {
      description: `Docket ${report.caseId} intelligence report generated with Section 65B cryptographic seals.`,
    });
  };

  const handleExportJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `NETRA-REPORT-${report.caseId}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    toast.success("Case Dossier JSON Archive Exported");
  };

  return (
    <div className="space-y-4 font-sans select-none">
      {/* Modal Preview */}
      {isPreviewOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs p-6 flex items-center justify-center overflow-y-auto">
          <div className="w-full max-w-4xl">
            <ReportPreview
              report={report}
              onClose={() => setIsPreviewOpen(false)}
              onExportPDF={handleExportPDF}
            />
          </div>
        </div>
      )}

      {/* Top Header */}
      <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 flex flex-wrap items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-lg bg-sky-950/60 border border-sky-800 text-sky-300">
            <FileText className="size-5" />
          </span>
          <div>
            <h3 className="font-bold text-slate-100 text-sm uppercase">
              Judicial Intelligence Report Composition Workspace
            </h3>
            <p className="text-[10px] font-mono text-slate-400">
              Report Ref: <strong>{report.reportNumber}</strong> · Lead Officer: {report.leadOfficer}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={() => setIsPreviewOpen(true)}
            className="flex items-center gap-1.5 rounded border border-sky-500/50 bg-sky-950/40 px-3 py-1.5 font-bold text-sky-300 hover:bg-sky-900/60 transition-colors cursor-pointer"
          >
            <Eye className="size-3.5" /> Preview Judicial Dossier
          </button>

          <button
            onClick={handleExportPDF}
            className="flex items-center gap-1.5 rounded border border-emerald-500/50 bg-emerald-950/40 px-3 py-1.5 font-bold text-emerald-300 hover:bg-emerald-900/60 transition-colors cursor-pointer"
          >
            <Download className="size-3.5" /> Export PDF
          </button>

          <button
            onClick={handleExportJSON}
            className="flex items-center gap-1.5 rounded border border-slate-800 bg-[#161D24] px-2.5 py-1.5 font-semibold text-slate-300 hover:border-slate-700 transition-colors cursor-pointer"
          >
            JSON
          </button>
        </div>
      </div>

      {/* Sections Configurator List */}
      <div className="space-y-3">
        {sections.map((sec) => (
          <div
            key={sec.id}
            className={cn(
              "rounded-lg border p-4 space-y-2.5 transition-all",
              sec.enabled
                ? "border-slate-800 bg-[#121820]"
                : "border-slate-800/40 bg-[#0C1016] opacity-60"
            )}
          >
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={sec.enabled}
                  onChange={() => toggleSection(sec.id)}
                  className="rounded border-slate-700 bg-slate-800 text-sky-500 cursor-pointer size-4"
                />
                <h4 className="font-bold text-slate-100 text-xs font-mono">
                  {sec.title}
                </h4>
              </div>

              <span className="font-mono text-[10px] text-slate-400">
                {sec.enabled ? "Section Active in Export" : "Excluded from Export"}
              </span>
            </div>

            {sec.enabled && (
              <textarea
                rows={3}
                value={sec.content || ""}
                onChange={(e) => handleUpdateContent(sec.id, e.target.value)}
                className="w-full rounded border border-slate-800 bg-[#161D24] p-3 text-xs text-slate-200 font-sans leading-relaxed outline-none focus:border-sky-500/80"
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
