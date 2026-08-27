import { createFileRoute, Link } from "@tanstack/react-router";
import { Fingerprint, Lock, ShieldCheck, User, KeyRound, Shield, Building2 } from "lucide-react";
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
            <h2 className="text-xl font-bold text-[#111827]">Officer Sign-In</h2>
            <p className="mt-1 text-xs text-[#64748B]">
              Enter your officer badge credentials and cryptographic token.
            </p>
          </div>

          <form
            className="mt-6 space-y-4"
            onSubmit={(e) => e.preventDefault()}
          >
            <div>
              <label className="block text-xs font-semibold text-[#111827] mb-1.5">
                Officer Service ID / PEN
              </label>
              <div className="flex items-center gap-2 rounded-md border border-[#E5E7EB] bg-[#F8FAF8] px-3.5 py-2.5 text-xs text-[#111827] focus-within:border-[#16A34A] focus-within:bg-white focus-within:ring-1 focus-within:ring-[#16A34A]">
                <User className="size-4 text-[#64748B]" />
                <input
                  defaultValue="IN-BOSE-4417"
                  className="w-full bg-transparent text-xs font-mono font-semibold outline-none text-[#111827]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#111827] mb-1.5">
                Passphrase / Token Pin
              </label>
              <div className="flex items-center gap-2 rounded-md border border-[#E5E7EB] bg-[#F8FAF8] px-3.5 py-2.5 text-xs text-[#111827] focus-within:border-[#16A34A] focus-within:bg-white focus-within:ring-1 focus-within:ring-[#16A34A]">
                <Lock className="size-4 text-[#64748B]" />
                <input
                  type="password"
                  defaultValue="netragraph-secure"
                  className="w-full bg-transparent text-xs font-mono font-semibold outline-none text-[#111827]"
                />
              </div>
            </div>

            {/* Token Badge */}
            <div className="flex items-center justify-between rounded-md border border-emerald-200 bg-emerald-50 p-2.5 text-xs">
              <div className="flex items-center gap-2 text-[#16A34A] font-semibold">
                <Fingerprint className="size-4 text-[#16A34A]" />
                <span>Security Token Verified</span>
              </div>
              <span className="text-xs font-medium text-[#16A34A]">Active</span>
            </div>

            <Link
              to="/dashboard"
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-md bg-[#064E3B] hover:bg-[#04382A] px-4 py-3 text-xs font-semibold text-white transition-all shadow-xs cursor-pointer"
            >
              <KeyRound className="size-4" />
              Access Investigation Portal
            </Link>
          </form>

          <div className="mt-6 border-t border-[#E5E7EB] pt-4 text-center text-xs text-[#64748B]">
            Government of India · Ministry of Home Affairs · Cyber Crime Cell
          </div>
        </div>
      </section>
    </div>
  );
}
