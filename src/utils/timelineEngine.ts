import {
  SYNTHETIC_SPATIAL_EVENTS,
  type SpatialTimelineEvent,
} from "@/data/syntheticSpatialData";

export interface TimelineFilterOptions {
  eventTypes: Set<string>;
  severityLevels: Set<string>;
  entityId?: string;
  startDate?: string;
  endDate?: string;
  minConfidence: number;
}

export const DEFAULT_TIMELINE_FILTERS: TimelineFilterOptions = {
  eventTypes: new Set([
    "COMMUNICATION",
    "FINANCIAL_TRANSFER",
    "PHYSICAL_MEETING",
    "SIM_SWITCH",
    "CASE_ACTION",
    "AI_DETECTION",
  ]),
  severityLevels: new Set(["critical", "high", "medium", "low"]),
  minConfidence: 0,
};

/**
 * Filter and sort multi-source chronological events
 */
export function filterAndSortTimeline(
  events: SpatialTimelineEvent[] = SYNTHETIC_SPATIAL_EVENTS,
  filters: TimelineFilterOptions = DEFAULT_TIMELINE_FILTERS
): SpatialTimelineEvent[] {
  return events
    .filter((e) => {
      if (!filters.eventTypes.has(e.eventType)) return false;
      if (!filters.severityLevels.has(e.severity)) return false;
      if (e.confidenceScore < filters.minConfidence) return false;

      if (filters.entityId) {
        const matches =
          e.primaryEntityId === filters.entityId ||
          e.associatedEntityIds.includes(filters.entityId);
        if (!matches) return false;
      }

      if (filters.startDate) {
        if (new Date(e.timestamp) < new Date(filters.startDate)) return false;
      }

      if (filters.endDate) {
        if (new Date(e.timestamp) > new Date(filters.endDate)) return false;
      }

      return true;
    })
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}
