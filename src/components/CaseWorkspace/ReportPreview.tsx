import React from "react";
import {
  FileText,
  Download,
  Printer,
  ShieldCheck,
  CheckCircle2,
  X,
  Lock,
} from "lucide-react";
import type { JudicialInvestigationReport } from "@/services/reportGenerator";

interface ReportPreviewProps {
  report: JudicialInvestigationReport;
  onClose: () => void;
  onExportPDF: () => void;
}

export function ReportPreview({
  report,
  onClose,
  onExportPDF,
}: ReportPreviewProps) {
  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-6 text-xs select-none space-y-6 font-sans shadow-2xl max-h-[85vh] overflow-y-auto custom-scrollbar">
      {/* Top Controls */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <FileText className="size-4 text-sky-400" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
            Judicial Dossier Document Preview
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onExportPDF}
            className="flex items-center gap-1.5 rounded border border-emerald-500/50 bg-emerald-950/40 px-3 py-1 text-xs font-mono font-bold text-emerald-300 hover:bg-emerald-900/60 transition-colors cursor-pointer"
          >
            <Download className="size-3.5" /> Download PDF Dossier
          </button>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded cursor-pointer"
          >
            <X className="size-4" />
          </button>
        </div>
      </div>

      {/* Simulated Document Paper Container */}
      <div className="rounded border border-slate-800 bg-[#0B0F14] p-8 space-y-6 text-slate-300 font-sans shadow-inner">
        {/* Document Header */}
        <div className="text-center space-y-1 border-b border-slate-800 pb-5">
          <span className="text-[10px] font-mono uppercase tracking-widest text-slate-500 block font-bold">
            CONFIDENTIAL // LAW ENFORCEMENT INTELLIGENCE ONLY
          </span>
          <h1 className="text-base font-bold text-slate-100 tracking-wide uppercase">
            {report.title}
          </h1>
          <p className="text-xs text-sky-400 font-mono">
            DOCKET: {report.caseId} · REPORT REF: {report.reportNumber}
          </p>
          <p className="text-[11px] text-slate-400">
            Investigating Agency: <strong>{report.investigatingAgency}</strong>
          </p>
        </div>

        {/* Sections */}
        <div className="space-y-4 text-xs leading-relaxed text-slate-200">
          <div className="space-y-1">
            <h3 className="font-bold text-sky-300 text-xs font-mono uppercase">
              1. Executive Summary
            </h3>
            <p className="text-slate-300">{report.sections.executiveSummary}</p>
          </div>

          <div className="space-y-1">
            <h3 className="font-bold text-sky-300 text-xs font-mono uppercase">
              2. Knowledge Graph Topology & Centrality
            </h3>
            <p className="text-slate-300">{report.sections.networkOverview}</p>
          </div>

          <div className="space-y-1">
            <h3 className="font-bold text-sky-300 text-xs font-mono uppercase">
              3. Target Dossiers & Attribution
            </h3>
            <p className="text-slate-300">{report.sections.entityAnalysis}</p>
          </div>

          <div className="space-y-1">
            <h3 className="font-bold text-sky-300 text-xs font-mono uppercase">
              4. Behavioral Anomalies & Fund Cycles
            </h3>
            <p className="text-slate-300">{report.sections.anomalySummary}</p>
          </div>

          <div className="space-y-1">
            <h3 className="font-bold text-sky-300 text-xs font-mono uppercase">
              5. Spatial & Cell Tower Analysis
            </h3>
            <p className="text-slate-300">{report.sections.spatialAnalysis}</p>
          </div>

          <div className="space-y-1">
            <h3 className="font-bold text-sky-300 text-xs font-mono uppercase">
              6. Chronological Surveillance Timeline
            </h3>
            <p className="text-slate-300">{report.sections.timelineSummary}</p>
          </div>

          <div className="space-y-1">
            <h3 className="font-bold text-sky-300 text-xs font-mono uppercase">
              7. Netra AI GraphRAG Reasoning
            </h3>
            <p className="text-slate-300">{report.sections.aiAnalysis}</p>
          </div>
        </div>

        {/* Section 65B Certificate Footer */}
        <div className="rounded border border-emerald-900/60 bg-emerald-950/20 p-4 space-y-2 mt-6">
          <div className="flex items-center gap-2 text-emerald-400 font-mono font-bold text-[11px] uppercase">
            <ShieldCheck className="size-4" />
            <span>Evidentiary Custody & Section 65B Certificate</span>
          </div>
          <p className="text-[11px] text-slate-300 font-mono leading-relaxed">
            {report.statutoryCertificate}
          </p>

          <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-emerald-900/40 text-[10px] font-mono text-slate-400">
            <div>
              Authorizing Officer: <strong className="text-slate-200">{report.leadOfficer}</strong>
            </div>
            <div>
              Date Signed: <strong className="text-slate-200">{new Date(report.dateGenerated).toLocaleDateString()}</strong>
            </div>
            <div className="text-emerald-400 font-bold">
              [CRYPTOGRAPHICALLY SEALED EXHIBIT]
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
