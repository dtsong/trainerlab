import type { Metadata } from "next";

import { EvolutionLayoutClient } from "./layout-client";

export const metadata: Metadata = {
  title: "Deck Evolution | TrainerLab",
  description:
    "Track how top Pokemon TCG archetypes evolve over time. Adaptation analysis, meta share trends, and competitive predictions.",
  openGraph: {
    title: "Deck Evolution | TrainerLab",
    description:
      "Track how top Pokemon TCG archetypes evolve over time. Adaptation analysis, meta share trends, and competitive predictions.",
    images: [{ url: "/api/og/meta.png" }],
  },
};

export default function EvolutionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <EvolutionLayoutClient>{children}</EvolutionLayoutClient>;
}
