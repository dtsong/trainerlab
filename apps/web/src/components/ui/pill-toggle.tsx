"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const pillButtonVariants = cva(
  "rounded-full font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2",
  {
    variants: {
      selected: {
        true: "bg-teal-500 text-white",
        false: "bg-transparent text-muted-foreground hover:text-foreground",
      },
      size: {
        sm: "px-3 py-1 text-sm",
        md: "px-4 py-1.5 text-base",
      },
    },
    defaultVariants: {
      selected: false,
      size: "sm",
    },
  }
);

export interface PillToggleOption {
  value: string;
  label: string;
}

export interface PillToggleProps
  extends
    Omit<React.HTMLAttributes<HTMLDivElement>, "onChange">,
    Omit<VariantProps<typeof pillButtonVariants>, "selected"> {
  options: PillToggleOption[];
  value: string;
  onChange: (value: string) => void;
  size?: "sm" | "md";
}

export const PillToggle = React.forwardRef<HTMLDivElement, PillToggleProps>(
  ({ className, options, value, onChange, size = "sm", ...props }, ref) => {
    // Handle empty options array
    if (!options || options.length === 0) {
      return null;
    }

    const handleKeyDown = (e: React.KeyboardEvent, currentIndex: number) => {
      if (e.key === "ArrowRight") {
        e.preventDefault();
        const nextIndex = (currentIndex + 1) % options.length;
        onChange(options[nextIndex].value);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        const prevIndex = (currentIndex - 1 + options.length) % options.length;
        onChange(options[prevIndex].value);
      }
    };

    return (
      <div
        ref={ref}
        role="group"
        data-testid="pill-toggle"
        className={cn(
          "inline-flex items-center gap-1 rounded-full bg-muted p-1",
          className
        )}
        {...props}
      >
        {options.map((option, index) => {
          const isSelected = option.value === value;
          return (
            <button
              key={option.value}
              type="button"
              role="button"
              aria-pressed={isSelected}
              className={cn(pillButtonVariants({ selected: isSelected, size }))}
              onClick={() => onChange(option.value)}
              onKeyDown={(e) => handleKeyDown(e, index)}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    );
  }
);

PillToggle.displayName = "PillToggle";
