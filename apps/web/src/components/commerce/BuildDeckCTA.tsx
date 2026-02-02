"use client";

import { DollarSign, ExternalLink, ShoppingCart } from "lucide-react";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  estimateDeckPrice,
  getDoubleHoloLink,
  getTCGPlayerLink,
} from "@/lib/affiliate";
import { trackAffiliateClick, trackBuildDeckCTA } from "@/lib/analytics";

interface BuildDeckCTAProps {
  deckName: string;
  deckId?: string;
  cardCount?: number;
  className?: string;
}

export function BuildDeckCTA({
  deckName,
  deckId,
  cardCount = 60,
  className,
}: BuildDeckCTAProps) {
  const doubleHoloLink = getDoubleHoloLink(deckName, deckId);
  const tcgPlayerLink = getTCGPlayerLink(deckName, deckId);
  const priceEstimate = estimateDeckPrice(cardCount);

  useEffect(() => {
    trackBuildDeckCTA("view", deckName);
  }, [deckName]);

  const handleDoubleHoloClick = () => {
    trackAffiliateClick("doubleHolo", "deck", deckId);
    trackBuildDeckCTA("click_primary", deckName);
  };

  const handleTCGPlayerClick = () => {
    trackAffiliateClick("tcgPlayer", "deck", deckId);
    trackBuildDeckCTA("click_secondary", deckName);
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-lg">
          <ShoppingCart className="h-5 w-5" />
          Build This Deck
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Price Estimate */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <DollarSign className="h-4 w-4" />
          <span>
            Estimated: ${priceEstimate.low} - ${priceEstimate.high}
          </span>
        </div>

        {/* Primary CTA - DoubleHolo */}
        <a
          href={doubleHoloLink}
          target="_blank"
          rel="noopener noreferrer"
          onClick={handleDoubleHoloClick}
          className="block"
        >
          <Button className="w-full" size="lg">
            <ExternalLink className="h-4 w-4 mr-2" />
            Buy on DoubleHolo
          </Button>
        </a>

        {/* Secondary CTA - TCGPlayer */}
        <a
          href={tcgPlayerLink}
          target="_blank"
          rel="noopener noreferrer"
          onClick={handleTCGPlayerClick}
          className="block"
        >
          <Button variant="outline" className="w-full">
            <ExternalLink className="h-4 w-4 mr-2" />
            View on TCGPlayer
          </Button>
        </a>

        <p className="text-xs text-muted-foreground text-center">
          Prices are estimates. TrainerLab may earn a commission from purchases.
        </p>
      </CardContent>
    </Card>
  );
}
