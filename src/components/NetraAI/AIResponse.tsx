import React from "react";
import {
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  Flame,
  CheckCircle2,
  AlertTriangle,
  Info,
  Clock,
  Share2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { NetraAIResponse } from "@/services/netraAI";
import { ReasoningPipeline } from "./ReasoningPipeline";
import { GraphQueryViewer } from "./GraphQueryViewer";

interface AIResponseProps {
  response: NetraAIResponse;
}

export function AIResponse({ response }: AIResponseProps) {
  const isHighConf = response.confidenceScore >= 90;

  return (
    <div className="space-y-4 font-sans select-none">
      {/* Visual GraphRAG Pipeline Telemetry */}
      <ReasoningPipeline steps={response.pipelineSteps} />

      {/* Generated Cypher Query Plan */}
      <GraphQueryViewer
        cypherQuery={response.parsedQuery.suggestedCypherQuery}
        intentLabel={response.parsedQuery.intentLabel}
      />

      {/* Main AI Response Card */}
      <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs space-y-4 shadow-2xl">
        {/* Header Line */}
        <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-purple-950/60 border border-purple-800 text-purple-300">
              <Sparkles className="size-4" />
            </span>
            <div>
              <h3 className="font-bold text-slate-100 text-sm uppercase">
                Netra AI Intelligence Brief
              </h3>
              <p className="text-[10px] font-mono text-slate-400">
                Grounding: Neo4j Knowledge Graph & FIU-IND Telemetry · Case: {response.parsedQuery.targetCaseId}
              </p>
            </div>
          </div>

          {/* Confidence Score Pill */}
          <span
            className={cn(
              "rounded px-2.5 py-1 font-mono text-xs font-bold border",
              isHighConf
                ? "bg-emerald-950/80 text-emerald-300 border-emerald-500/60"
                : "bg-amber-950/80 text-amber-300 border-amber-500/50"
            )}
          >
            {response.confidence} Confidence: {response.confidenceScore}%
          </span>
        </div>

        {/* 1. Executive Summary */}
        <div className="rounded border border-purple-900/40 bg-purple-950/20 p-3.5 space-y-1">
          <span className="text-[10px] font-mono uppercase font-bold text-purple-400 block">
            1. Executive Synthesis Summary
          </span>
          <p className="text-xs text-slate-100 font-sans leading-relaxed">
            {response.summary}
          </p>
        </div>

        {/* 2. Observed Graph Data */}
        <div className="rounded border border-slate-800 bg-[#121820] p-3.5 space-y-2">
          <span className="text-[10px] font-mono uppercase font-bold text-slate-400 block">
            2. Verified Graph Observations (Empirical Data Points)
          </span>
          <div className="space-y-1.5 font-mono text-[11px] text-slate-300">
            {response.observedData.map((item, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <CheckCircle2 className="size-3.5 text-sky-400 shrink-0 mt-0.5" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 3. Graph Evidence Metrics */}
        <div className="rounded border border-slate-800 bg-[#121820] p-3.5 space-y-2 font-mono text-[11px]">
          <span className="text-[10px] uppercase font-bold text-slate-400 block">
            3. Network Topological Evidence
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="rounded bg-[#161D24] p-2 border border-slate-800">
              <span className="text-[9px] text-slate-500 block">CLUSTER</span>
              <strong className="text-slate-200 text-xs truncate block">
                {response.graphEvidence.clusterName}
              </strong>
            </div>
            <div className="rounded bg-[#161D24] p-2 border border-slate-800">
              <span className="text-[9px] text-slate-500 block">PATHS FOUND</span>
              <strong className="text-sky-300 text-xs">
                {response.graphEvidence.pathsFound} Multi-Hop Links
              </strong>
            </div>
            <div className="rounded bg-[#161D24] p-2 border border-slate-800">
              <span className="text-[9px] text-slate-500 block">GLOBAL RANK</span>
              <strong className="text-amber-400 text-xs">
                #{response.graphEvidence.centralityRank || 1} Influencer
              </strong>
            </div>
            <div className="rounded bg-[#161D24] p-2 border border-slate-800">
              <span className="text-[9px] text-slate-500 block">ANOMALIES</span>
              <strong className="text-red-400 text-xs">
                {response.graphEvidence.anomaliesCount} Flagged Cycles
              </strong>
            </div>
          </div>
        </div>

        {/* 4. Analytical Interpretation */}
        <div className="rounded border border-sky-900/50 bg-[#0C1A29] p-3.5 space-y-1">
          <span className="text-[10px] font-mono uppercase font-bold text-sky-400 block">
            4. Analytical Inference & Threat Assessment
          </span>
          <p className="text-xs text-slate-200 font-sans leading-relaxed">
            {response.analyticalInterpretation}
          </p>
        </div>

        {/* 5. Mandatory Human Verification Disclaimer */}
        <div className="rounded border border-amber-900/60 bg-amber-950/20 p-3 text-[10px] font-mono text-amber-300 flex items-start gap-2">
          <AlertTriangle className="size-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed font-sans">
            <strong>Analyst Verification Required:</strong> {response.analystVerification}
          </div>
        </div>
      </div>
    </div>
  );
}
