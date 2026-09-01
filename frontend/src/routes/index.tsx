import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import {
  Fingerprint,
  Mail,
  ShieldCheck,
  KeyRound,
  Shield,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  ArrowLeft,
  Loader2,
} from "lucide-react";
import { NetraLogo } from "@/components/brand/NetraLogo";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Officer Login — NetraGraph Crime Investigation Portal" },
      {
        name: "description",
        content:
          "Law Enforcement & Intelligence Officer Access Portal — NetraGraph AI Investigation Platform.",
      },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<"EMAIL" | "OTP">("EMAIL");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  // Timer states
  const [countdown, setCountdown] = useState(300); // 5 minutes OTP expiry
  const [cooldown, setCooldown] = useState(0); // 60s resend cooldown

  // Cooldown & countdown tick
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (step === "OTP") {
      timer = setInterval(() => {
        setCountdown((prev) => (prev > 0 ? prev - 1 : 0));
        setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [step]);

  const handleRequestOtp = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);
    setInfoMessage(null);

    const normEmail = email.trim().toLowerCase();
    if (!normEmail || !normEmail.includes("@")) {
      setError("Please enter a valid Gmail address.");
      return;
    }

    if (!normEmail.endsWith("@gmail.com") && !normEmail.endsWith("@googlemail.com")) {
      setError("Access is restricted to authorized @gmail.com accounts.");
      return;
    }

    if (cooldown > 0) {
      setError(`Please wait ${cooldown}s before requesting another OTP.`);
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/auth/request-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: normEmail }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Unable to dispatch OTP. Please try again.");
      } else {
        setStep("OTP");
        setCountdown(300);
        setCooldown(60);
        setOtp(["", "", "", "", "", ""]);
        setInfoMessage("OTP sent to your email.");
      }
    } catch (err: any) {
      setError("Network error connecting to NetraGraph authentication gateway.");
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index: number, val: string) => {
    // Handle paste of 6-digit code
    if (val.length === 6 && /^\d+$/.test(val)) {
      const digits = val.split("").slice(0, 6);
      setOtp(digits);
      const lastInput = document.getElementById("otp-input-5");
      lastInput?.focus();
      return;
    }

    if (!/^\d*$/.test(val)) return;
    const newOtp = [...otp];
    newOtp[index] = val.slice(-1);
    setOtp(newOtp);

    // Auto-advance to next input box
    if (val && index < 5) {
      const nextInput = document.getElementById(`otp-input-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-input-${index - 1}`);
      prevInput?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text").trim();
    if (/^\d{6}$/.test(pastedData)) {
      setOtp(pastedData.split(""));
      const lastInput = document.getElementById("otp-input-5");
      lastInput?.focus();
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const otpCode = otp.join("");
    if (otpCode.length !== 6) {
      setError("Please enter the complete 6-digit verification code.");
      return;
    }

    if (countdown === 0) {
      setError("OTP code has expired. Please request a new code.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          otp: otpCode,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Invalid or expired verification code.");
      } else {
        // Store session token in localStorage
        if (data.access_token) {
          localStorage.setItem("netragraph_token", data.access_token);
        }
        if (data.user) {
          localStorage.setItem("netragraph_user", JSON.stringify(data.user));
        }
        navigate({ to: "/dashboard" });
      }
    } catch (err) {
      setError("Network error communicating with authentication service.");
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  return (
    <div className="relative min-h-screen bg-[#F8FAF8] text-[#111827] grid lg:grid-cols-12 font-sans">
      {/* Left Column: Official Portal Banner (5 cols) */}
      <section className="relative hidden flex-col justify-between p-12 lg:flex lg:col-span-5 border-r border-[#064E3B] bg-[#064E3B] text-white">
        <div>
          <div className="flex items-center gap-3">
            <NetraLogo size={36} inverted />
            <div>
              <span className="text-xs uppercase tracking-widest text-[#86EFAC] font-semibold block">
                Government of India · Law Enforcement
              </span>
              <span className="text-sm font-bold text-white tracking-wide">
                Cyber Crime Investigation Division
              </span>
            </div>
          </div>

          <div className="mt-20 max-w-md">
            <div className="inline-flex items-center gap-2 rounded-md bg-white/10 border border-white/20 px-3 py-1 text-xs font-semibold text-white">
              <Shield className="size-3.5 text-amber-300" />
              National Intelligence Portal
            </div>

            <h1 className="mt-6 text-2xl font-bold tracking-tight text-white xl:text-3xl leading-snug">
              NetraGraph Unified Case & Network Intelligence Platform
            </h1>

            <p className="mt-4 text-xs text-emerald-100/80 leading-relaxed">
              Standardized crime syndicate tracking, financial link analysis, Section 65B compliant electronic evidence registers, and AI-assisted investigation workflows for authorized law enforcement personnel.
            </p>

            {/* Quick Metrics */}
            <div className="mt-8 grid grid-cols-3 gap-3">
              {[
                { value: "14", label: "Active Dockets" },
                { value: "105", label: "Tracked Entities" },
                { value: "100%", label: "Court Compliance" },
              ].map((stat) => (
                <div key={stat.label} className="rounded-md border border-white/15 bg-white/5 p-3 text-center">
                  <span className="block text-xl font-bold text-white">
                    {stat.value}
                  </span>
                  <span className="block text-[11px] text-[#86EFAC] font-medium mt-0.5">
                    {stat.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Notice */}
        <div className="border-t border-white/15 pt-4 text-xs text-emerald-200/80 space-y-1">
          <p className="flex items-center gap-2 text-white font-semibold">
            <ShieldCheck className="size-4 text-[#22C55E]" />
            Official Secrets Act §5 & IT Act §69B Protected
          </p>
          <p className="text-[11px]">
            Unauthorized access is strictly prohibited and subject to legal prosecution.
          </p>
        </div>
      </section>

      {/* Right Column: Officer Sign-In Form (7 cols) */}
      <section className="relative flex items-center justify-center p-6 sm:p-12 lg:col-span-7 bg-[#F8FAF8]">
        <div className="w-full max-w-md rounded-md border border-[#E5E7EB] bg-white p-8 shadow-xs">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#E5E7EB] pb-4">
            <div className="flex items-center gap-2 text-xs font-bold text-[#064E3B]">
              <ShieldCheck className="size-4 text-[#16A34A]" />
              Authorized Officer Authentication
            </div>
            <span className="text-xs font-semibold text-[#64748B]">SEC-PORTAL-IN</span>
          </div>

          <div className="mt-6">
            <h2 className="text-xl font-bold text-[#111827]">
              {step === "EMAIL" ? "Enter your Gmail address" : "Cryptographic OTP Verification"}
            </h2>
            <p className="mt-1 text-xs text-[#64748B]">
              {step === "EMAIL"
                ? "Provide your authorized Gmail address to receive your authentication code."
                : `Enter the 6-digit cryptographic code dispatched to ${email}`}
            </p>
          </div>

          {/* Feedback Alerts */}
          {error && (
            <div className="mt-4 flex items-start gap-2 rounded-md bg-red-50 border border-red-200 p-3 text-xs text-red-700">
              <AlertCircle className="size-4 shrink-0 mt-0.5 text-red-500" />
              <span>{error}</span>
            </div>
          )}

          {infoMessage && (
            <div className="mt-4 flex items-start gap-2 rounded-md bg-emerald-50 border border-emerald-200 p-3 text-xs text-emerald-800">
              <CheckCircle2 className="size-4 shrink-0 mt-0.5 text-emerald-600" />
              <span>{infoMessage}</span>
            </div>
          )}

          {/* Step 1: Email Form */}
          {step === "EMAIL" && (
            <form className="mt-6 space-y-4" onSubmit={handleRequestOtp}>
              <div>
                <label className="block text-xs font-semibold text-[#111827] mb-1.5">
                  Enter your Gmail address
                </label>
                <div className="flex items-center gap-2 rounded-md border border-[#E5E7EB] bg-[#F8FAF8] px-3.5 py-2.5 text-xs text-[#111827] focus-within:border-[#16A34A] focus-within:bg-white focus-within:ring-1 focus-within:ring-[#16A34A]">
                  <Mail className="size-4 text-[#64748B]" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="yourname@gmail.com"
                    required
                    className="w-full bg-transparent text-xs font-mono font-semibold outline-none text-[#111827]"
                  />
                </div>
              </div>

              {/* Security Policy Badge */}
              <div className="flex items-center justify-between rounded-md border border-emerald-200 bg-emerald-50 p-2.5 text-xs">
                <div className="flex items-center gap-2 text-[#16A34A] font-semibold">
                  <Fingerprint className="size-4 text-[#16A34A]" />
                  <span>Gmail OTP Security Protected</span>
                </div>
                <span className="text-xs font-medium text-[#16A34A]">Active</span>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-md bg-[#064E3B] hover:bg-[#04382A] px-4 py-3 text-xs font-semibold text-white transition-all shadow-xs cursor-pointer disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <KeyRound className="size-4" />
                )}
                <span>Send OTP</span>
              </button>
            </form>
          )}

          {/* Step 2: 6-Digit OTP Form */}
          {step === "OTP" && (
            <form className="mt-6 space-y-4" onSubmit={handleVerifyOtp}>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-semibold text-[#111827]">
                    6-Digit Verification Code
                  </label>
                  <span className={`text-xs font-mono font-semibold ${countdown < 60 ? "text-red-600" : "text-emerald-700"}`}>
                    Expires in: {formatTime(countdown)}
                  </span>
                </div>

                <div className="flex justify-between gap-2">
                  {otp.map((digit, idx) => (
                    <input
                      key={idx}
                      id={`otp-input-${idx}`}
                      type="text"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOtpChange(idx, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(idx, e)}
                      onPaste={handlePaste}
                      autoFocus={idx === 0}
                      className="size-12 rounded-md border border-[#E5E7EB] bg-[#F8FAF8] text-center font-mono text-lg font-bold text-[#111827] focus:border-[#16A34A] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#16A34A]"
                    />
                  ))}
                </div>
              </div>

              {/* Resend & Change Email Actions */}
              <div className="flex items-center justify-between pt-2 text-xs">
                <button
                  type="button"
                  onClick={() => setStep("EMAIL")}
                  className="flex items-center gap-1 text-[#64748B] hover:text-[#111827]"
                >
                  <ArrowLeft className="size-3.5" />
                  <span>Change Email</span>
                </button>

                <button
                  type="button"
                  disabled={cooldown > 0 || loading}
                  onClick={() => handleRequestOtp()}
                  className="flex items-center gap-1 font-semibold text-[#064E3B] hover:underline disabled:text-[#94A3B8] disabled:no-underline"
                >
                  <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
                  <span>{cooldown > 0 ? `Resend code in ${cooldown}s` : "Resend OTP"}</span>
                </button>
              </div>

              <button
                type="submit"
                disabled={loading || otp.join("").length !== 6}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-md bg-[#064E3B] hover:bg-[#04382A] px-4 py-3 text-xs font-semibold text-white transition-all shadow-xs cursor-pointer disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <ShieldCheck className="size-4" />
                )}
                <span>Verify & Access Portal</span>
              </button>
            </form>
          )}

          <div className="mt-6 border-t border-[#E5E7EB] pt-4 text-center text-xs text-[#64748B]">
            Government of India · Ministry of Home Affairs · Cyber Crime Cell
          </div>
        </div>
      </section>
    </div>
  );
}
