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
    <div className="rounded-md border border-[#D9E2EC] bg-white p-6 text-xs select-none space-y-6 font-sans shadow-2xl max-h-[85vh] overflow-y-auto">
      {/* Top Controls */}
      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
        <div className="flex items-center gap-2">
          <FileText className="size-4 text-[#065F46]" />
          <span className="text-sm font-bold text-[#0F172A]">
            Judicial Dossier Document Preview
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onExportPDF}
            className="flex items-center gap-1.5 rounded-md bg-[#065F46] hover:bg-[#047857] px-3.5 py-1.5 text-xs font-semibold text-white transition-colors cursor-pointer shadow-xs"
          >
            <Download className="size-3.5" /> Download PDF Dossier
          </button>
          <button
            onClick={onClose}
            className="text-[#64748B] hover:text-[#0F172A] p-1.5 rounded-md hover:bg-[#F1F5F9] cursor-pointer"
          >
            <X className="size-4" />
          </button>
        </div>
      </div>

      {/* Official White Document Paper Container */}
      <div className="rounded-md border border-[#CBD5E1] bg-[#FFFFFF] p-8 space-y-6 text-[#0F172A] font-sans shadow-sm">
        {/* Document Header */}
        <div className="text-center space-y-1.5 border-b border-[#D9E2EC] pb-5">
          <span className="text-[11px] uppercase tracking-widest text-[#065F46] block font-bold">
            CONFIDENTIAL // FOR OFFICIAL POLICE & JUDICIAL USE ONLY
          </span>
          <h1 className="text-lg font-bold text-[#0F172A] tracking-tight">
            {report.title}
          </h1>
          <p className="text-xs text-[#64748B]">
            Report Reference: <strong className="font-mono text-[#065F46]">{report.reportNumber}</strong> · Docket ID: <strong className="font-mono">{report.caseId}</strong>
          </p>
        </div>

        {/* Executive Meta Table */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-[#F8FAFC] p-3.5 rounded-md border border-[#D9E2EC] text-xs">
          <div>
            <span className="text-[#64748B] block text-[10px]">Agency / Unit:</span>
            <span className="font-semibold text-[#0F172A]">{report.investigatingAgency}</span>
          </div>
          <div>
            <span className="text-[#64748B] block text-[10px]">Lead Investigator:</span>
            <span className="font-semibold text-[#065F46]">{report.leadOfficer}</span>
          </div>
          <div>
            <span className="text-[#64748B] block text-[10px]">Date of Compilation:</span>
            <span className="font-semibold text-[#0F172A]">{new Date(report.dateGenerated).toLocaleDateString()}</span>
          </div>
          <div>
            <span className="text-[#64748B] block text-[10px]">Statutory Status:</span>
            <span className="font-bold text-[#198754]">Section 65B Sealed</span>
          </div>
        </div>

        {/* Document Content Sections */}
        <div className="space-y-5 text-xs leading-relaxed text-[#CBD5E1]">
          <div className="space-y-1.5">
            <h2 className="text-sm font-bold text-[#065F46] border-b border-[#E2E8F0] pb-1">
              1. Executive Summary
            </h2>
            <p>{report.sections.executiveSummary}</p>
          </div>

          <div className="space-y-1.5">
            <h2 className="text-sm font-bold text-[#065F46] border-b border-[#E2E8F0] pb-1">
              2. Network Structure & Key Connections
            </h2>
            <p>{report.sections.networkOverview}</p>
          </div>

          <div className="space-y-1.5">
            <h2 className="text-sm font-bold text-[#065F46] border-b border-[#E2E8F0] pb-1">
              3. Target Profiles & Suspect Attribution
            </h2>
            <p>{report.sections.entityAnalysis}</p>
          </div>

          <div className="space-y-1.5">
            <h2 className="text-sm font-bold text-[#065F46] border-b border-[#E2E8F0] pb-1">
              4. Behavioral Anomalies & Fund Cycles
            </h2>
            <p>{report.sections.anomalySummary}</p>
          </div>

          <div className="space-y-1.5">
            <h2 className="text-sm font-bold text-[#065F46] border-b border-[#E2E8F0] pb-1">
              5. Spatial & Cell Tower Intelligence
            </h2>
            <p>{report.sections.spatialAnalysis}</p>
          </div>

          <div className="space-y-1.5">
            <h2 className="text-sm font-bold text-[#065F46] border-b border-[#E2E8F0] pb-1">
              6. Chronological Surveillance Timeline
            </h2>
            <p>{report.sections.timelineSummary}</p>
          </div>

          <div className="space-y-1.5">
            <h2 className="text-sm font-bold text-[#065F46] border-b border-[#E2E8F0] pb-1">
              7. Netra AI Investigative Insights
            </h2>
            <p>{report.sections.aiAnalysis}</p>
          </div>
        </div>

        {/* Section 65B Certificate Footer */}
        <div className="rounded-md border border-emerald-200 bg-emerald-50/50 p-4 space-y-2 mt-6">
          <div className="flex items-center gap-2 text-[#198754] font-bold text-xs">
            <ShieldCheck className="size-4 text-[#198754]" />
            <span>Evidentiary Custody & Section 65B Certificate</span>
          </div>
          <p className="text-xs text-[#CBD5E1] leading-relaxed">
            {report.statutoryCertificate}
          </p>

          <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-emerald-200 text-xs text-[#64748B]">
            <div>
              Authorizing Officer: <strong className="text-[#0F172A]">{report.leadOfficer}</strong>
            </div>
            <div>
              Date Signed: <strong className="text-[#0F172A]">{new Date(report.dateGenerated).toLocaleDateString()}</strong>
            </div>
            <div className="text-[#198754] font-bold">
              DIGITALLY VERIFIED
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
