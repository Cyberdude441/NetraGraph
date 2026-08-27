import React from "react";
import { Share2, Flame, FileText, Repeat } from "lucide-react";

interface SuggestedActionsProps {
  onSelectQuery: (query: string) => void;
}

export function SuggestedActions({ onSelectQuery }: SuggestedActionsProps) {
  const suggestions = [
    { text: "Find connections between Vikram and ICICI Bank", icon: Share2, label: "Find connections between Vikram and ICICI Bank" },
    { text: "Summarize case CASE-2026-N09", icon: FileText, label: "Summarize case CASE-2026-N09" },
    { text: "Explain why Vikramaditya Rawat has high risk", icon: Flame, label: "Explain why Vikramaditya Rawat has high risk" },
    { text: "Review circular transaction anomalies", icon: Repeat, label: "Review circular transaction anomalies" },
  ];

  return (
    <div className="space-y-2 select-none font-sans">
      <span className="text-xs font-semibold text-[#64748B] block">
        Suggested Inquiries:
      </span>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((s, idx) => {
          const Icon = s.icon;
          return (
            <button
              key={idx}
              onClick={() => onSelectQuery(s.text)}
              className="flex items-center gap-1.5 rounded-full border border-[#D9E2EC] bg-white px-3.5 py-1.5 text-xs font-medium text-[#065F46] hover:border-[#065F46] hover:bg-emerald-50/50 transition-all cursor-pointer text-left shadow-xs"
            >
              <Icon className="size-3.5 text-[#065F46] shrink-0" />
              <span>{s.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
