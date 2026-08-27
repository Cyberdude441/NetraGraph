import React, { useState } from "react";
import { Search, Send, Loader2 } from "lucide-react";
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
      <div className="flex items-center gap-2 rounded-md border border-[#E5E7EB] bg-white px-4 py-3 text-xs text-[#111827] focus-within:border-[#16A34A] focus-within:ring-1 focus-within:ring-[#16A34A] transition-all shadow-xs">
        <Search className="size-4 text-[#064E3B] shrink-0" />
        <input
          type="text"
          placeholder="What would you like to investigate? (e.g. Find connections between Vikram and ICICI Bank)..."
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          className="w-full bg-transparent text-xs text-[#111827] placeholder:text-[#9CA3AF] outline-none font-sans"
        />

        <button
          type="submit"
          disabled={isLoading || !inputVal.trim()}
          className={cn(
            "flex items-center gap-1.5 rounded-md px-4 py-2 text-xs font-semibold transition-all cursor-pointer",
            inputVal.trim() && !isLoading
              ? "bg-[#064E3B] hover:bg-[#04382A] text-white shadow-xs"
              : "bg-[#F3F4F6] text-[#9CA3AF] cursor-not-allowed"
          )}
        >
          {isLoading ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <>
              <span>Investigate</span>
              <Send className="size-3.5" />
            </>
          )}
        </button>
      </div>
    </form>
  );
}
