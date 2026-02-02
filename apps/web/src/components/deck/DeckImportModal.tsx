"use client";

import { useState, useCallback, useMemo } from "react";
import { Upload, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useDeckStore } from "@/stores/deckStore";
import { cardsApi } from "@/lib/api";
import { parseDeckList, type ParsedCard } from "@/lib/deckFormats";
import { cn } from "@/lib/utils";

interface DeckImportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ImportStatus {
  card: ParsedCard;
  status: "pending" | "found" | "not_found" | "error";
}

export function DeckImportModal({ open, onOpenChange }: DeckImportModalProps) {
  const [inputText, setInputText] = useState("");
  const [isImporting, setIsImporting] = useState(false);
  const [importStatuses, setImportStatuses] = useState<ImportStatus[]>([]);

  const addCard = useDeckStore((state) => state.addCard);
  const setQuantity = useDeckStore((state) => state.setQuantity);

  const parseResult = useMemo(() => {
    if (!inputText.trim()) {
      return null;
    }
    return parseDeckList(inputText);
  }, [inputText]);

  const totalCards = useMemo(() => {
    if (!parseResult) return 0;
    return parseResult.cards.reduce((sum, c) => sum + c.quantity, 0);
  }, [parseResult]);

  const handleImport = useCallback(async () => {
    if (!parseResult || parseResult.cards.length === 0) return;

    setIsImporting(true);
    const statuses: ImportStatus[] = parseResult.cards.map((card) => ({
      card,
      status: "pending" as const,
    }));
    setImportStatuses(statuses);

    for (let i = 0; i < parseResult.cards.length; i++) {
      const parsedCard = parseResult.cards[i];

      try {
        // Search for the card by name
        const response = await cardsApi.search({
          q: parsedCard.name,
          limit: 10,
        });

        // Try to find an exact match
        const exactMatch = response.items.find(
          (c) => c.name.toLowerCase() === parsedCard.name.toLowerCase(),
        );

        // If we have set info, try to match that too
        const matchWithSet =
          parsedCard.setCode && parsedCard.number
            ? response.items.find(
                (c) =>
                  c.name.toLowerCase() === parsedCard.name.toLowerCase() &&
                  c.set_id.toLowerCase() === parsedCard.setCode!.toLowerCase(),
              )
            : null;

        const matchedCard = matchWithSet || exactMatch || response.items[0];

        if (matchedCard) {
          // Add the card to the deck
          addCard(matchedCard);
          // Set the quantity (addCard starts at 1, so we need to set the full quantity)
          if (parsedCard.quantity > 1) {
            setQuantity(matchedCard.id, parsedCard.quantity);
          }

          setImportStatuses((prev) =>
            prev.map((s, idx) =>
              idx === i ? { ...s, status: "found" as const } : s,
            ),
          );
        } else {
          setImportStatuses((prev) =>
            prev.map((s, idx) =>
              idx === i ? { ...s, status: "not_found" as const } : s,
            ),
          );
        }
      } catch (error) {
        console.error(`Failed to find card: ${parsedCard.name}`, error);
        setImportStatuses((prev) =>
          prev.map((s, idx) =>
            idx === i ? { ...s, status: "error" as const } : s,
          ),
        );
      }
    }

    setIsImporting(false);
  }, [parseResult, addCard, setQuantity]);

  const handleClose = useCallback(() => {
    setInputText("");
    setImportStatuses([]);
    onOpenChange(false);
  }, [onOpenChange]);

  const foundCount = importStatuses.filter((s) => s.status === "found").length;
  const notFoundCount = importStatuses.filter(
    (s) => s.status === "not_found",
  ).length;
  const errorCount = importStatuses.filter((s) => s.status === "error").length;
  const importComplete = importStatuses.length > 0 && !isImporting;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Import Deck</DialogTitle>
          <DialogDescription>
            Paste a deck list from Pokemon TCG Online or Pokemon TCG Live.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Input textarea */}
          <div className="space-y-2">
            <label htmlFor="import-decklist" className="text-sm font-medium">
              Deck List
            </label>
            <Textarea
              id="import-decklist"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={`Paste your deck list here...

Example:
Pokemon: 20
4 Pikachu SVI 123
2 Raichu SVI 124

Trainer: 30
4 Professor's Research SVI 189

Energy: 10
10 Lightning Energy SVI 257`}
              className="font-mono text-xs h-[180px] resize-none"
              disabled={isImporting}
            />
          </div>

          {/* Parse preview */}
          {parseResult && !importComplete && (
            <div className="rounded-md border p-3 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Preview</span>
                <span className="text-muted-foreground">
                  {parseResult.cards.length} unique cards, {totalCards} total
                </span>
              </div>

              {parseResult.errors.length > 0 && (
                <div className="text-xs text-amber-600 space-y-1">
                  {parseResult.errors.slice(0, 3).map((error, i) => (
                    <div key={i} className="flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {error}
                    </div>
                  ))}
                  {parseResult.errors.length > 3 && (
                    <div>...and {parseResult.errors.length - 3} more</div>
                  )}
                </div>
              )}

              <div className="text-xs text-muted-foreground max-h-[100px] overflow-y-auto space-y-0.5">
                {parseResult.cards.slice(0, 10).map((card, i) => (
                  <div key={i}>
                    {card.quantity}x {card.name}
                    {card.setCode && ` (${card.setCode})`}
                  </div>
                ))}
                {parseResult.cards.length > 10 && (
                  <div>...and {parseResult.cards.length - 10} more</div>
                )}
              </div>
            </div>
          )}

          {/* Import status */}
          {importStatuses.length > 0 && (
            <div className="rounded-md border p-3 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Import Status</span>
                {importComplete && (
                  <span className="text-muted-foreground">
                    {foundCount} found, {notFoundCount} not found
                    {errorCount > 0 && `, ${errorCount} failed`}
                  </span>
                )}
              </div>

              <div className="text-xs max-h-[120px] overflow-y-auto space-y-1">
                {importStatuses.map((status, i) => (
                  <div
                    key={i}
                    className={cn(
                      "flex items-center gap-2",
                      status.status === "found" && "text-green-600",
                      status.status === "not_found" && "text-red-600",
                      status.status === "error" && "text-amber-600",
                      status.status === "pending" && "text-muted-foreground",
                    )}
                  >
                    {status.status === "pending" && (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    )}
                    {status.status === "found" && (
                      <CheckCircle2 className="h-3 w-3" />
                    )}
                    {status.status === "not_found" && (
                      <AlertCircle className="h-3 w-3" />
                    )}
                    {status.status === "error" && (
                      <AlertCircle className="h-3 w-3" />
                    )}
                    {status.card.quantity}x {status.card.name}
                    {status.status === "error" && (
                      <span className="text-amber-600">(network error)</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleClose} className="flex-1">
              {importComplete ? "Done" : "Cancel"}
            </Button>
            {!importComplete && (
              <Button
                onClick={handleImport}
                disabled={
                  !parseResult || parseResult.cards.length === 0 || isImporting
                }
                className="flex-1"
              >
                {isImporting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Import
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
