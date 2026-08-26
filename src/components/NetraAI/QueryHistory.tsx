import React from "react";
import { History, Bookmark, Sparkles, Clock, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export interface QueryHistoryItem {
  id: string;
  query: string;
  intent: string;
  timestamp: string;
  isSaved?: boolean;
}

interface QueryHistoryProps {
  history: QueryHistoryItem[];
  onSelectHistory: (query: string) => void;
  onToggleSave: (id: string) => void;
}

export function QueryHistory({
  history,
  onSelectHistory,
  onToggleSave,
}: QueryHistoryProps) {
  return (
    <div className="space-y-3 font-sans select-none text-xs">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <label className="text-[10px] font-mono uppercase font-bold text-slate-400 flex items-center gap-1">
          <History className="size-3 text-sky-400" /> Recent Graph Queries ({history.length})
        </label>
      </div>

      <div className="space-y-1.5 font-mono text-[11px]">
        {history.map((item) => (
          <div
            key={item.id}
            onClick={() => onSelectHistory(item.query)}
            className="rounded border border-slate-800 bg-[#121820] p-2 hover:border-sky-500/50 hover:bg-[#14202A] transition-all cursor-pointer group space-y-1"
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-slate-200 text-xs font-sans truncate block group-hover:text-sky-300">
                {item.query}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleSave(item.id);
                }}
                className={cn(
                  "p-0.5 rounded cursor-pointer",
                  item.isSaved ? "text-amber-400" : "text-slate-600 hover:text-slate-400"
                )}
                title="Bookmark Query"
              >
                <Bookmark className="size-3" />
              </button>
            </div>

            <div className="flex items-center justify-between text-[9px] text-slate-500">
              <span className="text-sky-400">{item.intent}</span>
              <span>{new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
