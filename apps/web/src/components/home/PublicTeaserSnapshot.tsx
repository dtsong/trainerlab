"use client";

import Link from "next/link";
import { ArrowRight, Clock3, Lock } from "lucide-react";

import { useHomeTeaser } from "@/hooks";
import { Button } from "@/components/ui/button";
import { SectionLabel } from "@/components/ui/section-label";

export function PublicTeaserSnapshot() {
  const { data, isLoading, isError } = useHomeTeaser("standard");
  const delayDays = data?.delay_days ?? 14;

  return (
    <section className="bg-notebook-aged py-12 md:py-16">
      <div className="container">
        <div className="mb-6 flex items-center justify-between gap-4">
          <SectionLabel
            label="Public Meta Teaser"
            icon={<Clock3 className="h-4 w-4" />}
            variant="notebook"
          />
          <span className="rounded-full border border-notebook-grid bg-notebook-cream px-3 py-1 font-mono text-xs text-pencil">
            Delayed by {delayDays} days
          </span>
        </div>

        <div className="rounded-xl border border-notebook-grid bg-notebook-cream p-6 shadow-sm">
          <p className="mb-4 text-sm text-pencil">
            Get a delayed look at format trends. Live intelligence, deck-level
            insights, and fresh tournament reads are available to closed beta
            members.
          </p>

          {isLoading && <div className="h-24 animate-pulse rounded bg-muted" />}

          {isError && !isLoading && (
            <p className="text-sm text-muted-foreground">
              Teaser data is temporarily unavailable.
            </p>
          )}

          {!isLoading && !isError && data && (
            <div className="space-y-3">
              {data.top_archetypes.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Not enough delayed sample data yet.
                </p>
              ) : (
                data.top_archetypes.map((item, index) => (
                  <div
                    key={item.name}
                    className="flex items-center justify-between rounded-lg border border-notebook-grid bg-white px-3 py-2"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-6 text-center font-mono text-xs text-pencil">
                        #{index + 1}
                      </span>
                      <span className="font-medium text-ink-black">
                        {item.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="font-mono text-ink-red">
                        {(item.global_share * 100).toFixed(1)}%
                      </span>
                      {item.jp_share !== null && (
                        <span className="font-mono text-teal-700">
                          JP {(item.jp_share * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}

              <p className="pt-2 text-xs text-muted-foreground">
                Sample size: {data.sample_size.toLocaleString()} decklists.
              </p>
            </div>
          )}

          <div className="mt-6 flex flex-wrap gap-3">
            <Button asChild>
              <Link href="/auth/login">
                <Lock className="mr-2 h-4 w-4" />
                Sign In for Closed Beta
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/lab-notes">
                Browse Lab Notes
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/lab-notes/introducing-trainerlab-closed-beta">
                Closed Beta Announcement
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/lab-notes/onboarding-competitors-closed-beta">
                Competitor Onboarding
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
