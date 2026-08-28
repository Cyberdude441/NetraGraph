import React from "react";
import {
  Cpu,
  Layers,
  ShieldCheck,
  Zap,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Upload,
  RefreshCw,
} from "lucide-react";
import type { MLModel } from "@/types";

interface MLOverviewHeaderProps {
  models: MLModel[];
  isLoading: boolean;
  onRefresh: () => void;
  onOpenImport: () => void;
}

export function MLOverviewHeader({
  models,
  isLoading,
  onRefresh,
  onOpenImport,
}: MLOverviewHeaderProps) {
  const activeCount = models.filter((m) => m.active).length;
  const totalVersions = models.length;

  const domains = [
    { label: "Session Intrusion", task: "intrusion", icon: ShieldCheck },
    { label: "Network Intrusion", task: "intrusion", icon: Activity },
    { label: "Phishing URL", task: "phishing-url", icon: Zap },
    { label: "Web Phishing", task: "phishing-url", icon: Layers },
    { label: "Phishing Email", task: "phishing-email", icon: Cpu },
  ];

  return (
    <div className="space-y-4">
      {/* Top Banner / Header Actions */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-lg border border-[#E2E8F0] bg-white p-4 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-[#064E3B] text-white shadow-xs">
            <Cpu className="size-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-[#0F172A]">
                Machine Learning Intelligence Workspace
              </h2>
              <span className="rounded bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[11px] font-semibold text-[#16A34A]">
                Inference Engine Active
              </span>
            </div>
            <p className="text-xs text-[#64748B]">
              Standardized scikit-learn & tabular prediction engines with cryptographic bundle registry and schema validation.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center gap-1.5 rounded-md border border-[#E2E8F0] bg-white px-3 py-1.5 text-xs font-semibold text-[#0F172A] hover:bg-[#F8FAFC] transition-colors cursor-pointer disabled:opacity-60 shadow-xs"
          >
            <RefreshCw className={`size-3.5 ${isLoading ? "animate-spin text-[#16A34A]" : "text-[#64748B]"}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={onOpenImport}
            className="flex items-center gap-1.5 rounded-md bg-[#064E3B] px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-[#047857] transition-colors cursor-pointer shadow-xs"
          >
            <Upload className="size-3.5" />
            <span>Import Model Bundle (.zip)</span>
          </button>
        </div>
      </div>

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-[#E2E8F0] bg-white p-3.5 shadow-xs">
          <div className="flex items-center justify-between text-[#64748B] text-xs font-semibold">
            <span>Active Deployments</span>
            <CheckCircle2 className="size-4 text-[#16A34A]" />
          </div>
          <div className="mt-2 text-2xl font-bold text-[#0F172A]">
            {activeCount}
          </div>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            {activeCount > 0 ? "Ready for live inference" : "No active model version"}
          </p>
        </div>

        <div className="rounded-lg border border-[#E2E8F0] bg-white p-3.5 shadow-xs">
          <div className="flex items-center justify-between text-[#64748B] text-xs font-semibold">
            <span>Registered Artifacts</span>
            <Layers className="size-4 text-[#0284C7]" />
          </div>
          <div className="mt-2 text-2xl font-bold text-[#0F172A]">
            {totalVersions}
          </div>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            Immutable versioned bundles
          </p>
        </div>

        <div className="rounded-lg border border-[#E2E8F0] bg-white p-3.5 shadow-xs">
          <div className="flex items-center justify-between text-[#64748B] text-xs font-semibold">
            <span>Supported Domains</span>
            <Cpu className="size-4 text-[#9333EA]" />
          </div>
          <div className="mt-2 text-2xl font-bold text-[#0F172A]">
            5
          </div>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            Intrusion, URLs, Emails & Web
          </p>
        </div>

        <div className="rounded-lg border border-[#E2E8F0] bg-white p-3.5 shadow-xs">
          <div className="flex items-center justify-between text-[#64748B] text-xs font-semibold">
            <span>Runtime Runtime Guard</span>
            <ShieldCheck className="size-4 text-[#16A34A]" />
          </div>
          <div className="mt-2 text-2xl font-bold text-[#064E3B]">
            Python 3.11 / 3.12
          </div>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            Standard scikit-learn stack
          </p>
        </div>
      </div>
    </div>
  );
}
