import { describe, it, expect } from "vitest";
import {
  parseDeckList,
  exportToPTCGO,
  exportDeck,
  getFormatDisplayName,
  type ParsedCard,
} from "../deckFormats";
import type { DeckCard } from "@/types/deck";
import type { ApiCardSummary } from "@trainerlab/shared-types";

// Helper to create a mock DeckCard
function createDeckCard(
  overrides: Partial<ApiCardSummary> & { quantity?: number }
): DeckCard {
  const { quantity = 1, ...cardOverrides } = overrides;
  return {
    card: {
      id: "sv1-25",
      name: "Pikachu",
      supertype: "Pokemon",
      types: ["Lightning"],
      set_id: "sv1",
      rarity: "Common",
      image_small: null,
      ...cardOverrides,
    },
    quantity,
    position: 0,
  };
}

describe("parseDeckList", () => {
  describe("PTCGO format parsing", () => {
    it("should parse standard PTCGO format: '4 Card Name SET 123'", () => {
      const result = parseDeckList("4 Pikachu SVI 123");

      expect(result.cards).toHaveLength(1);
      expect(result.cards[0]).toEqual({
        quantity: 4,
        name: "Pikachu",
        setCode: "SVI",
        number: "123",
      });
      expect(result.errors).toHaveLength(0);
    });

    it("should parse format with 'x' quantity: '4x Card Name SET 123'", () => {
      const result = parseDeckList("4x Pikachu SVI 123");

      expect(result.cards).toHaveLength(1);
      expect(result.cards[0]).toEqual({
        quantity: 4,
        name: "Pikachu",
        setCode: "SVI",
        number: "123",
      });
    });

    it("should parse multi-word card names", () => {
      const result = parseDeckList("4 Professor's Research SVI 189");

      expect(result.cards).toHaveLength(1);
      expect(result.cards[0].name).toBe("Professor's Research");
    });

    it("should parse card names with special characters", () => {
      const result = parseDeckList("2 Arven (ACE Spec) TEF 166");

      expect(result.cards).toHaveLength(1);
      expect(result.cards[0].name).toBe("Arven (ACE Spec)");
    });

    it("should handle lowercase set codes", () => {
      const result = parseDeckList("4 Pikachu svi 123");

      expect(result.cards[0].setCode).toBe("SVI");
    });
  });

  describe("simple format parsing", () => {
    it("should parse simple format without set: '4 Card Name'", () => {
      const result = parseDeckList("4 Pikachu");

      expect(result.cards).toHaveLength(1);
      expect(result.cards[0]).toEqual({
        quantity: 4,
        name: "Pikachu",
      });
      expect(result.cards[0].setCode).toBeUndefined();
      expect(result.cards[0].number).toBeUndefined();
    });

    it("should parse simple format with 'x': '4x Card Name'", () => {
      const result = parseDeckList("4x Pikachu");

      expect(result.cards[0]).toEqual({
        quantity: 4,
        name: "Pikachu",
      });
    });
  });

  describe("reverse format parsing", () => {
    it("should parse reverse format: 'Card Name x4'", () => {
      const result = parseDeckList("Pikachu x4");

      expect(result.cards).toHaveLength(1);
      expect(result.cards[0]).toEqual({
        quantity: 4,
        name: "Pikachu",
      });
    });

    it("should parse reverse format with uppercase X: 'Card Name X4'", () => {
      const result = parseDeckList("Pikachu X4");

      expect(result.cards[0].quantity).toBe(4);
    });
  });

  describe("section headers", () => {
    it("should skip Pokemon section header", () => {
      const result = parseDeckList("Pokemon: 20\n4 Pikachu SVI 123");

      expect(result.cards).toHaveLength(1);
      expect(result.errors).toHaveLength(0);
    });

    it("should skip Trainer section header", () => {
      const result = parseDeckList(
        "Trainer: 30\n4 Professor's Research SVI 189"
      );

      expect(result.cards).toHaveLength(1);
    });

    it("should skip Energy section header", () => {
      const result = parseDeckList(
        "Energy: 10\n10 Basic Lightning Energy SVI 257"
      );

      expect(result.cards).toHaveLength(1);
    });

    it("should skip Pokémon header with accent", () => {
      const result = parseDeckList("Pokémon: 20\n4 Pikachu SVI 123");

      expect(result.cards).toHaveLength(1);
      expect(result.errors).toHaveLength(0);
    });
  });

  describe("empty lines and whitespace", () => {
    it("should skip empty lines", () => {
      const result = parseDeckList("4 Pikachu SVI 123\n\n4 Raichu SVI 124");

      expect(result.cards).toHaveLength(2);
      expect(result.errors).toHaveLength(0);
    });

    it("should trim whitespace from lines", () => {
      const result = parseDeckList("  4 Pikachu SVI 123  ");

      expect(result.cards).toHaveLength(1);
      expect(result.cards[0].name).toBe("Pikachu");
    });
  });

  describe("error handling", () => {
    it("should report errors for invalid lines", () => {
      const result = parseDeckList("Invalid line\n4 Pikachu SVI 123");

      expect(result.cards).toHaveLength(1);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0]).toContain("Line 1");
      expect(result.errors[0]).toContain("Invalid line");
    });

    it("should handle mixed valid and invalid lines", () => {
      const result = parseDeckList(
        "4 Pikachu SVI 123\nInvalid\n4 Raichu SVI 124"
      );

      expect(result.cards).toHaveLength(2);
      expect(result.errors).toHaveLength(1);
    });

    it("should return empty arrays for empty input", () => {
      const result = parseDeckList("");

      expect(result.cards).toHaveLength(0);
      expect(result.errors).toHaveLength(0);
    });

    it("should return empty arrays for whitespace-only input", () => {
      const result = parseDeckList("   \n   \n   ");

      expect(result.cards).toHaveLength(0);
      expect(result.errors).toHaveLength(0);
    });
  });

  describe("full deck parsing", () => {
    it("should parse a complete PTCGO deck list", () => {
      const deckList = `Pokemon: 12
4 Pikachu SVI 123
4 Raichu SVI 124
4 Pichu SVI 122

Trainer: 38
4 Professor's Research SVI 189
4 Boss's Orders SVI 172

Energy: 10
10 Basic Lightning Energy SVI 257`;

      const result = parseDeckList(deckList);

      expect(result.cards).toHaveLength(6);
      expect(result.errors).toHaveLength(0);

      // Verify specific cards
      expect(result.cards[0]).toEqual({
        quantity: 4,
        name: "Pikachu",
        setCode: "SVI",
        number: "123",
      });
      expect(result.cards[5]).toEqual({
        quantity: 10,
        name: "Basic Lightning Energy",
        setCode: "SVI",
        number: "257",
      });
    });
  });
});

