import { Link, useRouterState, useNavigate } from "@tanstack/react-router";
import {
  Bell,
  Bot,
  CheckCheck,
  ChevronRight,
  FileText,
  FolderSearch,
  LayoutDashboard,
  Menu,
  Moon,
  Network,
  Search,
  Settings,
  ShieldCheck,
  Sun,
  Users,
  X,
  Clock,
  ArrowUpRight,
  Database,
  Plus,
  TrendingUp,
  Flame,
  MapPin,
  Sparkles,
} from "lucide-react";
import { useState, useRef, useEffect, type ReactNode } from "react";

import { cn } from "@/lib/utils";
import { useTheme } from "@/lib/theme";
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
      color: "var(--critical)",
      bg: "rgba(239, 68, 68, 0.12)",
      border: "rgba(239, 68, 68, 0.3)",
      label: "Critical Risk",
    };
  }
  if (score >= 70) {
    return {
      color: "var(--warning)",
      bg: "rgba(245, 158, 11, 0.12)",
      border: "rgba(245, 158, 11, 0.3)",
      label: "High Threat",
    };
  }
  return {
    color: "var(--brand)",
    bg: "rgba(56, 189, 248, 0.12)",
    border: "rgba(56, 189, 248, 0.3)",
    label: "Medium Watch",
  };
}

