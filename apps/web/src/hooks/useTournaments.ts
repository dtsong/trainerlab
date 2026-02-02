import { useQuery } from "@tanstack/react-query";

import { tournamentsApi, type TournamentSearchParams } from "@/lib/api";

export function useTournaments(params: TournamentSearchParams = {}) {
  return useQuery({
    queryKey: ["tournaments", params],
    queryFn: () => tournamentsApi.list(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function useTournament(id: string) {
  return useQuery({
    queryKey: ["tournament", id],
    queryFn: () => tournamentsApi.getById(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
}
