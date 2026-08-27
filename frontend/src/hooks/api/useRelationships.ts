import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import type { Relationship } from "@/types";

export const RELATIONSHIPS_QUERY_KEY = ["relationships"] as const;

/**
 * Hook to fetch all criminal network relationships
 */
export function useRelationships() {
  return useQuery<Relationship[]>({
    queryKey: RELATIONSHIPS_QUERY_KEY,
    queryFn: () => api.getRelationships(),
    staleTime: 1000 * 60 * 5,
  });
}
