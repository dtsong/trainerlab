"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AdminHeader, DataTable } from "@/components/admin";
import type { Column } from "@/components/admin";
import { cardsApi } from "@/lib/api";
import type { ApiCardSummary } from "@trainerlab/shared-types";

const LIMIT = 25;

const columns: Column<ApiCardSummary>[] = [
  {
    key: "id",
    header: "ID",
    render: (row) => row.id,
    className: "whitespace-nowrap",
  },
  {
    key: "name",
    header: "Name",
    render: (row) => row.name,
  },
  {
    key: "supertype",
    header: "Supertype",
    render: (row) => row.supertype,
  },
  {
    key: "types",
    header: "Types",
    render: (row) => row.types?.join(", ") ?? "-",
  },
  {
    key: "set_id",
    header: "Set",
    render: (row) => row.set_id,
    className: "whitespace-nowrap",
  },
  {
    key: "rarity",
    header: "Rarity",
    render: (row) => row.rarity ?? "-",
  },
];

export default function AdminCardsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin", "cards", { page, limit: LIMIT, q: query }],
    queryFn: () =>
      cardsApi.search({ page, limit: LIMIT, q: query || undefined }),
    staleTime: 1000 * 60 * 5,
  });

  const totalPages = data ? Math.ceil(data.total / LIMIT) : 1;

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setQuery(search);
    setPage(1);
  }

  return (
    <>
      <AdminHeader title="Cards" />
      <div className="flex-1 overflow-auto p-6">
        <form onSubmit={handleSearch} className="mb-4 flex gap-2">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search cards..."
            className="flex-1 rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 font-mono text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-zinc-500 focus:outline-none"
          />
          <button
            type="submit"
            className="rounded border border-zinc-700 bg-zinc-800 px-4 py-1.5 font-mono text-sm text-zinc-300 hover:bg-zinc-700 hover:text-zinc-100"
          >
            Search
          </button>
        </form>

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
