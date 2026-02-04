"use client";

import { useQuery } from "@tanstack/react-query";

import {
  translationsApi,
  JPAdoptionRatesParams,
  JPUpcomingCardsParams,
} from "@/lib/api";

const TRANSLATIONS_STALE_TIME = 1000 * 60 * 15;

/**
 * Hook to fetch JP card adoption rates.
 */
export function useJPAdoptionRates(params: JPAdoptionRatesParams = {}) {
  return useQuery({
    queryKey: ["translations", "adoption-rates", params.days, params.archetype, params.limit],
    queryFn: () => translationsApi.getAdoptionRates(params),
    staleTime: TRANSLATIONS_STALE_TIME,
  });
}

/**
 * Hook to fetch JP unreleased/upcoming cards.
 */
export function useJPUpcomingCards(params: JPUpcomingCardsParams = {}) {
  return useQuery({
    queryKey: [
      "translations",
      "upcoming-cards",
      params.include_released,
      params.min_impact,
      params.limit,
    ],
    queryFn: () => translationsApi.getUpcomingCards(params),
    staleTime: TRANSLATIONS_STALE_TIME,
  });
}
