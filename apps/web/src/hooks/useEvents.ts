import { useQuery } from "@tanstack/react-query";

import { eventsApi, type EventSearchParams } from "@/lib/api";

const EVENTS_KEY = ["events"] as const;

/**
 * Hook to fetch upcoming events with optional filters.
 */
export function useEvents(params: EventSearchParams = {}) {
  return useQuery({
    queryKey: [...EVENTS_KEY, params],
    queryFn: () => eventsApi.list(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook to fetch a single event by ID.
 */
export function useEvent(id: string | null) {
  return useQuery({
    queryKey: [...EVENTS_KEY, id],
    queryFn: () => eventsApi.getById(id!),
    enabled: !!id,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}
