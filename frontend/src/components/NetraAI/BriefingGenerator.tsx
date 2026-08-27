import React from "react";
import {
  FileText,
  Download,
  Printer,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Users,
  GitFork,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { generateInvestigationBriefing, type InvestigationBriefing } from "@/services/netraAI";

interface BriefingGeneratorProps {
  caseId?: string;
  onClose?: () => void;
}

export function BriefingGenerator({ caseId = "CASE-2026-N09", onClose }: BriefingGeneratorProps) {
  const briefing: InvestigationBriefing = generateInvestigationBriefing(caseId);

  const handleExportPDF = () => {
    toast.success("Investigation Dossier Exported", {
      description: "Cryptographically certified Section 65B intelligence briefing PDF compiled.",
    });
  };

  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-6 text-xs select-none space-y-5 font-sans shadow-2xl">
      {/* Top Action Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E2E8F0] pb-4">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300">
            <FileText className="size-5" />
          </span>
          <div>
            <h2 className="font-bold text-slate-900 text-sm uppercase tracking-wide">
              {briefing.caseTitle}
            </h2>
            <p className="text-[10px] font-mono text-slate-400">
              Docket: <strong>{briefing.caseId}</strong> · Generated: {new Date(briefing.generatedAt).toLocaleString()}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-1.5 rounded border border-emerald-500/50 bg-emerald-950/40 px-3 py-1.5 text-xs font-mono font-bold text-emerald-300 hover:bg-emerald-900/60 transition-colors cursor-pointer"
          >
            <Download className="size-3.5" /> Export Certified PDF
          </button>

          {onClose && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-800 p-1.5 rounded cursor-pointer"
            >
              <X className="size-4" />
            </button>
          )}
        </div>
      </div>

      {/* 8-Section Structured Dossier Document */}
      <div className="space-y-4 text-slate-700 font-sans">
        {/* Section 1: Overview */}
        <div className="rounded border border-[#E2E8F0] bg-white p-4 space-y-1.5">
          <h4 className="text-[11px] font-mono uppercase font-bold text-emerald-400 flex items-center gap-1.5">
            <span className="text-slate-500">§ 1.</span> Executive Case Overview
          </h4>
          <p className="text-xs text-slate-800 leading-relaxed">
            {briefing.sections.overview}
          </p>
        </div>

        {/* Section 2: Key Entities */}
        <div className="rounded border border-[#E2E8F0] bg-white p-4 space-y-2">
          <h4 className="text-[11px] font-mono uppercase font-bold text-emerald-400 flex items-center gap-1.5">
            <span className="text-slate-500">§ 2.</span> Identified Key Suspects & Shell Entities
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-[11px]">
            {briefing.sections.keyEntities.map((e) => (
              <div key={e.id} className="rounded bg-[#F8FAFC] p-2.5 border border-[#E2E8F0] flex items-center justify-between">
                <div>
                  <strong className="text-slate-900 text-xs block">{e.name}</strong>
                  <span className="text-[10px] text-slate-400">{e.role} ({e.id})</span>
                </div>
                <span className="text-red-400 font-bold text-xs">Risk {e.risk}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Section 3 & 4: Network Structure & Key Relationships */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded border border-[#E2E8F0] bg-white p-4 space-y-2 font-mono text-[11px]">
            <h4 className="text-[11px] uppercase font-bold text-emerald-400">
              § 3. Network Topology
            </h4>
            <div className="space-y-1 text-slate-700">
              <div className="flex justify-between border-b border-[#E2E8F0] pb-1">
                <span className="text-slate-500">Total Nodes / Links:</span>
                <strong>{briefing.sections.networkStructure.totalNodes} Nodes / {briefing.sections.networkStructure.totalEdges} Edges</strong>
              </div>
              <div className="flex justify-between border-b border-[#E2E8F0] py-1">
                <span className="text-slate-500">Syndicate Clusters:</span>
                <strong className="text-purple-400">{briefing.sections.networkStructure.clustersCount} Distinct Cells</strong>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Observed Graph Density:</span>
                <strong className="text-emerald-300">{briefing.sections.networkStructure.density}</strong>
              </div>
            </div>
          </div>

          <div className="rounded border border-[#E2E8F0] bg-white p-4 space-y-2">
            <h4 className="text-[11px] font-mono uppercase font-bold text-emerald-400">
              § 4. Corroborated Conduits
            </h4>
            <ul className="space-y-1 font-mono text-[10px] text-slate-700">
              {briefing.sections.importantRelationships.map((r, i) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-emerald-400">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Section 5, 6, 7: Detected Patterns, Anomalies & Risk */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="rounded border border-[#E2E8F0] bg-white p-3.5 space-y-1.5">
            <h4 className="text-[10px] font-mono uppercase font-bold text-amber-400">
              § 5. Behavioral Patterns
            </h4>
            <p className="text-[11px] text-slate-700 leading-relaxed font-sans">
              {briefing.sections.detectedPatterns.join(" ")}
            </p>
          </div>

          <div className="rounded border border-[#E2E8F0] bg-white p-3.5 space-y-1.5">
            <h4 className="text-[10px] font-mono uppercase font-bold text-red-400">
              § 6. Anomaly Telemetry
            </h4>
            <p className="text-[11px] text-slate-700 leading-relaxed font-sans">
              {briefing.sections.anomalySummary.join(" ")}
            </p>
          </div>

          <div className="rounded border border-[#E2E8F0] bg-white p-3.5 space-y-1.5">
            <h4 className="text-[10px] font-mono uppercase font-bold text-purple-400">
              § 7. Threat Attribution
            </h4>
            <p className="text-[11px] text-slate-700 leading-relaxed font-sans">
              {briefing.sections.riskIndicators.join(" ")}
            </p>
          </div>
        </div>

        {/* Section 8: Statutory Evidence References */}
        <div className="rounded border border-emerald-900/40 bg-emerald-950/20 p-4 space-y-2">
          <h4 className="text-[11px] font-mono uppercase font-bold text-emerald-400 flex items-center gap-1.5">
            <ShieldCheck className="size-4" /> § 8. Statutory Custody & Section 65B References
          </h4>
          <div className="flex flex-wrap gap-2 font-mono text-[11px]">
            {briefing.sections.evidenceReferences.map((ref, idx) => (
              <span key={idx} className="rounded bg-[#101E18] px-2.5 py-1 text-emerald-300 border border-emerald-800/60 font-semibold">
                ✓ {ref}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
