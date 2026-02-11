import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Card Database | TrainerLab",
  description:
    "Browse and search the complete Pokemon TCG card database. Filter by type, set, format legality, and more.",
  openGraph: {
    title: "Card Database | TrainerLab",
    description:
      "Browse and search the complete Pokemon TCG card database. Filter by type, set, format legality, and more.",
    images: [{ url: "/api/og/meta.png" }],
  },
};

export default function CardsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
