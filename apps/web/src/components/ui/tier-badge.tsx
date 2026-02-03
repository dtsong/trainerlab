import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const tierBadgeVariants = cva(
  "inline-flex items-center justify-center font-semibold rounded text-white",
  {
    variants: {
      tier: {
        S: "bg-tier-s text-black",
        A: "bg-tier-a",
        B: "bg-tier-b",
        C: "bg-tier-c",
        Rogue: "bg-tier-rogue",
      },
      size: {
        sm: "h-4 min-w-4 px-1 text-xs",
        md: "h-6 min-w-6 px-1.5 text-sm",
      },
    },
    defaultVariants: {
      size: "sm",
    },
  }
);

export interface TierBadgeProps
  extends
    React.HTMLAttributes<HTMLSpanElement>,
    Omit<VariantProps<typeof tierBadgeVariants>, "tier"> {
  tier: "S" | "A" | "B" | "C" | "Rogue";
  size?: "sm" | "md";
}

export const TierBadge = React.forwardRef<HTMLSpanElement, TierBadgeProps>(
  ({ className, tier, size = "sm", ...props }, ref) => {
    return (
      <span
        ref={ref}
        data-testid="tier-badge"
        className={cn(tierBadgeVariants({ tier, size }), className)}
        {...props}
      >
        {tier}
      </span>
    );
  }
);

TierBadge.displayName = "TierBadge";
