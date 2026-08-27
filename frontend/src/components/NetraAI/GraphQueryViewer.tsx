import React from "react";
import { Database, Copy, Check, Terminal } from "lucide-react";
import { toast } from "sonner";

interface GraphQueryViewerProps {
  cypherQuery: string;
  intentLabel: string;
}

export function GraphQueryViewer({ cypherQuery, intentLabel }: GraphQueryViewerProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(cypherQuery);
    setCopied(true);
    toast.success("Cypher Query Copied to Clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-4 text-xs select-none space-y-2.5 font-sans shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2">
        <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase font-bold text-emerald-400">
          <Terminal className="size-3.5" />
          <span>AI-Generated Graph Query Plan (Cypher / GQL)</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="rounded bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 font-mono text-[9px] text-emerald-300 font-bold">
            {intentLabel}
          </span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-[10px] font-mono text-slate-400 hover:text-slate-800 cursor-pointer p-1 rounded hover:bg-slate-100"
            title="Copy Cypher Query"
          >
            {copied ? <Check className="size-3 text-emerald-400" /> : <Copy className="size-3" />}
          </button>
        </div>
      </div>

      {/* Code Viewer Box */}
      <div className="rounded border border-[#E2E8F0]/90 bg-[#F8FAFC] p-3 font-mono text-[11px] text-emerald-300 leading-relaxed overflow-x-auto whitespace-pre">
        {cypherQuery}
      </div>

      <div className="flex items-center justify-between text-[9px] font-mono text-slate-500">
        <span>Execution Engine: Neo4j 5.x Enterprise / GDS Analytics</span>
        <span>Deterministic Traversal Certified</span>
      </div>
    </div>
  );
}
