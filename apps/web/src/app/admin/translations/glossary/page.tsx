"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AdminHeader, DataTable } from "@/components/admin";
import type { Column } from "@/components/admin";
import {
  useGlossaryTerms,
  useCreateGlossaryTerm,
} from "@/hooks/useTranslationsAdmin";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ApiGlossaryTermOverride } from "@trainerlab/shared-types";

const columns: Column<ApiGlossaryTermOverride>[] = [
  {
    key: "term_jp",
    header: "Japanese",
    render: (row) => (
      <span className="font-mono text-zinc-200">{row.term_jp}</span>
    ),
  },
  {
    key: "term_en",
    header: "English",
    render: (row) => (
      <span className="font-mono text-teal-400">{row.term_en}</span>
    ),
  },
  {
    key: "context",
    header: "Context",
    render: (row) => (
      <span className="text-zinc-400">{row.context || "-"}</span>
    ),
  },
  {
    key: "source",
    header: "Source",
    render: (row) => (
      <Badge
        variant="outline"
        className="border-zinc-700 font-mono text-xs text-zinc-500"
      >
        {row.source || "manual"}
      </Badge>
    ),
  },
  {
    key: "is_active",
    header: "Active",
    render: (row) => (
      <Badge
        variant="outline"
        className={`font-mono text-xs ${
          row.is_active
            ? "border-teal-600 text-teal-400"
            : "border-zinc-600 text-zinc-500"
        }`}
      >
        {row.is_active ? "Active" : "Inactive"}
      </Badge>
    ),
  },
];

export default function GlossaryPage() {
  const router = useRouter();
  const [activeOnly, setActiveOnly] = useState(true);
  const [newTermJp, setNewTermJp] = useState("");
  const [newTermEn, setNewTermEn] = useState("");
  const [newContext, setNewContext] = useState("");

  const { data, isLoading } = useGlossaryTerms(activeOnly);
  const createMutation = useCreateGlossaryTerm();

  const handleCreate = async () => {
    if (!newTermJp.trim() || !newTermEn.trim()) return;
    try {
      await createMutation.mutateAsync({
        term_jp: newTermJp.trim(),
        term_en: newTermEn.trim(),
        context: newContext.trim() || null,
      });
      setNewTermJp("");
      setNewTermEn("");
      setNewContext("");
    } catch (error) {
      console.error("Failed to create term:", error);
    }
  };

  return (
    <>
      <AdminHeader title="Translation Glossary" />
      <div className="flex-1 overflow-auto p-6">
        <div className="mb-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/admin/translations")}
            className="font-mono text-xs text-zinc-400"
          >
            ← Back to Translations
          </Button>
        </div>

        <div className="mb-6 rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <h3 className="mb-3 font-mono text-sm text-zinc-300">
            Add/Update Term Override
          </h3>
          <div className="grid gap-2 sm:grid-cols-4">
            <Input
              placeholder="Japanese term"
              value={newTermJp}
              onChange={(e) => setNewTermJp(e.target.value)}
              className="border-zinc-700 bg-zinc-800 font-mono text-sm"
            />
            <Input
              placeholder="English translation"
              value={newTermEn}
              onChange={(e) => setNewTermEn(e.target.value)}
              className="border-zinc-700 bg-zinc-800 font-mono text-sm"
            />
            <Input
              placeholder="Context (optional)"
              value={newContext}
              onChange={(e) => setNewContext(e.target.value)}
              className="border-zinc-700 bg-zinc-800 font-mono text-sm"
            />
            <Button
              onClick={handleCreate}
              disabled={
                !newTermJp.trim() ||
                !newTermEn.trim() ||
                createMutation.isPending
              }
              className="bg-teal-600 font-mono text-xs text-white hover:bg-teal-500"
            >
              {createMutation.isPending ? "Adding..." : "Add Term"}
            </Button>
          </div>
          <p className="mt-2 text-xs text-zinc-500">
            Term overrides take precedence over the static glossary. If a term
            already exists, it will be updated.
          </p>
        </div>

        <div className="mb-4 flex items-center gap-2">
          <button
            onClick={() => setActiveOnly(true)}
            className={`rounded-full px-3 py-1 font-mono text-xs transition-colors ${
              activeOnly
                ? "bg-zinc-700 text-zinc-100"
                : "text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
            }`}
          >
            Active Only
          </button>
          <button
            onClick={() => setActiveOnly(false)}
            className={`rounded-full px-3 py-1 font-mono text-xs transition-colors ${
              !activeOnly
                ? "bg-zinc-700 text-zinc-100"
                : "text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
            }`}
          >
            All Terms
          </button>
        </div>

        <DataTable
          columns={columns}
          data={data?.terms ?? []}
          page={1}
          totalPages={1}
          onPageChange={() => {}}
          isLoading={isLoading}
          rowKey={(row) => row.id}
        />

        {data && (
          <p className="mt-4 text-center font-mono text-xs text-zinc-500">
            {data.total} term override{data.total !== 1 ? "s" : ""}
          </p>
        )}
      </div>
    </>
  );
}
