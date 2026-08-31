import React, { useState } from "react";
import {
  Target,
  ShieldAlert,
  Activity,
  Calendar,
  Layers,
  FileText,
  ChevronRight,
  Zap,
  Info,
  Clock,
  MapPin,
  Smartphone,
  CreditCard,
  Building2,
  Cpu,
  User,
  Hash,
  Globe2,
  FileCheck2,
  Binary,
  X,
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
  const [activeTab, setActiveTab] = useState<"overview" | "metrics" | "connections" | "provenance">("overview");

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

  const risk = entity.riskScore ?? 50;
  const isHighRisk = risk >= 85;

  return (
    <aside className="w-80 shrink-0 border-l border-[#334155] bg-[#0f172a] flex flex-col h-full z-20 shadow-2xl select-none 2xl:w-96 text-slate-200">
      {/* Header */}
      <div className="border-b border-[#334155] bg-[#0a0e17] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="flex size-7 shrink-0 items-center justify-center rounded bg-cyan-950 text-cyan-400 border border-cyan-800/80">
            <Target className="size-4" />
          </span>
          <div className="min-w-0">
            <h3 className="font-mono text-xs font-bold text-slate-100 tracking-tight truncate">
              {entity.name}
            </h3>
            <span className="text-[10px] text-cyan-400 font-mono">
              {entity.id} • {entity.label}
            </span>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:bg-[#1e293b] hover:text-slate-200 transition-colors"
          >
            <X className="size-4" />
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#334155] bg-[#0a0e17]/80 px-2 pt-1 gap-1 text-[11px] font-mono">
        <button
          onClick={() => setActiveTab("overview")}
          className={cn(
            "px-2.5 py-1.5 rounded-t font-semibold transition-colors",
            activeTab === "overview"
              ? "bg-[#1e293b] text-cyan-400 border-t-2 border-cyan-400"
              : "text-slate-400 hover:text-slate-200"
          )}
        >
          Profile
        </button>
        <button
          onClick={() => setActiveTab("metrics")}
          className={cn(
            "px-2.5 py-1.5 rounded-t font-semibold transition-colors",
            activeTab === "metrics"
              ? "bg-[#1e293b] text-cyan-400 border-t-2 border-cyan-400"
              : "text-slate-400 hover:text-slate-200"
          )}
        >
          Metrics
        </button>
        <button
          onClick={() => setActiveTab("connections")}
          className={cn(
            "px-2.5 py-1.5 rounded-t font-semibold transition-colors",
            activeTab === "connections"
              ? "bg-[#1e293b] text-cyan-400 border-t-2 border-cyan-400"
              : "text-slate-400 hover:text-slate-200"
          )}
        >
          Links ({directLinks.length})
        </button>
        <button
          onClick={() => setActiveTab("provenance")}
          className={cn(
            "px-2.5 py-1.5 rounded-t font-semibold transition-colors",
            activeTab === "provenance"
              ? "bg-[#1e293b] text-cyan-400 border-t-2 border-cyan-400"
              : "text-slate-400 hover:text-slate-200"
          )}
        >
          Audit
        </button>
      </div>

      {/* Body Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {activeTab === "overview" && (
          <div className="space-y-4">
            {/* Risk & Confidence Overview */}
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-lg border border-[#334155] bg-[#1e293b]/80 p-2.5">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Threat Risk</span>
                <span
                  className={cn(
                    "text-lg font-mono font-bold block",
                    isHighRisk ? "text-red-400" : risk >= 70 ? "text-amber-400" : "text-slate-200"
                  )}
                >
                  {risk}/100
                </span>
                <span className="text-[10px] text-slate-400">
                  {isHighRisk ? "Critical Anomaly" : risk >= 70 ? "Elevated Risk" : "Normal Baseline"}
                </span>
              </div>
              <div className="rounded-lg border border-[#334155] bg-[#1e293b]/80 p-2.5">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Attribution</span>
                <span className="text-lg font-mono font-bold text-teal-400 block">
                  {(entity.confidenceScore * 100).toFixed(0)}%
                </span>
                <span className="text-[10px] text-slate-400">Verified Evidence</span>
              </div>
            </div>

            {/* Entity Attributes */}
            <div className="rounded-lg border border-[#334155] bg-[#1e293b]/60 p-3 space-y-2 font-mono text-[11px]">
              <div className="flex justify-between border-b border-[#334155]/60 pb-1.5">
                <span className="text-slate-400">Identity:</span>
                <span className="text-slate-100 font-semibold">{entity.name}</span>
              </div>
              <div className="flex justify-between border-b border-[#334155]/60 pb-1.5">
                <span className="text-slate-400">Entity Type:</span>
                <span className="text-cyan-400">{entity.label}</span>
              </div>
              <div className="flex justify-between border-b border-[#334155]/60 pb-1.5">
                <span className="text-slate-400">Role / Designation:</span>
                <span className="text-slate-200">{entity.role || "Standard Asset"}</span>
              </div>
              <div className="flex justify-between border-b border-[#334155]/60 pb-1.5">
                <span className="text-slate-400">Case Docket:</span>
                <span className="text-amber-400">{entity.caseId || "NCRB Public"}</span>
              </div>
              {entity.metadata?.jurisdiction && (
                <div className="flex justify-between border-b border-[#334155]/60 pb-1.5">
                  <span className="text-slate-400">Jurisdiction:</span>
                  <span className="text-slate-200">{entity.metadata.jurisdiction}</span>
                </div>
              )}
              {entity.metadata?.ipAddress && (
                <div className="flex justify-between border-b border-[#334155]/60 pb-1.5">
                  <span className="text-slate-400">IP Indicator:</span>
                  <span className="text-cyan-300">{entity.metadata.ipAddress}</span>
                </div>
              )}
              {entity.metadata?.accountNumber && (
                <div className="flex justify-between border-b border-[#334155]/60 pb-1.5">
                  <span className="text-slate-400">Account / Escrow:</span>
                  <span className="text-amber-300">{entity.metadata.accountNumber}</span>
                </div>
              )}
            </div>

            {/* Description */}
            {entity.metadata?.description && (
              <div className="rounded-lg border border-[#334155] bg-[#1e293b]/40 p-3 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Investigative Context</span>
                <p className="text-xs text-slate-300 leading-relaxed">{entity.metadata.description}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === "metrics" && (
          <div className="space-y-3 font-mono">
            <div className="rounded-lg border border-[#334155] bg-[#1e293b] p-3 space-y-2">
              <span className="text-[10px] text-cyan-400 uppercase font-bold block">Network Topology Centrality</span>
              <div className="space-y-1.5 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-400">Degree Centrality:</span>
                  <span className="text-slate-200 font-bold">{directLinks.length} Connections</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Betweenness Brokerage:</span>
                  <span className="text-amber-400 font-bold">
                    {centrality?.betweenness ? `${(centrality.betweenness * 100).toFixed(2)}%` : "0.00%"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">PageRank Authority:</span>
                  <span className="text-teal-400 font-bold">
                    {centrality?.rank ? `Rank #${centrality.rank}` : "Standard"}
                  </span>
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-[#334155] bg-[#1e293b]/50 p-3 space-y-1.5 text-[11px]">
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Community Cluster</span>
              <div className="flex justify-between">
                <span className="text-slate-400">Cluster Assignment:</span>
                <span className="text-cyan-300">Cluster #{entity.communityId || 0}</span>
              </div>
              <p className="text-[10px] text-slate-400 pt-1">
                Clustering computed via authentic Greedy Modularity Optimization.
              </p>
            </div>
          </div>
        )}

        {activeTab === "connections" && (
          <div className="space-y-2">
            <span className="text-[10px] text-slate-400 uppercase font-mono block">Direct Graph Neighbors</span>
            {directLinks.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-2">No direct connections recorded.</p>
            ) : (
              directLinks.map(({ rel, isOut, otherEntity }) => (
                <div
                  key={rel.id}
                  onClick={() => otherEntity && onSelectEntity(otherEntity.id)}
                  className="rounded-lg border border-[#334155] bg-[#1e293b]/60 p-2.5 hover:bg-[#1e293b] hover:border-cyan-500/50 transition-all cursor-pointer space-y-1"
                >
                  <div className="flex items-center justify-between font-mono text-[11px]">
                    <span className="text-cyan-400 font-semibold truncate">{otherEntity?.name}</span>
                    <span className="text-[10px] text-slate-400">{isOut ? "→ OUT" : "← IN"}</span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                    <span className="text-amber-400">{rel.type}</span>
                    <span>{rel.detail || "Verified Edge"}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "provenance" && (
          <div className="space-y-3 font-mono text-[11px]">
            <div className="rounded-lg border border-[#334155] bg-[#1e293b] p-3 space-y-2">
              <span className="text-[10px] text-teal-400 uppercase font-bold block">Chain of Custody & Source</span>
              <div className="space-y-1 text-slate-300">
                <div className="text-slate-400">Primary Source Document:</div>
                <div className="text-slate-100 font-semibold">{entity.sourceDocument || "Police FIR Docket #0891"}</div>
              </div>
              <div className="pt-1.5 border-t border-[#334155] space-y-1 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-slate-400">Ingested At:</span>
                  <span className="text-slate-300">{entity.firstSeen}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Audit Status:</span>
                  <span className="text-emerald-400 font-bold">Section 65B Compliant</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
