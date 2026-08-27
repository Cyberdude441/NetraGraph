import React from "react";
import {
  Network,
  GitFork,
  PieChart,
  CalendarDays,
  Target,
  Sparkles,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type LayoutMode = "force" | "hierarchical" | "circular" | "timeline";

interface LayoutSwitcherProps {
  currentLayout: LayoutMode;
  onLayoutChange: (mode: LayoutMode) => void;
  hopDistance: number;
  onHopChange: (hops: number) => void;
  hasFocalNode: boolean;
  focalNodeName?: string | undefined;
  totalVisible: number;
}

export function LayoutSwitcher({
  currentLayout,
  onLayoutChange,
  hopDistance,
  onHopChange,
  hasFocalNode,
  focalNodeName,
  totalVisible,
}: LayoutSwitcherProps) {
  const layouts: { id: LayoutMode; label: string; icon: React.ElementType; desc: string }[] = [
    {
      id: "force",
      label: "Force-Directed",
      icon: Network,
      desc: "Physics-based organic clustering",
    },
    {
      id: "hierarchical",
      label: "Hierarchical",
      icon: GitFork,
      desc: "Command & control tiers",
    },
    {
      id: "circular",
      label: "Circular Clusters",
      icon: PieChart,
      desc: "Community orbit separation",
    },
    {
      id: "timeline",
      label: "Timeline Stream",
      icon: CalendarDays,
      desc: "Chronological sequence",
    },
  ];

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E2E8F0] bg-white px-4 py-2 text-xs select-none">
      {/* Layout Engine Switcher */}
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-mono text-slate-400 uppercase font-bold flex items-center gap-1">
          <Layers className="size-3 text-emerald-400" />
          Layout Engine:
        </span>
        <div className="flex items-center gap-1 rounded bg-[#F8FAFC] p-1 border border-[#E2E8F0]">
          {layouts.map((l) => {
            const Icon = l.icon;
            const active = currentLayout === l.id;
            return (
              <button
                key={l.id}
                onClick={() => onLayoutChange(l.id)}
                title={l.desc}
                className={cn(
                  "flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer",
                  active
                    ? "bg-emerald-100 text-emerald-400 border border-emerald-500/40 shadow-xs"
                    : "text-slate-400 hover:text-slate-800"
                )}
              >
                <Icon className={cn("size-3.5", active ? "text-emerald-400" : "text-slate-400")} />
                <span>{l.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Degree-of-Separation (Hop Expansion) Toolbar */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px]">
          <Target className="size-3.5 text-amber-400" />
          <span>Focal Hop Scope:</span>
        </div>

        <div className="flex items-center gap-1 rounded bg-[#F8FAFC] p-0.5 border border-[#E2E8F0]">
          <button
            onClick={() => onHopChange(0)}
            className={cn(
              "rounded px-2 py-0.5 text-[10px] font-mono font-bold transition-all cursor-pointer",
              hopDistance === 0
                ? "bg-emerald-100 text-slate-800 border border-slate-300"
                : "text-slate-400 hover:text-slate-800"
            )}
            title="Show full network without hop attenuation"
          >
            All
          </button>
          <button
            onClick={() => onHopChange(1)}
            disabled={!hasFocalNode}
            className={cn(
              "rounded px-2 py-0.5 text-[10px] font-mono font-bold transition-all cursor-pointer",
              hopDistance === 1
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/50"
                : "text-slate-400 hover:text-slate-800 disabled:opacity-30 disabled:cursor-not-allowed"
            )}
            title="Direct 1st degree connections"
          >
            1-Hop
          </button>
          <button
            onClick={() => onHopChange(2)}
            disabled={!hasFocalNode}
            className={cn(
              "rounded px-2 py-0.5 text-[10px] font-mono font-bold transition-all cursor-pointer",
              hopDistance === 2
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/50"
                : "text-slate-400 hover:text-slate-800 disabled:opacity-30 disabled:cursor-not-allowed"
            )}
            title="2nd degree intermediary perimeter"
          >
            2-Hops
          </button>
          <button
            onClick={() => onHopChange(3)}
            disabled={!hasFocalNode}
            className={cn(
              "rounded px-2 py-0.5 text-[10px] font-mono font-bold transition-all cursor-pointer",
              hopDistance === 3
                ? "bg-purple-500/20 text-purple-300 border border-purple-500/50"
                : "text-slate-400 hover:text-slate-800 disabled:opacity-30 disabled:cursor-not-allowed"
            )}
            title="3rd degree outer syndicate perimeter"
          >
            3-Hops
          </button>
        </div>

        {hasFocalNode && hopDistance > 0 && (
          <span className="rounded bg-emerald-950/60 border border-emerald-800/80 px-2 py-0.5 text-[10px] font-mono text-emerald-300 flex items-center gap-1">
            <Sparkles className="size-3 text-emerald-400" />
            Filtered on: <strong className="text-slate-900 truncate max-w-[120px]">{focalNodeName}</strong>
          </span>
        )}
      </div>
    </div>
  );
}
