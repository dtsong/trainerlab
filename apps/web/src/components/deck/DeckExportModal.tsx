"use client";

import { useState, useCallback, useMemo } from "react";
import { Copy, Download, Check, AlertCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useDeckStore } from "@/stores/deckStore";
import {
  exportDeck,
  getFormatDisplayName,
  type DeckExportFormat,
} from "@/lib/deckFormats";

interface DeckExportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Optional cards to export. If not provided, uses the deck store. */
  cards?: DeckCard[];
  /** Optional deck name for file download. If not provided, uses the deck store. */
  deckName?: string;
}

import type { DeckCard } from "@/types/deck";

export function DeckExportModal({
  open,
  onOpenChange,
  cards: cardsProp,
  deckName,
}: DeckExportModalProps) {
  const [format, setFormat] = useState<DeckExportFormat>("ptcgo");
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);

  const storeCards = useDeckStore((state) => state.cards);
  const storeName = useDeckStore((state) => state.name);

  const cards = cardsProp ?? storeCards;
  const name = deckName ?? storeName;

  const exportedText = useMemo(() => {
    return exportDeck(cards, format);
  }, [cards, format]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(exportedText);
      setCopied(true);
      setCopyError(false);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy to clipboard:", error);
      setCopyError(true);
      setTimeout(() => setCopyError(false), 3000);
    }
  }, [exportedText]);

  const handleDownload = useCallback(() => {
    const filename = `${name || "deck"}-${format}.txt`;
    const blob = new Blob([exportedText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [exportedText, name, format]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Export Deck</DialogTitle>
          <DialogDescription>
            Export your deck list to use in Pokemon TCG Online or Pokemon TCG
            Live.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Format selector */}
          <div className="space-y-2">
            <label htmlFor="export-format" className="text-sm font-medium">
              Format
            </label>
            <Select
              value={format}
              onValueChange={(value) => setFormat(value as DeckExportFormat)}
            >
              <SelectTrigger id="export-format">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ptcgo">
                  {getFormatDisplayName("ptcgo")}
                </SelectItem>
                <SelectItem value="ptcgl">
                  {getFormatDisplayName("ptcgl")}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Preview */}
          <div className="space-y-2">
            <label htmlFor="export-preview" className="text-sm font-medium">
              Preview
            </label>
            <Textarea
              id="export-preview"
              value={exportedText}
              readOnly
              className="font-mono text-xs h-[200px] resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button onClick={handleCopy} variant="outline" className="flex-1">
              {copyError ? (
                <>
                  <AlertCircle className="h-4 w-4 mr-2 text-destructive" />
                  Copy failed
                </>
              ) : copied ? (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy to Clipboard
                </>
              )}
            </Button>
            <Button onClick={handleDownload} className="flex-1">
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
