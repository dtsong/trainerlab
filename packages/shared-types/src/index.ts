// Card types
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

// Set types
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

// Deck types
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

// User types
export interface User {
  id: string;
  email: string;
  displayName?: string;
  preferences?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}
