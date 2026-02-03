import { useQuery } from "@tanstack/react-query";

import { formatApi, rotationApi } from "@/lib/api";

export function useCurrentFormat() {
  return useQuery({
    queryKey: ["format", "current"],
    queryFn: () => formatApi.getCurrent(),
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}

export function useUpcomingFormat() {
  return useQuery({
    queryKey: ["format", "upcoming"],
    queryFn: () => formatApi.getUpcoming(),
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}

export function useRotationImpacts(transition: string) {
  return useQuery({
    queryKey: ["rotation", "impacts", transition],
    queryFn: () => rotationApi.getImpacts(transition),
    enabled: !!transition,
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
}

export function useArchetypeRotationImpact(
  archetypeId: string,
  transition?: string
) {
  return useQuery({
    queryKey: ["rotation", "archetype", archetypeId, transition],
    queryFn: () => rotationApi.getArchetypeImpact(archetypeId, transition),
    enabled: !!archetypeId,
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
}
