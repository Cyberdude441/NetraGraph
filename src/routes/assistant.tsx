import { createFileRoute, useNavigate } from "@tanstack/react-router";
import React, { useState } from "react";
import {
  Sparkles,
  Bot,
  ShieldCheck,
  FileText,
  Share2,
  Download,
  CheckCircle2,
  FolderSearch,
  Users,
  Activity,
  Layers,
  Cpu,
} from "lucide-react";
import { toast } from "sonner";

import { AppShell } from "@/components/AppShell";
import { QueryInput } from "@/components/NetraAI/QueryInput";
import { SuggestedActions } from "@/components/NetraAI/SuggestedActions";
import { AIResponse } from "@/components/NetraAI/AIResponse";
import { EvidenceCitation } from "@/components/NetraAI/EvidenceCitation";
import { ContextManager } from "@/components/NetraAI/ContextManager";
import { QueryHistory, type QueryHistoryItem } from "@/components/NetraAI/QueryHistory";
import { BriefingGenerator } from "@/components/NetraAI/BriefingGenerator";

import {
  analyzeInvestigationQuery,
  type NetraAIResponse,
} from "@/services/netraAI";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/assistant")({
  head: () => ({
    meta: [
      { title: "Netra AI Copilot & GraphRAG Reasoning — NetraGraph AI" },
      {
        name: "description",
        content:
          "Enterprise GraphRAG AI Copilot grounded in Neo4j Knowledge Graph, generating explainable multi-hop investigative evidence and zero-hallucination case briefings.",
      },
    ],
  }),
  component: NetraAIAssistantPage,
});

