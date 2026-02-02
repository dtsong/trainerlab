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

function SpecimenCard({
  rank,
  name,
  metaShare,
  trend,
  trendValue,
  jpSignal,
  animationDelay = "0s",
}: ArchetypeSnapshotProps & { animationDelay?: string }) {
  return (
    <div
      className="group relative flex flex-col items-center rounded-lg border border-notebook-grid bg-notebook-cream p-4 shadow-sm transition-all hover:shadow-md hover:-translate-y-1 motion-safe:animate-paper-rustle"
      style={
        {
          "--rustle-base": `${(rank % 2 === 0 ? 1 : -1) * 0.5}deg`,
          animationDelay,
          animationDuration: `${5 + rank * 0.5}s`,
        } as React.CSSProperties
      }
    >
      {/* Red rank badge - like professor's grading mark */}
      <div className="absolute -top-3 -left-3 flex h-8 w-8 items-center justify-center rounded-full bg-ink-red text-sm font-mono font-bold text-white shadow-sm ring-2 ring-notebook-cream">
        {rank}
      </div>

      {/* Tape effect at top right - with subtle wiggle */}
      <div className="absolute -top-1 right-3 w-8 h-3 bg-gradient-to-b from-amber-100/80 to-amber-200/60 rounded-sm rotate-12 shadow-sm motion-safe:animate-tape-wiggle" />

      {/* Card image placeholder - styled as specimen photo */}
      <div className="relative mb-4 mt-2">
        <div className="h-24 w-16 rounded bg-gradient-to-br from-slate-200 to-slate-300 shadow-inner" />
        {/* Photo corner effect */}
        <div className="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2 border-notebook-grid" />
      </div>

      {/* Name - typewritten label style */}
      <h3 className="text-center font-mono text-sm font-medium text-ink-black uppercase tracking-wide">
        {name}
      </h3>

      {/* Stats row */}
      <div className="mt-2 flex items-center gap-2 bg-notebook-aged/50 px-2 py-1 rounded-sm">
        <span className="font-mono text-sm font-bold text-ink-red">
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

      {/* Commerce link - styled as handwritten note */}
      <Button
        variant="ghost"
        size="sm"
        className="mt-3 text-xs font-mono text-pencil hover:text-ink-red hover:bg-notebook-aged/50"
        asChild
      >
        <Link href={`/decks/new?archetype=${encodeURIComponent(name)}`}>
          Build It
          <ExternalLink className="ml-1 h-3 w-3" />
        </Link>
      </Button>

      {/* Subtle ruled line at bottom */}
      <div className="absolute bottom-0 left-2 right-2 h-px bg-gradient-to-r from-transparent via-notebook-grid to-transparent" />
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
    <section className="relative py-12 md:py-16 bg-notebook-aged">
      {/* Subtle texture */}
      <div className="absolute inset-0 bg-paper-texture" />

      {/* Red margin line continuation */}
      <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-ink-red/20 hidden lg:block" />

      <div className="container relative">
        <div className="mb-8 flex items-center justify-between lg:pl-8">
          <SectionLabel
            label="Meta Snapshot"
            icon={<BarChart3 className="h-4 w-4" />}
            variant="notebook"
          />
          <Button
            variant="ghost"
            size="sm"
            className="font-mono text-xs uppercase tracking-wide text-pencil hover:text-ink-red hover:bg-notebook-cream"
            asChild
          >
            <Link href="/meta">
              View Full Meta
              <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </Button>
        </div>

        {/* Section annotation */}
        <div className="mb-6 lg:pl-8">
          <p className="font-mono text-xs text-pencil italic">
            Current tournament meta analysis &mdash; updated weekly
          </p>
        </div>

        {/* Horizontal scrolling on mobile, grid on desktop */}
        <div className="flex gap-4 overflow-x-auto pb-4 md:grid md:grid-cols-5 md:overflow-visible md:pb-0 lg:pl-8">
          {mockArchetypes.map((archetype, index) => (
            <div
              key={archetype.rank}
              className="min-w-[160px] flex-shrink-0 md:min-w-0"
            >
              <SpecimenCard {...archetype} animationDelay={`${index * 0.8}s`} />
            </div>
          ))}
        </div>

        {/* Bottom annotation - with gentle rustle */}
        <div className="mt-6 flex justify-end lg:pr-8">
          <div
            className="bg-notebook-cream border border-notebook-grid px-3 py-1.5 rounded-sm shadow-sm motion-safe:animate-paper-rustle"
            style={{ "--rustle-base": "1deg" } as React.CSSProperties}
          >
            <span className="font-mono text-xs text-pencil">
              Data from <span className="text-ink-red font-medium">47</span>{" "}
              tournaments
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
