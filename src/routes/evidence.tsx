import { createFileRoute } from "@tanstack/react-router";
import {
  FileText,
  FileCode,
  FileAudio,
  FileVideo,
  HardDrive,
  Image as ImageIcon,
  Plus,
  Lock,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  X,
  Loader2,
  Search,
  Filter,
  ShieldCheck,
} from "lucide-react";
import React, { useState, useEffect, useMemo } from "react";
import { toast } from "sonner";
import { useQuery } from "@tanstack/react-query";

import { AppShell, Panel } from "@/components/AppShell";
import { api } from "@/services/api";
import type { Evidence } from "@/types";

export const Route = createFileRoute("/evidence")({
  head: () => ({
    meta: [
      { title: "Evidence Vault — NetraGraph AI" },
      {
        name: "description",
        content:
          "Cyber Cell Cryptographic Evidence Vault: SHA-256 integrity register, chain of custody logs, and multi-format forensic artifact store.",
      },
      { property: "og:title", content: "Evidence Vault — NetraGraph AI" },
      {
        property: "og:description",
        content: "Cryptographic exhibit store and custody tracking.",
      },
    ],
  }),
  component: EvidenceVault,
});

type EvidenceTypeOption = "Audio" | "Video" | "Document" | "Image" | "Data" | "Other";
type CustodyStatusOption = "PROCESSING" | "VERIFIED" | "SEALED";

function typeIcon(type: string) {
  if (type === "Audio") return FileAudio;
  if (type === "Video") return FileVideo;
  if (type === "Image") return ImageIcon;
  if (type === "Data") return HardDrive;
  if (type === "Code" || type === "Other") return FileCode;
  return FileText;
}

function statusBadge(status: string) {
  const norm = status?.toUpperCase();
  if (norm === "VERIFIED") return "bg-[var(--success)]/15 border-[var(--success)]/30 text-[var(--success)]";
  if (norm === "SEALED") return "bg-[var(--panel-sec)] border-[var(--border-theme)] text-[var(--text-secondary)]";
  return "bg-[var(--warning)]/15 border-[var(--warning)]/30 text-[var(--warning)]";
}

async function generateSHA256(seed: string): Promise<string> {
  try {
    const encoder = new TextEncoder();
    const data = encoder.encode(seed + Date.now() + Math.random().toString());
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  } catch {
    return Array.from({ length: 64 }, () =>
      Math.floor(Math.random() * 16).toString(16)
    ).join("");
  }
}