function NetraAIAssistantPage() {
  const navigate = useNavigate();

  // Active Context State
  const [activeCaseId, setActiveCaseId] = useState<string>("CASE-2026-N09");
  const [pinnedEntities, setPinnedEntities] = useState<{ id: string; name: string }[]>([
    { id: "ENT-P-01", name: "Vikramaditya Rawat" },
    { id: "ENT-P-06", name: "Arjun Menon" },
  ]);
  const [focusArea, setFocusArea] = useState<string>("All Telemetry");

  // Query & Response State
  const [currentResponse, setCurrentResponse] = useState<NetraAIResponse>(() =>
    analyzeInvestigationQuery("Show connections between Vikramaditya Rawat and Arjun Menon")
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [briefingModalOpen, setBriefingModalOpen] = useState<boolean>(false);

  // History State
  const [queryHistory, setQueryHistory] = useState<QueryHistoryItem[]>([
    {
      id: "Q-01",
      query: "Show connections between Vikramaditya Rawat and Arjun Menon",
      intent: "Relationship Path",
      timestamp: "2026-08-27T10:15:00Z",
      isSaved: true,
    },
    {
      id: "Q-02",
      query: "Who are the most influential kingpin entities in this network?",
      intent: "Centrality Ranks",
      timestamp: "2026-08-27T09:40:00Z",
      isSaved: false,
    },
    {
      id: "Q-03",
      query: "Find unusual circular transaction loops and fund recycling.",
      intent: "Financial Loops",
      timestamp: "2026-08-27T09:12:00Z",
      isSaved: true,
    },
  ]);

  const handleExecuteQuery = (queryText: string) => {
    setIsLoading(true);

    setTimeout(() => {
      const resp = analyzeInvestigationQuery(queryText, {
        activeCaseId,
        pinnedEntityIds: pinnedEntities.map((e) => e.id),
      });

      setCurrentResponse(resp);
      setIsLoading(false);

      // Append to history
      setQueryHistory((prev) => [
        {
          id: `Q-${Date.now()}`,
          query: queryText,
          intent: resp.parsedQuery.intentLabel,
          timestamp: new Date().toISOString(),
          isSaved: false,
        },
        ...prev,
      ]);
    }, 450);
  };

  const handleToggleSave = (id: string) => {
    setQueryHistory((prev) =>
      prev.map((item) => (item.id === id ? { ...item, isSaved: !item.isSaved } : item))
    );
  };

  const handleRemovePinnedEntity = (id: string) => {
    setPinnedEntities((prev) => prev.filter((e) => e.id !== id));
  };

  return (
    <AppShell
      title="Netra AI Copilot & GraphRAG Reasoning Console"
      subtitle="Natural Language-to-Graph Query Synthesis, 8-Stage Reasoning Telemetry & Evidence Attribution"
    >
      <div className="flex flex-col h-[calc(100vh-130px)] rounded border border-slate-800 bg-[#0B0F14] shadow-2xl overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP ACTION & MODEL STATUS BAR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-[#0E1318] px-4 py-2 z-20">
          <div className="flex items-center gap-3 font-mono text-xs">
            <span className="flex items-center gap-1.5 text-purple-400 font-bold">
              <Sparkles className="size-3.5" />
              <span>NETRA-GRAPHRAG v4.2</span>
            </span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400">
              Grounding: <strong className="text-slate-200">Neo4j Enterprise Knowledge Graph</strong>
            </span>
            <span className="rounded bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 text-emerald-300 text-[10px] font-bold">
              Zero Hallucination Grounded
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setBriefingModalOpen(true)}
              className="flex items-center gap-1.5 rounded border border-purple-500/50 bg-purple-950/40 px-3 py-1 text-xs font-mono font-bold text-purple-300 hover:bg-purple-900/50 transition-colors cursor-pointer shadow-xs"
            >
              <FileText className="size-3.5" />
              <span>Generate Case Briefing</span>
            </button>

            <button
              onClick={() => navigate({ to: "/network" })}
              className="flex items-center gap-1 rounded border border-sky-500/50 bg-sky-950/40 px-2.5 py-1 text-xs font-mono font-semibold text-sky-300 hover:bg-sky-900/50 transition-colors cursor-pointer"
            >
              <Share2 className="size-3" />
              <span>Knowledge Graph</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. THREE-PANEL INVESTIGATION WORKSPACE
           ========================================================================= */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* Briefing Modal Overlay */}
          {briefingModalOpen && (
            <div className="absolute inset-0 z-30 bg-black/80 backdrop-blur-xs p-6 flex items-center justify-center overflow-y-auto">
              <div className="w-full max-w-4xl">
                <BriefingGenerator
                  caseId={activeCaseId}
                  onClose={() => setBriefingModalOpen(false)}
                />
              </div>
            </div>
          )}

          {/* LEFT PANEL: Context Manager & Query History */}
          <aside className="w-80 border-r border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-slate-800 bg-[#141A21] px-4 py-3">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 flex items-center gap-1.5">
                <FolderSearch className="size-3.5 text-sky-400" />
                Investigation Context
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4 custom-scrollbar">
              <ContextManager
                activeCaseId={activeCaseId}
                onSelectCase={setActiveCaseId}
                pinnedEntities={pinnedEntities}
                onRemovePinnedEntity={handleRemovePinnedEntity}
                focusArea={focusArea}
                onSelectFocusArea={setFocusArea}
              />

              <QueryHistory
                history={queryHistory}
                onSelectHistory={handleExecuteQuery}
                onToggleSave={handleToggleSave}
              />
            </div>
          </aside>

          {/* CENTER PANEL: Query Input, Suggested Queries & GraphRAG Response */}
          <main className="flex-1 h-full overflow-y-auto p-4 custom-scrollbar bg-[#0B0F14] space-y-4">
            {/* Top Natural Language Search Input */}
            <QueryInput onSearch={handleExecuteQuery} isLoading={isLoading} />

            {/* Quick Investigation Inquiries */}
            <SuggestedActions onSelectQuery={handleExecuteQuery} />

            {/* Structured AI Response with Pipeline Telemetry */}
            {currentResponse && <AIResponse response={currentResponse} />}
          </main>

          {/* RIGHT PANEL: Evidence Citations & Action Triggers */}
          <aside className="w-88 border-l border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-slate-800 bg-[#141A21] px-4 py-3">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 flex items-center gap-1.5">
                <ShieldCheck className="size-3.5 text-emerald-400" />
                Corroborating Evidence
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4 custom-scrollbar">
              {currentResponse && (
                <EvidenceCitation citations={currentResponse.citations} />
              )}

              {/* Fast Quick Links */}
              <div className="rounded-lg border border-slate-800 bg-[#121820] p-3 space-y-2 font-mono text-[11px]">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">
                  Quick Navigation
                </span>
                <div className="space-y-1">
                  <button
                    onClick={() => navigate({ to: "/profiles" })}
                    className="w-full flex items-center justify-between rounded bg-[#161D24] p-2 hover:bg-[#1A2634] text-slate-300 hover:text-sky-300 transition-colors cursor-pointer border border-slate-800"
                  >
                    <span>Target Dossiers (105 Profiles)</span>
                    <span className="text-sky-400">→</span>
                  </button>
                  <button
                    onClick={() => navigate({ to: "/analytics" })}
                    className="w-full flex items-center justify-between rounded bg-[#161D24] p-2 hover:bg-[#1A2634] text-slate-300 hover:text-sky-300 transition-colors cursor-pointer border border-slate-800"
                  >
                    <span>Centrality & Louvain Clusters</span>
                    <span className="text-sky-400">→</span>
                  </button>
                  <button
                    onClick={() => navigate({ to: "/anomalies" as any })}
                    className="w-full flex items-center justify-between rounded bg-[#161D24] p-2 hover:bg-[#1A2634] text-slate-300 hover:text-sky-300 transition-colors cursor-pointer border border-slate-800"
                  >
                    <span>Behavioral Anomaly Streams</span>
                    <span className="text-sky-400">→</span>
                  </button>
                </div>
              </div>
            </div>
          </aside>
        </div>

        {/* =========================================================================
            3. BOTTOM HIGH-DENSITY STATUS BAR
           ========================================================================= */}
        <div className="border-t border-slate-800 bg-[#0B0F14] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-400 z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-purple-400 animate-pulse" />
              NETRA AI GRAPHRAG ENGINE
            </span>
            <span>
              Ground Truth Node Coverage: <strong className="text-slate-100">105 / 105 Entities</strong>
            </span>
            <span>
              Evidence Linkage: <strong className="text-emerald-400">100% Attributed</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-slate-400">
            <ShieldCheck className="size-3.5 text-emerald-400" />
            <span>Statutory Evidentiary Standard §65B Compliant</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
