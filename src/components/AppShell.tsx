import { Link, useRouterState, useNavigate } from "@tanstack/react-router";
import {
  Bot,
  ChevronRight,
  Clock,
  Database,
  FileText,
  Flame,
  FolderSearch,
  History,
  LayoutDashboard,
  MapPin,
  Menu,
  Moon,
  Network,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Sun,
  TrendingUp,
  Users,
  X,
} from "lucide-react";
import { useState, useRef, useEffect, type ReactNode } from "react";

import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";
import { NetraLogo } from "./brand/NetraLogo";
import { DataIngestionModal } from "./ingestion/DataIngestionModal";
import { DemoTourModal } from "./DemoMode/DemoTourModal";

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  time: string;
  type: "critical" | "warning" | "verified" | "info";
  unread: boolean;
  link?: string;
  caseRef?: string;
}

export function RiskTone(score: number): {
  color: string;
  bg: string;
  border: string;
  label: string;
} {
  if (score >= 85) {
    return {
      color: "#DC2626",
      bg: "#FEE2E2",
      border: "#FCA5A5",
      label: "Critical Risk",
    };
  }
  if (score >= 70) {
    return {
      color: "#EA580C",
      bg: "#FFEDD5",
      border: "#FDBA74",
      label: "High Watch",
    };
  }
  if (score >= 50) {
    return {
      color: "#F59E0B",
      bg: "#FEF3C7",
      border: "#FCD34D",
      label: "Medium Risk",
    };
  }
  return {
    color: "#16A34A",
    bg: "#D1FAE5",
    border: "#86EFAC",
    label: "Low Risk",
  };
}

const NAV = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  { label: "Case Workspace", to: "/cases", icon: FolderSearch },
  { label: "Entities & Profiles", to: "/profiles", icon: Users },
  { label: "Knowledge Graph", to: "/network", icon: Network },
  { label: "Network Analytics", to: "/analytics", icon: TrendingUp },
  { label: "Alerts & Anomalies", to: "/anomalies", icon: Flame },
  { label: "Geographic Intelligence", to: "/geo-timeline", icon: MapPin },
  { label: "Evidence Vault", to: "/cases", icon: ShieldCheck },
  { label: "Reports & Dossiers", to: "/cases", icon: FileText },
  { label: "AI Assistant", to: "/assistant", icon: Bot },
  { label: "Audit Trail", to: "/cases", icon: History },
] as const;

