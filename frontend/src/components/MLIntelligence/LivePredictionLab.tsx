import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  Zap,
  Globe,
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
  Database,
} from "lucide-react";
import { toast } from "sonner";
import type { MLModel, MLPredictionResult } from "@/types";
import { api } from "@/services/api";

interface LivePredictionLabProps {
  models: MLModel[];
  onRefreshModels: () => void;
}

type PredictionDomain = "intrusion" | "phishing-url" | "webpage-phishing" | "phishing-email";

// Built-in presets for live testing
const PRESETS: Record<string, { benign: Record<string, any>; threat: Record<string, any> }> = {
  intrusion: {
    benign: {
      network_packet_size: 256,
      protocol_type: "HTTPS",
      login_attempts: 1,
      session_duration: 340.0,
      encryption_used: "AES-256",
      ip_reputation_score: 0.98,
      failed_logins: 0,
      browser_type: "Chrome",
      unusual_time_access: 0,
    },
    threat: {
      network_packet_size: 8192,
      protocol_type: "TCP",
      login_attempts: 18,
      session_duration: 14.5,
      encryption_used: "None",
      ip_reputation_score: 0.08,
      failed_logins: 17,
      browser_type: "Unknown",
      unusual_time_access: 1,
    },
  },
  "network-intrusion": {
    benign: {
      duration: 0,
      protocol_type: "tcp",
      service: "http",
      flag: "SF",
      src_bytes: 232,
      dst_bytes: 8153,
      land: 0,
      wrong_fragment: 0,
      urgent: 0,
      hot: 0,
      num_failed_logins: 0,
      logged_in: 1,
      num_compromised: 0,
      root_shell: 0,
      su_attempted: 0,
      num_root: 0,
      num_file_creations: 0,
      num_shells: 0,
      num_access_files: 0,
      num_outbound_cmds: 0,
      is_host_login: 0,
      is_guest_login: 0,
      count: 5,
      srv_count: 5,
      serror_rate: 0.0,
      srv_serror_rate: 0.0,
      rerror_rate: 0.0,
      srv_rerror_rate: 0.0,
      same_srv_rate: 1.0,
      diff_srv_rate: 0.0,
      srv_diff_host_rate: 0.0,
      dst_host_count: 5,
      dst_host_srv_count: 5,
      dst_host_same_srv_rate: 1.0,
      dst_host_diff_srv_rate: 0.0,
      dst_host_same_src_port_rate: 0.2,
      dst_host_srv_diff_host_rate: 0.0,
      dst_host_serror_rate: 0.0,
      dst_host_srv_serror_rate: 0.0,
      dst_host_rerror_rate: 0.0,
      dst_host_srv_rerror_rate: 0.0,
    },
    threat: {
      duration: 0,
      protocol_type: "tcp",
      service: "private",
      flag: "S0",
      src_bytes: 0,
      dst_bytes: 0,
      land: 0,
      wrong_fragment: 0,
      urgent: 0,
      hot: 0,
      num_failed_logins: 0,
      logged_in: 0,
      num_compromised: 0,
      root_shell: 0,
      su_attempted: 0,
      num_root: 0,
      num_file_creations: 0,
      num_shells: 0,
      num_access_files: 0,
      num_outbound_cmds: 0,
      is_host_login: 0,
      is_guest_login: 0,
      count: 123,
      srv_count: 6,
      serror_rate: 1.0,
      srv_serror_rate: 1.0,
      rerror_rate: 0.0,
      srv_rerror_rate: 0.0,
      same_srv_rate: 0.05,
      diff_srv_rate: 0.07,
      srv_diff_host_rate: 0.0,
      dst_host_count: 255,
      dst_host_srv_count: 6,
      dst_host_same_srv_rate: 0.02,
      dst_host_diff_srv_rate: 0.06,
      dst_host_same_src_port_rate: 0.0,
      dst_host_srv_diff_host_rate: 0.0,
      dst_host_serror_rate: 1.0,
      dst_host_srv_serror_rate: 1.0,
      dst_host_rerror_rate: 0.0,
      dst_host_srv_rerror_rate: 0.0,
    },
  },
  "phishing-url": {
    benign: {
      URLLength: 24,
      DomainLength: 12,
      IsDomainIP: 0,
      TLD: "com",
      URLSimilarityIndex: 100.0,
      CharContinuationRate: 0.8,
      TLDLegitimateProb: 0.52,
      URLCharProb: 0.05,
      TLDLength: 3,
      NoOfSubDomain: 1,
      HasObfuscation: 0,
      NoOfObfuscatedChar: 0,
      ObfuscationRatio: 0.0,
      NoOfLettersInURL: 18,
      LetterRatioInURL: 0.75,
      NoOfDegitsInURL: 0,
      DegitRatioInURL: 0.0,
      NoOfEqualsInURL: 0,
      NoOfQMarkInURL: 0,
      NoOfAmpersandInURL: 0,
      NoOfOtherSpecialCharsInURL: 2,
      SpacialCharRatioInURL: 0.08,
      IsHTTPS: 1,
      LineOfCode: 250,
      LargestLineLength: 120,
      HasTitle: 1,
      DomainTitleMatchScore: 100.0,
      URLTitleMatchScore: 100.0,
      HasFavicon: 1,
      Robots: 1,
      IsResponsive: 1,
      NoOfURLRedirect: 0,
      NoOfSelfRedirect: 0,
      HasDescription: 1,
      NoOfPopup: 0,
      NoOfiFrame: 0,
      HasExternalFormSubmit: 0,
      HasSocialNet: 1,
      HasSubmitButton: 1,
      HasHiddenFields: 0,
      HasPasswordField: 0,
      Bank: 0,
      Pay: 0,
      Crypto: 0,
      HasCopyrightInfo: 1,
      NoOfImage: 5,
      NoOfCSS: 2,
      NoOfJS: 4,
      NoOfSelfRef: 10,
      NoOfEmptyRef: 0,
      NoOfExternalRef: 2,
    },
    threat: {
      URLLength: 88,
      DomainLength: 32,
      IsDomainIP: 1,
      TLD: "xyz",
      URLSimilarityIndex: 22.0,
      CharContinuationRate: 0.3,
      TLDLegitimateProb: 0.02,
      URLCharProb: 0.45,
      TLDLength: 3,
      NoOfSubDomain: 4,
      HasObfuscation: 1,
      NoOfObfuscatedChar: 8,
      ObfuscationRatio: 0.25,
      NoOfLettersInURL: 45,
      LetterRatioInURL: 0.51,
      NoOfDegitsInURL: 16,
      DegitRatioInURL: 0.18,
      NoOfEqualsInURL: 3,
      NoOfQMarkInURL: 2,
      NoOfAmpersandInURL: 2,
      NoOfOtherSpecialCharsInURL: 12,
      SpacialCharRatioInURL: 0.31,
      IsHTTPS: 0,
      LineOfCode: 45,
      LargestLineLength: 45,
      HasTitle: 0,
      DomainTitleMatchScore: 0.0,
      URLTitleMatchScore: 0.0,
      HasFavicon: 0,
      Robots: 0,
      IsResponsive: 0,
      NoOfURLRedirect: 3,
      NoOfSelfRedirect: 2,
      HasDescription: 0,
      NoOfPopup: 2,
      NoOfiFrame: 3,
      HasExternalFormSubmit: 1,
      HasSocialNet: 0,
      HasSubmitButton: 1,
      HasHiddenFields: 4,
      HasPasswordField: 1,
      Bank: 1,
      Pay: 1,
      Crypto: 1,
      HasCopyrightInfo: 0,
      NoOfImage: 1,
      NoOfCSS: 0,
      NoOfJS: 1,
      NoOfSelfRef: 0,
      NoOfEmptyRef: 8,
      NoOfExternalRef: 15,
    },
  },
  "webpage-phishing": {
    benign: {
      length_url: 35,
      length_hostname: 15,
      ip: 0,
      nb_dots: 2,
      nb_hyphens: 0,
      nb_at: 0,
      nb_qm: 0,
      nb_and: 0,
      nb_or: 0,
      nb_eq: 0,
      nb_underscore: 0,
      nb_tilde: 0,
      nb_percent: 0,
      nb_slash: 3,
      nb_star: 0,
      nb_colon: 1,
      nb_comma: 0,
      nb_semicolumn: 0,
      nb_dollar: 0,
      nb_space: 0,
      nb_www: 1,
      nb_com: 1,
      nb_dslash: 0,
      http_in_path: 0,
      https_token: 0,
      ratio_digits_url: 0.0,
      ratio_digits_host: 0.0,
      punycode: 0,
      port: 0,
      tld_in_path: 0,
      tld_in_subdomain: 0,
      abnormal_subdomain: 0,
      nb_subdomains: 1,
      prefix_suffix: 0,
      random_domain: 0,
      shortening_service: 0,
      path_extension: 0,
      nb_redirection: 0,
      nb_external_redirection: 0,
      length_words_raw: 4,
      char_repeat: 0,
      shortest_words_raw: 3,
      shortest_word_host: 3,
      shortest_word_path: 4,
      longest_words_raw: 8,
      longest_word_host: 8,
      longest_word_path: 6,
      avg_words_raw: 5.0,
      avg_word_host: 5.0,
      avg_word_path: 5.0,
      phish_hints: 0,
      domain_in_brand: 0,
      brand_in_subdomain: 0,
      brand_in_path: 0,
      suspecious_tld: 0,
      statistical_report: 0,
      nb_hyperlinks: 25,
      ratio_intHyperlinks: 0.9,
      ratio_extHyperlinks: 0.1,
      ratio_nullHyperlinks: 0,
      nb_extCSS: 1,
      ratio_intRedirection: 0,
      ratio_extRedirection: 0.0,
      ratio_intErrors: 0,
      ratio_extErrors: 0.0,
      login_form: 0,
      external_favicon: 0,
      links_in_tags: 85.0,
      submit_email: 0,
      ratio_intMedia: 0.95,
      ratio_extMedia: 0.05,
      sfh: 0,
      iframe: 0,
      popup_window: 0,
      safe_anchor: 90.0,
      onmouseover: 0,
      right_clic: 0,
      empty_title: 0,
      domain_in_title: 1,
      domain_with_copyright: 1,
      whois_registered_domain: 1,
      domain_registration_length: 365,
      domain_age: 1500,
      web_traffic: 1000,
      dns_record: 1,
      google_index: 1,
      page_rank: 5,
    },
    threat: {
      length_url: 95,
      length_hostname: 35,
      ip: 1,
      nb_dots: 5,
      nb_hyphens: 4,
      nb_at: 1,
      nb_qm: 2,
      nb_and: 3,
      nb_or: 0,
      nb_eq: 2,
      nb_underscore: 2,
      nb_tilde: 0,
      nb_percent: 4,
      nb_slash: 6,
      nb_star: 0,
      nb_colon: 1,
      nb_comma: 0,
      nb_semicolumn: 0,
      nb_dollar: 0,
      nb_space: 0,
      nb_www: 0,
      nb_com: 0,
      nb_dslash: 1,
      http_in_path: 1,
      https_token: 1,
      ratio_digits_url: 0.35,
      ratio_digits_host: 0.25,
      punycode: 1,
      port: 8080,
      tld_in_path: 1,
      tld_in_subdomain: 1,
      abnormal_subdomain: 1,
      nb_subdomains: 4,
      prefix_suffix: 1,
      random_domain: 1,
      shortening_service: 1,
      path_extension: 1,
      nb_redirection: 3,
      nb_external_redirection: 2,
      length_words_raw: 12,
      char_repeat: 4,
      shortest_words_raw: 2,
      shortest_word_host: 2,
      shortest_word_path: 2,
      longest_words_raw: 18,
      longest_word_host: 18,
      longest_word_path: 14,
      avg_words_raw: 8.0,
      avg_word_host: 8.0,
      avg_word_path: 7.0,
      phish_hints: 4,
      domain_in_brand: 1,
      brand_in_subdomain: 1,
      brand_in_path: 1,
      suspecious_tld: 1,
      statistical_report: 1,
      nb_hyperlinks: 5,
      ratio_intHyperlinks: 0.1,
      ratio_extHyperlinks: 0.9,
      ratio_nullHyperlinks: 4,
      nb_extCSS: 4,
      ratio_intRedirection: 1,
      ratio_extRedirection: 0.8,
      ratio_intErrors: 2,
      ratio_extErrors: 0.4,
      login_form: 1,
      external_favicon: 1,
      links_in_tags: 15.0,
      submit_email: 1,
      ratio_intMedia: 0.1,
      ratio_extMedia: 0.9,
      sfh: 1,
      iframe: 1,
      popup_window: 1,
      safe_anchor: 10.0,
      onmouseover: 1,
      right_clic: 1,
      empty_title: 1,
      domain_in_title: 0,
      domain_with_copyright: 0,
      whois_registered_domain: 0,
      domain_registration_length: 10,
      domain_age: 5,
      web_traffic: 0,
      dns_record: 0,
      google_index: 0,
      page_rank: 0,
    },
  },
  "phishing-email": {
    benign: {
      sender: "notifications@github.com",
      receiver: "analyst@netragraph.gov.in",
      date: "Mon, 31 Aug 2026 10:00:00 +0530",
      subject: "[NetraGraph] CI Pipeline Completed Successfully",
      body: "All automated regression tests and model verification suites have completed with exit code 0.",
      urls: 0,
    },
    threat: {
      sender: "security-alert@verify-banking-portal-secure.net",
      receiver: "target@netragraph.gov.in",
      date: "Mon, 31 Aug 2026 03:15:00 -0400",
      subject: "URGENT NOTICE: Immediate Account Suspension Pending Verification",
      body: "We detected unauthorized access from a suspicious IP address. Click here immediately to restore access: http://verify-banking-portal-secure.net/login",
      urls: 2,
    },
  },
};

