import React, { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import {
  User,
  Building2,
  MapPin,
  CreditCard,
  Smartphone,
  ShieldAlert,
  Flame,
  Car,
  CalendarDays,
  Cpu,
  Globe2,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface IntelligenceNodeEntity {
  id: string;
  label: string;
  name: string;
  communityId?: number;
  riskScore?: number;
  confidenceScore?: number;
  caseId?: string;
  investigationGroup?: string;
  role?: string;
  status?: string;
  influenceScore?: number;
  firstSeen?: string;
  lastSeen?: string;
  metadata?: {
    category?: string;
    description?: string;
    alias?: string[];
    jurisdiction?: string;
    financialLossINR?: number;
    phoneImei?: string;
    accountNumber?: string;
    tags?: string[];
  };
}

export interface EntityNodeData {
  entity: IntelligenceNodeEntity;
  isHighlighted?: boolean;
  isDimmed?: boolean;
  isRoot?: boolean;
  isCentralFocus?: boolean;
  hopDistance?: number;
  influenceSizeFactor?: number;
}

export const CustomEntityNode = memo(({ data, selected }: NodeProps) => {
  const nodeData = (data || {}) as EntityNodeData;
  const entity = nodeData.entity || ({} as IntelligenceNodeEntity);
  const label = entity.label || "Person";
  const risk = entity.riskScore ?? 70;
  const isHighRisk = risk >= 85;
  const isCentral = nodeData.isCentralFocus || nodeData.isRoot;

  // Classification colors keep entity types distinct.
  let colorBadge = "bg-emerald-50 text-[#16A34A] border-emerald-200";
  let iconBgClass = "bg-emerald-100 text-[#16A34A]";
  let borderClass = "border-[#16A34A]";

  if (label === "Person") {
    colorBadge = "bg-emerald-50 text-[#16A34A] border-emerald-200";
    iconBgClass = "bg-emerald-100 text-[#16A34A]";
    borderClass = isHighRisk ? "border-[#DC2626] border-2" : "border-[#16A34A]";
  } else if (label === "Organization") {
    colorBadge = "bg-emerald-50 text-[#047857] border-emerald-200";
    iconBgClass = "bg-emerald-100 text-[#047857]";
    borderClass = "border-[#047857]";
  } else if (label === "Location") {
    colorBadge = "bg-orange-50 text-[#EA580C] border-orange-200";
    iconBgClass = "bg-orange-100 text-[#EA580C]";
    borderClass = "border-[#EA580C]";
  } else if (label === "Vehicle") {
    colorBadge = "bg-purple-50 text-[#9333EA] border-purple-200";
    iconBgClass = "bg-purple-100 text-[#9333EA]";
    borderClass = "border-[#9333EA]";
  } else if (label === "BankAccount" || label === "Financial" || label === "Bank") {
    colorBadge = "bg-amber-50 text-[#CA8A04] border-amber-200";
    iconBgClass = "bg-amber-100 text-[#CA8A04]";
    borderClass = "border-[#CA8A04]";
  } else {
    colorBadge = "bg-slate-50 text-[#64748B] border-slate-200";
    iconBgClass = "bg-slate-100 text-[#64748B]";
    borderClass = "border-[#94A3B8]";
  }

  const typeConfig: Record<
    string,
    {
      icon: React.ElementType;
      badgeText: string;
    }
  > = {
    Person: {
      icon: User,
      badgeText: "Person",
    },
    Phone: {
      icon: Smartphone,
      badgeText: "Phone",
    },
    BankAccount: {
      icon: CreditCard,
      badgeText: "Bank Account",
    },
    Financial: {
      icon: CreditCard,
      badgeText: "Financial",
    },
    Location: {
      icon: MapPin,
      badgeText: "Location",
    },
    Organization: {
      icon: Building2,
      badgeText: "Organization",
    },
    Device: {
      icon: Cpu,
      badgeText: "Device",
    },
    Vehicle: {
      icon: Car,
      badgeText: "Vehicle",
    },
    Event: {
      icon: CalendarDays,
      badgeText: "Event",
    },
    State: {
      icon: Globe2,
      badgeText: "State",
    },
    CrimeCategory: {
      icon: ShieldAlert,
      badgeText: "Crime Category",
    },
  };

  const cfg = typeConfig[label] || typeConfig["Person"];
  const Icon = cfg.icon;

  const nodeWidth = 210;

  return (
    <div
      className={cn(
        "group relative flex items-center gap-2.5 rounded-md px-3.5 py-2.5 text-[#0F172A] transition-all duration-200 cursor-pointer select-none",
        "bg-white border shadow-sm",
        borderClass,
        isCentral && "ring-2 ring-[#065F46] scale-105 shadow-md",
        nodeData.isDimmed && "opacity-25 grayscale",
        nodeData.isHighlighted && !isCentral && "ring-2 ring-emerald-400",
        selected && "ring-2 ring-[#065F46]"
      )}
      style={{
        width: nodeWidth,
      }}
    >
      {/* React Flow Handles */}
      <Handle type="target" position={Position.Top} className="!size-2 !bg-[#64748B] !border-white" />
      <Handle type="source" position={Position.Bottom} className="!size-2 !bg-[#64748B] !border-white" />
      <Handle type="target" position={Position.Left} className="!size-2 !bg-[#64748B] !border-white" />
      <Handle type="source" position={Position.Right} className="!size-2 !bg-[#64748B] !border-white" />

      {/* Entity Icon Container */}
      <div
        className={cn(
          "flex size-8 shrink-0 items-center justify-center rounded-md border border-[#D9E2EC]",
          iconBgClass
        )}
      >
        <Icon className="size-4" />
      </div>

      {/* Primary Details */}
      <div className="min-w-0 flex-1">
        <h4 className="font-sans text-xs font-bold text-[#0F172A] truncate" title={entity.name}>
          {entity.name}
        </h4>
        <span className="text-xs text-[#64748B] truncate block">
          {entity.role || entity.status || cfg.badgeText}
        </span>
      </div>

      {/* Risk Indicator Meter */}
      <div className="shrink-0 flex items-center gap-1">
        <span
          className={cn(
            "flex items-center gap-0.5 rounded-md px-2 py-0.5 text-xs font-bold",
            isHighRisk
              ? "bg-red-50 text-[#DC3545] border border-red-200"
              : risk >= 70
              ? "bg-amber-50 text-[#F59E0B] border border-amber-200"
              : "bg-slate-100 text-[#475569] border border-slate-200"
          )}
        >
          {risk}
        </span>
      </div>
    </div>
  );
});
