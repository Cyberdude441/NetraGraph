import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowUpRight,
  ChevronRight,
  FolderSearch,
  Network,
  ShieldAlert,
  Users,
  ExternalLink,
  Search,
  Database,
  UploadCloud,
  FileText,
  PhoneCall,
  CreditCard,
  HardDrive,
  ShieldCheck,
  Plus,
  BarChart3,
  TrendingUp,
  Scale,
  MapPin,
  RefreshCw,
  Globe2,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import React, { useState, useMemo } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";
import { toast } from "sonner";

import { AppShell, Panel, riskBadge } from "@/components/AppShell";
import { useTheme } from "@/lib/theme";
import { api } from "@/services/api";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Live NCRB Intelligence Grid — NetraGraph AI" },
      {
        name: "description",
        content:
          "Live Open Government Data (data.gov.in) NCRB Crime Analytics: State-wise incidents, motives, police disposal, and court trial outcomes.",
      },
      { property: "og:title", content: "Live NCRB Intelligence Grid — NetraGraph AI" },
      {
        property: "og:description",
        content: "Open Government Data live cyber intelligence analysis platform.",
      },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [activeMotiveIndex, setActiveMotiveIndex] = useState<number | null>(null);
  const [selectedMotiveState, setSelectedMotiveState] = useState<string>("National");
  const [isSyncing, setIsSyncing] = useState(false);

  // 1. Live OGD Pipeline Status
  const { data: pipelineStatus, refetch: refetchPipeline } = useQuery({
    queryKey: ["ogd-pipeline-status"],
    queryFn: () => api.getOGDPipelineStatus(),
  });

  // 2. High-Level National Overview
  const { data: ncrbOverview, refetch: refetchOverview } = useQuery({
    queryKey: ["ncrb-overview"],
    queryFn: () => api.getNCRBOverview(),
  });

  // 3. Official NCRB Motives Endpoint (GET /api/ncrb/motives)
  const { data: rawMotives = [], refetch: refetchMotives } = useQuery({
    queryKey: ["ncrb-motives", selectedMotiveState],
    queryFn: () => api.getNCRBMotives({ state: selectedMotiveState }),
  });

  const motives = useMemo(() => {
    return rawMotives.map((m) => ({
      Motive: m.motive_full || m.crime_motive,
      Cases: m.cases,
      Percentage: m.percentage || 0,
      Category: m.category || "General",
      Risk_Level: m.risk_level || "MODERATE",
    }));
  }, [rawMotives]);

  // 4. Police Pendency & Disposal (GET /api/ncrb/investigation)
  const { data: rawPolice = [], refetch: refetchPolice } = useQuery({
    queryKey: ["ncrb-investigation"],
    queryFn: () => api.getNCRBInvestigation(),
  });

  const policeDisposal = useMemo(() => {
    return rawPolice.map((p) => ({
      Crime_Head: p.crime_head,
      Total_Investigated: p.total_investigated,
      Disposed_By_Police: p.disposed_by_police,
      Chargesheeted: p.chargesheeted,
      Pending_Investigation: p.pending_investigation,
      Chargesheet_Rate: p.chargesheet_rate,
    }));
  }, [rawPolice]);

  // 5. Court Trial Outcomes (GET /api/ncrb/court)
  const { data: rawCourt = [], refetch: refetchCourt } = useQuery({
    queryKey: ["ncrb-court"],
    queryFn: () => api.getNCRBCourt(),
  });

  const courtDisposal = useMemo(() => {
    return rawCourt.map((c) => ({
      Crime_Head: c.crime_head,
      Total_Trials: c.total_trials,
      Disposed_By_Courts: c.disposed_by_courts,
      Convicted: c.convicted,
      Acquitted: c.acquitted,
      Pending_Trial: c.pending_trial,
      Conviction_Rate: c.conviction_rate,
    }));
  }, [rawCourt]);

  // 6. State-wise Top Hotspots (GET /api/ncrb/cyber-crime)
  const { data: rawCyberCrime = [], refetch: refetchStates } = useQuery({
    queryKey: ["ncrb-cyber-crime"],
    queryFn: () => api.getNCRBCyberCrime(),
  });

  const ncrbStates = useMemo(() => {
    return rawCyberCrime.slice(0, 8).map((s) => ({
      state: s.state,
      incidents2023: s.incidents2023 || 0,
      incidents2024: s.incidents2024 || 0,
      incidents2025: s.incidents2025 || s.incidents,
      ratePerLakh: s.rate_per_lakh,
      chargesheetRate: s.chargesheet_rate,
      convictionRate: s.conviction_rate,
      personsArrested: s.persons_arrested,
    }));
  }, [rawCyberCrime]);

  // Live Metric Aggregations for Phase 4
  const totalNationalCases = useMemo(() => {
    if (rawCyberCrime.length > 0) {
      return rawCyberCrime.reduce((acc, s) => acc + (s.incidents2025 || s.incidents || 0), 0);
    }
    return ncrbOverview?.nationalTotal2025 || 122655;
  }, [rawCyberCrime, ncrbOverview]);

  const totalActiveInvestigations = useMemo(() => {
    if (rawPolice.length > 0) {
      return rawPolice.reduce((acc, p) => acc + (p.pending_investigation || 0), 0);
    }
    return 61470;
  }, [rawPolice]);

  const totalInvestigatedCases = useMemo(() => {
    if (rawPolice.length > 0) {
      return rawPolice.reduce((acc, p) => acc + (p.total_investigated || 0), 0);
    }
    return 141440;
  }, [rawPolice]);

  const highRiskJurisdictions = useMemo(() => {
    return rawCyberCrime.filter((s) => s.rate_per_lakh >= 15);
  }, [rawCyberCrime]);

  const crimeTrends = useMemo(() => {
    const sum2023 = rawCyberCrime.reduce((acc, s) => acc + (s.incidents2023 || 0), 0) || 98450;
    const sum2024 = rawCyberCrime.reduce((acc, s) => acc + (s.incidents2024 || 0), 0) || 108420;
    const sum2025 = rawCyberCrime.reduce((acc, s) => acc + (s.incidents2025 || s.incidents || 0), 0) || 122655;

    return [
      { year: "2023", incidents: sum2023, chargesheetRate: 48.2, convictionRate: 21.0 },
      { year: "2024", incidents: sum2024, chargesheetRate: 46.8, convictionRate: 22.4 },
      { year: "2025", incidents: sum2025, chargesheetRate: 44.9, convictionRate: 24.1 },
    ];
  }, [rawCyberCrime]);

  // 7. IT Act Sections
  const { data: ncrbSections = [], refetch: refetchSections } = useQuery({
    queryKey: ["ncrb-it-act"],
    queryFn: () => api.getNCRBITActSections(),
  });

  const refreshAll = () => {
    refetchPipeline();
    refetchOverview();
    refetchMotives();
    refetchPolice();
    refetchCourt();
    refetchStates();
    refetchSections();
  };

  const handleSyncNow = async () => {
    setIsSyncing(true);
    const toastId = "sync-ogd";
    toast.loading("Fetching live data.gov.in NCRB feeds...", { id: toastId });

    try {
      const res = await api.syncOGDPipeline();
      toast.success("OGD Pipeline Synchronized", {
        id: toastId,
        description: `Synced ${res.sync?.total_datasets || 6} feeds & rebuilt Neo4j Knowledge Graph.`,
      });
      refreshAll();
    } catch (err: any) {
      toast.error("Pipeline sync failed", {
        id: toastId,
        description: err.message || "Failed to reach data.gov.in API gateway.",
      });
    } finally {
      setIsSyncing(false);
    }
  };

  // Motive Color Palette
  const motiveColors = [
    "#DC2626", // Financial Fraud (Critical)
    "#EA580C", // Revenge
    "#F59E0B", // Extortion
    "#2563EB", // Harassment
    "#7C3AED", // Disrepute
    "#059669", // Corporate / Info
    "#475569", // Hate Speech
    "#0891B2", // Cyber Terrorism
    "#64748B", // Others
  ];

  const tooltipStyle = useMemo(() => ({
    backgroundColor: isDark ? "#111B21" : "#FFFFFF",
    borderColor: isDark ? "#2A3942" : "#E5E7EB",
    borderRadius: "4px",
    color: isDark ? "#F8FAFC" : "#0F172A",
    fontSize: "11px",
    boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
  }), [isDark]);

  const activeMotive = activeMotiveIndex !== null ? motives[activeMotiveIndex] : null;
  const activeCount = activeMotive ? activeMotive.Cases : ncrbOverview?.nationalTotal2025 || 122655;
  const activeLabel = activeMotive ? activeMotive.Motive : "Total National Incidents";

  return (
    <AppShell
      title="National Cyber Investigation Dashboard"
      subtitle="Operational Case Overview · National Crime Records & Multi-Hop Link Intelligence"
    >
      {/* 0. Top Operational Summary Cards (Police & Investigator KPI Grid) */}
      {/* 0. Top KPI cards with large numbers, short explanation & small trend indicators */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {[
          {
            title: "Active Entities",
            value: "105",
            desc: "Verified & Indexed",
            trend: "+12 this week",
            icon: Users,
            to: "/profiles",
            color: "text-[#064E3B]",
            bg: "bg-emerald-50 border-emerald-200",
          },
          {
            title: "Graph Connections",
            value: "200",
            desc: "Active Relational Edges",
            trend: "+24 new links",
            icon: Network,
            to: "/network",
            color: "text-[#047857]",
            bg: "bg-emerald-50 border-emerald-200",
          },
          {
            title: "Urgent Alerts",
            value: "5",
            desc: "Requiring Officer Review",
            trend: "Action Required",
            icon: ShieldAlert,
            to: "/anomalies",
            color: "text-[#DC2626]",
            bg: "bg-red-50 border-red-200",
            badge: "Critical",
          },
          {
            title: "Evidence Records",
            value: "4",
            desc: "Section 65B Certified",
            trend: "100% Cryptographic",
            icon: ShieldCheck,
            to: "/cases",
            color: "text-[#16A34A]",
            bg: "bg-emerald-50 border-emerald-200",
          },
          {
            title: "Timeline Events",
            value: "200",
            desc: "Logged & Corroborated",
            trend: "Spatial-Temporal",
            icon: BarChart3,
            to: "/geo-timeline",
            color: "text-[#F59E0B]",
            bg: "bg-amber-50 border-amber-200",
          },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.title}
              to={item.to}
              className="group block min-w-0 rounded-md border border-[#E5E7EB] bg-white p-5 shadow-xs transition-all hover:border-[#16A34A] hover:shadow-sm lg:min-w-[220px]"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[#64748B]">
                  {item.title}
                </span>
                <span
                  className={cn(
                    "flex size-8 items-center justify-center rounded-md border",
                    item.bg,
                    item.color
                  )}
                >
                  <Icon className="size-4" />
                </span>
              </div>
              <p className="mt-3 font-display text-3xl font-bold tracking-tight text-[#111827]">
                {item.value}
              </p>
              <div className="mt-2 flex items-center justify-between text-xs">
                <span className="text-[#64748B]">{item.desc}</span>
                {item.badge ? (
                  <span className="rounded bg-red-100 text-[#DC2626] font-semibold text-[10px] px-1.5 py-0.5">
                    {item.badge}
                  </span>
                ) : (
                  <span className="text-[11px] font-medium text-[#16A34A]">
                    {item.trend}
                  </span>
                )}
              </div>
            </Link>
          );
        })}
      </div>

      {/* 0.5 Quick Operational Actions & Current Case Docket Banner */}
      <div className="mt-5 rounded-md border border-[#E5E7EB] bg-white p-5 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="flex size-11 items-center justify-center rounded-md bg-[#064E3B] text-white shadow-xs">
            <FolderSearch className="size-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-[#064E3B] font-mono">
                CASE-2026-N09
              </span>
              <span className="text-xs font-bold text-[#111827]">
                · Operation Netra-Vigil (National Cyber Syndicate)
              </span>
              <span className="rounded bg-red-50 text-[#DC2626] border border-red-200 px-2 py-0.5 text-[10px] font-bold">
                Critical Priority
              </span>
            </div>
            <p className="text-xs text-[#64748B] mt-1">
              Lead Officer: <strong>Insp. D. Bose</strong> · Primary Hub: <strong>Kolkata / Mumbai Cyber Grid</strong> · 12 connected suspect accounts
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            to="/cases"
            className="flex items-center gap-1.5 rounded-md bg-[#064E3B] hover:bg-[#04382A] px-4 py-2 text-xs font-semibold text-white transition-all shadow-xs"
          >
            <FolderSearch className="size-3.5" />
            <span>Open Case Docket</span>
          </Link>
          <Link
            to="/network"
            className="flex items-center gap-1.5 rounded-md border border-[#E5E7EB] bg-[#F8FAF8] hover:bg-[#F3F4F6] px-4 py-2 text-xs font-semibold text-[#111827] transition-all"
          >
            <Network className="size-3.5 text-[#064E3B]" />
            <span>Knowledge Graph</span>
          </Link>
        </div>
      </div>

      {/* 1. National NCRB Live Data Pipeline Banner */}
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-md border border-[#E5E7EB] bg-white px-5 py-3.5 shadow-xs">
        <div className="flex items-center gap-3">
          <span className="flex size-8 shrink-0 items-center justify-center rounded-md border border-emerald-200 bg-emerald-50 text-[#064E3B]">
            <Globe2 className="size-4" />
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-display text-xs font-bold text-[#111827]">
                National Open Government Data (data.gov.in) Feeds Active
              </h3>
              <span className="inline-flex items-center gap-1 rounded bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[10px] font-bold text-[#16A34A]">
                <CheckCircle2 className="size-3" /> 6 Feeds Synchronized
              </span>
            </div>
            <p className="text-xs text-[#64748B] mt-0.5">
              Live National Cyber Crime statistics and police disposition records normalized.
            </p>
          </div>
        </div>

        <button
          onClick={handleSyncNow}
          disabled={isSyncing}
          className="flex items-center gap-1.5 rounded-md border border-[#E5E7EB] bg-[#F8FAF8] hover:bg-[#F3F4F6] px-3.5 py-1.5 text-xs font-semibold text-[#111827] transition-colors cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`size-3.5 text-[#064E3B] ${isSyncing ? "animate-spin" : ""}`} />
          <span>{isSyncing ? "Synchronizing..." : "Sync Live NCRB Data"}</span>
        </button>
      </div>

      {/* 1.5 Multi-Year Crime Trend & Disposal Velocity Graph */}
      <div className="mt-4">
        <Panel
          title="National Multi-Year Cyber Crime Trajectory & Enforcement Velocity (2023 - 2025)"
          action={
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1 text-[11px] text-[var(--text-secondary)] font-mono">
                <span className="size-2 rounded-full bg-[var(--brand)]" /> Incident Surge
              </span>
              <span className="flex items-center gap-1 text-[11px] text-[var(--text-secondary)] font-mono">
                <span className="size-2 rounded-full bg-[var(--success)]" /> Chargesheet %
              </span>
              <span className="flex items-center gap-1 text-[11px] text-[var(--text-secondary)] font-mono">
                <span className="size-2 rounded-full bg-[var(--warning)]" /> Conviction %
              </span>
            </div>
          }
        >
          <div className="h-44 w-full pt-1">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={crimeTrends} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#2A3942" : "#E5E7EB"} />
                <XAxis
                  dataKey="year"
                  stroke={isDark ? "#8696A0" : "#64748B"}
                  tick={{ fontSize: 11, fontFamily: "Inter, sans-serif" }}
                />
                <YAxis
                  yAxisId="left"
                  stroke={isDark ? "#8696A0" : "#64748B"}
                  tick={{ fontSize: 10, fontFamily: "Inter, sans-serif" }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  domain={[0, 100]}
                  stroke={isDark ? "#8696A0" : "#64748B"}
                  tick={{ fontSize: 10, fontFamily: "Inter, sans-serif" }}
                />
                <Tooltip contentStyle={tooltipStyle} />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="incidents"
                  name="National Incidents"
                  stroke={isDark ? "#53BDEB" : "#2563EB"}
                  strokeWidth={2.5}
                  dot={{ r: 4 }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="chargesheetRate"
                  name="Chargesheet %"
                  stroke={isDark ? "#00A884" : "#059669"}
                  strokeWidth={2}
                  strokeDasharray="4 4"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="convictionRate"
                  name="Conviction %"
                  stroke={isDark ? "#FFB02E" : "#F59E0B"}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      {/* 2. Main Analytics Grid: Motives Donut + State Hotspot Distribution */}
      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        {/* Dominant Cyber Crime Motives Donut */}
        <Panel
          title={`Cyber Crime Motives (${selectedMotiveState})`}
          action={
            <div className="flex items-center gap-2">
              <select
                value={selectedMotiveState}
                onChange={(e) => setSelectedMotiveState(e.target.value)}
                className="rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-2 py-1 text-[11px] font-medium text-[var(--text-primary)] focus:border-[var(--brand)] outline-none"
              >
                <option value="National">National Aggregate</option>
                <option value="Odisha">Odisha</option>
                <option value="Telangana">Telangana</option>
                <option value="Karnataka">Karnataka</option>
                <option value="Maharashtra">Maharashtra</option>
                <option value="Uttar Pradesh">Uttar Pradesh</option>
                <option value="Delhi (UT)">Delhi (UT)</option>
              </select>
            </div>
          }
        >
          <div className="relative flex flex-col items-center">
            <div className="relative h-48 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                  <Pie
                    data={motives}
                    dataKey="Cases"
                    nameKey="Motive"
                    cx="50%"
                    cy="50%"
                    innerRadius={56}
                    outerRadius={78}
                    paddingAngle={3}
                    stroke={isDark ? "#1F2C34" : "#FFFFFF"}
                    strokeWidth={2}
                    onMouseEnter={(_, index) => setActiveMotiveIndex(index)}
                    onMouseLeave={() => setActiveMotiveIndex(null)}
                  >
                    {motives.map((entry, index) => {
                      const isHovered = activeMotiveIndex === index;
                      const isDimmed = activeMotiveIndex !== null && !isHovered;
                      return (
                        <Cell
                          key={entry.Motive}
                          fill={motiveColors[index % motiveColors.length]}
                          style={{
                            outline: "none",
                            cursor: "pointer",
                            opacity: isDimmed ? 0.4 : 1,
                            transition: "opacity 0.15s ease",
                          }}
                        />
                      );
                    })}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>

              {/* Center Donut Label */}
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center px-4">
                <span className="text-[10px] font-semibold tracking-wider text-[var(--text-secondary)] uppercase truncate max-w-[110px]">
                  {activeLabel}
                </span>
                <span className="font-display text-lg font-bold tracking-tight text-[var(--text-primary)]">
                  {activeCount.toLocaleString()}
                </span>
                <span className="text-[10px] font-bold text-[var(--brand)]">
                  {activeMotive ? `${activeMotive.Percentage}%` : "OGD Motives"}
                </span>
              </div>
            </div>

            {/* Motive Legend Grid */}
            <div className="mt-2 grid w-full grid-cols-2 gap-1.5 font-sans text-xs max-h-36 overflow-y-auto pr-1">
              {motives.map((m, idx) => (
                <div
                  key={m.Motive}
                  className="flex items-center justify-between rounded border border-[var(--border-theme)] bg-[var(--card-bg)] px-2 py-1.5 text-[11px]"
                >
                  <span className="flex items-center gap-1.5 truncate font-medium text-[var(--text-primary)]">
                    <span
                      className="size-2 rounded-full shrink-0"
                      style={{ backgroundColor: motiveColors[idx % motiveColors.length] }}
                    />
                    <span className="truncate">{m.Motive}</span>
                  </span>
                  <span className="font-bold text-[var(--text-primary)] shrink-0 ml-1">
                    {m.Percentage}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </Panel>

        {/* State-wise Incidents & Rate Bar Chart */}
        <Panel
          title="State/UT-wise Cyber Crime Exposure (Top Hotspots)"
          className="xl:col-span-2"
          action={
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-[var(--text-secondary)]">Rate Per Lakh Pop</span>
              <Link
                to="/network"
                className="flex items-center gap-1 text-xs font-semibold text-[var(--brand)] hover:underline"
              >
                Neo4j Graph <ChevronRight className="size-3" />
              </Link>
            </div>
          }
        >
          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ncrbStates} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#2A3942" : "#E5E7EB"} />
                <XAxis
                  dataKey="state"
                  stroke={isDark ? "#8696A0" : "#64748B"}
                  tick={{ fontSize: 10, fontFamily: "Inter, sans-serif" }}
                  interval={0}
                  angle={-20}
                  textAnchor="end"
                />
                <YAxis
                  stroke={isDark ? "#8696A0" : "#64748B"}
                  tick={{ fontSize: 10, fontFamily: "Inter, sans-serif" }}
                />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar
                  dataKey="incidents2025"
                  name="2025 Incidents"
                  fill={isDark ? "#53BDEB" : "#2563EB"}
                  radius={[3, 3, 0, 0]}
                />
                <Bar
                  dataKey="ratePerLakh"
                  name="Rate / Lakh Pop"
                  fill={isDark ? "#FFB02E" : "#F59E0B"}
                  radius={[3, 3, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      {/* 3. Police Investigation Pendency vs Court Conviction Rate */}
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {/* Police Disposal & Chargesheeting */}
        <Panel
          title="Police Investigation Disposal & Pendency (data.gov.in)"
          action={
            <span className="font-mono text-xs text-[var(--text-secondary)]">
              Chargesheet Velocity
            </span>
          }
        >
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {policeDisposal.map((p) => (
              <div
                key={p.Crime_Head}
                className="flex items-center justify-between rounded border border-[var(--border-theme)] bg-[var(--card-bg)] p-2.5 text-xs transition-colors hover:border-[var(--brand)]"
              >
                <div className="min-w-0 flex-1 pr-3">
                  <span className="font-semibold text-[var(--text-primary)] block truncate">
                    {p.Crime_Head}
                  </span>
                  <div className="flex items-center gap-3 text-[10px] text-[var(--text-secondary)] mt-0.5 font-mono">
                    <span>Investigated: {p.Total_Investigated.toLocaleString()}</span>
                    <span>Pending: {p.Pending_Investigation.toLocaleString()}</span>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <span className="font-display font-bold text-[var(--text-primary)] block">
                    {p.Chargesheeted.toLocaleString()} Filed
                  </span>
                  <span className="text-[10px] text-[var(--success)] font-semibold">
                    {p.Chargesheet_Rate}% Chargesheet
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        {/* Court Trial Disposal & Conviction Rate */}
        <Panel
          title="Court Trial Outcomes & Conviction Rates (data.gov.in)"
          action={
            <span className="font-mono text-xs text-[var(--text-secondary)]">
              Judicial Adjudication
            </span>
          }
        >
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {courtDisposal.map((c) => (
              <div
                key={c.Crime_Head}
                className="flex items-center justify-between rounded border border-[var(--border-theme)] bg-[var(--card-bg)] p-2.5 text-xs transition-colors hover:border-[var(--brand)]"
              >
                <div className="min-w-0 flex-1 pr-3">
                  <span className="font-semibold text-[var(--text-primary)] block truncate">
                    {c.Crime_Head}
                  </span>
                  <div className="flex items-center gap-3 text-[10px] text-[var(--text-secondary)] mt-0.5 font-mono">
                    <span>Total Trials: {c.Total_Trials.toLocaleString()}</span>
                    <span>Pending Trials: {c.Pending_Trial.toLocaleString()}</span>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <span className="font-display font-bold text-[var(--text-primary)] block">
                    {c.Convicted.toLocaleString()} Convicted
                  </span>
                  <span className="text-[10px] text-[var(--brand)] font-semibold">
                    {c.Conviction_Rate}% Conviction Rate
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      {/* 4. Statutory IT Act Legal Offenses Matrix */}
      <div className="mt-4">
        <Panel
          title="Statutory IT Act Sections & Enforcement Telemetry (data.gov.in)"
          action={
            <span className="font-mono text-xs text-[var(--text-secondary)]">
              Statutory IT Act §65-§74
            </span>
          }
        >
          <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
            {ncrbSections.map((sec) => (
              <div
                key={sec.sectionCode}
                className="rounded border border-[var(--border-theme)] bg-[var(--card-bg)] p-3 text-xs shadow-xs hover:border-[var(--brand)] transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-[var(--brand)]">
                    {sec.sectionCode}
                  </span>
                  <span className="rounded bg-[var(--panel-sec)] px-1.5 py-0.5 text-[10px] font-semibold text-[var(--text-secondary)]">
                    {sec.act}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-[var(--text-secondary)] line-clamp-2">
                  {sec.description}
                </p>
                <div className="mt-2.5 flex items-center justify-between border-t border-[var(--divider)] pt-2 text-[10px]">
                  <span className="font-semibold text-[var(--text-primary)]">
                    {sec.totalCases.toLocaleString()} Cases
                  </span>
                  <span className="text-[var(--success)] font-semibold">
                    {sec.chargesheetRate}% Chargesheet
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
