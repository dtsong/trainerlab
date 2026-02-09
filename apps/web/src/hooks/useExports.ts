import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { exportsApi, type ExportSearchParams } from "@/lib/api";
import type { ApiExportCreate } from "@trainerlab/shared-types";

const EXPORTS_KEY = ["exports"] as const;

export function useExports(params: ExportSearchParams = {}) {
  return useQuery({
    queryKey: [...EXPORTS_KEY, params],
    queryFn: () => exportsApi.list(params),
    staleTime: 1000 * 60 * 2,
  });
}

export function useExport(id: string) {
  return useQuery({
    queryKey: [...EXPORTS_KEY, id],
    queryFn: () => exportsApi.getById(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  });
}

export function useCreateExport() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: EXPORTS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: (data: ApiExportCreate) => exportsApi.create(data),
    onSuccess,
  });
}

export function useExportDownloadUrl(id: string) {
  return useQuery({
    queryKey: [...EXPORTS_KEY, id, "download"],
    queryFn: () => exportsApi.getDownloadUrl(id),
    enabled: !!id,
    staleTime: 1000 * 60,
  });
}
