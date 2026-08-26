import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import type { Case } from "@/types";

export const CASES_QUERY_KEY = ["cases"] as const;
export const caseQueryKey = (id: string) => ["cases", id] as const;

/**
 * Hook to fetch all investigation cases
 */
export function useCases() {
  return useQuery<Case[]>({
    queryKey: CASES_QUERY_KEY,
    queryFn: () => api.getCases(),
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * Hook to fetch a single case by ID
 */
export function useCase(id: string | undefined) {
  return useQuery<Case | undefined>({
    queryKey: caseQueryKey(id ?? ""),
    queryFn: () => (id ? api.getCase(id) : Promise.resolve(undefined)),
    enabled: Boolean(id),
    staleTime: 1000 * 60 * 5,
  });
}
