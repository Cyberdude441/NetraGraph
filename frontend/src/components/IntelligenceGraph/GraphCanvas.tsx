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

        let markerColor = "#94A3B8";
        if (isMoney) markerColor = "#F59E0B";
        else if (rel.type === "COMMUNICATION") markerColor = "#047857";
        else if (rel.type === "OWNERSHIP") markerColor = "#198754";
        else if (rel.type === "EVENT_PARTICIPATION") markerColor = "#DC3545";
        else if (rel.type === "ASSOCIATION") markerColor = "#065F46";

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
    <div className="flex-1 h-full bg-white relative">
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
        <Background color="#E2E8F0" gap={32} size={1} />
        <Controls className="!bg-white !border-[#E2E8F0] !text-[#0F172A] !rounded-md !shadow-xs" />
        <MiniMap
          nodeColor={(n: any) => {
            const l = n.data?.entity?.label;
            if (l === "Person") return "#16A34A";
            if (l === "BankAccount" || l === "Financial") return "#CA8A04";
            if (l === "Location") return "#EA580C";
            if (l === "Vehicle") return "#9333EA";
            if (l === "Organization") return "#047857";
            return "#64748B";
          }}
          maskColor="rgba(248, 250, 252, 0.75)"
          className="!bg-white !border !border-[#E2E8F0] !rounded-md !opacity-85 hover:!opacity-100 transition-opacity"
        />
      </ReactFlow>
    </div>
  );
}
