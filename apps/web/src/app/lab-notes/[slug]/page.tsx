import type { Metadata } from "next";

import { LabNotePageClient } from "./LabNotePageClient";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface LabNotePageProps {
  params: Promise<{ slug: string }>;
}

function humanizeSlug(slug: string): string {
  return slug
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export async function generateMetadata({
  params,
}: LabNotePageProps): Promise<Metadata> {
  const { slug } = await params;

  const fallbackTitle = `${humanizeSlug(slug)} | Lab Notes | TrainerLab`;
  const fallbackDescription =
    "Read strategic Pokemon TCG research from TrainerLab Lab Notes.";

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/lab-notes/${encodeURIComponent(slug)}`,
      { next: { revalidate: 900 } }
    );

    if (!response.ok) {
      return {
        title: fallbackTitle,
        description: fallbackDescription,
        openGraph: {
          title: fallbackTitle,
          description: fallbackDescription,
          images: [
            { url: `/api/og/lab-notes/${encodeURIComponent(slug)}.png` },
          ],
        },
      };
    }

    const note = await response.json();
    const title = `${note.title} | TrainerLab`;
    const description =
      note.summary ||
      "Read strategic Pokemon TCG research from TrainerLab Lab Notes.";

    return {
      title,
      description,
      openGraph: {
        title,
        description,
        images: [{ url: `/api/og/lab-notes/${encodeURIComponent(slug)}.png` }],
      },
    };
  } catch {
    return {
      title: fallbackTitle,
      description: fallbackDescription,
      openGraph: {
        title: fallbackTitle,
        description: fallbackDescription,
        images: [{ url: `/api/og/lab-notes/${encodeURIComponent(slug)}.png` }],
      },
    };
  }
}

export default async function LabNotePage({ params }: LabNotePageProps) {
  const { slug } = await params;
  return <LabNotePageClient slug={slug} />;
}
