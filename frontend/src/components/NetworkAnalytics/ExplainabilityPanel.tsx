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
      <div className="rounded-md border border-[#D9E2EC] bg-white p-4 text-xs text-[#64748B] text-center shadow-xs">
        Select a suspect or entity from the list to view why it is highlighted.
      </div>
    );
  }

  const isHighRisk = score.riskScore >= 85;

  return (
    <div className="rounded-md border border-[#D9E2EC] bg-white p-4 text-xs select-none space-y-4 font-sans shadow-xs">
      {/* Header */}
      <div className="border-b border-[#E2E8F0] pb-3 flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-1.5 text-[#065F46] font-bold text-xs">
            <Info className="size-3.5" />
            <span>Why is this suspect highlighted?</span>
          </div>
          <h3 className="font-bold text-[#0F172A] text-sm mt-0.5">
            {score.name}
          </h3>
          <span className="text-xs text-[#64748B]">
            ID: <strong className="font-mono text-[#065F46]">{score.entityId}</strong> · {score.role || score.label}
          </span>
        </div>

        <span
          className={cn(
            "rounded-md px-2.5 py-1 text-xs font-bold border",
            isHighRisk
              ? "bg-red-50 text-[#DC3545] border-red-200"
              : "bg-amber-50 text-[#F59E0B] border-amber-200"
          )}
        >
          Rank #{score.overallRank} · Risk {score.riskScore}/100
        </span>
      </div>

      {/* Structured Reasoning 3-Tier Card */}
      <div className="space-y-3 font-sans">
        {/* 1. Observation: Raw Graph Statistics */}
        <div className="rounded-md border border-[#D9E2EC] bg-[#F8FAFC] p-3 space-y-1.5">
          <span className="text-xs font-bold text-[#0F172A] block">
            1. Key Connectivity Metrics:
          </span>
          <div className="space-y-1 text-xs text-[#475569]">
            <div className="flex items-center gap-1.5">
              <span className="text-[#065F46]">•</span>
              <span>Direct Connections: <strong className="text-[#0F172A]">{score.degree} links</strong></span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[#065F46]">•</span>
              <span>Network Bridge Importance: <strong className="text-[#0F172A]">{score.betweenness}%</strong> (Rank #{score.betweennessRank})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[#065F46]">•</span>
              <span>Suspect Influence Score: <strong className="text-[#0F172A]">{score.pageRank}%</strong> (Rank #{score.pageRankRank})</span>
            </div>
          </div>
        </div>

        {/* 2. Analysis: Algorithm Interpretation */}
        <div className="rounded-md border border-emerald-200 bg-emerald-50/50 p-3 space-y-1">
          <span className="text-xs font-bold text-[#065F46] block">
            2. Network Role Analysis:
          </span>
          <p className="text-xs text-[#0F172A] leading-relaxed">
            {score.explanation}
          </p>
        </div>

        {/* 3. Conclusion: Actionable Investigation Advice */}
        <div className="rounded-md border border-amber-200 bg-amber-50/50 p-3 space-y-1">
          <span className="text-xs font-bold text-[#F59E0B] block flex items-center gap-1">
            <AlertTriangle className="size-3.5" /> 3. Recommended Investigation Action:
          </span>
          <p className="text-xs text-[#0F172A] leading-relaxed">
            {score.betweenness > 15
              ? "Key operational bridge: Monitoring or securing warrants on this node will disrupt coordination between multiple suspect groups."
              : "High-influence controller: Target for search warrant, CDR analysis, and banking freeze notices under IT Act Section 69B."}
          </p>
        </div>
      </div>
    </div>
  );
}
