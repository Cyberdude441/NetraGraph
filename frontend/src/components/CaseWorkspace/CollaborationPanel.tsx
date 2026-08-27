import React, { useState } from "react";
import {
  Users,
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
    <div className="rounded-md border border-[#D9E2EC] bg-white p-5 text-xs select-none space-y-4 font-sans shadow-sm">
      {/* Header */}
      <div className="border-b border-[#E2E8F0] pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="size-4 text-[#065F46]" />
          <h3 className="text-sm font-bold text-[#0F172A]">
            Case Team Collaboration & Task Assignment
          </h3>
        </div>

        <span className="text-xs text-[#64748B]">
          3 Active Investigators Assigned
        </span>
      </div>

      {/* Task Checklist */}
      <div className="space-y-2 text-xs">
        <span className="text-xs font-semibold text-[#0F172A] block mb-1">
          Investigation Milestones Checklist:
        </span>
        {tasks.map((task) => (
          <div
            key={task.id}
            onClick={() => toggleTask(task.id)}
            className="rounded-md border border-[#D9E2EC] bg-[#F8FAFC] p-3 flex items-center justify-between hover:border-[#065F46] transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={task.completed}
                onChange={() => {}}
                className="rounded border-[#D9E2EC] text-[#065F46] cursor-pointer size-4"
              />
              <span
                className={
                  task.completed ? "line-through text-[#94A3B8]" : "text-[#0F172A] font-medium"
                }
              >
                {task.title}
              </span>
            </div>

            <span className="text-xs text-[#065F46] font-semibold shrink-0 ml-2">
              {task.assignedTo}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
