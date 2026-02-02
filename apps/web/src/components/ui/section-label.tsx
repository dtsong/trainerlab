import * as React from "react";
import { cn } from "@/lib/utils";

export interface SectionLabelProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  icon?: React.ReactNode;
}

export const SectionLabel = React.forwardRef<HTMLDivElement, SectionLabelProps>(
  ({ className, label, icon, ...props }, ref) => {
    const displayLabel = label ?? "";
    if (process.env.NODE_ENV === "development" && !label) {
      console.warn("[SectionLabel] Missing required label prop");
    }

    return (
      <div
        ref={ref}
        data-testid="section-label"
        className={cn(
          "flex items-center gap-2 font-mono text-mono-sm uppercase tracking-wide text-muted-foreground",
          className,
        )}
        {...props}
      >
        {icon && (
          <span data-testid="section-label-icon" className="flex-shrink-0">
            {icon}
          </span>
        )}
        <span className="flex-shrink-0">{displayLabel.toUpperCase()}</span>
        <div
          data-testid="section-label-divider"
          className="flex-grow h-px bg-border"
        />
      </div>
    );
  },
);

SectionLabel.displayName = "SectionLabel";
