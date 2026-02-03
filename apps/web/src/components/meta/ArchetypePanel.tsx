"use client";

import { X, ExternalLink } from "lucide-react";
import Link from "next/link";
import { PanelOverlay } from "@/components/ui/panel-overlay";
import { TierBadge } from "@/components/ui/tier-badge";
import { TrendArrow } from "@/components/ui/trend-arrow";
import { Button } from "@/components/ui/button";
import { MatchupSpread, type MatchupData } from "./MatchupSpread";
import type { Tier } from "./TierList";
import { cn } from "@/lib/utils";

interface KeyCard {
  name: string;
  inclusionRate: number;
  avgCopies: number;
}

interface BuildVariant {
  name: string;
  description: string;
  share: number;
}

interface RecentResult {
  tournament: string;
  placement: string;
  date: string;
}

export interface ArchetypePanelData {
  id: string;
  name: string;
  tier: Tier;
  share: number;
  trend: "up" | "down" | "stable";
  trendValue?: number;
  keyCards: KeyCard[];
  buildVariants: BuildVariant[];
  matchups: MatchupData[];
  recentResults: RecentResult[];
}

interface PanelSectionProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

function PanelSection({ title, children, className }: PanelSectionProps) {
  return (
    <div className={cn("border-b border-terminal-border pb-4", className)}>
      <h3 className="mb-3 font-mono text-xs uppercase tracking-wide text-terminal-muted">
        {title}
      </h3>
      {children}
    </div>
  );
}

export interface ArchetypePanelProps {
  archetype: ArchetypePanelData | null;
  isOpen: boolean;
  onClose: () => void;
}

export function ArchetypePanel({
  archetype,
  isOpen,
  onClose,
}: ArchetypePanelProps) {
  if (!archetype) return null;

  return (
    <PanelOverlay isOpen={isOpen} onClose={onClose}>
      {/* Panel container */}
      <div
        className={cn(
          "fixed right-0 top-0 h-full w-full max-w-[480px] transform overflow-y-auto",
          "bg-terminal-bg text-terminal-text shadow-2xl transition-transform duration-300",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-start justify-between border-b border-terminal-border bg-terminal-surface p-4">
          <div className="flex items-start gap-3">
            {/* Signature card placeholder */}
            <div className="h-16 w-12 flex-shrink-0 rounded bg-gradient-to-br from-slate-600 to-slate-700" />
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-display text-xl font-semibold text-white">
                  {archetype.name}
                </h2>
                <TierBadge tier={archetype.tier} size="md" />
              </div>
              <div className="mt-1 flex items-center gap-2">
                <span className="font-mono text-lg text-terminal-accent">
                  {archetype.share.toFixed(1)}%
                </span>
                <TrendArrow
                  direction={archetype.trend}
                  value={archetype.trendValue}
                />
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-terminal-muted hover:bg-terminal-border hover:text-white transition-colors"
            aria-label="Close panel"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-4 p-4">
          {/* Key Cards */}
          <PanelSection title="Key Cards">
            <div className="space-y-2">
              {archetype.keyCards.slice(0, 8).map((card) => (
                <div
                  key={card.name}
                  className="flex items-center justify-between rounded bg-terminal-surface px-3 py-2"
                >
                  <span className="text-sm text-terminal-text">
                    {card.name}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-terminal-muted">
                      {(card.inclusionRate * 100).toFixed(0)}%
                    </span>
                    <span className="font-mono text-xs text-terminal-accent">
                      {card.avgCopies.toFixed(1)}x
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </PanelSection>

          {/* Build Variants */}
          <PanelSection title="Build Variants">
            <div className="space-y-2">
              {archetype.buildVariants.map((variant) => (
                <div
                  key={variant.name}
                  className="rounded bg-terminal-surface p-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-terminal-text">
                      {variant.name}
                    </span>
                    <span className="font-mono text-xs text-terminal-accent">
                      {variant.share.toFixed(0)}%
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-terminal-muted">
                    {variant.description}
                  </p>
                </div>
              ))}
            </div>
          </PanelSection>

          {/* Matchup Spread */}
          <PanelSection title="Matchup Spread">
            <MatchupSpread matchups={archetype.matchups} />
          </PanelSection>

          {/* Recent Results */}
          <PanelSection title="Recent Results" className="border-b-0">
            <div className="space-y-2">
              {archetype.recentResults.slice(0, 5).map((result, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between rounded bg-terminal-surface px-3 py-2"
                >
                  <div>
                    <span className="text-sm text-terminal-text">
                      {result.tournament}
                    </span>
                    <span className="ml-2 font-mono text-xs text-terminal-muted">
                      {result.date}
                    </span>
                  </div>
                  <span className="font-mono text-sm font-semibold text-terminal-accent">
                    {result.placement}
                  </span>
                </div>
              ))}
            </div>
          </PanelSection>

          {/* Commerce CTA */}
          <div className="pt-2">
            <Button
              asChild
              className="w-full bg-teal-500 hover:bg-teal-600 text-white"
            >
              <Link
                href={`/decks/new?archetype=${encodeURIComponent(archetype.name)}`}
              >
                Build This Deck
                <ExternalLink className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </PanelOverlay>
  );
}
