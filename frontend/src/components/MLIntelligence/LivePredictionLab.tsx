import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  Zap,
  Mail,
  Play,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Info,
  Clock,
  Fingerprint,
  RefreshCw,
  Sparkles,
  Sliders,
} from "lucide-react";
import { toast } from "sonner";
import type { MLModel, MLPredictionResult } from "@/types";
import { api } from "@/services/api";

interface LivePredictionLabProps {
  models: MLModel[];
  onRefreshModels: () => void;
}

type PredictionDomain = "intrusion" | "phishing-url" | "phishing-email";

export function LivePredictionLab({ models, onRefreshModels }: LivePredictionLabProps) {
  const [activeDomain, setActiveDomain] = useState<PredictionDomain>("intrusion");
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [selectedModelName, setSelectedModelName] = useState<string>("");
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionResult, setPredictionResult] = useState<MLPredictionResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filter available models for the selected task/domain
  const domainModels = models.filter((m) => {
    const task = (m.task_type || m.model_name || "").toLowerCase();
    if (activeDomain === "intrusion") {
      return task.includes("intrusion") || m.model_name.toLowerCase().includes("intrusion");
    }
    if (activeDomain === "phishing-url") {
      return task.includes("url") || task.includes("web") || m.model_name.toLowerCase().includes("url") || m.model_name.toLowerCase().includes("web");
    }
    if (activeDomain === "phishing-email") {
      return task.includes("email") || m.model_name.toLowerCase().includes("email");
    }
    return false;
  });

  const activeModel = domainModels.find((m) => m.active) || domainModels[0] || null;

  // Sync selected model and dynamic features on domain or active model change
  useEffect(() => {
    if (activeModel) {
      setSelectedModelName(activeModel.model_name);
      // Initialize empty form with feature schema
      const initial: Record<string, any> = {};
      activeModel.input_schema?.feature_names?.forEach((f) => {
        initial[f] = "";
      });
      setFormData(initial);
    } else {
      setSelectedModelName("");
      setFormData({});
    }
    setPredictionResult(null);
    setErrorMsg(null);
  }, [activeDomain, activeModel?.model_name, activeModel?.version]);

  const handleInputChange = (featureName: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [featureName]: value,
    }));
  };

  const handleApplyPreset = (presetValues: Record<string, any>) => {
    setFormData(presetValues);
    toast.success("Preset sample applied", {
      description: "Feature inputs filled with synthetic test telemetry.",
    });
  };

  const handleRunPrediction = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsPredicting(true);
    setErrorMsg(null);
    setPredictionResult(null);

    // Convert numeric inputs appropriately
    const payload: Record<string, any> = {};
    for (const [key, val] of Object.entries(formData)) {
      if (val === "" || val === undefined) {
        payload[key] = 0; // Default zero fill if empty
      } else if (!isNaN(Number(val)) && typeof val === "string" && val.trim() !== "") {
        payload[key] = Number(val);
      } else {
        payload[key] = val;
      }
    }

    try {
      let res: MLPredictionResult;
      if (activeDomain === "intrusion") {
        res = await api.predictIntrusion(payload);
      } else if (activeDomain === "phishing-url") {
        res = await api.predictPhishingUrl(payload);
      } else {
        res = await api.predictPhishingEmail(payload);
      }
      setPredictionResult(res);
      toast.success("Prediction Executed", {
        description: `Class: ${res.prediction} · Confidence: ${res.probability ? (res.probability * 100).toFixed(1) + "%" : "Evaluated"}`,
      });
    } catch (err: any) {
      const msg = err.message || "Failed to execute prediction.";
      setErrorMsg(msg);
      toast.error("Inference Error", {
        description: msg,
      });
    } finally {
      setIsPredicting(false);
    }
  };

  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white shadow-xs">
      {/* Tab Navigation for Supported Prediction Domains */}
      <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] px-4 py-2.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setActiveDomain("intrusion")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold cursor-pointer transition-all ${
              activeDomain === "intrusion"
                ? "bg-[#064E3B] text-white shadow-xs"
                : "text-[#64748B] hover:bg-[#E2E8F0] hover:text-[#0F172A]"
            }`}
          >
            <ShieldAlert className="size-3.5" />
            <span>Intrusion Detection</span>
          </button>

          <button
            onClick={() => setActiveDomain("phishing-url")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold cursor-pointer transition-all ${
              activeDomain === "phishing-url"
                ? "bg-[#064E3B] text-white shadow-xs"
                : "text-[#64748B] hover:bg-[#E2E8F0] hover:text-[#0F172A]"
            }`}
          >
            <Zap className="size-3.5" />
            <span>Phishing URL Detection</span>
          </button>

          <button
            onClick={() => setActiveDomain("phishing-email")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold cursor-pointer transition-all ${
              activeDomain === "phishing-email"
                ? "bg-[#064E3B] text-white shadow-xs"
                : "text-[#64748B] hover:bg-[#E2E8F0] hover:text-[#0F172A]"
            }`}
          >
            <Mail className="size-3.5" />
            <span>Phishing Email Detection</span>
          </button>
        </div>

        {activeModel && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-[#64748B]">Active Model:</span>
            <span className="font-bold text-[#064E3B] bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              {activeModel.model_name} ({activeModel.version})
            </span>
          </div>
        )}
      </div>

      {/* Main Grid: Feature Input Form (Left) & Result Panel (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[#E2E8F0]">
        {/* Left 7 Columns: Dynamic Feature Form */}
        <div className="lg:col-span-7 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2.5">
            <div>
              <h4 className="text-sm font-bold text-[#0F172A] flex items-center gap-2">
                <Sliders className="size-4 text-[#064E3B]" />
                <span>Telemetry Input Parameters</span>
              </h4>
              <p className="text-xs text-[#64748B]">
                {activeModel
                  ? `Dynamic input schema generated from active bundle (${activeModel.input_schema?.feature_names?.length || 0} features expected)`
                  : "No active model registered for this task domain."}
              </p>
            </div>
          </div>

          {!activeModel ? (
            <div className="rounded-md border border-dashed border-[#E2E8F0] bg-[#F8FAFC] p-6 text-center text-xs text-[#64748B] space-y-2">
              <AlertTriangle className="size-6 text-[#EA580C] mx-auto" />
              <p className="font-semibold text-[#0F172A]">
                No Model Active for {activeDomain === "intrusion" ? "Intrusion Detection" : activeDomain === "phishing-url" ? "Phishing URL" : "Phishing Email"}
              </p>
              <p>
                Import a model artifact bundle or activate an existing version from the Model Registry above to unlock live inference.
              </p>
            </div>
          ) : (
            <form onSubmit={handleRunPrediction} className="space-y-4">
              {/* Dynamic Feature Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[360px] overflow-y-auto pr-1">
                {activeModel.input_schema?.feature_names?.map((feature) => {
                  const dtype = activeModel.input_schema.dtypes?.[feature] || "number";
                  const isNum = dtype.includes("int") || dtype.includes("float") || dtype === "number";

                  return (
                    <div key={feature} className="space-y-1">
                      <label className="text-xs font-mono font-semibold text-[#334155] block truncate" title={feature}>
                        {feature}
                      </label>
                      <input
                        type={isNum ? "number" : "text"}
                        step={isNum ? "any" : undefined}
                        value={formData[feature] ?? ""}
                        onChange={(e) => handleInputChange(feature, e.target.value)}
                        placeholder={`Enter ${feature}...`}
                        className="w-full rounded-md border border-[#D9E2EC] bg-white px-2.5 py-1.5 text-xs text-[#0F172A] placeholder:text-[#94A3B8] focus:border-[#064E3B] focus:outline-none focus:ring-1 focus:ring-[#064E3B]"
                      />
                    </div>
                  );
                })}
              </div>

              {/* Submit Action */}
              <div className="pt-3 border-t border-[#E2E8F0] flex items-center justify-between">
                <span className="text-[11px] text-[#64748B]">
                  POST /api/ml/predict/{activeDomain}
                </span>

                <button
                  type="submit"
                  disabled={isPredicting || !activeModel}
                  className="flex items-center gap-1.5 rounded-md bg-[#064E3B] px-4 py-2 text-xs font-semibold text-white hover:bg-[#047857] transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
                >
                  <Play className={`size-3.5 ${isPredicting ? "animate-spin" : ""}`} />
                  <span>{isPredicting ? "Executing Inference..." : "Run ML Inference"}</span>
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Right 5 Columns: Result & Forensic Output */}
        <div className="lg:col-span-5 p-5 bg-[#F8FAFC] space-y-4">
          <h4 className="text-sm font-bold text-[#0F172A] border-b border-[#E2E8F0] pb-2.5 flex items-center justify-between">
            <span>Inference Forensics & Classification</span>
            {predictionResult && (
              <span className="rounded bg-emerald-50 text-[#16A34A] border border-emerald-200 px-2 py-0.5 text-[10px] font-bold">
                VALIDATED
              </span>
            )}
          </h4>

          {errorMsg ? (
            <div className="rounded-md border border-red-200 bg-red-50 p-4 text-xs text-[#DC2626] space-y-1.5">
              <div className="flex items-center gap-1.5 font-bold">
                <AlertTriangle className="size-4" />
                <span>Prediction Failed</span>
              </div>
              <p className="leading-relaxed">{errorMsg}</p>
            </div>
          ) : !predictionResult ? (
            <div className="rounded-md border border-dashed border-[#D9E2EC] bg-white p-8 text-center text-xs text-[#64748B] space-y-2">
              <Sparkles className="size-6 text-[#94A3B8] mx-auto" />
              <p className="font-semibold text-[#0F172A]">Awaiting Input Execution</p>
              <p className="text-[11px] max-w-xs mx-auto">
                Fill telemetry parameters and click <strong>Run ML Inference</strong> to evaluate classification and confidence scores.
              </p>
            </div>
          ) : (
            <div className="space-y-3.5">
              {/* Verdict Card */}
              <div className="rounded-lg border border-[#E2E8F0] bg-white p-4 shadow-xs space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#64748B] block">
                  Target Classification
                </span>
                <div className="flex items-center justify-between">
                  <span className="text-lg font-bold text-[#0F172A]">
                    {predictionResult.prediction}
                  </span>
                  <span
                    className={`rounded-md px-2.5 py-1 text-xs font-bold ${
                      predictionResult.prediction.toLowerCase().includes("malicious") ||
                      predictionResult.prediction.toLowerCase().includes("attack") ||
                      predictionResult.prediction.toLowerCase().includes("phish") ||
                      predictionResult.prediction === "1"
                        ? "bg-red-50 text-[#DC2626] border border-red-200"
                        : "bg-emerald-50 text-[#16A34A] border border-emerald-200"
                    }`}
                  >
                    {predictionResult.prediction.toLowerCase().includes("malicious") ||
                    predictionResult.prediction.toLowerCase().includes("attack") ||
                    predictionResult.prediction.toLowerCase().includes("phish") ||
                    predictionResult.prediction === "1"
                      ? "High Threat Detected"
                      : "Benign / Normal"}
                  </span>
                </div>

                {/* Probability Bar */}
                {predictionResult.probability !== null && (
                  <div className="space-y-1 pt-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-[#64748B]">Confidence Score</span>
                      <span className="font-bold text-[#064E3B]">
                        {(predictionResult.probability * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-[#E2E8F0]">
                      <div
                        className="h-full rounded-full bg-[#16A34A] transition-all duration-500"
                        style={{ width: `${Math.min(100, predictionResult.probability * 100)}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Forensic Details */}
              <div className="rounded-lg border border-[#E2E8F0] bg-white p-3.5 text-xs space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#64748B] block">
                  Model Provenance
                </span>
                <div className="space-y-1.5 text-xs text-[#334155]">
                  <div className="flex justify-between">
                    <span className="text-[#64748B]">Source Model:</span>
                    <span className="font-bold text-[#0F172A]">{predictionResult.model} ({predictionResult.model_version})</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#64748B]">Artifact Hash:</span>
                    <span className="font-mono text-[11px] text-[#064E3B]" title={predictionResult.artifact_hash}>
                      {predictionResult.artifact_hash ? `${predictionResult.artifact_hash.slice(0, 12)}...` : "—"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#64748B]">Inference Timestamp:</span>
                    <span className="text-[#0F172A]">{new Date(predictionResult.prediction_timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>

                {predictionResult.analyst_verification_required && (
                  <div className="mt-2 rounded bg-amber-50 p-2 border border-amber-200/80 text-[11px] text-[#D97706] flex items-start gap-1.5">
                    <Info className="size-3.5 shrink-0 mt-0.5" />
                    <span>ML inference results provide decision support. Judicial submission requires forensic analyst sign-off under Section 65B.</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
