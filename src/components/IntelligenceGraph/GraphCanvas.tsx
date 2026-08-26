import React, { useMemo } from "react";
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
  type ReactFlowInstance,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  CustomEntityNode,
  type EntityNodeData,
  type IntelligenceNodeEntity,
} from "@/components/network/CustomEntityNode";
import {
  CustomRelationshipEdge,
  type RelationshipEdgeData,
} from "@/components/network/CustomRelationshipEdge";
import type { SyntheticEntity, SyntheticRelationship } from "@/data/syntheticGraphData";
import type { LayoutPosition } from "@/utils/graphAlgorithms";

const nodeTypes = {
  entityNode: CustomEntityNode,
};

const edgeTypes = {
  relationshipEdge: CustomRelationshipEdge,
};

interface GraphCanvasProps {
  entities: SyntheticEntity[];
  relationships: SyntheticRelationship[];
  positions: Record<string, LayoutPosition>;
  focalNodeId: string;
  hopReachableIds: Set<string> | null;
  hopEdgeIds: Set<string> | null;
  onNodeClick: (entityId: string) => void;
  onInit?: (instance: ReactFlowInstance) => void;
}

export function GraphCanvas({
  entities,
  relationships,
  positions,
  focalNodeId,
  hopReachableIds,
  hopEdgeIds,
  onNodeClick,
  onInit,
}: GraphCanvasProps) {
  // Map Entities to ReactFlow Nodes
  const nodes: Node[] = useMemo(() => {
    return entities.map((entity) => {
      const isFocal = focalNodeId === entity.id;
      const isReachable = hopReachableIds ? hopReachableIds.has(entity.id) : true;
      const isDimmed = hopReachableIds ? !isReachable : false;
      const isHighlighted = isFocal || (hopReachableIds ? isReachable : false);

      const pos = positions[entity.id] || { x: 500, y: 300 };

      return {
        id: entity.id,
        type: "entityNode",
        position: pos,
        data: {
          entity: entity as unknown as IntelligenceNodeEntity,
          isHighlighted,
          isDimmed,
          isRoot: isFocal,
          isCentralFocus: isFocal,
        } as EntityNodeData,
        selected: isFocal,
      };
    });
  }, [entities, positions, focalNodeId, hopReachableIds]);

  // Map Relationships to ReactFlow Edges
  const edges: Edge[] = useMemo(() => {
    const validNodeIds = new Set(entities.map((e) => e.id));

    return relationships
      .filter((rel) => validNodeIds.has(rel.sourceId) && validNodeIds.has(rel.targetId))
      .map((rel) => {
        const isFocalDirect =
          rel.sourceId === focalNodeId || rel.targetId === focalNodeId;
        const isHopEdge = hopEdgeIds ? hopEdgeIds.has(rel.id) : true;
        const isDimmed = hopEdgeIds ? !isHopEdge : false;
        const isHighlighted = isFocalDirect || (hopEdgeIds ? isHopEdge : false);

        const isMoney =
          rel.type === "FINANCIAL_TRANSFER" ||
          rel.type.includes("MONEY") ||
          rel.type.includes("FINANCIAL");

        let markerColor = "#64748B";
        if (isMoney) markerColor = "#F59E0B";
        else if (rel.type === "COMMUNICATION") markerColor = "#38BDF8";
        else if (rel.type === "OWNERSHIP") markerColor = "#10B981";
        else if (rel.type === "EVENT_PARTICIPATION") markerColor = "#F43F5E";
        else if (rel.type === "ASSOCIATION") markerColor = "#A855F7";

        return {
          id: rel.id,
          source: rel.sourceId,
          target: rel.targetId,
          type: "relationshipEdge",
          data: {
            type: rel.type,
            label: rel.label,
            detail: rel.detail,
            isHighlighted,
            isDimmed,
            isAnimated: isMoney,
          } as RelationshipEdgeData,
          animated: isMoney,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 14,
            height: 14,
            color: markerColor,
          },
        };
      });
  }, [relationships, entities, focalNodeId, hopEdgeIds]);

  return (
    <div className="flex-1 h-full bg-[#0B0F14] relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodeClick={(_, node) => onNodeClick(node.id)}
        onInit={onInit}
        fitView
        minZoom={0.15}
        maxZoom={2.4}
        defaultEdgeOptions={{ type: "relationshipEdge" }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#1E293B" gap={28} size={1} />
        <Controls className="!bg-[#11161B] !border-slate-800 !text-slate-300 !rounded !shadow-2xl" />
        <MiniMap
          nodeColor={(n: any) => {
            const l = n.data?.entity?.label;
            if (l === "Person") return "#0284C7";
            if (l === "BankAccount") return "#D97706";
            if (l === "Phone") return "#10B981";
            if (l === "Location") return "#94A3B8";
            if (l === "Organization") return "#A855F7";
            if (l === "Device") return "#06B6D4";
            if (l === "Event") return "#F43F5E";
            return "#64748B";
          }}
          maskColor="rgba(11, 15, 20, 0.85)"
          className="!bg-[#0E1318] !border !border-slate-800 !rounded"
        />
      </ReactFlow>
    </div>
  );
}
