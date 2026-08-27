import {
  SYNTHETIC_LOCATIONS,
  SYNTHETIC_SPATIAL_EVENTS,
  type SyntheticLocation,
  type SpatialTimelineEvent,
} from "@/data/syntheticSpatialData";

export interface SharedLocationCluster {
  locationId: string;
  locationName: string;
  city: string;
  latitude: number;
  longitude: number;
  entitiesInvolved: { id: string; name: string; eventCount: number }[];
  totalEventsInWindow: number;
  timeWindowOverlap: string;
  spatialConfidence: number;
  threatLevel: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  explanation: string;
}

export interface LocationActivityMetrics {
  location: SyntheticLocation;
  eventTypesBreakdown: Record<string, number>;
  totalFinancialVolumeINR: number;
  uniqueSuspectsCount: number;
  connectedCommunities: string[];
}

/**
 * Scan and detect multi-suspect shared location co-presence patterns
 */
export function detectSharedLocationPatterns(
  locations: SyntheticLocation[] = SYNTHETIC_LOCATIONS,
  events: SpatialTimelineEvent[] = SYNTHETIC_SPATIAL_EVENTS
): SharedLocationCluster[] {
  const clusters: SharedLocationCluster[] = [];

  locations.forEach((loc) => {
    const locEvents = events.filter((e) => e.locationId === loc.id);
    const entityEventCount = new Map<string, { name: string; count: number }>();

    locEvents.forEach((e) => {
      if (!entityEventCount.has(e.primaryEntityId)) {
        entityEventCount.set(e.primaryEntityId, { name: e.primaryEntityName, count: 0 });
      }
      entityEventCount.get(e.primaryEntityId)!.count++;

      e.associatedEntityIds.forEach((aId) => {
        if (!entityEventCount.has(aId)) {
          entityEventCount.set(aId, { name: aId, count: 0 });
        }
        entityEventCount.get(aId)!.count++;
      });
    });

    const entitiesInvolved = Array.from(entityEventCount.entries()).map(([id, val]) => ({
      id,
      name: val.name,
      eventCount: val.count,
    }));

    if (entitiesInvolved.length >= 2 || locEvents.length >= 3) {
      clusters.push({
        locationId: loc.id,
        locationName: loc.name,
        city: loc.city,
        latitude: loc.latitude,
        longitude: loc.longitude,
        entitiesInvolved,
        totalEventsInWindow: locEvents.length,
        timeWindowOverlap: "Overlapping Nocturnal Operating Intervals (20:00 - 04:00)",
        spatialConfidence: loc.threatLevel === "CRITICAL" ? 94 : 85,
        threatLevel: loc.threatLevel,
        explanation: `${entitiesInvolved.length} independent suspect profiles registered ${locEvents.length} corroborated events within this tactical facility.`,
      });
    }
  });

  return clusters.sort((a, b) => b.entitiesInvolved.length - a.entitiesInvolved.length);
}

/**
 * Compute detailed analytical metrics for a specific location
 */
export function calculateLocationMetrics(
  locationId: string,
  locations: SyntheticLocation[] = SYNTHETIC_LOCATIONS,
  events: SpatialTimelineEvent[] = SYNTHETIC_SPATIAL_EVENTS
): LocationActivityMetrics | null {
  const loc = locations.find((l) => l.id === locationId);
  if (!loc) return null;

  const locEvents = events.filter((e) => e.locationId === locationId);
  const types: Record<string, number> = {};
  let totalINR = 0;
  const suspects = new Set<string>();

  locEvents.forEach((e) => {
    types[e.eventType] = (types[e.eventType] || 0) + 1;
    if (e.amountINR) totalINR += e.amountINR;
    suspects.add(e.primaryEntityId);
    e.associatedEntityIds.forEach((a) => suspects.add(a));
  });

  return {
    location: loc,
    eventTypesBreakdown: types,
    totalFinancialVolumeINR: totalINR,
    uniqueSuspectsCount: suspects.size || loc.connectedEntityIds.length,
    connectedCommunities: [loc.associatedCommunity],
  };
}
