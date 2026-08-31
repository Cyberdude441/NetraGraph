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

  // Map Relationships to ReactFlow Edges with Dark SOC styling
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

        let markerColor = isHighlighted ? "#06B6D4" : "#475569";
        if (isMoney) markerColor = "#F59E0B";
        else if (rel.type === "COMMUNICATION" || rel.type.includes("CALL")) markerColor = "#14B8A6";
        else if (rel.type === "COMMAND_CONTROL" || rel.type.includes("EXPLOIT")) markerColor = "#EF4444";
        else if (rel.type === "STATUTORY_OFFENSE" || rel.type === "BENEFICIAL_OWNER") markerColor = "#06B6D4";

        return {
          id: rel.id,
          source: rel.sourceId,
          target: rel.targetId,
          type: "relationshipEdge",
          data: {
            type: rel.type,
            label: rel.label || rel.type,
            detail: rel.detail,
            isHighlighted,
            isDimmed,
            isAnimated: isMoney || isHighlighted,
          } as RelationshipEdgeData,
          animated: isMoney || isHighlighted,
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
    <div className="flex-1 h-full bg-[#0a0e17] relative overflow-hidden">
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
        <Background color="#1e293b" gap={28} size={1} />
        <Controls className="!bg-[#0f172a] !border-[#334155] !text-[#94a3b8] !rounded-md !shadow-lg" />
        <MiniMap
          nodeColor={(n: any) => {
            const l = n.data?.entity?.label;
            const r = n.data?.entity?.riskScore || 50;
            if (r >= 85) return "#EF4444";
            if (r >= 70) return "#F59E0B";
            if (l === "Person") return "#14B8A6";
            if (l === "BankAccount" || l === "Financial") return "#F59E0B";
            if (l === "State" || l === "CrimeCategory") return "#06B6D4";
            if (l === "Device" || l === "IP") return "#818CF8";
            return "#64748B";
          }}
          maskColor="rgba(10, 14, 23, 0.85)"
          className="!bg-[#0f172a] !border !border-[#334155] !rounded-md !opacity-90 hover:!opacity-100 transition-opacity"
        />
      </ReactFlow>
    </div>
  );
}