export function LivePredictionLab({ models, onRefreshModels }: LivePredictionLabProps) {
  const [activeDomain, setActiveDomain] = useState<PredictionDomain>("intrusion");
  const [selectedModelName, setSelectedModelName] = useState<string>("");
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionResult, setPredictionResult] = useState<MLPredictionResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filter available models for the active domain
  const domainModels = models.filter((m) => {
    const task = (m.task_type || "").toLowerCase();
    const name = (m.model_name || "").toLowerCase();

    if (activeDomain === "intrusion") {
      return task.includes("intrusion") || name.includes("intrusion");
    }
    if (activeDomain === "phishing-url") {
      return (task.includes("url") || name.includes("url")) && !task.includes("web") && !name.includes("web");
    }
    if (activeDomain === "webpage-phishing") {
      return task.includes("web") || name.includes("web");
    }
    if (activeDomain === "phishing-email") {
      return task.includes("email") || name.includes("email");
    }
    return false;
  });

  // Current active or selected model
  const activeModel =
    domainModels.find((m) => m.model_name === selectedModelName) ||
    domainModels.find((m) => m.active) ||
    domainModels[0] ||
    null;

  // Sync selected model and form data when domain or models list changes
  useEffect(() => {
    if (domainModels.length > 0) {
      const target =
        domainModels.find((m) => m.model_name === selectedModelName) ||
        domainModels.find((m) => m.active) ||
        domainModels[0];

      setSelectedModelName(target.model_name);

      // Populate preset sample or empty schema fields
      const modelKey = target.model_name;
      const preset = PRESETS[modelKey] || PRESETS[activeDomain];
      if (preset && preset.benign) {
        setFormData({ ...preset.benign });
      } else {
        const initial: Record<string, any> = {};
        target.input_schema?.feature_names?.forEach((f) => {
          initial[f] = "";
        });
        setFormData(initial);
      }
    } else {
      setSelectedModelName("");
      setFormData({});
    }
    setPredictionResult(null);
    setErrorMsg(null);
  }, [activeDomain, models.length]);

  // When model selector changes within same domain
  const handleModelSelect = (modelName: string) => {
    setSelectedModelName(modelName);
    const target = domainModels.find((m) => m.model_name === modelName);
    if (target) {
      const preset = PRESETS[target.model_name] || PRESETS[activeDomain];
      if (preset && preset.benign) {
        setFormData({ ...preset.benign });
      } else {
        const initial: Record<string, any> = {};
        target.input_schema?.feature_names?.forEach((f) => {
          initial[f] = "";
        });
        setFormData(initial);
      }
    }
    setPredictionResult(null);
    setErrorMsg(null);
  };

  const handleInputChange = (featureName: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [featureName]: value,
    }));
  };

  const handleApplyPreset = (type: "benign" | "threat") => {
    const modelKey = activeModel?.model_name || activeDomain;
    const preset = PRESETS[modelKey] || PRESETS[activeDomain];
    if (preset && preset[type]) {
      setFormData({ ...preset[type] });
      toast.success(`${type === "benign" ? "Benign / Normal" : "Threat / Malicious"} Preset Applied`, {
        description: `Loaded authentic test telemetry for ${activeModel?.model_name || activeDomain}.`,
      });
    }
  };

  const handleRunPrediction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeModel) return;

    setIsPredicting(true);
    setErrorMsg(null);
    setPredictionResult(null);

    // Convert numeric inputs appropriately
    const payload: Record<string, any> = {};
    for (const [key, val] of Object.entries(formData)) {
      const expectedDtype = activeModel.input_schema?.dtypes?.[key] || "number";
      const isNum = expectedDtype.includes("int") || expectedDtype.includes("float") || expectedDtype === "number";

      if (val === "" || val === undefined) {
        payload[key] = isNum ? 0 : "";
      } else if (isNum && !isNaN(Number(val)) && typeof val === "string") {
        payload[key] = Number(val);
      } else {
        payload[key] = val;
      }
    }

    try {
      let res: MLPredictionResult;
      if (activeDomain === "intrusion") {
        res = await api.predictIntrusion(payload, activeModel.model_name);
      } else if (activeDomain === "phishing-url") {
        res = await api.predictPhishingUrl(payload, activeModel.model_name);
      } else if (activeDomain === "webpage-phishing") {
        res = await api.predictWebpagePhishing(payload, activeModel.model_name);
      } else {
        res = await api.predictPhishingEmail(payload, activeModel.model_name);
      }
      setPredictionResult(res);
      toast.success("Prediction Executed", {
        description: `Class: ${res.prediction} · Confidence: ${res.probability !== null ? (res.probability * 100).toFixed(1) + "%" : "Evaluated"}`,
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
        <div className="flex items-center gap-1.5 flex-wrap">
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
            <span>Phishing URL</span>
          </button>

          <button
            onClick={() => setActiveDomain("webpage-phishing")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold cursor-pointer transition-all ${
              activeDomain === "webpage-phishing"
                ? "bg-[#064E3B] text-white shadow-xs"
                : "text-[#64748B] hover:bg-[#E2E8F0] hover:text-[#0F172A]"
            }`}
          >
            <Globe className="size-3.5" />
            <span>Web Page Phishing</span>
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
            <span>Phishing Email</span>
          </button>
        </div>

        {/* Model Selector & Active Tag */}
        {domainModels.length > 0 && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-[#64748B] font-medium">Model:</span>
            {domainModels.length > 1 ? (
              <select
                value={selectedModelName}
                onChange={(e) => handleModelSelect(e.target.value)}
                className="rounded border border-[#D9E2EC] bg-white px-2 py-1 text-xs font-bold text-[#064E3B] focus:outline-none focus:ring-1 focus:ring-[#064E3B] cursor-pointer"
              >
                {domainModels.map((m) => (
                  <option key={m.model_name} value={m.model_name}>
                    {m.model_name} ({m.task_type || m.version})
                  </option>
                ))}
              </select>
            ) : (
              <span className="font-bold text-[#064E3B] bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                {activeModel?.model_name} ({activeModel?.version})
              </span>
            )}
          </div>
        )}
      </div>

      {/* Main Grid: Feature Input Form (Left) & Result Panel (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[#E2E8F0]">
        {/* Left 7 Columns: Dynamic Feature Form */}
        <div className="lg:col-span-7 p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between border-b border-[#E2E8F0] pb-2.5 gap-2">
            <div>
              <h4 className="text-sm font-bold text-[#0F172A] flex items-center gap-2">
                <Sliders className="size-4 text-[#064E3B]" />
                <span>Telemetry Input Parameters</span>
              </h4>
              <p className="text-xs text-[#64748B]">
                {activeModel
                  ? `${activeModel.model_name} (${activeModel.input_schema?.feature_names?.length || 0} features expected)`
                  : "No active model registered for this task domain."}
              </p>
            </div>

            {/* 1-Click Preset Test Buttons */}
            {activeModel && (
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => handleApplyPreset("benign")}
                  className="rounded border border-emerald-300 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-[#16A34A] hover:bg-emerald-100 transition-colors cursor-pointer"
                  title="Load a realistic normal/benign telemetry vector"
                >
                  Load Normal Sample
                </button>
                <button
                  type="button"
                  onClick={() => handleApplyPreset("threat")}
                  className="rounded border border-red-300 bg-red-50 px-2.5 py-1 text-[11px] font-semibold text-[#DC2626] hover:bg-red-100 transition-colors cursor-pointer"
                  title="Load a realistic attack/phishing telemetry vector"
                >
                  Load Threat Sample
                </button>
              </div>
            )}
          </div>

          {!activeModel ? (
            <div className="rounded-md border border-dashed border-[#E2E8F0] bg-[#F8FAFC] p-6 text-center text-xs text-[#64748B] space-y-2">
              <AlertTriangle className="size-6 text-[#EA580C] mx-auto" />
              <p className="font-semibold text-[#0F172A]">
                No Model Available for {activeDomain}
              </p>
              <p>
                Import a model artifact bundle or activate an existing version from the Model Registry below to unlock live inference.
              </p>
            </div>
          ) : (
            <form onSubmit={handleRunPrediction} className="space-y-4">
              {/* Dynamic Feature Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[380px] overflow-y-auto pr-1">
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
                <span className="text-[11px] text-[#64748B] font-mono">
                  POST /api/ml/predict/{activeDomain === "webpage-phishing" ? "webpage-phishing" : activeDomain}?model={activeModel.model_name}
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
                Fill telemetry parameters or click <strong>Load Sample</strong> and run inference to evaluate classification.
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
                      predictionResult.prediction.toLowerCase().includes("anomaly") ||
                      predictionResult.prediction === "1"
                        ? "bg-red-50 text-[#DC2626] border border-red-200"
                        : "bg-emerald-50 text-[#16A34A] border border-emerald-200"
                    }`}
                  >
                    {predictionResult.prediction.toLowerCase().includes("malicious") ||
                    predictionResult.prediction.toLowerCase().includes("attack") ||
                    predictionResult.prediction.toLowerCase().includes("phish") ||
                    predictionResult.prediction.toLowerCase().includes("anomaly") ||
                    predictionResult.prediction === "1"
                      ? "Threat Detected"
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
