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

    // 1. Determine edge stroke and dash pattern based on investigation specs.
    // COMMUNICATION: Solid green
    // FINANCIAL_TRANSFER: Animated Amber / Gold
    // LOCATION_OVERLAP: Dotted Slate Grey
    // OWNERSHIP: Emerald Solid
    // EVENT_PARTICIPATION: Rose
    // ASSOCIATION: Subtle Lavender / Grey
    // Light grey lines with clean white badges for readability
    let strokeColor = "#94A3B8";
    let strokeWidth = 1.5;
    let strokeDasharray: string | undefined = undefined;
    let isAnimated = false;
    let labelBadge = "border-[#CBD5E1] bg-white text-[#CBD5E1] shadow-xs";

    if (relType.includes("COMMUNICATION") || relType === "CALL" || relType === "CALLS") {
      strokeColor = "#047857"; // Government green
      strokeWidth = 1.6;
      strokeDasharray = undefined;
      labelBadge = "border-emerald-200 bg-emerald-50 text-[#065F46]";
    } else if (
      relType.includes("FINANCIAL") ||
      relType.includes("MONEY") ||
      relType.includes("TRANSFER")
    ) {
      strokeColor = "#F59E0B"; // Amber / Gold
      strokeWidth = 1.8;
      strokeDasharray = "5 3";
      labelBadge = "border-amber-200 bg-amber-50 text-[#92400E]";
    } else if (relType.includes("LOCATION") || relType === "LOCATED_AT") {
      strokeColor = "#94A3B8"; // Dotted Grey
      strokeWidth = 1.4;
      strokeDasharray = "2 3";
      labelBadge = "border-[#CBD5E1] bg-[#F8FAFC] text-[#475569]";
    } else if (relType.includes("OWNERSHIP")) {
      strokeColor = "#198754"; // Emerald
      strokeWidth = 1.6;
      strokeDasharray = undefined;
      labelBadge = "border-emerald-200 bg-emerald-50 text-[#198754]";
    }

    if (edgeData.isHighlighted) {
      strokeWidth += 1.5;
      strokeColor = "#065F46";
      labelBadge = "border-[#065F46] bg-emerald-50 text-[#065F46] font-bold";
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
            opacity: edgeData.isDimmed ? 0.2 : 0.85,
            transition: "all 0.2s ease",
          }}
        />

        {edgeData.label && (
          <EdgeLabelRenderer>
            <div
              style={{
                position: "absolute",
                transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
                pointerEvents: "all",
                opacity: edgeData.isDimmed ? 0.15 : 1,
              }}
              className="nodrag nopan"
            >
              <div
                className={cn(
                  "flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-semibold shadow-xs transition-opacity cursor-pointer",
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
