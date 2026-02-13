"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { AdminHeader } from "@/components/admin";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  adminAccessApi,
  adminAccessGrantsApi,
  adminAuditApi,
  type AdminAccessGrant,
  type AdminAccessUser,
  type AdminAuditEvent,
} from "@/lib/api";
import {
  filterGrantsByEmail,
  filterRecentAccessEvents,
  filterUsersByEmail,
  formatWhen,
  normalizeEmail,
  parseEmailLines,
} from "./utils";

type AccessAction =
  | "grant_beta"
  | "revoke_beta"
  | "grant_subscriber"
  | "revoke_subscriber";

const ACTION_LABEL: Record<AccessAction, string> = {
  grant_beta: "Grant beta",
  revoke_beta: "Revoke beta",
  grant_subscriber: "Grant subscriber",
  revoke_subscriber: "Revoke subscriber",
};

async function runAccessAction(action: AccessAction, email: string) {
  if (action === "grant_beta") return adminAccessGrantsApi.grantBeta(email);
  if (action === "revoke_beta") return adminAccessGrantsApi.revokeBeta(email);
  if (action === "grant_subscriber")
    return adminAccessGrantsApi.grantSubscriber(email);
  return adminAccessGrantsApi.revokeSubscriber(email);
}

function FlagPill({ label, active }: { label: string; active: boolean }) {
  return (
    <span
      className={
        "inline-flex items-center rounded border px-1.5 py-0.5 font-mono text-[10px] leading-none " +
        (active
          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
          : "border-zinc-700 bg-zinc-900 text-zinc-500")
      }
    >
      {label}
    </span>
  );
}

function UserRow({
  user,
  onGrantBeta,
  onRevokeBeta,
  onGrantSubscriber,
  onRevokeSubscriber,
}: {
  user: AdminAccessUser;
  onGrantBeta: (email: string) => void;
  onRevokeBeta: (email: string) => void;
  onGrantSubscriber: (email: string) => void;
  onRevokeSubscriber: (email: string) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-zinc-800/50 px-3 py-2 last:border-0">
      <div className="min-w-0">
        <div className="truncate font-mono text-sm text-zinc-100">
          {user.email}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-1.5">
          <FlagPill label="beta" active={user.is_beta_tester} />
          <FlagPill label="subscriber" active={user.is_subscriber} />
          <FlagPill label="creator" active={user.is_creator} />
          <span className="ml-1 font-mono text-[10px] text-zinc-500">
            updated {user.updated_at}
          </span>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {user.is_beta_tester ? (
          <Button
            variant="outline"
            size="sm"
            className="h-8 border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
            onClick={() => onRevokeBeta(user.email)}
          >
            Revoke beta
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            className="h-8 border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
            onClick={() => onGrantBeta(user.email)}
          >
            Grant beta
          </Button>
        )}

        {user.is_subscriber ? (
          <Button
            variant="outline"
            size="sm"
            className="h-8 border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
            onClick={() => onRevokeSubscriber(user.email)}
          >
            Revoke sub
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            className="h-8 border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
            onClick={() => onGrantSubscriber(user.email)}
          >
            Grant sub
          </Button>
        )}
      </div>
    </div>
  );
}

function InviteRow({
  grant,
  onRevokeBeta,
  onRevokeSubscriber,
}: {
  grant: AdminAccessGrant;
  onRevokeBeta: (email: string) => void;
  onRevokeSubscriber: (email: string) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-zinc-800/50 px-3 py-2 last:border-0">
      <div className="min-w-0">
        <div className="truncate font-mono text-sm text-zinc-100">
          {grant.email}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-1.5">
          <FlagPill label="beta" active={grant.is_beta_tester} />
          <FlagPill label="subscriber" active={grant.is_subscriber} />
          {grant.note ? (
            <span className="ml-1 truncate font-mono text-[10px] text-zinc-500">
              note: {grant.note}
            </span>
          ) : null}
        </div>
        <div className="mt-1 font-mono text-[10px] text-zinc-500">
          updated {grant.updated_at}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {grant.is_beta_tester ? (
          <Button
            variant="outline"
            size="sm"
            className="h-8 border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
            onClick={() => onRevokeBeta(grant.email)}
          >
            Revoke beta
          </Button>
        ) : null}

        {grant.is_subscriber ? (
          <Button
            variant="outline"
            size="sm"
            className="h-8 border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
            onClick={() => onRevokeSubscriber(grant.email)}
          >
            Revoke sub
          </Button>
        ) : null}
      </div>
    </div>
  );
}

