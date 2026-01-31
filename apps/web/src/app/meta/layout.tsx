import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Meta Dashboard | TrainerLab",
  description:
    "Explore the current Pokemon TCG competitive meta, archetype breakdowns, and card usage statistics.",
};

export default function MetaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8">{children}</main>
    </div>
  );
}
