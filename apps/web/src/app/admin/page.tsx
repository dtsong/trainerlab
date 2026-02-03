"use client";

import { useQuery } from "@tanstack/react-query";
import { AdminHeader, StatCard } from "@/components/admin";
import { tournamentsApi, cardsApi, metaApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

export default function AdminOverviewPage() {
  const tournaments = useQuery({
    queryKey: ["admin", "tournaments", { limit: 10 }],
    queryFn: () => tournamentsApi.list({ limit: 10 }),
    staleTime: 1000 * 60 * 5,
  });

  const cards = useQuery({
    queryKey: ["admin", "cards", { limit: 1 }],
    queryFn: () => cardsApi.search({ limit: 1 }),
    staleTime: 1000 * 60 * 5,
  });

  const meta = useQuery({
    queryKey: ["admin", "meta-current"],
    queryFn: () => metaApi.getCurrent(),
    staleTime: 1000 * 60 * 5,
  });

  return (
    <>
      <AdminHeader title="Overview" />
      <div className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Tournaments"
            value={tournaments.data?.total ?? "..."}
            detail={tournaments.isLoading ? "loading" : undefined}
          />
          <StatCard
            label="Cards"
            value={cards.data?.total ?? "..."}
            detail={cards.isLoading ? "loading" : undefined}
          />
          <StatCard
            label="Meta Archetypes"
            value={meta.data?.archetype_breakdown?.length ?? "..."}
            detail={
              meta.data?.snapshot_date
                ? `as of ${meta.data.snapshot_date}`
                : undefined
            }
          />
          <StatCard
            label="Meta Sample Size"
            value={meta.data?.sample_size ?? "..."}
            detail={
              meta.data?.format ? `${meta.data.format} format` : undefined
            }
          />
        </div>

        <div className="mt-8">
          <h2 className="mb-3 font-mono text-sm uppercase tracking-wider text-zinc-500">
            Recent Tournaments
          </h2>
          {tournaments.isLoading ? (
            <div className="font-mono text-sm text-zinc-500">Loading...</div>
          ) : tournaments.data?.items.length === 0 ? (
            <div className="font-mono text-sm text-zinc-500">
              No tournaments found
            </div>
          ) : (
            <div className="space-y-2">
              {tournaments.data?.items.map((t) => (
                <div
                  key={t.id}
                  className="flex items-center gap-3 rounded border border-zinc-800 bg-zinc-900/50 px-4 py-2.5"
                >
                  <div className="flex-1">
                    <div className="font-mono text-sm text-zinc-200">
                      {t.name}
                    </div>
                    <div className="mt-0.5 font-mono text-xs text-zinc-500">
                      {t.date} &middot; {t.region}
                      {t.country ? ` (${t.country})` : ""}
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className="border-zinc-700 font-mono text-xs text-zinc-400"
                  >
                    {t.format}
                  </Badge>
                  <Badge
                    variant="outline"
                    className="border-zinc-700 font-mono text-xs text-zinc-400"
                  >
                    BO{t.best_of}
                  </Badge>
                  {t.tier && (
                    <Badge
                      variant="outline"
                      className="border-zinc-700 font-mono text-xs text-zinc-400"
                    >
                      {t.tier}
                    </Badge>
                  )}
                  {t.participant_count != null && (
                    <span className="font-mono text-xs text-zinc-500">
                      {t.participant_count} players
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
