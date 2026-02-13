import type { Metadata } from "next";

import { CardDossierClient } from "./CardDossierClient";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CardDossierPageProps {
  params: Promise<{ cardId: string }>;
}

export async function generateMetadata({
  params,
}: CardDossierPageProps): Promise<Metadata> {
  const { cardId } = await params;

  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/cards/${encodeURIComponent(cardId)}`,
      { next: { revalidate: 3600 } }
    );
    if (!res.ok) {
      return {
        title: "Card Dossier | TrainerLab",
        description: "Investigate a Pokemon TCG card on TrainerLab.",
      };
    }

    const card = await res.json();
    const title = `${card.name} Dossier | TrainerLab`;
    const description = `Investigate ${card.name} with meta context and clean links.`;

    return {
      title,
      description,
      openGraph: {
        title,
        description,
        images: card.image_large ? [{ url: card.image_large }] : undefined,
      },
    };
  } catch {
    return {
      title: "Card Dossier | TrainerLab",
      description: "Investigate a Pokemon TCG card on TrainerLab.",
    };
  }
}

export default async function CardDossierPage({
  params,
}: CardDossierPageProps) {
  const { cardId } = await params;
  return <CardDossierClient cardId={cardId} />;
}
