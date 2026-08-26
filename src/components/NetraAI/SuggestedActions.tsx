import React from "react";
import { Sparkles, Share2, Award, Flame, FileText, Repeat } from "lucide-react";

interface SuggestedActionsProps {
  onSelectQuery: (query: string) => void;
}

export function SuggestedActions({ onSelectQuery }: SuggestedActionsProps) {
  const suggestions = [
    { text: "Show connections between Vikramaditya Rawat and Arjun Menon", icon: Share2, label: "Shortest Path" },
    { text: "Who are the most influential kingpin entities in this network?", icon: Award, label: "Centrality Ranks" },
    { text: "Explain why Vikramaditya Rawat has a high analytical risk score.", icon: Flame, label: "Risk Attribution" },
    { text: "Find unusual circular transaction loops and fund recycling.", icon: Repeat, label: "Financial Loop" },
    { text: "Summarize this investigation and generate case briefing.", icon: FileText, label: "Briefing Synthesis" },
  ];

  return (
    <div className="space-y-2 select-none font-sans">
      <span className="text-[10px] font-mono uppercase font-bold text-slate-500 block">
        Suggested Forensic Inquiries:
      </span>
      <div className="flex flex-wrap gap-1.5">
        {suggestions.map((s, idx) => {
          const Icon = s.icon;
          return (
            <button
              key={idx}
              onClick={() => onSelectQuery(s.text)}
              className="flex items-center gap-1.5 rounded border border-slate-800 bg-[#121820] px-2.5 py-1 text-[11px] font-mono text-slate-300 hover:border-sky-500/50 hover:bg-[#14202A] transition-all cursor-pointer text-left"
            >
              <Icon className="size-3 text-sky-400 shrink-0" />
              <span className="truncate">{s.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
