import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Introducing TrainerLab Closed Beta",
  description:
    "TrainerLab is now in closed beta for invited Pokemon TCG competitors, creators, coaches, and stakeholders.",
};

export default function IntroducingTrainerLabClosedBetaPage() {
  return (
    <article className="container mx-auto max-w-3xl px-4 py-10">
      <p className="font-mono text-xs uppercase tracking-widest text-teal-600">
        Closed Beta Announcement
      </p>
      <h1 className="mt-2 text-4xl font-bold tracking-tight text-ink-black">
        Introducing TrainerLab (Closed Beta)
      </h1>

      <p className="mt-6 text-lg text-muted-foreground">
        TrainerLab is a competitive intelligence platform for Pokemon TCG. We
        are launching in a closed beta with invited stakeholders so we can
        refine signal quality, workflows, and onboarding before broader release.
      </p>

      <section className="mt-8 space-y-4 text-base leading-7 text-slate-800">
        <p>
          We built TrainerLab for people who do their homework before a major:
          competitors preparing matchups, coaches teaching better sequencing,
          creators planning content from real shifts, and stakeholders who need
          a clearer view of where the format is headed.
        </p>
        <p>
          The platform combines official-major and grassroots tracks, date-based
          format windows, and confidence-oriented freshness cues so users can
          make better calls with context, not just raw numbers.
        </p>
        <p>
          This closed beta is intentionally invite-led. We are prioritizing
          operators and power users who will pressure-test workflows and give
          direct feedback on what should ship next.
        </p>
      </section>

      <section className="mt-10 rounded-xl border border-slate-200 bg-slate-50 p-5">
        <h2 className="text-xl font-semibold text-slate-900">
          What invitees get
        </h2>
        <ul className="mt-3 list-disc space-y-2 pl-6 text-slate-700">
          <li>Early access to official and grassroots meta analysis tracks</li>
          <li>Tournament and event views with major format window context</li>
          <li>
            Deck research workflows tuned for weekly prep and content planning
          </li>
          <li>Direct feedback loop with the TrainerLab product roadmap</li>
        </ul>
      </section>

      <section className="mt-10">
        <h2 className="text-2xl font-semibold text-slate-900">Start here</h2>
        <div className="mt-4 flex flex-wrap gap-3">
          <Button asChild>
            <Link href="/closed-beta">Request Closed Beta Access</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/lab-notes/onboarding-competitors-closed-beta">
              Competitor Onboarding
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/lab-notes/onboarding-creators-coaches-closed-beta">
              Creator + Coach Onboarding
            </Link>
          </Button>
        </div>
      </section>
    </article>
  );
}
