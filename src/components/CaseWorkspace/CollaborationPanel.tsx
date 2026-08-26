import React, { useState } from "react";
import {
  Users,
  CheckCircle2,
  Plus,
  Send,
  MessageSquare,
  Clock,
  ShieldCheck,
  UserCheck,
} from "lucide-react";
import { toast } from "sonner";

interface TaskItem {
  id: string;
  title: string;
  assignedTo: string;
  completed: boolean;
}

export function CollaborationPanel() {
  const [tasks, setTasks] = useState<TaskItem[]>([
    { id: "T-1", title: "Serve Section 91 CrPC notice on ICICI Bank Nodal Officer", assignedTo: "Insp. D. Bose", completed: true },
    { id: "T-2", title: "Triangulate IMEI 864902049182019 on CEIR Portal", assignedTo: "Cyber Forensic Officer", completed: true },
    { id: "T-3", title: "Dispatch physical surveillance team to Sector 62 Safehouse", assignedTo: "Sub-Inspector S. Jena", completed: false },
    { id: "T-4", title: "Compile Final Section 65B Dossier for Judicial Court Filing", assignedTo: "Insp. D. Bose", completed: false },
  ]);

  const toggleTask = (id: string) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t))
    );
    toast.success("Task Checklist Status Updated");
  };

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-5 text-xs select-none space-y-4 font-sans shadow-2xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="size-4 text-sky-400" />
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100">
            Case Team Collaboration & Task Assignment
          </h3>
        </div>

        <span className="font-mono text-[10px] text-slate-400">
          3 Active Investigators Assigned
        </span>
      </div>

      {/* Task Checklist */}
      <div className="space-y-2 font-mono text-[11px]">
        <span className="text-[10px] uppercase font-bold text-slate-400 block">
          Investigation Milestones Checklist:
        </span>
        {tasks.map((task) => (
          <div
            key={task.id}
            onClick={() => toggleTask(task.id)}
            className="rounded border border-slate-800 bg-[#121820] p-3 flex items-center justify-between hover:border-sky-500/50 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2.5">
              <input
                type="checkbox"
                checked={task.completed}
                onChange={() => {}}
                className="rounded border-slate-700 bg-slate-800 text-sky-500 cursor-pointer size-4"
              />
              <span
                className={
                  task.completed ? "line-through text-slate-500" : "text-slate-200"
                }
              >
                {task.title}
              </span>
            </div>

            <span className="text-[10px] text-sky-300 font-bold shrink-0 ml-2">
              {task.assignedTo}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
