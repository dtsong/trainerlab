"use client";

import { useState, useCallback, useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  Check,
  Edit,
  Eye,
  Trash2,
  Download,
  Share2,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DeckBuilder, DeckExportModal } from "@/components/deck";
import { DeckListReadOnly } from "./DeckListReadOnly";
import { useDeckStore } from "@/stores/deckStore";
import { useDecks } from "@/hooks/useDecks";
import type { DeckState } from "@/types/deck";

export default function DeckDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();

  const deckId = params.id as string;
  const initialEditMode = searchParams.get("edit") === "true";

  const [isEditMode, setIsEditMode] = useState(initialEditMode);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const { getDeck, updateDeck, deleteDeck, isLoading } = useDecks();
  const deck = getDeck(deckId);

  const loadDeck = useDeckStore((state) => state.loadDeck);
  const resetModified = useDeckStore((state) => state.resetModified);
  const isModified = useDeckStore((state) => state.isModified);

  // Load deck into store when entering edit mode
  useEffect(() => {
    if (deck && isEditMode) {
      loadDeck({
        cards: deck.cards,
        name: deck.name,
        description: deck.description,
        format: deck.format,
      });
    }
  }, [deck, isEditMode, loadDeck]);

  const handleSave = useCallback(
    async (deckData: Omit<DeckState, "isModified">) => {
      setIsSaving(true);

      const result = updateDeck(deckId, {
        name: deckData.name || "Untitled Deck",
        description: deckData.description,
        format: deckData.format,
        cards: deckData.cards,
      });

      if (!result.deck) {
        alert("Could not save deck. It may have been deleted.");
        setIsSaving(false);
        return;
      }

      if (!result.saved) {
        alert(
          "Could not save deck. Your browser storage may be full or unavailable.",
        );
        setIsSaving(false);
        return;
      }

      resetModified();
      setIsEditMode(false);
      setIsSaving(false);
    },
    [deckId, updateDeck, resetModified],
  );

  const handleDelete = useCallback(async () => {
    setIsDeleting(true);

    const result = deleteDeck(deckId);

    if (!result.found) {
      alert("Could not delete deck. It may have already been deleted.");
      setIsDeleting(false);
      setShowDeleteConfirm(false);
      return;
    }

    if (!result.saved) {
      alert("Could not delete deck. Your browser storage may be unavailable.");
      setIsDeleting(false);
      return;
    }

    router.push("/decks");
  }, [deckId, deleteDeck, router]);

  const handleToggleEdit = useCallback(() => {
    if (isEditMode && isModified) {
      const confirmed = window.confirm(
        "You have unsaved changes. Discard them?",
      );
      if (!confirmed) return;
    }

    if (!isEditMode && deck) {
      // Entering edit mode - load deck
      loadDeck({
        cards: deck.cards,
        name: deck.name,
        description: deck.description,
        format: deck.format,
      });
    }

    setIsEditMode(!isEditMode);
  }, [isEditMode, isModified, deck, loadDeck]);

  const handleBack = useCallback(() => {
    if (isEditMode && isModified) {
      const confirmed = window.confirm(
        "You have unsaved changes. Are you sure you want to leave?",
      );
      if (!confirmed) return;
    }
    router.push("/decks");
  }, [isEditMode, isModified, router]);

  const [linkCopied, setLinkCopied] = useState(false);

  const handleShare = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy link:", error);
      alert(
        "Could not copy link. Please copy the URL from your browser's address bar.",
      );
    }
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Not found state
  if (!deck) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <h1 className="text-2xl font-bold">Deck not found</h1>
        <p className="text-muted-foreground">
          This deck may have been deleted or doesn&apos;t exist.
        </p>
        <Button onClick={() => router.push("/decks")}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Decks
        </Button>
      </div>
    );
  }

  const totalCards = deck.cards.reduce((sum, c) => sum + c.quantity, 0);

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

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-semibold truncate">{deck.name}</h1>
            <Badge variant={deck.format === "standard" ? "default" : "outline"}>
              {deck.format === "standard" ? "Standard" : "Expanded"}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {totalCards} card{totalCards !== 1 ? "s" : ""}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {!isEditMode && (
            <>
              <Button
                variant="outline"
                size="icon"
                onClick={handleShare}
                aria-label="Share deck"
              >
                {linkCopied ? (
                  <Check className="h-4 w-4 text-green-600" />
                ) : (
                  <Share2 className="h-4 w-4" />
                )}
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setShowExportModal(true)}
                aria-label="Export deck"
              >
                <Download className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setShowDeleteConfirm(true)}
                aria-label="Delete deck"
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </>
          )}

          <Button
            onClick={handleToggleEdit}
            variant={isEditMode ? "outline" : "default"}
          >
            {isEditMode ? (
              <>
                <Eye className="h-4 w-4 mr-2" />
                View
              </>
            ) : (
              <>
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </>
            )}
          </Button>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {isEditMode ? (
          <DeckBuilder onSave={handleSave} isSaving={isSaving} />
        ) : (
          <DeckListReadOnly deck={deck} />
        )}
      </div>

      {/* Export Modal */}
      <DeckExportModal
        open={showExportModal}
        onOpenChange={setShowExportModal}
        cards={deck.cards}
        deckName={deck.name}
      />

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-background rounded-lg p-6 max-w-sm mx-4 space-y-4">
            <h2 className="text-lg font-semibold">Delete Deck</h2>
            <p className="text-muted-foreground">
              Are you sure you want to delete &quot;{deck.name}&quot;? This
              action cannot be undone.
            </p>
            <div className="flex gap-2 justify-end">
              <Button
                variant="outline"
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={isDeleting}
              >
                {isDeleting ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : null}
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
