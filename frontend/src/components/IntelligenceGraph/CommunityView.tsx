import React from "react";
import { PieChart, Users, Share2, Flame, ArrowRight, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CommunityCluster } from "@/utils/graphAlgorithms";

interface CommunityViewProps {
  communities: CommunityCluster[];
  activeClusterId: number | null;
  onSelectCluster: (clusterId: number | null) => void;
  onSelectBridgeNode: (nodeId: string) => void;
}

export function CommunityView({
  communities,
  activeClusterId,
  onSelectCluster,
  onSelectBridgeNode,
}: CommunityViewProps) {
  return (
    <div className="rounded border border-[#E2E8F0] bg-white p-3 text-xs space-y-3 select-none">
      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2">
        <div className="flex items-center gap-2">
          <PieChart className="size-4 text-emerald-400" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-900">
            Detected Criminal Communities ({communities.length} Syndicates)
          </span>
        </div>
        {activeClusterId !== null && (
          <button
            onClick={() => onSelectCluster(null)}
            className="text-[10px] font-mono text-emerald-400 hover:underline cursor-pointer"
          >
            Show All Clusters
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
        {communities.map((comm) => {
          const isActive = activeClusterId === comm.id;
          return (
            <div
              key={comm.id}
              onClick={() => onSelectCluster(isActive ? null : comm.id)}
              className={cn(
                "rounded border p-3 transition-all cursor-pointer",
                isActive
                  ? "border-emerald-500 bg-emerald-50 shadow-lg ring-1 ring-emerald-400/50"
                  : "border-[#E2E8F0] bg-white hover:border-slate-300"
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span
                    className="size-3 rounded-full"
                    style={{ backgroundColor: comm.color }}
                  />
                  <h4 className="font-sans font-bold text-slate-800 text-xs truncate max-w-[180px]">
                    {comm.name}
                  </h4>
                </div>
                <span className="font-mono text-[10px] font-bold text-slate-400 bg-[#F8FAFC] px-1.5 py-0.5 rounded border border-[#E2E8F0]">
                  {comm.memberCount} Nodes
                </span>
              </div>

              <div className="space-y-1.5 text-[11px] font-mono text-slate-400">
                <div className="flex items-center justify-between">
                  <span>Internal Linkages:</span>
                  <span className="text-slate-800 font-bold">{comm.internalEdgeCount}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Avg Risk Score:</span>
                  <span className={cn("font-bold", comm.avgRisk >= 85 ? "text-red-400" : "text-amber-400")}>
                    {comm.avgRisk}/100
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Dominant Class:</span>
                  <span className="text-emerald-300 font-semibold">{comm.dominantType}</span>
                </div>
              </div>

              {/* Bridge Nodes */}
              {comm.bridgeNodeIds.length > 0 && (
                <div className="mt-2.5 border-t border-[#E2E8F0]/80 pt-2">
                  <span className="text-[9px] font-mono uppercase tracking-wider text-amber-400/90 font-bold block mb-1 flex items-center gap-1">
                    <Share2 className="size-2.5" /> Inter-Cluster Bridge Nodes:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {comm.bridgeNodeIds.map((bId) => (
                      <button
                        key={bId}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectBridgeNode(bId);
                        }}
                        className="rounded bg-amber-950/40 border border-amber-800/60 px-1.5 py-0.5 text-[9px] font-mono text-amber-300 hover:border-amber-400 transition-colors cursor-pointer"
                      >
                        {bId}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
