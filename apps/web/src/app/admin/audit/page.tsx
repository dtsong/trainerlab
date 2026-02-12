"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { AdminHeader } from "@/components/admin";
import { Button } from "@/components/ui/button";
import { adminAuditApi, type AdminAuditEvent } from "@/lib/api";

function normalizeEmail(value: string): string {
  return value.trim().toLowerCase();
}

function formatWhen(value: string): string {
  // created_at is ISO; keep it compact and UTC-ish.
  return value.replace(".000", "");
}

export default function AdminAuditPage() {
  const [action, setAction] = useState("");
  const [actorEmail, setActorEmail] = useState("");
  const [targetEmail, setTargetEmail] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filters = useMemo(
    () => ({
      action: action.trim() || undefined,
      actor_email: normalizeEmail(actorEmail) || undefined,
      target_email: normalizeEmail(targetEmail) || undefined,
      limit: 200,
      offset: 0,
    }),
    [action, actorEmail, targetEmail]
  );

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["admin", "audit-events", filters],
    queryFn: () => adminAuditApi.listEvents(filters),
    staleTime: 1000 * 10,
  });

  const selected = useMemo<AdminAuditEvent | null>(() => {
    if (!data || !selectedId) return null;
    return data.find((e) => e.id === selectedId) ?? null;
  }, [data, selectedId]);

  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col">
      <AdminHeader title="Audit" />
      <main className="flex-1 overflow-auto px-6 py-6">
        <div className="rounded border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <label className="block">
                <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                  Action
                </div>
                <input
                  value={action}
                  onChange={(e) => setAction(e.target.value)}
                  placeholder="beta.grant"
                  className="mt-1 h-9 w-full rounded border border-zinc-700 bg-zinc-950 px-2 font-mono text-xs text-zinc-200 placeholder:text-zinc-600"
                />
              </label>

              <label className="block">
                <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                  Actor email
                </div>
                <input
                  value={actorEmail}
                  onChange={(e) => setActorEmail(e.target.value)}
                  placeholder="admin@..."
                  className="mt-1 h-9 w-full rounded border border-zinc-700 bg-zinc-950 px-2 font-mono text-xs text-zinc-200 placeholder:text-zinc-600"
                />
              </label>

              <label className="block">
                <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                  Target email
                </div>
                <input
                  value={targetEmail}
                  onChange={(e) => setTargetEmail(e.target.value)}
                  placeholder="user@..."
                  className="mt-1 h-9 w-full rounded border border-zinc-700 bg-zinc-950 px-2 font-mono text-xs text-zinc-200 placeholder:text-zinc-600"
                />
              </label>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-9 border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
                onClick={() => {
                  setAction("");
                  setActorEmail("");
                  setTargetEmail("");
                  setSelectedId(null);
                }}
              >
                Clear
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-9 border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
                onClick={() => refetch()}
                disabled={isFetching}
              >
                {isFetching ? "Refreshing..." : "Refresh"}
              </Button>
            </div>
          </div>

          <div
            className="mt-4 grid gap-4 lg:grid-cols-2"
            style={{ minHeight: "520px" }}
          >
            <div className="rounded border border-zinc-800 bg-zinc-950/40">
              <div className="flex items-center justify-between border-b border-zinc-800 px-3 py-2">
                <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                  Events
                </div>
                <div className="font-mono text-xs text-zinc-500">
                  {data ? `${data.length} loaded` : ""}
                </div>
              </div>

              {isLoading ? (
                <div className="p-3 font-mono text-sm text-zinc-500">
                  Loading...
                </div>
              ) : isError ? (
                <div className="p-3 font-mono text-sm text-zinc-500">
                  Failed to load audit events
                </div>
              ) : (data?.length ?? 0) === 0 ? (
                <div className="p-3 font-mono text-sm text-zinc-500">
                  No events
                </div>
              ) : (
                <div className="max-h-[460px] overflow-auto">
                  {data?.map((e) => {
                    const active = selectedId === e.id;
                    return (
                      <button
                        key={e.id}
                        onClick={() => setSelectedId(e.id)}
                        className={
                          "w-full border-b border-zinc-800/50 px-3 py-2 text-left transition-colors last:border-0 " +
                          (active ? "bg-zinc-800" : "hover:bg-zinc-900/60")
                        }
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="truncate font-mono text-xs text-zinc-300">
                            {formatWhen(e.created_at)}
                          </div>
                          <div className="shrink-0 rounded border border-zinc-700 bg-zinc-950 px-1.5 py-0.5 font-mono text-[10px] text-zinc-400">
                            {e.action}
                          </div>
                        </div>
                        <div className="mt-1 font-mono text-xs text-zinc-500">
                          {e.actor_email} → {e.target_email}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="rounded border border-zinc-800 bg-zinc-950/40">
              <div className="border-b border-zinc-800 px-3 py-2">
                <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                  Detail
                </div>
              </div>

              {!selected ? (
                <div className="flex h-[460px] items-center justify-center p-3 font-mono text-sm text-zinc-500">
                  Select an event
                </div>
              ) : (
                <div className="p-3">
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    <div>
                      <div className="font-mono text-[10px] uppercase tracking-wider text-zinc-500">
                        Action
                      </div>
                      <div className="font-mono text-xs text-zinc-200">
                        {selected.action}
                      </div>
                    </div>
                    <div>
                      <div className="font-mono text-[10px] uppercase tracking-wider text-zinc-500">
                        When
                      </div>
                      <div className="font-mono text-xs text-zinc-200">
                        {formatWhen(selected.created_at)}
                      </div>
                    </div>
                    <div>
                      <div className="font-mono text-[10px] uppercase tracking-wider text-zinc-500">
                        Actor
                      </div>
                      <div className="font-mono text-xs text-zinc-200">
                        {selected.actor_email}
                      </div>
                    </div>
                    <div>
                      <div className="font-mono text-[10px] uppercase tracking-wider text-zinc-500">
                        Target
                      </div>
                      <div className="font-mono text-xs text-zinc-200">
                        {selected.target_email}
                      </div>
                    </div>
                    <div>
                      <div className="font-mono text-[10px] uppercase tracking-wider text-zinc-500">
                        Path
                      </div>
                      <div className="font-mono text-xs text-zinc-200">
                        {selected.path ?? "-"}
                      </div>
                    </div>
                    <div>
                      <div className="font-mono text-[10px] uppercase tracking-wider text-zinc-500">
                        IP
                      </div>
                      <div className="font-mono text-xs text-zinc-200">
                        {selected.ip_address ?? "-"}
                      </div>
                    </div>
                  </div>

                  <div className="mt-3">
                    <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-zinc-500">
                      Raw
                    </div>
                    <pre className="max-h-[310px] overflow-auto rounded bg-zinc-950 p-3 font-mono text-xs text-zinc-300">
                      {JSON.stringify(selected, null, 2)}
                    </pre>
                    {selected.user_agent ? (
                      <div className="mt-2 font-mono text-[10px] text-zinc-500">
                        UA: {selected.user_agent}
                      </div>
                    ) : null}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
