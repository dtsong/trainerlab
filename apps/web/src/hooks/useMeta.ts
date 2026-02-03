"use client";

import { useQuery, useQueries } from "@tanstack/react-query";

import { metaApi, type MetaSearchParams } from "@/lib/api";

const META_STALE_TIME = 1000 * 60 * 5; // 5 minutes

export function useCurrentMeta(params: MetaSearchParams = {}) {
  return useQuery({
    queryKey: ["meta", "current", params],
    queryFn: () => metaApi.getCurrent(params),
    staleTime: META_STALE_TIME,
  });
}

export function useMetaHistory(params: MetaSearchParams = {}) {
  return useQuery({
    queryKey: ["meta", "history", params],
    queryFn: () => metaApi.getHistory(params),
    staleTime: META_STALE_TIME,
  });
}

/**
 * Convenience hook for homepage: fetches global meta (BO3), JP meta (BO1),
 * and 30-day history in parallel. React Query deduplicates shared queries.
 */
export function useHomeMetaData() {
  const results = useQueries({
    queries: [
      {
        queryKey: ["meta", "current", { best_of: 3 as const }],
        queryFn: () => metaApi.getCurrent({ best_of: 3 }),
        staleTime: META_STALE_TIME,
      },
      {
        queryKey: ["meta", "current", { region: "JP", best_of: 1 as const }],
        queryFn: () => metaApi.getCurrent({ region: "JP", best_of: 1 }),
        staleTime: META_STALE_TIME,
      },
      {
        queryKey: ["meta", "history", { best_of: 3 as const, days: 30 }],
        queryFn: () => metaApi.getHistory({ best_of: 3, days: 30 }),
        staleTime: META_STALE_TIME,
      },
    ],
  });

  const [globalMeta, jpMeta, history] = results;

  return {
    globalMeta: globalMeta.data,
    jpMeta: jpMeta.data,
    history: history.data,
    isLoading: results.some((r) => r.isLoading),
    isError: results.some((r) => r.isError),
    errors: results.map((r) => r.error).filter((e): e is Error => e != null),
    refetch: () => results.forEach((r) => r.refetch()),
  };
}
