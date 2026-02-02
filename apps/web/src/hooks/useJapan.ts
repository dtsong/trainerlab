"use client";

import { useQuery } from "@tanstack/react-query";

import {
  japanApi,
  JapanInnovationParams,
  JapanArchetypeParams,
  JapanSetImpactParams,
  JapanPredictionParams,
} from "@/lib/api";

/**
 * Hook to fetch JP card innovations.
 */
export function useJPCardInnovations(params: JapanInnovationParams = {}) {
  return useQuery({
    queryKey: [
      "japan",
      "innovations",
      params.set_code,
      params.en_legal,
      params.min_impact,
      params.limit,
    ],
    queryFn: () => japanApi.listInnovations(params),
  });
}

/**
 * Hook to fetch JP card innovation detail.
 */
export function useJPCardInnovationDetail(cardId: string | null) {
  return useQuery({
    queryKey: ["japan", "innovation", cardId],
    queryFn: () => japanApi.getInnovationDetail(cardId!),
    enabled: !!cardId,
  });
}

/**
 * Hook to fetch JP-only archetypes.
 */
export function useJPNewArchetypes(params: JapanArchetypeParams = {}) {
  return useQuery({
    queryKey: ["japan", "archetypes", params.set_code, params.limit],
    queryFn: () => japanApi.listNewArchetypes(params),
  });
}

/**
 * Hook to fetch JP set impacts.
 */
export function useJPSetImpacts(params: JapanSetImpactParams = {}) {
  return useQuery({
    queryKey: ["japan", "set-impacts", params.set_code, params.limit],
    queryFn: () => japanApi.listSetImpacts(params),
  });
}

/**
 * Hook to fetch predictions.
 */
export function usePredictions(params: JapanPredictionParams = {}) {
  return useQuery({
    queryKey: [
      "japan",
      "predictions",
      params.category,
      params.resolved_only,
      params.limit,
    ],
    queryFn: () => japanApi.listPredictions(params),
  });
}
