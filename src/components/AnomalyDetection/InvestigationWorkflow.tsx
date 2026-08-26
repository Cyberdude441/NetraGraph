import React, { useState } from "react";
import {
  Activity,
  UserCheck,
  FileCheck2,
  Send,
  CheckCircle2,
  AlertTriangle,
  History,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import type { AnomalyAlert, InvestigationNote } from "@/utils/anomalyDetection";
import type { AnomalyStatus } from "@/utils/anomalyRules";

interface InvestigationWorkflowProps {
  alert: AnomalyAlert;
  onUpdateStatus: (alertId: string, nextStatus: AnomalyStatus) => void;
  onAddNote: (alertId: string, note: InvestigationNote) => void;
  onAssignAnalyst: (alertId: string, analystName: string) => void;
}

export function InvestigationWorkflow({
  alert,
  onUpdateStatus,
  onAddNote,
  onAssignAnalyst,
}: InvestigationWorkflowProps) {
  const [newNote, setNewNote] = useState<string>("");
  const [analyst, setAnalyst] = useState<string>(alert.assignedAnalyst || "Insp. D. Bose");

  const handleStatusChange = (status: AnomalyStatus) => {
    onUpdateStatus(alert.id, status);
    toast.success(`Alert Status Updated to ${status.replace("_", " ")}`);
  };

  const handleAddNote = () => {
    if (!newNote.trim()) return;
    const noteObj: InvestigationNote = {
      id: `NOTE-${Date.now()}`,
      author: analyst || "Insp. D. Bose",
      timestamp: new Date().toISOString(),
      content: newNote.trim(),
    };
    onAddNote(alert.id, noteObj);
    setNewNote("");
    toast.success("Forensic Case Note Appended");
  };

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-4 text-xs select-none space-y-3 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-2 flex items-center justify-between">
        <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase font-bold text-slate-300">
          <Activity className="size-3.5 text-emerald-400" />
          <span>Analyst Investigation Workflow</span>
        </div>

        <span className="font-mono text-[10px] text-sky-400 font-bold">
          {alert.status.replace("_", " ")}
        </span>
      </div>

      {/* Lifecycle Status Stepper Buttons */}
      <div className="space-y-1">
        <span className="text-[9px] font-mono uppercase text-slate-500 font-bold block">
          Transition Status:
        </span>
        <div className="grid grid-cols-3 gap-1 font-mono text-[10px]">
          {(
            [
              { id: "UNDER_REVIEW", label: "Review" },
              { id: "INVESTIGATING", label: "Investigate" },
              { id: "RESOLVED", label: "Resolve" },
              { id: "FALSE_POSITIVE", label: "False Pos" },
              { id: "ARCHIVED", label: "Archive" },
            ] as const
          ).map((s) => {
            const active = alert.status === s.id;
            return (
              <button
                key={s.id}
                onClick={() => handleStatusChange(s.id as AnomalyStatus)}
                className={cn(
                  "rounded border py-1 font-bold transition-all cursor-pointer",
                  active
                    ? "bg-sky-500/20 text-sky-300 border-sky-500/50"
                    : "border-slate-800 bg-[#121820] text-slate-400 hover:text-slate-200"
                )}
              >
                {s.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Assign Officer */}
      <div className="space-y-1 font-mono text-[10px]">
        <span className="text-slate-500 font-bold uppercase block">
          Assigned Case Officer:
        </span>
        <div className="flex items-center gap-1.5">
          <input
            type="text"
            value={analyst}
            onChange={(e) => setAnalyst(e.target.value)}
            className="flex-1 rounded border border-slate-800 bg-[#121820] px-2 py-1 text-xs text-slate-200 font-mono outline-none focus:border-sky-500"
          />
          <button
            onClick={() => {
              onAssignAnalyst(alert.id, analyst);
              toast.success(`Assigned to ${analyst}`);
            }}
            className="rounded border border-slate-800 bg-[#161D24] px-2.5 py-1 text-xs font-mono text-sky-400 hover:border-sky-500 cursor-pointer"
          >
            Assign
          </button>
        </div>
      </div>

      {/* Investigation Notes History */}
      <div className="space-y-1.5 pt-1">
        <span className="text-[9px] font-mono uppercase text-slate-500 font-bold block">
          Forensic Case Memos ({alert.notes.length})
        </span>

        <div className="max-h-28 overflow-y-auto space-y-1.5 custom-scrollbar font-mono text-[10px]">
          {alert.notes.length === 0 ? (
            <span className="text-slate-500 italic block">No notes recorded yet.</span>
          ) : (
            alert.notes.map((n) => (
              <div key={n.id} className="rounded border border-slate-800 bg-[#121820] p-2 space-y-0.5">
                <div className="flex items-center justify-between text-[9px] text-slate-500">
                  <strong className="text-sky-300">{n.author}</strong>
                  <span>{new Date(n.timestamp).toLocaleDateString()}</span>
                </div>
                <p className="text-slate-300 font-sans text-[11px] leading-tight">{n.content}</p>
              </div>
            ))
          )}
        </div>

        {/* Add Note Input */}
        <div className="flex items-center gap-1.5 pt-1">
          <input
            type="text"
            placeholder="Add case memo or warrant note..."
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddNote()}
            className="flex-1 rounded border border-slate-800 bg-[#121820] px-2 py-1 text-xs text-slate-200 font-mono outline-none focus:border-sky-500"
          />
          <button
            onClick={handleAddNote}
            className="rounded bg-sky-500/20 border border-sky-500/50 p-1 text-sky-300 hover:bg-sky-500/30 cursor-pointer"
          >
            <Send className="size-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
