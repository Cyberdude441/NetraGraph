import React from "react";
import {
  PieChart,
  Users,
  Share2,
  Flame,
  Award,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { CommunityDetail, ModularityMetrics } from "@/utils/communityDetection";

interface CommunityDetectionProps {
  communities: CommunityDetail[];
  modularity: ModularityMetrics;
  selectedCommunityId: number | null;
  onSelectCommunity: (id: number | null) => void;
  onSelectEntity: (id: string) => void;
}

export function CommunityDetection({
  communities,
  modularity,
  selectedCommunityId,
  onSelectCommunity,
  onSelectEntity,
}: CommunityDetectionProps) {
  return (
    <div className="space-y-4 font-sans select-none">
      {/* Modularity Overview Banner */}
      <div className="rounded-lg border border-[#E2E8F0] bg-white p-4 flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-lg bg-purple-950/60 border border-purple-800 text-purple-300">
            <PieChart className="size-5" />
          </span>
          <div>
            <div className="font-bold text-slate-900 uppercase text-xs">
              Louvain Modularity Cluster Score: <span className="text-purple-400 font-bold">{modularity.modularityScore}</span>
            </div>
            <p className="text-[10px] text-slate-400 font-normal mt-0.5">
              Detected {modularity.communityCount} modular syndicates with {modularity.totalInternalEdges} internal links and {modularity.totalExternalEdges} cross-boundary conduits.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="rounded bg-[#F8FAFC] px-2.5 py-1 text-[11px] border border-[#E2E8F0] text-slate-700">
            Fragmentation: <strong>{modularity.networkFragmentationScore}</strong>
          </span>
          {selectedCommunityId !== null && (
            <button
              onClick={() => onSelectCommunity(null)}
              className="text-[11px] font-mono text-emerald-400 hover:underline cursor-pointer"
            >
              Show All Clusters
            </button>
          )}
        </div>
      </div>

      {/* Community Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {communities.map((comm) => {
          const isSelected = selectedCommunityId === comm.id;

          return (
            <div
              key={comm.id}
              onClick={() => onSelectCommunity(isSelected ? null : comm.id)}
              className={cn(
                "rounded-lg border p-4 transition-all cursor-pointer space-y-3",
                isSelected
                  ? "border-emerald-500 bg-[#141F2B] shadow-xl ring-1 ring-emerald-400/50"
                  : "border-[#E2E8F0] bg-[#10161E] hover:border-slate-300 hover:bg-[#131B25]"
              )}
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <span
                    className="size-3.5 rounded-full shrink-0 shadow-xs"
                    style={{ backgroundColor: comm.color }}
                  />
                  <h3 className="font-bold text-slate-900 text-xs truncate">
                    {comm.name}
                  </h3>
                </div>

                <span className="shrink-0 font-mono text-[10px] font-bold text-slate-700 bg-[#F8FAFC] px-2 py-0.5 rounded border border-[#E2E8F0]">
                  {comm.memberCount} Entities
                </span>
              </div>

              {/* Metrics Table */}
              <div className="space-y-1.5 font-mono text-[11px] text-slate-400 border-t border-b border-[#E2E8F0]/80 py-2">
                <div className="flex items-center justify-between">
                  <span>Cluster Density:</span>
                  <strong className="text-slate-800">{comm.density}</strong>
                </div>
                <div className="flex items-center justify-between">
                  <span>Internal Linkages:</span>
                  <strong className="text-slate-800">{comm.internalEdgeCount} Edges</strong>
                </div>
                <div className="flex items-center justify-between">
                  <span>Average Risk:</span>
                  <strong
                    className={cn(
                      comm.avgRisk >= 85 ? "text-red-400" : "text-amber-400"
                    )}
                  >
                    {comm.avgRisk}/100
                  </strong>
                </div>
                <div className="flex items-center justify-between">
                  <span>Top Influencer:</span>
                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectEntity(comm.topInfluencer.id);
                    }}
                    className="text-emerald-300 font-bold hover:underline cursor-pointer truncate max-w-[150px]"
                  >
                    {comm.topInfluencer.name}
                  </span>
                </div>
              </div>

              {/* Bridge Nodes Footer */}
              <div>
                <span className="text-[9px] font-mono uppercase tracking-wider text-amber-400 font-bold block mb-1">
                  Inter-Community Bridge Nodes ({comm.bridgeNodes.length}):
                </span>
                {comm.bridgeNodes.length === 0 ? (
                  <span className="text-[10px] font-mono text-slate-500">Isolated cluster (0 external bridges)</span>
                ) : (
                  <div className="flex flex-wrap gap-1">
                    {comm.bridgeNodes.map((b) => (
                      <button
                        key={b.entityId}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectEntity(b.entityId);
                        }}
                        className="rounded bg-amber-950/40 border border-amber-800/60 px-1.5 py-0.5 text-[9px] font-mono text-amber-300 hover:border-amber-400 transition-colors cursor-pointer"
                        title={`${b.externalLinksCount} external links to other syndicates`}
                      >
                        {b.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
