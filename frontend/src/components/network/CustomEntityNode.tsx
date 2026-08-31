import React, { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import {
  User,
  Building2,
  MapPin,
  CreditCard,
  Smartphone,
  ShieldAlert,
  Car,
  CalendarDays,
  Cpu,
  Globe2,
  FileCode2,
  FileCheck2,
  Binary,
  AtSign,
  Globe,
  Radio,
  Network,
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
  sourceDocument?: string;
  metadata?: {
    category?: string;
    description?: string;
    jurisdiction?: string;
    statutorySection?: string;
    ipAddress?: string;
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
  const risk = entity.riskScore ?? 50;
  const isHighRisk = risk >= 85;
  const isCentral = nodeData.isCentralFocus || nodeData.isRoot;

  // Dark SOC theme palette
  let iconBgClass = "bg-cyan-950/80 text-cyan-400 border-cyan-800/60";
  let borderClass = "border-[#334155]";

  if (label === "Person") {
    iconBgClass = "bg-teal-950/80 text-teal-400 border-teal-800/60";
    borderClass = isHighRisk ? "border-red-500/80 shadow-[0_0_12px_rgba(239,68,68,0.25)]" : "border-teal-700/60";
  } else if (label === "Organization") {
    iconBgClass = "bg-blue-950/80 text-blue-400 border-blue-800/60";
    borderClass = "border-blue-700/60";
  } else if (label === "Location") {
    iconBgClass = "bg-orange-950/80 text-orange-400 border-orange-800/60";
    borderClass = "border-orange-700/60";
  } else if (label === "BankAccount" || label === "Financial") {
    iconBgClass = "bg-amber-950/80 text-amber-400 border-amber-800/60";
    borderClass = "border-amber-700/60";
  } else if (label === "State" || label === "CrimeCategory") {
    iconBgClass = "bg-cyan-950/80 text-cyan-400 border-cyan-800/60";
    borderClass = "border-cyan-700/60";
  } else if (label === "Evidence" || label === "Case") {
    iconBgClass = "bg-emerald-950/80 text-emerald-400 border-emerald-800/60";
    borderClass = "border-emerald-700/60";
  } else if (label === "MLPrediction") {
    iconBgClass = "bg-purple-950/80 text-purple-400 border-purple-800/60";
    borderClass = "border-purple-700/60";
  } else if (label === "Device" || label === "IP" || label === "Domain") {
    iconBgClass = "bg-indigo-950/80 text-indigo-400 border-indigo-800/60";
    borderClass = "border-indigo-700/60";
  }

  const typeConfig: Record<string, { icon: React.ElementType; badgeText: string }> = {
    Person: { icon: User, badgeText: "Suspect / Witness" },
    Phone: { icon: Smartphone, badgeText: "Phone / IMEI" },
    BankAccount: { icon: CreditCard, badgeText: "Bank Account" },
    Financial: { icon: CreditCard, badgeText: "Financial Flow" },
    Location: { icon: MapPin, badgeText: "Location" },
    Organization: { icon: Building2, badgeText: "Organization" },
    Device: { icon: Cpu, badgeText: "Device / Intercept" },
    Vehicle: { icon: Car, badgeText: "Vehicle" },
    Event: { icon: CalendarDays, badgeText: "Event" },
    State: { icon: Globe2, badgeText: "Jurisdiction" },
    CrimeCategory: { icon: ShieldAlert, badgeText: "IT Act Offense" },
    Evidence: { icon: FileCheck2, badgeText: "Verified Evidence" },
    MLPrediction: { icon: Binary, badgeText: "Model Prediction" },
    IP: { icon: Network, badgeText: "IP Address" },
    Domain: { icon: Globe, badgeText: "Domain / URL" },
    Email: { icon: AtSign, badgeText: "Email" },
    Hash: { icon: FileCode2, badgeText: "SHA-256 Hash" },
  };

  const cfg = typeConfig[label] || typeConfig["Person"];
  const Icon = cfg.icon;
  const nodeWidth = 220;

  return (
    <div
      className={cn(
        "group relative flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-slate-100 transition-all duration-200 cursor-pointer select-none",
        "bg-[#0f172a] border backdrop-blur-md shadow-md",
        borderClass,
        isCentral && "ring-2 ring-cyan-400 scale-105 shadow-[0_0_16px_rgba(6,182,212,0.35)]",
        nodeData.isDimmed && "opacity-25 grayscale",
        nodeData.isHighlighted && !isCentral && "ring-2 ring-cyan-500/80 shadow-[0_0_12px_rgba(6,182,212,0.25)]",
        selected && "ring-2 ring-cyan-400 border-cyan-400"
      )}
      style={{ width: nodeWidth }}
    >
      {/* Handles */}
      <Handle type="target" position={Position.Top} className="!size-2 !bg-cyan-500 !border-[#0f172a]" />
      <Handle type="source" position={Position.Bottom} className="!size-2 !bg-cyan-500 !border-[#0f172a]" />
      <Handle type="target" position={Position.Left} className="!size-2 !bg-cyan-500 !border-[#0f172a]" />
      <Handle type="source" position={Position.Right} className="!size-2 !bg-cyan-500 !border-[#0f172a]" />

      {/* Entity Icon */}
      <div className={cn("flex size-8 shrink-0 items-center justify-center rounded-md border", iconBgClass)}>
        <Icon className="size-4" />
      </div>

      {/* Details */}
      <div className="min-w-0 flex-1">
        <h4 className="font-sans text-xs font-semibold text-slate-100 truncate" title={entity.name}>
          {entity.name}
        </h4>
        <span className="text-[10px] text-slate-400 truncate block">
          {entity.role || entity.status || cfg.badgeText}
        </span>
      </div>

      {/* Risk Badge */}
      <div className="shrink-0 flex items-center">
        <span
          className={cn(
            "flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-mono font-bold",
            isHighRisk
              ? "bg-red-950/80 text-red-400 border border-red-800/80"
              : risk >= 70
              ? "bg-amber-950/80 text-amber-400 border border-amber-800/80"
              : "bg-slate-800 text-slate-300 border border-slate-700"
          )}
        >
          {risk}
        </span>
      </div>
    </div>
  );
});
