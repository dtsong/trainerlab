"use client";

import { useState } from "react";
import Link from "next/link";
import { AdminHeader, DataTable } from "@/components/admin";
import type { Column } from "@/components/admin";
import { useLabNotesAdmin } from "@/hooks/useLabNotesAdmin";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { labNoteTypeLabels } from "@trainerlab/shared-types";
import type {
  ApiLabNoteSummary,
  LabNoteStatus,
} from "@trainerlab/shared-types";

const LIMIT = 25;

const STATUS_COLORS: Record<LabNoteStatus, string> = {
  draft: "border-zinc-600 text-zinc-400",
  review: "border-amber-600 text-amber-400",
  published: "border-teal-600 text-teal-400",
  archived: "border-red-600 text-red-400",
};

const STATUS_FILTERS: { label: string; value: LabNoteStatus | null }[] = [
  { label: "All", value: null },
  { label: "Draft", value: "draft" },
  { label: "Review", value: "review" },
  { label: "Published", value: "published" },
  { label: "Archived", value: "archived" },
];

const columns: Column<ApiLabNoteSummary>[] = [
  {
    key: "title",
    header: "Title",
    render: (row) => (
      <Link
        href={`/admin/lab-notes/${row.id}`}
        className="text-zinc-200 underline-offset-4 hover:text-teal-400 hover:underline"
        onClick={(e) => e.stopPropagation()}
      >
        {row.title}
      </Link>
    ),
  },
  {
    key: "note_type",
    header: "Type",
    render: (row) => (
      <Badge
        variant="outline"
        className="border-zinc-700 font-mono text-xs text-zinc-400"
      >
        {labNoteTypeLabels[row.note_type]}
      </Badge>
    ),
  },
  {
    key: "status",
    header: "Status",
    render: (row) => (
      <Badge
        variant="outline"
        className={`font-mono text-xs ${STATUS_COLORS[row.status]}`}
      >
        {row.status}
      </Badge>
    ),
  },
  {
    key: "author",
    header: "Author",
    render: (row) => row.author_name ?? "-",
  },
  {
    key: "updated",
    header: "Updated",
    render: (row) => {
      const date = row.published_at ?? row.created_at;
      return new Date(date).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    },
    className: "whitespace-nowrap",
  },
];

export default function AdminLabNotesPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<LabNoteStatus | null>(null);

  const { data, isLoading } = useLabNotesAdmin({
    page,
    limit: LIMIT,
    status: statusFilter ?? undefined,
  });

  const totalPages = data ? Math.ceil(data.total / LIMIT) : 1;

  return (
    <>
      <AdminHeader title="Lab Notes" />
      <div className="flex-1 overflow-auto p-6">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex gap-1">
            {STATUS_FILTERS.map((filter) => (
              <button
                key={filter.label}
                onClick={() => {
                  setStatusFilter(filter.value);
                  setPage(1);
                }}
                className={`rounded-full px-3 py-1 font-mono text-xs transition-colors ${
                  statusFilter === filter.value
                    ? "bg-zinc-700 text-zinc-100"
                    : "text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
          <Link href="/admin/lab-notes/new">
            <Button
              size="sm"
              className="bg-teal-600 font-mono text-xs text-white hover:bg-teal-500"
            >
              New Note
            </Button>
          </Link>
        </div>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
          isLoading={isLoading}
          rowKey={(row) => row.id}
        />
      </div>
    </>
  );
}
