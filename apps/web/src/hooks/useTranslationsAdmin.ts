"use client";

import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  translationsAdminApi,
  AdminTranslationsParams,
} from "@/lib/api";
import type {
  ApiSubmitTranslationRequest,
  ApiUpdateTranslationRequest,
  ApiGlossaryTermCreateRequest,
} from "@trainerlab/shared-types";

const ADMIN_TRANSLATIONS_KEY = ["admin", "translations"] as const;
const ADMIN_GLOSSARY_KEY = ["admin", "translations", "glossary"] as const;

/**
 * Hook to fetch admin translation queue.
 */
export function useTranslationsAdmin(params: AdminTranslationsParams = {}) {
  return useQuery({
    queryKey: [...ADMIN_TRANSLATIONS_KEY, params],
    queryFn: () => translationsAdminApi.list(params),
    staleTime: 1000 * 60 * 2,
  });
}

/**
 * Hook to submit a URL for translation.
 */
export function useSubmitTranslation() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ADMIN_TRANSLATIONS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: (data: ApiSubmitTranslationRequest) =>
      translationsAdminApi.submit(data),
    onSuccess,
  });
}

/**
 * Hook to update a translation.
 */
export function useUpdateTranslation() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ADMIN_TRANSLATIONS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ApiUpdateTranslationRequest }) =>
      translationsAdminApi.update(id, data),
    onSuccess,
  });
}

/**
 * Hook to fetch glossary term overrides.
 */
export function useGlossaryTerms(activeOnly = true) {
  return useQuery({
    queryKey: [...ADMIN_GLOSSARY_KEY, activeOnly],
    queryFn: () => translationsAdminApi.listGlossary(activeOnly),
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * Hook to create/update a glossary term.
 */
export function useCreateGlossaryTerm() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ADMIN_GLOSSARY_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: (data: ApiGlossaryTermCreateRequest) =>
      translationsAdminApi.createGlossaryTerm(data),
    onSuccess,
  });
}
