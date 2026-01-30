"use client";

import { useQuery } from "@tanstack/react-query";
import { setsApi } from "@/lib/api";

export function useSets() {
  return useQuery({
    queryKey: ["sets"],
    queryFn: () => setsApi.list(),
    staleTime: 1000 * 60 * 30, // 30 minutes (sets don't change often)
  });
}

export function useSet(id: string) {
  return useQuery({
    queryKey: ["set", id],
    queryFn: () => setsApi.getById(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 30,
  });
}

export function useSetCards(id: string, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["set-cards", id, page, pageSize],
    queryFn: () => setsApi.getCards(id, page, pageSize),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  });
}
