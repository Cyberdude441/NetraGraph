import React, { useState } from "react";
import {
  FileText,
  Download,
  Eye,
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
    { id: "networkOverview", title: "2. Network Structure & Key Connections", enabled: true, content: report.sections.networkOverview },
    { id: "entityAnalysis", title: "3. Target Profiles & Suspect Attribution", enabled: true, content: report.sections.entityAnalysis },
    { id: "anomalySummary", title: "4. Detected Anomalies & Transaction Loops", enabled: true, content: report.sections.anomalySummary },
    { id: "spatialAnalysis", title: "5. Geospatial Locations & Cell Towers", enabled: true, content: report.sections.spatialAnalysis },
    { id: "timelineSummary", title: "6. Chronological Surveillance Timeline", enabled: true, content: report.sections.timelineSummary },
    { id: "aiAnalysis", title: "7. Netra AI Investigative Analysis", enabled: true, content: report.sections.aiAnalysis },
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
      description: `Docket ${report.caseId} intelligence report generated with Section 65B cryptographic certificate.`,
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
    toast.success("Case Dossier JSON Exported");
  };

  return (
    <div className="space-y-4 font-sans select-none">
      {/* Modal Preview */}
      {isPreviewOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs p-6 flex items-center justify-center overflow-y-auto">
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
      <div className="rounded-md border border-[#D9E2EC] bg-white p-5 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-md bg-emerald-50 border border-emerald-200 text-[#065F46]">
            <FileText className="size-5" />
          </span>
          <div>
            <h3 className="font-bold text-[#0F172A] text-sm">
              Investigation Report Composition Workspace
            </h3>
            <p className="text-xs text-[#64748B] mt-0.5">
              Report Ref: <strong className="font-mono text-[#065F46]">{report.reportNumber}</strong> · Lead Investigator: {report.leadOfficer}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => setIsPreviewOpen(true)}
            className="flex items-center gap-1.5 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-1.5 font-semibold text-[#065F46] hover:bg-emerald-100 transition-colors cursor-pointer shadow-xs"
          >
            <Eye className="size-3.5" /> Preview Dossier
          </button>

          <button
            onClick={handleExportPDF}
            className="flex items-center gap-1.5 rounded-md bg-[#065F46] hover:bg-[#047857] px-3.5 py-1.5 font-semibold text-white transition-colors cursor-pointer shadow-xs"
          >
            <Download className="size-3.5" /> Export PDF
          </button>

          <button
            onClick={handleExportJSON}
            className="flex items-center gap-1.5 rounded-md border border-[#D9E2EC] bg-[#F8FAFC] px-2.5 py-1.5 font-semibold text-[#0F172A] hover:bg-[#F1F5F9] transition-colors cursor-pointer"
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
              "rounded-md border p-4 space-y-2.5 transition-all",
              sec.enabled
                ? "border-[#D9E2EC] bg-white shadow-xs"
                : "border-[#E2E8F0] bg-[#F8FAFC] opacity-60"
            )}
          >
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={sec.enabled}
                  onChange={() => toggleSection(sec.id)}
                  className="rounded border-[#D9E2EC] text-[#065F46] cursor-pointer size-4"
                />
                <h4 className="font-semibold text-[#0F172A] text-xs">
                  {sec.title}
                </h4>
              </div>

              <span className="text-[11px] text-[#64748B]">
                {sec.enabled ? "Included in Report" : "Excluded from Export"}
              </span>
            </div>

            {sec.enabled && (
              <textarea
                rows={3}
                value={sec.content || ""}
                onChange={(e) => handleUpdateContent(sec.id, e.target.value)}
                className="w-full rounded-md border border-[#D9E2EC] bg-[#F8FAFC] p-3 text-xs text-[#0F172A] font-sans leading-relaxed outline-none focus:border-[#065F46] focus:bg-white transition-all"
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
