import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "My Decks | TrainerLab",
  description:
    "Manage your Pokemon TCG deck collection. Create, edit, and export decks for competitive play.",
  openGraph: {
    title: "My Decks | TrainerLab",
    description:
      "Manage your Pokemon TCG deck collection. Create, edit, and export decks for competitive play.",
  },
};

export default function DecksLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
