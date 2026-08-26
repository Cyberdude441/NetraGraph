import React, { useState } from "react";
import {
  MapPin,
  Radio,
  Building2,
  Cpu,
  Flame,
  ShieldAlert,
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  Navigation,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { SyntheticLocation, SpatialTimelineEvent } from "@/data/syntheticSpatialData";

interface IntelligenceMapProps {
  locations: SyntheticLocation[];
  events: SpatialTimelineEvent[];
  selectedLocationId: string | null;
  onSelectLocation: (id: string) => void;
  showHotspots: boolean;
  showVectors: boolean;
}

const TYPE_ICONS: Record<string, React.ElementType> = {
  CELL_TOWER: Radio,
  SAFEHOUSE: ShieldAlert,
  SHELL_OFFICE: Building2,
  ATM_CDM_KIOSK: Flame,
  SERVER_FARM: Cpu,
  MEETING_POINT: Navigation,
};

export function IntelligenceMap({
  locations,
  events,
  selectedLocationId,
  onSelectLocation,
  showHotspots,
  showVectors,
}: IntelligenceMapProps) {
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Map India geographic bounding box to SVG coordinates (Lat ~8 to 36, Lon ~68 to 97)
  const mapWidth = 900;
  const mapHeight = 650;

  const projectCoords = (lat: number, lon: number) => {
    // Standard Mercator-like projection scale for India subcontinent
    const minLon = 68.0;
    const maxLon = 92.0;
    const minLat = 10.0;
    const maxLat = 32.0;

    const x = ((lon - minLon) / (maxLon - minLon)) * (mapWidth - 100) + 50;
    const y = ((maxLat - lat) / (maxLat - minLat)) * (mapHeight - 100) + 50;

    return { x, y };
  };

  const handleZoomIn = () => setZoom((z) => Math.min(2.5, z + 0.25));
  const handleZoomOut = () => setZoom((z) => Math.max(0.75, z - 0.25));
  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // Vector relationship arcs between connected locations (e.g. Noida -> Mumbai -> Bhubaneswar -> Kolkata)
  const connectionVectors = [
    { from: "LOC-NCR-01", to: "LOC-NCR-02", label: "Tactical Dispatch" },
    { from: "LOC-NCR-02", to: "LOC-MH-01", label: "RTGS Layered Fund Route (₹1.54 Cr)" },
    { from: "LOC-NCR-03", to: "LOC-MH-01", label: "USDT Liquidation Vector" },
    { from: "LOC-OD-01", to: "LOC-NCR-01", label: "GSM Gateway OTP Relays" },
    { from: "LOC-MH-01", to: "LOC-WB-02", label: "Hawala Bullion Clearing" },
    { from: "LOC-WB-01", to: "LOC-NCR-02", label: "Mule Account Flow" },
  ];

  return (
    <div className="relative w-full h-full bg-[#080B0F] overflow-hidden select-none font-sans rounded-lg border border-slate-800">
      {/* Map Tactical HUD Overlay Bar */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-2 bg-[#0E1318]/90 backdrop-blur-md p-1.5 rounded-lg border border-slate-800 font-mono text-[10px]">
        <span className="flex size-2 rounded-full bg-sky-400 animate-pulse" />
        <span className="font-bold text-slate-200 uppercase">
          Tactical Geospatial Grid · Synthetic Telemetry
        </span>
        <span className="text-slate-500">|</span>
        <span className="text-sky-400">{locations.length} Monitored Facilities</span>
      </div>

      {/* Map Zoom / Pan Controls */}
      <div className="absolute top-3 right-3 z-10 flex flex-col gap-1 bg-[#0E1318]/90 backdrop-blur-md p-1 rounded-lg border border-slate-800">
        <button
          onClick={handleZoomIn}
          className="p-1.5 text-slate-400 hover:text-sky-300 hover:bg-slate-800 rounded transition-colors cursor-pointer"
          title="Zoom In"
        >
          <ZoomIn className="size-4" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-1.5 text-slate-400 hover:text-sky-300 hover:bg-slate-800 rounded transition-colors cursor-pointer"
          title="Zoom Out"
        >
          <ZoomOut className="size-4" />
        </button>
        <button
          onClick={handleReset}
          className="p-1.5 text-slate-400 hover:text-sky-300 hover:bg-slate-800 rounded transition-colors cursor-pointer"
          title="Reset View"
        >
          <RotateCcw className="size-4" />
        </button>
      </div>

      {/* Interactive SVG Geospatial Map Canvas */}
      <svg
        viewBox={`0 0 ${mapWidth} ${mapHeight}`}
        className="w-full h-full cursor-grab active:cursor-grabbing transition-transform duration-200"
        style={{
          transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
        }}
      >
        <defs>
          {/* Tactical Grid Pattern */}
          <pattern id="tacticalGrid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#141B24" strokeWidth="0.8" />
          </pattern>

          {/* Glowing Filter for Critical Hotspots */}
          <filter id="glowCrit" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background Grid */}
        <rect width={mapWidth} height={mapHeight} fill="#0A0D13" />
        <rect width={mapWidth} height={mapHeight} fill="url(#tacticalGrid)" />

        {/* Ambient Geographic Regions (Stylized India Boundary Nodes) */}
        <g opacity="0.3" stroke="#1E293B" strokeWidth="1" fill="none" strokeDasharray="3 3">
          <circle cx="280" cy="180" r="110" /> {/* Northern NCR */}
          <circle cx="240" cy="420" r="90" /> {/* Western Mumbai */}
          <circle cx="580" cy="380" r="95" /> {/* Eastern Odisha */}
          <circle cx="680" cy="320" r="90" /> {/* Kolkata */}
          <circle cx="340" cy="540" r="75" /> {/* Southern Bengaluru */}
        </g>

        {/* Connection Vector Arcs Between Facilities */}
        {showVectors &&
          connectionVectors.map((vec, idx) => {
            const locA = locations.find((l) => l.id === vec.from);
            const locB = locations.find((l) => l.id === vec.to);
            if (!locA || !locB) return null;

            const posA = projectCoords(locA.latitude, locA.longitude);
            const posB = projectCoords(locB.latitude, locB.longitude);

            // Curve control point
            const midX = (posA.x + posB.x) / 2;
            const midY = (posA.y + posB.y) / 2 - 30;

            return (
              <g key={idx} className="group">
                <path
                  d={`M ${posA.x} ${posA.y} Q ${midX} ${midY} ${posB.x} ${posB.y}`}
                  fill="none"
                  stroke="#38BDF8"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                  opacity="0.6"
                  className="animate-pulse"
                />
              </g>
            );
          })}

        {/* Hotspot Threat Density Heat Circles */}
        {showHotspots &&
          locations.map((loc) => {
            const pos = projectCoords(loc.latitude, loc.longitude);
            const isCrit = loc.threatLevel === "CRITICAL";

            return (
              <circle
                key={`heat-${loc.id}`}
                cx={pos.x}
                cy={pos.y}
                r={isCrit ? "45" : "28"}
                fill={isCrit ? "rgba(239, 68, 68, 0.15)" : "rgba(245, 158, 11, 0.12)"}
                stroke={isCrit ? "rgba(239, 68, 68, 0.4)" : "rgba(245, 158, 11, 0.3)"}
                strokeWidth="1"
                filter="url(#glowCrit)"
              />
            );
          })}

        {/* Facility Markers */}
        {locations.map((loc) => {
          const pos = projectCoords(loc.latitude, loc.longitude);
          const isSelected = selectedLocationId === loc.id;
          const isCrit = loc.threatLevel === "CRITICAL";
          const isHigh = loc.threatLevel === "HIGH";

          return (
            <g
              key={loc.id}
              onClick={() => onSelectLocation(loc.id)}
              className="cursor-pointer transition-transform duration-150 hover:scale-110"
              style={{ transformOrigin: `${pos.x}px ${pos.y}px` }}
            >
              {/* Outer Target Ping */}
              {isSelected && (
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="18"
                  fill="none"
                  stroke="#38BDF8"
                  strokeWidth="2"
                  className="animate-ping"
                  opacity="0.75"
                />
              )}

              {/* Marker Pin Base */}
              <circle
                cx={pos.x}
                cy={pos.y}
                r={isSelected ? "11" : "8"}
                fill={isCrit ? "#EF4444" : isHigh ? "#F59E0B" : "#38BDF8"}
                stroke="#0E1318"
                strokeWidth="2.5"
                className="shadow-lg"
              />

              {/* Facility Label */}
              <text
                x={pos.x + 12}
                y={pos.y + 4}
                fill={isSelected ? "#38BDF8" : "#E2E8F0"}
                fontSize={isSelected ? "11" : "9"}
                fontFamily="Inter, monospace"
                fontWeight="bold"
                className="select-none"
              >
                {loc.name}
              </text>

              {/* Sub-label: City & Events */}
              <text
                x={pos.x + 12}
                y={pos.y + 16}
                fill="#94A3B8"
                fontSize="8"
                fontFamily="monospace"
                className="select-none"
              >
                {loc.city} · {loc.totalEventsCount} Events
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
