import React, { useState } from "react";
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  FolderSearch,
  Share2,
  TrendingUp,
  Flame,
  MapPin,
  Bot,
  ShieldCheck,
  FileText,
  X,
  Play,
} from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

interface DemoStep {
  stepNumber: number;
  title: string;
  moduleRoute: string;
  badge: string;
  icon: React.ElementType;
  description: string;
  investigatorAction: string;
  keyObservation: string;
}

const DEMO_STEPS: DemoStep[] = [
  {
    stepNumber: 1,
    title: "1. Open Active Case Docket",
    moduleRoute: "/cases",
    badge: "Case Workspace",
    icon: FolderSearch,
    description: "Initialize Docket CASE-2026-N09 (Operation Netra-Vigil) tracking an organized inter-state cyber fraud and mule laundering syndicate.",
    investigatorAction: "Review case metadata, priority rating, lead officer assignment, and 85% lifecycle progress.",
    keyObservation: "Case aggregates 105 suspect entities, 148 graph links, 5 anomalies, and 4 sealed evidence blocks.",
  },
  {
    stepNumber: 2,
    title: "2. Operational Intelligence Overview",
    moduleRoute: "/dashboard",
    badge: "Main Dashboard",
    icon: Sparkles,
    description: "Examine high-level intelligence KPIs, real-time activity feed, risk distribution charts, and syndicate community health.",
    investigatorAction: "Inspect active alerts stream and syndicate breakdown across NCR, Mumbai, Bhubaneswar, and Kolkata.",
    keyObservation: "Overall threat severity is elevated due to active cross-state financial dispersion.",
  },
  {
    stepNumber: 3,
    title: "3. Explore Network Topology",
    moduleRoute: "/network",
    badge: "Knowledge Graph",
    icon: Share2,
    description: "Launch the force-directed intelligence graph to explore multi-hop relationship links across suspects, bank accounts, and phones.",
    investigatorAction: "Apply 2-hop BFS expansion on Vikramaditya Rawat (ENT-P-01) and filter by Financial Transfer edges.",
    keyObservation: "Discovers direct conduits linking shell company Apex Global Infotech to mule accounts.",
  },
  {
    stepNumber: 4,
    title: "4. Network Analytics & Centrality",
    moduleRoute: "/analytics",
    badge: "Graph Algorithms",
    icon: TrendingUp,
    description: "Run mathematical centrality algorithms (PageRank, Brandes Betweenness, Louvain Modularity) to detect syndicate kingpins.",
    investigatorAction: "Review authority leaderboard and identify cross-community bridges.",
    keyObservation: "Vikramaditya Rawat ranks #1 in PageRank (24.8%), while Arjun Menon acts as the Hawala conduit bridge.",
  },
  {
    stepNumber: 5,
    title: "5. Detect Behavioral Anomalies",
    moduleRoute: "/anomalies",
    badge: "Anomaly Engine",
    icon: Flame,
    description: "Inspect the behavioral anomaly engine for circular transaction cycles and burner handset SIM-hopping patterns.",
    investigatorAction: "Examine 4-hop circular fund recycling loop ALT-2026-001 and IMEI 864902049182019 SIM swap telemetry.",
    keyObservation: "₹1.54 Cr was layered through 4 accounts with a 9% return haircut, confirming deliberate money laundering.",
  },
  {
    stepNumber: 6,
    title: "6. Geographic & Timeline Radar",
    moduleRoute: "/geo-timeline",
    badge: "Spatial-Temporal",
    icon: MapPin,
    description: "Triangulate suspect movements on the tactical geospatial map and replay chronological surveillance events.",
    investigatorAction: "Scrub the timeline scrubber and inspect the Sector 62 Noida call-center nocturnal co-location cluster.",
    keyObservation: "54 spoofed VoIP calls (+350% burst) were dispatched from Noida 18 hours prior to the RTGS mule transfer.",
  },
  {
    stepNumber: 7,
    title: "7. Netra AI GraphRAG Reasoning",
    moduleRoute: "/assistant",
    badge: "AI Copilot",
    icon: Bot,
    description: "Query the autonomous GraphRAG AI assistant using natural language with zero-hallucination evidence citations.",
    investigatorAction: "Ask 'Show connections between Vikramaditya and Arjun Menon' and review the 8-stage execution telemetry.",
    keyObservation: "AI compiles a 6-tier structured brief with Cypher query plan and Section 65B statutory citations.",
  },
  {
    stepNumber: 8,
    title: "8. Validate Cryptographic Evidence",
    moduleRoute: "/cases",
    badge: "Evidence Vault",
    icon: ShieldCheck,
    description: "Inspect the tamper-evident SHA-256 blockchain-inspired audit chain securing court-admissible electronic records.",
    investigatorAction: "Click 'Validate Chain Hashes' to verify cryptographic integrity across all 4 sealed exhibits.",
    keyObservation: "All SHA-256 block hashes match previous linkages with zero tamper anomalies.",
  },
  {
    stepNumber: 9,
    title: "9. Generate Judicial Dossier",
    moduleRoute: "/reports",
    badge: "Dossier Builder",
    icon: FileText,
    description: "Assemble the final 7-section court-ready investigation report and export as an encrypted PDF / JSON package.",
    investigatorAction: "Click 'Preview Judicial Dossier' and verify the Section 65B statutory certificate.",
    keyObservation: "Complete investigation dossier compiled with full cryptographic chain of custody.",
  },
];

