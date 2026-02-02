"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { X, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

const DISMISS_KEY = "trainerlab_jp_alert_dismissed";
const DISMISS_DURATION = 24 * 60 * 60 * 1000; // 24 hours

interface JPAlertBannerProps {
  /** Whether there's significant JP divergence to show */
  hasSignificantDivergence?: boolean;
  /** Custom message to display */
  message?: string;
}

export function JPAlertBanner({
  hasSignificantDivergence = true,
  message = "Japan's meta is diverging from the global meta. New archetypes emerging that could impact your region soon.",
}: JPAlertBannerProps) {
  const [dismissed, setDismissed] = useState(true); // Start true to avoid flash

  useEffect(() => {
    const dismissedAt = localStorage.getItem(DISMISS_KEY);
    if (dismissedAt) {
      const dismissedTime = parseInt(dismissedAt, 10);
      if (Date.now() - dismissedTime < DISMISS_DURATION) {
        setDismissed(true);
        return;
      }
    }
    setDismissed(false);
  }, []);

  const handleDismiss = () => {
    localStorage.setItem(DISMISS_KEY, Date.now().toString());
    setDismissed(true);
  };

  if (dismissed || !hasSignificantDivergence) {
    return null;
  }

  return (
    <div className="relative bg-gradient-to-r from-rose-500 to-rose-600 py-3">
      <div className="container flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-white" />
          <p className="text-sm font-medium text-white">{message}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            asChild
            size="sm"
            variant="secondary"
            className="bg-white/20 text-white hover:bg-white/30"
          >
            <Link href="/meta/japan">View JP Meta</Link>
          </Button>
          <button
            onClick={handleDismiss}
            className="rounded-full p-1 text-white/80 hover:bg-white/20 hover:text-white transition-colors"
            aria-label="Dismiss alert"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
