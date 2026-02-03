"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AdminHeader, StatCard } from "@/components/admin";
import { metaApi } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const REGIONS = ["global", "NA", "EU", "JP", "LATAM", "OCE"] as const;
const FORMATS = ["standard", "expanded"] as const;
const BEST_OFS = [3, 1] as const;

export default function AdminMetaPage() {
  const [region, setRegion] = useState<string>("global");
  const [format, setFormat] = useState<"standard" | "expanded">("standard");
  const [bestOf, setBestOf] = useState<1 | 3>(3);

  const { data, isLoading } = useQuery({
    queryKey: [
      "admin",
      "meta",
      {
        region: region === "global" ? undefined : region,
        format,
        best_of: bestOf,
      },
    ],
    queryFn: () =>
      metaApi.getCurrent({
        region: region === "global" ? undefined : region,
        format,
        best_of: bestOf,
      }),
    staleTime: 1000 * 60 * 5,
  });

  return (
    <>
      <AdminHeader title="Meta Snapshots" />
      <div className="flex-1 overflow-auto p-6">
        <div className="mb-6 flex flex-wrap items-center gap-4">
          <div className="flex flex-col gap-1">
            <label className="font-mono text-xs uppercase tracking-wider text-zinc-500">
              Region
            </label>
            <div className="flex gap-1">
              {REGIONS.map((r) => (
                <button
                  key={r}
                  onClick={() => setRegion(r)}
                  className={`rounded px-2 py-1 font-mono text-xs transition-colors ${
                    region === r
                      ? "bg-zinc-700 text-zinc-100"
                      : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="font-mono text-xs uppercase tracking-wider text-zinc-500">
              Format
            </label>
            <div className="flex gap-1">
              {FORMATS.map((f) => (
                <button
                  key={f}
                  onClick={() => setFormat(f)}
                  className={`rounded px-2 py-1 font-mono text-xs transition-colors ${
                    format === f
                      ? "bg-zinc-700 text-zinc-100"
                      : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="font-mono text-xs uppercase tracking-wider text-zinc-500">
              Best Of
            </label>
            <div className="flex gap-1">
              {BEST_OFS.map((bo) => (
                <button
                  key={bo}
                  onClick={() => setBestOf(bo)}
                  className={`rounded px-2 py-1 font-mono text-xs transition-colors ${
                    bestOf === bo
                      ? "bg-zinc-700 text-zinc-100"
                      : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                  }`}
                >
                  BO{bo}
                </button>
              ))}
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="font-mono text-sm text-zinc-500">Loading...</div>
        ) : !data ? (
          <div className="font-mono text-sm text-zinc-500">
            No meta snapshot found for these filters
          </div>
        ) : (
          <>
            <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <StatCard label="Snapshot Date" value={data.snapshot_date} />
              <StatCard label="Sample Size" value={data.sample_size} />
              <StatCard
                label="Archetypes"
                value={data.archetype_breakdown.length}
              />
            </div>

            <Tabs defaultValue="archetypes">
              <TabsList className="bg-zinc-800/50">
                <TabsTrigger
                  value="archetypes"
                  className="font-mono text-xs data-[state=active]:bg-zinc-700 data-[state=active]:text-zinc-100"
                >
                  Archetypes
                </TabsTrigger>
                <TabsTrigger
                  value="card-usage"
                  className="font-mono text-xs data-[state=active]:bg-zinc-700 data-[state=active]:text-zinc-100"
                >
                  Card Usage
                </TabsTrigger>
                {data.tournaments_included && (
                  <TabsTrigger
                    value="tournaments"
                    className="font-mono text-xs data-[state=active]:bg-zinc-700 data-[state=active]:text-zinc-100"
                  >
                    Tournaments ({data.tournaments_included.length})
                  </TabsTrigger>
                )}
              </TabsList>

              <TabsContent value="archetypes" className="mt-4">
                <div className="space-y-1">
                  {data.archetype_breakdown
                    .sort((a, b) => b.share - a.share)
                    .map((arch) => (
                      <div
                        key={arch.name}
                        className="flex items-center gap-3 rounded border border-zinc-800 bg-zinc-900/50 px-4 py-2"
                      >
                        <div className="w-32 font-mono text-sm text-zinc-200 truncate">
                          {arch.name}
                        </div>
                        <div className="flex-1">
                          <div
                            className="h-2 rounded bg-teal-600/60"
                            style={{
                              width: `${Math.min(arch.share * 100, 100)}%`,
                            }}
                          />
                        </div>
                        <div className="w-16 text-right font-mono text-sm text-zinc-400">
                          {(arch.share * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                </div>
              </TabsContent>

              <TabsContent value="card-usage" className="mt-4">
                {data.card_usage.length === 0 ? (
                  <div className="font-mono text-sm text-zinc-500">
                    No card usage data
                  </div>
                ) : (
                  <div className="space-y-1">
                    {data.card_usage
                      .sort((a, b) => b.inclusion_rate - a.inclusion_rate)
                      .slice(0, 50)
                      .map((card) => (
                        <div
                          key={card.card_id}
                          className="flex items-center gap-3 rounded border border-zinc-800 bg-zinc-900/50 px-4 py-2"
                        >
                          <div className="flex-1 font-mono text-sm text-zinc-200">
                            {card.card_id}
                          </div>
                          <div className="font-mono text-xs text-zinc-400">
                            {(card.inclusion_rate * 100).toFixed(1)}% inclusion
                          </div>
                          <div className="font-mono text-xs text-zinc-500">
                            avg {card.avg_copies.toFixed(1)} copies
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </TabsContent>

              {data.tournaments_included && (
                <TabsContent value="tournaments" className="mt-4">
                  <div className="space-y-1">
                    {data.tournaments_included.map((tId) => (
                      <div
                        key={tId}
                        className="rounded border border-zinc-800 bg-zinc-900/50 px-4 py-2 font-mono text-sm text-zinc-300"
                      >
                        {tId}
                      </div>
                    ))}
                  </div>
                </TabsContent>
              )}
            </Tabs>
          </>
        )}
      </div>
    </>
  );
}