function SidebarContent({
  onNavigate,
  onOpenSettings,
  onOpenIngest,
}: {
  onNavigate?: () => void;
  onOpenSettings?: () => void;
  onOpenIngest?: () => void;
}) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const navigate = useNavigate();

  return (
    <div className="flex h-full min-h-0 flex-col bg-[#064E3B] text-[#E2E8F0] transition-colors duration-200 select-none">
      {/* Sticky brand header */}
      <div className="sticky top-0 z-10 shrink-0 border-b border-[#065F46] bg-[#064E3B] p-4">
        <Link
          to="/dashboard"
          onClick={onNavigate}
          className="flex items-center justify-center gap-2.5 px-1 py-1 transition-opacity hover:opacity-90 lg:justify-start"
        >
          <NetraLogo size={30} inverted />
        </Link>
      </div>

      {/* Navigation and quick actions scroll together */}
      <div className="min-h-0 flex-1 overflow-y-auto px-2 py-3 lg:px-4 [scrollbar-color:#10B981_transparent] [scrollbar-width:thin]">
      <div className="space-y-4">

        {/* Navigation Items */}
        <nav className="flex flex-col gap-1 pt-2">
          <div className="px-2 pb-1 text-[11px] font-bold uppercase tracking-wider text-[#86EFAC]/70">
            Navigation
          </div>
          {NAV.map((item) => {
            const active = pathname === item.to;
            return (
              <Link
                key={item.label}
                to={item.to}
                onClick={onNavigate}
                className={cn(
                  "group flex items-center gap-3 rounded-md px-3 py-2 text-xs font-medium transition-all lg:justify-start justify-center",
                  active
                    ? "bg-[#16A34A] text-white font-semibold shadow-xs"
                    : "text-[#D1D5DB] hover:bg-[#064E3B] hover:text-white"
                )}
              >
                <item.icon
                  className={cn(
                    "size-4 shrink-0 transition-colors",
                    active ? "text-white" : "text-[#9CA3AF] group-hover:text-white"
                  )}
                />
                <span className="hidden truncate lg:inline">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Quick Actions Section */}
        <div className="pt-2 border-t border-[#064E3B]">
          <div className="hidden px-2 pb-2 text-[11px] font-bold uppercase tracking-wider text-[#86EFAC]/70 lg:block">
            Quick Actions
          </div>
          <div className="space-y-1">
            <button
              onClick={() => {
                if (onNavigate) onNavigate();
                if (onOpenIngest) onOpenIngest();
              }}
              className="group flex w-full items-center gap-2.5 rounded-md px-3 py-1.5 text-xs text-[#D1D5DB] hover:bg-[#065F46] hover:text-white transition-colors text-left cursor-pointer lg:justify-start justify-center"
            >
              <Plus className="size-3.5 text-[#86EFAC]" />
              <span className="hidden lg:inline">Ingest Evidence</span>
            </button>
            <button
              onClick={() => {
                if (onNavigate) onNavigate();
                if (onOpenIngest) onOpenIngest();
              }}
              className="group flex w-full items-center gap-2.5 rounded-md px-3 py-1.5 text-xs text-[#D1D5DB] hover:bg-[#065F46] hover:text-white transition-colors text-left cursor-pointer lg:justify-start justify-center"
            >
              <Database className="size-3.5 text-[#86EFAC]" />
              <span className="hidden lg:inline">Import Entity List</span>
            </button>
            <button
              onClick={() => {
                if (onNavigate) onNavigate();
                navigate({ to: "/cases" });
              }}
              className="group flex w-full items-center gap-2.5 rounded-md px-3 py-1.5 text-xs text-[#D1D5DB] hover:bg-[#065F46] hover:text-white transition-colors text-left cursor-pointer lg:justify-start justify-center"
            >
              <FileText className="size-3.5 text-[#86EFAC]" />
              <span className="hidden lg:inline">Generate Report</span>
            </button>
            <button
              onClick={() => {
                if (onNavigate) onNavigate();
                navigate({ to: "/network" });
              }}
              className="group flex w-full items-center gap-2.5 rounded-md px-3 py-1.5 text-xs text-[#D1D5DB] hover:bg-[#065F46] hover:text-white transition-colors text-left cursor-pointer lg:justify-start justify-center"
            >
              <Network className="size-3.5 text-[#86EFAC]" />
              <span className="hidden lg:inline">Trace Network</span>
            </button>
          </div>
        </div>
      </div>

      </div>

      {/* Sticky sidebar footer */}
      <div className="sticky bottom-0 z-10 shrink-0 border-t border-[#065F46] bg-[#064E3B] p-3 space-y-2 text-xs lg:p-4">
        <div className="hidden rounded-md bg-[#065F46] border border-[#047857] p-2.5 lg:block">
          <div className="flex items-center justify-between text-white">
            <span className="flex items-center gap-1.5 font-medium text-[11px]">
              <span className="size-2 rounded-full bg-[#22C55E] animate-pulse" />
              Government Grid Live
            </span>
            <span className="font-mono text-[10px] text-[#86EFAC]">v2.4</span>
          </div>
          <p className="mt-1 text-[10px] text-[#9CA3AF] leading-tight">
            IT Act §69B & Official Secrets Act Compliant.
          </p>
        </div>

        <button
          onClick={() => {
            if (onNavigate) onNavigate();
            if (onOpenSettings) onOpenSettings();
          }}
          className="group flex w-full items-center gap-2 rounded-md px-2 py-1 text-xs text-[#9CA3AF] hover:text-white transition-colors text-left cursor-pointer lg:justify-start justify-center"
        >
          <Settings className="size-3.5 text-[#9CA3AF] group-hover:text-white" />
          <span className="hidden lg:inline">System Settings & Audit</span>
        </button>
      </div>
    </div>
  );
}

export function AppShell({
  title,
  subtitle,
  children,
  onIngestSuccess,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  onIngestSuccess?: () => void;
}) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [ingestModalOpen, setIngestModalOpen] = useState(false);
  const [demoTourOpen, setDemoTourOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  const navigate = useNavigate();
  const profileRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileMenuOpen(false);
      }
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setIsSearching(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    navigate({ to: "/network" });
    setIsSearching(false);
  };

  return (
    <div className="min-h-screen bg-[var(--app-bg)] text-[var(--text-primary)] flex flex-col lg:flex-row font-sans transition-colors duration-200 selection:bg-[var(--brand)]/20 selection:text-[var(--brand)]">
      {/* Desktop Sidebar */}
      <aside className="fixed inset-y-0 left-0 top-0 z-40 hidden h-screen min-h-screen w-20 min-w-[80px] overflow-y-auto md:block lg:w-[280px] lg:min-w-[280px]">
        <SidebarContent
          onOpenSettings={() => setSettingsOpen(true)}
          onOpenIngest={() => setIngestModalOpen(true)}
        />
      </aside>

      {/* Mobile Drawer */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            aria-label="Close navigation"
            className="absolute inset-0 bg-black/60 backdrop-blur-xs"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 w-64 bg-[var(--sidebar-bg)] border-r border-[var(--border-theme)] shadow-xl">
            <button
              aria-label="Close navigation"
              onClick={() => setSidebarOpen(false)}
              className="absolute top-3 right-3 text-[var(--text-secondary)] hover:text-[var(--text-primary)] p-1 rounded"
            >
              <X className="size-4" />
            </button>
            <SidebarContent
              onNavigate={() => setSidebarOpen(false)}
              onOpenSettings={() => {
                setSidebarOpen(false);
                setSettingsOpen(true);
              }}
              onOpenIngest={() => {
                setSidebarOpen(false);
                setIngestModalOpen(true);
              }}
            />
          </aside>
        </div>
      )}

      {/* Main Content Viewport */}
      {/* Main Content Viewport */}
      <div className="main-content flex min-w-0 flex-1 flex-col md:pl-20 lg:pl-[280px]">
        {/* Official Top Government Portal Header */}
        <header className="sticky top-0 z-30 border-b border-[#E5E7EB] bg-white transition-colors duration-200">
          <div className="flex items-center justify-between gap-4 px-4 py-3 sm:px-6">
            {/* Left Page Title & Breadcrumb */}
            <div className="flex items-center gap-3 min-w-0">
              <button
                aria-label="Open navigation"
                className="rounded-md border border-[#E5E7EB] bg-[#F8FAF8] p-2 text-[#4B5563] hover:text-[#111827] md:hidden"
                onClick={() => setSidebarOpen(true)}
              >
                <Menu className="size-4" />
              </button>

              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="hidden sm:inline-block size-2 rounded-full bg-[#16A34A]" />
                  <h1 className="truncate font-display text-base font-bold text-[#111827]">
                    {title}
                  </h1>
                </div>
                <p className="truncate text-xs text-[#64748B]">{subtitle}</p>
              </div>
            </div>

            {/* Primary header actions */}
            <div className="flex items-center gap-3">
              {/* Global Quick Search Bar */}
              <div ref={searchRef} className="relative hidden md:block">
                <form onSubmit={handleSearchSubmit}>
                  <div className="flex items-center gap-2 rounded-md border border-[#E5E7EB] bg-[#F8FAF8] px-3.5 py-1.5 text-xs text-[#111827] transition-all focus-within:border-[#16A34A] focus-within:bg-white focus-within:ring-1 focus-within:ring-[#16A34A]">
                    <Search className="size-4 text-[#64748B]" />
                    <input
                      type="text"
                      placeholder="Search cases, entities, evidence..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onFocus={() => setIsSearching(true)}
                      className="w-56 lg:w-72 bg-transparent text-xs text-[#111827] placeholder:text-[#9CA3AF] outline-none"
                    />
                    <kbd className="rounded border border-[#E5E7EB] bg-white px-1.5 py-0.5 text-[10px] font-mono text-[#64748B]">
                      /
                    </kbd>
                  </div>
                </form>
              </div>

              {/* Ingest Quick Button in Header */}
              <button
                type="button"
                onClick={() => setIngestModalOpen(true)}
                className="hidden sm:flex items-center gap-1.5 rounded-md bg-[#064E3B] hover:bg-[#04382A] px-3 py-1.5 text-xs font-semibold text-white transition-all cursor-pointer shadow-xs"
              >
                <Plus className="size-3.5 text-white" />
                <span>Add Record</span>
              </button>

              {/* Officer Profile and secondary actions */}
              <div className="relative" ref={profileRef}>
                <button
                  type="button"
                  onClick={() => setProfileMenuOpen((prev) => !prev)}
                  className="flex items-center gap-2.5 rounded-md border border-[#E5E7EB] bg-[#F8FAF8] px-3 py-1 text-left hover:border-[#16A34A] transition-colors"
                  aria-expanded={profileMenuOpen}
                >
                <div className="flex size-7 items-center justify-center rounded-full bg-[#064E3B] text-white font-sans font-bold text-xs">
                  DB
                </div>
                <div className="hidden sm:block text-left">
                  <span className="block text-xs font-bold text-[#111827] leading-tight">
                    Insp. D. Bose
                  </span>
                  <span className="block text-[10px] text-[#64748B] leading-none">
                    Cyber Crime Cell
                  </span>
                </div>
                </button>
                {profileMenuOpen && (
                  <div className="absolute right-0 top-full z-40 mt-2 w-52 rounded-md border border-[#E2E8F0] bg-white p-1.5 shadow-lg">
                    <button onClick={() => { setDemoTourOpen(true); setProfileMenuOpen(false); }} className="flex w-full items-center gap-2 rounded px-2.5 py-2 text-xs text-[#0F172A] hover:bg-[#ECFDF5]">
                      <Sparkles className="size-3.5 text-[#047857]" /> Demo Tour
                    </button>
                    <button onClick={toggleTheme} className="flex w-full items-center gap-2 rounded px-2.5 py-2 text-xs text-[#0F172A] hover:bg-[#ECFDF5]">
                      {isDark ? <Sun className="size-3.5 text-[#F59E0B]" /> : <Moon className="size-3.5 text-[#047857]" />}
                      {isDark ? "Switch to light mode" : "Switch to dark mode"}
                    </button>
                    <button onClick={() => { setSettingsOpen(true); setProfileMenuOpen(false); }} className="flex w-full items-center gap-2 rounded px-2.5 py-2 text-xs text-[#0F172A] hover:bg-[#ECFDF5]">
                      <Settings className="size-3.5 text-[#047857]" /> System settings
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Page Content Container */}
        <main className="flex-1 px-4 py-5 sm:px-6">{children}</main>

        {/* Global Footer Status Bar */}
        <footer className="border-t border-[#E5E7EB] bg-white px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs text-[#64748B]">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 font-semibold text-[#064E3B]">
              <span className="size-2 rounded-full bg-[#16A34A]" />
              NetraGraph Core v2.4 · Operational
            </span>
            <span className="hidden sm:inline text-[#9CA3AF]">|</span>
            <span className="hidden sm:inline">National Cyber Crime Investigation Network</span>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-[#64748B]">
            <ShieldCheck className="size-3.5 text-[#16A34A]" />
            <span>Official Secrets Act §5 & Section 65B Certified</span>
          </div>
        </footer>
      </div>

      {/* Guided Investigation Demo Tour Modal */}
      <DemoTourModal
        isOpen={demoTourOpen}
        onClose={() => setDemoTourOpen(false)}
      />

      {/* Data Ingestion Modal */}
      <DataIngestionModal
        isOpen={ingestModalOpen}
        onClose={() => setIngestModalOpen(false)}
        onSuccess={() => {
          if (onIngestSuccess) onIngestSuccess();
        }}
      />

      {/* System Settings Modal */}
      {settingsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded border border-[var(--border-theme)] bg-[var(--panel-bg)] p-5 shadow-2xl font-sans">
            <div className="flex items-center justify-between border-b border-[var(--divider)] pb-3">
              <div className="flex items-center gap-2">
                <Settings className="size-4 text-[var(--brand)]" />
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                  Cyber Cell Terminal Settings
                </h3>
              </div>
              <button
                onClick={() => setSettingsOpen(false)}
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] p-1 rounded"
              >
                <X className="size-4" />
              </button>
            </div>

            <div className="mt-4 space-y-3 text-xs text-[var(--text-secondary)]">
              <div className="flex items-center justify-between rounded border border-[var(--border-theme)] bg-[var(--card-bg)] p-3">
                <div>
                  <span className="block font-medium text-[var(--text-primary)]">Appearance Theme</span>
                  <span className="text-[11px] text-[var(--text-secondary)]">
                    Current mode: <strong className="capitalize text-[var(--brand)]">{theme}</strong>
                  </span>
                </div>
                <button
                  onClick={toggleTheme}
                  className="rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-2.5 py-1 text-[11px] font-semibold text-[var(--text-primary)] hover:border-[var(--brand)] cursor-pointer"
                >
                  Toggle to {isDark ? "Light" : "Dark"}
                </button>
              </div>

              <div className="flex items-center justify-between rounded border border-[var(--border-theme)] bg-[var(--card-bg)] p-3">
                <div>
                  <span className="block font-medium text-[var(--text-primary)]">Audit Log Compliance</span>
                  <span className="text-[11px] text-[var(--text-secondary)]">Official Secrets Act §5 & IT Act §69B</span>
                </div>
                <span className="rounded bg-[var(--success)]/15 border border-[var(--success)]/30 px-2 py-0.5 text-[10px] font-semibold text-[var(--success)]">
                  Active
                </span>
              </div>
            </div>

            <div className="mt-5 flex justify-end border-t border-[var(--divider)] pt-3">
              <button
                onClick={() => setSettingsOpen(false)}
                className="rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-4 py-2 text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--border-theme)] transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function Panel({
  title,
  action,
  className,
  children,
}: {
  title: string;
  action?: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  return (
    <section className={cn("rounded-md border border-[#E5E7EB] bg-white p-5 shadow-xs transition-colors duration-200", className)}>
      <div className="mb-4 flex items-center justify-between gap-3 border-b border-[#E5E7EB] pb-3">
        <h2 className="font-display text-sm font-bold text-[#111827]">
          {title}
        </h2>
        {action}
      </div>
      {children}
    </section>
  );
}

export function riskTone(risk: number): string {
  if (risk >= 85) return "text-[#DC2626]";
  if (risk >= 70) return "text-[#EA580C]";
  if (risk >= 50) return "text-[#F59E0B]";
  return "text-[#16A34A]";
}

export function riskBadge(risk: number): { bg: string; text: string; label: string } {
  if (risk >= 85)
    return {
      bg: "bg-red-50 border-red-200",
      text: "text-[#DC2626]",
      label: "Critical Risk",
    };
  if (risk >= 70)
    return {
      bg: "bg-orange-50 border-orange-200",
      text: "text-[#EA580C]",
      label: "High Watch",
    };
  if (risk >= 50)
    return {
      bg: "bg-amber-50 border-amber-200",
      text: "text-[#F59E0B]",
      label: "Medium Watch",
    };
  return {
    bg: "bg-emerald-50 border-emerald-200",
    text: "text-[#16A34A]",
    label: "Low Risk",
  };
}
