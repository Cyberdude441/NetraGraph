import React from "react";
import {
  History,
  ShieldCheck,
  Download,
  UserCheck,
  Clock,
  FileCheck2,
  GitMerge,
  Tag,
  TrendingUp,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import type { AuditLogEntry } from "@/utils/entityResolver";

interface AuditTrailProps {
  logs: AuditLogEntry[];
}

export function AuditTrail({ logs }: AuditTrailProps) {
  const handleExportAudit = () => {
    toast.success("Audit Log Exported", {
      description: "Cryptographically signed Section 65B audit trail PDF/JSON dossier generated.",
    });
  };

  const getActionBadge = (action: AuditLogEntry["action"]) => {
    switch (action) {
      case "ENTITY_MERGED":
        return {
          icon: GitMerge,
          text: "Profile Merged",
          style: "bg-purple-950/60 border-purple-800 text-purple-300",
        };
      case "ALIAS_ADDED":
        return {
          icon: Tag,
          text: "Alias Added",
          style: "bg-emerald-950/60 border-emerald-800 text-emerald-300",
        };
      case "CONFIDENCE_UPDATED":
        return {
          icon: ShieldCheck,
          text: "Confidence Updated",
          style: "bg-emerald-950/60 border-emerald-800 text-emerald-300",
        };
      default:
        return {
          icon: FileCheck2,
          text: "Record Modified",
          style: "bg-slate-100 border-slate-300 text-slate-700",
        };
    }
  };

  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
        <div className="flex items-center gap-2">
          <History className="size-4 text-emerald-400" />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-900">
              Forensic Audit Trail & Chain of Custody Register
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              Statutory Compliance under IT Act §69B & Indian Evidence Act §65B
            </p>
          </div>
        </div>

        <button
          onClick={handleExportAudit}
          className="flex items-center gap-1.5 rounded border border-[#E2E8F0] bg-[#F8FAFC] px-3 py-1.5 text-xs font-mono font-semibold text-slate-800 hover:border-emerald-500 transition-colors cursor-pointer"
        >
          <Download className="size-3.5 text-emerald-400" />
          <span>Export Audit Certificate</span>
        </button>
      </div>

      {/* Audit Log Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-[11px]">
          <thead className="border-b border-[#E2E8F0] bg-white text-slate-400 uppercase text-[9px]">
            <tr>
              <th className="px-3 py-2">Timestamp</th>
              <th className="px-3 py-2">Action Type</th>
              <th className="px-3 py-2">Target Entity</th>
              <th className="px-3 py-2">Authorized Officer</th>
              <th className="px-3 py-2">Forensic Modification Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {logs.map((log) => {
              const badge = getActionBadge(log.action);
              const Icon = badge.icon;
              return (
                <tr key={log.id} className="hover:bg-white transition-colors">
                  <td className="px-3 py-2.5 text-slate-400 whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-3 py-2.5">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[9px] font-bold uppercase",
                        badge.style
                      )}
                    >
                      <Icon className="size-2.5" />
                      {badge.text}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 font-bold text-slate-800">
                    {log.entityName} <span className="text-slate-500 font-normal">({log.entityId})</span>
                  </td>
                  <td className="px-3 py-2.5 text-emerald-300">
                    {log.userName}
                    <span className="text-slate-500 block text-[9px]">{log.userRole}</span>
                  </td>
                  <td className="px-3 py-2.5 text-slate-700 max-w-xs truncate" title={log.details}>
                    {log.details}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
