import { createFileRoute, useNavigate } from "@tanstack/react-router";
import React, { useState, useMemo, useEffect } from "react";
import {
  MapPin,
  Clock,
  Sparkles,
  Layers,
  Share2,
  Download,
  Filter,
  ShieldAlert,
  ShieldCheck,
  Radio,
  Flame,
  Activity,
  Users,
} from "lucide-react";
import { toast } from "sonner";

import { AppShell } from "@/components/AppShell";
import { IntelligenceMap } from "@/components/GeographicIntelligence/IntelligenceMap";
import { MapFilters, DEFAULT_MAP_FILTERS, type MapFilterState } from "@/components/GeographicIntelligence/MapFilters";
import { LocationPanel } from "@/components/GeographicIntelligence/LocationPanel";
import { EventTimeline } from "@/components/TimelineIntelligence/EventTimeline";
import { PlaybackControls } from "@/components/TimelineIntelligence/PlaybackControls";
import { CorrelationPanel } from "@/components/TimelineIntelligence/CorrelationPanel";

import {
  SYNTHETIC_LOCATIONS,
  SYNTHETIC_SPATIAL_EVENTS,
  type SyntheticLocation,
  type SpatialTimelineEvent,
} from "@/data/syntheticSpatialData";
import {
  detectSharedLocationPatterns,
  type SharedLocationCluster,
} from "@/utils/spatialAnalysis";
import {
  filterAndSortTimeline,
  DEFAULT_TIMELINE_FILTERS,
} from "@/utils/timelineEngine";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/geo-timeline")({
  head: () => ({
    meta: [
      { title: "Geographic & Timeline Intelligence — NetraGraph AI" },
      {
        name: "description",
        content:
          "Enterprise spatial-temporal intelligence: Tactical geographic mapping, multi-source event timelines, cell-tower triangulation, and lag correlation.",
      },
    ],
  }),
  component: GeoTimelinePage,
});

type WorkspaceMode = "map" | "timeline" | "correlations" | "shared_locations";

