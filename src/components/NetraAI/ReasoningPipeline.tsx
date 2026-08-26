import React from "react";
import { CheckCircle2, Loader2, Sparkles, Cpu, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import type { GraphRAGStep } from "@/services/netraAI";

interface ReasoningPipelineProps {
  steps: GraphRAGStep[];
  isStreaming?: boolean;
}

export function ReasoningPipeline({ steps, isStreaming }: ReasoningPipelineProps) {
  const totalMs = steps.reduce((acc, s) => acc + (s.executionMs || 0), 0);

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-4 text-xs select-none space-y-3 font-sans shadow-xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-2 flex items-center justify-between">
        <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase font-bold text-purple-400">
          <Sparkles className="size-3.5" />
          <span>GraphRAG Reasoning Telemetry ({steps.length} Pipeline Stages)</span>
        </div>

        <span className="font-mono text-[10px] text-slate-400 flex items-center gap-1">
          <Clock className="size-3 text-slate-500" />
          Executed in {totalMs}ms
        </span>
      </div>

      {/* Pipeline Stepper Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 font-mono text-[10px]">
        {steps.map((step) => (
          <div
            key={step.stepNumber}
            className="rounded border border-slate-800/80 bg-[#121820] p-2.5 space-y-1 relative"
          >
            <div className="flex items-center justify-between">
              <span className="text-[9px] uppercase font-bold text-slate-500">
                Step 0{step.stepNumber}
              </span>
              <CheckCircle2 className="size-3 text-emerald-400" />
            </div>

            <div className="font-bold text-slate-200 truncate">{step.name}</div>
            <p className="text-[9px] text-slate-400 leading-tight font-sans line-clamp-2">
              {step.description}
            </p>

            {step.nodesScanned && (
              <div className="text-[8px] text-sky-400 pt-0.5">
                Scanned: {step.nodesScanned} Nodes ({step.executionMs}ms)
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
