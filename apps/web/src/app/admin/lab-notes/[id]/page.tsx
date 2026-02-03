"use client";

import { use } from "react";
import { AdminHeader } from "@/components/admin";
import { LabNoteEditor } from "@/components/admin/LabNoteEditor";
import { useLabNoteAdmin } from "@/hooks/useLabNotesAdmin";

export default function EditLabNotePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: note, isLoading } = useLabNoteAdmin(id);

  if (isLoading) {
    return (
      <>
        <AdminHeader title="Edit Lab Note" />
        <div className="flex flex-1 items-center justify-center">
          <span className="font-mono text-sm text-zinc-500">Loading...</span>
        </div>
      </>
    );
  }

  if (!note) {
    return (
      <>
        <AdminHeader title="Edit Lab Note" />
        <div className="flex flex-1 items-center justify-center">
          <span className="font-mono text-sm text-zinc-500">
            Note not found
          </span>
        </div>
      </>
    );
  }

  return (
    <>
      <AdminHeader title="Edit Lab Note" />
      <LabNoteEditor note={note} />
    </>
  );
}