function GeoTimelinePage() {
  const navigate = useNavigate();

  // Data State
  const [locations] = useState<SyntheticLocation[]>(SYNTHETIC_LOCATIONS);
  const [events] = useState<SpatialTimelineEvent[]>(SYNTHETIC_SPATIAL_EVENTS);

  // View Mode & Selection
  const [activeMode, setActiveMode] = useState<WorkspaceMode>("map");
  const [selectedLocationId, setSelectedLocationId] = useState<string>("LOC-NCR-01");
  const [mapFilters, setMapFilters] = useState<MapFilterState>(DEFAULT_MAP_FILTERS);

  // Playback Engine State
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [progressPct, setProgressPct] = useState<number>(100);

  // Filter Locations
  const filteredLocations = useMemo(() => {
    return locations.filter((loc) => {
      if (!mapFilters.facilityTypes.has(loc.type)) return false;
      if (!mapFilters.threatLevels.has(loc.threatLevel)) return false;
      if (mapFilters.selectedCity !== "ALL" && loc.city !== mapFilters.selectedCity) return false;
      return true;
    });
  }, [locations, mapFilters]);

  // Filter Timeline Events
  const filteredEvents = useMemo(() => {
    return filterAndSortTimeline(events, DEFAULT_TIMELINE_FILTERS);
  }, [events]);

  const selectedLocation = useMemo(() => {
    return locations.find((l) => l.id === selectedLocationId) || locations[0] || null;
  }, [locations, selectedLocationId]);

  const sharedClusters: SharedLocationCluster[] = useMemo(() => {
    return detectSharedLocationPatterns(locations, events);
  }, [locations, events]);

  const cityOptions = useMemo(() => {
    return Array.from(new Set(locations.map((l) => l.city)));
  }, [locations]);

  // Timeline Playback Timer
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setProgressPct((prev) => {
          if (prev >= 100) {
            setIsPlaying(false);
            return 100;
          }
          return Math.min(100, prev + 2 * playbackSpeed);
        });
      }, 300);
    }
    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed]);

  return (
    <AppShell
      title="Geographic & Timeline Intelligence"
      subtitle="Spatial Threat Mapping, Chronological Event Playback & Spatial-Temporal Lag Correlation"
    >
      <div className="flex flex-col h-[calc(100vh-130px)] rounded border border-slate-800 bg-[#0B0F14] shadow-2xl overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP WORKSPACE NAVIGATION & MODE SELECTOR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-[#0E1318] px-4 py-2 z-20">
          <div className="flex items-center gap-1.5 font-mono text-xs">
            {[
              { id: "map", label: "Tactical Map View", icon: MapPin },
              { id: "timeline", label: "Event Timeline Stream", icon: Clock },
              { id: "correlations", label: "Spatial-Temporal Correlations", icon: Sparkles },
              { id: "shared_locations", label: "Shared Location Clusters", icon: Users },
            ].map((tab) => {
              const Icon = tab.icon;
              const active = activeMode === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveMode(tab.id as WorkspaceMode)}
                  className={cn(
                    "flex items-center gap-1.5 rounded px-3 py-1 font-bold transition-all cursor-pointer",
                    active
                      ? "bg-[#1E293B] text-sky-400 border border-sky-500/40 shadow-xs"
                      : "text-slate-400 hover:text-slate-200"
                  )}
                >
                  <Icon className="size-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate({ to: "/network" })}
              className="flex items-center gap-1 rounded border border-sky-500/50 bg-sky-950/40 px-2.5 py-1 text-xs font-mono font-semibold text-sky-300 hover:bg-sky-900/50 transition-colors cursor-pointer"
            >
              <Share2 className="size-3.5" />
              <span>Knowledge Graph</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. THREE-PANEL INVESTIGATION WORKSPACE
           ========================================================================= */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* LEFT PANEL: Filters */}
          <aside className="w-72 border-r border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-slate-800 bg-[#141A21] px-4 py-3">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 flex items-center gap-1.5">
                <Filter className="size-3.5 text-sky-400" />
                Geospatial & Time Filters
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 custom-scrollbar">
              <MapFilters
                filters={mapFilters}
                onFilterChange={setMapFilters}
                onReset={() => setMapFilters(DEFAULT_MAP_FILTERS)}
                cityOptions={cityOptions}
              />
            </div>
          </aside>

          {/* CENTER PANEL: Interactive Map / Timeline / Correlations */}
          <main className="flex-1 h-full overflow-y-auto p-4 custom-scrollbar bg-[#0B0F14] space-y-4">
            {/* View Mode 1: Interactive Tactical Map */}
            {activeMode === "map" && (
              <div className="h-full flex flex-col space-y-3">
                <div className="flex-1 rounded-lg border border-slate-800 overflow-hidden relative">
                  <IntelligenceMap
                    locations={filteredLocations}
                    events={events}
                    selectedLocationId={selectedLocationId}
                    onSelectLocation={(id) => setSelectedLocationId(id)}
                    showHotspots={mapFilters.showHotspots}
                    showVectors={mapFilters.showVectors}
                  />
                </div>
              </div>
            )}

            {/* View Mode 2: Multi-Source Event Timeline & Playback */}
            {activeMode === "timeline" && (
              <div className="space-y-4">
                <PlaybackControls
                  isPlaying={isPlaying}
                  onTogglePlay={() => setIsPlaying((p) => !p)}
                  playbackSpeed={playbackSpeed}
                  onSpeedChange={setPlaybackSpeed}
                  onReset={() => {
                    setIsPlaying(false);
                    setProgressPct(0);
                  }}
                  currentDateLabel="August 2026 Surveillance Horizon"
                  progressPercentage={progressPct}
                  onScrub={setProgressPct}
                />

                <div className="rounded-lg border border-slate-800 bg-[#0E1318] p-4">
                  <EventTimeline
                    events={filteredEvents}
                    onSelectEvent={(evt) => setSelectedLocationId(evt.locationId)}
                    onSelectEntity={(id) => navigate({ to: "/profiles" })}
                  />
                </div>
              </div>
            )}

            {/* View Mode 3: Spatial-Temporal Correlations */}
            {activeMode === "correlations" && (
              <CorrelationPanel
                onSelectLocation={(locId) => {
                  setSelectedLocationId(locId);
                  setActiveMode("map");
                }}
              />
            )}

            {/* View Mode 4: Shared Location Clusters */}
            {activeMode === "shared_locations" && (
              <div className="space-y-3">
                <div className="border-b border-slate-800 pb-2">
                  <h3 className="font-mono text-xs font-bold uppercase text-slate-100 flex items-center gap-2">
                    <Users className="size-4 text-purple-400" />
                    Multi-Suspect Shared Location Clusters ({sharedClusters.length} Tactical Sites)
                  </h3>
                  <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                    Automated spatial scan identified facilities where multiple suspects converged during active operational windows.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  {sharedClusters.map((cluster) => (
                    <div
                      key={cluster.locationId}
                      onClick={() => {
                        setSelectedLocationId(cluster.locationId);
                        setActiveMode("map");
                      }}
                      className="rounded-lg border border-slate-800 bg-[#121820] p-4 space-y-3 hover:border-purple-500/60 transition-all cursor-pointer"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h4 className="font-bold text-slate-100 text-xs uppercase">
                            {cluster.locationName}
                          </h4>
                          <span className="text-[10px] font-mono text-slate-400">
                            {cluster.city} · Coordinates: {cluster.latitude}, {cluster.longitude}
                          </span>
                        </div>

                        <span
                          className={cn(
                            "rounded px-2 py-0.5 font-mono text-[9px] font-bold uppercase",
                            cluster.threatLevel === "CRITICAL"
                              ? "bg-red-950/80 text-red-300 border border-red-500/60"
                              : "bg-amber-950/80 text-amber-300 border border-amber-500/50"
                          )}
                        >
                          {cluster.threatLevel}
                        </span>
                      </div>

                      <div className="rounded bg-[#161D24] p-2.5 border border-slate-800 font-mono text-[11px] space-y-1">
                        <span className="text-[9px] text-slate-500 block uppercase font-bold">
                          Converging Suspect Operatives:
                        </span>
                        <div className="flex flex-wrap gap-1.5 pt-0.5">
                          {cluster.entitiesInvolved.map((e) => (
                            <span
                              key={e.id}
                              className="rounded bg-[#1A2634] px-2 py-0.5 text-sky-200 border border-slate-700 font-bold text-[10px]"
                            >
                              {e.name} ({e.eventCount} Events)
                            </span>
                          ))}
                        </div>
                      </div>

                      <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
                        {cluster.explanation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </main>

          {/* RIGHT PANEL: Location Dossier */}
          <aside className="w-88 border-l border-slate-800 bg-[#0E1318] flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-slate-800 bg-[#141A21] px-4 py-3">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 flex items-center gap-1.5">
                <MapPin className="size-3.5 text-amber-400" />
                Location Dossier
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4 custom-scrollbar">
              <LocationPanel
                location={selectedLocation}
                events={events}
                onSelectEntity={(id) => navigate({ to: "/profiles" })}
              />
            </div>
          </aside>
        </div>

        {/* =========================================================================
            3. BOTTOM STATUS STRIP
           ========================================================================= */}
        <div className="border-t border-slate-800 bg-[#0B0F14] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-400 z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-sky-400 animate-pulse" />
              NETRA SPATIAL-TEMPORAL RADAR
            </span>
            <span>
              Monitored Nodes: <strong className="text-slate-100">{locations.length} Facilities</strong>
            </span>
            <span>
              Corroborated Events: <strong className="text-sky-400">{events.length} Records</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-slate-400">
            <ShieldCheck className="size-3.5 text-emerald-400" />
            <span>Synthetic Research Prototype · Non-Real-World Tracking</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
