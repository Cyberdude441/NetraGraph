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
      {/* Main AI Response Card */}
      <div className="rounded-md border border-[#E5E7EB] bg-white p-5 text-xs space-y-4 shadow-xs">
        {/* Header Line */}
        <div className="flex items-start justify-between gap-3 border-b border-[#E5E7EB] pb-3.5">
          <div className="flex items-center gap-2.5">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-emerald-50 border border-emerald-200 text-[#064E3B]">
              <Sparkles className="size-4 text-[#16A34A]" />
            </span>
            <div>
              <h3 className="font-bold text-[#111827] text-sm">
                Investigation Intelligence Assessment
              </h3>
              <p className="text-xs text-[#64748B] mt-0.5">
                Grounding: Case Graph Data · Docket: <strong className="font-mono text-[#064E3B]">{response.parsedQuery.targetCaseId}</strong>
              </p>
            </div>
          </div>

          {/* Confidence Score Pill */}
          <span
            className={cn(
              "rounded-md px-3 py-1 text-xs font-bold border",
              isHighConf
                ? "bg-emerald-50 text-[#16A34A] border-emerald-200"
                : "bg-amber-50 text-[#F59E0B] border-amber-200"
            )}
          >
            {response.confidence} Confidence: {response.confidenceScore}%
          </span>
        </div>

        {/* 1. Observation / Summary */}
        <div className="rounded-md border border-emerald-100 bg-emerald-50/50 p-4 space-y-1">
          <span className="text-xs font-bold text-[#064E3B] block">
            Observation
          </span>
          <p className="text-xs text-[#111827] font-sans leading-relaxed">
            {response.summary}
          </p>
        </div>

        {/* 2. Evidence */}
        <div className="rounded-md border border-[#E5E7EB] bg-[#F8FAF8] p-4 space-y-2.5">
          <span className="text-xs font-bold text-[#111827] block">
            Evidence & Verified Data Points
          </span>
          <div className="space-y-1.5 text-xs text-[#374151]">
            {response.observedData.map((item, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <CheckCircle2 className="size-4 text-[#16A34A] shrink-0 mt-0.5" />
                <span className="leading-normal">{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 3. Related Entities */}
        <div className="rounded-md border border-[#E5E7EB] bg-white p-3.5 space-y-2">
          <span className="text-xs font-bold text-[#111827] block">
            Related Entities Involved
          </span>
          <div className="flex flex-wrap gap-2">
            {[response.parsedQuery.targetCaseId, response.graphEvidence.clusterName, "Vikramaditya Rawat", "ICICI Bank - A/C 9402"].map((ent, idx) => (
              <span
                key={idx}
                className="rounded-md bg-[#F3F4F6] border border-[#E5E7EB] px-2.5 py-1 text-xs font-medium text-[#064E3B]"
              >
                {ent}
              </span>
            ))}
          </div>
        </div>

        {/* 4. Officer Verification Notice */}
        <div className="rounded-md border border-amber-200 bg-amber-50/50 p-3 text-xs text-[#0F172A] flex items-start gap-2">
          <AlertTriangle className="size-4 text-[#F59E0B] shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <strong className="text-[#F59E0B]">Investigating Officer Notice:</strong> {response.analystVerification}
          </div>
        </div>
      </div>
    </div>
  );
}
