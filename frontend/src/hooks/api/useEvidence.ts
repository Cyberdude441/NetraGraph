import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import type { DocumentAnalysisResult, Evidence } from "@/types";

export const EVIDENCE_QUERY_KEY = ["evidence"] as const;

/**
 * Hook to fetch all evidence exhibits
 */
export function useEvidence() {
  return useQuery<Evidence[]>({
    queryKey: EVIDENCE_QUERY_KEY,
    queryFn: () => api.getEvidence(),
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * Hook to upload an evidence exhibit
 */
export function useUploadEvidence() {
  const queryClient = useQueryClient();

  return useMutation<Evidence, Error, FormData | Partial<Evidence>>({
    mutationFn: (payload) => api.uploadEvidence(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EVIDENCE_QUERY_KEY });
    },
  });
}

/**
 * Hook to run AI entity extraction on a case document or FIR
 */
export function useAnalyzeDocument() {
  const queryClient = useQueryClient();

  return useMutation<
    DocumentAnalysisResult,
    Error,
    { documentId?: string; content?: string } | FormData
  >({
    mutationFn: (payload) => api.analyzeDocument(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["entities"] });
      queryClient.invalidateQueries({ queryKey: ["relationships"] });
    },
  });
}
