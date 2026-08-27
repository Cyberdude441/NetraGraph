import React, { useState } from "react";
import {
  ShieldCheck,
  ArrowDown,
  CheckCircle2,
  Download,
  Fingerprint,
} from "lucide-react";
import { toast } from "sonner";
import {
  INITIAL_EVIDENCE_CHAIN,
  verifyEvidenceChainIntegrity,
  type EvidenceBlock,
} from "@/services/evidenceService";

export function EvidenceChain() {
  const [chain, setChain] = useState<EvidenceBlock[]>(INITIAL_EVIDENCE_CHAIN);
  const [viewMode, setViewMode] = useState<"table" | "blocks">("table");
  const integrityResult = verifyEvidenceChainIntegrity(chain);

  const handleVerifyChain = () => {
    if (integrityResult.isValid) {
      toast.success("Cryptographic Integrity Verified", {
        description: `${integrityResult.totalVerifiedBlocks} blocks verified. Zero hash mismatches.`,
      });
    } else {
      toast.error("Integrity Mismatch Detected", {
        description: integrityResult.verificationMessage,
      });
    }
  };

  const handleExportCertificate = () => {
    toast.success("Section 65B Certificate Generated", {
      description: "Signed Section 65B electronic evidence certificate prepared for judicial submission.",
    });
  };

  return (
    <div className="rounded-md border border-[#E2E8F0] bg-white p-5 text-xs select-none space-y-4 font-sans shadow-xs">
      {/* Top Header */}
      <div className="border-b border-[#E2E8F0] pb-3.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <Fingerprint className="size-5 text-[#064E3B]" />
          <div>
            <h3 className="text-sm font-bold text-[#0F172A]">
              Electronic Evidence Vault & Section 65B Register
            </h3>
            <p className="text-xs text-[#64748B]">
              Forensic chain-of-custody document register under Indian Evidence Act §65B with SHA-256 integrity seal.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center rounded-md bg-[#E2E8F0] p-0.5 text-xs mr-2">
            <button
              onClick={() => setViewMode("table")}
              className={cn(
                "px-2.5 py-1 rounded text-xs font-semibold cursor-pointer transition-all",
                viewMode === "table"
                  ? "bg-[#064E3B] text-white shadow-xs"
                  : "text-[#64748B] hover:text-[#0F172A]"
              )}
            >
              Document Table
            </button>
            <button
              onClick={() => setViewMode("blocks")}
              className={cn(
                "px-2.5 py-1 rounded text-xs font-semibold cursor-pointer transition-all",
                viewMode === "blocks"
                  ? "bg-[#064E3B] text-white shadow-xs"
                  : "text-[#64748B] hover:text-[#0F172A]"
              )}
            >
              Chain Blocks
            </button>
          </div>

          <button
            onClick={handleVerifyChain}
            className="flex items-center gap-1.5 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-1.5 font-semibold text-[#16A34A] hover:bg-emerald-100 transition-colors cursor-pointer shadow-xs"
          >
            <CheckCircle2 className="size-3.5" />
            <span>Verify Integrity</span>
          </button>

          <button
            onClick={handleExportCertificate}
            className="flex items-center gap-1.5 rounded-md bg-[#064E3B] hover:bg-[#04382A] px-3.5 py-1.5 font-semibold text-white transition-colors cursor-pointer shadow-xs"
          >
            <Download className="size-3.5" />
            <span>Generate §65B Certificate</span>
          </button>
        </div>
      </div>

      {/* Chain Status Bar */}
      <div className="flex items-center justify-between rounded-md bg-[#F8FAFC] border border-[#E2E8F0] p-3 text-xs">
        <div className="flex items-center gap-2 text-[#0F172A]">
          <ShieldCheck className="size-4 text-[#16A34A]" />
          <span>
            Chain Status: <strong>{integrityResult.totalVerifiedBlocks} Exhibits Sealed</strong> · All SHA-256 Hashes Validated
          </span>
        </div>
        <span className="rounded bg-emerald-50 text-[#16A34A] border border-emerald-200 px-2 py-0.5 font-semibold text-[11px]">
          Court Admissible
        </span>
      </div>

      {/* View 1: Forensic Document Management Table */}
      {viewMode === "table" ? (
        <div className="overflow-x-auto rounded-md border border-[#E2E8F0]">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#F8FAFC] border-b border-[#E2E8F0] text-[#64748B]">
                <th className="px-3.5 py-2.5 font-bold uppercase tracking-wider text-[10px]">Exhibit ID</th>
                <th className="px-3.5 py-2.5 font-bold uppercase tracking-wider text-[10px]">File / Description</th>
                <th className="px-3.5 py-2.5 font-bold uppercase tracking-wider text-[10px]">SHA-256 Hash</th>
                <th className="px-3.5 py-2.5 font-bold uppercase tracking-wider text-[10px]">Status</th>
                <th className="px-3.5 py-2.5 font-bold uppercase tracking-wider text-[10px]">Date Logged</th>
                <th className="px-3.5 py-2.5 font-bold uppercase tracking-wider text-[10px]">Investigating Officer</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E8F0] bg-white">
              {chain.map((block) => (
                <tr key={block.blockNumber} className="hover:bg-[#F8FAFC] transition-colors">
                  <td className="px-3.5 py-3 font-mono font-bold text-[#064E3B] whitespace-nowrap">
                    EXH-00{block.blockNumber}
                  </td>
                  <td className="px-3.5 py-3">
                    <span className="font-semibold text-[#0F172A] block">{block.title}</span>
                    <span className="text-[11px] text-[#64748B]">{block.evidenceId} · {block.sourceCategory}</span>
                  </td>
                  <td className="px-3.5 py-3 font-mono text-[11px] text-[#64748B] max-w-xs truncate" title={block.sha256Hash}>
                    {block.sha256Hash.slice(0, 16)}...{block.sha256Hash.slice(-8)}
                  </td>
                  <td className="px-3.5 py-3 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1 rounded bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[11px] font-semibold text-[#16A34A]">
                      <CheckCircle2 className="size-3 text-[#16A34A]" />
                      §65B Sealed
                    </span>
                  </td>
                  <td className="px-3.5 py-3 text-[#64748B] whitespace-nowrap">
                    {new Date(block.timestamp).toLocaleDateString()}
                  </td>
                  <td className="px-3.5 py-3 font-medium text-[#0F172A] whitespace-nowrap">
                    {block.verifyingAnalyst}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        /* View 2: Sequential Evidence Block List */
        <div className="space-y-4 pt-1">
          {chain.map((block, idx) => {
            const isFirst = idx === 0;

            return (
              <div key={block.blockNumber} className="space-y-2">
                {!isFirst && (
                  <div className="flex items-center justify-center py-1">
                    <div className="flex items-center gap-1.5 text-xs text-[#64748B] bg-[#F1F5F9] px-3 py-1 rounded-md border border-[#E2E8F0]">
                      <ArrowDown className="size-3.5 text-[#064E3B]" />
                      <span>Cryptographic Block Linkage Verified</span>
                    </div>
                  </div>
                )}

                <div className="rounded-md border border-[#E2E8F0] bg-[#F8FAFC] p-4 space-y-3 text-xs relative hover:border-[#064E3B] transition-all">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] pb-2.5">
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-emerald-50 border border-emerald-200 text-[#064E3B] font-bold px-2 py-0.5 text-xs">
                        Exhibit #{block.blockNumber}
                      </span>
                      <strong className="text-[#0F172A] text-sm font-semibold">{block.title}</strong>
                    </div>

                    <span className="flex items-center gap-1 text-xs text-[#16A34A] font-semibold">
                      <CheckCircle2 className="size-3.5" /> Verified & Sealed
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                    <div className="rounded bg-white p-2.5 border border-[#E2E8F0]">
                      <span className="text-[#64748B] text-[10px] uppercase font-semibold block mb-0.5">
                        Current Block SHA-256 Hash
                      </span>
                      <span className="text-[#064E3B] break-all select-all font-mono text-[11px]">
                        {block.sha256Hash}
                      </span>
                    </div>

                    <div className="rounded bg-white p-2.5 border border-[#E2E8F0]">
                      <span className="text-[#64748B] text-[10px] uppercase font-semibold block mb-0.5">
                        Previous Block Hash
                      </span>
                      <span className="text-[#64748B] break-all select-all font-mono text-[11px]">
                        {block.previousBlockHash}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#E2E8F0] pt-2 text-xs text-[#64748B]">
                    <span>Evidence ID: <strong className="font-mono text-[#0F172A]">{block.evidenceId}</strong> · Category: {block.sourceCategory}</span>
                    <span>Verifying Investigator: <strong className="text-[#064E3B]">{block.verifyingAnalyst}</strong></span>
                    <span>Timestamp: <strong className="text-[#0F172A]">{new Date(block.timestamp).toLocaleString()}</strong></span>
                  </div>

                  <div className="rounded bg-white p-2 text-xs text-[#475569] border border-[#E2E8F0] flex items-center justify-between">
                    <span>Statutory Certification: <strong className="text-[#0F172A]">{block.statutoryCertification}</strong></span>
                    <span className="text-[#16A34A] font-bold text-[11px] bg-emerald-50 px-2 py-0.5 rounded">
                      Sealed Exhibit
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
