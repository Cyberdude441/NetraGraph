import { createFileRoute } from "@tanstack/react-router";
import React, { useState, useEffect, useCallback } from "react";
import {
  Cpu,
  Layers,
  FlaskConical,
  Database,
  Upload,
  RefreshCw,
  Info,
  ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";

import { AppShell } from "@/components/AppShell";
import { MLOverviewHeader } from "@/components/MLIntelligence/MLOverviewHeader";
import { ModelRegistryTable } from "@/components/MLIntelligence/ModelRegistryTable";
import { LivePredictionLab } from "@/components/MLIntelligence/LivePredictionLab";
import { ModelImportModal } from "@/components/MLIntelligence/ModelImportModal";
import { api } from "@/services/api";
import type { MLModel } from "@/types";

export const Route = createFileRoute("/ml-intelligence")({
  head: () => ({
    meta: [
      { title: "Machine Learning Intelligence & Prediction Engines — NetraGraph AI" },
      {
        name: "description",
        content:
          "Operational Machine Learning Intelligence workspace: Model Registry, dynamic schema-driven Live Prediction Lab, version management, and cryptographic bundle imports for cyber threat intelligence.",
      },
    ],
  }),
  component: MLIntelligencePage,
});

function MLIntelligencePage() {
  const [models, setModels] = useState<MLModel[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isImportModalOpen, setIsImportModalOpen] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"overview" | "lab" | "registry">("overview");

  const fetchModels = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.getMLModels();
      setModels(data || []);
    } catch (err: any) {
      console.error("Failed to load ML models:", err);
      toast.error("Failed to load Model Registry", {
        description: err.message || "Ensure the backend service is running.",
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  return (
    <AppShell title="ML Intelligence">
      <div className="space-y-6 pb-12">
        {/* Top Header & KPI Summary */}
        <MLOverviewHeader
          models={models}
          isLoading={isLoading}
          onRefresh={fetchModels}
          onOpenImport={() => setIsImportModalOpen(true)}
        />

        {/* Navigation Tabs between Live Prediction Lab and Model Registry */}
        <div className="flex items-center gap-1 border-b border-[#E2E8F0] pb-2 text-xs font-semibold">
          <button
            onClick={() => setActiveTab("overview")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md cursor-pointer transition-all ${
              activeTab === "overview"
                ? "bg-[#064E3B] text-white shadow-xs"
                : "text-[#64748B] hover:bg-[#E2E8F0] hover:text-[#0F172A]"
            }`}
          >
            <Cpu className="size-3.5" />
            <span>Full Workspace</span>
          </button>

          <button
            onClick={() => setActiveTab("lab")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md cursor-pointer transition-all ${
              activeTab === "lab"
                ? "bg-[#064E3B] text-white shadow-xs"
                : "text-[#64748B] hover:bg-[#E2E8F0] hover:text-[#0F172A]"
            }`}
          >
            <FlaskConical className="size-3.5" />
            <span>Live Prediction Lab</span>
          </button>

          <button
            onClick={() => setActiveTab("registry")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md cursor-pointer transition-all ${
              activeTab === "registry"
                ? "bg-[#064E3B] text-white shadow-xs"
                : "text-[#64748B] hover:bg-[#E2E8F0] hover:text-[#0F172A]"
            }`}
          >
            <Database className="size-3.5" />
            <span>Model Registry</span>
          </button>
        </div>

        {/* Workspace Sections */}
        {(activeTab === "overview" || activeTab === "lab") && (
          <section className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#0F172A] flex items-center gap-2">
                <FlaskConical className="size-4 text-[#064E3B]" />
                <span>Live Interactive Inference Lab</span>
              </h3>
              <span className="text-xs text-[#64748B]">
                Real-time prediction with input feature contract validation
              </span>
            </div>
            <LivePredictionLab models={models} onRefreshModels={fetchModels} />
          </section>
        )}

        {(activeTab === "overview" || activeTab === "registry") && (
          <section className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#0F172A] flex items-center gap-2">
                <Database className="size-4 text-[#064E3B]" />
                <span>Model Artifacts & Deployment Registry</span>
              </h3>
              <span className="text-xs text-[#64748B]">
                Version catalog & active model controllers
              </span>
            </div>
            <ModelRegistryTable
              models={models}
              isLoading={isLoading}
              onRefresh={fetchModels}
            />
          </section>
        )}

        {/* Model Import Modal */}
        <ModelImportModal
          isOpen={isImportModalOpen}
          onClose={() => setIsImportModalOpen(false)}
          onSuccess={fetchModels}
        />
      </div>
    </AppShell>
  );
}
