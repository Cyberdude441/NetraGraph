import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import type { Entity } from "@/types";

export const ENTITIES_QUERY_KEY = ["entities"] as const;
export const entityQueryKey = (id: string) => ["entities", id] as const;

/**
 * Hook to fetch all criminal entities
 */
export function useEntities() {
  return useQuery<Entity[]>({
    queryKey: ENTITIES_QUERY_KEY,
    queryFn: () => api.getEntities(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook to fetch a single entity by ID
 */
export function useEntity(id: string | undefined) {
  return useQuery<Entity | undefined>({
    queryKey: entityQueryKey(id ?? ""),
    queryFn: () => (id ? api.getEntity(id) : Promise.resolve(undefined)),
    enabled: Boolean(id),
    staleTime: 1000 * 60 * 5,
  });
}
