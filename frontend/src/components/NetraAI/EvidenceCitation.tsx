import React from "react";
import {
  ExternalLink,
  ShieldCheck,
  FileCheck2,
  Share2,
  Users,
  AlertTriangle,
} from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import type { EvidenceCitation as CitationType } from "@/utils/evidenceMatcher";

interface EvidenceCitationProps {
  citations: CitationType[];
}

export function EvidenceCitation({ citations }: EvidenceCitationProps) {
  const navigate = useNavigate();

  const handleNavigate = (route: string) => {
    navigate({ to: route as any });
  };

  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-4 text-xs select-none space-y-3 font-sans shadow-xl">
      {/* Header */}
      <div className="border-b border-[#E2E8F0] pb-2 flex items-center justify-between">
        <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase font-bold text-emerald-400">
          <ShieldCheck className="size-3.5" />
          <span>Evidence Citation Register ({citations.length} Corroborating Sources)</span>
        </div>

        <span className="font-mono text-[9px] text-slate-500">
          Section 65B Certified Chain
        </span>
      </div>

      {/* Citations List */}
      <div className="space-y-2 font-mono text-[11px]">
        {citations.map((cite) => (
          <div
            key={cite.id}
            onClick={() => handleNavigate(cite.deepLinkRoute)}
            className="rounded border border-[#E2E8F0] bg-white p-2.5 space-y-1.5 hover:border-emerald-500/60 hover:bg-[#14201C] transition-all cursor-pointer group"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-1.5 min-w-0">
                <span className="rounded bg-slate-100 px-1.5 py-0.2 text-[9px] text-slate-700 font-bold">
                  {cite.id}
                </span>
                <strong className="text-slate-900 text-xs truncate group-hover:text-emerald-300 transition-colors">
                  {cite.title}
                </strong>
              </div>

              <span className="shrink-0 flex items-center gap-1 text-[10px] font-bold text-emerald-400">
                {cite.confidenceScore}% Conf
                <ExternalLink className="size-3 text-slate-500 group-hover:text-emerald-400" />
              </span>
            </div>

            <p className="text-[10px] text-slate-400 font-sans leading-tight">
              {cite.subtitle}
            </p>

            {cite.statutoryBasis && (
              <div className="text-[9px] text-slate-500 pt-0.5 border-t border-[#E2E8F0]/80">
                Statutory Basis: <strong className="text-slate-400">{cite.statutoryBasis}</strong>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
