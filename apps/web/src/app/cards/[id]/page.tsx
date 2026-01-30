import type { Metadata } from "next";
import { CardDetailClient } from "./CardDetailClient";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CardDetailPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({
  params,
}: CardDetailPageProps): Promise<Metadata> {
  const { id } = await params;

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/cards/${encodeURIComponent(id)}`,
      { next: { revalidate: 3600 } }, // Cache for 1 hour
    );

    if (!response.ok) {
      return {
        title: "Card Not Found | TrainerLab",
        description: "The requested Pokemon TCG card could not be found.",
      };
    }

    const card = await response.json();
    const title = `${card.name} | TrainerLab`;
    const description = `View ${card.name} from ${card.set?.name || card.set_id}. ${card.supertype}${card.types?.length ? ` - ${card.types.join("/")}` : ""}${card.hp ? ` - ${card.hp} HP` : ""}.`;

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
      title: "Card | TrainerLab",
      description: "View Pokemon TCG card details on TrainerLab.",
    };
  }
}

export default async function CardDetailPage({ params }: CardDetailPageProps) {
  const { id } = await params;
  return <CardDetailClient id={id} />;
}
