"use client";

import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

import type { SurvivalRating } from "@trainerlab/shared-types";

const survivalBadgeVariants = cva(
  "inline-flex items-center justify-center rounded-md px-2 py-1 text-xs font-semibold",
  {
    variants: {
      rating: {
        dies: "bg-red-500/20 text-red-400 border border-red-500/30",
        crippled:
          "bg-orange-500/20 text-orange-400 border border-orange-500/30",
        adapts: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
        thrives: "bg-green-500/20 text-green-400 border border-green-500/30",
        unknown: "bg-slate-500/20 text-slate-400 border border-slate-500/30",
      },
    },
    defaultVariants: {
      rating: "unknown",
    },
  }
);

export interface SurvivalBadgeProps
  extends
    React.HTMLAttributes<HTMLSpanElement>,
    Omit<VariantProps<typeof survivalBadgeVariants>, "rating"> {
  rating: SurvivalRating;
}

const ratingLabels: Record<SurvivalRating, string> = {
  dies: "Dies",
  crippled: "Crippled",
  adapts: "Adapts",
  thrives: "Thrives",
  unknown: "Unknown",
};

export const SurvivalBadge = React.forwardRef<
  HTMLSpanElement,
  SurvivalBadgeProps
>(({ className, rating, ...props }, ref) => (
  <span
    ref={ref}
    className={cn(survivalBadgeVariants({ rating }), className)}
    {...props}
  >
    {ratingLabels[rating]}
  </span>
));
SurvivalBadge.displayName = "SurvivalBadge";
