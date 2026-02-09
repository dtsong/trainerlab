import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiKeysApi } from "@/lib/api";
import type { ApiApiKeyCreate } from "@trainerlab/shared-types";

const API_KEYS_KEY = ["api-keys"] as const;

export function useApiKeys() {
  return useQuery({
    queryKey: [...API_KEYS_KEY],
    queryFn: () => apiKeysApi.list(),
    staleTime: 1000 * 60 * 2,
  });
}

export function useApiKey(id: string) {
  return useQuery({
    queryKey: [...API_KEYS_KEY, id],
    queryFn: () => apiKeysApi.getById(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  });
}

export function useCreateApiKey() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: API_KEYS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: (data: ApiApiKeyCreate) => apiKeysApi.create(data),
    onSuccess,
  });
}

export function useRevokeApiKey() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: API_KEYS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: (id: string) => apiKeysApi.revoke(id),
    onSuccess,
  });
}
