import * as React from "react";
import { cn } from "@/lib/utils";
import { TrendArrow } from "./trend-arrow";

export interface StatBlockProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string | number;
  label: string;
  subtext?: string;
  trend?: "up" | "down" | "stable";
}

export const StatBlock = React.forwardRef<HTMLDivElement, StatBlockProps>(
  ({ className, value, label, subtext, trend, ...props }, ref) => {
    return (
      <div
        ref={ref}
        data-testid="stat-block"
        className={cn("flex flex-col", className)}
        {...props}
      >
        <div className="flex items-center gap-2">
          <span className="text-4xl font-mono font-semibold">{value}</span>
          {trend && <TrendArrow direction={trend} />}
        </div>
        <span className="text-sm text-muted-foreground">{label}</span>
        {subtext && (
          <span
            data-testid="stat-block-subtext"
            className="text-sm text-muted-foreground/70"
          >
            {subtext}
          </span>
        )}
      </div>
    );
  },
);

StatBlock.displayName = "StatBlock";
