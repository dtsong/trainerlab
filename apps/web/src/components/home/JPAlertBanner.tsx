"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { X, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useHomeMetaData } from "@/hooks/useMeta";
import { computeJPDivergence } from "@/lib/home-utils";

const DISMISS_KEY = "trainerlab_jp_alert_dismissed";
const DISMISS_DURATION = 24 * 60 * 60 * 1000; // 24 hours

export function JPAlertBanner() {
  const [dismissed, setDismissed] = useState(true); // Start true to avoid flash
  const { globalMeta, jpMeta } = useHomeMetaData();

  const { hasSignificantDivergence, message } = computeJPDivergence(
    globalMeta,
    jpMeta
  );

  useEffect(() => {
    try {
      const dismissedAt = localStorage.getItem(DISMISS_KEY);
      if (dismissedAt) {
        const dismissedTime = parseInt(dismissedAt, 10);
        if (Date.now() - dismissedTime < DISMISS_DURATION) {
          setDismissed(true);
          return;
        }
      }
    } catch {
      // localStorage unavailable (SSR, privacy mode, etc.)
    }
    setDismissed(false);
  }, []);

  const handleDismiss = () => {
    try {
      localStorage.setItem(DISMISS_KEY, Date.now().toString());
    } catch {
      // localStorage unavailable
    }
    setDismissed(true);
  };

  if (dismissed || !hasSignificantDivergence) {
    return null;
  }

  return (
    <div
      role="alert"
      className="relative border border-signal-jp/20 bg-signal-jp/5 rounded-lg py-3"
    >
      <div className="container flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 shrink-0 text-signal-jp" />
          <p className="text-sm font-medium text-signal-jp">{message}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            asChild
            size="sm"
            variant="outline"
            className="border-signal-jp/30 text-signal-jp hover:bg-signal-jp/10"
          >
            <Link href="/meta/japan">View JP Meta</Link>
          </Button>
          <button
            onClick={handleDismiss}
            className="rounded-full p-1 text-signal-jp/60 hover:bg-signal-jp/10 hover:text-signal-jp transition-colors"
            aria-label="Dismiss alert"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
