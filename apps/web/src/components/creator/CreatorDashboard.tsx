"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Download, KeyRound, Plus, Sparkles, Wand2 } from "lucide-react";

import {
  useApiKeys,
  useCreateApiKey,
  useCreateExport,
  useExports,
  useFormatForecast,
  useWidgets,
} from "@/hooks";
import { exportsApi, type ExportSearchParams } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import type { ApiApiKeyResponse, ExportType } from "@trainerlab/shared-types";

const QUICK_EXPORT_PRESETS: {
  label: string;
  export_type: ExportType;
  format: "csv" | "json" | "xlsx";
}[] = [
  { label: "Meta Snapshot CSV", export_type: "meta_snapshot", format: "csv" },
  { label: "Meta History JSON", export_type: "meta_history", format: "json" },
  { label: "JP Data XLSX", export_type: "jp_data", format: "xlsx" },
];

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function usagePercent(key: ApiApiKeyResponse): number {
  if (key.monthly_limit <= 0) return 0;
  return Math.min(
    100,
    Math.round((key.requests_this_month / key.monthly_limit) * 100)
  );
}

export function CreatorDashboard() {
  const widgetQuery = useWidgets({ page: 1, limit: 24 });
  const exportsParams: ExportSearchParams = { page: 1, limit: 8 };
  const exportQuery = useExports(exportsParams);
  const apiKeyQuery = useApiKeys();
  const forecastQuery = useFormatForecast({ top_n: 5 });

  const createExport = useCreateExport();
  const createApiKey = useCreateApiKey();

  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyLimit, setNewKeyLimit] = useState("25000");
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);

  const topForecastIdeas = useMemo(() => {
    return (forecastQuery.data?.forecast_archetypes ?? []).slice(0, 3);
  }, [forecastQuery.data?.forecast_archetypes]);

  const handleQuickExport = async (
    exportType: ExportType,
    format: "csv" | "json" | "xlsx"
  ) => {
    try {
      await createExport.mutateAsync({ export_type: exportType, format });
      toast.success("Export queued");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to queue export";
      toast.error(message);
    }
  };

  const handleDownload = async (exportId: string) => {
    try {
      const data = await exportsApi.getDownloadUrl(exportId);
      window.open(data.download_url, "_blank", "noopener,noreferrer");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to get download URL";
      toast.error(message);
    }
  };

  const handleCreateApiKey = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    const monthlyLimit = Number(newKeyLimit);

    if (!newKeyName.trim()) {
      toast.error("API key name is required");
      return;
    }

    if (!Number.isFinite(monthlyLimit) || monthlyLimit < 1) {
      toast.error("Monthly limit must be a positive number");
      return;
    }

    try {
      const response = await createApiKey.mutateAsync({
        name: newKeyName.trim(),
        monthly_limit: monthlyLimit,
      });

      setGeneratedKey(response.full_key);
      setNewKeyName("");
      toast.success("API key created");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to create API key";
      toast.error(message);
    }
  };

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Creator Dashboard</h1>
        <p className="text-muted-foreground">
          Build embeds, export insights, and publish data-backed content faster.
        </p>
      </header>

      <section>
        <Card>
          <CardHeader className="flex flex-row items-start justify-between gap-4">
            <div>
              <CardTitle>Your Widgets</CardTitle>
              <CardDescription>
                Manage active embeds and quickly jump into editing.
              </CardDescription>
            </div>
            <Button asChild>
              <Link href="/creator/widgets/new">
                <Plus className="mr-2 h-4 w-4" />
                New Widget
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {widgetQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">
                Loading widgets...
              </p>
            ) : widgetQuery.data?.items.length ? (
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {widgetQuery.data.items.map((widget) => (
                  <div key={widget.id} className="rounded-md border p-3">
                    <p className="text-sm font-semibold">{widget.type}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Embeds {widget.embed_count} · Views {widget.view_count}
                    </p>
                    <div className="mt-3 flex gap-2">
                      <Button size="sm" variant="outline" asChild>
                        <Link href={`/creator/widgets/${widget.id}/edit`}>
                          Edit
                        </Link>
                      </Button>
                      <Button size="sm" variant="ghost" asChild>
                        <Link
                          href={`/embed/${widget.id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Preview
                        </Link>
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No widgets yet. Create your first widget to start embedding
                TrainerLab data.
              </p>
            )}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Quick Exports
            </CardTitle>
            <CardDescription>
              Generate creator-ready datasets and download when complete.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {QUICK_EXPORT_PRESETS.map((preset) => (
                <Button
                  key={preset.label}
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    handleQuickExport(preset.export_type, preset.format)
                  }
                  disabled={createExport.isPending}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Recent exports
              </p>
              {exportQuery.data?.items.length ? (
                exportQuery.data.items.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                  >
                    <div>
                      <p className="font-medium">{item.export_type}</p>
                      <p className="text-xs text-muted-foreground">
                        {item.status} · {formatDate(item.created_at)}
                      </p>
                    </div>
                    {item.status === "completed" ? (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDownload(item.id)}
                      >
                        Download
                      </Button>
                    ) : null}
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No exports yet.</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Trending Data
            </CardTitle>
            <CardDescription>
              This week&apos;s strongest content angles from format divergence.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {forecastQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">
                Loading trend ideas...
              </p>
            ) : topForecastIdeas.length ? (
              topForecastIdeas.map((item) => (
                <div
                  key={item.archetype}
                  className="rounded-md border px-3 py-2"
                >
                  <p className="font-medium">{item.archetype}</p>
                  <p className="text-sm text-muted-foreground">
                    JP {(item.jp_share * 100).toFixed(1)}% vs Global{" "}
                    {(item.en_share * 100).toFixed(1)}% (
                    {item.divergence > 0 ? "+" : ""}
                    {(item.divergence * 100).toFixed(1)}pp)
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">
                No forecast data available right now.
              </p>
            )}
            <Button variant="ghost" size="sm" asChild>
              <Link href="/meta/japan">
                <Wand2 className="mr-2 h-4 w-4" />
                Open JP analysis ideas
              </Link>
            </Button>
          </CardContent>
        </Card>
      </section>

      <section>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5" />
              API Access
            </CardTitle>
            <CardDescription>
              Create and monitor API keys for programmatic integrations.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <form
              className="grid gap-3 sm:grid-cols-[1fr_160px_auto]"
              onSubmit={handleCreateApiKey}
            >
              <Input
                placeholder="Key name (e.g. YouTube automation)"
                value={newKeyName}
                onChange={(event) => setNewKeyName(event.target.value)}
              />
              <Input
                type="number"
                min={1}
                placeholder="Monthly limit"
                value={newKeyLimit}
                onChange={(event) => setNewKeyLimit(event.target.value)}
              />
              <Button type="submit" disabled={createApiKey.isPending}>
                Create Key
              </Button>
            </form>

            {generatedKey ? (
              <div className="rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm">
                <p className="font-medium">New key (shown once)</p>
                <code className="mt-1 block break-all text-xs">
                  {generatedKey}
                </code>
              </div>
            ) : null}

            <div className="space-y-3">
              {apiKeyQuery.data?.items.length ? (
                apiKeyQuery.data.items.map((key) => (
                  <div
                    key={key.id}
                    className="space-y-1 rounded-md border px-3 py-2"
                  >
                    <div className="flex items-center justify-between text-sm">
                      <p className="font-medium">{key.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {key.key_prefix}
                      </p>
                    </div>
                    <Progress value={usagePercent(key)} />
                    <p className="text-xs text-muted-foreground">
                      {key.requests_this_month.toLocaleString()} /{" "}
                      {key.monthly_limit.toLocaleString()} requests this month
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">
                  No API keys yet.
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