const NAV = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  { label: "Cases", to: "/cases", icon: FolderSearch },
  { label: "Knowledge Graph", to: "/network", icon: Network },
  { label: "Network Analytics", to: "/analytics", icon: TrendingUp },
  { label: "Anomaly Detection", to: "/anomalies", icon: Flame },
  { label: "Geo & Timeline", to: "/geo-timeline", icon: MapPin },
  { label: "Profiles", to: "/profiles", icon: Users },
  { label: "Evidence", to: "/evidence", icon: ShieldCheck },
  { label: "Reports", to: "/reports", icon: FileText },
  { label: "AI Assistant", to: "/assistant", icon: Bot },
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

  return (
    <div className="flex h-full flex-col justify-between bg-[var(--sidebar-bg)] border-r border-[var(--border-theme)] text-[var(--text-secondary)] p-3 transition-colors duration-200">
      <div className="space-y-4">
        {/* Brand Header */}
        <Link
          to="/dashboard"
          onClick={onNavigate}
          className="flex items-center gap-2 px-2 py-1.5 transition-opacity hover:opacity-90"
        >
          <NetraLogo size={26} />
        </Link>

        {/* Agency Clearance Banner */}
        <div className="rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-3 py-2 text-xs">
          <div className="flex items-center justify-between text-[var(--text-secondary)]">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Classification</span>
            <span className="font-mono text-[9px] font-bold text-[var(--brand)] bg-[var(--card-bg)] px-1.5 py-0.5 rounded border border-[var(--border-theme)]">
              CYBER CELL S-4
            </span>
          </div>
          <p className="mt-1 text-[11px] font-medium text-[var(--text-primary)]">
            Authorized Intelligence Terminal
          </p>
        </div>

        {/* Ingest CTA Button */}
        <button
          type="button"
          onClick={() => {
            if (onNavigate) onNavigate();
            if (onOpenIngest) onOpenIngest();
          }}
          className="flex w-full items-center justify-center gap-2 rounded border border-[var(--border-theme)] bg-[var(--brand-active)] px-3 py-2 text-xs font-semibold uppercase tracking-wider text-[var(--brand)] hover:border-[var(--brand)] transition-all cursor-pointer shadow-xs"
        >
          <Plus className="size-3.5" /> Ingest Evidence / CDR
        </button>

        {/* Navigation Items */}
        <nav className="flex flex-col gap-0.5">
          <div className="px-2 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-disabled)]">
            Investigation Modules
          </div>
          {NAV.map((item) => {
            const active = pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                onClick={onNavigate}
                className={cn(
                  "group flex items-center gap-3 rounded px-3 py-2 text-xs font-medium transition-colors",
                  active
                    ? "bg-[var(--brand-active)] text-[var(--text-primary)] border-l-[3px] border-[var(--brand)] font-semibold"
                    : "text-[var(--text-secondary)] hover:bg-[var(--panel-sec)] hover:text-[var(--text-primary)]"
                )}
              >
                <item.icon
                  className={cn(
                    "size-4 shrink-0 transition-colors",
                    active ? "text-[var(--brand)]" : "text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]"
                  )}
                />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}

          {/* Settings Trigger */}
          <button
            onClick={() => {
              if (onNavigate) onNavigate();
              if (onOpenSettings) onOpenSettings();
            }}
            className="group flex w-full items-center gap-3 rounded px-3 py-2 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--panel-sec)] hover:text-[var(--text-primary)] transition-colors text-left cursor-pointer"
          >
            <Settings className="size-4 shrink-0 text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]" />
            <span>System Settings</span>
          </button>
        </nav>
      </div>

      {/* System Operational Badge */}
      <div className="rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] p-2.5 text-xs">
        <div className="flex items-center justify-between text-[var(--text-primary)]">
          <span className="flex items-center gap-1.5 font-medium text-[11px]">
            <span className="size-2 rounded-full bg-[var(--success)]" />
            Cyber Cell Engine
          </span>
          <span className="font-mono text-[10px] text-[var(--text-secondary)]">v2.4.0</span>
        </div>
        <p className="mt-1 text-[10px] text-[var(--text-secondary)] leading-tight">
          Encrypted Intelligence Ingestion & Graph Analysis.
        </p>
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
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [ingestModalOpen, setIngestModalOpen] = useState(false);
  const [demoTourOpen, setDemoTourOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const navigate = useNavigate();
  const notifRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter((n) => n.unread).length;

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotificationsOpen(false);
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
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-60 lg:block">
        <SidebarContent
          onOpenSettings={() => setSettingsOpen(true)}
          onOpenIngest={() => setIngestModalOpen(true)}
        />
      </aside>

      {/* Mobile Drawer */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
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
      <div className="flex min-w-0 flex-1 flex-col lg:pl-60">
        {/* Top Navigation Header */}
        <header className="sticky top-0 z-30 border-b border-[var(--border-theme)] bg-[var(--header-bg)] transition-colors duration-200">
          <div className="flex items-center justify-between gap-4 px-4 py-2.5 sm:px-6">
            {/* Left Page Title */}
            <div className="flex items-center gap-3 min-w-0">
              <button
                aria-label="Open navigation"
                className="rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] p-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] lg:hidden"
                onClick={() => setSidebarOpen(true)}
              >
                <Menu className="size-4" />
              </button>

              <div className="min-w-0">
                <h1 className="truncate font-display text-base font-semibold text-[var(--text-primary)]">
                  {title}
                </h1>
                <p className="truncate text-xs text-[var(--text-secondary)]">{subtitle}</p>
              </div>
            </div>

            {/* Right Controls: Ingest Button + Search + Theme Switcher + Notifications + Profile */}
            <div className="flex items-center gap-2.5">
              {/* Ingest Quick Button in Header */}
              <button
                type="button"
                onClick={() => setIngestModalOpen(true)}
                className="hidden sm:flex items-center gap-1.5 rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)] hover:border-[var(--brand)] hover:text-[var(--brand)] transition-all cursor-pointer shadow-xs"
              >
                <Database className="size-3.5 text-[var(--brand)]" />
                <span>Ingest Data</span>
              </button>

              {/* Global Search Bar */}
              <div ref={searchRef} className="relative hidden md:block">
                <form onSubmit={handleSearchSubmit}>
                  <div className="flex items-center gap-2 rounded border border-[var(--border-theme)] bg-[var(--input-bg)] px-3 py-1.5 text-xs text-[var(--text-primary)] transition-all focus-within:border-[var(--brand)]">
                    <Search className="size-3.5 text-[var(--text-secondary)]" />
                    <input
                      type="text"
                      placeholder="Search cases, persons, evidence, identifiers..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onFocus={() => setIsSearching(true)}
                      className="w-56 lg:w-64 bg-transparent text-xs text-[var(--text-primary)] placeholder:text-[var(--text-disabled)] outline-none"
                    />
                    <kbd className="rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-1.5 py-0.5 text-[9px] font-mono text-[var(--text-secondary)]">
                      ⌘K
                    </kbd>
                  </div>
                </form>
              </div>

              {/* Synthetic Demo Environment Badge */}
              <span className="hidden xl:inline-flex items-center gap-1 rounded bg-amber-950/60 border border-amber-800/80 px-2 py-0.5 text-[9px] font-mono font-bold text-amber-300">
                <span className="size-1.5 rounded-full bg-amber-400 animate-pulse" />
                DEMO ENVIRONMENT
              </span>

              {/* Guided Demo Tour Trigger */}
              <button
                type="button"
                onClick={() => setDemoTourOpen(true)}
                className="hidden sm:flex items-center gap-1.5 rounded border border-purple-500/50 bg-purple-950/40 px-2.5 py-1 text-xs font-mono font-bold text-purple-300 hover:bg-purple-900/60 transition-all cursor-pointer shadow-xs"
                title="Launch Guided Investigation Walkthrough"
              >
                <Sparkles className="size-3.5 text-purple-400" />
                <span>Demo Tour</span>
              </button>

              {/* Theme Toggle Button (Sun / Moon) */}
              <button
                type="button"
                onClick={toggleTheme}
                title={isDark ? "Switch to light mode" : "Switch to dark mode"}
                aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
                className="relative flex size-8 items-center justify-center rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--brand)] transition-all cursor-pointer shadow-xs"
              >
                {isDark ? (
                  <Sun className="size-4 text-[#FFB02E] animate-in spin-in-180 duration-200" />
                ) : (
                  <Moon className="size-4 text-[#2563EB] animate-in spin-in-180 duration-200" />
                )}
              </button>

              {/* Notification Bell */}
              <div ref={notifRef} className="relative">
                <button
                  aria-label="Open notifications drawer"
                  onClick={() => setNotificationsOpen((prev) => !prev)}
                  className="relative flex size-8 items-center justify-center rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--brand)] transition-all cursor-pointer shadow-xs"
                  title="Notifications"
                >
                  <Bell className="size-4" />
                </button>
              </div>

              {/* User Profile Pill */}
              <div className="flex items-center gap-2.5 rounded border border-[var(--border-theme)] bg-[var(--panel-sec)] px-2.5 py-1">
                <div className="flex size-6 items-center justify-center rounded bg-[var(--brand-active)] text-[var(--brand)] border border-[var(--border-theme)] font-sans font-bold text-[10px]">
                  DB
                </div>
                <div className="hidden sm:block text-left">
                  <span className="block text-xs font-semibold text-[var(--text-primary)] leading-tight">
                    Insp. D. Bose
                  </span>
                  <span className="block text-[10px] text-[var(--text-secondary)] leading-none">
                    Cyber Crime Operations
                  </span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content Container */}
        <main className="flex-1 px-4 py-4 sm:px-6">{children}</main>
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
    <section className={cn("rounded border border-[var(--border-theme)] bg-[var(--panel-bg)] p-4 shadow-sm transition-colors duration-200", className)}>
      <div className="mb-3 flex items-center justify-between gap-3 border-b border-[var(--divider)] pb-2.5">
        <h2 className="font-display text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">
          {title}
        </h2>
        {action}
      </div>
      {children}
    </section>
  );
}

export function riskTone(risk: number): string {
  if (risk >= 85) return "text-[var(--critical)]";
  if (risk >= 70) return "text-[var(--warning)]";
  if (risk >= 50) return "text-[var(--text-secondary)]";
  return "text-[var(--success)]";
}

export function riskBadge(risk: number): { bg: string; text: string; label: string } {
  if (risk >= 85)
    return {
      bg: "bg-[var(--critical)]/15 border-[var(--critical)]/30",
      text: "text-[var(--critical)]",
      label: "CRITICAL",
    };
  if (risk >= 70)
    return {
      bg: "bg-[var(--warning)]/15 border-[var(--warning)]/30",
      text: "text-[var(--warning)]",
      label: "HIGH RISK",
    };
  if (risk >= 50)
    return {
      bg: "bg-[var(--panel-sec)] border-[var(--border-theme)]",
      text: "text-[var(--text-secondary)]",
      label: "MODERATE",
    };
  return {
    bg: "bg-[var(--success)]/15 border-[var(--success)]/30",
    text: "text-[var(--success)]",
    label: "LOW RISK",
  };
}
