"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AdminHeader, DataTable } from "@/components/admin";
import type { Column, SortState } from "@/components/admin";
import { tournamentsApi } from "@/lib/api";
import type { ApiTournamentSummary } from "@trainerlab/shared-types";
import { Badge } from "@/components/ui/badge";

const LIMIT = 25;

const columns: Column<ApiTournamentSummary>[] = [
  {
    key: "name",
    header: "Name",
    render: (row) => row.name,
    sortable: true,
  },
  {
    key: "date",
    header: "Date",
    render: (row) => row.date,
    className: "whitespace-nowrap",
    sortable: true,
  },
  {
    key: "region",
    header: "Region",
    render: (row) => (
      <span>
        {row.region}
        {row.country ? ` (${row.country})` : ""}
      </span>
    ),
    sortable: true,
  },
  {
    key: "format",
    header: "Format",
    render: (row) => (
      <Badge
        variant="outline"
        className="border-zinc-700 font-mono text-xs text-zinc-400"
      >
        {row.format}
      </Badge>
    ),
    sortable: true,
  },
  {
    key: "best_of",
    header: "BO",
    render: (row) => `BO${row.best_of}`,
    sortable: true,
  },
  {
    key: "tier",
    header: "Tier",
    render: (row) => row.tier ?? "-",
    sortable: true,
  },
  {
    key: "participants",
    header: "Players",
    render: (row) =>
      row.participant_count != null
        ? row.participant_count.toLocaleString()
        : "-",
    className: "text-right",
    sortable: true,
  },
];

export default function AdminTournamentsPage() {
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<SortState>({
    key: "date",
    direction: "desc",
  });

  function handleSortChange(newSort: SortState) {
    setSort(newSort);
    setPage(1);
  }

  const { data, isLoading } = useQuery({
    queryKey: [
      "admin",
      "tournaments",
      { page, limit: LIMIT, sort_by: sort.key, order: sort.direction },
    ],
    queryFn: () =>
      tournamentsApi.list({
        page,
        limit: LIMIT,
        sort_by: sort.key,
        order: sort.direction,
      }),
    staleTime: 1000 * 60 * 5,
  });

  const totalPages = data ? Math.ceil(data.total / LIMIT) : 1;

  return (
    <>
      <AdminHeader title="Tournaments" />
      <div className="flex-1 overflow-auto p-6">
        <DataTable
          columns={columns}
          data={data?.items ?? []}
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
          isLoading={isLoading}
          rowKey={(row) => row.id}
          sort={sort}
          onSortChange={handleSortChange}
          expandedRow={(row) => (
            <div>
              <div className="mb-2 font-mono text-xs uppercase tracking-wider text-zinc-500">
                Top Placements
              </div>
              {row.top_placements.length === 0 ? (
                <div className="font-mono text-xs text-zinc-500">
                  No placement data
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-1 sm:grid-cols-2 lg:grid-cols-3">
                  {row.top_placements.map((p, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-2 font-mono text-xs text-zinc-300"
                    >
                      <span className="w-6 text-right text-zinc-500">
                        #{p.placement}
                      </span>
                      <span className="text-zinc-200">{p.archetype}</span>
                      {p.player_name && (
                        <span className="text-zinc-500">({p.player_name})</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        />
      </div>
    </>
  );
}
