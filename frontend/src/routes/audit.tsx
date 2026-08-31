import { createFileRoute } from "@tanstack/react-router";
import { ShieldCheck, FileText, History, CheckCircle2 } from "lucide-react";
import { AppShell, Panel } from "@/components/AppShell";
import { INITIAL_GLOBAL_AUDIT_LOGS } from "@/services/auditService";

export const Route = createFileRoute("/audit")({
  head: () => ({
    meta: [
      { title: "Audit Trail — NetraGraph AI" },
      {
        name: "description",
        content: "Forensic audit trail, operational events, and cryptographic compliance history for the investigation system.",
      },
    ],
  }),
  component: AuditTrailPage,
});

function AuditTrailPage() {
  return (
    <AppShell
      title="Audit Trail & Compliance Ledger"
      subtitle="System Activity, Forensic Integrity, and Court-Ready Compliance History"
    >
      <div className="grid gap-4 lg:grid-cols-3">
        {[
          {
            label: "Validated Events",
            value: INITIAL_GLOBAL_AUDIT_LOGS.length,
            hint: "Signed and archived audit entries",
            icon: CheckCircle2,
          },
          {
            label: "Compliance Status",
            value: "100%",
            hint: "Section 65B ready",
            icon: ShieldCheck,
          },
          {
            label: "Last Sync",
            value: "2 mins ago",
            hint: "Immutable ledger checkpoint",
            icon: History,
          },
        ].map(({ label, value, hint, icon: Icon }) => (
          <div key={label} className="rounded border border-[var(--border-theme)] bg-[var(--card-bg)] p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">{label}</span>
              <Icon className="size-4 text-[var(--brand)]" />
            </div>
            <p className="mt-3 font-display text-2xl font-bold tracking-tight text-[var(--text-primary)]">{value}</p>
            <p className="mt-1 text-xs text-[var(--text-secondary)]">{hint}</p>
          </div>
        ))}
      </div>

      <Panel title="Forensic Audit Register" className="mt-4">
        <div className="space-y-3">
          {INITIAL_GLOBAL_AUDIT_LOGS.map((log) => (
            <div key={log.id} className="rounded border border-[var(--border-theme)] bg-[var(--card-bg)] p-3.5">
              <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] font-bold text-[var(--brand)]">{log.id}</span>
                    <span className="rounded border border-[var(--border-theme)] bg-[var(--panel - sec)] px-1.5 py-0.5 text-[10px] font-medium uppercase text-[var(--text-secondary)]">
                      {log.module}
                    </span>
                  </div>
                  <p className="mt-1 text-sm font-semibold text-[var(--text-primary)]">{log.action}</p>
                </div>
                <div className="text-xs text-[var(--text-secondary)]">
                  {new Date(log.timestamp).toLocaleString()}
                </div>
              </div>

              <div className="mt-2 flex flex-col gap-1 text-xs text-[var(--text-secondary)]">
                <p><span className="font-semibold text-[var(--text-primary)]">Officer:</span> {log.officerName} · {log.officerRole}</p>
                <p><span className="font-semibold text-[var(--text-primary)]">Details:</span> {log.details}</p>
                <p><span className="font-semibold text-[var(--text-primary)]">Source:</span> {log.ipAddress}</p>
                <p><span className="font-semibold text-[var(--text-primary)]">Verification Hash:</span> {log.verificationHash}</p>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </AppShell>
  );
}
