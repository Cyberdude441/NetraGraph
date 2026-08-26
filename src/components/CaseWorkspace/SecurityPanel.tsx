import React from "react";
import { Lock, ShieldCheck, UserCheck, Key, Server, CheckCircle2 } from "lucide-react";

export function SecurityPanel() {
  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Lock className="size-4 text-emerald-400" />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
              Role-Based Access Control (RBAC) & Security Governance
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              Statutory Access Control certified under IT Act Section 69B and NCRB Security Standard 4.1.
            </p>
          </div>
        </div>

        <span className="rounded bg-emerald-950/60 border border-emerald-800 px-2.5 py-1 text-xs font-mono font-bold text-emerald-300">
          TLS 1.3 · AES-256 GCM
        </span>
      </div>

      {/* RBAC Matrix Table */}
      <div className="rounded border border-slate-800 bg-[#121820] overflow-hidden font-mono text-[11px]">
        <div className="border-b border-slate-800 bg-[#141A21] px-3 py-2 text-[10px] uppercase font-bold text-slate-300">
          User Role Permissions Matrix
        </div>
        <table className="w-full text-left">
          <thead className="border-b border-slate-800/80 bg-[#161D24] text-slate-500 text-[9px] uppercase">
            <tr>
              <th className="px-3 py-1.5">User Role</th>
              <th className="px-3 py-1.5">Graph Analysis</th>
              <th className="px-3 py-1.5">Entity Resolution</th>
              <th className="px-3 py-1.5">Evidence Sealing</th>
              <th className="px-3 py-1.5">Judicial Export</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            <tr className="hover:bg-[#161D24]">
              <td className="px-3 py-2 font-bold text-slate-100">Administrator</td>
              <td className="px-3 py-2 text-emerald-400">Full Access</td>
              <td className="px-3 py-2 text-emerald-400">Full Access</td>
              <td className="px-3 py-2 text-emerald-400">Full Access</td>
              <td className="px-3 py-2 text-emerald-400">Full Access</td>
            </tr>
            <tr className="hover:bg-[#161D24]">
              <td className="px-3 py-2 font-bold text-sky-300">Investigator (Active)</td>
              <td className="px-3 py-2 text-emerald-400">Full Access</td>
              <td className="px-3 py-2 text-emerald-400">Full Access</td>
              <td className="px-3 py-2 text-emerald-400">Full Access</td>
              <td className="px-3 py-2 text-emerald-400">Full Access</td>
            </tr>
            <tr className="hover:bg-[#161D24]">
              <td className="px-3 py-2 font-bold text-amber-300">Analyst</td>
              <td className="px-3 py-2 text-emerald-400">Full Access</td>
              <td className="px-3 py-2 text-emerald-400">Suggest Only</td>
              <td className="px-3 py-2 text-slate-500">Read Only</td>
              <td className="px-3 py-2 text-emerald-400">Draft Only</td>
            </tr>
            <tr className="hover:bg-[#161D24]">
              <td className="px-3 py-2 font-bold text-slate-400">Viewer / Auditor</td>
              <td className="px-3 py-2 text-slate-400">Read Only</td>
              <td className="px-3 py-2 text-slate-500">No Access</td>
              <td className="px-3 py-2 text-slate-400">Verify Hash</td>
              <td className="px-3 py-2 text-slate-500">No Access</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
