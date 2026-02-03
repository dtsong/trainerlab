"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  FileText,
  Trophy,
  Calendar,
  LayoutGrid,
} from "lucide-react";
import { SectionLabel } from "@/components/ui/section-label";
import { useLabNotes } from "@/hooks/useLabNotes";
import { useTournaments } from "@/hooks/useTournaments";
import { IndexCardSkeleton } from "./skeletons";
import type {
  ApiLabNoteSummary,
  ApiTournamentSummary,
} from "@trainerlab/shared-types";

interface ContentItem {
  title: string;
  description: string;
  date: string;
  href: string;
}

interface ContentColumnProps {
  title: string;
  icon: React.ReactNode;
  items: ContentItem[];
  viewAllHref: string;
  viewAllLabel: string;
  rotation?: number;
  isLoading?: boolean;
  emptyMessage?: string;
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function labNoteToContentItem(note: ApiLabNoteSummary): ContentItem {
  return {
    title: note.title,
    description: note.summary ?? "",
    date: formatDate(note.published_at ?? note.created_at),
    href: `/lab-notes/${note.slug}`,
  };
}

function tournamentToContentItem(t: ApiTournamentSummary): ContentItem {
  const parts: string[] = [];
  if (t.participant_count) parts.push(`${t.participant_count} players`);
  if (t.top_placements?.[0])
    parts.push(`${t.top_placements[0].archetype} takes 1st`);

  return {
    title: t.name,
    description: parts.join(" | ") || t.region,
    date: formatDate(t.date),
    href: `/tournaments/${t.id}`,
  };
}

function upcomingToContentItem(t: ApiTournamentSummary): ContentItem {
  const parts: string[] = [];
  parts.push(formatDate(t.date));
  if (t.participant_count)
    parts.push(`Expected ${t.participant_count}+ players`);
  if (t.region) parts.push(t.region);

  return {
    title: t.name,
    description: parts.join(" | "),
    date: formatDate(t.date),
    href: `/tournaments/${t.id}`,
  };
}

function IndexCard({
  title,
  icon,
  items,
  viewAllHref,
  viewAllLabel,
  rotation = 0,
  isLoading,
  emptyMessage = "No items yet",
}: ContentColumnProps) {
  const rotationClass =
    rotation === 0
      ? ""
      : rotation > 0
        ? "rotate-1 hover:rotate-0"
        : "-rotate-1 hover:rotate-0";

  if (isLoading) {
    return <IndexCardSkeleton />;
  }

  return (
    <div
      className={`relative rounded-lg border border-notebook-grid bg-notebook-cream p-5 shadow-sm transition-all duration-300 hover:shadow-md ${rotationClass}`}
    >
      {/* Paper clip effect */}
      <div className="absolute -top-1 right-8 w-5 h-8 border-2 border-pencil/40 rounded-t-full bg-transparent" />

      {/* Ruled lines background */}
      <div className="absolute inset-0 rounded-lg overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-ruled-lines opacity-30" />
      </div>

      {/* Content */}
      <div className="relative">
        <div className="mb-4 flex items-center gap-2">
          <div className="text-ink-red">{icon}</div>
          <h3 className="font-mono text-sm font-medium uppercase tracking-wide text-ink-black">
            {title}
          </h3>
        </div>

        {items.length === 0 ? (
          <p className="font-mono text-sm text-pencil/60 italic py-4">
            {emptyMessage}
          </p>
        ) : (
          <div className="space-y-4">
            {items.map((item, index) => (
              <Link key={index} href={item.href} className="block group">
                {/* Date - typewriter style */}
                <span className="font-mono text-xs text-pencil/70 uppercase tracking-wider">
                  {item.date}
                </span>
                <h4 className="font-display text-base font-medium text-ink-black group-hover:text-ink-red transition-colors leading-snug">
                  {item.title}
                </h4>
                <p className="mt-1 text-sm text-pencil line-clamp-2 leading-relaxed">
                  {item.description}
                </p>
              </Link>
            ))}
          </div>
        )}

        {/* View all link - handwritten note style */}
        <Link
          href={viewAllHref}
          className="mt-5 inline-flex items-center gap-1 font-mono text-xs uppercase tracking-wide text-pencil hover:text-ink-red transition-colors"
        >
          {viewAllLabel}
          <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}

export function ContentGrid() {
  const [todayISO] = useState(() => new Date().toISOString().split("T")[0]);

  const {
    data: labNotesData,
    isLoading: labNotesLoading,
    isError: labNotesError,
  } = useLabNotes({
    limit: 3,
  });
  const {
    data: tournamentsData,
    isLoading: tournamentsLoading,
    isError: tournamentsError,
  } = useTournaments({ limit: 3 });
  const {
    data: upcomingData,
    isLoading: upcomingLoading,
    isError: upcomingError,
  } = useTournaments({
    start_date: todayISO,
    limit: 3,
  });

  const labNotes = labNotesData?.items.map(labNoteToContentItem) ?? [];
  const tournaments = tournamentsData?.items.map(tournamentToContentItem) ?? [];
  const upcoming = upcomingData?.items.map(upcomingToContentItem) ?? [];

  return (
    <section className="relative py-12 md:py-16 bg-notebook-cream">
      {/* Dot grid background */}
      <div className="absolute inset-0 bg-dot-grid-lg opacity-40" />

      {/* Paper texture */}
      <div className="absolute inset-0 bg-paper-texture" />

      {/* Red margin line */}
      <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-ink-red/20 hidden lg:block" />

      <div className="container relative">
        <div className="lg:pl-8">
          <SectionLabel
            label="Latest Updates"
            icon={<LayoutGrid className="h-4 w-4" />}
            variant="notebook"
            className="mb-8"
          />

          {/* Annotation */}
          <p className="font-mono text-xs text-pencil italic mb-6">
            Research notes, tournament results, and upcoming events
          </p>
        </div>

        {/* Index cards grid with alternating rotations */}
        <div className="grid gap-6 md:grid-cols-3 lg:pl-8">
          <IndexCard
            title="Lab Notes"
            icon={<FileText className="h-5 w-5" />}
            items={labNotes}
            viewAllHref="/lab-notes"
            viewAllLabel="All articles"
            rotation={-1}
            isLoading={labNotesLoading}
            emptyMessage={
              labNotesError ? "Could not load articles" : "No articles yet"
            }
          />
          <IndexCard
            title="Recent Tournaments"
            icon={<Trophy className="h-5 w-5" />}
            items={tournaments}
            viewAllHref="/tournaments"
            viewAllLabel="All tournaments"
            rotation={0}
            isLoading={tournamentsLoading}
            emptyMessage={
              tournamentsError
                ? "Could not load tournaments"
                : "No tournaments yet"
            }
          />
          <IndexCard
            title="Upcoming Events"
            icon={<Calendar className="h-5 w-5" />}
            items={upcoming}
            viewAllHref="/tournaments?filter=upcoming"
            viewAllLabel="Full calendar"
            rotation={1}
            isLoading={upcomingLoading}
            emptyMessage={
              upcomingError ? "Could not load events" : "No upcoming events"
            }
          />
        </div>

        {/* Section divider - dot separator */}
        <div className="mt-12 flex justify-center">
          <div className="flex gap-1">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="w-1.5 h-1.5 rounded-full bg-notebook-grid"
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
