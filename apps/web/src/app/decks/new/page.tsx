"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DeckBuilder } from "@/components/deck";
import { useDeckStore } from "@/stores/deckStore";
import { useDecks } from "@/hooks/useDecks";
import type { DeckState } from "@/types/deck";

export default function NewDeckPage() {
  const router = useRouter();
  const [isSaving, setIsSaving] = useState(false);

  const clearDeck = useDeckStore((state) => state.clearDeck);
  const resetModified = useDeckStore((state) => state.resetModified);
  const isModified = useDeckStore((state) => state.isModified);

  const { createDeck } = useDecks();

  // Clear the deck store when mounting a new deck page
  useEffect(() => {
    clearDeck();
    resetModified();
  }, [clearDeck, resetModified]);

  const handleSave = useCallback(
    async (deck: Omit<DeckState, "isModified">) => {
      setIsSaving(true);

      const result = createDeck({
        name: deck.name || "Untitled Deck",
        description: deck.description,
        format: deck.format,
        cards: deck.cards,
      });

      if (!result.saved) {
        alert(
          "Could not save deck. Your browser storage may be full or unavailable.",
        );
        setIsSaving(false);
        return;
      }

      resetModified();
      router.push(`/decks/${result.deck.id}`);
    },
    [createDeck, resetModified, router],
  );

  const handleBack = useCallback(() => {
    if (isModified) {
      const confirmed = window.confirm(
        "You have unsaved changes. Are you sure you want to leave?",
      );
      if (!confirmed) return;
    }
    router.push("/decks");
  }, [isModified, router]);

  return (
    <div className="flex flex-col h-screen">
      {/* Page header */}
      <header className="flex items-center gap-4 p-4 border-b bg-background">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleBack}
          aria-label="Go back"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-lg font-semibold">Create New Deck</h1>
          <p className="text-sm text-muted-foreground">
            Build your deck by searching and adding cards
          </p>
        </div>
      </header>

      {/* Deck builder */}
      <div className="flex-1 overflow-hidden">
        <DeckBuilder onSave={handleSave} isSaving={isSaving} />
      </div>
    </div>
  );
}
