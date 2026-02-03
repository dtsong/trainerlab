"use client";

import { useQuery } from "@tanstack/react-query";

import {
  japanApi,
  JapanInnovationParams,
  JapanArchetypeParams,
  JapanSetImpactParams,
  JapanPredictionParams,
  CardCountEvolutionParams,
} from "@/lib/api";

// Japan meta data changes infrequently - use 15 minute stale time
const JAPAN_STALE_TIME = 1000 * 60 * 15;

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
    staleTime: JAPAN_STALE_TIME,
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
    staleTime: JAPAN_STALE_TIME,
  });
}

/**
 * Hook to fetch JP-only archetypes.
 */
export function useJPNewArchetypes(params: JapanArchetypeParams = {}) {
  return useQuery({
    queryKey: ["japan", "archetypes", params.set_code, params.limit],
    queryFn: () => japanApi.listNewArchetypes(params),
    staleTime: JAPAN_STALE_TIME,
  });
}

/**
 * Hook to fetch JP set impacts.
 */
export function useJPSetImpacts(params: JapanSetImpactParams = {}) {
  return useQuery({
    queryKey: ["japan", "set-impacts", params.set_code, params.limit],
    queryFn: () => japanApi.listSetImpacts(params),
    staleTime: JAPAN_STALE_TIME,
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
    staleTime: JAPAN_STALE_TIME,
  });
}

/**
 * Hook to fetch card count evolution for an archetype.
 */
export function useCardCountEvolution(params: CardCountEvolutionParams | null) {
  return useQuery({
    queryKey: [
      "japan",
      "card-count-evolution",
      params?.archetype,
      params?.days,
      params?.top_cards,
    ],
    queryFn: () => japanApi.getCardCountEvolution(params!),
    enabled: !!params?.archetype,
    staleTime: JAPAN_STALE_TIME,
  });
}
