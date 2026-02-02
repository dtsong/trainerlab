import * as React from "react";
import { cn } from "@/lib/utils";

export interface JPSignalBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  jpShare: number;
  enShare: number;
  threshold?: number;
}

export const JPSignalBadge = React.forwardRef<
  HTMLSpanElement,
  JPSignalBadgeProps
>(({ className, jpShare, enShare, threshold = 0.05, ...props }, ref) => {
  // Validate numeric inputs
  if (!Number.isFinite(jpShare) || !Number.isFinite(enShare)) {
    return null;
  }
  if (!Number.isFinite(threshold) || threshold < 0) {
    return null;
  }

  const difference = jpShare - enShare;
  const absDifference = Math.abs(difference);

  if (absDifference <= threshold) {
    return null;
  }

  const percentDiff = Math.round(absDifference * 100);
  const sign = difference > 0 ? "+" : "-";
  const displayText = `JP ${sign}${percentDiff}%`;

  return (
    <span
      ref={ref}
      data-testid="jp-signal-badge"
      className={cn(
        "inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium bg-signal-jp text-white",
        className,
      )}
      {...props}
    >
      {displayText}
    </span>
  );
});

JPSignalBadge.displayName = "JPSignalBadge";
