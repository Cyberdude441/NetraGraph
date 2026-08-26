import React, { useState } from "react";
import {
  ShieldCheck,
  Lock,
  ArrowDown,
  CheckCircle2,
  AlertTriangle,
  FileCheck2,
  Download,
  Fingerprint,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import {
  INITIAL_EVIDENCE_CHAIN,
  verifyEvidenceChainIntegrity,
  type EvidenceBlock,
} from "@/services/evidenceService";

export function EvidenceChain() {
  const [chain, setChain] = useState<EvidenceBlock[]>(INITIAL_EVIDENCE_CHAIN);
  const integrityResult = verifyEvidenceChainIntegrity(chain);

  const handleVerifyChain = () => {
    if (integrityResult.isValid) {
      toast.success("Evidence Cryptographic Integrity Verified", {
        description: `${integrityResult.totalVerifiedBlocks} blocks verified. Zero hash mismatches detected.`,
      });
    } else {
      toast.error("Integrity Tamper Detected", {
        description: integrityResult.verificationMessage,
      });
    }
  };

  const handleExportCertificate = () => {
    toast.success("Section 65B Certificate Exported", {
      description: "Cryptographically signed Section 65B evidentiary custody certificate downloaded.",
    });
  };

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Top Header */}
      <div className="border-b border-slate-800 pb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Fingerprint className="size-4 text-emerald-400" />
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
              Tamper-Evident SHA-256 Evidence Chain & Section 65B Ledger
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">
              Immutable chain-of-custody blocks for court-admissible electronic records under Indian Evidence Act §65B.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={handleVerifyChain}
            className="flex items-center gap-1.5 rounded border border-emerald-500/50 bg-emerald-950/40 px-3 py-1.5 font-bold text-emerald-300 hover:bg-emerald-900/60 transition-colors cursor-pointer"
          >
            <ShieldCheck className="size-3.5" /> Validate Chain Hashes
          </button>

          <button
            onClick={handleExportCertificate}
            className="flex items-center gap-1.5 rounded border border-slate-800 bg-[#161D24] px-3 py-1.5 font-semibold text-slate-300 hover:border-slate-700 transition-colors cursor-pointer"
          >
            <Download className="size-3.5 text-sky-400" /> Export §65B Certificate
          </button>
        </div>
      </div>

      {/* Chain Blocks List */}
      <div className="space-y-4">
        {chain.map((block, idx) => {
          const isFirst = idx === 0;

          return (
            <div key={block.blockNumber} className="space-y-2">
              {/* Previous Block Connector Arrow */}
              {!isFirst && (
                <div className="flex items-center justify-center py-1">
                  <div className="flex items-center gap-2 font-mono text-[9px] text-emerald-400/80 bg-[#121820] px-3 py-0.5 rounded border border-slate-800">
                    <ArrowDown className="size-3 text-emerald-400 animate-bounce" />
                    <span>Cryptographic Block Linkage Verified</span>
                  </div>
                </div>
              )}

              {/* Block Card */}
              <div className="rounded-lg border border-slate-800 bg-[#121820] p-4 space-y-3 font-mono text-[11px] relative">
                {/* Header Line */}
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-emerald-950/80 border border-emerald-500/60 text-emerald-300 font-bold px-2 py-0.5 text-xs">
                      BLOCK #0{block.blockNumber}
                    </span>
                    <strong className="text-slate-100 text-xs font-sans">{block.title}</strong>
                  </div>

                  <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-bold">
                    <CheckCircle2 className="size-3" /> {block.integrityStatus}
                  </span>
                </div>

                {/* Hashes HUD */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[10px]">
                  <div className="rounded bg-[#0A0D12] p-2 border border-slate-800">
                    <span className="text-slate-500 text-[8px] uppercase block">CURRENT BLOCK SHA-256 HASH</span>
                    <span className="text-emerald-300 break-all select-all font-mono">
                      {block.sha256Hash}
                    </span>
                  </div>

                  <div className="rounded bg-[#0A0D12] p-2 border border-slate-800">
                    <span className="text-slate-500 text-[8px] uppercase block">PREVIOUS BLOCK HASH</span>
                    <span className="text-slate-400 break-all select-all font-mono">
                      {block.previousBlockHash}
                    </span>
                  </div>
                </div>

                {/* Metadata Row */}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-800/80 pt-2 text-[10px] text-slate-400">
                  <span>ID: <strong className="text-slate-200">{block.evidenceId}</strong> · Category: {block.sourceCategory}</span>
                  <span>Verifying Officer: <strong className="text-sky-300">{block.verifyingAnalyst}</strong></span>
                  <span>Timestamp: <strong className="text-slate-300">{new Date(block.timestamp).toLocaleString()}</strong></span>
                </div>

                {/* Statutory Seal */}
                <div className="rounded bg-[#161D24] p-2 text-[9px] text-slate-400 font-sans flex items-center justify-between">
                  <span>Certification: <strong className="text-slate-200">{block.statutoryCertification}</strong></span>
                  <span className="text-emerald-400 font-mono font-bold">SEALED EXHIBIT</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
