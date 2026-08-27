import React from "react";
import { Lock } from "lucide-react";

export function SecurityPanel() {
  return (
    <div className="rounded-md border border-[#D9E2EC] bg-white p-5 text-xs select-none space-y-4 font-sans shadow-sm">
      {/* Header */}
      <div className="border-b border-[#E2E8F0] pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Lock className="size-4 text-[#065F46]" />
          <div>
            <h3 className="text-sm font-bold text-[#0F172A]">
              Role-Based Access Control (RBAC) & Security Governance
            </h3>
            <p className="text-xs text-[#64748B]">
              Statutory Access Control certified under IT Act Section 69B and NCRB Security Standard 4.1.
            </p>
          </div>
        </div>

        <span className="rounded bg-emerald-50 border border-emerald-200 px-2.5 py-1 text-xs font-semibold text-[#065F46]">
          TLS 1.3 · AES-256 GCM
        </span>
      </div>

      {/* RBAC Matrix Table */}
      <div className="rounded-md border border-[#D9E2EC] bg-white overflow-hidden text-xs">
        <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] px-3.5 py-2 text-xs font-bold text-[#0F172A]">
          Officer Role Permissions Matrix
        </div>
        <table className="w-full text-left">
          <thead className="border-b border-[#E2E8F0] bg-[#F8FAFC] text-[#64748B] text-[11px] font-semibold">
            <tr>
              <th className="px-3.5 py-2">Role</th>
              <th className="px-3.5 py-2">Graph Analysis</th>
              <th className="px-3.5 py-2">Entity Resolution</th>
              <th className="px-3.5 py-2">Evidence Sealing</th>
              <th className="px-3.5 py-2">Judicial Export</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0] text-[#0F172A]">
            <tr className="hover:bg-[#F8FAFC]">
              <td className="px-3.5 py-2.5 font-bold text-[#0F172A]">Superintendent / Admin</td>
              <td className="px-3.5 py-2.5 text-[#198754] font-medium">Full Access</td>
              <td className="px-3.5 py-2.5 text-[#198754] font-medium">Full Access</td>
              <td className="px-3.5 py-2.5 text-[#198754] font-medium">Full Access</td>
              <td className="px-3.5 py-2.5 text-[#198754] font-medium">Full Access</td>
            </tr>
            <tr className="hover:bg-[#F8FAFC]">
              <td className="px-3.5 py-2.5 font-bold text-[#065F46]">Investigating Officer (IO)</td>
              <td className="px-3.5 py-2.5 text-[#198754] font-medium">Full Access</td>
              <td className="px-3.5 py-2.5 text-[#198754] font-medium">Full Access</td>
              <td className="px-3.5 py-2.5 text-[#198754] font-medium">Full Access</td>
              <td className="px-3.5 py-2.5 text-[#198754] font-medium">Full Access</td>
            </tr>
            <tr className="hover:bg-[#F8FAFC]">
              <td className="px-3.5 py-2.5 font-bold text-[#F59E0B]">Cyber Cell Analyst</td>
              <td className="px-3.5 py-2.5 text-[#198754] font-medium">Full Access</td>
              <td className="px-3.5 py-2.5 text-[#047857] font-medium">Suggest Only</td>
              <td className="px-3.5 py-2.5 text-[#64748B]">Read Only</td>
              <td className="px-3.5 py-2.5 text-[#047857] font-medium">Draft Only</td>
            </tr>
            <tr className="hover:bg-[#F8FAFC]">
              <td className="px-3.5 py-2.5 font-bold text-[#64748B]">Judicial Auditor / Court Clerk</td>
              <td className="px-3.5 py-2.5 text-[#64748B]">Read Only</td>
              <td className="px-3.5 py-2.5 text-[#94A3B8]">No Access</td>
              <td className="px-3.5 py-2.5 text-[#065F46] font-medium">Verify Hash</td>
              <td className="px-3.5 py-2.5 text-[#94A3B8]">No Access</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
