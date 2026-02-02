"use client";

import Link from "next/link";
import { ArrowRight, Flag, Globe } from "lucide-react";
import { SectionLabel } from "@/components/ui/section-label";
import { JPSignalBadge } from "@/components/ui/jp-signal-badge";
import { Button } from "@/components/ui/button";

interface DeckComparison {
  rank: number;
  jpName: string;
  jpShare: number;
  enName: string;
  enShare: number;
  divergence: number;
}

// Mock data - will be replaced with real API data
const mockComparisons: DeckComparison[] = [
  {
    rank: 1,
    jpName: "Raging Bolt ex",
    jpShare: 22.1,
    enName: "Charizard ex",
    enShare: 18.5,
    divergence: 35,
  },
  {
    rank: 2,
    jpName: "Charizard ex",
    jpShare: 15.8,
    enName: "Lugia VSTAR",
    enShare: 14.2,
    divergence: 0,
  },
  {
    rank: 3,
    jpName: "Terapagos ex",
    jpShare: 12.4,
    enName: "Gardevoir ex",
    enShare: 12.8,
    divergence: 28,
  },
];

export function JPPreview() {
  return (
    <section className="bg-slate-900 py-12 md:py-16">
      <div className="container">
        <div className="mb-8 flex items-center justify-between">
          <SectionLabel
            label="Japan vs Global"
            icon={<Globe className="h-4 w-4" />}
            className="text-slate-200"
          />
          <Button
            variant="ghost"
            size="sm"
            className="text-slate-400 hover:text-white"
            asChild
          >
            <Link href="/meta/japan">
              Full JP Analysis
              <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </Button>
        </div>

        {/* Comparison grid */}
        <div className="overflow-hidden rounded-xl border border-slate-700">
          {/* Header row */}
          <div className="grid grid-cols-2 border-b border-slate-700 bg-slate-800/50 text-sm font-medium">
            <div className="flex items-center gap-2 px-4 py-3 text-slate-300">
              <Flag className="h-4 w-4 text-rose-400" />
              Japan Top 3
            </div>
            <div className="flex items-center gap-2 border-l border-slate-700 px-4 py-3 text-slate-300">
              <Flag className="h-4 w-4 text-teal-400" />
              Global Top 3
            </div>
          </div>

          {/* Data rows */}
          {mockComparisons.map((comparison, index) => (
            <div
              key={comparison.rank}
              className={`grid grid-cols-2 ${
                index < mockComparisons.length - 1
                  ? "border-b border-slate-700/50"
                  : ""
              }`}
            >
              <div className="flex items-center gap-3 px-4 py-3">
                <span className="font-mono text-sm text-slate-500">
                  {comparison.rank}
                </span>
                <div className="flex-1">
                  <span className="font-medium text-white">
                    {comparison.jpName}
                  </span>
                  <span className="ml-2 font-mono text-sm text-slate-400">
                    {comparison.jpShare}%
                  </span>
                </div>
                {comparison.divergence > 0 && (
                  <JPSignalBadge
                    jpShare={comparison.jpShare + comparison.divergence}
                    enShare={comparison.jpShare}
                    threshold={5}
                  />
                )}
              </div>
              <div className="flex items-center gap-3 border-l border-slate-700/50 px-4 py-3">
                <span className="font-mono text-sm text-slate-500">
                  {comparison.rank}
                </span>
                <div className="flex-1">
                  <span className="font-medium text-white">
                    {comparison.enName}
                  </span>
                  <span className="ml-2 font-mono text-sm text-slate-400">
                    {comparison.enShare}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Prediction callout */}
        <div className="mt-6 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3">
          <p className="text-sm text-amber-200">
            <strong className="font-medium">Prediction:</strong> Raging Bolt ex
            likely to enter NA meta within 2-3 weeks as players adapt JP
            strategies. Currently seeing 35% higher play rate in Japan.
          </p>
        </div>
      </div>
    </section>
  );
}
