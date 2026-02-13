import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Creator + Coach Onboarding (Closed Beta)",
  description:
    "How invited creators and coaches can use TrainerLab closed beta for repeatable content and teaching workflows.",
};

export default function OnboardingCreatorsCoachesClosedBetaPage() {
  return (
    <article className="container mx-auto max-w-3xl px-4 py-10">
      <p className="font-mono text-xs uppercase tracking-widest text-teal-600">
        Closed Beta Onboarding
      </p>
      <h1 className="mt-2 text-4xl font-bold tracking-tight text-ink-black">
        Creator + Coach Onboarding Guide
      </h1>

      <p className="mt-6 text-lg text-muted-foreground">
        This guide is for invited creators, coaches, and analysts who need
        repeatable research workflows they can trust and explain.
      </p>

      <section className="mt-8">
        <h2 className="text-2xl font-semibold text-slate-900">
          Fast start workflow
        </h2>
        <ol className="mt-4 list-decimal space-y-3 pl-6 text-slate-800">
          <li>
            Start with{" "}
            <Link className="text-teal-700 underline" href="/meta/official">
              official meta
            </Link>{" "}
            for stable major narratives.
          </li>
          <li>
            Layer in{" "}
            <Link className="text-teal-700 underline" href="/meta/grassroots">
              grassroots meta
            </Link>{" "}
            to find experimentation before it reaches majors.
          </li>
          <li>
            Use{" "}
            <Link className="text-teal-700 underline" href="/tournaments">
              tournament filters
            </Link>{" "}
            to scope by major format window and season.
          </li>
          <li>
            Pull examples from{" "}
            <Link className="text-teal-700 underline" href="/lab-notes">
              Lab Notes
            </Link>{" "}
            for structured writeups and recurring formats.
          </li>
        </ol>
      </section>

      <section className="mt-10 rounded-xl border border-slate-200 bg-slate-50 p-5">
        <h2 className="text-xl font-semibold text-slate-900">
          Publishing cadence template
        </h2>
        <ul className="mt-3 list-disc space-y-2 pl-6 text-slate-700">
          <li>Weekly: official-major movement and breakout archetype watch</li>
          <li>Pre-event: matchup map and risk-adjusted deck recommendations</li>
          <li>
            Post-event: what changed, what stayed noise, what to test next
          </li>
          <li>Coaching: assign students one data-backed adjustment per week</li>
        </ul>
      </section>

      <section className="mt-10">
        <h2 className="text-2xl font-semibold text-slate-900">
          Closed beta access + feedback
        </h2>
        <p className="mt-3 text-slate-700">
          Invitees are encouraged to submit workflow friction and feature
          requests in our beta feedback thread.
        </p>
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
