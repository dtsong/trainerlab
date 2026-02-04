"use client";

import { useQuery } from "@tanstack/react-query";

import { evolutionApi, EvolutionArticlesParams } from "@/lib/api";

const EVOLUTION_STALE_TIME = 1000 * 60 * 15;

export function useEvolutionArticles(params: EvolutionArticlesParams = {}) {
  return useQuery({
    queryKey: ["evolution", "articles", params],
    queryFn: () => evolutionApi.listArticles(params),
    staleTime: EVOLUTION_STALE_TIME,
  });
}

export function useEvolutionArticle(slug: string | null) {
  return useQuery({
    queryKey: ["evolution", "article", slug],
    queryFn: () => evolutionApi.getArticleBySlug(slug!),
    enabled: !!slug,
    staleTime: EVOLUTION_STALE_TIME,
  });
}

export function useArchetypeEvolution(
  archetypeId: string | null,
  limit?: number
) {
  return useQuery({
    queryKey: ["evolution", "archetype", archetypeId, limit],
    queryFn: () => evolutionApi.getArchetypeEvolution(archetypeId!, limit),
    enabled: !!archetypeId,
    staleTime: EVOLUTION_STALE_TIME,
  });
}

export function useArchetypePrediction(archetypeId: string | null) {
  return useQuery({
    queryKey: ["evolution", "prediction", archetypeId],
    queryFn: () => evolutionApi.getArchetypePrediction(archetypeId!),
    enabled: !!archetypeId,
    staleTime: EVOLUTION_STALE_TIME,
  });
}

export function usePredictionAccuracy(limit?: number) {
  return useQuery({
    queryKey: ["evolution", "accuracy", limit],
    queryFn: () => evolutionApi.getAccuracy(limit),
    staleTime: EVOLUTION_STALE_TIME,
  });
}
