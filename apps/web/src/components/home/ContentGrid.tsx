"use client";

import Link from "next/link";
import {
  ArrowRight,
  FileText,
  Trophy,
  Calendar,
  LayoutGrid,
} from "lucide-react";
import { SectionLabel } from "@/components/ui/section-label";

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
}

function IndexCard({
  title,
  icon,
  items,
  viewAllHref,
  viewAllLabel,
  rotation = 0,
}: ContentColumnProps) {
  const rotationClass =
    rotation === 0
      ? ""
      : rotation > 0
        ? "rotate-1 hover:rotate-0"
        : "-rotate-1 hover:rotate-0";

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

// Mock data - will be replaced with real API data
const mockLabNotes: ContentItem[] = [
  {
    title: "Charizard's Counter Matrix",
    description:
      "Deep dive into the best counters for the current king of the meta.",
    date: "Feb 1",
    href: "/lab-notes/charizard-counters",
  },
  {
    title: "Budget Builds: Competitive on $50",
    description: "Viable tournament decks that won't break the bank.",
    date: "Jan 28",
    href: "/lab-notes/budget-builds",
  },
  {
    title: "Japan Meta Report: Week 4",
    description:
      "This week's JP tournament results and what they mean for you.",
    date: "Jan 25",
    href: "/lab-notes/jp-week-4",
  },
];

const mockTournaments: ContentItem[] = [
  {
    title: "Charlotte Regionals",
    description: "1,200 players | Charizard ex takes 1st, Gardevoir in Top 8",
    date: "Jan 28",
    href: "/tournaments/charlotte-regionals",
  },
  {
    title: "Liverpool Regionals",
    description: "800 players | Surprise Lugia VSTAR dominance",
    date: "Jan 27",
    href: "/tournaments/liverpool-regionals",
  },
  {
    title: "OCIC Day 2 Meta",
    description: "450 day 2 players | 23% Charizard, 18% Gardevoir",
    date: "Jan 21",
    href: "/tournaments/ocic",
  },
];

const mockUpcoming: ContentItem[] = [
  {
    title: "Knoxville Regionals",
    description: "Feb 10-11 | Expected 1,500+ players",
    date: "Feb 10",
    href: "/tournaments/knoxville-regionals",
  },
  {
    title: "Dortmund Regionals",
    description: "Feb 17-18 | EU's largest event this season",
    date: "Feb 17",
    href: "/tournaments/dortmund-regionals",
  },
  {
    title: "LAIC 2024",
    description: "Mar 15-17 | Latin America International Championships",
    date: "Mar 15",
    href: "/tournaments/laic-2024",
  },
];

export function ContentGrid() {
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
            items={mockLabNotes}
            viewAllHref="/lab-notes"
            viewAllLabel="All articles"
            rotation={-1}
          />
          <IndexCard
            title="Recent Tournaments"
            icon={<Trophy className="h-5 w-5" />}
            items={mockTournaments}
            viewAllHref="/tournaments"
            viewAllLabel="All tournaments"
            rotation={0}
          />
          <IndexCard
            title="Upcoming Events"
            icon={<Calendar className="h-5 w-5" />}
            items={mockUpcoming}
            viewAllHref="/tournaments?filter=upcoming"
            viewAllLabel="Full calendar"
            rotation={1}
          />
        </div>

        {/* Section divider - torn paper effect simulation */}
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
