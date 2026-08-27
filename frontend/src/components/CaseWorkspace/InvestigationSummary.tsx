import React from "react";
import {
  FileText,
  ShieldCheck,
  Share2,
  Repeat,
} from "lucide-react";

interface InvestigationSummaryProps {
  onNavigateModule?: (route: string) => void;
}

export function InvestigationSummary({ onNavigateModule }: InvestigationSummaryProps) {
  return (
    <div className="rounded-md border border-[#D9E2EC] bg-white p-5 text-xs select-none space-y-4 font-sans shadow-sm">
      {/* Header */}
      <div className="border-b border-[#E2E8F0] pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="size-4 text-[#065F46]" />
          <h3 className="text-sm font-bold text-[#0F172A]">
            Executive Investigative Summary & Cross-Module Intelligence
          </h3>
        </div>

        <span className="rounded bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 text-xs text-[#198754] font-semibold">
          85% Case Maturity
        </span>
      </div>

      {/* Synthesis Narrative */}
      <div className="rounded-md border border-emerald-100 bg-emerald-50/60 p-4 text-[#0F172A] leading-relaxed text-xs">
        <strong className="text-[#065F46] font-semibold">Lead Case Synopsis: </strong>
        Case <strong>CASE-2026-N09</strong> centers on an inter-state cyber extortion and hawala syndicate. Operatives operated illegal VoIP call-center infrastructure in Sector 62 Noida, synchronized OTP relays via a 128-channel GSM SIM farm in Bhubaneswar, and layered ₹1.54 Cr in extortion proceeds through ICICI mule accounts and Mumbai OTC crypto desks.
      </div>

      {/* Findings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 text-xs">
        {/* Finding 1 */}
        <div className="rounded-md border border-[#D9E2EC] bg-[#F8FAFC] p-3.5 space-y-1.5 hover:border-[#065F46] transition-all">
          <div className="flex items-center gap-1.5 text-[#065F46] font-semibold text-xs">
            <Share2 className="size-4" /> Most Connected Entity
          </div>
          <p className="text-[#475569] leading-tight">
            Vikramaditya Rawat confirmed as primary kingpin with 14 direct connections (Rank #1).
          </p>
        </div>

        {/* Finding 2 */}
        <div className="rounded-md border border-[#D9E2EC] bg-[#F8FAFC] p-3.5 space-y-1.5 hover:border-[#DC3545] transition-all">
          <div className="flex items-center gap-1.5 text-[#DC3545] font-semibold text-xs">
            <Repeat className="size-4" /> Detected Transaction Loops
          </div>
          <p className="text-[#475569] leading-tight">
            4-hop circular fund recycling pattern verified across 3 mule bank accounts.
          </p>
        </div>

        {/* Finding 3 */}
        <div className="rounded-md border border-[#D9E2EC] bg-[#F8FAFC] p-3.5 space-y-1.5 hover:border-[#198754] transition-all">
          <div className="flex items-center gap-1.5 text-[#198754] font-semibold text-xs">
            <ShieldCheck className="size-4" /> Evidence Vault
          </div>
          <p className="text-[#475569] leading-tight">
            4 SHA-256 evidence blocks sealed and certified under Section 65B compliance.
          </p>
        </div>
      </div>
    </div>
  );
}