export default function AdminAccessPage() {
  const qc = useQueryClient();
  const [email, setEmail] = useState("");
  const [emailSearch, setEmailSearch] = useState("");
  const [batchAction, setBatchAction] = useState<AccessAction>("grant_beta");
  const [batchEmails, setBatchEmails] = useState("");
  const [batchLog, setBatchLog] = useState<{
    startedAt: string;
    action: AccessAction;
    results: Array<{ email: string; ok: boolean; error?: string }>;
  } | null>(null);

  const normalizedEmail = useMemo(() => normalizeEmail(email), [email]);
  const normalizedEmailSearch = useMemo(
    () => normalizeEmail(emailSearch),
    [emailSearch]
  );
  const parsedBatch = useMemo(
    () => parseEmailLines(batchEmails),
    [batchEmails]
  );

  const betaUsers = useQuery({
    queryKey: ["admin", "access", "beta-users", "active"],
    queryFn: () => adminAccessApi.listBetaUsers({ active: true, limit: 200 }),
    staleTime: 1000 * 30,
  });

  const subscribers = useQuery({
    queryKey: ["admin", "access", "subscribers", "active"],
    queryFn: () => adminAccessApi.listSubscribers({ active: true, limit: 200 }),
    staleTime: 1000 * 30,
  });

  const pendingInvites = useQuery({
    queryKey: ["admin", "access", "access-grants", "pending"],
    queryFn: () =>
      adminAccessGrantsApi.list({ active: true, claimed: false, limit: 500 }),
    staleTime: 1000 * 30,
  });

  const recentAccessEvents = useQuery({
    queryKey: ["admin", "access", "recent-events"],
    queryFn: () => adminAuditApi.listEvents({ limit: 40, offset: 0 }),
    staleTime: 1000 * 20,
  });

  const filteredBetaUsers = useMemo(
    () => filterUsersByEmail(betaUsers.data, normalizedEmailSearch),
    [betaUsers.data, normalizedEmailSearch]
  );

  const filteredSubscribers = useMemo(
    () => filterUsersByEmail(subscribers.data, normalizedEmailSearch),
    [subscribers.data, normalizedEmailSearch]
  );

  const filteredPendingInvites = useMemo(
    () => filterGrantsByEmail(pendingInvites.data, normalizedEmailSearch),
    [pendingInvites.data, normalizedEmailSearch]
  );

  const filteredRecentAccessEvents = useMemo<AdminAuditEvent[]>(
    () =>
      filterRecentAccessEvents(recentAccessEvents.data, normalizedEmailSearch),
    [recentAccessEvents.data, normalizedEmailSearch]
  );

  const singleMutation = useMutation({
    mutationFn: ({ action, email }: { action: AccessAction; email: string }) =>
      runAccessAction(action, email),
    onSuccess: (grant) => {
      toast.success(
        grant.has_user
          ? `Updated ${grant.email}`
          : `Invited ${grant.email} (applies on first login)`
      );
      qc.invalidateQueries({ queryKey: ["admin", "access"] });
    },
    onError: (err) => {
      const message = err instanceof Error ? err.message : "Request failed";
      if (message === "Not authenticated") {
        toast.error("Session expired. Please refresh and sign in again.");
        return;
      }
      toast.error(message);
    },
  });

  const batchMutation = useMutation({
    mutationFn: async ({
      action,
      emails,
    }: {
      action: AccessAction;
      emails: string[];
    }) => {
      const results: Array<{ email: string; ok: boolean; error?: string }> = [];
      for (const e of emails) {
        try {
          await runAccessAction(action, e);
          results.push({ email: e, ok: true });
        } catch (err) {
          results.push({
            email: e,
            ok: false,
            error: err instanceof Error ? err.message : String(err),
          });
        }
      }
      return results;
    },
    onSuccess: (results, vars) => {
      const ok = results.filter((r) => r.ok).length;
      const fail = results.length - ok;
      setBatchLog({
        startedAt: new Date().toISOString(),
        action: vars.action,
        results,
      });
      if (fail === 0)
        toast.success(`${ACTION_LABEL[vars.action]}: ${ok} succeeded`);
      else
        toast.error(`${ACTION_LABEL[vars.action]}: ${ok} ok, ${fail} failed`);
      qc.invalidateQueries({ queryKey: ["admin", "access"] });
    },
  });

  const canSubmitSingle =
    normalizedEmail.includes("@") && normalizedEmail.includes(".");

  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col">
      <AdminHeader title="Access" />
      <main className="flex-1 overflow-auto px-6 py-6">
        <Tabs defaultValue="single" className="w-full">
          <TabsList className="bg-zinc-900/50">
            <TabsTrigger value="single">Single</TabsTrigger>
            <TabsTrigger value="batch">Batch</TabsTrigger>
            <TabsTrigger value="lists">Active Lists</TabsTrigger>
          </TabsList>

          <TabsContent value="single" className="mt-6">
            <div className="rounded border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                Email
              </div>
              <div className="mt-2 flex flex-col gap-3 sm:flex-row sm:items-center">
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@example.com"
                  className="h-10 flex-1 rounded border border-zinc-700 bg-zinc-950 px-3 font-mono text-sm text-zinc-200 placeholder:text-zinc-600"
                />
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!canSubmitSingle || singleMutation.isPending}
                    onClick={() =>
                      singleMutation.mutate({
                        action: "grant_beta",
                        email: normalizedEmail,
                      })
                    }
                    className="border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
                  >
                    Grant beta
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!canSubmitSingle || singleMutation.isPending}
                    onClick={() =>
                      singleMutation.mutate({
                        action: "revoke_beta",
                        email: normalizedEmail,
                      })
                    }
                    className="border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
                  >
                    Revoke beta
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!canSubmitSingle || singleMutation.isPending}
                    onClick={() =>
                      singleMutation.mutate({
                        action: "grant_subscriber",
                        email: normalizedEmail,
                      })
                    }
                    className="border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
                  >
                    Grant subscriber
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!canSubmitSingle || singleMutation.isPending}
                    onClick={() =>
                      singleMutation.mutate({
                        action: "revoke_subscriber",
                        email: normalizedEmail,
                      })
                    }
                    className="border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
                  >
                    Revoke subscriber
                  </Button>
                </div>
              </div>
              <div className="mt-2 font-mono text-xs text-zinc-500">
                Tip: after grant/revoke, user should refresh to pick up access.
              </div>
            </div>
          </TabsContent>

          <TabsContent value="batch" className="mt-6">
            <div className="rounded border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                    Batch operation
                  </div>
                  <div className="mt-1 font-mono text-xs text-zinc-500">
                    One email per line. Duplicates are ignored.
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={batchAction}
                    onChange={(e) =>
                      setBatchAction(e.target.value as AccessAction)
                    }
                    className="h-9 rounded border border-zinc-700 bg-zinc-950 px-2 font-mono text-xs text-zinc-300"
                  >
                    <option value="grant_beta">Grant beta</option>
                    <option value="revoke_beta">Revoke beta</option>
                    <option value="grant_subscriber">Grant subscriber</option>
                    <option value="revoke_subscriber">Revoke subscriber</option>
                  </select>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={
                      parsedBatch.length === 0 || batchMutation.isPending
                    }
                    onClick={() =>
                      batchMutation.mutate({
                        action: batchAction,
                        emails: parsedBatch,
                      })
                    }
                    className="border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
                  >
                    Run ({parsedBatch.length})
                  </Button>
                </div>
              </div>

              <textarea
                value={batchEmails}
                onChange={(e) => setBatchEmails(e.target.value)}
                placeholder={"alice@example.com\n" + "bob@example.com"}
                rows={8}
                className="mt-4 w-full rounded border border-zinc-700 bg-zinc-950 p-3 font-mono text-xs text-zinc-200 placeholder:text-zinc-600"
              />

              {batchLog ? (
                <div className="mt-4">
                  <div className="mb-2 font-mono text-xs uppercase tracking-wider text-zinc-500">
                    Last run
                  </div>
                  <pre className="max-h-64 overflow-auto rounded bg-zinc-950 p-3 font-mono text-xs text-zinc-300">
                    {JSON.stringify(batchLog, null, 2)}
                  </pre>
                </div>
              ) : null}
            </div>
          </TabsContent>

          <TabsContent value="lists" className="mt-6">
            <div className="mb-4 rounded border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                Search by email
              </div>
              <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center">
                <input
                  value={emailSearch}
                  onChange={(e) => setEmailSearch(e.target.value)}
                  placeholder="Filter active users, invites, and recent access changes"
                  className="h-10 flex-1 rounded border border-zinc-700 bg-zinc-950 px-3 font-mono text-sm text-zinc-200 placeholder:text-zinc-600"
                />
                <Button
                  variant="outline"
                  size="sm"
                  className="h-10 border-zinc-700 bg-zinc-950 font-mono text-xs text-zinc-300 hover:bg-zinc-900"
                  onClick={() => setEmailSearch("")}
                >
                  Clear
                </Button>
              </div>
            </div>

            <div className="mb-4 rounded border border-zinc-800 bg-zinc-900/50">
              <div className="flex items-center justify-between border-b border-zinc-800 px-3 py-2">
                <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                  Recent access changes
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 font-mono text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                  onClick={() => recentAccessEvents.refetch()}
                >
                  Refresh
                </Button>
              </div>

              {recentAccessEvents.isLoading ? (
                <div className="p-3 font-mono text-sm text-zinc-500">
                  Loading...
                </div>
              ) : recentAccessEvents.isError ? (
                <div className="p-3 font-mono text-sm text-zinc-500">
                  Failed to load recent access changes
                </div>
              ) : filteredRecentAccessEvents.length === 0 ? (
                <div className="p-3 font-mono text-sm text-zinc-500">
                  No recent matching access events
                </div>
              ) : (
                <div className="max-h-[220px] overflow-auto">
                  {filteredRecentAccessEvents.map((event) => (
                    <div
                      key={event.id}
                      className="border-b border-zinc-800/50 px-3 py-2 last:border-0"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="truncate font-mono text-xs text-zinc-300">
                          {formatWhen(event.created_at)}
                        </div>
                        <div className="shrink-0 rounded border border-zinc-700 bg-zinc-950 px-1.5 py-0.5 font-mono text-[10px] text-zinc-400">
                          {event.action}
                        </div>
                      </div>
                      <div className="mt-1 font-mono text-xs text-zinc-500">
                        {event.actor_email} → {event.target_email}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <div className="rounded border border-zinc-800 bg-zinc-900/50">
                <div className="flex items-center justify-between border-b border-zinc-800 px-3 py-2">
                  <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                    Beta users
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 font-mono text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                    onClick={() => betaUsers.refetch()}
                  >
                    Refresh
                  </Button>
                </div>
                {betaUsers.isLoading ? (
                  <div className="p-3 font-mono text-sm text-zinc-500">
                    Loading...
                  </div>
                ) : betaUsers.isError ? (
                  <div className="p-3 font-mono text-sm text-zinc-500">
                    Failed to load
                  </div>
                ) : filteredBetaUsers.length === 0 ? (
                  <div className="p-3 font-mono text-sm text-zinc-500">
                    No active beta users
                  </div>
                ) : (
                  <div className="max-h-[520px] overflow-auto">
                    {filteredBetaUsers.map((u) => (
                      <UserRow
                        key={u.id}
                        user={u}
                        onGrantBeta={(e) =>
                          singleMutation.mutate({
                            action: "grant_beta",
                            email: e,
                          })
                        }
                        onRevokeBeta={(e) =>
                          singleMutation.mutate({
                            action: "revoke_beta",
                            email: e,
                          })
                        }
                        onGrantSubscriber={(e) =>
                          singleMutation.mutate({
                            action: "grant_subscriber",
                            email: e,
                          })
                        }
                        onRevokeSubscriber={(e) =>
                          singleMutation.mutate({
                            action: "revoke_subscriber",
                            email: e,
                          })
                        }
                      />
                    ))}
                  </div>
                )}
              </div>

              <div className="rounded border border-zinc-800 bg-zinc-900/50">
                <div className="flex items-center justify-between border-b border-zinc-800 px-3 py-2">
                  <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                    Subscribers
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 font-mono text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                    onClick={() => subscribers.refetch()}
                  >
                    Refresh
                  </Button>
                </div>
                {subscribers.isLoading ? (
                  <div className="p-3 font-mono text-sm text-zinc-500">
                    Loading...
                  </div>
                ) : subscribers.isError ? (
                  <div className="p-3 font-mono text-sm text-zinc-500">
                    Failed to load
                  </div>
                ) : filteredSubscribers.length === 0 ? (
                  <div className="p-3 font-mono text-sm text-zinc-500">
                    No active subscribers
                  </div>
                ) : (
                  <div className="max-h-[520px] overflow-auto">
                    {filteredSubscribers.map((u) => (
                      <UserRow
                        key={u.id}
                        user={u}
                        onGrantBeta={(e) =>
                          singleMutation.mutate({
                            action: "grant_beta",
                            email: e,
                          })
                        }
                        onRevokeBeta={(e) =>
                          singleMutation.mutate({
                            action: "revoke_beta",
                            email: e,
                          })
                        }
                        onGrantSubscriber={(e) =>
                          singleMutation.mutate({
                            action: "grant_subscriber",
                            email: e,
                          })
                        }
                        onRevokeSubscriber={(e) =>
                          singleMutation.mutate({
                            action: "revoke_subscriber",
                            email: e,
                          })
                        }
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-4 rounded border border-zinc-800 bg-zinc-900/50">
              <div className="flex items-center justify-between border-b border-zinc-800 px-3 py-2">
                <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                  Pending invites
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 font-mono text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                  onClick={() => pendingInvites.refetch()}
                >
                  Refresh
                </Button>
              </div>

              {pendingInvites.isLoading ? (
                <div className="p-3 font-mono text-sm text-zinc-500">
                  Loading...
                </div>
              ) : pendingInvites.isError ? (
                <div className="p-3 font-mono text-sm text-zinc-500">
                  Failed to load
                </div>
              ) : filteredPendingInvites.length === 0 ? (
                <div className="p-3 font-mono text-sm text-zinc-500">
                  No pending invites
                </div>
              ) : (
                <div className="max-h-[520px] overflow-auto">
                  {filteredPendingInvites.map((g) => (
                    <InviteRow
                      key={g.id}
                      grant={g}
                      onRevokeBeta={(e) =>
                        singleMutation.mutate({
                          action: "revoke_beta",
                          email: e,
                        })
                      }
                      onRevokeSubscriber={(e) =>
                        singleMutation.mutate({
                          action: "revoke_subscriber",
                          email: e,
                        })
                      }
                    />
                  ))}
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
