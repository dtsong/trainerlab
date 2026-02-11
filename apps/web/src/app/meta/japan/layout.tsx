import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "From Japan | TrainerLab",
  description:
    "Post-rotation Japan BO1 intelligence, archetype divergence, and tech card scouting.",
  openGraph: {
    title: "From Japan | TrainerLab",
    description:
      "Post-rotation Japan BO1 intelligence, archetype divergence, and tech card scouting.",
    images: [{ url: "/api/og/meta.png" }],
  },
};

export default function JapanMetaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
