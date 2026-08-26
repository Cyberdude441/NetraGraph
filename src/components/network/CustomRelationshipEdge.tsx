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

    // 1. Determine Edge Stroke & Dash Pattern based on investigation specs:
    // COMMUNICATION: Solid Cyan / Blue
    // FINANCIAL_TRANSFER: Animated Amber / Gold with glowing underlay
    // LOCATION_OVERLAP: Dotted Slate Grey
    // OWNERSHIP: Emerald Solid
    // EVENT_PARTICIPATION: Rose
    // ASSOCIATION: Subtle Lavender / Grey
    let strokeColor = "#475569";
    let strokeWidth = 1.4;
    let strokeDasharray: string | undefined = undefined;
    let isAnimated = false;
    let labelBadge = "border-slate-700/60 bg-[#141A21] text-slate-300";

    if (relType.includes("COMMUNICATION") || relType === "CALL" || relType === "CALLS") {
      strokeColor = "#38BDF8"; // Cyan / Blue
      strokeWidth = 1.8;
      strokeDasharray = undefined;
      labelBadge = "border-sky-500/40 bg-[#0C2133] text-sky-300";
    } else if (
      relType.includes("FINANCIAL") ||
      relType.includes("MONEY") ||
      relType.includes("TRANSFER")
    ) {
      strokeColor = "#F59E0B"; // Dark Amber / Gold
      strokeWidth = 2.2;
      strokeDasharray = "6 4";
      isAnimated = true;
      labelBadge = "border-amber-500/50 bg-[#291B08] text-amber-300";
    } else if (relType.includes("LOCATION") || relType === "LOCATED_AT") {
      strokeColor = "#94A3B8"; // Dotted Grey
      strokeWidth = 1.4;
      strokeDasharray = "2 3";
      labelBadge = "border-slate-600/40 bg-[#161D24] text-slate-300";
    } else if (relType.includes("OWNERSHIP")) {
      strokeColor = "#10B981"; // Emerald
      strokeWidth = 1.6;
      strokeDasharray = undefined;
      labelBadge = "border-emerald-500/40 bg-[#06291C] text-emerald-300";
    } else if (relType.includes("EVENT")) {
      strokeColor = "#F43F5E"; // Rose
      strokeWidth = 1.8;
      strokeDasharray = "4 4";
      labelBadge = "border-rose-500/40 bg-[#2A0F15] text-rose-300";
    } else {
      // ASSOCIATION / default
      strokeColor = "#A855F7"; // Purple
      strokeWidth = 1.2;
      strokeDasharray = "4 2";
      labelBadge = "border-purple-700/40 bg-[#191024] text-purple-300";
    }

    if (edgeData.isHighlighted) {
      strokeWidth += 1.5;
      strokeColor = "#38BDF8";
    }

    return (
      <>
        {/* Shadow / Glow line for animated transfers or highlighted links */}
        {(isAnimated || edgeData.isHighlighted) && (
          <path
            d={edgePath}
            fill="none"
            stroke={strokeColor}
            strokeWidth={strokeWidth + 4}
            strokeOpacity={0.2}
            className="animate-pulse"
          />
        )}

        <BaseEdge
          id={id}
          path={edgePath}
          markerEnd={markerEnd}
          style={{
            stroke: strokeColor,
            strokeWidth,
            strokeDasharray,
            opacity: edgeData.isDimmed ? 0.15 : 0.9,
            transition: "all 0.2s ease",
            animation: isAnimated ? "dashdraw 1.2s linear infinite" : undefined,
          }}
        />

        {edgeData.label && (
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
                  "flex items-center gap-1 rounded border px-1.5 py-0.5 text-[9px] font-mono font-medium shadow-md transition-opacity cursor-pointer hover:border-slate-400",
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
