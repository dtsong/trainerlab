"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import {
  useCreateWidget,
  useDeleteWidget,
  useUpdateWidget,
  useWidget,
  useWidgetEmbedCode,
} from "@/hooks";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type {
  ApiWidgetCreate,
  ApiWidgetUpdate,
  WidgetTheme,
  WidgetType,
} from "@trainerlab/shared-types";

const WIDGET_TYPES: WidgetType[] = [
  "meta_snapshot",
  "archetype_card",
  "meta_pie",
  "meta_trend",
  "jp_comparison",
  "deck_cost",
  "tournament_result",
  "prediction",
  "evolution_timeline",
];

const TYPE_LABELS: Record<WidgetType, string> = {
  meta_snapshot: "Meta Snapshot",
  archetype_card: "Archetype Card",
  meta_pie: "Meta Pie",
  meta_trend: "Meta Trend",
  jp_comparison: "JP Comparison",
  deck_cost: "Deck Cost",
  tournament_result: "Tournament Result",
  prediction: "Prediction",
  evolution_timeline: "Evolution Timeline",
};

interface WidgetBuilderProps {
  mode: "create" | "edit";
  widgetId?: string;
}

export function WidgetBuilder({ mode, widgetId }: WidgetBuilderProps) {
  const router = useRouter();
  const widgetQuery = useWidget(widgetId ?? "");
  const embedCodeQuery = useWidgetEmbedCode(widgetId ?? "");

  const createWidget = useCreateWidget();
  const updateWidget = useUpdateWidget();
  const deleteWidget = useDeleteWidget();

  const [type, setType] = useState<WidgetType>("meta_snapshot");
  const [theme, setTheme] = useState<WidgetTheme>("light");
  const [accentColor, setAccentColor] = useState("#14b8a6");
  const [showAttribution, setShowAttribution] = useState(true);
  const [config, setConfig] = useState<Record<string, unknown>>({
    region: "global",
    format: "standard",
  });

  useEffect(() => {
    if (mode !== "edit" || !widgetQuery.data) return;
    const widget = widgetQuery.data;
    setType(widget.type as WidgetType);
    setTheme((widget.theme as WidgetTheme) ?? "light");
    setAccentColor(widget.accent_color ?? "#14b8a6");
    setShowAttribution(widget.show_attribution);
    setConfig(widget.config ?? {});
  }, [mode, widgetQuery.data]);

  const updateConfigField = (key: string, value: string) => {
    setConfig((current) => ({ ...current, [key]: value }));
  };

  const ogUrl = widgetId ? `/api/og/w_${widgetId}.png` : null;

  const defaultIframeCode = widgetId
    ? `<iframe src="https://www.trainerlab.io/embed/${widgetId}" width="100%" height="420" frameborder="0"></iframe>`
    : "";

  const defaultScriptCode = widgetId
    ? `<div data-trainerlab-widget="${widgetId}"></div>\n<script src="https://www.trainerlab.io/embed.js" async></script>`
    : "";

  const iframeCode = embedCodeQuery.data?.iframe_code ?? defaultIframeCode;
  const scriptCode = embedCodeQuery.data?.script_code ?? defaultScriptCode;

  const previewRows = useMemo(() => {
    return Object.entries(config)
      .filter((entry) => entry[1] !== "" && entry[1] !== undefined)
      .slice(0, 4);
  }, [config]);

  const submitLabel = mode === "create" ? "Create Widget" : "Save Changes";

  const submitWidget = async () => {
    const payload: ApiWidgetCreate = {
      type,
      config,
      theme,
      accent_color: accentColor || null,
      show_attribution: showAttribution,
    };

    try {
      if (mode === "create") {
        const created = await createWidget.mutateAsync(payload);
        toast.success("Widget created");
        router.push(`/creator/widgets/${created.id}/edit`);
        return;
      }

      if (!widgetId) return;

      const updatePayload: ApiWidgetUpdate = {
        config,
        theme,
        accent_color: accentColor || null,
        show_attribution: showAttribution,
      };

      await updateWidget.mutateAsync({ id: widgetId, data: updatePayload });
      toast.success("Widget updated");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to save widget";
      toast.error(message);
    }
  };

  const removeWidget = async () => {
    if (!widgetId) return;

    const confirmed = window.confirm(
      "Delete this widget? This cannot be undone."
    );
    if (!confirmed) return;

    try {
      await deleteWidget.mutateAsync(widgetId);
      toast.success("Widget deleted");
      router.push("/creator");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to delete widget";
      toast.error(message);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied to clipboard");
    } catch {
      toast.error("Unable to copy code");
    }
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <Card>
        <CardHeader>
          <CardTitle>
            {mode === "create" ? "New Widget" : "Edit Widget"}
          </CardTitle>
          <CardDescription>
            Configure widget type, visual style, and embed settings.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {mode === "edit" && widgetQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading widget...</p>
          ) : null}

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Widget Type</Label>
              <Select
                value={type}
                onValueChange={(value) => setType(value as WidgetType)}
              >
                <SelectTrigger data-testid="widget-type-selector">
                  <SelectValue placeholder="Select widget type" />
                </SelectTrigger>
                <SelectContent>
                  {WIDGET_TYPES.map((item) => (
                    <SelectItem key={item} value={item}>
                      {TYPE_LABELS[item]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Theme</Label>
              <Select
                value={theme}
                onValueChange={(value) => setTheme(value as WidgetTheme)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Theme" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">Light</SelectItem>
                  <SelectItem value="dark">Dark</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="accentColor">Accent Color</Label>
              <Input
                id="accentColor"
                type="color"
                value={accentColor}
                onChange={(event) => setAccentColor(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="showAttribution">Show Attribution</Label>
              <Select
                value={showAttribution ? "yes" : "no"}
                onValueChange={(value) => setShowAttribution(value === "yes")}
              >
                <SelectTrigger id="showAttribution">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="yes">Yes</SelectItem>
                  <SelectItem value="no">No</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-3 rounded-md border p-4">
            <h3 className="text-sm font-semibold">Configuration</h3>
            {type === "meta_snapshot" ||
            type === "meta_pie" ||
            type === "meta_trend" ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <Input
                  placeholder="Region (global/JP/NA/EU)"
                  value={String(config.region ?? "")}
                  onChange={(event) =>
                    updateConfigField("region", event.target.value)
                  }
                />
                <Input
                  placeholder="Format (standard/expanded)"
                  value={String(config.format ?? "")}
                  onChange={(event) =>
                    updateConfigField("format", event.target.value)
                  }
                />
              </div>
            ) : null}

            {type === "archetype_card" ||
            type === "deck_cost" ||
            type === "evolution_timeline" ? (
              <Input
                placeholder="Archetype name"
                value={String(config.archetype ?? "")}
                onChange={(event) =>
                  updateConfigField("archetype", event.target.value)
                }
              />
            ) : null}

            {type === "tournament_result" ? (
              <Input
                placeholder="Tournament ID"
                value={String(config.tournament_id ?? "")}
                onChange={(event) =>
                  updateConfigField("tournament_id", event.target.value)
                }
              />
            ) : null}

            {type === "prediction" ? (
              <Input
                placeholder="Prediction category"
                value={String(config.category ?? "")}
                onChange={(event) =>
                  updateConfigField("category", event.target.value)
                }
              />
            ) : null}

            {type === "jp_comparison" ? (
              <Input
                placeholder="Lookback days"
                value={String(config.days ?? "30")}
                onChange={(event) =>
                  updateConfigField("days", event.target.value)
                }
              />
            ) : null}
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              onClick={submitWidget}
              disabled={createWidget.isPending || updateWidget.isPending}
            >
              {submitLabel}
            </Button>

            {mode === "edit" ? (
              <>
                <Button variant="outline" asChild>
                  <Link
                    href={widgetId ? `/embed/${widgetId}` : "/creator"}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open Embed Preview
                  </Link>
                </Button>
                <Button variant="destructive" onClick={removeWidget}>
                  Delete Widget
                </Button>
              </>
            ) : null}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Live Preview</CardTitle>
            <CardDescription>
              Visual preview updates as you change options.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div
              className={`rounded-lg border p-4 ${theme === "dark" ? "bg-slate-950 text-slate-100" : "bg-white text-slate-900"}`}
              data-testid="widget-live-preview"
            >
              <div
                className="mb-3 h-1.5 w-full rounded"
                style={{ backgroundColor: accentColor }}
              />
              <p className="text-sm font-semibold">{TYPE_LABELS[type]}</p>
              <p className="text-xs text-muted-foreground">Theme: {theme}</p>
              <div className="mt-3 space-y-1 text-xs">
                {previewRows.length ? (
                  previewRows.map(([key, value]) => (
                    <p key={key}>
                      {key}: <span className="font-mono">{String(value)}</span>
                    </p>
                  ))
                ) : (
                  <p className="text-muted-foreground">No config values yet.</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Embed Code</CardTitle>
            <CardDescription>
              Use iframe, script, or OG image endpoints in your publishing flow.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {widgetId ? (
              <Tabs defaultValue="iframe">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="iframe">iFrame</TabsTrigger>
                  <TabsTrigger value="script">JS</TabsTrigger>
                  <TabsTrigger value="og">OG</TabsTrigger>
                </TabsList>
                <TabsContent value="iframe" className="space-y-2">
                  <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs">
                    {iframeCode}
                  </pre>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => copyToClipboard(iframeCode)}
                  >
                    Copy iFrame Code
                  </Button>
                </TabsContent>
                <TabsContent value="script" className="space-y-2">
                  <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs">
                    {scriptCode}
                  </pre>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => copyToClipboard(scriptCode)}
                  >
                    Copy JS Code
                  </Button>
                </TabsContent>
                <TabsContent value="og" className="space-y-2">
                  <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs">{`https://www.trainerlab.io${ogUrl}`}</pre>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      copyToClipboard(`https://www.trainerlab.io${ogUrl}`)
                    }
                  >
                    Copy OG URL
                  </Button>
                </TabsContent>
              </Tabs>
            ) : (
              <p className="text-sm text-muted-foreground">
                Create the widget first to generate embed and OG code.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
