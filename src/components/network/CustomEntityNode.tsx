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

  const typeConfig: Record<
    string,
    {
      icon: React.ElementType;
      iconColor: string;
      cardBorder: string;
      glowColor: string;
      badgeText: string;
    }
  > = {
    Person: {
      icon: User,
      iconColor: "text-sky-400",
      cardBorder: "border-sky-800/60 hover:border-sky-500",
      glowColor: "rgba(56, 189, 248, 0.4)",
      badgeText: "Person",
    },
    Phone: {
      icon: Smartphone,
      iconColor: "text-emerald-400",
      cardBorder: "border-emerald-800/60 hover:border-emerald-500",
      glowColor: "rgba(16, 185, 129, 0.4)",
      badgeText: "Phone / Burner",
    },
    BankAccount: {
      icon: CreditCard,
      iconColor: "text-amber-400",
      cardBorder: "border-amber-800/60 hover:border-amber-500",
      glowColor: "rgba(245, 158, 11, 0.4)",
      badgeText: "Bank Account",
    },
    Financial: {
      icon: CreditCard,
      iconColor: "text-amber-400",
      cardBorder: "border-amber-800/60 hover:border-amber-500",
      glowColor: "rgba(245, 158, 11, 0.4)",
      badgeText: "Financial",
    },
    Location: {
      icon: MapPin,
      iconColor: "text-slate-300",
      cardBorder: "border-slate-700/70 hover:border-slate-400",
      glowColor: "rgba(148, 163, 184, 0.35)",
      badgeText: "Location",
    },
    Organization: {
      icon: Building2,
      iconColor: "text-purple-400",
      cardBorder: "border-purple-800/60 hover:border-purple-500",
      glowColor: "rgba(168, 85, 247, 0.4)",
      badgeText: "Organization",
    },
    Device: {
      icon: Cpu,
      iconColor: "text-cyan-400",
      cardBorder: "border-cyan-800/60 hover:border-cyan-500",
      glowColor: "rgba(6, 182, 212, 0.4)",
      badgeText: "Device / C2",
    },
    Vehicle: {
      icon: Car,
      iconColor: "text-orange-400",
      cardBorder: "border-orange-800/60 hover:border-orange-500",
      glowColor: "rgba(249, 115, 22, 0.35)",
      badgeText: "Vehicle",
    },
    Event: {
      icon: CalendarDays,
      iconColor: "text-rose-400",
      cardBorder: "border-rose-800/60 hover:border-rose-500",
      glowColor: "rgba(244, 63, 94, 0.4)",
      badgeText: "Event Incident",
    },
    State: {
      icon: Globe2,
      iconColor: "text-emerald-400",
      cardBorder: "border-emerald-800/60 hover:border-emerald-500",
      glowColor: "rgba(16, 185, 129, 0.35)",
      badgeText: "State",
    },
    CrimeCategory: {
      icon: ShieldAlert,
      iconColor: "text-teal-400",
      cardBorder: "border-teal-800/60 hover:border-teal-500",
      glowColor: "rgba(20, 184, 166, 0.35)",
      badgeText: "Crime Category",
    },
  };

  const cfg = typeConfig[label] || typeConfig["Person"];
  const Icon = cfg.icon;

  const nodeWidth = 200;

  return (
    <div
      className={cn(
        "group relative flex items-center gap-2.5 rounded-lg px-3 py-2 text-slate-200 transition-all duration-200 cursor-pointer select-none",
        "bg-[#11161B]/95 backdrop-blur-md border shadow-xl",
        cfg.cardBorder,
        isCentral && "ring-2 ring-sky-400 bg-[#16212B] scale-105",
        nodeData.isDimmed && "opacity-20 grayscale",
        nodeData.isHighlighted && !isCentral && "ring-1 ring-sky-400/80"
      )}
      style={{
        width: nodeWidth,
        boxShadow: isCentral
          ? `0 0 24px ${cfg.glowColor}, 0 8px 30px rgba(0, 0, 0, 0.9)`
          : selected
          ? `0 0 16px ${cfg.glowColor}, 0 4px 20px rgba(0, 0, 0, 0.7)`
          : "0 4px 16px rgba(0, 0, 0, 0.6)",
      }}
    >
      {/* React Flow Handles */}
      <Handle type="target" position={Position.Top} className="!size-1.5 !bg-slate-500 !border-none" />
      <Handle type="source" position={Position.Bottom} className="!size-1.5 !bg-slate-500 !border-none" />
      <Handle type="target" position={Position.Left} className="!size-1.5 !bg-slate-500 !border-none" />
      <Handle type="source" position={Position.Right} className="!size-1.5 !bg-slate-500 !border-none" />

      {/* Entity Icon Container */}
      <div
        className={cn(
          "flex size-7 shrink-0 items-center justify-center rounded border border-slate-800 bg-[#182028]",
          cfg.iconColor
        )}
      >
        <Icon className="size-3.5" />
      </div>

      {/* Primary Details */}
      <div className="min-w-0 flex-1">
        <h4 className="font-sans text-xs font-semibold text-slate-100 truncate" title={entity.name}>
          {entity.name}
        </h4>
        <span className="text-[9px] font-mono text-slate-400 truncate block">
          {entity.role || entity.status || cfg.badgeText}
        </span>
      </div>

      {/* Risk Indicator Meter */}
      <div className="shrink-0 flex items-center gap-1">
        <span
          className={cn(
            "flex items-center gap-0.5 rounded px-1.5 py-0.5 font-mono text-[9px] font-bold",
            isHighRisk
              ? "bg-[#7F1D1D] text-red-200 border border-red-500/60"
              : risk >= 70
              ? "bg-[#78350F] text-amber-200 border border-amber-500/50"
              : "bg-[#1E293B] text-slate-400 border border-slate-700"
          )}
        >
          {isHighRisk && <Flame className="size-2 text-red-400 animate-pulse" />}
          {risk}
        </span>
      </div>
    </div>
  );
});
