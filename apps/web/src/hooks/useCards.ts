"use client";

import { useQuery } from "@tanstack/react-query";
import { cardsApi, type CardSearchParams } from "@/lib/api";

export function useCards(params: CardSearchParams = {}) {
  return useQuery({
    queryKey: ["cards", params],
    queryFn: () => cardsApi.search(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function useCard(id: string) {
  return useQuery({
    queryKey: ["card", id],
    queryFn: () => cardsApi.getById(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook for card search in deck builder.
 * Uses React Query for caching - repeated searches hit cache instead of API.
 */
export function useCardSearch(query: string, limit = 20) {
  return useQuery({
    queryKey: ["cards", "search", query, limit],
    queryFn: () => cardsApi.search({ q: query, limit }),
    enabled: query.trim().length > 0,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
