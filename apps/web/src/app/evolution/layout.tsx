import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Deck Evolution | TrainerLab",
  description:
    "Track how top Pokemon TCG archetypes evolve over time. Adaptation analysis, meta share trends, and competitive predictions.",
};

export default function EvolutionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
