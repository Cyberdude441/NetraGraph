import React, { useState } from "react";
import { Search, Sparkles, Send, Loader2, CornerDownLeft } from "lucide-react";
import { cn } from "@/lib/utils";

interface QueryInputProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
}

export function QueryInput({ onSearch, isLoading }: QueryInputProps) {
  const [inputVal, setInputVal] = useState<string>("");

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputVal.trim() || isLoading) return;
    onSearch(inputVal.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="relative select-none font-sans">
      <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-[#121820] px-3.5 py-2.5 text-xs text-slate-200 focus-within:border-sky-500 transition-all shadow-inner">
        <Sparkles className="size-4 text-purple-400 shrink-0" />
        <input
          type="text"
          placeholder="Ask Netra AI (e.g. 'Show connections between Vikramaditya and Arjun', 'Explain high risk score')..."
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          className="w-full bg-transparent text-xs text-slate-100 placeholder:text-slate-500 outline-none font-sans"
        />

        <button
          type="submit"
          disabled={isLoading || !inputVal.trim()}
          className={cn(
            "flex items-center gap-1 rounded px-3 py-1 text-xs font-mono font-bold transition-all cursor-pointer",
            inputVal.trim() && !isLoading
              ? "bg-purple-600 hover:bg-purple-500 text-white shadow-md"
              : "bg-slate-800 text-slate-500 cursor-not-allowed"
          )}
        >
          {isLoading ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <>
              <span>Query Graph</span>
              <CornerDownLeft className="size-3" />
            </>
          )}
        </button>
      </div>
    </form>
  );
}
