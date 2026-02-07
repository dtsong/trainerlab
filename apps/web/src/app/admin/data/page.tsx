"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AdminHeader } from "@/components/admin";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { adminDataApi } from "@/lib/api";

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    healthy: "bg-emerald-500/20 text-emerald-400",
    stale: "bg-amber-500/20 text-amber-400",
    critical: "bg-red-500/20 text-red-400",
  };
  const dotStyles: Record<string, string> = {
    healthy: "bg-emerald-400",
    stale: "bg-amber-400",
    critical: "bg-red-400",
  };

  const style = styles[status] ?? "bg-zinc-500/20 text-zinc-400";
  const dot = dotStyles[status] ?? "bg-zinc-400";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 font-mono text-xs ${style}`}
    >
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${dot}`} />
      {status}
    </span>
  );
}

function OverviewTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin", "data", "overview"],
    queryFn: () => adminDataApi.getOverview(),
    staleTime: 1000 * 60 * 5,
  });

  if (isLoading) {
    return <div className="font-mono text-sm text-zinc-500">Loading...</div>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {data?.tables.map((table) => (
        <div
          key={table.name}
          className="rounded border border-zinc-800 bg-zinc-900/50 px-4 py-3"
        >
          <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
            {table.name}
          </div>
          <div className="mt-1 font-mono text-2xl font-semibold text-zinc-100">
            {table.row_count.toLocaleString()}
          </div>
          {table.latest_date && (
            <div className="mt-0.5 font-mono text-xs text-zinc-500">
              Latest: {table.latest_date}
            </div>
          )}
          {table.detail && (
            <div className="mt-0.5 font-mono text-xs text-zinc-400">
              {table.detail}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function MetaInspectorTab() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [regionFilter, setRegionFilter] = useState<string>("");
  const [formatFilter, setFormatFilter] = useState<string>("");

  const { data: snapshots, isLoading } = useQuery({
    queryKey: ["admin", "data", "meta-snapshots", regionFilter, formatFilter],
    queryFn: () =>
      adminDataApi.listMetaSnapshots({
        region: regionFilter || undefined,
        format: formatFilter || undefined,
        limit: 50,
      }),
    staleTime: 1000 * 60 * 5,
  });

  const { data: detail } = useQuery({
    queryKey: ["admin", "data", "meta-snapshots", selectedId],
    queryFn: () => adminDataApi.getMetaSnapshotDetail(selectedId!),
    enabled: !!selectedId,
    staleTime: 1000 * 60 * 5,
  });

  return (
    <div className="flex gap-4" style={{ minHeight: "500px" }}>
      {/* Left panel - snapshot list */}
      <div className="w-80 shrink-0 rounded border border-zinc-800 bg-zinc-900/50">
        <div className="flex gap-2 border-b border-zinc-800 p-3">
          <select
            value={regionFilter}
            onChange={(e) => setRegionFilter(e.target.value)}
            className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 font-mono text-xs text-zinc-300"
          >
            <option value="">All Regions</option>
            <option value="Global">Global</option>
            <option value="JP">JP</option>
          </select>
          <select
            value={formatFilter}
            onChange={(e) => setFormatFilter(e.target.value)}
            className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 font-mono text-xs text-zinc-300"
          >
            <option value="">All Formats</option>
            <option value="standard">standard</option>
            <option value="expanded">expanded</option>
          </select>
        </div>
        <div className="max-h-[450px] overflow-auto">
          {isLoading ? (
            <div className="p-3 font-mono text-sm text-zinc-500">
              Loading...
            </div>
          ) : snapshots?.items.length === 0 ? (
            <div className="p-3 font-mono text-sm text-zinc-500">
              No snapshots found
            </div>
          ) : (
            snapshots?.items.map((s) => (
              <button
                key={s.id}
                onClick={() => setSelectedId(s.id)}
                className={`w-full border-b border-zinc-800/50 px-3 py-2 text-left transition-colors ${
                  selectedId === s.id ? "bg-zinc-800" : "hover:bg-zinc-800/50"
                }`}
              >
                <div className="font-mono text-sm text-zinc-200">
                  {s.snapshot_date}
                </div>
                <div className="mt-0.5 font-mono text-xs text-zinc-500">
                  {s.region ?? "Global"} &middot; {s.format} &middot; BO
                  {s.best_of} &middot; n=
                  {s.sample_size}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Right panel - detail */}
      <div className="flex-1 rounded border border-zinc-800 bg-zinc-900/50 p-4">
        {!selectedId ? (
          <div className="flex h-full items-center justify-center font-mono text-sm text-zinc-500">
            Select a snapshot to view details
          </div>
        ) : !detail ? (
          <div className="font-mono text-sm text-zinc-500">Loading...</div>
        ) : (
          <div className="space-y-4">
            <div>
              <h3 className="font-mono text-sm font-semibold text-zinc-200">
                {detail.snapshot_date}
              </h3>
              <div className="mt-1 font-mono text-xs text-zinc-500">
                {detail.region ?? "Global"} &middot; {detail.format} &middot; BO
                {detail.best_of} &middot; Sample: {detail.sample_size} &middot;
                Archetypes: {detail.archetype_count}
                {detail.diversity_index != null &&
                  ` · Diversity: ${detail.diversity_index.toFixed(3)}`}
              </div>
            </div>

            <div>
              <h4 className="mb-1 font-mono text-xs uppercase tracking-wider text-zinc-500">
                Archetype Shares
              </h4>
              <pre className="max-h-64 overflow-auto rounded bg-zinc-950 p-3 font-mono text-xs text-zinc-300">
                {JSON.stringify(detail.archetype_shares, null, 2)}
              </pre>
            </div>

            {detail.tier_assignments && (
              <div>
                <h4 className="mb-1 font-mono text-xs uppercase tracking-wider text-zinc-500">
                  Tier Assignments
                </h4>
                <pre className="max-h-64 overflow-auto rounded bg-zinc-950 p-3 font-mono text-xs text-zinc-300">
                  {JSON.stringify(detail.tier_assignments, null, 2)}
                </pre>
              </div>
            )}

            {detail.card_usage && (
              <div>
                <h4 className="mb-1 font-mono text-xs uppercase tracking-wider text-zinc-500">
                  Card Usage
                </h4>
                <pre className="max-h-64 overflow-auto rounded bg-zinc-950 p-3 font-mono text-xs text-zinc-300">
                  {JSON.stringify(detail.card_usage, null, 2)}
                </pre>
              </div>
            )}

            {detail.jp_signals && (
              <div>
                <h4 className="mb-1 font-mono text-xs uppercase tracking-wider text-zinc-500">
                  JP Signals
                </h4>
                <pre className="max-h-64 overflow-auto rounded bg-zinc-950 p-3 font-mono text-xs text-zinc-300">
                  {JSON.stringify(detail.jp_signals, null, 2)}
                </pre>
              </div>
            )}

            {detail.trends && (
              <div>
                <h4 className="mb-1 font-mono text-xs uppercase tracking-wider text-zinc-500">
                  Trends
                </h4>
                <pre className="max-h-64 overflow-auto rounded bg-zinc-950 p-3 font-mono text-xs text-zinc-300">
                  {JSON.stringify(detail.trends, null, 2)}
                </pre>
              </div>
            )}

            {detail.tournaments_included &&
              detail.tournaments_included.length > 0 && (
                <div>
                  <h4 className="mb-1 font-mono text-xs uppercase tracking-wider text-zinc-500">
                    Tournaments Included ({detail.tournaments_included.length})
                  </h4>
                  <pre className="max-h-64 overflow-auto rounded bg-zinc-950 p-3 font-mono text-xs text-zinc-300">
                    {JSON.stringify(detail.tournaments_included, null, 2)}
                  </pre>
                </div>
              )}
          </div>
        )}
      </div>
    </div>
  );
}

function PipelineHealthTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin", "data", "pipeline-health"],
    queryFn: () => adminDataApi.getPipelineHealth(),
    staleTime: 1000 * 60 * 5,
  });

  if (isLoading) {
    return <div className="font-mono text-sm text-zinc-500">Loading...</div>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {data?.pipelines.map((pipeline) => (
        <div
          key={pipeline.name}
          className="rounded border border-zinc-800 bg-zinc-900/50 px-4 py-3"
        >
          <div className="flex items-center justify-between">
            <div className="font-mono text-sm text-zinc-200">
              {pipeline.name}
            </div>
            <StatusBadge status={pipeline.status} />
          </div>
          <div className="mt-2 font-mono text-xs text-zinc-500">
            {pipeline.last_run ? `Last run: ${pipeline.last_run}` : "Never run"}
          </div>
          {pipeline.days_since_run != null && (
            <div className="mt-0.5 font-mono text-xs text-zinc-400">
              {pipeline.days_since_run === 0
                ? "Today"
                : `${pipeline.days_since_run} day${pipeline.days_since_run === 1 ? "" : "s"} ago`}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function AdminDataPage() {
  return (
    <>
      <AdminHeader title="Data" />
      <div className="flex-1 overflow-auto p-6">
        <Tabs defaultValue="overview">
          <TabsList className="border border-zinc-800 bg-zinc-900/50">
            <TabsTrigger
              value="overview"
              className="font-mono text-xs text-zinc-400 data-[state=active]:bg-zinc-800 data-[state=active]:text-zinc-100"
            >
              Overview
            </TabsTrigger>
            <TabsTrigger
              value="meta-inspector"
              className="font-mono text-xs text-zinc-400 data-[state=active]:bg-zinc-800 data-[state=active]:text-zinc-100"
            >
              Meta Inspector
            </TabsTrigger>
            <TabsTrigger
              value="pipeline-health"
              className="font-mono text-xs text-zinc-400 data-[state=active]:bg-zinc-800 data-[state=active]:text-zinc-100"
            >
              Pipeline Health
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-4">
            <OverviewTab />
          </TabsContent>

          <TabsContent value="meta-inspector" className="mt-4">
            <MetaInspectorTab />
          </TabsContent>

          <TabsContent value="pipeline-health" className="mt-4">
            <PipelineHealthTab />
          </TabsContent>
        </Tabs>
      </div>
    </>
  );
}
