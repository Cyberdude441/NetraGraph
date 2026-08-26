import React from "react";
import {
  Target,
  ShieldAlert,
  Flame,
  Activity,
  Share2,
  Calendar,
  Layers,
  Database,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Award,
  Zap,
  Info,
  Clock,
  MapPin,
  Smartphone,
  CreditCard,
  Building2,
  Cpu,
  User,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { SyntheticEntity, SyntheticRelationship } from "@/data/syntheticGraphData";
import type { CentralityMetrics, CommunityCluster } from "@/utils/graphAlgorithms";

export interface EntityDetailDrawerProps {
  entity: SyntheticEntity | null;
  relationships: SyntheticRelationship[];
  allEntities: SyntheticEntity[];
  centrality?: CentralityMetrics | undefined;
  community?: CommunityCluster | undefined;
  onSelectEntity: (id: string) => void;
  onClose?: (() => void) | undefined;
}

export function EntityDetailDrawer({
  entity,
  relationships,
  allEntities,
  centrality,
  community,
  onSelectEntity,
  onClose,
}: EntityDetailDrawerProps) {
  if (!entity) return null;

  const entityMap = new Map(allEntities.map((e) => [e.id, e]));

  // Connected incoming & outgoing links
  const directLinks = relationships
    .filter((r) => r.sourceId === entity.id || r.targetId === entity.id)
    .map((r) => {
      const isOut = r.sourceId === entity.id;
      const otherId = isOut ? r.targetId : r.sourceId;
      const otherEntity = entityMap.get(otherId);
      return {
        rel: r,
        isOut,
        otherEntity,
      };
    })
    .filter((item) => Boolean(item.otherEntity));

  // Explainability Generator ("Why is this entity important?")
  const explainabilityReasons: string[] = [];
  const risk = entity.riskScore;
  const rank = centrality?.rank || 99;
  const betweenness = centrality?.betweenness || 0;
  const degree = directLinks.length;

  if (rank <= 3) {
    explainabilityReasons.push(`Ranked #${rank} in Global Network Influence (High PageRank Authority).`);
  }
  if (betweenness > 15) {
    explainabilityReasons.push(`Critical Inter-Cluster Bridge (Betweenness ${betweenness}%): Funnels communications/finances between disjoint cells.`);
  }
  if (degree >= 4) {
    explainabilityReasons.push(`High Density Hub: Direct multi-modal links to ${degree} distinct network assets.`);
  }
  if (entity.metadata.financialLossINR && entity.metadata.financialLossINR > 10000000) {
    explainabilityReasons.push(`Major Financial Velocity: Implicated in cumulative transactions exceeding ₹${(entity.metadata.financialLossINR / 10000000).toFixed(2)} Crore.`);
  }
  if (entity.confidenceScore >= 0.95) {
    explainabilityReasons.push(`Forensically Verified: ${(entity.confidenceScore * 100).toFixed(0)}% attribution confidence from CDR & hardware seizures.`);
  }
  if (explainabilityReasons.length === 0) {
    explainabilityReasons.push(`Standard operational entity associated with ${entity.investigationGroup}.`);
  }

  return (
    <aside className="w-96 border-l border-slate-800 bg-[#0E1318] flex flex-col h-full z-10 shadow-2xl select-none">
      {/* Header */}
      <div className="border-b border-slate-800 bg-[#141A21] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <span className="flex size-7 shrink-0 items-center justify-center rounded bg-[#1E293B] text-sky-400 border border-slate-700">
            <Target className="size-4" />
          </span>
          <div className="min-w-0">
            <h3 className="font-sans text-xs font-bold text-slate-100 uppercase tracking-wider truncate">
              {entity.name}
            </h3>
            <span className="text-[10px] font-mono text-slate-400 truncate block">
              {entity.label} · ID: {entity.id}
            </span>
          </div>
        </div>

        {/* Risk Pill */}
        <div className="shrink-0 flex items-center gap-1">
          <span
            className={cn(
              "flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[10px] font-bold",
              risk >= 85
                ? "bg-red-950/80 text-red-300 border border-red-500/60"
                : risk >= 70
                ? "bg-amber-950/80 text-amber-300 border border-amber-500/50"
                : "bg-slate-800 text-slate-300 border border-slate-700"
            )}
          >
            {risk >= 85 && <Flame className="size-2.5 text-red-400 animate-pulse" />}
            Risk {risk}/100
          </span>
        </div>
      </div>

      {/* Drawer Body Scroll */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs text-slate-300 custom-scrollbar">
        {/* 1. Explainability Panel ("Why is this entity important?") */}
        <div className="rounded border border-sky-900/60 bg-[#0C1A29] p-3 space-y-2">
          <div className="flex items-center gap-1.5 text-sky-400 font-mono font-bold text-[10px] uppercase tracking-wider">
            <Info className="size-3.5" />
            <span>Netra Intelligence Explainability</span>
          </div>
          <div className="space-y-1.5">
            {explainabilityReasons.map((reason, idx) => (
              <div
                key={idx}
                className="flex items-start gap-1.5 text-[11px] text-slate-300 leading-tight font-sans"
              >
                <span className="text-sky-400 mt-0.5 font-bold">•</span>
                <span>{reason}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 2. Centrality Analytics Scorecard */}
        <div className="rounded border border-slate-800 bg-[#141A21] p-3 space-y-2.5">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider font-bold block flex items-center gap-1">
            <TrendingUp className="size-3 text-sky-400" /> Algorithmic Graph Metrics
          </span>

          <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
            <div className="rounded bg-[#10171F] p-2 border border-slate-800">
              <span className="text-[9px] text-slate-500 block">GLOBAL RANK</span>
              <span className="text-sm font-bold text-amber-400">
                #{centrality?.rank || "—"}
              </span>
            </div>
            <div className="rounded bg-[#10171F] p-2 border border-slate-800">
              <span className="text-[9px] text-slate-500 block">PAGERANK INFLUENCE</span>
              <span className="text-sm font-bold text-sky-400">
                {centrality ? `${centrality.pageRank}%` : "—"}
              </span>
            </div>
            <div className="rounded bg-[#10171F] p-2 border border-slate-800">
              <span className="text-[9px] text-slate-500 block">BETWEENNESS (BRIDGE)</span>
              <span className="text-sm font-bold text-emerald-400">
                {centrality ? `${centrality.betweenness}%` : "—"}
              </span>
            </div>
            <div className="rounded bg-[#10171F] p-2 border border-slate-800">
              <span className="text-[9px] text-slate-500 block">DEGREE LINKS</span>
              <span className="text-sm font-bold text-slate-200">
                {centrality?.degree || directLinks.length}
              </span>
            </div>
          </div>
        </div>

        {/* 3. Syndicate / Community Membership */}
        <div className="rounded border border-slate-800 bg-[#141A21] p-3 space-y-2 font-mono text-[11px]">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 font-bold block flex items-center gap-1">
            <Layers className="size-3 text-purple-400" /> Syndicate Association
          </span>
          <div className="flex items-center justify-between border-t border-slate-800/80 pt-1.5">
            <span className="text-slate-500">Investigation Group</span>
            <span className="font-bold text-slate-200 truncate max-w-[190px]">
              {entity.investigationGroup}
            </span>
          </div>
          <div className="flex items-center justify-between border-t border-slate-800/80 pt-1.5">
            <span className="text-slate-500">Case Docket</span>
            <span className="font-bold text-sky-400">{entity.caseId}</span>
          </div>
          <div className="flex items-center justify-between border-t border-slate-800/80 pt-1.5">
            <span className="text-slate-500">First / Last Seen</span>
            <span className="text-slate-300 text-[10px]">
              {entity.firstSeen} → {entity.lastSeen}
            </span>
          </div>
        </div>

        {/* 4. Connected Relationships Matrix */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
              <Share2 className="size-3 text-sky-400" /> Direct Links ({directLinks.length})
            </span>
          </div>

          <div className="space-y-1.5">
            {directLinks.map((item, idx) => (
              <div
                key={idx}
                onClick={() => item.otherEntity && onSelectEntity(item.otherEntity.id)}
                className="rounded border border-slate-800 bg-[#141A21] p-2 hover:border-sky-500 transition-all cursor-pointer"
              >
                <div className="flex items-center justify-between mb-0.5">
                  <span className="font-semibold text-slate-200 text-[11px] truncate">
                    {item.otherEntity?.name}
                  </span>
                  <span className="font-mono text-[9px] text-slate-400 uppercase">
                    {item.otherEntity?.label}
                  </span>
                </div>
                <div className="text-[10px] font-mono text-sky-400 flex items-center gap-1">
                  <span>{item.isOut ? "→" : "←"} {item.rel.label}</span>
                </div>
                {item.rel.detail && (
                  <div className="text-[9px] text-slate-400 mt-1 truncate">
                    {item.rel.detail}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 5. Forensic Provenance */}
        <div className="rounded border border-slate-800 bg-[#10171F] p-2.5 space-y-1 text-[10px] font-mono">
          <div className="flex items-center gap-1.5 text-emerald-400 font-bold">
            <Database className="size-3" />
            <span>CHAIN OF CUSTODY PROVENANCE</span>
          </div>
          <div className="text-slate-400 space-y-0.5">
            <div>Confidence: <span className="text-emerald-400">{(entity.confidenceScore * 100).toFixed(0)}% (Authenticated)</span></div>
            <div>Jurisdiction: <span className="text-slate-200">{entity.metadata.jurisdiction || "National Cyber Cell"}</span></div>
          </div>
        </div>
      </div>
    </aside>
  );
}
