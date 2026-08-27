import React, { useState } from "react";
import {
  Share2,
  GitFork,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  Clock,
  PhoneCall,
  CreditCard,
  Building2,
  Cpu,
  User,
  MapPin,
  Flame,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { SyntheticEntity, SyntheticRelationship } from "@/data/syntheticGraphData";
import { findShortestPath, type ShortestPathResult } from "@/utils/shortestPath";

interface ShortestPathTracerProps {
  entities: SyntheticEntity[];
  relationships: SyntheticRelationship[];
  onSelectEntity: (id: string) => void;
}

export function ShortestPathTracer({
  entities,
  relationships,
  onSelectEntity,
}: ShortestPathTracerProps) {
  const [sourceId, setSourceId] = useState<string>("ENT-P-01"); // Vikramaditya Rawat
  const [targetId, setTargetId] = useState<string>("ENT-P-06"); // Arjun Menon
  const [activePathIndex, setActivePathIndex] = useState<number>(0);

  const { primaryPath, alternativePaths } = findShortestPath(
    sourceId,
    targetId,
    entities,
    relationships
  );

  const allPaths: ShortestPathResult[] = primaryPath
    ? [primaryPath, ...alternativePaths]
    : [];

  const currentPath = allPaths[activePathIndex] || primaryPath;

  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-[#E2E8F0] pb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Share2 className="size-4 text-amber-400" />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-900">
              Forensic Shortest Path & Intermediary Conduit Tracer
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              Uncovers multi-hop intermediary bridges, mule hops, and communication conduits between two targets.
            </p>
          </div>
        </div>

        {currentPath && (
          <span className="rounded bg-amber-950/40 border border-amber-800/60 px-2.5 py-1 text-xs font-mono font-bold text-amber-300">
            {currentPath.hopCount} Hops · {currentPath.pathConfidence}% Path Confidence
          </span>
        )}
      </div>

      {/* Target Selectors */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-white p-3 rounded-lg border border-[#E2E8F0]">
        <div>
          <label className="text-[10px] font-mono uppercase font-bold text-emerald-400 block mb-1">
            Source Origin Target (Entity A):
          </label>
          <select
            value={sourceId}
            onChange={(e) => {
              setSourceId(e.target.value);
              setActivePathIndex(0);
            }}
            className="w-full rounded border border-[#E2E8F0] bg-[#F8FAFC] px-2.5 py-1.5 text-xs text-slate-900 font-mono outline-none focus:border-emerald-500 cursor-pointer"
          >
            {entities.map((e) => (
              <option key={e.id} value={e.id}>
                {e.name} ({e.label} · {e.id})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-[10px] font-mono uppercase font-bold text-amber-400 block mb-1">
            Destination Suspect (Entity B):
          </label>
          <select
            value={targetId}
            onChange={(e) => {
              setTargetId(e.target.value);
              setActivePathIndex(0);
            }}
            className="w-full rounded border border-[#E2E8F0] bg-[#F8FAFC] px-2.5 py-1.5 text-xs text-slate-900 font-mono outline-none focus:border-amber-500 cursor-pointer"
          >
            {entities.map((e) => (
              <option key={e.id} value={e.id}>
                {e.name} ({e.label} · {e.id})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Path Alternatives Toggle */}
      {allPaths.length > 1 && (
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-slate-500 text-[10px] uppercase font-bold">
            Discovered Routes:
          </span>
          <div className="flex items-center gap-1 rounded bg-[#F8FAFC] p-0.5 border border-[#E2E8F0]">
            {allPaths.map((p, idx) => (
              <button
                key={idx}
                onClick={() => setActivePathIndex(idx)}
                className={cn(
                  "rounded px-2.5 py-0.5 text-[10px] font-bold transition-all cursor-pointer",
                  activePathIndex === idx
                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/50"
                    : "text-slate-400 hover:text-slate-800"
                )}
              >
                Route #{idx + 1} ({p.hopCount} Hops)
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Path Visualizer Stream */}
      {currentPath ? (
        <div className="space-y-4">
          {/* Explanation Banner */}
          <div className="rounded border border-amber-900/40 bg-amber-950/20 p-3 text-[11px] font-mono text-amber-200 leading-relaxed">
            <span className="font-bold text-amber-300">Conduit Pathway Analysis: </span>
            {currentPath.explanation}
          </div>

          {/* Hop Nodes Chain */}
          <div className="space-y-3 relative pl-6 before:absolute before:left-2.5 before:top-4 before:bottom-4 before:w-0.5 before:bg-slate-100">
            {currentPath.pathNodes.map((node, nIdx) => {
              const isFirst = nIdx === 0;
              const isLast = nIdx === currentPath.pathNodes.length - 1;
              const nextEdge = currentPath.pathEdges[nIdx];

              return (
                <div key={node.id} className="relative group">
                  {/* Step Bullet */}
                  <div
                    className={cn(
                      "absolute -left-6 top-2 flex size-5 items-center justify-center rounded-full border shadow-sm font-mono text-[9px] font-bold",
                      isFirst
                        ? "border-emerald-500 bg-emerald-950 text-emerald-300 ring-2 ring-emerald-500/40"
                        : isLast
                        ? "border-amber-500 bg-amber-950 text-amber-300 ring-2 ring-amber-500/40"
                        : "border-purple-500 bg-purple-950 text-purple-300"
                    )}
                  >
                    {nIdx + 1}
                  </div>

                  {/* Node Card */}
                  <div
                    onClick={() => onSelectEntity(node.id)}
                    className="rounded-lg border border-[#E2E8F0] bg-white p-3 hover:border-emerald-500 transition-all cursor-pointer flex items-center justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <strong className="font-bold text-slate-900 text-xs">
                          {node.name}
                        </strong>
                        <span className="rounded bg-[#F8FAFC] px-1.5 py-0.2 font-mono text-[9px] text-slate-400 border border-[#E2E8F0]">
                          {node.label}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400 block mt-0.5">
                        {node.role || node.metadata.jurisdiction || node.id}
                      </span>
                    </div>

                    <span
                      className={cn(
                        "rounded px-2 py-0.5 font-mono text-[9px] font-bold",
                        node.riskScore >= 85
                          ? "bg-red-950/60 text-red-300 border border-red-500/50"
                          : "bg-slate-100 text-slate-700"
                      )}
                    >
                      Risk {node.riskScore}
                    </span>
                  </div>

                  {/* Relationship Link Badge Between Nodes */}
                  {nextEdge && (
                    <div className="my-1.5 ml-4 flex items-center gap-2 text-[10px] font-mono text-slate-400">
                      <ArrowRight className="size-3 text-amber-400 shrink-0" />
                      <span className="rounded bg-[#F8FAFC] px-2 py-0.5 text-amber-300 border border-[#E2E8F0] font-bold">
                        {nextEdge.label}
                      </span>
                      <span className="text-slate-500 truncate">
                        {nextEdge.detail || nextEdge.type}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="rounded border border-dashed border-[#E2E8F0] p-8 text-center text-slate-500 font-mono text-xs">
          No relationship pathway found between selected entities within 4 hops.
        </div>
      )}
    </div>
  );
}
