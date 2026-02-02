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
}

function ContentColumn({
  title,
  icon,
  items,
  viewAllHref,
  viewAllLabel,
}: ContentColumnProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="mb-4 flex items-center gap-2 text-slate-700">
        {icon}
        <h3 className="font-medium">{title}</h3>
      </div>

      <div className="space-y-4">
        {items.map((item, index) => (
          <Link key={index} href={item.href} className="block group">
            <span className="font-mono text-xs text-slate-400">
              {item.date}
            </span>
            <h4 className="font-medium text-slate-900 group-hover:text-teal-600 transition-colors">
              {item.title}
            </h4>
            <p className="mt-1 text-sm text-slate-500 line-clamp-2">
              {item.description}
            </p>
          </Link>
        ))}
      </div>

      <Link
        href={viewAllHref}
        className="mt-4 flex items-center gap-1 text-sm font-medium text-teal-600 hover:text-teal-700"
      >
        {viewAllLabel}
        <ArrowRight className="h-4 w-4" />
      </Link>
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
    <section className="py-12 md:py-16">
      <div className="container">
        <SectionLabel
          label="Latest Updates"
          icon={<LayoutGrid className="h-4 w-4" />}
          className="mb-8"
        />

        <div className="grid gap-6 md:grid-cols-3">
          <ContentColumn
            title="Lab Notes"
            icon={<FileText className="h-5 w-5 text-teal-500" />}
            items={mockLabNotes}
            viewAllHref="/lab-notes"
            viewAllLabel="All articles"
          />
          <ContentColumn
            title="Recent Tournaments"
            icon={<Trophy className="h-5 w-5 text-amber-500" />}
            items={mockTournaments}
            viewAllHref="/tournaments"
            viewAllLabel="All tournaments"
          />
          <ContentColumn
            title="Upcoming Events"
            icon={<Calendar className="h-5 w-5 text-rose-500" />}
            items={mockUpcoming}
            viewAllHref="/tournaments?filter=upcoming"
            viewAllLabel="Full calendar"
          />
        </div>
      </div>
    </section>
  );
}
