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
      title="AI Investigation Assistant"
      subtitle="Case Query Assistant: Grounded Knowledge Search, Suspect Linkage & Evidentiary Briefings"
    >
      <div className="flex min-h-[calc(100vh-130px)] flex-col rounded-md border border-[#E5E7EB] bg-white shadow-xs overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP ACTION & MODEL STATUS BAR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E5E7EB] bg-[#F8FAF8] px-4 py-2.5 z-20">
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-[#064E3B] font-bold">
              <Sparkles className="size-4 text-[#16A34A]" />
              <span>Assisted Case Intelligence</span>
            </span>
            <span className="text-[#D1D5DB]">|</span>
            <span className="text-[#64748B]">
              Active Scope: <strong className="text-[#111827]">Operation Netra-Vigil (CASE-2026-N09)</strong>
            </span>
            <span className="rounded-md bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 text-[#16A34A] text-xs font-semibold">
              Deterministic Graph Grounded
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setBriefingModalOpen(true)}
              className="flex items-center gap-1.5 rounded-md bg-[#064E3B] hover:bg-[#04382A] px-3.5 py-1.5 text-xs font-semibold text-white transition-colors cursor-pointer shadow-xs"
            >
              <FileText className="size-3.5" />
              <span>Generate Case Briefing</span>
            </button>

            <button
              onClick={() => navigate({ to: "/network" })}
              className="flex items-center gap-1 rounded-md border border-[#E5E7EB] bg-white px-3 py-1.5 text-xs font-semibold text-[#111827] hover:bg-[#F3F4F6] transition-colors cursor-pointer shadow-xs"
            >
              <Share2 className="size-3.5 text-[#064E3B]" />
              <span>Graph View</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. THREE-PANEL INVESTIGATION WORKSPACE
           ========================================================================= */}
        <div className="flex min-h-0 flex-1 overflow-hidden relative">
          {/* Briefing Modal Overlay */}
          {briefingModalOpen && (
            <div className="absolute inset-0 z-30 bg-black/60 backdrop-blur-xs p-6 flex items-center justify-center overflow-y-auto">
              <div className="w-full max-w-4xl">
                <BriefingGenerator
                  caseId={activeCaseId}
                  onClose={() => setBriefingModalOpen(false)}
                />
              </div>
            </div>
          )}

          {/* LEFT PANEL: Context Manager & Query History */}
          <aside className="w-80 shrink-0 border-r border-[#D9E2EC] bg-[#F8FAFC] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-[#E2E8F0] bg-white px-4 py-3">
              <span className="text-xs font-bold text-[#0F172A] flex items-center gap-1.5">
                <FolderSearch className="size-4 text-[#065F46]" />
                Investigation Context
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4">
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
          <main className="min-w-0 flex-1 h-full overflow-y-auto p-4 bg-[#F5F8FC] space-y-4">
            {/* Top Natural Language Search Input */}
            <QueryInput onSearch={handleExecuteQuery} isLoading={isLoading} />

            {/* Quick Investigation Inquiries */}
            <SuggestedActions onSelectQuery={handleExecuteQuery} />

            {/* Structured AI Response */}
            {currentResponse && <AIResponse response={currentResponse} />}
          </main>

          {/* RIGHT PANEL: Evidence Citations & Action Triggers */}
          <aside className="w-72 shrink-0 border-l border-[#D9E2EC] bg-white flex flex-col h-full overflow-hidden select-none 2xl:w-96">
            <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] px-4 py-3">
              <span className="text-xs font-bold text-[#0F172A] flex items-center gap-1.5">
                <ShieldCheck className="size-4 text-[#198754]" />
                Evidentiary Basis
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4">
              {currentResponse && (
                <EvidenceCitation citations={currentResponse.citations} />
              )}

              {/* Fast Quick Links */}
              <div className="rounded-md border border-[#D9E2EC] bg-white p-3.5 space-y-2 text-xs shadow-xs">
                <span className="text-xs font-bold text-[#0F172A] block">
                  Quick Actions
                </span>
                <div className="space-y-1">
                  <button
                    onClick={() => navigate({ to: "/profiles" })}
                    className="w-full flex items-center justify-between rounded-md bg-[#F8FAFC] p-2 hover:bg-[#F1F5F9] text-[#0F172A] transition-colors cursor-pointer border border-[#D9E2EC]"
                  >
                    <span>Target Dossiers (105 Profiles)</span>
                    <span className="text-[#065F46] font-bold">→</span>
                  </button>
                  <button
                    onClick={() => navigate({ to: "/analytics" })}
                    className="w-full flex items-center justify-between rounded-md bg-[#F8FAFC] p-2 hover:bg-[#F1F5F9] text-[#0F172A] transition-colors cursor-pointer border border-[#D9E2EC]"
                  >
                    <span>Investigation Insights</span>
                    <span className="text-[#065F46] font-bold">→</span>
                  </button>
                  <button
                    onClick={() => navigate({ to: "/anomalies" as any })}
                    className="w-full flex items-center justify-between rounded-md bg-[#F8FAFC] p-2 hover:bg-[#F1F5F9] text-[#0F172A] transition-colors cursor-pointer border border-[#D9E2EC]"
                  >
                    <span>Alerts & Anomalies</span>
                    <span className="text-[#065F46] font-bold">→</span>
                  </button>
                </div>
              </div>
            </div>
          </aside>
        </div>

        {/* =========================================================================
            3. BOTTOM STATUS BAR
           ========================================================================= */}
        <div className="border-t border-[#D9E2EC] bg-[#F8FAFC] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs text-[#64748B] z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-[#065F46] flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-[#198754]" />
              NETRA ASSISTANT ACTIVE
            </span>
            <span>
              Target Coverage: <strong className="text-[#0F172A]">105 / 105 Entities</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-xs text-[#64748B]">
            <ShieldCheck className="size-3.5 text-[#198754]" />
            <span>Section 65B Compliant Evidentiary Attribution</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
