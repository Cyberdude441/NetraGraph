import React, { useState } from "react";
import {
  CheckCircle2,
  XCircle,
  Play,
  Shield,
  Layers,
  FileCode,
  Calendar,
  KeyRound,
  BarChart3,
  AlertCircle,
  Power,
  PowerOff,
  ChevronRight,
  Database,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";
import type { MLModel } from "@/types";
import { api } from "@/services/api";

interface ModelRegistryTableProps {
  models: MLModel[];
  isLoading: boolean;
  onRefresh: () => void;
}

export function ModelRegistryTable({
  models,
  isLoading,
  onRefresh,
}: ModelRegistryTableProps) {
  const [selectedSchemaModel, setSelectedSchemaModel] = useState<MLModel | null>(null);
  const [confirmActivateModel, setConfirmActivateModel] = useState<{
    name: string;
    version: string;
    action: "activate" | "deactivate";
  } | null>(null);
  const [isActionPending, setIsActionPending] = useState(false);

  const handleConfirmToggle = async () => {
    if (!confirmActivateModel) return;
    setIsActionPending(true);
    try {
      if (confirmActivateModel.action === "activate") {
        await api.activateMLModel(confirmActivateModel.name, confirmActivateModel.version);
        toast.success(`Model Activated Successfully`, {
          description: `${confirmActivateModel.name} (${confirmActivateModel.version}) is now active for live predictions.`,
        });
      } else {
        await api.deactivateMLModel(confirmActivateModel.name, confirmActivateModel.version);
        toast.info(`Model Deactivated`, {
          description: `${confirmActivateModel.name} (${confirmActivateModel.version}) has been set to inactive.`,
        });
      }
      onRefresh();
    } catch (err: any) {
      toast.error("Action Failed", {
        description: err.message || "Failed to update model status.",
      });
    } finally {
      setIsActionPending(false);
      setConfirmActivateModel(null);
    }
  };

  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white shadow-xs">
      {/* Table Header */}
      <div className="border-b border-[#E2E8F0] px-4 py-3 flex flex-wrap items-center justify-between gap-3 bg-[#F8FAFC]">
        <div>
          <h3 className="text-sm font-bold text-[#0F172A] flex items-center gap-2">
            <span>Registered Model Artifacts</span>
            <span className="rounded bg-[#E2E8F0] px-2 py-0.5 text-xs font-semibold text-[#475569]">
              {models.length} Versions
            </span>
          </h3>
          <p className="text-xs text-[#64748B]">
            Validated bundles loaded into the NetraGraph Model Registry for operational inference.
          </p>
        </div>
      </div>

      {/* Table Body */}
      {isLoading ? (
        <div className="p-12 text-center text-xs text-[#64748B]">
          <div className="inline-block size-6 animate-spin rounded-full border-2 border-[#064E3B] border-t-transparent mb-2" />
          <p>Querying Model Registry catalog...</p>
        </div>
      ) : models.length === 0 ? (
        <div className="p-12 text-center space-y-2">
          <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-emerald-50 text-[#064E3B]">
            <Database className="size-6" />
          </div>
          <h4 className="text-sm font-bold text-[#0F172A]">No Models Registered Yet</h4>
          <p className="text-xs text-[#64748B] max-w-md mx-auto">
            Upload your trained model bundle ZIP via the <strong>Import Model Bundle</strong> button above or deploy through Colab/Kaggle export pipelines.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#E2E8F0] bg-[#F8FAFC] text-[#64748B] text-[10px] uppercase font-bold tracking-wider">
                <th className="px-4 py-2.5">Model Name / Task</th>
                <th className="px-4 py-2.5">Version</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Input Features</th>
                <th className="px-4 py-2.5">Training Metrics</th>
                <th className="px-4 py-2.5">Artifact SHA-256</th>
                <th className="px-4 py-2.5">Imported Date</th>
                <th className="px-4 py-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E8F0] bg-white">
              {models.map((model) => {
                const metrics = model.metrics || {};
                const accuracy = metrics.accuracy ?? metrics.f1_score ?? metrics.f1;
                const featuresCount = model.input_schema?.feature_names?.length || 0;

                return (
                  <tr key={`${model.model_name}-${model.version}`} className="hover:bg-[#F8FAFC] transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="size-2 rounded-full bg-[#064E3B]" />
                        <div>
                          <strong className="text-[#0F172A] font-bold block">{model.model_name}</strong>
                          <span className="text-[11px] text-[#64748B] font-mono">
                            {model.task_type || model.model_name}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="px-4 py-3 font-mono font-semibold text-[#0F172A]">
                      <span className="rounded bg-[#F1F5F9] border border-[#E2E8F0] px-2 py-0.5 text-xs">
                        {model.version}
                      </span>
                    </td>

                    <td className="px-4 py-3">
                      {model.active ? (
                        <span className="inline-flex items-center gap-1 rounded bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[11px] font-semibold text-[#16A34A]">
                          <CheckCircle2 className="size-3" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded bg-slate-50 border border-slate-200 px-2 py-0.5 text-[11px] font-medium text-[#64748B]">
                          <PowerOff className="size-3 text-[#94A3B8]" />
                          Inactive
                        </span>
                      )}
                    </td>

                    <td className="px-4 py-3">
                      <button
                        onClick={() => setSelectedSchemaModel(model)}
                        className="inline-flex items-center gap-1 text-[#064E3B] hover:text-[#047857] font-semibold cursor-pointer underline text-xs"
                      >
                        <FileCode className="size-3" />
                        <span>{featuresCount} Features</span>
                      </button>
                    </td>

                    <td className="px-4 py-3">
                      {accuracy !== undefined ? (
                        <div className="flex items-center gap-1.5">
                          <BarChart3 className="size-3 text-[#16A34A]" />
                          <span className="font-semibold text-[#0F172A]">
                            {(accuracy * 100).toFixed(1)}% Acc
                          </span>
                        </div>
                      ) : (
                        <span className="text-[#94A3B8] italic text-[11px]">N/A</span>
                      )}
                    </td>

                    <td className="px-4 py-3 font-mono text-[11px] text-[#64748B]" title={model.artifact_sha256}>
                      {model.artifact_sha256 ? `${model.artifact_sha256.slice(0, 10)}...${model.artifact_sha256.slice(-6)}` : "—"}
                    </td>

                    <td className="px-4 py-3 text-[#64748B] text-[11px] whitespace-nowrap">
                      {model.import_timestamp
                        ? new Date(model.import_timestamp).toLocaleDateString()
                        : "—"}
                    </td>

                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      {model.active ? (
                        <button
                          onClick={() =>
                            setConfirmActivateModel({
                              name: model.model_name,
                              version: model.version,
                              action: "deactivate",
                            })
                          }
                          className="inline-flex items-center gap-1 rounded border border-[#E2E8F0] bg-white px-2.5 py-1 text-xs font-semibold text-[#64748B] hover:bg-[#F8FAFC] cursor-pointer shadow-xs"
                        >
                          <PowerOff className="size-3 text-[#EA580C]" />
                          <span>Deactivate</span>
                        </button>
                      ) : (
                        <button
                          onClick={() =>
                            setConfirmActivateModel({
                              name: model.model_name,
                              version: model.version,
                              action: "activate",
                            })
                          }
                          className="inline-flex items-center gap-1 rounded bg-[#064E3B] px-2.5 py-1 text-xs font-semibold text-white hover:bg-[#047857] cursor-pointer shadow-xs"
                        >
                          <Play className="size-3 text-white" />
                          <span>Set Active</span>
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Feature Schema Modal */}
      {selectedSchemaModel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-lg border border-[#E2E8F0] bg-white p-5 shadow-xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <div>
                <h4 className="text-sm font-bold text-[#0F172A] flex items-center gap-2">
                  <FileCode className="size-4 text-[#064E3B]" />
                  <span>Feature Schema Contract</span>
                </h4>
                <p className="text-xs text-[#64748B]">
                  {selectedSchemaModel.model_name} · Version {selectedSchemaModel.version}
                </p>
              </div>
              <button
                onClick={() => setSelectedSchemaModel(null)}
                className="rounded-md p-1 text-[#64748B] hover:bg-[#F1F5F9] cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 text-xs">
              <div className="text-[11px] font-bold uppercase tracking-wider text-[#64748B]">
                Expected Input Columns ({selectedSchemaModel.input_schema.feature_names.length}):
              </div>
              <div className="rounded border border-[#E2E8F0] bg-[#F8FAFC] divide-y divide-[#E2E8F0]">
                {selectedSchemaModel.input_schema.feature_names.map((name, idx) => (
                  <div key={idx} className="p-2 flex items-center justify-between">
                    <span className="font-mono font-semibold text-[#0F172A]">{name}</span>
                    <span className="text-[11px] font-mono text-[#64748B]">
                      {selectedSchemaModel.input_schema.dtypes?.[name] || "numeric / text"}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-[#E2E8F0]">
              <button
                onClick={() => setSelectedSchemaModel(null)}
                className="rounded-md bg-[#064E3B] px-4 py-1.5 text-xs font-semibold text-white cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Dialog for Activation */}
      {confirmActivateModel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-md rounded-lg border border-[#E2E8F0] bg-white p-5 shadow-xl space-y-4">
            <div className="flex items-center gap-3">
              <div className={`flex size-10 items-center justify-center rounded-full ${confirmActivateModel.action === "activate" ? "bg-emerald-50 text-[#16A34A]" : "bg-amber-50 text-[#EA580C]"}`}>
                <AlertCircle className="size-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#0F172A]">
                  {confirmActivateModel.action === "activate" ? "Confirm Model Activation" : "Confirm Model Deactivation"}
                </h4>
                <p className="text-xs text-[#64748B]">
                  Target: <strong>{confirmActivateModel.name}</strong> ({confirmActivateModel.version})
                </p>
              </div>
            </div>

            <p className="text-xs text-[#334155] leading-relaxed">
              {confirmActivateModel.action === "activate"
                ? `Activating this version will direct all live inference requests for '${confirmActivateModel.name}' to this specific bundle. Any currently active version will become inactive.`
                : `Deactivating will cause prediction requests for '${confirmActivateModel.name}' to return 404 until another version is activated.`}
            </p>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
              <button
                onClick={() => setConfirmActivateModel(null)}
                disabled={isActionPending}
                className="rounded-md border border-[#E2E8F0] px-3.5 py-1.5 text-xs font-semibold text-[#64748B] hover:bg-[#F8FAFC] cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmToggle}
                disabled={isActionPending}
                className="rounded-md bg-[#064E3B] px-4 py-1.5 text-xs font-semibold text-white hover:bg-[#047857] cursor-pointer disabled:opacity-50"
              >
                {isActionPending ? "Updating..." : confirmActivateModel.action === "activate" ? "Activate Version" : "Deactivate Version"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
