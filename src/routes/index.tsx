import { createFileRoute, Link } from "@tanstack/react-router";
import { Fingerprint, Lock, ShieldCheck, User, KeyRound, Terminal, Shield, Sun, Moon } from "lucide-react";
import { NetraLogo } from "@/components/brand/NetraLogo";
import { useTheme } from "@/lib/theme";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Authentication — NetraGraph AI" },
      {
        name: "description",
        content:
          "Enterprise Intelligence Console Access for NetraGraph AI Criminal Intelligence Management System.",
      },
      { property: "og:title", content: "Authentication — NetraGraph AI" },
      {
        property: "og:description",
        content: "Enterprise intelligence console for authorized defense and law enforcement analysts.",
      },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <div className="relative min-h-screen bg-[var(--app-bg)] text-[var(--text-primary)] grid lg:grid-cols-2 font-sans transition-colors duration-200">
      {/* Top right theme button */}
      <div className="absolute top-4 right-4 z-20">
        <button
          type="button"
          onClick={toggleTheme}
          title={isDark ? "Switch to light mode" : "Switch to dark mode"}
          className="flex size-8 items-center justify-center rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--brand)] transition-all cursor-pointer shadow-xs"
        >
          {isDark ? <Sun className="size-4 text-[#FFB02E]" /> : <Moon className="size-4 text-[#2563EB]" />}
        </button>
      </div>

      {/* Left Column: Intelligence System Dossier */}
      <section className="relative hidden flex-col justify-between p-12 lg:flex border-r border-[var(--border-theme)] bg-[var(--sidebar-bg)]">
        <div>
          <NetraLogo size={32} />
          
          <div className="mt-16 max-w-lg">
            <div className="inline-flex items-center gap-2 rounded bg-[var(--brand-active)] border border-[var(--border-theme)] px-3 py-1 text-xs font-semibold text-[var(--brand)] uppercase tracking-wider">
              <Shield className="size-3.5 text-[var(--brand)]" />
              Criminal Network Intelligence Infrastructure
            </div>

            <h1 className="mt-6 text-3xl font-bold tracking-tight text-[var(--text-primary)] xl:text-4xl leading-snug font-display">
              Disrupt organized crime.
              <br />
              <span className="text-[var(--brand)]">Map hidden criminal networks.</span>
            </h1>

            <p className="mt-4 text-sm text-[var(--text-secondary)] leading-relaxed">
              Unified graph reasoning, entity resolution, and AI-assisted link analysis for defense intelligence, financial investigation, and law enforcement units.
            </p>

            {/* System Telemetry Metrics */}
            <div className="mt-10 grid grid-cols-3 gap-3">
              {[
                { value: "47", label: "Syndicates", hint: "9 cross-border" },
                { value: "1,482", label: "Active Cases", hint: "12 state districts" },
                { value: "128", label: "Monitored Targets", hint: "Threat score > 80" },
              ].map((stat) => (
                <div key={stat.label} className="rounded border border-[var(--border-theme)] bg-[var(--card-bg)] p-3.5 shadow-sm">
                  <span className="block font-display text-2xl font-bold text-[var(--text-primary)]">
                    {stat.value}
                  </span>
                  <span className="block text-xs font-semibold text-[var(--brand)] mt-1">
                    {stat.label}
                  </span>
                  <span className="block text-[11px] text-[var(--text-secondary)] mt-0.5">
                    {stat.hint}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Audit Notice */}
        <div className="border-t border-[var(--divider)] pt-4 text-xs text-[var(--text-secondary)] space-y-1">
          <p className="flex items-center gap-2 text-[var(--text-primary)] font-medium">
            <ShieldCheck className="size-4 text-[var(--success)]" />
            Official Secrets Act §5 & IT Act §69B Enforced
          </p>
          <p>
            All console activity, graph queries, and dossier extractions are cryptographically audited.
          </p>
        </div>
      </section>

      {/* Right Column: Secure Analyst Terminal */}
      <section className="relative flex items-center justify-center p-6 sm:p-12 bg-[var(--app-bg)]">
        <div className="w-full max-w-md rounded border border-[var(--border-theme)] bg-[var(--panel-bg)] p-8 shadow-2xl">
          <div className="flex items-center justify-between border-b border-[var(--divider)] pb-4">
            <div className="flex items-center gap-2 text-xs font-semibold text-[var(--brand)] uppercase tracking-wider">
              <ShieldCheck className="size-4 text-[var(--success)]" />
              Secure Analyst Authentication
            </div>
            <span className="font-mono text-xs text-[var(--text-secondary)]">NODE: KOL-01</span>
          </div>

          <div className="mt-6">
            <h2 className="text-xl font-bold text-[var(--text-primary)] tracking-tight font-display">Analyst Sign-In</h2>
            <p className="mt-1 text-xs text-[var(--text-secondary)]">
              Provide your officer badge identifier and security token to initialize console.
            </p>
          </div>

          <form
            className="mt-6 space-y-4"
            onSubmit={(e) => e.preventDefault()}
          >
            <div>
              <label className="block text-xs font-medium text-[var(--text-primary)] mb-1.5">
                Officer Service ID
              </label>
              <div className="flex items-center gap-2 rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-2 text-xs text-[var(--text-primary)] focus-within:border-[var(--brand)]">
                <User className="size-4 text-[var(--text-secondary)]" />
                <input
                  defaultValue="IN-BOSE-4417"
                  className="w-full bg-transparent text-xs font-mono outline-none text-[var(--text-primary)]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-primary)] mb-1.5">
                Security Token / Passphrase
              </label>
              <div className="flex items-center gap-2 rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-2 text-xs text-[var(--text-primary)] focus-within:border-[var(--brand)]">
                <Lock className="size-4 text-[var(--text-secondary)]" />
                <input
                  type="password"
                  defaultValue="netragraph-secure"
                  className="w-full bg-transparent text-xs font-mono outline-none text-[var(--text-primary)]"
                />
              </div>
            </div>

            {/* Hardware Token / Biometric Indicator */}
            <div className="flex items-center justify-between rounded border border-[var(--success)]/30 bg-[var(--success)]/10 p-2.5 text-xs">
              <div className="flex items-center gap-2 text-[var(--success)] font-medium">
                <Fingerprint className="size-4 text-[var(--success)]" />
                <span>RSA Hard Token Verified</span>
              </div>
              <span className="text-[11px] text-[var(--text-secondary)]">Audited</span>
            </div>

            <Link
              to="/dashboard"
              className="mt-4 flex w-full items-center justify-center gap-2 rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)] transition-all hover:border-[var(--brand)] hover:text-[var(--brand)] shadow-sm cursor-pointer"
            >
              <KeyRound className="size-3.5 text-[var(--brand)]" />
              Authorize Intelligence Session
            </Link>
          </form>

          <div className="mt-6 border-t border-[var(--divider)] pt-4 text-center text-xs text-[var(--text-secondary)]">
            NetraGraph Intel Core v2.4.0 · Level-4 Authorized
          </div>
        </div>
      </section>
    </div>
  );
}
