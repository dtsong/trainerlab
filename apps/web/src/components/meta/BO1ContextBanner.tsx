"use client";

import { Info, X } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const STORAGE_KEY = "trainerlab-bo1-banner-dismissed";

interface BO1ContextBannerProps {
  className?: string;
}

export function BO1ContextBanner({ className }: BO1ContextBannerProps) {
  const [dismissed, setDismissed] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(STORAGE_KEY) === "true";
  });

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem(STORAGE_KEY, "true");
  };

  if (dismissed) {
    return null;
  }

  return (
    <div
      className={cn(
        "relative rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-950",
        className
      )}
      data-testid="bo1-context-banner"
      role="alert"
    >
      <button
        onClick={handleDismiss}
        className="absolute right-2 top-2 rounded p-1 text-blue-600 hover:bg-blue-100 dark:text-blue-400 dark:hover:bg-blue-900"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
      <div className="flex gap-3">
        <Info className="mt-0.5 h-5 w-5 shrink-0 text-blue-600 dark:text-blue-400" />
        <div className="space-y-2 pr-6">
          <h3 className="font-semibold text-blue-900 dark:text-blue-100">
            Japan Best-of-1 Format
          </h3>
          <p className="text-sm text-blue-800 dark:text-blue-200">
            Japanese Pokemon TCG tournaments use a Best-of-1 (BO1) format with
            unique tie-breaker rules. In BO1, a{" "}
            <strong>tie counts as a loss for both players</strong>, which
            significantly impacts deck building and meta choices.
          </p>
          <p className="text-sm text-blue-800 dark:text-blue-200">
            This creates a distinct meta where faster, more aggressive decks are
            favored over control strategies that might lead to time-based ties.
          </p>
        </div>
      </div>
    </div>
  );
}
