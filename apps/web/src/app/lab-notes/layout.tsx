import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Lab Notes | TrainerLab",
  description:
    "Analysis, reports, and competitive insights from the TrainerLab research desk.",
  openGraph: {
    title: "Lab Notes | TrainerLab",
    description:
      "Analysis, reports, and competitive insights from the TrainerLab research desk.",
    images: [{ url: "/api/og/meta.png" }],
  },
};

export default function LabNotesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