describe("exportToPTCGO", () => {
  it("should export empty deck as empty string", () => {
    const result = exportToPTCGO([]);
    expect(result).toBe("");
  });

  it("should export Pokemon section with header and count", () => {
    const cards: DeckCard[] = [
      createDeckCard({ name: "Pikachu", supertype: "Pokemon", quantity: 4 }),
    ];

    const result = exportToPTCGO(cards);

    expect(result).toContain("Pokemon: 4");
    expect(result).toContain("4 Pikachu SV1 25");
  });

  it("should export Trainer section", () => {
    const cards: DeckCard[] = [
      createDeckCard({
        id: "sv1-189",
        name: "Professor's Research",
        supertype: "Trainer",
        quantity: 4,
      }),
    ];

    const result = exportToPTCGO(cards);

    expect(result).toContain("Trainer: 4");
    expect(result).toContain("4 Professor's Research SV1 189");
  });

  it("should export Energy section", () => {
    const cards: DeckCard[] = [
      createDeckCard({
        id: "sv1-257",
        name: "Basic Lightning Energy",
        supertype: "Energy",
        quantity: 10,
      }),
    ];

    const result = exportToPTCGO(cards);

    expect(result).toContain("Energy: 10");
    expect(result).toContain("10 Basic Lightning Energy SV1 257");
  });

  it("should group cards by supertype in correct order", () => {
    const cards: DeckCard[] = [
      createDeckCard({
        id: "sv1-257",
        name: "Lightning Energy",
        supertype: "Energy",
        quantity: 10,
      }),
      createDeckCard({
        id: "sv1-189",
        name: "Professor's Research",
        supertype: "Trainer",
        quantity: 4,
      }),
      createDeckCard({
        name: "Pikachu",
        supertype: "Pokemon",
        quantity: 4,
      }),
    ];

    const result = exportToPTCGO(cards);
    const pokemonIndex = result.indexOf("Pokemon:");
    const trainerIndex = result.indexOf("Trainer:");
    const energyIndex = result.indexOf("Energy:");

    expect(pokemonIndex).toBeLessThan(trainerIndex);
    expect(trainerIndex).toBeLessThan(energyIndex);
  });

  it("should calculate correct totals for sections", () => {
    const cards: DeckCard[] = [
      createDeckCard({
        id: "sv1-25",
        name: "Pikachu",
        supertype: "Pokemon",
        quantity: 4,
      }),
      createDeckCard({
        id: "sv1-26",
        name: "Raichu",
        supertype: "Pokemon",
        quantity: 2,
      }),
    ];

    const result = exportToPTCGO(cards);

    expect(result).toContain("Pokemon: 6");
  });

  it("should extract card number from ID correctly", () => {
    const cards: DeckCard[] = [
      createDeckCard({
        id: "swsh1-025",
        name: "Pikachu",
        supertype: "Pokemon",
        quantity: 1,
        set_id: "swsh1",
      }),
    ];

    const result = exportToPTCGO(cards);

    expect(result).toContain("1 Pikachu SWSH1 025");
  });

  it("should handle deck with only one card type", () => {
    const cards: DeckCard[] = [
      createDeckCard({
        id: "sv1-189",
        name: "Professor's Research",
        supertype: "Trainer",
        quantity: 4,
      }),
    ];

    const result = exportToPTCGO(cards);

    expect(result).toContain("Trainer: 4");
    expect(result).not.toContain("Pokemon:");
    expect(result).not.toContain("Energy:");
  });
});

describe("exportDeck", () => {
  it("should export to PTCGO format when specified", () => {
    const cards: DeckCard[] = [
      createDeckCard({ name: "Pikachu", supertype: "Pokemon", quantity: 4 }),
    ];

    const result = exportDeck(cards, "ptcgo");

    expect(result).toContain("Pokemon: 4");
  });

  it("should export to PTCGL format when specified", () => {
    const cards: DeckCard[] = [
      createDeckCard({ name: "Pikachu", supertype: "Pokemon", quantity: 4 }),
    ];

    const result = exportDeck(cards, "ptcgl");

    // Currently PTCGL uses same format as PTCGO
    expect(result).toContain("Pokemon: 4");
  });
});

describe("getFormatDisplayName", () => {
  it("should return 'PTCGO' for ptcgo format", () => {
    expect(getFormatDisplayName("ptcgo")).toBe("PTCGO");
  });

  it("should return 'Pokemon TCG Live' for ptcgl format", () => {
    expect(getFormatDisplayName("ptcgl")).toBe("Pokemon TCG Live");
  });
});
