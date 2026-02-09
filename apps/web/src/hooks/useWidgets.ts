import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { widgetsApi, type WidgetSearchParams } from "@/lib/api";
import type {
  ApiWidgetCreate,
  ApiWidgetUpdate,
} from "@trainerlab/shared-types";

const WIDGETS_KEY = ["widgets"] as const;

export function useWidgets(params: WidgetSearchParams = {}) {
  return useQuery({
    queryKey: [...WIDGETS_KEY, params],
    queryFn: () => widgetsApi.list(params),
    staleTime: 1000 * 60 * 2,
  });
}

export function useWidget(id: string) {
  return useQuery({
    queryKey: [...WIDGETS_KEY, id],
    queryFn: () => widgetsApi.getById(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  });
}

export function useWidgetData(id: string) {
  return useQuery({
    queryKey: [...WIDGETS_KEY, id, "data"],
    queryFn: () => widgetsApi.getData(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 2,
  });
}

export function useCreateWidget() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: WIDGETS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: (data: ApiWidgetCreate) => widgetsApi.create(data),
    onSuccess,
  });
}

export function useUpdateWidget() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: WIDGETS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ApiWidgetUpdate }) =>
      widgetsApi.update(id, data),
    onSuccess,
  });
}

export function useDeleteWidget() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: WIDGETS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: (id: string) => widgetsApi.delete(id),
    onSuccess,
  });
}

export function useWidgetEmbedCode(id: string) {
  return useQuery({
    queryKey: [...WIDGETS_KEY, id, "embed-code"],
    queryFn: () => widgetsApi.getEmbedCode(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 10,
  });
}
