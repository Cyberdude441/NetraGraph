import React, { useState } from "react";
import {
  Calendar,
  Play,
  RotateCcw,
  Activity,
  TrendingUp,
  Share2,
  Clock,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { SyntheticEntity, SyntheticRelationship } from "@/data/syntheticGraphData";
import { calculateNetworkEvolution, type NetworkEvolutionSnapshot } from "@/utils/networkMetrics";

interface NetworkEvolutionProps {
  entities: SyntheticEntity[];
  relationships: SyntheticRelationship[];
}

export function NetworkEvolution({ entities, relationships }: NetworkEvolutionProps) {
  const [timeframe, setTimeframe] = useState<"7D" | "30D" | "1Y" | "ALL">("ALL");

  const snapshot: NetworkEvolutionSnapshot = calculateNetworkEvolution(
    entities,
    relationships,
    timeframe
  );

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header & Playback Horizon Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Clock className="size-4 text-sky-400" />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
              Time-Based Network Evolution & Growth Playback
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              Temporal window progression tracking new relationships, community expansion, and transaction velocity.
            </p>
          </div>
        </div>

        {/* Timeframe Buttons */}
        <div className="flex items-center gap-1 rounded bg-[#161D24] p-1 border border-slate-800 font-mono text-xs">
          {(
            [
              { id: "7D", label: "Last 7 Days" },
              { id: "30D", label: "Last 30 Days" },
              { id: "1Y", label: "Past Year" },
              { id: "ALL", label: "Full Evolution" },
            ] as const
          ).map((t) => {
            const active = timeframe === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTimeframe(t.id)}
                className={cn(
                  "rounded px-2.5 py-1 font-bold transition-all cursor-pointer",
                  active
                    ? "bg-sky-500/20 text-sky-300 border border-sky-500/50"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                {t.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Evolution Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
        <div className="rounded border border-slate-800 bg-[#121820] p-3">
          <span className="text-[9px] uppercase text-slate-500 font-bold block">
            ACTIVE ENTITIES
          </span>
          <div className="text-xl font-bold text-slate-100 mt-1">
            {snapshot.totalActiveEntities} Nodes
          </div>
          <span className="text-[9px] text-sky-400">In Selected Window</span>
        </div>

        <div className="rounded border border-slate-800 bg-[#121820] p-3">
          <span className="text-[9px] uppercase text-slate-500 font-bold block">
            ACTIVE LINKAGES
          </span>
          <div className="text-xl font-bold text-slate-100 mt-1">
            {snapshot.totalActiveLinks} Edges
          </div>
          <span className="text-[9px] text-emerald-400">+{snapshot.newLinksCount} New Links</span>
        </div>

        <div className="rounded border border-slate-800 bg-[#121820] p-3">
          <span className="text-[9px] uppercase text-slate-500 font-bold block">
            DOMINANT CLUSTER
          </span>
          <div className="text-sm font-bold text-purple-400 mt-1 truncate">
            {snapshot.dominantActiveCluster}
          </div>
          <span className="text-[9px] text-slate-500">Highest Link Surge</span>
        </div>

        <div className="rounded border border-slate-800 bg-[#121820] p-3">
          <span className="text-[9px] uppercase text-slate-500 font-bold block">
            TRANSACTION VELOCITY
          </span>
          <div className="text-lg font-bold text-amber-400 mt-1">
            ₹{(snapshot.financialVelocityINR / 10000000).toFixed(2)} Cr
          </div>
          <span className="text-[9px] text-slate-500">Cumulative Transfers</span>
        </div>
      </div>
    </div>
  );
}
