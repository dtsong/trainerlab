/**
 * Affiliate link generation and UTM tracking utilities.
 */

const DOUBLE_HOLO_BASE_URL = "https://doubleholo.com";
const TCGPLAYER_BASE_URL = "https://tcgplayer.com";

// TrainerLab affiliate codes (placeholder - need actual codes)
const AFFILIATE_CODES = {
  doubleHolo: "trainerlab",
  tcgPlayer: "trainerlab",
};

interface UTMParams {
  source: string;
  medium: string;
  campaign: string;
  content?: string;
}

function buildUTMQuery(params: UTMParams): string {
  const searchParams = new URLSearchParams();
  searchParams.set("utm_source", params.source);
  searchParams.set("utm_medium", params.medium);
  searchParams.set("utm_campaign", params.campaign);
  if (params.content) {
    searchParams.set("utm_content", params.content);
  }
  return searchParams.toString();
}

/**
 * Generate a DoubleHolo affiliate link for a deck.
 */
export function getDoubleHoloLink(deckName: string, deckId?: string): string {
  const utm = buildUTMQuery({
    source: "trainerlab",
    medium: "referral",
    campaign: "build_deck",
    content: deckId,
  });

  // Placeholder URL structure - need actual DoubleHolo API docs
  const deckPath = encodeURIComponent(
    deckName.toLowerCase().replace(/\s+/g, "-")
  );
  return `${DOUBLE_HOLO_BASE_URL}/search?ref=${AFFILIATE_CODES.doubleHolo}&${utm}`;
}

/**
 * Generate a TCGPlayer affiliate link for a deck.
 */
export function getTCGPlayerLink(deckName: string, deckId?: string): string {
  const utm = buildUTMQuery({
    source: "trainerlab",
    medium: "referral",
    campaign: "build_deck",
    content: deckId,
  });

  // Placeholder URL structure - need actual TCGPlayer affiliate docs
  return `${TCGPLAYER_BASE_URL}/search/pokemon-tcg?ref=${AFFILIATE_CODES.tcgPlayer}&${utm}`;
}

/**
 * Generate affiliate links for a specific card.
 */
export function getCardLinks(
  cardId: string,
  cardName: string
): {
  doubleHolo: string;
  tcgPlayer: string;
} {
  const utm = buildUTMQuery({
    source: "trainerlab",
    medium: "referral",
    campaign: "card_view",
    content: cardId,
  });

  return {
    doubleHolo: `${DOUBLE_HOLO_BASE_URL}/search?q=${encodeURIComponent(cardName)}&ref=${AFFILIATE_CODES.doubleHolo}&${utm}`,
    tcgPlayer: `${TCGPLAYER_BASE_URL}/search/pokemon-tcg?q=${encodeURIComponent(cardName)}&ref=${AFFILIATE_CODES.tcgPlayer}&${utm}`,
  };
}

/**
 * Placeholder price estimates (need actual pricing API).
 */
export function estimateDeckPrice(cardCount: number): {
  low: number;
  mid: number;
  high: number;
} {
  // Very rough estimates based on typical deck costs
  // Real implementation would use TCGPlayer or DoubleHolo pricing APIs
  const basePrice = cardCount * 0.5; // Assume $0.50 per card on average
  return {
    low: Math.round(basePrice * 0.7),
    mid: Math.round(basePrice),
    high: Math.round(basePrice * 1.5),
  };
}
