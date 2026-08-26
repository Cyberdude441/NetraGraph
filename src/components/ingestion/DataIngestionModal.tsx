import React, { useState } from "react";
import {
  FileText,
  PhoneCall,
  CreditCard,
  ShieldAlert,
  HardDrive,
  UploadCloud,
  Loader2,
  CheckCircle2,
  X,
  Plus,
  ArrowRight,
  Database,
  BarChart3,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/services/api";
import type { IngestionResponse } from "@/types";

interface DataIngestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (res?: any) => void;
}

type IngestionTab = "ncrb" | "fir" | "cdr" | "finance" | "cyber" | "evidence";

export function DataIngestionModal({
  isOpen,
  onClose,
  onSuccess,
}: DataIngestionModalProps) {
  const [activeTab, setActiveTab] = useState<IngestionTab>("ncrb");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [progressText, setProgressText] = useState("");

  // Tab 0: NCRB CSV State
  const [ncrbFile, setNcrbFile] = useState<File | null>(null);
  const [ncrbRawCsv, setNcrbRawCsv] = useState("");

  // Tab 1: FIR State
  const [firNumber, setFirNumber] = useState("FIR-2026-8841");
  const [policeStation, setPoliceStation] = useState("Special Cell / Cyber Crime PS");
  const [firSections, setFirSections] = useState("IT Act 66D, IPC 420, IPC 120B");
  const [firPersons, setFirPersons] = useState("Karan Verma, Mohit Sharma");
  const [firText, setFirText] = useState("");

  // Tab 2: CDR State
  const [cdrCaseRef, setCdrCaseRef] = useState("CDR-INVESTIGATION-01");
  const [callerNum, setCallerNum] = useState("+919876543210");
  const [receiverNum, setReceiverNum] = useState("+919123456789");
  const [cdrDuration, setCdrDuration] = useState(145);
  const [cdrTower, setCdrTower] = useState("Tower Sector-62 BTS");
  const [cdrImei, setCdrImei] = useState("864201048291024");

  // Tab 3: Finance State
  const [finCaseRef, setFinCaseRef] = useState("FIN-LAYER-01");
  const [senderAcc, setSenderAcc] = useState("HDFC-99214012");
  const [receiverAcc, setReceiverAcc] = useState("ICICI-88120491");
  const [finAmount, setFinAmount] = useState(450000);
  const [finBank, setFinBank] = useState("HDFC Bank");
  const [finType, setFinType] = useState("IMPS");

  // Tab 4: Cyber Complaint State
  const [complaintId, setComplaintId] = useState("NCRP-2026-9042");
  const [victimName, setVictimName] = useState("Sunil Kumar");
  const [attackType, setAttackType] = useState("Financial Fraud (UPI Phishing)");
  const [maliciousIp, setMaliciousIp] = useState("185.220.101.5");
  const [fraudAmount, setFraudAmount] = useState(250000);
  const [suspectPhone, setSuspectPhone] = useState("+919811223344");
  const [suspectAccount, setSuspectAccount] = useState("PAYTM-99882211");

  // Tab 5: Digital Evidence State
  const [evFileName, setEvFileName] = useState("suspect_firmware_dump.bin");
  const [evHash, setEvHash] = useState("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
  const [evCase, setEvCase] = useState("CS-2291");
  const [evType, setEvType] = useState("Data");
  const [evDomain, setEvDomain] = useState("secure-kyc-update.com");

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      let res: any;

      if (activeTab === "ncrb") {
        setProgressText("Parsing and computing NCRB crime statistics...");
        res = await api.ingestNCRBCSV(ncrbFile || undefined, ncrbRawCsv || undefined);
        toast.success("NCRB Dataset Processed", {
          description: res.message || "Successfully integrated NCRB crime analytics.",
        });
      } else if (activeTab === "fir") {
        setProgressText("Parsing FIR and extracting criminal entities...");
        const personsList = firPersons.split(",").map((p) => p.trim()).filter(Boolean);
        const sectionsList = firSections.split(",").map((s) => s.trim()).filter(Boolean);

        res = await api.ingestFIR({
          caseNumber: firNumber,
          policeStation,
          actsAndSections: sectionsList,
          extractedPersons: personsList,
          rawText: firText || undefined,
        });
        toast.success(`${res.module} Ingested Successfully`, {
          description: `Created ${res.nodesCreated} nodes and ${res.edgesCreated} graph linkages.`,
        });
      } else if (activeTab === "cdr") {
        setProgressText("Normalizing telecom MSISDNs & cell towers...");
        res = await api.ingestCDR({
          caseReference: cdrCaseRef,
          records: [
            {
              caller_number: callerNum,
              receiver_number: receiverNum,
              duration: Number(cdrDuration),
              timestamp: new Date().toISOString(),
              tower_location: cdrTower,
              imei: cdrImei,
            },
          ],
        });
        toast.success(`${res.module} Ingested Successfully`, {
          description: `Created ${res.nodesCreated} nodes and ${res.edgesCreated} graph linkages.`,
        });
      } else if (activeTab === "finance") {
        setProgressText("Indexing banking ledger nodes & transactions...");
        res = await api.ingestFinance({
          caseReference: finCaseRef,
          transactions: [
            {
              sender_account: senderAcc,
              receiver_account: receiverAcc,
              amount: Number(finAmount),
              bank: finBank,
              timestamp: new Date().toISOString(),
              transaction_type: finType,
            },
          ],
        });
        toast.success(`${res.module} Ingested Successfully`, {
          description: `Created ${res.nodesCreated} nodes and ${res.edgesCreated} graph linkages.`,
        });
      } else if (activeTab === "cyber") {
        setProgressText("Linking complaint entities, attacker IPs and mule accounts...");
        res = await api.ingestCyberComplaint({
          complaint_id: complaintId,
          victim: victimName,
          attack_type: attackType,
          ip_address: maliciousIp || undefined,
          loss_amount: Number(fraudAmount),
          suspect_phone: suspectPhone || undefined,
          suspect_account: suspectAccount || undefined,
        });
        toast.success(`${res.module} Ingested Successfully`, {
          description: `Created ${res.nodesCreated} nodes and ${res.edgesCreated} graph linkages.`,
        });
      } else {
        setProgressText("Sealing cryptographic SHA-256 evidence exhibit...");
        res = await api.ingestDigitalEvidence({
          file_name: evFileName,
          hash_sha256: evHash,
          case_reference: evCase,
          file_type: evType,
          domain: evDomain || undefined,
        });
        toast.success(`${res.module} Ingested Successfully`, {
          description: `Created ${res.nodesCreated} nodes and ${res.edgesCreated} graph linkages.`,
        });
      }

      if (onSuccess) onSuccess(res);
      onClose();
    } catch (err: any) {
      console.error("Ingestion failed:", err);
      toast.error("Data Ingestion Failed", {
        description: err.message || "Failed to process data payload.",
      });
    } finally {
      setIsSubmitting(false);
      setProgressText("");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/65 p-4 backdrop-blur-xs font-sans">
      <div className="w-full max-w-2xl rounded border border-[var(--border-theme)] bg-[var(--panel-bg)] shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--divider)] px-5 py-3.5 bg-[var(--header-bg)]">
          <div className="flex items-center gap-2.5">
            <span className="flex size-7 items-center justify-center rounded bg-[var(--brand)]/15 border border-[var(--brand)]/30 text-[var(--brand)]">
              <Database className="size-4" />
            </span>
            <div>
              <h3 className="font-display text-sm font-bold text-[var(--text-primary)]">
                Cyber Cell Data Ingestion Gateway
              </h3>
              <p className="text-[11px] text-[var(--text-secondary)]">
                Import NCRB CSVs, authorized FIRs, CDR telecom feeds, banking ledgers & evidence
              </p>
            </div>
          </div>
          <button
            disabled={isSubmitting}
            onClick={onClose}
            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-40"
          >
            <X className="size-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="grid grid-cols-6 border-b border-[var(--divider)] bg-[var(--panel-sec)] text-xs">
          {[
            { id: "ncrb", label: "NCRB CSV", icon: BarChart3 },
            { id: "fir", label: "FIR Report", icon: FileText },
            { id: "cdr", label: "CDR Telecom", icon: PhoneCall },
            { id: "finance", label: "Bank Ledger", icon: CreditCard },
            { id: "cyber", label: "Complaint", icon: ShieldAlert },
            { id: "evidence", label: "Forensics", icon: HardDrive },
          ].map((tab) => {
            const active = activeTab === tab.id;
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as IngestionTab)}
                className={`flex items-center justify-center gap-1.5 py-2.5 px-2 font-semibold transition-all border-b-2 ${
                  active
                    ? "border-[var(--brand)] bg-[var(--card-bg)] text-[var(--brand)]"
                    : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }`}
              >
                <Icon className="size-3.5 shrink-0" />
                <span className="truncate hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          {/* TAB 0: NCRB CSV Ingestion */}
          {activeTab === "ncrb" && (
            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                  Upload Official NCRB CSV Dataset
                </label>
                <div className="rounded border border-dashed border-[var(--border-theme)] bg-[var(--input-bg)] p-4 text-center">
                  <input
                    type="file"
                    id="ncrb-file"
                    accept=".csv"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setNcrbFile(e.target.files[0]);
                      }
                    }}
                    className="hidden"
                  />
                  <label
                    htmlFor="ncrb-file"
                    className="cursor-pointer flex flex-col items-center justify-center gap-1.5"
                  >
                    <UploadCloud className="size-6 text-[var(--brand)]" />
                    <span className="text-xs font-semibold text-[var(--text-primary)]">
                      {ncrbFile ? ncrbFile.name : "Choose NCRB CSV file or drag here"}
                    </span>
                    <span className="text-[10px] text-[var(--text-secondary)]">
                      Supports State-wise Crime, Fraud Categories, IT Act Sections (.csv)
                    </span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                  Or Paste Raw NCRB CSV Text
                </label>
                <textarea
                  rows={4}
                  value={ncrbRawCsv}
                  onChange={(e) => setNcrbRawCsv(e.target.value)}
                  placeholder={`State_UT,Incidents_2024,Incidents_2025,Rate_Per_Lakh,Conviction_Rate\nTelangana,16834,18420,49.2,18.2\nKarnataka,14120,15890,23.5,22.1`}
                  className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] font-mono outline-none focus:border-[var(--brand)] resize-none"
                />
              </div>
            </div>
          )}

          {/* TAB 1: FIR Ingestion */}
          {activeTab === "fir" && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    FIR / Case File Number *
                  </label>
                  <input
                    required
                    value={firNumber}
                    onChange={(e) => setFirNumber(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Police Station / Cell Unit
                  </label>
                  <input
                    value={policeStation}
                    onChange={(e) => setPoliceStation(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                  Named Suspects / Accused (comma-separated)
                </label>
                <input
                  value={firPersons}
                  onChange={(e) => setFirPersons(e.target.value)}
                  placeholder="e.g. Karan Verma, Mohit Sharma"
                  className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                  Acts & Statutory Sections
                </label>
                <input
                  value={firSections}
                  onChange={(e) => setFirSections(e.target.value)}
                  className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                  Case Narrative / Investigation Transcript (Optional)
                </label>
                <textarea
                  rows={2}
                  value={firText}
                  onChange={(e) => setFirText(e.target.value)}
                  placeholder="Paste brief case statement or incident description for AI entity extraction..."
                  className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)] resize-none"
                />
              </div>
            </div>
          )}

          {/* TAB 2: CDR Telecom Ingestion */}
          {activeTab === "cdr" && (
            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                  Investigation Reference ID
                </label>
                <input
                  value={cdrCaseRef}
                  onChange={(e) => setCdrCaseRef(e.target.value)}
                  className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Caller MSISDN (A-Party) *
                  </label>
                  <input
                    required
                    value={callerNum}
                    onChange={(e) => setCallerNum(e.target.value)}
                    placeholder="+919876543210"
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] font-mono outline-none focus:border-[var(--brand)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Called MSISDN (B-Party) *
                  </label>
                  <input
                    required
                    value={receiverNum}
                    onChange={(e) => setReceiverNum(e.target.value)}
                    placeholder="+919123456789"
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] font-mono outline-none focus:border-[var(--brand)]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Duration (Secs)
                  </label>
                  <input
                    type="number"
                    value={cdrDuration}
                    onChange={(e) => setCdrDuration(Number(e.target.value))}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    BTS Tower Location
                  </label>
                  <input
                    value={cdrTower}
                    onChange={(e) => setCdrTower(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Handset IMEI
                  </label>
                  <input
                    value={cdrImei}
                    onChange={(e) => setCdrImei(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] font-mono outline-none focus:border-[var(--brand)]"
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: Finance Ingestion */}
          {activeTab === "finance" && (
            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                  Case / Ledger Reference ID
                </label>
                <input
                  value={finCaseRef}
                  onChange={(e) => setFinCaseRef(e.target.value)}
                  className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Sender Account / UPI *
                  </label>
                  <input
                    required
                    value={senderAcc}
                    onChange={(e) => setSenderAcc(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] font-mono outline-none focus:border-[var(--brand)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Beneficiary Account / UPI *
                  </label>
                  <input
                    required
                    value={receiverAcc}
                    onChange={(e) => setReceiverAcc(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] font-mono outline-none focus:border-[var(--brand)]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Amount (INR) *
                  </label>
                  <input
                    type="number"
                    required
                    value={finAmount}
                    onChange={(e) => setFinAmount(Number(e.target.value))}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] font-bold outline-none focus:border-[var(--brand)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Routing Bank
                  </label>
                  <input
                    value={finBank}
                    onChange={(e) => setFinBank(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Transfer Type
                  </label>
                  <select
                    value={finType}
                    onChange={(e) => setFinType(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  >
                    <option value="IMPS">IMPS</option>
                    <option value="NEFT">NEFT</option>
                    <option value="RTGS">RTGS</option>
                    <option value="UPI">UPI</option>
                    <option value="Hawala">Hawala Cash</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: Cyber Complaint */}
          {activeTab === "cyber" && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Complaint ID *
                  </label>
                  <input
                    required
                    value={complaintId}
                    onChange={(e) => setComplaintId(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Victim / Complainant *
                  </label>
                  <input
                    required
                    value={victimName}
                    onChange={(e) => setVictimName(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Cyber Attack Vector
                  </label>
                  <input
                    value={attackType}
                    onChange={(e) => setAttackType(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Reported Financial Loss (INR)
                  </label>
                  <input
                    type="number"
                    value={fraudAmount}
                    onChange={(e) => setFraudAmount(Number(e.target.value))}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Suspect Phone / Line
                  </label>
                  <input
                    value={suspectPhone}
                    onChange={(e) => setSuspectPhone(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] font-mono outline-none focus:border-[var(--brand)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Mule Bank Account
                  </label>
                  <input
                    value={suspectAccount}
                    onChange={(e) => setSuspectAccount(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] font-mono outline-none focus:border-[var(--brand)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Attacker IP Address
                  </label>
                  <input
                    value={maliciousIp}
                    onChange={(e) => setMaliciousIp(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] font-mono outline-none focus:border-[var(--brand)]"
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: Digital Evidence */}
          {activeTab === "evidence" && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    File Name *
                  </label>
                  <input
                    required
                    value={evFileName}
                    onChange={(e) => setEvFileName(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Case Reference *
                  </label>
                  <input
                    required
                    value={evCase}
                    onChange={(e) => setEvCase(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                  SHA-256 Cryptographic Hash *
                </label>
                <input
                  required
                  value={evHash}
                  onChange={(e) => setEvHash(e.target.value)}
                  className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] font-mono outline-none focus:border-[var(--brand)]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Artifact Type
                  </label>
                  <select
                    value={evType}
                    onChange={(e) => setEvType(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] outline-none focus:border-[var(--brand)]"
                  >
                    <option value="Data">Data Ledger / Database</option>
                    <option value="Document">Forensic Document</option>
                    <option value="Audio">Voice / Audio Intercept</option>
                    <option value="Video">CCTV / Video Recording</option>
                    <option value="DiskImage">EnCase / E01 Disk Image</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[var(--text-primary)] mb-1">
                    Associated Domain (Optional)
                  </label>
                  <input
                    value={evDomain}
                    onChange={(e) => setEvDomain(e.target.value)}
                    className="w-full rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] font-mono outline-none focus:border-[var(--brand)]"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Ingestion Progress Notice */}
          {isSubmitting && (
            <div className="flex items-center gap-2 rounded border border-[var(--brand)]/30 bg-[var(--brand)]/10 p-2.5 text-xs text-[var(--brand)]">
              <Loader2 className="size-4 animate-spin shrink-0" />
              <span>{progressText || "Processing Cyber Cell data ingestion..."}</span>
            </div>
          )}

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-2.5 border-t border-[var(--divider)] pt-4">
            <button
              type="button"
              disabled={isSubmitting}
              onClick={onClose}
              className="rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-4 py-2 text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-1.5 rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-4 py-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)] hover:border-[var(--brand)] transition-colors shadow-sm cursor-pointer disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" /> Processing Dataset...
                </>
              ) : (
                <>
                  <UploadCloud className="size-3.5 text-[var(--brand)]" /> Commit Ingestion
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
