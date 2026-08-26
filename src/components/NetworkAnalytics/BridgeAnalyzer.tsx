import React from "react";
import {
  Share2,
  GitMerge,
  ShieldAlert,
  Flame,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  Target,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { CentralityScore } from "@/utils/centralityAlgorithms";
import type { CommunityDetail } from "@/utils/communityDetection";

interface BridgeAnalyzerProps {
  bridgeEntities: CentralityScore[];
  communities: CommunityDetail[];
  onSelectEntity: (id: string) => void;
}

export function BridgeAnalyzer({
  bridgeEntities,
  communities,
  onSelectEntity,
}: BridgeAnalyzerProps) {
  // Filter top betweenness bridge nodes
  const topBridges = bridgeEntities
    .filter((e) => e.betweenness > 10 || e.betweennessRank <= 5)
    .slice(0, 8);

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Share2 className="size-4 text-emerald-400" />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
              Inter-Community Bridge & Broker Intelligence
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              Identifies key single points of failure that connect otherwise separated criminal clusters.
            </p>
          </div>
        </div>

        <span className="rounded bg-emerald-950/40 border border-emerald-800/60 px-2.5 py-1 text-xs font-mono font-bold text-emerald-300">
          {topBridges.length} Critical Bridge Nodes Detected
        </span>
      </div>

      {/* Bridge Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {topBridges.map((bridge) => (
          <div
            key={bridge.entityId}
            onClick={() => onSelectEntity(bridge.entityId)}
            className="rounded-lg border border-slate-800 bg-[#121820] p-3.5 space-y-3 hover:border-emerald-500/60 transition-all cursor-pointer"
          >
            {/* Title & Betweenness Score */}
            <div className="flex items-start justify-between gap-3">
              <div>
                <h4 className="font-bold text-slate-100 text-xs uppercase">
                  {bridge.name}
                </h4>
                <span className="text-[10px] font-mono text-slate-400">
                  ID: {bridge.entityId} · {bridge.role || bridge.label}
                </span>
              </div>

              <div className="text-right font-mono">
                <span className="text-sm font-bold text-emerald-400 block">
                  {bridge.betweenness}%
                </span>
                <span className="text-[9px] text-slate-500">Betweenness Score</span>
              </div>
            </div>

            {/* Bridge Path Explanation */}
            <div className="rounded border border-slate-800/80 bg-[#161D24] p-2.5 space-y-1">
              <span className="text-[9px] font-mono uppercase font-bold text-emerald-400 block flex items-center gap-1">
                <AlertTriangle className="size-3" /> Conduit Role:
              </span>
              <p className="text-[11px] text-slate-300 leading-tight font-sans">
                {bridge.explanation}
              </p>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-3 gap-2 border-t border-slate-800/80 pt-2 font-mono text-[10px] text-slate-400">
              <div>
                <span className="text-slate-500">Degree: </span>
                <strong className="text-slate-200">{bridge.degree} Links</strong>
              </div>
              <div>
                <span className="text-slate-500">PageRank: </span>
                <strong className="text-sky-300">{bridge.pageRank}%</strong>
              </div>
              <div>
                <span className="text-slate-500">Risk: </span>
                <strong className={cn(bridge.riskScore >= 85 ? "text-red-400" : "text-amber-400")}>
                  {bridge.riskScore}/100
                </strong>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
