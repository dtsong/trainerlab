import { describe, it, expect } from "vitest";
import {
  getDoubleHoloLink,
  getTCGPlayerLink,
  getCardLinks,
  estimateDeckPrice,
} from "../affiliate";

describe("getDoubleHoloLink", () => {
  it("should generate DoubleHolo link with UTM params", () => {
    const link = getDoubleHoloLink("Charizard ex");

    expect(link).toContain("https://doubleholo.com/search");
    expect(link).toContain("ref=trainerlab");
    expect(link).toContain("utm_source=trainerlab");
    expect(link).toContain("utm_medium=referral");
    expect(link).toContain("utm_campaign=build_deck");
  });

  it("should include deck ID in utm_content when provided", () => {
    const link = getDoubleHoloLink("Charizard ex", "deck-123");

    expect(link).toContain("utm_content=deck-123");
  });

  it("should not include utm_content when deck ID is undefined", () => {
    const link = getDoubleHoloLink("Charizard ex");

    expect(link).not.toContain("utm_content=undefined");
  });

  it("should handle special characters in deck name", () => {
    const link = getDoubleHoloLink("Charizard ex / Pidgeot");

    expect(link).toContain("https://doubleholo.com/search");
  });
});

describe("getTCGPlayerLink", () => {
  it("should generate TCGPlayer link with UTM params", () => {
    const link = getTCGPlayerLink("Charizard ex");

    expect(link).toContain("https://tcgplayer.com/search/pokemon-tcg");
    expect(link).toContain("ref=trainerlab");
    expect(link).toContain("utm_source=trainerlab");
    expect(link).toContain("utm_medium=referral");
    expect(link).toContain("utm_campaign=build_deck");
  });

  it("should include deck ID in utm_content when provided", () => {
    const link = getTCGPlayerLink("Charizard ex", "deck-456");

    expect(link).toContain("utm_content=deck-456");
  });

  it("should not include utm_content when deck ID is undefined", () => {
    const link = getTCGPlayerLink("Charizard ex");

    expect(link).not.toContain("utm_content=undefined");
  });
});

describe("getCardLinks", () => {
  it("should generate both DoubleHolo and TCGPlayer links", () => {
    const links = getCardLinks("sv3-125", "Charizard ex");

    expect(links.doubleHolo).toContain("https://doubleholo.com/search");
    expect(links.tcgPlayer).toContain("https://tcgplayer.com/search/pokemon-tcg");
  });

  it("should include card name in search query", () => {
    const links = getCardLinks("sv3-125", "Charizard ex");

    expect(links.doubleHolo).toContain(
      `q=${encodeURIComponent("Charizard ex")}`
    );
    expect(links.tcgPlayer).toContain(
      `q=${encodeURIComponent("Charizard ex")}`
    );
  });

  it("should include card ID in utm_content", () => {
    const links = getCardLinks("sv3-125", "Charizard ex");

    expect(links.doubleHolo).toContain("utm_content=sv3-125");
    expect(links.tcgPlayer).toContain("utm_content=sv3-125");
  });

  it("should use card_view campaign for card links", () => {
    const links = getCardLinks("sv3-125", "Charizard ex");

    expect(links.doubleHolo).toContain("utm_campaign=card_view");
    expect(links.tcgPlayer).toContain("utm_campaign=card_view");
  });

  it("should handle card names with special characters", () => {
    const links = getCardLinks("sv1-166", "Professor's Research");

    expect(links.doubleHolo).toContain(
      encodeURIComponent("Professor's Research")
    );
    expect(links.tcgPlayer).toContain(
      encodeURIComponent("Professor's Research")
    );
  });

  it("should include affiliate codes", () => {
    const links = getCardLinks("sv3-125", "Charizard ex");

    expect(links.doubleHolo).toContain("ref=trainerlab");
    expect(links.tcgPlayer).toContain("ref=trainerlab");
  });
});

describe("estimateDeckPrice", () => {
  it("should return price estimates with low, mid, and high values", () => {
    const prices = estimateDeckPrice(60);

    expect(prices).toHaveProperty("low");
    expect(prices).toHaveProperty("mid");
    expect(prices).toHaveProperty("high");
  });

  it("should return integer values", () => {
    const prices = estimateDeckPrice(60);

    expect(Number.isInteger(prices.low)).toBe(true);
    expect(Number.isInteger(prices.mid)).toBe(true);
    expect(Number.isInteger(prices.high)).toBe(true);
  });

  it("should maintain low < mid < high ordering", () => {
    const prices = estimateDeckPrice(60);

    expect(prices.low).toBeLessThan(prices.mid);
    expect(prices.mid).toBeLessThan(prices.high);
  });

  it("should scale with card count", () => {
    const smallDeck = estimateDeckPrice(30);
    const largeDeck = estimateDeckPrice(60);

    expect(largeDeck.mid).toBeGreaterThan(smallDeck.mid);
  });

  it("should handle typical deck size (60 cards)", () => {
    const prices = estimateDeckPrice(60);

    expect(prices.mid).toBe(30);
    expect(prices.low).toBe(21);
    expect(prices.high).toBe(45);
  });

  it("should handle zero cards", () => {
    const prices = estimateDeckPrice(0);

    expect(prices.low).toBe(0);
    expect(prices.mid).toBe(0);
    expect(prices.high).toBe(0);
  });

  it("should handle single card", () => {
    const prices = estimateDeckPrice(1);

    expect(prices.mid).toBeLessThanOrEqual(1);
    expect(prices.low).toBeLessThanOrEqual(prices.mid);
    expect(prices.high).toBeGreaterThanOrEqual(prices.mid);
  });

  it("should handle large card counts", () => {
    const prices = estimateDeckPrice(100);

    expect(prices.mid).toBe(50);
    expect(prices.low).toBe(35);
    expect(prices.high).toBe(75);
  });
});
