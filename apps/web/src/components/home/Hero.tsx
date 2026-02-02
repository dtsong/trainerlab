"use client";

import Link from "next/link";
import { ArrowRight, TrendingUp, Users, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ShufflingDeck } from "./ShufflingDeck";

interface StatItemProps {
  icon: React.ReactNode;
  value: string;
  label: string;
  delay?: string;
}

function StatItem({ icon, value, label, delay = "0s" }: StatItemProps) {
  return (
    <div
      className="flex items-center gap-3 rounded-sm bg-notebook-aged/60 px-3 py-2 shadow-sm opacity-0 animate-fade-in-up"
      style={{ animationDelay: delay }}
    >
      <div className="text-pencil">{icon}</div>
      <div className="flex items-baseline gap-1.5">
        <span className="font-mono text-lg font-bold text-ink-red">
          {value}
        </span>
        <span className="font-mono text-xs uppercase tracking-wide text-pencil">
          {label}
        </span>
      </div>
    </div>
  );
}

function ResearchCard({
  className,
  color,
  label,
  animationStyle,
}: {
  className?: string;
  color: string;
  label: string;
  animationStyle?: React.CSSProperties;
}) {
  return (
    <div
      className={`relative motion-safe:animate-sway-pinned ${className}`}
      style={animationStyle}
    >
      {/* Tape effect at top - with subtle wiggle */}
      <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-10 h-4 bg-gradient-to-b from-amber-100/80 to-amber-200/60 rounded-sm shadow-sm z-10 motion-safe:animate-tape-wiggle" />

      {/* Card with shuffle animation */}
      <div
        className={`h-[280px] w-[200px] rounded-lg shadow-lg transition-all duration-300 motion-safe:hover:-translate-y-2 motion-safe:hover:shadow-xl ${color}`}
      />

      {/* Label strip at bottom */}
      <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 bg-notebook-cream border border-notebook-grid px-3 py-1 rounded-sm shadow-sm">
        <span className="font-mono text-xs uppercase tracking-wide text-pencil whitespace-nowrap">
          {label}
        </span>
      </div>
    </div>
  );
}

