import React, { memo } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface RelationshipEdgeData {
  type?: string;
  label?: string;
  weight?: number;
  detail?: string;
  confidence?: number;
  isHighlighted?: boolean;
  isDimmed?: boolean;
  isAnimated?: boolean;
}

export const CustomRelationshipEdge = memo(
  ({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    data,
    markerEnd,
  }: EdgeProps) => {
    const [edgePath, labelX, labelY] = getBezierPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
    });

    const edgeData = (data || {}) as RelationshipEdgeData;
    const relType = (edgeData.type || "ASSOCIATION").toUpperCase();

    // Restrained dark SOC intelligence palette
    let strokeColor = "#475569";
    let strokeWidth = 1.5;
    let strokeDasharray: string | undefined = undefined;
    let labelBadge = "border-[#334155] bg-[#0f172a]/95 text-slate-300 shadow-sm";

    if (relType.includes("COMMUNICATION") || relType === "CALL" || relType === "CALLS") {
      strokeColor = "#14B8A6"; // Teal
      strokeWidth = 1.6;
      labelBadge = "border-teal-800/80 bg-[#0f172a]/95 text-teal-300";
    } else if (
      relType.includes("FINANCIAL") ||
      relType.includes("MONEY") ||
      relType.includes("TRANSFER")
    ) {
      strokeColor = "#F59E0B"; // Amber
      strokeWidth = 1.8;
      strokeDasharray = "5 3";
      labelBadge = "border-amber-800/80 bg-[#0f172a]/95 text-amber-300";
    } else if (relType.includes("COMMAND") || relType.includes("C2") || relType.includes("MALWARE")) {
      strokeColor = "#EF4444"; // Red
      strokeWidth = 1.8;
      labelBadge = "border-red-800/80 bg-[#0f172a]/95 text-red-300";
    } else if (relType.includes("OWNERSHIP") || relType.includes("BENEFICIAL")) {
      strokeColor = "#06B6D4"; // Cyan
      strokeWidth = 1.6;
      labelBadge = "border-cyan-800/80 bg-[#0f172a]/95 text-cyan-300";
    }

    if (edgeData.isHighlighted) {
      strokeWidth += 1.5;
      strokeColor = "#06B6D4";
      labelBadge = "border-cyan-400 bg-cyan-950 text-cyan-200 font-bold shadow-[0_0_10px_rgba(6,182,212,0.35)]";
    }

    return (
      <>
        <BaseEdge
          id={id}
          path={edgePath}
          markerEnd={markerEnd}
          style={{
            stroke: strokeColor,
            strokeWidth,
            strokeDasharray,
            opacity: edgeData.isDimmed ? 0.15 : 0.85,
            transition: "all 0.2s ease",
          }}
        />

        {edgeData.label && !edgeData.isDimmed && (
          <EdgeLabelRenderer>
            <div
              style={{
                position: "absolute",
                transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
                pointerEvents: "all",
                opacity: edgeData.isDimmed ? 0.1 : 1,
              }}
              className="nodrag nopan"
            >
              <div
                className={cn(
                  "flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-mono tracking-tight transition-opacity cursor-pointer backdrop-blur-md select-none",
                  labelBadge
                )}
                title={edgeData.detail || edgeData.label}
              >
                <span>{edgeData.label}</span>
              </div>
            </div>
          </EdgeLabelRenderer>
        )}
      </>
    );
  }
);
