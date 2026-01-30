import { describe, it, expect, expectTypeOf } from "vitest";
import type {
  Card,
  Set,
  Deck,
  DeckCard,
  User,
  ApiCard,
  ApiCardSummary,
  ApiSet,
  ApiPaginatedResponse,
} from "../index";

describe("Card type", () => {
  it("accepts valid card with required fields", () => {
    const card: Card = {
      id: "sv4-6",
      nameEn: "Charizard ex",
      supertype: "Pokemon",
      setId: "sv4",
      setName: "Paradox Rift",
      number: "6",
    };

    expect(card.id).toBe("sv4-6");
    expect(card.supertype).toBe("Pokemon");
  });

  it("accepts card with all optional fields", () => {
    const card: Card = {
      id: "sv4-6",
      nameEn: "Charizard ex",
      nameJa: "リザードンex",
      supertype: "Pokemon",
      subtypes: ["Stage 2", "ex"],
      hp: 330,
      types: ["Fire"],
      setId: "sv4",
      setName: "Paradox Rift",
      number: "6",
      rarity: "Double Rare",
      imageSmall: "https://example.com/small.png",
      imageLarge: "https://example.com/large.png",
      legalityStandard: "Legal",
      legalityExpanded: "Legal",
      regulationMark: "G",
    };

    expect(card.nameJa).toBe("リザードンex");
    expect(card.hp).toBe(330);
  });

  it("enforces supertype union", () => {
    expectTypeOf<Card["supertype"]>().toEqualTypeOf<
      "Pokemon" | "Trainer" | "Energy"
    >();
  });

  it("enforces legality union", () => {
    expectTypeOf<Card["legalityStandard"]>().toEqualTypeOf<
      "Legal" | "Banned" | "Not Legal" | undefined
    >();
  });
});

describe("Set type", () => {
  it("accepts valid set", () => {
    const set: Set = {
      id: "sv4",
      name: "Paradox Rift",
      series: "Scarlet & Violet",
    };

    expect(set.id).toBe("sv4");
  });

  it("accepts set with optional fields", () => {
    const set: Set = {
      id: "sv4",
      name: "Paradox Rift",
      series: "Scarlet & Violet",
      totalCards: 182,
      releaseDate: "2023-11-03",
      releaseDateJp: "2023-09-22",
    };

    expect(set.totalCards).toBe(182);
  });
});

describe("Deck type", () => {
  it("accepts valid deck", () => {
    const deck: Deck = {
      id: "deck-123",
      userId: "user-456",
      name: "Charizard ex",
      format: "standard",
      cards: [{ cardId: "sv4-6", quantity: 3 }],
      isPublic: false,
      createdAt: "2024-01-01T00:00:00Z",
      updatedAt: "2024-01-01T00:00:00Z",
    };

    expect(deck.name).toBe("Charizard ex");
    expect(deck.cards).toHaveLength(1);
  });

  it("enforces format union", () => {
    expectTypeOf<Deck["format"]>().toEqualTypeOf<"standard" | "expanded">();
  });
});

describe("DeckCard type", () => {
  it("accepts valid deck card", () => {
    const deckCard: DeckCard = {
      cardId: "sv4-6",
      quantity: 4,
    };

    expect(deckCard.quantity).toBe(4);
  });
});

describe("User type", () => {
  it("accepts valid user", () => {
    const user: User = {
      id: "user-123",
      email: "trainer@example.com",
      createdAt: "2024-01-01T00:00:00Z",
      updatedAt: "2024-01-01T00:00:00Z",
    };

    expect(user.email).toBe("trainer@example.com");
  });

  it("accepts user with optional fields", () => {
    const user: User = {
      id: "user-123",
      email: "trainer@example.com",
      displayName: "Ash Ketchum",
      preferences: { theme: "dark" },
      createdAt: "2024-01-01T00:00:00Z",
      updatedAt: "2024-01-01T00:00:00Z",
    };

    expect(user.displayName).toBe("Ash Ketchum");
  });
});

// API response types (snake_case, matching backend)
describe("ApiCard type", () => {
  it("accepts valid API card response", () => {
    const card: ApiCard = {
      id: "sv4-6",
      local_id: "6",
      name: "Charizard ex",
      supertype: "Pokemon",
      set_id: "sv4",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    };

    expect(card.id).toBe("sv4-6");
    expect(card.set_id).toBe("sv4");
  });

  it("accepts API card with all fields", () => {
    const card: ApiCard = {
      id: "sv4-6",
      local_id: "6",
      name: "Charizard ex",
      japanese_name: "リザードンex",
      supertype: "Pokemon",
      subtypes: ["Stage 2", "ex"],
      types: ["Fire"],
      hp: 330,
      attacks: [{ name: "Flare Blitz", cost: ["Fire", "Fire"], damage: "180" }],
      abilities: [{ name: "Inferno Reign", effect: "Draw cards" }],
      weaknesses: [{ type: "Water", value: "x2" }],
      set_id: "sv4",
      rarity: "Double Rare",
      number: "6",
      image_small: "https://example.com/small.png",
      image_large: "https://example.com/large.png",
      regulation_mark: "G",
      legalities: { standard: true, expanded: true },
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    };

    expect(card.japanese_name).toBe("リザードンex");
    expect(card.hp).toBe(330);
  });
});

describe("ApiCardSummary type", () => {
  it("accepts valid API card summary", () => {
    const summary: ApiCardSummary = {
      id: "sv4-6",
      name: "Charizard ex",
      supertype: "Pokemon",
      set_id: "sv4",
    };

    expect(summary.name).toBe("Charizard ex");
  });
});

describe("ApiSet type", () => {
  it("accepts valid API set response", () => {
    const set: ApiSet = {
      id: "sv4",
      name: "Paradox Rift",
      series: "Scarlet & Violet",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    };

    expect(set.id).toBe("sv4");
  });
});

describe("ApiPaginatedResponse type", () => {
  it("accepts valid paginated response", () => {
    const response: ApiPaginatedResponse<ApiCardSummary> = {
      items: [
        {
          id: "sv4-6",
          name: "Charizard ex",
          supertype: "Pokemon",
          set_id: "sv4",
        },
      ],
      total: 100,
      page: 1,
      page_size: 20,
      pages: 5,
    };

    expect(response.items).toHaveLength(1);
    expect(response.total).toBe(100);
  });
});
