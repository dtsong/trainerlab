import { CheckCircle, Info, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const CONFIDENCE_CONFIG = {
  high: {
    icon: CheckCircle,
    label: "High",
    className:
      "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:border-emerald-400/30 dark:bg-emerald-400/10 dark:text-emerald-300",
  },
  medium: {
    icon: Info,
    label: "Med",
    className:
      "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-300",
  },
  low: {
    icon: AlertTriangle,
    label: "Low",
    className:
      "border-slate-400/30 bg-slate-400/10 text-slate-600 dark:border-slate-500/30 dark:bg-slate-500/10 dark:text-slate-400",
  },
} as const;

interface ConfidenceBadgeProps {
  confidence: "high" | "medium" | "low";
  sampleSize: number;
  freshnessLabel?: string;
  className?: string;
}

export function ConfidenceBadge({
  confidence,
  sampleSize,
  freshnessLabel,
  className,
}: ConfidenceBadgeProps) {
  const config = CONFIDENCE_CONFIG[confidence];
  const Icon = config.icon;

  const tooltip = freshnessLabel
    ? `${sampleSize.toLocaleString()} placements, ${freshnessLabel}`
    : `${sampleSize.toLocaleString()} placements`;

  return (
    <Badge
      variant="outline"
      title={tooltip}
      className={cn(
        "gap-1 font-mono text-[10px] leading-none",
        config.className,
        className
      )}
      data-testid="confidence-badge"
    >
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  );
}
