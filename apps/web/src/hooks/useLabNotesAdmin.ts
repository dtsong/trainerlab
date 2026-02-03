import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { labNotesAdminApi, type AdminLabNotesSearchParams } from "@/lib/api";
import type {
  ApiLabNoteCreateRequest,
  ApiLabNoteUpdateRequest,
  LabNoteStatus,
} from "@trainerlab/shared-types";

const ADMIN_LAB_NOTES_KEY = ["admin", "lab-notes"] as const;

export function useLabNotesAdmin(params: AdminLabNotesSearchParams = {}) {
  return useQuery({
    queryKey: [...ADMIN_LAB_NOTES_KEY, params],
    queryFn: () => labNotesAdminApi.list(params),
    staleTime: 1000 * 60 * 2,
  });
}

export function useLabNoteAdmin(id: string) {
  return useQuery({
    queryKey: [...ADMIN_LAB_NOTES_KEY, id],
    queryFn: () => labNotesAdminApi.getById(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  });
}

export function useCreateLabNote() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ADMIN_LAB_NOTES_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: (data: ApiLabNoteCreateRequest) =>
      labNotesAdminApi.create(data),
    onSuccess,
  });
}

export function useUpdateLabNote() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ADMIN_LAB_NOTES_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ApiLabNoteUpdateRequest }) =>
      labNotesAdminApi.update(id, data),
    onSuccess,
  });
}

export function useUpdateLabNoteStatus() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ADMIN_LAB_NOTES_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: LabNoteStatus }) =>
      labNotesAdminApi.updateStatus(id, { status }),
    onSuccess,
  });
}

export function useDeleteLabNote() {
  const queryClient = useQueryClient();
  const router = useRouter();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ADMIN_LAB_NOTES_KEY });
    router.push("/admin/lab-notes");
  }, [queryClient, router]);

  return useMutation({
    mutationFn: (id: string) => labNotesAdminApi.delete(id),
    onSuccess,
  });
}

export function useLabNoteRevisions(id: string) {
  return useQuery({
    queryKey: [...ADMIN_LAB_NOTES_KEY, id, "revisions"],
    queryFn: () => labNotesAdminApi.listRevisions(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  });
}
