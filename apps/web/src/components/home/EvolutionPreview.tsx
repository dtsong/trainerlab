"use client";

import Link from "next/link";
import { ArrowRight, GitBranch, TrendingUp } from "lucide-react";
import { SectionLabel } from "@/components/ui/section-label";
import { Button } from "@/components/ui/button";

interface AdaptationStep {
  date: string;
  description: string;
}

interface EvolutionPreviewProps {
  archetypeName?: string;
  currentShare?: number;
  previousShare?: number;
  adaptationSteps?: AdaptationStep[];
}

// Mock data - will be replaced with real API data
const mockData: Required<EvolutionPreviewProps> = {
  archetypeName: "Charizard ex",
  currentShare: 18.5,
  previousShare: 12.2,
  adaptationSteps: [
    {
      date: "Jan 15",
      description: "Adopted 4-copy Arcanine line for draw power",
    },
    {
      date: "Jan 22",
      description: "Shifted to Bibarel engine over Radiant Greninja",
    },
    {
      date: "Feb 1",
      description: "Added Manaphy for bench protection against Roaring Moon",
    },
  ],
};

export function EvolutionPreview({
  archetypeName = mockData.archetypeName,
  currentShare = mockData.currentShare,
  previousShare = mockData.previousShare,
  adaptationSteps = mockData.adaptationSteps,
}: EvolutionPreviewProps) {
  const changePercent = currentShare - previousShare;

  return (
    <section className="bg-slate-50 py-12 md:py-16">
      <div className="container">
        <SectionLabel
          label="Deck Evolution"
          icon={<TrendingUp className="h-4 w-4" />}
          className="mb-8"
        />

        <div className="grid gap-8 lg:grid-cols-2 lg:items-center">
          {/* Left: Mini chart placeholder + stats */}
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-display text-xl font-semibold text-slate-900">
                {archetypeName}
              </h3>
              <span className="font-mono text-2xl font-bold text-teal-600">
                {currentShare.toFixed(1)}%
              </span>
            </div>

            {/* Mini chart placeholder */}
            <div className="mb-4 h-32 rounded-lg bg-gradient-to-r from-slate-100 to-slate-50">
              {/* Will be replaced with actual chart component */}
              <div className="flex h-full items-end justify-around px-4 pb-2">
                {[40, 55, 48, 62, 58, 75, 82].map((height, i) => (
                  <div
                    key={i}
                    className="w-4 rounded-t bg-teal-400"
                    style={{ height: `${height}%` }}
                  />
                ))}
              </div>
            </div>

            <p className="text-sm text-slate-500">
              <span
                className={
                  changePercent >= 0 ? "text-green-600" : "text-red-600"
                }
              >
                {changePercent >= 0 ? "+" : ""}
                {changePercent.toFixed(1)}%
              </span>{" "}
              over the last 30 days
            </p>
          </div>

          {/* Right: Adaptation steps */}
          <div>
            <h4 className="mb-4 flex items-center gap-2 font-medium text-slate-700">
              <GitBranch className="h-4 w-4 text-teal-500" />
              How it&apos;s adapting
            </h4>
            <div className="space-y-4">
              {adaptationSteps.map((step, index) => (
                <div key={index} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="h-2 w-2 rounded-full bg-teal-500" />
                    {index < adaptationSteps.length - 1 && (
                      <div className="h-full w-px bg-slate-200" />
                    )}
                  </div>
                  <div className="pb-4">
                    <span className="font-mono text-xs text-slate-400">
                      {step.date}
                    </span>
                    <p className="text-slate-700">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
            <Button variant="ghost" size="sm" className="mt-4" asChild>
              <Link
                href={`/meta/archetypes/${encodeURIComponent(archetypeName)}`}
              >
                Read the full story
                <ArrowRight className="ml-1 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
