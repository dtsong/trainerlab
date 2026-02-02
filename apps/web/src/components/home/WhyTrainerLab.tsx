"use client";

import { BarChart3, Globe, Layers, Star } from "lucide-react";
import { SectionLabel } from "@/components/ui/section-label";

interface ValuePropProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}

function ValueProp({ icon, title, description }: ValuePropProps) {
  return (
    <div className="text-center">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-teal-50 text-teal-600">
        {icon}
      </div>
      <h3 className="font-display text-lg font-semibold text-slate-900">
        {title}
      </h3>
      <p className="mt-2 text-slate-600">{description}</p>
    </div>
  );
}

const valueProps: ValuePropProps[] = [
  {
    icon: <BarChart3 className="h-6 w-6" />,
    title: "Data-Driven",
    description:
      "Real tournament results, not theory. We analyze thousands of decklists weekly to show you what's actually winning.",
  },
  {
    icon: <Globe className="h-6 w-6" />,
    title: "Japan Insights",
    description:
      "Stay ahead of the meta. Japan plays with future cards—see what's coming before it hits your region.",
  },
  {
    icon: <Layers className="h-6 w-6" />,
    title: "All-in-One",
    description:
      "Meta analysis, deck building, and card database in one place. No more jumping between 5 different sites.",
  },
];

export function WhyTrainerLab() {
  return (
    <section className="py-12 md:py-16">
      <div className="container">
        <SectionLabel
          label="Why TrainerLab"
          icon={<Star className="h-4 w-4" />}
          className="mb-8 justify-center"
        />

        <div className="mx-auto max-w-4xl">
          <div className="grid gap-8 md:grid-cols-3">
            {valueProps.map((prop, index) => (
              <ValueProp key={index} {...prop} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
