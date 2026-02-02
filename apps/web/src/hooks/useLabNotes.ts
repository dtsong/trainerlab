import { useQuery } from "@tanstack/react-query";

import { labNotesApi, type LabNotesSearchParams } from "@/lib/api";

export function useLabNotes(params: LabNotesSearchParams = {}) {
  return useQuery({
    queryKey: ["lab-notes", params],
    queryFn: () => labNotesApi.list(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function useLabNote(slug: string) {
  return useQuery({
    queryKey: ["lab-note", slug],
    queryFn: () => labNotesApi.getBySlug(slug),
    enabled: !!slug,
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
}
