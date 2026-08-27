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
      title: `Highly Connected Key Suspect (Rank #${entity.centralityRank})`,
      desc: "Node sits on dominant communication or financial routes in the syndicate.",
      type: "critical",
    });
  }
  if (entity.betweennessScore && entity.betweennessScore > 15) {
    observations.push({
      title: `Important Network Bridge (${entity.betweennessScore}%)`,
      desc: "Connects communications between separate suspect cells and groups.",
      type: "critical",
    });
  }
  if (entity.metadata.financialLossINR && entity.metadata.financialLossINR > 10000000) {
    observations.push({
      title: `High Financial Movement (₹${(entity.metadata.financialLossINR / 10000000).toFixed(2)} Cr)`,
      desc: "Associated with cumulative fund transfers across flagged accounts.",
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
      title: "Standard Case Associate",
      desc: "Entity associated with active case investigation docket.",
      type: "info",
    });
  }

  return (
    <aside className="w-[420px] border-l border-[#D9E2EC] bg-[#FFFFFF] flex flex-col h-full overflow-hidden select-none shadow-sm">
      {/* Profile Header */}
      <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] p-4 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-emerald-50 text-[#065F46] border border-emerald-200 shadow-xs">
              <Target className="size-5" />
            </span>
            <div className="min-w-0">
              <h2 className="font-sans text-base font-bold text-[#0F172A] truncate">
                {entity.name}
              </h2>
              <p className="text-xs text-[#64748B] truncate">
                <span className="font-mono text-[#065F46]">{entity.id}</span> · {entity.role || entity.label}
              </p>
            </div>
          </div>

          {/* Risk Pill */}
          <span
            className={cn(
              "shrink-0 flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-bold shadow-xs",
              isHighRisk
                ? "bg-red-50 text-[#DC3545] border border-red-200"
                : risk >= 70
                ? "bg-amber-50 text-[#F59E0B] border border-amber-200"
                : "bg-slate-50 text-[#475569] border border-slate-200"
            )}
          >
            {isHighRisk && <Flame className="size-3 text-[#DC3545]" />}
            Risk {risk}/100
          </span>
        </div>

        {/* Action Toolbar */}
        <div className="flex items-center gap-2 pt-1">
          {onNavigateToGraph && (
            <button
              onClick={() => onNavigateToGraph(entity.id)}
              className="flex-1 flex items-center justify-center gap-1.5 rounded-md bg-[#065F46] hover:bg-[#047857] px-3 py-1.5 text-xs font-semibold text-white transition-colors cursor-pointer shadow-xs"
            >
              <Share2 className="size-3.5" /> View on Knowledge Graph
            </button>
          )}

          {onOpenResolutionMatrix && entity.metadata.duplicateCandidateOf && (
            <button
              onClick={() => onOpenResolutionMatrix(entity)}
              className="flex items-center justify-center gap-1 rounded-md border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-xs font-semibold text-[#F59E0B] hover:bg-amber-100 transition-colors cursor-pointer"
              title="Resolve duplicate records"
            >
              Review Duplicate
            </button>
          )}
        </div>
      </div>

      {/* Profile Body Scroll */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs text-[#0F172A] font-sans">
        {/* 1. Identity & Attributes */}
        <div className="rounded-md border border-[#D9E2EC] bg-[#F8FAFC] p-3.5 space-y-2.5">
          <span className="text-xs font-bold text-[#0F172A] block">
            Identity & Registration Details
          </span>

          <div className="space-y-1.5 text-xs">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-1.5">
              <span className="text-[#64748B]">Entity Type:</span>
              <strong className="text-[#0F172A]">{entity.label}</strong>
            </div>
            <div className="flex items-center justify-between border-b border-[#E2E8F0] py-1.5">
              <span className="text-[#64748B]">Data Confidence:</span>
              <strong className="text-[#198754]">
                {(entity.confidenceScore * 100).toFixed(0)}% ({entity.verificationStatus})
              </strong>
            </div>
            <div className="flex items-center justify-between border-b border-[#E2E8F0] py-1.5">
              <span className="text-[#64748B]">Case Association:</span>
              <strong className="font-mono text-[#065F46]">{entity.caseId}</strong>
            </div>
            <div className="flex items-center justify-between py-1">
              <span className="text-[#64748B]">Syndicate / Group:</span>
              <strong className="text-[#0F172A] truncate max-w-[200px]">
                {entity.investigationGroup}
              </strong>
            </div>
          </div>

          {/* Aliases Tag Cloud */}
          {entity.metadata.alias && entity.metadata.alias.length > 0 && (
            <div className="pt-2 border-t border-[#E2E8F0]">
              <span className="text-xs text-[#64748B] font-semibold block mb-1">
                Known Aliases:
              </span>
              <div className="flex flex-wrap gap-1">
                {entity.metadata.alias.map((a, i) => (
                  <span
                    key={i}
                    className="rounded bg-white px-2 py-0.5 text-xs text-[#0F172A] border border-[#D9E2EC]"
                  >
                    "{a}"
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 2. Network Position & Connectivity */}
        <div className="rounded-md border border-[#D9E2EC] bg-[#F8FAFC] p-3.5 space-y-2.5">
          <span className="text-xs font-bold text-[#0F172A] block flex items-center gap-1.5">
            <TrendingUp className="size-4 text-[#065F46]" /> Network Importance
          </span>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="rounded bg-white p-2.5 border border-[#D9E2EC]">
              <span className="text-[10px] text-[#64748B] block">NETWORK RANK</span>
              <span className="text-lg font-bold text-[#065F46]">
                #{entity.centralityRank || "—"}
              </span>
            </div>
            <div className="rounded bg-white p-2.5 border border-[#D9E2EC]">
              <span className="text-[10px] text-[#64748B] block">TOTAL LINKS</span>
              <span className="text-lg font-bold text-[#0F172A]">
                {entity.degreeCount || entity.relationshipsCount || 1} connections
              </span>
            </div>
          </div>
        </div>

        {/* 3. Risk Assessment Findings */}
        <div className="rounded-md border border-[#D9E2EC] bg-[#F8FAFC] p-3.5 space-y-2.5">
          <span className="text-xs font-bold text-[#0F172A] flex items-center gap-1.5">
            <ShieldAlert className="size-4 text-[#DC3545]" /> Risk Evaluation Notes
          </span>

          <div className="space-y-1.5">
            {observations.map((obs, i) => (
              <div
                key={i}
                className="rounded-md border border-[#D9E2EC] bg-white p-2.5 space-y-0.5"
              >
                <span className="text-xs font-bold text-[#0F172A] block">
                  • {obs.title}
                </span>
                <p className="text-xs text-[#64748B] leading-normal">
                  {obs.desc}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* 4. Statutory Offenses */}
        {entity.metadata.statutoryOffenses && entity.metadata.statutoryOffenses.length > 0 && (
          <div className="rounded-md border border-[#D9E2EC] bg-[#F8FAFC] p-3.5 space-y-2">
            <span className="text-xs font-bold text-[#0F172A] block">
              Flagged Statutory Offenses
            </span>
            <div className="flex flex-wrap gap-1.5">
              {entity.metadata.statutoryOffenses.map((off, i) => (
                <span
                  key={i}
                  className="rounded-md border border-red-200 bg-red-50 px-2 py-0.5 text-xs font-semibold text-[#DC3545]"
                >
                  {off}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 5. Technical Attributes */}
        <div className="rounded-md border border-[#D9E2EC] bg-[#F8FAFC] p-3.5 space-y-2">
          <span className="text-xs font-bold text-[#0F172A] block">
            Technical Evidence Attributes
          </span>
          <div className="space-y-1.5 text-xs">
            {entity.metadata.phoneImei && (
              <div className="flex items-center justify-between border-b border-[#E2E8F0] py-1">
                <span className="text-[#64748B]">IMEI Number:</span>
                <span className="font-mono text-[#0F172A]">{entity.metadata.phoneImei}</span>
              </div>
            )}
            {entity.metadata.accountNumber && (
              <div className="flex items-center justify-between border-b border-[#E2E8F0] py-1">
                <span className="text-[#64748B]">Bank Account:</span>
                <span className="font-mono text-[#065F46] font-semibold">{entity.metadata.accountNumber}</span>
              </div>
            )}
            {entity.metadata.jurisdiction && (
              <div className="flex items-center justify-between py-1">
                <span className="text-[#64748B]">Jurisdiction:</span>
                <span className="text-[#0F172A]">{entity.metadata.jurisdiction}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
