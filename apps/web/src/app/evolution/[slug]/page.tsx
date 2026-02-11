import type { Metadata } from "next";

import { EvolutionArticlePageClient } from "./EvolutionArticlePageClient";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface EvolutionArticlePageProps {
  params: Promise<{ slug: string }>;
}

function humanizeSlug(slug: string): string {
  return slug
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export async function generateMetadata({
  params,
}: EvolutionArticlePageProps): Promise<Metadata> {
  const { slug } = await params;

  const fallbackTitle = `${humanizeSlug(slug)} | Evolution | TrainerLab`;
  const fallbackDescription =
    "Track archetype evolution and prediction insights for competitive Pokemon TCG.";

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/evolution/${encodeURIComponent(slug)}`,
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
            { url: `/api/og/evolution/${encodeURIComponent(slug)}.png` },
          ],
        },
      };
    }

    const article = await response.json();
    const title = `${article.title} | TrainerLab`;
    const description =
      article.excerpt ||
      "Track archetype evolution and prediction insights for competitive Pokemon TCG.";

    return {
      title,
      description,
      openGraph: {
        title,
        description,
        images: [{ url: `/api/og/evolution/${encodeURIComponent(slug)}.png` }],
      },
    };
  } catch {
    return {
      title: fallbackTitle,
      description: fallbackDescription,
      openGraph: {
        title: fallbackTitle,
        description: fallbackDescription,
        images: [{ url: `/api/og/evolution/${encodeURIComponent(slug)}.png` }],
      },
    };
  }
}

export default async function EvolutionArticlePage({
  params,
}: EvolutionArticlePageProps) {
  const { slug } = await params;
  return <EvolutionArticlePageClient slug={slug} />;
}
