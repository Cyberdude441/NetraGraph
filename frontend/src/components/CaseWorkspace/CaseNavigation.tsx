import React from "react";
import {
  FolderSearch,
  Users,
  Share2,
  ShieldCheck,
  FileText,
  Clock,
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
    { id: "overview", label: "Overview", icon: FolderSearch },
    { id: "entities", label: "Entities", icon: Users },
    { id: "network", label: "Network", icon: Share2 },
    { id: "evidence_chain", label: "Evidence", icon: ShieldCheck },
    { id: "geo_timeline", label: "Timeline", icon: Clock },
    { id: "report_builder", label: "Reports", icon: FileText },
    { id: "audit_history", label: "Audit Trail", icon: History },
    { id: "security", label: "Security & Access", icon: Lock },
  ];

  return (
    <div className="space-y-0.5 font-sans text-xs select-none">
      <span className="text-[11px] font-bold uppercase tracking-wider text-[#64748B] block px-2 py-1">
        Case Sections
      </span>
      {tabs.map((t) => {
        const Icon = t.icon;
        const active = activeTab === t.id;

        return (
          <button
            key={t.id}
            onClick={() => onSelectTab(t.id)}
            className={cn(
              "w-full flex items-center gap-2 rounded-md px-2.5 py-1.5 transition-all text-left cursor-pointer font-medium",
              active
                ? "bg-[#D1FAE5] text-[#064E3B] font-semibold border-l-[3px] border-[#16A34A]"
                : "text-[#4B5563] hover:text-[#111827] hover:bg-[#F3F4F6]"
            )}
          >
            <Icon className={cn("size-4", active ? "text-[#064E3B]" : "text-[#64748B]")} />
            <span className="truncate">{t.label}</span>
          </button>
        );
      })}
    </div>
  );
}
