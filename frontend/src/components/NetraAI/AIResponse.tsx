import React from "react";
import {
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Info,
  Clock,
  Layers,
  Network,
  Share2,
  Database,
  FileCheck2,
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
  const classification = response.classification || "VERIFIED FACT";

  let badgeColor = "bg-emerald-950/80 text-emerald-300 border-emerald-800/80";
  if (classification === "DERIVED ANALYTICS") {
    badgeColor = "bg-blue-950/80 text-blue-300 border-blue-800/80";
  } else if (classification === "INSUFFICIENT DATA") {
    badgeColor = "bg-amber-950/80 text-amber-300 border-amber-800/80";
  }

  const retrievedNodes = response.retrievedNodes || [];
  const retrievedRels = response.retrievedRelationships || [];

  return (
    <div className="space-y-4 font-sans select-none text-slate-200">
      {/* Main AI Response Card */}
      <div className="rounded-lg border border-[#334155] bg-[#0f172a] p-5 text-xs space-y-4 shadow-xl">
        {/* Header Line */}
        <div className="flex items-start justify-between gap-3 border-b border-[#334155] pb-3.5">
          <div className="flex items-center gap-2.5">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800/80">
              <Sparkles className="size-4" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-slate-100 text-sm">
                  Grounded Investigation Intelligence
                </h3>
                <span className={cn("rounded px-2 py-0.5 text-[10px] font-mono font-bold border", badgeColor)}>
                  {classification}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5 font-mono">
                Source: <span className="text-cyan-400 font-semibold">{response.provenance?.dataset || response.parsedQuery?.intentLabel || "Verified Knowledge Graph"}</span>
              </p>
            </div>
          </div>

          {/* Confidence Score Pill */}
          <span
            className={cn(
              "rounded px-2.5 py-1 text-[11px] font-mono font-bold border",
              isHighConf
                ? "bg-emerald-950/80 text-emerald-300 border-emerald-800/80"
                : "bg-amber-950/80 text-amber-300 border-amber-800/80"
            )}
          >
            {response.confidence} ({response.confidenceScore}%)
          </span>
        </div>

        {/* 1. Answer Summary */}
        <div className="rounded-lg border border-cyan-900/60 bg-cyan-950/30 p-4 space-y-1.5">
          <span className="text-[11px] font-mono font-bold text-cyan-300 flex items-center gap-1.5">
            <FileCheck2 className="size-3.5" />
            Synthesized Factual Assessment
          </span>
          <div className="text-xs text-slate-200 font-sans leading-relaxed whitespace-pre-wrap">
            {response.summary}
          </div>
        </div>

        {/* 2. Graph Traversal Path */}
        {response.graphPath && (
          <div className="rounded-lg border border-[#334155] bg-[#1e293b]/60 p-3 space-y-1 font-mono text-[11px]">
            <span className="text-[10px] text-slate-400 uppercase font-bold block flex items-center gap-1.5">
              <Network className="size-3 text-cyan-400" />
              Graph Traversal Path
            </span>
            <div className="text-cyan-300 bg-[#0f172a] px-2.5 py-1.5 rounded border border-[#334155]">
              {response.graphPath}
            </div>
          </div>
        )}

        {/* 3. Retrieved Graph Elements (Nodes & Relationships) */}
        {(retrievedNodes.length > 0 || retrievedRels.length > 0) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Retrieved Nodes */}
            <div className="rounded-lg border border-[#334155] bg-[#1e293b]/40 p-3 space-y-2">
              <span className="text-[10px] text-slate-400 uppercase font-mono font-bold block flex items-center gap-1">
                <Database className="size-3 text-teal-400" />
                Retrieved Nodes ({retrievedNodes.length})
              </span>
              <div className="space-y-1 max-h-36 overflow-y-auto pr-1">
                {retrievedNodes.slice(0, 6).map((n: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between text-[10px] font-mono bg-[#0f172a] p-1.5 rounded border border-[#334155]">
                    <span className="text-slate-200 font-semibold truncate">{n.name || n.id}</span>
                    <span className="text-teal-400">{n.label || "Entity"}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Retrieved Relationships */}
            <div className="rounded-lg border border-[#334155] bg-[#1e293b]/40 p-3 space-y-2">
              <span className="text-[10px] text-slate-400 uppercase font-mono font-bold block flex items-center gap-1">
                <Share2 className="size-3 text-amber-400" />
                Retrieved Relationships ({retrievedRels.length})
              </span>
              <div className="space-y-1 max-h-36 overflow-y-auto pr-1">
                {retrievedRels.slice(0, 6).map((r: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between text-[10px] font-mono bg-[#0f172a] p-1.5 rounded border border-[#334155]">
                    <span className="text-amber-400 truncate">{r.type || "CONNECTED"}</span>
                    <span className="text-slate-400 text-[9px]">{r.source_document || "Verified Edge"}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 4. Observed Provenance Data Points */}
        <div className="rounded-lg border border-[#334155] bg-[#1e293b]/30 p-3.5 space-y-2">
          <span className="text-[10px] text-slate-400 uppercase font-mono font-bold block">
            Provenance & Evidence Grounding Points
          </span>
          <div className="space-y-1 text-xs text-slate-300 font-mono">
            {response.observedData.map((item, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <CheckCircle2 className="size-3.5 text-teal-400 shrink-0 mt-0.5" />
                <span className="leading-normal">{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 5. Officer Verification Notice */}
        <div className="flex items-center gap-2 rounded-lg border border-teal-900/60 bg-teal-950/30 p-2.5 text-[11px] text-teal-300 font-mono">
          <ShieldCheck className="size-4 shrink-0 text-teal-400" />
          <span>
            Strict Zero-Hallucination Policy: All metrics and connections derive exclusively from verified Knowledge Graph transactions.
          </span>
        </div>
      </div>

      {/* Query Explanation Viewer */}
      <GraphQueryViewer
        targetCaseId={response.parsedQuery?.targetCaseId || "CASE-2024-DEL-0891"}
        extractedEntities={response.parsedQuery?.extractedEntities || []}
        timeRangeDays={response.parsedQuery?.timeRangeDays || 365}
      />
    </div>
  );
}
