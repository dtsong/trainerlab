"use client";

import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface BuildItBannerProps {
  selectedArchetype?: string;
  topDeckName?: string;
  className?: string;
}

export function BuildItBanner({
  selectedArchetype,
  topDeckName = "the top deck",
  className,
}: BuildItBannerProps) {
  const deckName = selectedArchetype || topDeckName;
  const deckParam = selectedArchetype
    ? encodeURIComponent(selectedArchetype)
    : "";

  return (
    <div
      className={cn(
        "rounded-lg bg-gradient-to-r from-teal-600 to-teal-500 px-6 py-4",
        className,
      )}
    >
      <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
        <div>
          <h3 className="font-display text-xl font-semibold text-white">
            Build {deckName}
          </h3>
          <p className="text-sm text-teal-100">
            Get the cards you need from our partner stores
          </p>
        </div>

        <div className="flex gap-3">
          {/* Primary: TCGPlayer (for now, placeholder for DoubleHolo) */}
          <Button asChild className="bg-white text-teal-700 hover:bg-teal-50">
            <Link
              href={`/decks/new${deckParam ? `?archetype=${deckParam}` : ""}`}
            >
              Build Deck
              <ExternalLink className="ml-2 h-4 w-4" />
            </Link>
          </Button>

          {/* Secondary: TCGPlayer */}
          <Button
            asChild
            variant="outline"
            className="border-white/30 text-white hover:bg-white/10"
          >
            <a
              href="https://www.tcgplayer.com/search/pokemon-product/product"
              target="_blank"
              rel="noopener noreferrer"
            >
              TCGPlayer
              <ExternalLink className="ml-2 h-4 w-4" />
            </a>
          </Button>
        </div>
      </div>
    </div>
  );
}
