"use client";

import { BarChart3, Globe, Layers, Star } from "lucide-react";
import { SectionLabel } from "@/components/ui/section-label";

interface ValuePropProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  annotation?: string;
}

function ValueProp({ icon, title, description, annotation }: ValuePropProps) {
  return (
    <div className="relative group">
      {/* Hand-drawn circle effect around icon */}
      <div className="relative mx-auto mb-4 w-14 h-14">
        {/* SVG hand-drawn circle */}
        <svg
          className="absolute inset-0 w-full h-full text-ink-red/20 group-hover:text-ink-red/40 transition-colors"
          viewBox="0 0 56 56"
        >
          <ellipse
            cx="28"
            cy="28"
            rx="24"
            ry="25"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeDasharray="4 2"
            transform="rotate(-3 28 28)"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center text-ink-red">
          {icon}
        </div>
      </div>

      <h3 className="font-display text-lg font-semibold text-ink-black text-center">
        {title}
      </h3>
      <p className="mt-2 text-pencil text-center leading-relaxed">
        {description}
      </p>

      {/* Margin annotation - appears on hover */}
      {annotation && (
        <div className="absolute -right-4 top-0 opacity-0 group-hover:opacity-100 transition-opacity hidden lg:block">
          <div className="bg-notebook-cream border border-notebook-grid px-2 py-1 rounded-sm shadow-sm -rotate-3">
            <span className="font-mono text-xs text-ink-red whitespace-nowrap">
              {annotation}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

const valueProps: ValuePropProps[] = [
  {
    icon: <BarChart3 className="h-6 w-6" />,
    title: "Data-Driven",
    description:
      "Real tournament results, not theory. We analyze thousands of decklists weekly to show you what's actually winning.",
    annotation: "12k+ decklists",
  },
  {
    icon: <Globe className="h-6 w-6" />,
    title: "Japan Insights",
    description:
      "Stay ahead of the meta. Japan plays with future cards—see what's coming before it hits your region.",
    annotation: "2-3 months ahead",
  },
  {
    icon: <Layers className="h-6 w-6" />,
    title: "All-in-One",
    description:
      "Meta analysis, deck building, and card database in one place. No more jumping between 5 different sites.",
    annotation: "Everything you need",
  },
];

export function WhyTrainerLab() {
  return (
    <section className="relative py-12 md:py-16 bg-notebook-cream">
      {/* Dot grid background */}
      <div className="absolute inset-0 bg-dot-grid opacity-50" />

      {/* Paper texture */}
      <div className="absolute inset-0 bg-paper-texture" />

      {/* Red margin line */}
      <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-ink-red/20 hidden lg:block" />

      <div className="container relative">
        <div className="lg:pl-8">
          <SectionLabel
            label="Why TrainerLab"
            icon={<Star className="h-4 w-4" />}
            variant="notebook"
            className="mb-8 justify-center lg:justify-start"
          />

          {/* Section annotation */}
          <p className="font-mono text-xs text-pencil italic mb-8 text-center lg:text-left">
            Your competitive edge in Pokemon TCG research
          </p>
        </div>

        {/* Value props grid - removed max-w constraint */}
        <div className="grid gap-10 md:grid-cols-3 lg:pl-8">
          {valueProps.map((prop, index) => (
            <ValueProp key={index} {...prop} />
          ))}
        </div>

        {/* Bottom decoration - notebook binding holes */}
        <div className="mt-12 flex justify-center gap-8 lg:pl-8">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="w-3 h-3 rounded-full border-2 border-notebook-grid bg-notebook-cream"
            />
          ))}
        </div>
      </div>
    </section>
  );
}
