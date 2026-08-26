import React from "react";
import {
  Scissors,
  RotateCcw,
  Download,
  Bookmark,
  Sparkles,
  CheckCircle2,
  Share2,
} from "lucide-react";
import { toast } from "sonner";

interface SubgraphWorkspaceProps {
  selectedNodeIds: Set<string>;
  isIsolated: boolean;
  totalEntities: number;
  visibleEntities: number;
  onIsolateSelected: () => void;
  onResetIsolation: () => void;
  onSaveSnapshot: () => void;
}

export function SubgraphWorkspace({
  selectedNodeIds,
  isIsolated,
  totalEntities,
  visibleEntities,
  onIsolateSelected,
  onResetIsolation,
  onSaveSnapshot,
}: SubgraphWorkspaceProps) {
  const handleExportJson = () => {
    toast.success("Graph Snapshot Exported", {
      description: `Encrypted dossier snapshot with ${visibleEntities} nodes generated.`,
    });
    onSaveSnapshot();
  };

  return (
    <div className="flex items-center gap-2 font-mono text-xs select-none">
      {/* Subgraph Indicator */}
      <div className="flex items-center gap-1.5 rounded border border-slate-800 bg-[#161D24] px-2.5 py-1 text-[11px] text-slate-300">
        <span className="size-2 rounded-full bg-sky-400 animate-pulse" />
        <span>
          Showing <strong className="text-sky-300">{visibleEntities}</strong> of{" "}
          <strong className="text-slate-400">{totalEntities}</strong> entities
        </span>
      </div>

      {/* Isolate Subgraph Button */}
      {selectedNodeIds.size > 0 && !isIsolated && (
        <button
          onClick={onIsolateSelected}
          className="flex items-center gap-1 rounded border border-sky-500/60 bg-sky-950/40 px-2.5 py-1 text-[11px] font-bold text-sky-300 hover:bg-sky-900/50 transition-all cursor-pointer shadow-xs"
        >
          <Scissors className="size-3 text-sky-400" />
          <span>Isolate Selection ({selectedNodeIds.size})</span>
        </button>
      )}

      {/* Reset Subgraph Button */}
      {isIsolated && (
        <button
          onClick={onResetIsolation}
          className="flex items-center gap-1 rounded border border-amber-500/60 bg-amber-950/40 px-2.5 py-1 text-[11px] font-bold text-amber-300 hover:bg-amber-900/50 transition-all cursor-pointer shadow-xs"
        >
          <RotateCcw className="size-3 text-amber-400" />
          <span>Exit Isolated Subgraph</span>
        </button>
      )}

      {/* Snapshot Export */}
      <button
        onClick={handleExportJson}
        className="flex items-center gap-1 rounded border border-slate-800 bg-[#161D24] px-2.5 py-1 text-[11px] font-medium text-slate-300 hover:border-slate-700 hover:text-slate-100 transition-colors cursor-pointer"
        title="Export evidence snapshot docket"
      >
        <Download className="size-3 text-slate-400" />
        <span>Export Snapshot</span>
      </button>
    </div>
  );
}
