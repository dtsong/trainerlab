"use client";

import { useState, useCallback } from "react";
import Image from "next/image";
import { Save, Loader2, ImageOff } from "lucide-react";
import { useDeckStore } from "@/stores/deckStore";
import { cardsApi, type CardSearchParams } from "@/lib/api";
import { DeckList } from "./DeckList";
import { DeckStats } from "./DeckStats";
import { DeckValidation } from "./DeckValidation";
import { CardSearchInput } from "@/components/cards/CardSearchInput";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { ApiCardSummary } from "@trainerlab/shared-types";

interface DeckBuilderProps {
  className?: string;
}

const THUMBNAIL_SIZE = { width: 80, height: 112 };

interface SearchResultCardProps {
  card: ApiCardSummary;
  onClick: (card: ApiCardSummary) => void;
}

function SearchResultCard({ card, onClick }: SearchResultCardProps) {
  const [imageError, setImageError] = useState(false);

  return (
    <button
      type="button"
      onClick={() => onClick(card)}
      className="group flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-accent transition-colors"
    >
      <div
        className="relative rounded overflow-hidden bg-muted"
        style={THUMBNAIL_SIZE}
      >
        {card.image_small && !imageError ? (
          <Image
            src={card.image_small}
            alt={card.name}
            width={THUMBNAIL_SIZE.width}
            height={THUMBNAIL_SIZE.height}
            className="object-cover group-hover:scale-105 transition-transform"
            onError={() => setImageError(true)}
            unoptimized
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <ImageOff className="w-6 h-6 text-muted-foreground" />
          </div>
        )}
      </div>
      <span className="text-xs font-medium truncate max-w-[80px]">
        {card.name}
      </span>
    </button>
  );
}

export function DeckBuilder({ className }: DeckBuilderProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<ApiCardSummary[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const name = useDeckStore((state) => state.name);
  const isModified = useDeckStore((state) => state.isModified);
  const addCard = useDeckStore((state) => state.addCard);
  const setName = useDeckStore((state) => state.setName);

  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query);

    if (!query.trim()) {
      setSearchResults([]);
      setSearchError(null);
      return;
    }

    setIsSearching(true);
    setSearchError(null);

    try {
      const params: CardSearchParams = {
        q: query,
        limit: 20,
      };

      const response = await cardsApi.search(params);
      setSearchResults(response.items);
    } catch (error) {
      console.error("Search failed:", error);
      setSearchError("Failed to search cards. Please try again.");
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleAddCard = useCallback(
    (card: ApiCardSummary) => {
      addCard(card);
    },
    [addCard],
  );

  const handleSave = useCallback(() => {
    // TODO: Implement save to backend
    console.log("Save deck:", useDeckStore.getState());
    alert("Save functionality coming soon!");
  }, []);

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header with deck name and save */}
      <header className="flex items-center gap-4 p-4 border-b">
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Deck name..."
          className="flex-1 max-w-xs"
        />
        <Button onClick={handleSave} disabled={!isModified} className="gap-2">
          <Save className="h-4 w-4" />
          Save
        </Button>
      </header>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel - Card search */}
        <div className="w-1/2 lg:w-2/3 flex flex-col border-r">
          {/* Search input */}
          <div className="p-4 border-b">
            <CardSearchInput
              value={searchQuery}
              onChange={handleSearch}
              placeholder="Search cards to add..."
            />
          </div>

          {/* Search results */}
          <div className="flex-1 overflow-y-auto p-4">
            {isSearching && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            )}

            {searchError && (
              <div className="text-center py-8 text-destructive">
                {searchError}
              </div>
            )}

            {!isSearching && !searchError && searchResults.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                {searchQuery
                  ? "No cards found"
                  : "Search for cards to add to your deck"}
              </div>
            )}

            {!isSearching && searchResults.length > 0 && (
              <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8 gap-2">
                {searchResults.map((card) => (
                  <SearchResultCard
                    key={card.id}
                    card={card}
                    onClick={handleAddCard}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right panel - Deck list */}
        <div className="w-1/2 lg:w-1/3 flex flex-col">
          {/* Stats header */}
          <div className="p-4 border-b">
            <DeckStats />
          </div>

          {/* Deck list */}
          <div className="flex-1 overflow-y-auto p-4">
            <DeckList />
          </div>

          {/* Validation footer */}
          <div className="p-4 border-t">
            <DeckValidation />
          </div>
        </div>
      </div>
    </div>
  );
}
