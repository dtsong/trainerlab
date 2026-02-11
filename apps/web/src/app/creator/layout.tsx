import type { Metadata } from "next";

import { CreatorGuard } from "@/components/creator";

export const metadata: Metadata = {
  title: "Creator Workspace | TrainerLab",
  description:
    "Build embeddable widgets, generate exports, and manage API access for your TrainerLab creator workflow.",
  openGraph: {
    title: "Creator Workspace | TrainerLab",
    description:
      "Build embeddable widgets, generate exports, and manage API access for your TrainerLab creator workflow.",
    images: [{ url: "/api/og/meta.png" }],
  },
};

export default function CreatorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="container mx-auto px-4 py-8">
      <CreatorGuard>{children}</CreatorGuard>
    </div>
  );
}
