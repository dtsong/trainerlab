import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const trendArrowVariants = cva("inline-flex items-center", {
  variants: {
    direction: {
      up: "text-signal-up",
      down: "text-signal-down",
      stable: "text-signal-stable",
    },
    size: {
      sm: "gap-0.5 text-sm",
      md: "gap-1 text-base",
    },
  },
  defaultVariants: {
    size: "sm",
  },
});

const iconSizes = {
  sm: "h-3 w-3",
  md: "h-4 w-4",
};

export interface TrendArrowProps
  extends
    Omit<React.HTMLAttributes<HTMLSpanElement>, "direction">,
    VariantProps<typeof trendArrowVariants> {
  direction: "up" | "down" | "stable";
  value?: number;
  size?: "sm" | "md";
}

function formatValue(
  value: number,
  direction: "up" | "down" | "stable"
): string {
  if (!Number.isFinite(value)) {
    return "";
  }
  const absValue = Math.abs(value);
  const sign = direction === "down" ? "-" : "+";
  return `${sign}${absValue}%`;
}

export const TrendArrow = React.forwardRef<HTMLSpanElement, TrendArrowProps>(
  ({ className, direction, value, size = "sm", ...props }, ref) => {
    const iconSize = iconSizes[size];

    return (
      <span
        ref={ref}
        data-testid="trend-arrow"
        className={cn(trendArrowVariants({ direction, size }), className)}
        {...props}
      >
        {direction === "up" && (
          <svg
            data-testid="trend-arrow-up"
            className={iconSize}
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path d="M8 3L13 9H3L8 3Z" fill="currentColor" />
          </svg>
        )}
        {direction === "down" && (
          <svg
            data-testid="trend-arrow-down"
            className={iconSize}
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path d="M8 13L3 7H13L8 13Z" fill="currentColor" />
          </svg>
        )}
        {direction === "stable" && (
          <svg
            data-testid="trend-arrow-stable"
            className={iconSize}
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              d="M3 8H13"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        )}
        {value !== undefined && <span>{formatValue(value, direction)}</span>}
      </span>
    );
  }
);

TrendArrow.displayName = "TrendArrow";
