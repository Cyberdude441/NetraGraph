import React from "react";
import {
  FolderSearch,
  ShieldCheck,
  Flame,
  Users,
  Share2,
  Clock,
} from "lucide-react";

interface CaseDashboardProps {
  caseId: string;
  onNavigateTab: (tabId: string) => void;
}

export function CaseDashboard({ caseId, onNavigateTab }: CaseDashboardProps) {
  return (
    <div className="space-y-4 font-sans">
      {/* Case Header Card */}
      <div className="rounded-md border border-[#D9E2EC] bg-white p-5 space-y-4 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-[#E2E8F0] pb-4">
          <div className="flex items-start gap-3.5">
            <span className="flex size-11 shrink-0 items-center justify-center rounded-md bg-emerald-50 border border-emerald-200 text-[#065F46]">
              <FolderSearch className="size-6" />
            </span>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="font-bold text-[#0F172A] text-lg tracking-tight">
                  Operation Netra-Vigil: Inter-State Cyber Syndicate
                </h2>
                <span className="rounded bg-red-50 text-[#DC3545] border border-red-200 px-2.5 py-0.5 text-xs font-bold">
                  High Priority
                </span>
              </div>
              <p className="text-xs text-[#475569] mt-1">
                Case Docket: <strong className="font-mono text-[#065F46]">{caseId}</strong> · Lead Investigator:{" "}
                <strong className="text-[#0F172A]">Insp. D. Bose</strong> · Unit: State Cyber Crime Police Station
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="rounded-md bg-[#F1F5F9] px-3 py-1.5 text-[#0F172A] font-semibold border border-[#D9E2EC]">
              Status: <span className="text-[#198754] font-bold">Under Active Investigation</span>
            </span>
          </div>
        </div>

        {/* Investigation Progress */}
        <div className="space-y-1.5 text-xs">
          <div className="flex items-center justify-between text-[#475569]">
            <span className="font-semibold text-[#0F172A]">Investigation Progress</span>
            <span className="text-[#065F46] font-bold">85% Complete (Evidence Sealed)</span>
          </div>
          <div className="w-full bg-[#E2E8F0] h-2.5 rounded-full overflow-hidden">
            <div className="bg-[#065F46] h-full rounded-full w-[85%]" />
          </div>
        </div>
      </div>

      {/* Case Telemetry Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5 text-xs">
        <div
          onClick={() => onNavigateTab("entities")}
          className="rounded-md border border-[#D9E2EC] bg-white p-3.5 hover:border-[#065F46] hover:shadow-sm transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-[#64748B] mb-1.5">
            <span className="font-semibold text-xs">Suspects</span>
            <Users className="size-4 text-[#047857]" />
          </div>
          <div className="text-2xl font-bold text-[#0F172A]">105 Entities</div>
          <p className="text-[11px] text-[#64748B] mt-0.5">4 Primary Kingpins</p>
        </div>

        <div
          onClick={() => onNavigateTab("network")}
          className="rounded-md border border-[#D9E2EC] bg-white p-3.5 hover:border-[#065F46] hover:shadow-sm transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-[#64748B] mb-1.5">
            <span className="font-semibold text-xs">Network Links</span>
            <Share2 className="size-4 text-[#065F46]" />
          </div>
          <div className="text-2xl font-bold text-[#065F46]">148 Connections</div>
          <p className="text-[11px] text-[#64748B] mt-0.5">4 Identified Groups</p>
        </div>

        <div
          onClick={() => onNavigateTab("anomalies")}
          className="rounded-md border border-[#D9E2EC] bg-white p-3.5 hover:border-[#DC3545] hover:shadow-sm transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-[#64748B] mb-1.5">
            <span className="font-semibold text-xs">Urgent Alerts</span>
            <Flame className="size-4 text-[#DC3545]" />
          </div>
          <div className="text-2xl font-bold text-[#DC3545]">5 Detected</div>
          <p className="text-[11px] text-[#64748B] mt-0.5">Circular funds & IMEI</p>
        </div>

        <div
          onClick={() => onNavigateTab("evidence")}
          className="rounded-md border border-[#D9E2EC] bg-white p-3.5 hover:border-[#198754] hover:shadow-sm transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-[#64748B] mb-1.5">
            <span className="font-semibold text-xs">Evidence Files</span>
            <ShieldCheck className="size-4 text-[#198754]" />
          </div>
          <div className="text-2xl font-bold text-[#198754]">4 Records</div>
          <p className="text-[11px] text-[#64748B] mt-0.5">SHA-256 Certified</p>
        </div>

        <div
          onClick={() => onNavigateTab("timeline")}
          className="rounded-md border border-[#D9E2EC] bg-white p-3.5 hover:border-[#F59E0B] hover:shadow-sm transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-[#64748B] mb-1.5">
            <span className="font-semibold text-xs">Timeline Events</span>
            <Clock className="size-4 text-[#F59E0B]" />
          </div>
          <div className="text-2xl font-bold text-[#F59E0B]">200 Events</div>
          <p className="text-[11px] text-[#64748B] mt-0.5">Surveillance log</p>
        </div>
      </div>
    </div>
  );
}
