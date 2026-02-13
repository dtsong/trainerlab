import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Competitor Onboarding (Closed Beta)",
  description:
    "How invited competitors can get value from TrainerLab in the first 10 minutes and build a weekly prep loop.",
};

export default function OnboardingCompetitorsClosedBetaPage() {
  return (
    <article className="container mx-auto max-w-3xl px-4 py-10">
      <p className="font-mono text-xs uppercase tracking-widest text-teal-600">
        Closed Beta Onboarding
      </p>
      <h1 className="mt-2 text-4xl font-bold tracking-tight text-ink-black">
        Competitor Onboarding Guide
      </h1>

      <p className="mt-6 text-lg text-muted-foreground">
        This guide is for invited competitors in TrainerLab closed beta. Goal:
        get from sign-in to actionable matchup prep in under 10 minutes.
      </p>

      <section className="mt-8">
        <h2 className="text-2xl font-semibold text-slate-900">
          First 10 minutes
        </h2>
        <ol className="mt-4 list-decimal space-y-3 pl-6 text-slate-800">
          <li>
            Open{" "}
            <Link className="text-teal-700 underline" href="/meta/official">
              /meta/official
            </Link>{" "}
            to anchor your prep to official-major signals.
          </li>
          <li>
            Compare with{" "}
            <Link className="text-teal-700 underline" href="/meta/grassroots">
              /meta/grassroots
            </Link>{" "}
            to spot early experimentation and ladder-style pressure.
          </li>
          <li>
            Review{" "}
            <Link className="text-teal-700 underline" href="/tournaments">
              /tournaments
            </Link>{" "}
            with major format windows to confirm which card pool context
            applies.
          </li>
          <li>
            Check{" "}
            <Link className="text-teal-700 underline" href="/events">
              /events
            </Link>{" "}
            for upcoming majors and timeline your testing cycle.
          </li>
          <li>
            Use{" "}
            <Link className="text-teal-700 underline" href="/decks/new">
              /decks/new
            </Link>{" "}
            to build your list and iterate against what is actually winning.
          </li>
        </ol>
      </section>

      <section className="mt-10 rounded-xl border border-slate-200 bg-slate-50 p-5">
        <h2 className="text-xl font-semibold text-slate-900">
          Weekly prep loop
        </h2>
        <ul className="mt-3 list-disc space-y-2 pl-6 text-slate-700">
          <li>
            Monday: scan official-major freshness and top archetype shifts
          </li>
          <li>
            Tuesday-Wednesday: cross-check grassroots divergences and counters
          </li>
          <li>Thursday: lock 60 and sideboard plan for expected field</li>
          <li>Friday: run final matchup reps against top 3 expected decks</li>
        </ul>
      </section>

      <section className="mt-10">
        <h2 className="text-2xl font-semibold text-slate-900">Need access?</h2>
        <div className="mt-4 flex flex-wrap gap-3">
          <Button asChild>
            <Link href="/closed-beta">Request Closed Beta Access</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/lab-notes/introducing-trainerlab-closed-beta">
              Read Announcement
            </Link>
          </Button>
        </div>
      </section>
    </article>
  );
}
