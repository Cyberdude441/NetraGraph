import React, { useState, useRef } from "react";
import {
  Upload,
  FileArchive,
  CheckCircle2,
  AlertCircle,
  X,
  FileCode,
  ShieldCheck,
  Layers,
  ArrowUpRight,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/services/api";

interface ModelImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function ModelImportModal({ isOpen, onClose, onSuccess }: ModelImportModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileSelection = (selectedFile: File | undefined) => {
    setUploadError(null);
    if (!selectedFile) return;

    if (!selectedFile.name.toLowerCase().endsWith(".zip")) {
      setUploadError("Invalid file type. Only .zip model artifact bundles are supported.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleImport = async () => {
    if (!file) {
      setUploadError("Please select a valid .zip model bundle first.");
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      const res = await api.importMLModel(file);
      toast.success("Model Bundle Imported Successfully", {
        description: `Imported ${res.model_name} (${res.version}) — Validation PASSED.`,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      const msg = err.message || "Failed to import model bundle.";
      setUploadError(msg);
      toast.error("Import Validation Failed", {
        description: msg,
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
      <div className="w-full max-w-xl rounded-lg border border-[#E2E8F0] bg-white p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-md bg-[#064E3B] text-white">
              <Upload className="size-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#0F172A]">
                Import Trained Model Bundle
              </h3>
              <p className="text-xs text-[#64748B]">
                Upload versioned .zip artifacts generated from NetraGraph export pipelines.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-[#64748B] hover:bg-[#F1F5F9] cursor-pointer"
          >
            <X className="size-4" />
          </button>
        </div>

        {/* Drag and Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`rounded-lg border-2 border-dashed p-6 text-center cursor-pointer transition-all ${
            dragOver
              ? "border-[#064E3B] bg-emerald-50/50"
              : file
              ? "border-[#16A34A] bg-[#F8FAFC]"
              : "border-[#D9E2EC] bg-[#F8FAFC] hover:border-[#94A3B8]"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            className="hidden"
            onChange={(e) => handleFileSelection(e.target.files?.[0])}
          />

          {file ? (
            <div className="space-y-2">
              <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-emerald-50 text-[#16A34A]">
                <FileArchive className="size-6" />
              </div>
              <div className="text-xs">
                <p className="font-bold text-[#0F172A]">{file.name}</p>
                <p className="text-[#64748B]">{(file.size / (1024 * 1024)).toFixed(2)} MB · Ready to upload</p>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                }}
                className="text-[11px] font-semibold text-red-600 hover:underline cursor-pointer"
              >
                Choose another file
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-[#E2E8F0] text-[#64748B]">
                <Upload className="size-6" />
              </div>
              <div className="text-xs">
                <p className="font-bold text-[#0F172A]">Drag & drop your model ZIP archive here</p>
                <p className="text-[#64748B]">or click to browse your computer</p>
              </div>
              <span className="inline-block rounded bg-[#E2E8F0] px-2 py-0.5 text-[10px] font-mono text-[#475569]">
                Supports .zip bundles up to 500 MB
              </span>
            </div>
          )}
        </div>

        {/* Error Alert */}
        {uploadError && (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-xs text-[#DC2626] flex items-start gap-2">
            <AlertCircle className="size-4 shrink-0 mt-0.5" />
            <div>
              <strong className="block">Import Validation Error</strong>
              <span>{uploadError}</span>
            </div>
          </div>
        )}

        {/* Bundle Specification Guide */}
        <div className="rounded-md bg-[#F8FAFC] p-3.5 border border-[#E2E8F0] text-xs space-y-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-[#064E3B] flex items-center gap-1.5">
            <ShieldCheck className="size-3.5" />
            <span>Required Artifact Bundle Contract</span>
          </span>
          <p className="text-[#64748B] text-[11px] leading-relaxed">
            The ZIP bundle must contain all required companion files:
          </p>
          <div className="grid grid-cols-2 gap-1.5 text-[11px] font-mono text-[#334155]">
            <span className="flex items-center gap-1">✓ model.joblib</span>
            <span className="flex items-center gap-1">✓ preprocessor.joblib</span>
            <span className="flex items-center gap-1">✓ feature_schema.json</span>
            <span className="flex items-center gap-1">✓ label_mapping.json</span>
            <span className="flex items-center gap-1">✓ metadata.json</span>
            <span className="flex items-center gap-1">✓ metrics.json</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
          <button
            onClick={onClose}
            disabled={isUploading}
            className="rounded-md border border-[#E2E8F0] px-3.5 py-1.5 text-xs font-semibold text-[#64748B] hover:bg-[#F8FAFC] cursor-pointer"
          >
            Cancel
          </button>

          <button
            onClick={handleImport}
            disabled={!file || isUploading}
            className="flex items-center gap-1.5 rounded-md bg-[#064E3B] px-4 py-1.5 text-xs font-semibold text-white hover:bg-[#047857] cursor-pointer disabled:opacity-50 shadow-xs"
          >
            <Upload className={`size-3.5 ${isUploading ? "animate-spin" : ""}`} />
            <span>{isUploading ? "Validating & Importing..." : "Import Model"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
