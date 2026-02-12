"use client";

import { useQuery } from "@tanstack/react-query";

import { publicApi } from "@/lib/api";

export function useHomeTeaser(format: "standard" | "expanded" = "standard") {
  return useQuery({
    queryKey: ["public", "home-teaser", format],
    queryFn: () => publicApi.getHomeTeaser(format),
    staleTime: 1000 * 60 * 5,
  });
}
