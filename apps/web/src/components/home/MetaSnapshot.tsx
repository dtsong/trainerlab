"use client";

import Link from "next/link";
import { ArrowRight, ExternalLink, BarChart3 } from "lucide-react";
import { TrendArrow } from "@/components/ui/trend-arrow";
import { JPSignalBadge } from "@/components/ui/jp-signal-badge";
import { SectionLabel } from "@/components/ui/section-label";
import { Button } from "@/components/ui/button";

interface ArchetypeSnapshotProps {
  rank: number;
  name: string;
  metaShare: number;
  trend: "up" | "down" | "stable";
  trendValue?: number;
  jpSignal?: number;
  cardImage?: string;
}

function ArchetypeCard({
  rank,
  name,
  metaShare,
  trend,
  trendValue,
  jpSignal,
  cardImage,
}: ArchetypeSnapshotProps) {
  return (
    <div className="group relative flex flex-col items-center rounded-lg border border-slate-200 bg-white p-4 transition-all hover:border-teal-200 hover:shadow-md">
      {/* Rank badge */}
      <div className="absolute -top-2 -left-2 flex h-6 w-6 items-center justify-center rounded-full bg-slate-900 text-xs font-bold text-white">
        {rank}
      </div>

      {/* Card image placeholder */}
      <div className="mb-3 h-24 w-16 rounded bg-gradient-to-br from-slate-200 to-slate-300" />

      {/* Name and stats */}
      <h3 className="text-center font-medium text-slate-900">{name}</h3>
      <div className="mt-1 flex items-center gap-2">
        <span className="font-mono text-sm text-slate-600">
          {metaShare.toFixed(1)}%
        </span>
        <TrendArrow direction={trend} value={trendValue} size="sm" />
      </div>

      {/* JP Signal badge if present */}
      {jpSignal !== undefined && jpSignal > 0 && (
        <div className="mt-2">
          <JPSignalBadge
            jpShare={metaShare + jpSignal}
            enShare={metaShare}
            threshold={5}
          />
        </div>
      )}

      {/* Commerce link */}
      <Button
        variant="ghost"
        size="sm"
        className="mt-3 text-xs text-teal-600 hover:text-teal-700"
        asChild
      >
        <Link href={`/decks/new?archetype=${encodeURIComponent(name)}`}>
          Build It
          <ExternalLink className="ml-1 h-3 w-3" />
        </Link>
      </Button>
    </div>
  );
}

// Mock data - will be replaced with real API data
const mockArchetypes: ArchetypeSnapshotProps[] = [
  {
    rank: 1,
    name: "Charizard ex",
    metaShare: 18.5,
    trend: "up",
    trendValue: 2.3,
    jpSignal: 0,
  },
  {
    rank: 2,
    name: "Lugia VSTAR",
    metaShare: 14.2,
    trend: "down",
    trendValue: -1.1,
    jpSignal: 15,
  },
  {
    rank: 3,
    name: "Gardevoir ex",
    metaShare: 12.8,
    trend: "stable",
    jpSignal: 0,
  },
  {
    rank: 4,
    name: "Miraidon ex",
    metaShare: 9.4,
    trend: "up",
    trendValue: 0.8,
    jpSignal: 25,
  },
  {
    rank: 5,
    name: "Arceus VSTAR",
    metaShare: 7.6,
    trend: "down",
    trendValue: -2.1,
    jpSignal: 0,
  },
];

export function MetaSnapshot() {
  return (
    <section className="py-12 md:py-16">
      <div className="container">
        <div className="mb-8 flex items-center justify-between">
          <SectionLabel
            label="Meta Snapshot"
            icon={<BarChart3 className="h-4 w-4" />}
          />
          <Button variant="ghost" size="sm" asChild>
            <Link href="/meta">
              View Full Meta
              <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </Button>
        </div>

        {/* Horizontal scrolling on mobile, grid on desktop */}
        <div className="flex gap-4 overflow-x-auto pb-4 md:grid md:grid-cols-5 md:overflow-visible md:pb-0">
          {mockArchetypes.map((archetype) => (
            <div
              key={archetype.rank}
              className="min-w-[160px] flex-shrink-0 md:min-w-0"
            >
              <ArchetypeCard {...archetype} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