interface DemoTourModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DemoTourModal({ isOpen, onClose }: DemoTourModalProps) {
  const navigate = useNavigate();
  const [currentStepIdx, setCurrentStepIdx] = useState<number>(0);

  if (!isOpen) return null;

  const currentStep = DEMO_STEPS[currentStepIdx]!;
  const Icon = currentStep.icon;

  const handleGoToModule = () => {
    navigate({ to: currentStep.moduleRoute as any });
    onClose();
  };

  const handleNext = () => {
    if (currentStepIdx < DEMO_STEPS.length - 1) {
      setCurrentStepIdx((idx) => idx + 1);
    }
  };

  const handlePrev = () => {
    if (currentStepIdx > 0) {
      setCurrentStepIdx((idx) => idx - 1);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4 select-none font-sans">
      <div className="w-full max-w-2xl rounded-xl border border-slate-800 bg-[#0E1318] p-6 shadow-2xl space-y-5">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <span className="flex size-8 items-center justify-center rounded-lg bg-sky-950/60 border border-sky-800 text-sky-300">
              <Sparkles className="size-4" />
            </span>
            <div>
              <h2 className="font-bold text-slate-100 text-sm uppercase tracking-wide">
                NetraGraph AI — Guided Demonstration Mode
              </h2>
              <p className="text-[10px] font-mono text-slate-400">
                Step {currentStep.stepNumber} of {DEMO_STEPS.length} · Preloaded Docket: CASE-2026-N09
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded cursor-pointer"
          >
            <X className="size-4" />
          </button>
        </div>

        {/* Step Progress Pills */}
        <div className="flex items-center gap-1">
          {DEMO_STEPS.map((step, idx) => (
            <div
              key={step.stepNumber}
              onClick={() => setCurrentStepIdx(idx)}
              className={cn(
                "h-1.5 flex-1 rounded-full transition-all cursor-pointer",
                idx === currentStepIdx
                  ? "bg-sky-400"
                  : idx < currentStepIdx
                  ? "bg-emerald-500"
                  : "bg-slate-800"
              )}
            />
          ))}
        </div>

        {/* Step Card Content */}
        <div className="rounded-lg border border-slate-800 bg-[#121820] p-5 space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <span className="flex size-9 items-center justify-center rounded-lg bg-[#161D24] border border-slate-700 text-sky-400">
                <Icon className="size-5" />
              </span>
              <div>
                <h3 className="font-bold text-slate-100 text-sm uppercase">
                  {currentStep.title}
                </h3>
                <span className="rounded bg-sky-950/60 border border-sky-800 px-2 py-0.2 text-[9px] font-mono font-bold text-sky-300">
                  {currentStep.badge}
                </span>
              </div>
            </div>

            <button
              onClick={handleGoToModule}
              className="flex items-center gap-1.5 rounded border border-sky-500/50 bg-sky-950/40 px-3 py-1.5 text-xs font-mono font-bold text-sky-300 hover:bg-sky-900/60 transition-colors cursor-pointer"
            >
              <Play className="size-3" /> Jump to Module
            </button>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            {currentStep.description}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 font-mono text-[11px]">
            <div className="rounded bg-[#161D24] p-3 border border-slate-800 space-y-1">
              <span className="text-[9px] uppercase font-bold text-amber-400 block">
                Investigator Action:
              </span>
              <p className="text-slate-300 font-sans text-xs leading-tight">
                {currentStep.investigatorAction}
              </p>
            </div>

            <div className="rounded bg-[#161D24] p-3 border border-slate-800 space-y-1">
              <span className="text-[9px] uppercase font-bold text-emerald-400 block">
                Forensic Observation:
              </span>
              <p className="text-slate-300 font-sans text-xs leading-tight">
                {currentStep.keyObservation}
              </p>
            </div>
          </div>
        </div>

        {/* Footer Navigation Buttons */}
        <div className="flex items-center justify-between border-t border-slate-800 pt-3">
          <button
            onClick={handlePrev}
            disabled={currentStepIdx === 0}
            className={cn(
              "flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-mono font-bold transition-all",
              currentStepIdx > 0
                ? "bg-[#161D24] border border-slate-800 text-slate-300 hover:text-white cursor-pointer"
                : "text-slate-600 cursor-not-allowed"
            )}
          >
            <ArrowLeft className="size-3.5" /> Previous Step
          </button>

          <div className="text-[10px] font-mono text-slate-500">
            Click 'Jump to Module' to interact directly
          </div>

          <button
            onClick={handleNext}
            disabled={currentStepIdx === DEMO_STEPS.length - 1}
            className={cn(
              "flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-mono font-bold transition-all",
              currentStepIdx < DEMO_STEPS.length - 1
                ? "bg-sky-600 hover:bg-sky-500 text-white cursor-pointer shadow-md"
                : "bg-emerald-600 text-white cursor-default"
            )}
          >
            {currentStepIdx < DEMO_STEPS.length - 1 ? (
              <>
                <span>Next Step</span>
                <ArrowRight className="size-3.5" />
              </>
            ) : (
              <span>Tour Completed</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
