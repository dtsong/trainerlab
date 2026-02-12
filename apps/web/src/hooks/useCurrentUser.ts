"use client";

import { useQuery } from "@tanstack/react-query";

import { usersApi } from "@/lib/api";

export function useCurrentUser(enabled = true) {
  return useQuery({
    queryKey: ["users", "me"],
    queryFn: () => usersApi.getMe(),
    enabled,
    staleTime: 1000 * 60,
  });
}
