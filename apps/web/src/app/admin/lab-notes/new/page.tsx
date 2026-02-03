"use client";

import { AdminHeader } from "@/components/admin";
import { LabNoteEditor } from "@/components/admin/LabNoteEditor";

export default function NewLabNotePage() {
  return (
    <>
      <AdminHeader title="New Lab Note" />
      <LabNoteEditor />
    </>
  );
}
