/**
 * Deck format utilities for import/export.
 * Supports PTCGO (Pokemon TCG Online) and Pokemon TCG Live formats.
 */

import type { DeckCard } from "@/types/deck";

export type DeckExportFormat = "ptcgo" | "ptcgl";

/**
 * Export a deck to PTCGO format.
 * Format: "4 Card Name SET 123"
 */
export function exportToPTCGO(cards: DeckCard[]): string {
  const grouped = groupCardsByType(cards);
  const lines: string[] = [];

  // Pokemon section
  if (grouped.Pokemon.length > 0) {
    lines.push("Pokemon: " + countCards(grouped.Pokemon));
    for (const dc of grouped.Pokemon) {
      lines.push(formatPTCGOLine(dc));
    }
    lines.push("");
  }

  // Trainer section
  if (grouped.Trainer.length > 0) {
    lines.push("Trainer: " + countCards(grouped.Trainer));
    for (const dc of grouped.Trainer) {
      lines.push(formatPTCGOLine(dc));
    }
    lines.push("");
  }

  // Energy section
  if (grouped.Energy.length > 0) {
    lines.push("Energy: " + countCards(grouped.Energy));
    for (const dc of grouped.Energy) {
      lines.push(formatPTCGOLine(dc));
    }
  }

  return lines.join("\n").trim();
}

/**
 * Export a deck to Pokemon TCG Live format.
 * Similar to PTCGO but uses different set codes.
 */
export function exportToPTCGL(cards: DeckCard[]): string {
  // PTCGL format is essentially the same as PTCGO
  // with potentially different set code mappings
  return exportToPTCGO(cards);
}

/**
 * Export deck to the specified format.
 */
export function exportDeck(
  cards: DeckCard[],
  format: DeckExportFormat,
): string {
  switch (format) {
    case "ptcgo":
      return exportToPTCGO(cards);
    case "ptcgl":
      return exportToPTCGL(cards);
  }
}

/**
 * Parse a deck list from text.
 * Auto-detects PTCGO/PTCGL format.
 */
export interface ParsedCard {
  quantity: number;
  name: string;
  setCode?: string;
  number?: string;
}

export interface ParseResult {
  cards: ParsedCard[];
  errors: string[];
}

export function parseDeckList(text: string): ParseResult {
  const cards: ParsedCard[] = [];
  const errors: string[] = [];
  const lines = text.split("\n");

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Skip empty lines and section headers
    if (!line || isHeaderLine(line)) {
      continue;
    }

    const parsed = parseLine(line);
    if (parsed) {
      cards.push(parsed);
    } else if (line.length > 0) {
      errors.push(`Line ${i + 1}: Could not parse "${line}"`);
    }
  }

  return { cards, errors };
}

/**
 * Format a single card line in PTCGO format.
 */
function formatPTCGOLine(dc: DeckCard): string {
  const { card, quantity } = dc;
  // Extract set code from set_id (e.g., "sv1" from "sv1-123")
  const setCode = card.set_id.toUpperCase();
  // Use local_id or extract number from id
  const number = extractCardNumber(card.id);
  return `${quantity} ${card.name} ${setCode} ${number}`;
}

/**
 * Extract card number from card ID.
 */
function extractCardNumber(cardId: string): string {
  // Card IDs are typically "setcode-number" format
  const parts = cardId.split("-");
  return parts.length > 1 ? parts[parts.length - 1] : cardId;
}

/**
 * Check if a line is a section header.
 */
function isHeaderLine(line: string): boolean {
  const lowerLine = line.toLowerCase();
  return (
    lowerLine.startsWith("pokemon:") ||
    lowerLine.startsWith("trainer:") ||
    lowerLine.startsWith("energy:") ||
    lowerLine.startsWith("pokémon:")
  );
}

/**
 * Parse a single line into a card entry.
 * Supports formats:
 * - "4 Card Name SET 123"
 * - "4x Card Name SET 123"
 * - "Card Name x4"
 */
function parseLine(line: string): ParsedCard | null {
  // Try "4 Card Name SET 123" format
  const ptcgoMatch = line.match(/^(\d+)x?\s+(.+?)\s+([A-Z0-9]+)\s+(\d+)$/i);
  if (ptcgoMatch) {
    return {
      quantity: parseInt(ptcgoMatch[1], 10),
      name: ptcgoMatch[2].trim(),
      setCode: ptcgoMatch[3].toUpperCase(),
      number: ptcgoMatch[4],
    };
  }

  // Try "4 Card Name" format (no set/number)
  const simpleMatch = line.match(/^(\d+)x?\s+(.+)$/i);
  if (simpleMatch) {
    return {
      quantity: parseInt(simpleMatch[1], 10),
      name: simpleMatch[2].trim(),
    };
  }

  // Try "Card Name x4" format
  const reverseMatch = line.match(/^(.+?)\s*[xX](\d+)$/);
  if (reverseMatch) {
    return {
      quantity: parseInt(reverseMatch[2], 10),
      name: reverseMatch[1].trim(),
    };
  }

  return null;
}

/**
 * Group cards by supertype.
 */
function groupCardsByType(cards: DeckCard[]): Record<string, DeckCard[]> {
  return {
    Pokemon: cards.filter((c) => c.card.supertype === "Pokemon"),
    Trainer: cards.filter((c) => c.card.supertype === "Trainer"),
    Energy: cards.filter((c) => c.card.supertype === "Energy"),
  };
}

/**
 * Count total cards in a group.
 */
function countCards(cards: DeckCard[]): number {
  return cards.reduce((sum, c) => sum + c.quantity, 0);
}

/**
 * Get format display name.
 */
export function getFormatDisplayName(format: DeckExportFormat): string {
  switch (format) {
    case "ptcgo":
      return "PTCGO";
    case "ptcgl":
      return "Pokemon TCG Live";
  }
}
