import { AlertTriangle, Clock3, Info } from "lucide-react";

import type { ApiDataFreshness } from "@trainerlab/shared-types";

interface DataFreshnessBannerProps {
  freshness?: ApiDataFreshness | null;
  className?: string;
}

function confidenceFromSampleSize(sampleSize: number): {
  label: "High" | "Med" | "Low";
  className: string;
} {
  if (sampleSize >= 64) {
    return {
      label: "High",
      className: "border-emerald-500/30 bg-emerald-500/10 text-emerald-800",
    };
  }
  if (sampleSize >= 8) {
    return {
      label: "Med",
      className: "border-amber-500/30 bg-amber-500/10 text-amber-800",
    };
  }
  return {
    label: "Low",
    className: "border-slate-400/30 bg-slate-500/10 text-slate-700",
  };
}

const statusStyles: Record<
  NonNullable<ApiDataFreshness["status"]>,
  {
    icon: typeof Info;
    container: string;
    iconColor: string;
  }
> = {
  fresh: {
    icon: Clock3,
    container: "border-emerald-500/30 bg-emerald-500/10 text-emerald-800",
    iconColor: "text-emerald-700",
  },
  partial: {
    icon: Info,
    container: "border-amber-500/30 bg-amber-500/10 text-amber-800",
    iconColor: "text-amber-700",
  },
  stale: {
    icon: AlertTriangle,
    container: "border-orange-500/30 bg-orange-500/10 text-orange-800",
    iconColor: "text-orange-700",
  },
  no_data: {
    icon: AlertTriangle,
    container: "border-slate-400/30 bg-slate-500/10 text-slate-700",
    iconColor: "text-slate-600",
  },
};

const cadenceLabels: Partial<
  Record<ApiDataFreshness["cadence_profile"], string>
> = {
  tpci_event_cadence: "TPCI major event cadence",
  jp_daily_cadence: "JP daily cadence",
  grassroots_daily_cadence: "Grassroots daily cadence",
  default_cadence: "Default cadence",
};

export function DataFreshnessBanner({
  freshness,
  className,
}: DataFreshnessBannerProps) {
  if (!freshness) return null;

  const sourceCoverage = (freshness.source_coverage ?? []).filter(
    (s): s is string => typeof s === "string" && s.trim().length > 0
  );

  const status = freshness.status;
  const style = statusStyles[status];
  const Icon = style.icon;
  const cadenceLabel = cadenceLabels[freshness.cadence_profile] ?? "Cadence";
  const sampleSize =
    typeof freshness.sample_size === "number" ? freshness.sample_size : null;
  const confidence =
    sampleSize != null ? confidenceFromSampleSize(sampleSize) : null;
  const confidenceTitle =
    sampleSize != null ? `${sampleSize.toLocaleString()} samples` : undefined;

  return (
    <div
      className={`flex items-start gap-2 rounded-md border px-3 py-2 text-xs ${style.container} ${className ?? ""}`}
      data-testid="data-freshness-banner"
      data-status={status}
      data-cadence={freshness.cadence_profile}
    >
      <Icon className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${style.iconColor}`} />
      <div className="space-y-0.5">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-medium">
            {freshness.message ?? "Data freshness update."}
          </p>
          {confidence ? (
            <span
              className={`inline-flex items-center rounded border px-1.5 py-0.5 font-mono text-[10px] leading-none ${confidence.className}`}
              title={confidenceTitle}
              data-testid="data-confidence-pill"
            >
              Confidence {confidence.label}
            </span>
          ) : null}
        </div>
        <p className="text-[11px] opacity-80">
          {cadenceLabel}
          {freshness.snapshot_date
            ? ` • Snapshot ${freshness.snapshot_date}`
            : ""}
          {typeof freshness.sample_size === "number"
            ? ` • Sample ${freshness.sample_size.toLocaleString()}`
            : ""}
        </p>
        {sourceCoverage.length > 0 ? (
          <p className="text-[11px] opacity-80">
            Sources: {sourceCoverage.join(", ")}
          </p>
        ) : null}
      </div>
    </div>
  );
}
