import * as React from "react";
import { cn } from "@/lib/utils";

export interface SectionLabelProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  icon?: React.ReactNode;
  variant?: "default" | "notebook";
}

export const SectionLabel = React.forwardRef<HTMLDivElement, SectionLabelProps>(
  ({ className, label, icon, variant = "default", ...props }, ref) => {
    const displayLabel = label ?? "";
    if (process.env.NODE_ENV === "development" && !label) {
      console.warn("[SectionLabel] Missing required label prop");
    }

    const isNotebook = variant === "notebook";

    return (
      <div
        ref={ref}
        data-testid="section-label"
        className={cn(
          "flex items-center gap-2 font-mono text-mono-sm uppercase tracking-wide",
          isNotebook ? "text-pencil" : "text-muted-foreground",
          className,
        )}
        {...props}
      >
        {icon && (
          <span
            data-testid="section-label-icon"
            className={cn("flex-shrink-0", isNotebook && "text-ink-red")}
          >
            {icon}
          </span>
        )}
        <span className="flex-shrink-0">{displayLabel.toUpperCase()}</span>
        <div
          data-testid="section-label-divider"
          className={cn(
            "flex-grow h-px",
            isNotebook
              ? "bg-gradient-to-r from-ink-red/30 via-notebook-grid to-transparent"
              : "bg-border",
          )}
        />
      </div>
    );
  },
);

SectionLabel.displayName = "SectionLabel";
