"use client";

import Link from "next/link";
import { ArrowRight, TrendingUp, Users, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";

interface StatItemProps {
  icon: React.ReactNode;
  value: string;
  label: string;
}

function StatItem({ icon, value, label }: StatItemProps) {
  return (
    <div className="flex items-center gap-2">
      <div className="text-teal-500">{icon}</div>
      <div>
        <span className="font-mono text-lg font-semibold text-slate-900">
          {value}
        </span>
        <span className="ml-1 text-sm text-slate-500">{label}</span>
      </div>
    </div>
  );
}

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-parchment-50 to-white py-16 md:py-24">
      <div className="container">
        <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
          {/* Text content */}
          <div className="max-w-xl">
            <h1 className="font-display text-4xl font-bold tracking-tight text-slate-900 md:text-5xl lg:text-6xl">
              Data-Driven
              <br />
              <span className="text-teal-600">Deck Building</span>
            </h1>
            <p className="mt-6 text-lg text-slate-600">
              Your competitive research lab for Pokemon TCG. Real-time meta
              analysis, Japan format preview, and smart deck building tools
              trusted by competitive players.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Button
                asChild
                size="lg"
                className="bg-teal-500 hover:bg-teal-600"
              >
                <Link href="/meta">
                  Explore the Meta
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="/decks/new">Build a Deck</Link>
              </Button>
            </div>

            {/* Stats bar */}
            <div className="mt-12 flex flex-wrap gap-6 border-t border-slate-200 pt-6">
              <StatItem
                icon={<TrendingUp className="h-5 w-5" />}
                value="47"
                label="tournaments this week"
              />
              <StatItem
                icon={<Users className="h-5 w-5" />}
                value="12k+"
                label="decklists analyzed"
              />
              <StatItem
                icon={<Calendar className="h-5 w-5" />}
                value="3"
                label="major events upcoming"
              />
            </div>
          </div>

          {/* Card fan visual */}
          <div className="relative hidden lg:block">
            <div className="relative mx-auto h-[400px] w-[300px]">
              {/* Card placeholders - will be replaced with actual card images */}
              <div className="absolute left-1/2 top-1/2 h-[280px] w-[200px] -translate-x-1/2 -translate-y-1/2 -rotate-12 transform rounded-xl bg-gradient-to-br from-blue-400 to-blue-600 shadow-xl transition-transform motion-safe:hover:-translate-y-3" />
              <div className="absolute left-1/2 top-1/2 h-[280px] w-[200px] -translate-x-1/2 -translate-y-1/2 rotate-0 transform rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-xl transition-transform motion-safe:hover:-translate-y-3" />
              <div className="absolute left-1/2 top-1/2 h-[280px] w-[200px] -translate-x-1/2 -translate-y-1/2 rotate-12 transform rounded-xl bg-gradient-to-br from-rose-400 to-rose-600 shadow-xl transition-transform motion-safe:hover:-translate-y-3" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
