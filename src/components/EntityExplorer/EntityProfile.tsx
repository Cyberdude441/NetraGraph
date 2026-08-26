import React from "react";
import {
  Target,
  ShieldAlert,
  Flame,
  ShieldCheck,
  TrendingUp,
  Share2,
  Calendar,
  Layers,
  Award,
  Zap,
  Info,
  Clock,
  ExternalLink,
  ChevronRight,
  User,
  Building2,
  Smartphone,
  CreditCard,
  Cpu,
  MapPin,
  Car,
  CalendarDays,
  FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ComprehensiveEntity } from "@/data/syntheticEntities";

interface EntityProfileProps {
  entity: ComprehensiveEntity;
  onNavigateToGraph?: (entityId: string) => void;
  onOpenResolutionMatrix?: (entity: ComprehensiveEntity) => void;
}

export function EntityProfile({
  entity,
  onNavigateToGraph,
  onOpenResolutionMatrix,
}: EntityProfileProps) {
  const risk = entity.riskScore;
  const isHighRisk = risk >= 85;

  // Risk Breakdown Observations
  const observations: { title: string; desc: string; type: "critical" | "warning" | "info" }[] = [];
  if (entity.centralityRank && entity.centralityRank <= 5) {
    observations.push({
      title: `High Network Centrality (Rank #${entity.centralityRank})`,
      desc: "Node sits on dominant communication or financial routes with high PageRank authority.",
      type: "critical",
    });
  }
  if (entity.betweennessScore && entity.betweennessScore > 15) {
    observations.push({
      title: `Inter-Community Bridge (${entity.betweennessScore}%)`,
      desc: "Bridges communications between distinct cyber syndicate clusters.",
      type: "critical",
    });
  }
  if (entity.metadata.financialLossINR && entity.metadata.financialLossINR > 10000000) {
    observations.push({
      title: `High Financial Velocity (₹${(entity.metadata.financialLossINR / 10000000).toFixed(2)} Cr)`,
      desc: "Associated with significant cumulative fund dispersion across mule accounts.",
      type: "warning",
    });
  }
  if (entity.metadata.phoneImei) {
    observations.push({
      title: "Hardened Hardware Identifier",
      desc: `IMEI [${entity.metadata.phoneImei}] matched across multiple SIM card activations.`,
      type: "info",
    });
  }
  if (observations.length === 0) {
    observations.push({
      title: "Standard Operational Associate",
      desc: "Baseline network node associated with active investigation docket.",
      type: "info",
    });
  }

  return (
    <aside className="w-[420px] border-l border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none shadow-2xl">
      {/* Profile Header */}
      <div className="border-b border-slate-800 bg-[#141A21] p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-[#1E293B] text-sky-400 border border-slate-700 shadow-sm">
              <Target className="size-5" />
            </span>
            <div className="min-w-0">
              <h2 className="font-sans text-sm font-bold text-slate-100 uppercase tracking-wide truncate">
                {entity.name}
              </h2>
              <p className="text-[10px] font-mono text-slate-400 truncate">
                {entity.id} · {entity.role || entity.label}
              </p>
            </div>
          </div>

          {/* Risk Pill */}
          <span
            className={cn(
              "shrink-0 flex items-center gap-1 rounded px-2.5 py-1 font-mono text-[11px] font-bold shadow-sm",
              isHighRisk
                ? "bg-red-950/80 text-red-200 border border-red-500/60"
                : risk >= 70
                ? "bg-amber-950/80 text-amber-200 border border-amber-500/50"
                : "bg-slate-800 text-slate-300 border border-slate-700"
            )}
          >
            {isHighRisk && <Flame className="size-3 text-red-400 animate-pulse" />}
            Risk {risk}/100
          </span>
        </div>

        {/* Action Toolbar */}
        <div className="mt-3 flex items-center gap-2 pt-2 border-t border-slate-800/80">
          {onNavigateToGraph && (
            <button
              onClick={() => onNavigateToGraph(entity.id)}
              className="flex-1 flex items-center justify-center gap-1.5 rounded border border-sky-500/50 bg-sky-950/40 px-3 py-1.5 text-xs font-mono font-semibold text-sky-300 hover:bg-sky-900/50 transition-colors cursor-pointer shadow-xs"
            >
              <Share2 className="size-3.5" /> View on Knowledge Graph
            </button>
          )}

          {onOpenResolutionMatrix && entity.metadata.duplicateCandidateOf && (
            <button
              onClick={() => onOpenResolutionMatrix(entity)}
              className="flex items-center justify-center gap-1 rounded border border-amber-500/50 bg-amber-950/40 px-2.5 py-1.5 text-xs font-mono font-semibold text-amber-300 hover:bg-amber-900/50 transition-colors cursor-pointer"
              title="Resolve duplicate profiles"
            >
              Resolve Duplicate
            </button>
          )}
        </div>
      </div>

      {/* Profile Body Scroll */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs text-slate-300 custom-scrollbar font-sans">
        {/* 1. Identity & Aliases */}
        <div className="rounded border border-slate-800 bg-[#141A21] p-3 space-y-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
            Identity & Authentication
          </span>

          <div className="space-y-1 text-[11px] font-mono">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-1">
              <span className="text-slate-500">Classification:</span>
              <strong className="text-slate-200">{entity.label}</strong>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/80 py-1">
              <span className="text-slate-500">Forensic Confidence:</span>
              <strong className="text-emerald-400">
                {(entity.confidenceScore * 100).toFixed(0)}% ({entity.verificationStatus})
              </strong>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/80 py-1">
              <span className="text-slate-500">Case Association:</span>
              <strong className="text-sky-300">{entity.caseId}</strong>
            </div>
            <div className="flex items-center justify-between py-1">
              <span className="text-slate-500">Syndicate Group:</span>
              <strong className="text-slate-200 truncate max-w-[200px]">
                {entity.investigationGroup}
              </strong>
            </div>
          </div>

          {/* Aliases Tag Cloud */}
          {entity.metadata.alias && entity.metadata.alias.length > 0 && (
            <div className="pt-2 border-t border-slate-800/80">
              <span className="text-[9px] font-mono text-slate-400 uppercase font-bold block mb-1">
                Known Aliases & Street Names:
              </span>
              <div className="flex flex-wrap gap-1">
                {entity.metadata.alias.map((a, i) => (
                  <span
                    key={i}
                    className="rounded bg-[#10171F] px-2 py-0.5 font-mono text-[10px] text-slate-200 border border-slate-800"
                  >
                    "{a}"
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 2. Network Centrality Analytics */}
        <div className="rounded border border-slate-800 bg-[#141A21] p-3 space-y-2.5">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block flex items-center gap-1">
            <TrendingUp className="size-3 text-sky-400" /> Graph Position & Centrality
          </span>

          <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
            <div className="rounded bg-[#10171F] p-2 border border-slate-800">
              <span className="text-[9px] text-slate-500 block">GLOBAL RANK</span>
              <span className="text-base font-bold text-amber-400">
                #{entity.centralityRank || "—"}
              </span>
            </div>
            <div className="rounded bg-[#10171F] p-2 border border-slate-800">
              <span className="text-[9px] text-slate-500 block">PAGERANK</span>
              <span className="text-base font-bold text-sky-400">
                {entity.pageRankScore ? `${entity.pageRankScore}%` : "—"}
              </span>
            </div>
            <div className="rounded bg-[#10171F] p-2 border border-slate-800">
              <span className="text-[9px] text-slate-500 block">BETWEENNESS</span>
              <span className="text-base font-bold text-emerald-400">
                {entity.betweennessScore ? `${entity.betweennessScore}%` : "—"}
              </span>
            </div>
            <div className="rounded bg-[#10171F] p-2 border border-slate-800">
              <span className="text-[9px] text-slate-500 block">DEGREE LINKS</span>
              <span className="text-base font-bold text-slate-200">
                {entity.degreeCount || entity.relationshipsCount || 1}
              </span>
            </div>
          </div>
        </div>

        {/* 3. Explainable Risk Analysis */}
        <div className="rounded border border-slate-800 bg-[#141A21] p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1">
              <ShieldAlert className="size-3 text-red-400" /> Risk Assessment Observations
            </span>
          </div>

          <div className="space-y-1.5">
            {observations.map((obs, i) => (
              <div
                key={i}
                className="rounded border border-slate-800/80 bg-[#10171F] p-2 space-y-0.5"
              >
                <span className="font-mono text-[10px] font-bold text-slate-200 block">
                  • {obs.title}
                </span>
                <p className="text-[10px] text-slate-400 leading-tight">
                  {obs.desc}
                </p>
              </div>
            ))}
          </div>

          <div className="rounded bg-sky-950/30 border border-sky-900/40 p-2 text-[10px] text-sky-300 font-mono">
            <strong>AI Assessment:</strong> Risk score reflects topology, transaction flow, and corroborated evidence. Requires certified analyst review before judicial action.
          </div>
        </div>

        {/* 4. Statutory Offenses */}
        {entity.metadata.statutoryOffenses && entity.metadata.statutoryOffenses.length > 0 && (
          <div className="rounded border border-slate-800 bg-[#141A21] p-3 space-y-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
              Flagged Statutory Offenses
            </span>
            <div className="flex flex-wrap gap-1.5">
              {entity.metadata.statutoryOffenses.map((off, i) => (
                <span
                  key={i}
                  className="rounded border border-red-500/40 bg-red-950/30 px-2 py-0.5 font-mono text-[10px] font-bold text-red-300"
                >
                  {off}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 5. Technical Attributes */}
        <div className="rounded border border-slate-800 bg-[#141A21] p-3 space-y-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
            Technical Evidence Attributes
          </span>
          <div className="space-y-1 text-[10px] font-mono">
            {entity.metadata.phoneImei && (
              <div className="flex items-center justify-between border-b border-slate-800/80 py-1">
                <span className="text-slate-500">IMEI Fingerprint:</span>
                <span className="text-slate-200">{entity.metadata.phoneImei}</span>
              </div>
            )}
            {entity.metadata.accountNumber && (
              <div className="flex items-center justify-between border-b border-slate-800/80 py-1">
                <span className="text-slate-500">Bank Account:</span>
                <span className="text-amber-300">{entity.metadata.accountNumber}</span>
              </div>
            )}
            {entity.metadata.ipAddress && (
              <div className="flex items-center justify-between border-b border-slate-800/80 py-1">
                <span className="text-slate-500">IP Host Range:</span>
                <span className="text-cyan-300">{entity.metadata.ipAddress}</span>
              </div>
            )}
            {entity.metadata.jurisdiction && (
              <div className="flex items-center justify-between py-1">
                <span className="text-slate-500">Jurisdiction:</span>
                <span className="text-slate-200">{entity.metadata.jurisdiction}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