function FloatingCard({
  className,
  delay,
  shuffleX,
}: {
  className?: string;
  delay?: string;
  shuffleX?: string;
}) {
  return (
    <div
      className={`absolute w-16 h-24 rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 border border-notebook-grid shadow-md motion-safe:animate-shuffle-peek ${className}`}
      style={
        {
          animationDelay: delay,
          "--shuffle-x": shuffleX,
        } as React.CSSProperties
      }
    />
  );
}

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-notebook-cream py-16 md:py-24">
      {/* Dot grid background */}
      <div className="absolute inset-0 bg-dot-grid opacity-60" />

      {/* Subtle paper texture overlay */}
      <div className="absolute inset-0 bg-paper-texture" />

      {/* Red margin line accent */}
      <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-ink-red/20 hidden lg:block" />

      {/* Ambient floating cards in background - very subtle */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none hidden lg:block">
        <FloatingCard
          className="top-[15%] left-[8%] rotate-12 opacity-20"
          delay="0s"
          shuffleX="8px"
        />
        <FloatingCard
          className="top-[60%] left-[5%] -rotate-6 opacity-15"
          delay="4s"
          shuffleX="-6px"
        />
        <FloatingCard
          className="bottom-[20%] right-[8%] rotate-[-15deg] opacity-20"
          delay="8s"
          shuffleX="10px"
        />
      </div>

      <div className="container relative">
        <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
          {/* Text content */}
          <div className="max-w-xl lg:pl-8">
            {/* Handwritten-style label */}
            <div className="mb-4 inline-flex items-center gap-2 rounded-sm bg-notebook-aged/80 px-3 py-1.5 border border-notebook-grid opacity-0 animate-fade-in-up">
              <div className="h-2 w-2 rounded-full bg-ink-red animate-pulse" />
              <span className="font-mono text-xs uppercase tracking-widest text-pencil">
                Research Lab Active
              </span>
            </div>

            <h1
              className="font-display text-4xl font-bold tracking-tight text-ink-black md:text-5xl lg:text-6xl opacity-0 animate-fade-in-up"
              style={{ animationDelay: "0.1s" }}
            >
              Data-Driven
              <br />
              <span className="relative inline-block text-ink-red">
                Deck Building
                {/* Animated underline annotation */}
                <svg
                  className="absolute -bottom-2 left-0 w-full h-3 text-ink-red/30"
                  viewBox="0 0 200 12"
                  preserveAspectRatio="none"
                >
                  <path
                    d="M0,8 Q50,2 100,8 T200,8"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    className="animate-draw-underline"
                  />
                </svg>
              </span>
            </h1>
            <p
              className="mt-8 text-lg text-pencil leading-relaxed opacity-0 animate-fade-in-up"
              style={{ animationDelay: "0.2s" }}
            >
              Your competitive research lab for Pokemon TCG. Real-time meta
              analysis, Japan format preview, and smart deck building tools
              trusted by competitive players.
            </p>
            <div
              className="mt-8 flex flex-wrap gap-4 opacity-0 animate-fade-in-up"
              style={{ animationDelay: "0.3s" }}
            >
              <Button
                asChild
                size="lg"
                className="bg-ink-black hover:bg-ink-black/90 text-notebook-cream font-mono uppercase tracking-wide"
              >
                <Link href="/meta">
                  Explore the Meta
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                size="lg"
                className="border-ink-black/30 text-ink-black hover:bg-notebook-aged font-mono uppercase tracking-wide"
              >
                <Link href="/decks/new">Build a Deck</Link>
              </Button>
            </div>

            {/* Stats bar - styled as typewritten labels */}
            <div className="mt-12 flex flex-wrap gap-3 border-t-2 border-dashed border-notebook-grid pt-6">
              <StatItem
                icon={<TrendingUp className="h-4 w-4" />}
                value="47"
                label="tournaments this week"
                delay="0.5s"
              />
              <StatItem
                icon={<Users className="h-4 w-4" />}
                value="12k+"
                label="decklists analyzed"
                delay="0.6s"
              />
              <StatItem
                icon={<Calendar className="h-4 w-4" />}
                value="3"
                label="major events upcoming"
                delay="0.7s"
              />
            </div>
          </div>

          {/* Card fan visual - styled as pinned research specimens */}
          <div className="relative hidden lg:block">
            <div className="relative mx-auto h-[450px] w-[350px]">
              {/* Background corkboard texture hint */}
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-amber-100/40 to-orange-50/30 border border-notebook-grid" />

              {/* Research cards with sway and shuffle animations */}
              <ResearchCard
                className="absolute left-1/2 top-1/2 -translate-x-[70%] -translate-y-1/2"
                color="bg-gradient-to-br from-blue-400 to-blue-600"
                label="Water Type"
                animationStyle={
                  {
                    "--sway-base": "-12deg",
                    animationDelay: "0s",
                  } as React.CSSProperties
                }
              />
              <ResearchCard
                className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
                color="bg-gradient-to-br from-amber-400 to-amber-600"
                label="Lightning"
                animationStyle={
                  {
                    "--sway-base": "0deg",
                    animationDelay: "2.5s",
                  } as React.CSSProperties
                }
              />
              <ResearchCard
                className="absolute left-1/2 top-1/2 -translate-x-[30%] -translate-y-1/2"
                color="bg-gradient-to-br from-rose-400 to-rose-600"
                label="Fire Type"
                animationStyle={
                  {
                    "--sway-base": "12deg",
                    animationDelay: "5s",
                  } as React.CSSProperties
                }
              />

              {/* Corner annotation with paper rustle */}
              <div
                className="absolute bottom-4 right-4 motion-safe:animate-paper-rustle"
                style={{ "--rustle-base": "3deg" } as React.CSSProperties}
              >
                <div className="bg-notebook-cream border border-notebook-grid px-3 py-2 rounded-sm shadow-sm">
                  <span className="font-mono text-xs text-pencil">
                    Specimen Collection
                  </span>
                  <br />
                  <span className="font-mono text-xs text-ink-red">
                    Updated Daily
                  </span>
                </div>
              </div>

              {/* Shuffling deck in corner */}
              <div className="absolute bottom-8 left-4">
                <ShufflingDeck />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
