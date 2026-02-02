// API response types (snake_case, matching backend schemas)
export * from "./card";
export * from "./set";
export * from "./pagination";
export * from "./meta";
export * from "./format";
export * from "./tournament";
export * from "./lab-note";
export * from "./japan";

// Frontend types (camelCase, for deck builder etc.)
// These match the original shared-types naming conventions

export interface Card {
  id: string;
  nameEn: string;
  nameJa?: string;
  supertype: "Pokemon" | "Trainer" | "Energy";
  subtypes?: string[];
  hp?: number;
  types?: string[];
  setId: string;
  setName: string;
  number: string;
  rarity?: string;
  imageSmall?: string;
  imageLarge?: string;
  legalityStandard?: "Legal" | "Banned" | "Not Legal";
  legalityExpanded?: "Legal" | "Banned" | "Not Legal";
  regulationMark?: string;
}

export interface Set {
  id: string;
  name: string;
  series: string;
  totalCards?: number;
  releaseDate?: string;
  releaseDateJp?: string;
  logoUrl?: string;
  symbolUrl?: string;
}

export interface DeckCard {
  cardId: string;
  quantity: number;
}

export interface Deck {
  id: string;
  userId: string;
  name: string;
  description?: string;
  format: "standard" | "expanded";
  archetype?: string;
  cards: DeckCard[];
  pokemonCount?: number;
  trainerCount?: number;
  energyCount?: number;
  isPublic: boolean;
  shareCode?: string;
  createdAt: string;
  updatedAt: string;
}

export interface User {
  id: string;
  email: string;
  displayName?: string;
  preferences?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}
