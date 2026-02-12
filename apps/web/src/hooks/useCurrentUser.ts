"use client";

import { useQuery } from "@tanstack/react-query";

import { usersApi } from "@/lib/api";

export function useCurrentUser(
  enabled = true,
  options?: {
    staleTimeMs?: number;
  }
) {
  return useQuery({
    queryKey: ["users", "me"],
    queryFn: () => usersApi.getMe(),
    enabled,
    staleTime: options?.staleTimeMs ?? 1000 * 60,
    refetchOnMount: "always",
    refetchOnWindowFocus: true,
  });
}
