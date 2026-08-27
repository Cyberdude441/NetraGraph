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
      subtitle="Spatial Threat Mapping, Chronological Event Playback & Location Co-Occurrence Analysis"
    >
      <div className="flex min-h-[calc(100vh-130px)] flex-col rounded-md border border-[#E5E7EB] bg-white shadow-xs overflow-hidden relative select-none font-sans">
        {/* =========================================================================
            1. TOP WORKSPACE NAVIGATION & MODE SELECTOR
           ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E5E7EB] bg-[#F8FAF8] px-4 py-2.5 z-20">
          <div className="flex items-center gap-1.5 text-xs">
            {[
              { id: "map", label: "Geographic Map", icon: MapPin },
              { id: "timeline", label: "Event Timeline", icon: Clock },
              { id: "correlations", label: "Time Correlations", icon: Sparkles },
              { id: "shared_locations", label: "Shared Sites", icon: Users },
            ].map((tab) => {
              const Icon = tab.icon;
              const active = activeMode === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveMode(tab.id as WorkspaceMode)}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-3.5 py-1.5 font-semibold transition-all cursor-pointer",
                    active
                      ? "bg-[#064E3B] text-white shadow-xs"
                      : "text-[#4B5563] hover:text-[#111827] hover:bg-white"
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
              className="flex items-center gap-1.5 rounded-md border border-[#E5E7EB] bg-white px-3 py-1.5 text-xs font-semibold text-[#111827] hover:bg-[#F3F4F6] transition-colors cursor-pointer shadow-xs"
            >
              <Share2 className="size-3.5 text-[#064E3B]" />
              <span>Knowledge Graph</span>
            </button>
          </div>
        </div>

        {/* =========================================================================
            2. THREE-PANEL INVESTIGATION WORKSPACE
           ========================================================================= */}
        <div className="flex min-h-0 flex-1 overflow-hidden relative">
          {/* LEFT PANEL: Filters */}
          <aside className="w-64 shrink-0 border-r border-[#E5E7EB] bg-[#F8FAF8] flex flex-col h-full overflow-hidden select-none xl:w-72">
            <div className="border-b border-[#E5E7EB] bg-white px-4 py-3">
              <span className="text-xs font-bold text-[#111827] flex items-center gap-1.5">
                <Filter className="size-4 text-[#064E3B]" />
                Location & Time Filters
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5">
              <MapFilters
                filters={mapFilters}
                onFilterChange={setMapFilters}
                onReset={() => setMapFilters(DEFAULT_MAP_FILTERS)}
                cityOptions={cityOptions}
              />
            </div>
          </aside>

          {/* CENTER PANEL: Interactive Map / Timeline / Correlations */}
          <main className="min-w-0 flex-1 h-full overflow-y-auto p-4 bg-[#F5F8FC] space-y-4">
            {/* View Mode 1: Interactive Tactical Map */}
            {activeMode === "map" && (
              <div className="h-full flex flex-col space-y-3">
                <div className="flex-1 rounded-md border border-[#D9E2EC] overflow-hidden relative shadow-xs bg-white">
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

                <div className="rounded-md border border-[#D9E2EC] bg-white p-4 shadow-xs">
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
                <div className="border-b border-[#E2E8F0] pb-2">
                  <h3 className="text-xs font-bold text-[#0F172A] flex items-center gap-2">
                    <Users className="size-4 text-[#065F46]" />
                    Multi-Suspect Shared Location Clusters ({sharedClusters.length} Tactical Sites)
                  </h3>
                  <p className="text-xs text-[#64748B] mt-0.5">
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
                      className="rounded-md border border-[#D9E2EC] bg-white p-4 space-y-3 hover:border-[#065F46] transition-all cursor-pointer shadow-xs"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h4 className="font-bold text-[#0F172A] text-xs">
                            {cluster.locationName}
                          </h4>
                          <span className="text-xs text-[#64748B]">
                            {cluster.city} · {cluster.latitude}, {cluster.longitude}
                          </span>
                        </div>

                        <span
                          className={cn(
                            "rounded-md px-2.5 py-0.5 text-xs font-bold",
                            cluster.threatLevel === "CRITICAL"
                              ? "bg-red-50 text-[#DC3545] border border-red-200"
                              : "bg-amber-50 text-[#F59E0B] border border-amber-200"
                          )}
                        >
                          {cluster.threatLevel === "CRITICAL" ? "High Threat" : "Watch"}
                        </span>
                      </div>

                      <div className="rounded-md bg-[#F8FAFC] p-2.5 border border-[#D9E2EC] text-xs space-y-1">
                        <span className="text-xs text-[#64748B] block font-semibold">
                          Converging Suspect Operatives:
                        </span>
                        <div className="flex flex-wrap gap-1.5 pt-0.5">
                          {cluster.entitiesInvolved.map((e) => (
                            <span
                              key={e.id}
                              className="rounded-md bg-white px-2 py-0.5 text-[#065F46] border border-[#D9E2EC] font-semibold text-xs"
                            >
                              {e.name} ({e.eventCount} Events)
                            </span>
                          ))}
                        </div>
                      </div>

                      <p className="text-xs text-[#475569] leading-relaxed">
                        {cluster.explanation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </main>

          {/* RIGHT PANEL: Location Dossier */}
          <aside className="w-88 border-l border-[#D9E2EC] bg-white flex flex-col h-full overflow-hidden select-none">
            <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] px-4 py-3">
              <span className="text-xs font-bold text-[#0F172A] flex items-center gap-1.5">
                <MapPin className="size-4 text-[#065F46]" />
                Location Dossier
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-4">
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
        <div className="border-t border-[#D9E2EC] bg-[#F8FAFC] px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs text-[#64748B] z-20">
          <div className="flex items-center gap-6">
            <span className="font-bold text-[#065F46] flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-[#198754]" />
              NETRA SPATIAL RADAR
            </span>
            <span>
              Tracked Locations: <strong className="text-[#0F172A]">{locations.length} Sites</strong>
            </span>
            <span>
              Corroborated Events: <strong className="text-[#065F46]">{events.length} Records</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 text-xs text-[#64748B]">
            <ShieldCheck className="size-3.5 text-[#198754]" />
            <span>Section 65B Electronic Record Verified</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