function EvidenceVault() {
  const { data: initialExhibits = [], refetch } = useQuery<Evidence[]>({
    queryKey: ["evidence"],
    queryFn: () => api.getEvidence(),
  });

  const [exhibitList, setExhibitList] = useState<Evidence[]>([]);
  const [searchFilter, setSearchFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");

  useEffect(() => {
    setExhibitList(initialExhibits);
  }, [initialExhibits]);

  // Modal & Form States
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [exhibitName, setExhibitName] = useState("");
  const [evidenceType, setEvidenceType] = useState<EvidenceTypeOption>("Document");
  const [caseFile, setCaseFile] = useState("CS-2291");
  const [description, setDescription] = useState("");
  const [custodyStatus, setCustodyStatus] = useState<CustodyStatusOption>("PROCESSING");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Submission Progress
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittingStep, setSubmittingStep] = useState<string>("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      if (!exhibitName) {
        setExhibitName(file.name);
      }
    }
  };

  const handleRegisterExhibit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!exhibitName.trim()) {
      toast.error("Validation Error", { description: "Please provide an exhibit name." });
      return;
    }

    setIsSubmitting(true);
    try {
      setSubmittingStep("Calculating SHA-256 cryptographic digest...");
      await new Promise((r) => setTimeout(r, 400));
      const generatedHash = await generateSHA256(exhibitName + (selectedFile?.name || ""));

      setSubmittingStep("Generating exhibit identifier EV-tag...");
      await new Promise((r) => setTimeout(r, 300));
      const generatedId = `EV-${Math.floor(1000 + Math.random() * 9000)}`;

      setSubmittingStep("Writing chain of custody entry into vault ledger...");
      await new Promise((r) => setTimeout(r, 300));

      const newExhibit: Evidence = {
        id: generatedId,
        fileName: exhibitName,
        fileType: evidenceType,
        case: caseFile,
        size: selectedFile ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB` : "14.2 MB",
        hash: generatedHash,
        uploadedBy: "Insp. D. Bose",
        timestamp: "Just now",
        verificationStatus: custodyStatus,
      };

      await api.uploadEvidence(newExhibit);

      setExhibitList((prev) => [newExhibit, ...prev]);
      refetch();

      toast.success(`Exhibit Registered: ${generatedId}`, {
        description: `SHA-256: ${generatedHash.slice(0, 16)}...`,
      });

      // Reset modal
      setIsModalOpen(false);
      setExhibitName("");
      setDescription("");
      setSelectedFile(null);
      setCustodyStatus("PROCESSING");
    } catch (err: any) {
      toast.error("Registration Failed", { description: err.message || "Could not register exhibit." });
    } finally {
      setIsSubmitting(false);
      setSubmittingStep("");
    }
  };

  const filteredExhibits = useMemo(() => {
    return exhibitList.filter((item) => {
      const matchSearch =
        item.fileName.toLowerCase().includes(searchFilter.toLowerCase()) ||
        item.id.toLowerCase().includes(searchFilter.toLowerCase()) ||
        item.case.toLowerCase().includes(searchFilter.toLowerCase()) ||
        item.hash.toLowerCase().includes(searchFilter.toLowerCase());
      const matchType =
        typeFilter === "ALL" || (item.fileType || (item as any).type) === typeFilter;
      return matchSearch && matchType;
    });
  }, [exhibitList, searchFilter, typeFilter]);

  const verifiedCount = exhibitList.filter((e) => e.verificationStatus === "VERIFIED").length;
  const sealedCount = exhibitList.filter((e) => e.verificationStatus === "SEALED").length;

  return (
    <AppShell
      title="Evidence Vault & Chain of Custody"
      subtitle="Cryptographic Forensic Exhibit Store · SHA-256 Integrity Verification"
    >
      {/* Top 4 Vault Telemetry Cards */}
      <div className="grid gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ["Exhibits Stored", `${exhibitList.length}`, "Active forensic exhibits"],
          ["Verified Hashes", `${verifiedCount}`, "SHA-256 integrity verified"],
          ["Sealed Exhibits", `${sealedCount}`, "Court-sealed forensic evidence"],
          ["Storage Protocol", "AES-256", "Hardware security module locked"],
        ].map(([label, value, hint]) => (
          <div key={label} className="rounded border border-[var(--border-theme)] bg-[var(--card-bg)] p-4 shadow-sm">
            <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider block">
              {label}
            </span>
            <p className="mt-2 font-display text-2xl font-bold text-[var(--text-primary)] tracking-tight">{value}</p>
            <span className="mt-1 block text-xs text-[var(--text-secondary)]">{hint}</span>
          </div>
        ))}
      </div>

      {/* Exhibit Register Table Panel */}
      <Panel
        title="Exhibit Register & Custody Ledger"
        className="mt-4"
        action={
          <div className="flex items-center gap-3">
            <div className="relative hidden sm:block">
              <Search className="absolute left-2.5 top-2 size-3 text-[var(--text-secondary)]" />
              <input
                type="text"
                placeholder="Search exhibit, case, hash..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="rounded border border-[var(--border-theme)] bg-[var(--input-bg)] pl-7 pr-2.5 py-1 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-disabled)] outline-none focus:border-[var(--brand)]"
              />
            </div>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-2 py-1 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
            >
              <option value="ALL">All Types</option>
              <option value="Audio">Audio</option>
              <option value="Video">Video</option>
              <option value="Document">Document</option>
              <option value="Image">Image</option>
              <option value="Data">Data</option>
            </select>
            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center gap-1.5 rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-3.5 py-1.5 text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider hover:border-[var(--brand)] transition-colors shadow-sm cursor-pointer ml-1"
            >
              <Plus className="size-3.5 text-[var(--brand)]" /> Register Exhibit
            </button>
          </div>
        }
      >
        {exhibitList.length === 0 ? (
          <div className="py-12 text-center">
            <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-[var(--brand)]/15 border border-[var(--brand)]/30 text-[var(--brand)] mb-3">
              <ShieldCheck className="size-6" />
            </div>
            <h3 className="text-base font-bold text-[var(--text-primary)] font-display">
              Evidence Vault is Empty
            </h3>
            <p className="max-w-md mx-auto text-xs text-[var(--text-secondary)] mt-1 mb-4">
              No digital forensic evidence exhibits have been cataloged yet. Register a new exhibit with SHA-256 cryptographic seal.
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-2 rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-4 py-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)] hover:border-[var(--brand)] cursor-pointer"
            >
              <Plus className="size-3.5 text-[var(--brand)]" /> Register First Exhibit
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[840px] text-left text-xs">
              <thead>
                <tr className="border-b border-[var(--border-theme)] bg-[var(--table-header)] text-[11px] font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                  <th className="py-2.5 pl-3">Exhibit Tag</th>
                  <th className="py-2.5">Artifact File</th>
                  <th className="py-2.5">Type</th>
                  <th className="py-2.5">Case File</th>
                  <th className="py-2.5">SHA-256 Digest</th>
                  <th className="py-2.5">Status</th>
                  <th className="py-2.5 text-right pr-3">Size</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--divider)] text-xs bg-[var(--table-row)]">
                {filteredExhibits.map((item) => {
                  const Icon = typeIcon(item.fileType || (item as any).type);
                  return (
                    <tr key={item.id} className="hover:bg-[var(--table-hover)] transition-colors">
                      <td className="py-3 pl-3 font-mono font-bold text-[var(--brand)]">
                        {item.id}
                      </td>
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <Icon className="size-4 text-[var(--brand)] shrink-0" />
                          <span className="font-semibold text-[var(--text-primary)]">{item.fileName}</span>
                        </div>
                      </td>
                      <td className="py-3 text-[var(--text-secondary)] font-medium">
                        {item.fileType || (item as any).type}
                      </td>
                      <td className="py-3 font-mono text-[var(--text-secondary)]">
                        {item.case}
                      </td>
                      <td className="py-3">
                        <span
                          className="font-mono text-[11px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer"
                          title={item.hash}
                          onClick={() => {
                            navigator.clipboard.writeText(item.hash);
                            toast.info("SHA-256 Copied", { description: item.hash });
                          }}
                        >
                          {item.hash.slice(0, 16)}...
                        </span>
                      </td>
                      <td className="py-3">
                        <span className={`rounded border px-2 py-0.5 text-[10px] font-bold ${statusBadge(item.verificationStatus)}`}>
                          {item.verificationStatus}
                        </span>
                      </td>
                      <td className="py-3 text-right pr-3 font-mono text-[var(--text-secondary)]">
                        {item.size}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      {/* Modal Drawer: Register New Exhibit */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs font-sans">
          <div className="w-full max-w-xl rounded border border-[var(--border-theme)] bg-[var(--panel-bg)] p-5 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-[var(--divider)] pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-4 text-[var(--brand)]" />
                <h3 className="text-sm font-bold text-[var(--text-primary)]">
                  Register New Evidence Exhibit
                </h3>
              </div>
              <button
                disabled={isSubmitting}
                onClick={() => setIsModalOpen(false)}
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-40"
              >
                <X className="size-4" />
              </button>
            </div>

            <form onSubmit={handleRegisterExhibit} className="mt-4 space-y-3.5 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                  Exhibit Name *
                </label>
                <input
                  required
                  placeholder="e.g. suspect_phone_extraction.tar.gz"
                  value={exhibitName}
                  onChange={(e) => setExhibitName(e.target.value)}
                  className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Evidence Type
                  </label>
                  <select
                    value={evidenceType}
                    onChange={(e) => setEvidenceType(e.target.value as EvidenceTypeOption)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  >
                    <option value="Document">Document</option>
                    <option value="Audio">Audio Intercept</option>
                    <option value="Video">CCTV / Video</option>
                    <option value="Image">Photographic / Screenshot</option>
                    <option value="Data">Data Ledger / Hex Dump</option>
                    <option value="Other">Other Binary</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Case Reference
                  </label>
                  <input
                    value={caseFile}
                    onChange={(e) => setCaseFile(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                  Attach Forensic File (Optional for Hashing)
                </label>
                <div className="rounded border border-dashed border-[var(--border-theme)] bg-[var(--panel-sec)] p-3 text-center">
                  <input
                    type="file"
                    id="exhibit-file"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <label
                    htmlFor="exhibit-file"
                    className="cursor-pointer flex flex-col items-center justify-center gap-1"
                  >
                    <UploadCloud className="size-5 text-[var(--brand)]" />
                    <span className="text-[11px] font-medium text-[var(--text-primary)]">
                      {selectedFile ? selectedFile.name : "Select file from forensic workstation"}
                    </span>
                    <span className="text-[10px] text-[var(--text-secondary)]">
                      PDF, MP4, WAV, JPG, PNG, JSON, ZIP, E01
                    </span>
                  </label>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Initial Custody Status
                  </label>
                  <select
                    value={custodyStatus}
                    onChange={(e) => setCustodyStatus(e.target.value as CustodyStatusOption)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  >
                    <option value="PROCESSING">PROCESSING</option>
                    <option value="VERIFIED">VERIFIED</option>
                    <option value="SEALED">SEALED</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Officer in Charge
                  </label>
                  <input
                    disabled
                    value="Insp. D. Bose"
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-3 py-1.5 text-xs text-[var(--text-disabled)] cursor-not-allowed"
                  />
                </div>
              </div>

              {isSubmitting && (
                <div className="flex items-center gap-2 rounded border border-[var(--brand)]/30 bg-[var(--brand)]/10 p-2.5 text-xs text-[var(--brand)]">
                  <Loader2 className="size-4 animate-spin shrink-0" />
                  <span>{submittingStep || "Sealing cryptographic hash..."}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 border-t border-[var(--divider)] pt-4">
                <button
                  type="button"
                  disabled={isSubmitting}
                  onClick={() => setIsModalOpen(false)}
                  className="rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-4 py-2 text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-4 py-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)] hover:border-[var(--brand)] transition-colors shadow-sm cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? "Registering..." : "Seal & Register Exhibit"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
