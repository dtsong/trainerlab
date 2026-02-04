"use client";

import { useState } from "react";
import Link from "next/link";
import { AdminHeader, DataTable } from "@/components/admin";
import type { Column } from "@/components/admin";
import { useTranslationsAdmin, useSubmitTranslation } from "@/hooks/useTranslationsAdmin";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type {
  ApiTranslatedContent,
  TranslationStatus,
  ContentType,
} from "@trainerlab/shared-types";

const LIMIT = 25;

const STATUS_COLORS: Record<TranslationStatus, string> = {
  pending: "border-amber-600 text-amber-400",
  completed: "border-teal-600 text-teal-400",
  failed: "border-red-600 text-red-400",
};

const STATUS_FILTERS: { label: string; value: TranslationStatus | null }[] = [
  { label: "All", value: null },
  { label: "Pending", value: "pending" },
  { label: "Completed", value: "completed" },
  { label: "Failed", value: "failed" },
];

const columns: Column<ApiTranslatedContent>[] = [
  {
    key: "source_id",
    header: "Source",
    render: (row) => (
      <Link
        href={`/admin/translations/${row.id}`}
        className="text-zinc-200 underline-offset-4 hover:text-teal-400 hover:underline"
        onClick={(e) => e.stopPropagation()}
      >
        {row.source_id.length > 30
          ? `${row.source_id.slice(0, 30)}...`
          : row.source_id}
      </Link>
    ),
  },
  {
    key: "content_type",
    header: "Type",
    render: (row) => (
      <Badge
        variant="outline"
        className="border-zinc-700 font-mono text-xs text-zinc-400"
      >
        {row.content_type}
      </Badge>
    ),
  },
  {
    key: "status",
    header: "Status",
    render: (row) => (
      <Badge
        variant="outline"
        className={`font-mono text-xs ${STATUS_COLORS[row.status as TranslationStatus]}`}
      >
        {row.status}
      </Badge>
    ),
  },
  {
    key: "original_text",
    header: "Preview",
    render: (row) => (
      <span className="text-zinc-400">
        {row.original_text.slice(0, 50)}
        {row.original_text.length > 50 ? "..." : ""}
      </span>
    ),
  },
  {
    key: "translated_at",
    header: "Translated",
    render: (row) => {
      if (!row.translated_at) return "-";
      return new Date(row.translated_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    },
    className: "whitespace-nowrap",
  },
];

export default function AdminTranslationsPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<TranslationStatus | null>(null);
  const [submitUrl, setSubmitUrl] = useState("");
  const [submitType, setSubmitType] = useState<ContentType>("article");

  const { data, isLoading } = useTranslationsAdmin({
    status: statusFilter ?? undefined,
    limit: LIMIT,
    offset: (page - 1) * LIMIT,
  });

  const submitMutation = useSubmitTranslation();

  const handleSubmit = async () => {
    if (!submitUrl.trim()) return;
    try {
      await submitMutation.mutateAsync({
        url: submitUrl.trim(),
        content_type: submitType,
      });
      setSubmitUrl("");
    } catch (error) {
      console.error("Failed to submit URL:", error);
    }
  };

  const totalPages = data ? Math.ceil(data.total / LIMIT) : 1;

  return (
    <>
      <AdminHeader title="Translations" />
      <div className="flex-1 overflow-auto p-6">
        <div className="mb-6 rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <h3 className="mb-3 font-mono text-sm text-zinc-300">
            Submit URL for Translation
          </h3>
          <div className="flex gap-2">
            <Input
              placeholder="https://pokecabook.com/..."
              value={submitUrl}
              onChange={(e) => setSubmitUrl(e.target.value)}
              className="flex-1 border-zinc-700 bg-zinc-800 font-mono text-sm"
            />
            <select
              value={submitType}
              onChange={(e) => setSubmitType(e.target.value as ContentType)}
              className="rounded border border-zinc-700 bg-zinc-800 px-3 font-mono text-sm text-zinc-300"
            >
              <option value="article">Article</option>
              <option value="tier_list">Tier List</option>
              <option value="tournament_result">Tournament</option>
              <option value="meta_report">Meta Report</option>
            </select>
            <Button
              onClick={handleSubmit}
              disabled={!submitUrl.trim() || submitMutation.isPending}
              className="bg-teal-600 font-mono text-xs text-white hover:bg-teal-500"
            >
              {submitMutation.isPending ? "Submitting..." : "Submit"}
            </Button>
          </div>
        </div>

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
          <Link href="/admin/translations/glossary">
            <Button
              variant="outline"
              size="sm"
              className="border-zinc-700 font-mono text-xs"
            >
              Manage Glossary
            </Button>
          </Link>
        </div>

        <DataTable
          columns={columns}
          data={data?.content ?? []}
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
