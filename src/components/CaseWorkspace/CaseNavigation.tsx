import React from "react";
import {
  FolderSearch,
  Users,
  Share2,
  TrendingUp,
  MapPin,
  Flame,
  ShieldCheck,
  FileText,
  History,
  Lock,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface CaseNavigationProps {
  activeTab: string;
  onSelectTab: (tabId: string) => void;
}

export function CaseNavigation({ activeTab, onSelectTab }: CaseNavigationProps) {
  const tabs = [
    { id: "overview", label: "Case Overview", icon: FolderSearch },
    { id: "entities", label: "Suspect Targets", icon: Users },
    { id: "network", label: "Knowledge Graph", icon: Share2 },
    { id: "analytics", label: "Network Centrality", icon: TrendingUp },
    { id: "geo_timeline", label: "Geo-Timeline", icon: MapPin },
    { id: "anomalies", label: "Anomalies & Loops", icon: Flame },
    { id: "evidence_chain", label: "Evidence Chain (§65B)", icon: ShieldCheck },
    { id: "report_builder", label: "Dossier & Reports", icon: FileText },
    { id: "audit_history", label: "Audit Log Register", icon: History },
    { id: "security", label: "Security & RBAC", icon: Lock },
  ];

  return (
    <div className="space-y-1 font-mono text-xs select-none">
      <span className="text-[10px] uppercase font-bold text-slate-500 block px-2 py-1">
        Investigation Workspace:
      </span>
      {tabs.map((t) => {
        const Icon = t.icon;
        const active = activeTab === t.id;

        return (
          <button
            key={t.id}
            onClick={() => onSelectTab(t.id)}
            className={cn(
              "w-full flex items-center gap-2 rounded px-2.5 py-2 transition-all text-left cursor-pointer font-semibold",
              active
                ? "bg-[#1A2634] text-sky-300 border border-sky-500/50 shadow-xs"
                : "text-slate-400 hover:text-slate-200 hover:bg-[#121820]"
            )}
          >
            <Icon className={cn("size-3.5", active ? "text-sky-400" : "text-slate-500")} />
            <span className="truncate">{t.label}</span>
          </button>
        );
      })}
    </div>
  );
}
