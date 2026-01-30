"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useCard } from "@/hooks/useCards";
import { CardDetail } from "@/components/cards";
import { Button } from "@/components/ui/button";

interface CardDetailClientProps {
  id: string;
}

function CardDetailSkeleton() {
  return (
    <div className="flex flex-col md:flex-row gap-8 animate-pulse">
      <div
        className="bg-muted rounded-lg flex-shrink-0 mx-auto md:mx-0"
        style={{ width: 320, height: 448 }}
      />
      <div className="flex-1 space-y-4">
        <div className="h-8 bg-muted rounded w-1/2" />
        <div className="h-4 bg-muted rounded w-1/3" />
        <div className="flex gap-2">
          <div className="h-6 bg-muted rounded w-20" />
          <div className="h-6 bg-muted rounded w-20" />
        </div>
        <div className="h-24 bg-muted rounded" />
        <div className="h-24 bg-muted rounded" />
      </div>
    </div>
  );
}

export function CardDetailClient({ id }: CardDetailClientProps) {
  const { data: card, isLoading, isError, error } = useCard(id);

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Back Button */}
      <Button variant="ghost" asChild className="mb-6">
        <Link href="/cards">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Cards
        </Link>
      </Button>

      {/* Loading State */}
      {isLoading && <CardDetailSkeleton />}

      {/* Error State */}
      {isError && (
        <div className="text-center py-12">
          <p className="text-destructive font-medium text-lg">
            Error loading card
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            {error instanceof Error ? error.message : "Card not found"}
          </p>
          <Button asChild className="mt-4">
            <Link href="/cards">Back to Cards</Link>
          </Button>
        </div>
      )}

      {/* Card Detail */}
      {card && !isLoading && <CardDetail card={card} />}
    </div>
  );
}
