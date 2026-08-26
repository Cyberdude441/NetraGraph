import React from "react";
import {
  Info,
  Award,
  Share2,
  TrendingUp,
  ShieldAlert,
  Flame,
  CheckCircle2,
  AlertTriangle,
  FileCheck2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { CentralityScore } from "@/utils/centralityAlgorithms";

interface ExplainabilityPanelProps {
  score: CentralityScore | null;
  onNavigateToGraph?: (id: string) => void;
}

export function ExplainabilityPanel({
  score,
  onNavigateToGraph,
}: ExplainabilityPanelProps) {
  if (!score) {
    return (
      <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-4 text-xs font-mono text-slate-500 text-center">
        Select an entity from the leaderboard to view algorithm explainability reasoning.
      </div>
    );
  }

  const isHighRisk = score.riskScore >= 85;

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-4 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-3 flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-1.5 text-sky-400 font-mono font-bold text-[10px] uppercase">
            <Info className="size-3.5" />
            <span>Algorithm Decision Reasoning</span>
          </div>
          <h3 className="font-bold text-slate-100 text-sm mt-0.5 uppercase">
            {score.name}
          </h3>
          <span className="text-[10px] font-mono text-slate-400">
            ID: {score.entityId} · {score.role || score.label}
          </span>
        </div>

        <span
          className={cn(
            "rounded px-2 py-0.5 font-mono text-[10px] font-bold border",
            isHighRisk
              ? "bg-red-950/80 text-red-300 border-red-500/60"
              : "bg-amber-950/80 text-amber-300 border-amber-500/60"
          )}
        >
          Rank #{score.overallRank} · Risk {score.riskScore}
        </span>
      </div>

      {/* Structured Reasoning 3-Tier Card */}
      <div className="space-y-3 font-sans">
        {/* 1. Observation: Raw Graph Statistics */}
        <div className="rounded border border-slate-800 bg-[#121820] p-3 space-y-1.5">
          <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-slate-400 block">
            1. Raw Graph Observations (Empirical Telemetry):
          </span>
          <div className="space-y-1 text-[11px] font-mono text-slate-300">
            <div className="flex items-center gap-1.5">
              <span className="text-sky-400">•</span>
              <span>Direct Link Connectivity: <strong>{score.degree} links</strong> (Top {score.normalizedDegree * 100}% of network)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-purple-400">•</span>
              <span>Betweenness Intermediary Score: <strong>{score.betweenness}%</strong> (Rank #{score.betweennessRank})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-emerald-400">•</span>
              <span>PageRank Authority Weight: <strong>{score.pageRank}%</strong> (Rank #{score.pageRankRank})</span>
            </div>
          </div>
        </div>

        {/* 2. Analysis: Algorithm Interpretation */}
        <div className="rounded border border-sky-900/60 bg-[#0C1A29] p-3 space-y-1.5">
          <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-sky-400 block">
            2. Algorithm Analysis (Topological Role):
          </span>
          <p className="text-[11px] text-slate-200 leading-relaxed font-sans">
            {score.explanation}
          </p>
        </div>

        {/* 3. Conclusion: Actionable Investigation Advice */}
        <div className="rounded border border-amber-900/60 bg-amber-950/20 p-3 space-y-1">
          <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-amber-400 block flex items-center gap-1">
            <AlertTriangle className="size-3" /> 3. Investigative Recommendation:
          </span>
          <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
            {score.betweenness > 15
              ? "Critical bridge node: Disrupting communications on this entity's channels will sever coordination between connected syndicate cells."
              : "High-authority command node: Target for digital search warrants and banking freeze orders under IT Act Section 69B."}
          </p>
        </div>
      </div>
    </div>
  );
}
