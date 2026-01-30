import { describe, it, expect, beforeEach } from "vitest";
import { useDeckStore } from "../deckStore";
import type { ApiCardSummary } from "@trainerlab/shared-types";

// Helper to create mock cards
function createMockCard(
  overrides: Partial<ApiCardSummary> = {},
): ApiCardSummary {
  return {
    id: "swsh1-1",
    name: "Pikachu",
    supertype: "Pokemon",
    types: ["Lightning"],
    set_id: "swsh1",
    rarity: "Common",
    image_small: "https://example.com/pikachu.png",
    ...overrides,
  };
}

function createBasicEnergyCard(): ApiCardSummary {
  return {
    id: "swsh1-energy-1",
    name: "Lightning Energy",
    supertype: "Energy",
    types: ["Lightning"],
    set_id: "swsh1",
    rarity: null,
    image_small: "https://example.com/energy.png",
  };
}

describe("deckStore", () => {
  beforeEach(() => {
    // Reset store state before each test
    useDeckStore.setState({
      cards: [],
      name: "",
      description: "",
      format: "standard",
      isModified: false,
    });
  });

  describe("initial state", () => {
    it("should have correct initial state", () => {
      const state = useDeckStore.getState();
      expect(state.cards).toEqual([]);
      expect(state.name).toBe("");
      expect(state.description).toBe("");
      expect(state.format).toBe("standard");
      expect(state.isModified).toBe(false);
    });
  });

  describe("addCard", () => {
    it("should add a new card with quantity 1", () => {
      const card = createMockCard();
      useDeckStore.getState().addCard(card);

      const state = useDeckStore.getState();
      expect(state.cards).toHaveLength(1);
      expect(state.cards[0].card.id).toBe("swsh1-1");
      expect(state.cards[0].quantity).toBe(1);
      expect(state.cards[0].position).toBe(0);
      expect(state.isModified).toBe(true);
    });

    it("should increment quantity when adding existing card", () => {
      const card = createMockCard();
      useDeckStore.getState().addCard(card);
      useDeckStore.getState().addCard(card);

      const state = useDeckStore.getState();
      expect(state.cards).toHaveLength(1);
      expect(state.cards[0].quantity).toBe(2);
    });

    it("should enforce 4-card limit for non-basic-energy", () => {
      const card = createMockCard();
      for (let i = 0; i < 6; i++) {
        useDeckStore.getState().addCard(card);
      }

      const state = useDeckStore.getState();
      expect(state.cards[0].quantity).toBe(4);
    });

    it("should allow unlimited basic energy", () => {
      const energy = createBasicEnergyCard();
      for (let i = 0; i < 10; i++) {
        useDeckStore.getState().addCard(energy);
      }

      const state = useDeckStore.getState();
      expect(state.cards[0].quantity).toBe(10);
    });

    it("should treat Special Energy as limited", () => {
      const specialEnergy = createMockCard({
        id: "swsh1-special-1",
        name: "Special Lightning Energy",
        supertype: "Energy",
      });

      for (let i = 0; i < 6; i++) {
        useDeckStore.getState().addCard(specialEnergy);
      }

      const state = useDeckStore.getState();
      expect(state.cards[0].quantity).toBe(4);
    });

    it("should assign sequential positions to new cards", () => {
      const card1 = createMockCard({ id: "card-1" });
      const card2 = createMockCard({ id: "card-2" });
      const card3 = createMockCard({ id: "card-3" });

      useDeckStore.getState().addCard(card1);
      useDeckStore.getState().addCard(card2);
      useDeckStore.getState().addCard(card3);

      const state = useDeckStore.getState();
      expect(state.cards[0].position).toBe(0);
      expect(state.cards[1].position).toBe(1);
      expect(state.cards[2].position).toBe(2);
    });
  });

  describe("removeCard", () => {
    it("should decrement quantity when > 1", () => {
      const card = createMockCard();
      useDeckStore.getState().addCard(card);
      useDeckStore.getState().addCard(card);
      useDeckStore.getState().removeCard(card.id);

      const state = useDeckStore.getState();
      expect(state.cards[0].quantity).toBe(1);
      expect(state.isModified).toBe(true);
    });

    it("should remove card entry when quantity reaches 0", () => {
      const card = createMockCard();
      useDeckStore.getState().addCard(card);
      useDeckStore.getState().removeCard(card.id);

      const state = useDeckStore.getState();
      expect(state.cards).toHaveLength(0);
    });

    it("should reindex positions after removal", () => {
      const card1 = createMockCard({ id: "card-1" });
      const card2 = createMockCard({ id: "card-2" });
      const card3 = createMockCard({ id: "card-3" });

      useDeckStore.getState().addCard(card1);
      useDeckStore.getState().addCard(card2);
      useDeckStore.getState().addCard(card3);
      useDeckStore.getState().removeCard(card2.id);

      const state = useDeckStore.getState();
      expect(state.cards).toHaveLength(2);
      expect(state.cards[0].card.id).toBe("card-1");
      expect(state.cards[0].position).toBe(0);
      expect(state.cards[1].card.id).toBe("card-3");
      expect(state.cards[1].position).toBe(1);
    });

    it("should do nothing for non-existent card", () => {
      const card = createMockCard();
      useDeckStore.getState().addCard(card);

      const stateBefore = useDeckStore.getState();
      useDeckStore.getState().removeCard("non-existent");
      const stateAfter = useDeckStore.getState();

      expect(stateAfter.cards).toEqual(stateBefore.cards);
    });
  });

  describe("setQuantity", () => {
    it("should set exact quantity", () => {
      const card = createMockCard();
      useDeckStore.getState().addCard(card);
      useDeckStore.getState().setQuantity(card.id, 3);

      const state = useDeckStore.getState();
      expect(state.cards[0].quantity).toBe(3);
      expect(state.isModified).toBe(true);
    });

    it("should remove card when quantity set to 0", () => {
      const card = createMockCard();
      useDeckStore.getState().addCard(card);
      useDeckStore.getState().setQuantity(card.id, 0);

      const state = useDeckStore.getState();
      expect(state.cards).toHaveLength(0);
    });

    it("should remove card when quantity set to negative", () => {
      const card = createMockCard();
      useDeckStore.getState().addCard(card);
      useDeckStore.getState().setQuantity(card.id, -1);

      const state = useDeckStore.getState();
      expect(state.cards).toHaveLength(0);
    });

    it("should enforce 4-card limit for non-basic-energy", () => {
      const card = createMockCard();
      useDeckStore.getState().addCard(card);
      useDeckStore.getState().setQuantity(card.id, 10);

      const state = useDeckStore.getState();
      expect(state.cards[0].quantity).toBe(4);
    });

    it("should allow any quantity for basic energy", () => {
      const energy = createBasicEnergyCard();
      useDeckStore.getState().addCard(energy);
      useDeckStore.getState().setQuantity(energy.id, 20);

      const state = useDeckStore.getState();
      expect(state.cards[0].quantity).toBe(20);
    });

    it("should do nothing for non-existent card", () => {
      useDeckStore.getState().setQuantity("non-existent", 5);

      const state = useDeckStore.getState();
      expect(state.cards).toHaveLength(0);
    });

    it("should reindex positions when removing via setQuantity", () => {
      const card1 = createMockCard({ id: "card-1" });
      const card2 = createMockCard({ id: "card-2" });
      const card3 = createMockCard({ id: "card-3" });

      useDeckStore.getState().addCard(card1);
      useDeckStore.getState().addCard(card2);
      useDeckStore.getState().addCard(card3);
      useDeckStore.getState().setQuantity(card2.id, 0);

      const state = useDeckStore.getState();
      expect(state.cards).toHaveLength(2);
      expect(state.cards[0].position).toBe(0);
      expect(state.cards[1].position).toBe(1);
    });
  });

  describe("metadata actions", () => {
    it("should set name and mark modified", () => {
      useDeckStore.getState().setName("My Deck");

      const state = useDeckStore.getState();
      expect(state.name).toBe("My Deck");
      expect(state.isModified).toBe(true);
    });

    it("should set description and mark modified", () => {
      useDeckStore.getState().setDescription("A great deck");

      const state = useDeckStore.getState();
      expect(state.description).toBe("A great deck");
      expect(state.isModified).toBe(true);
    });

    it("should set format and mark modified", () => {
      useDeckStore.getState().setFormat("expanded");

      const state = useDeckStore.getState();
      expect(state.format).toBe("expanded");
      expect(state.isModified).toBe(true);
    });
  });

  describe("clearDeck", () => {
    it("should remove all cards and mark modified", () => {
      const card = createMockCard();
      useDeckStore.getState().addCard(card);
      useDeckStore.getState().clearDeck();

      const state = useDeckStore.getState();
      expect(state.cards).toHaveLength(0);
      expect(state.isModified).toBe(true);
    });
  });

  describe("loadDeck", () => {
    it("should load deck state and set isModified to false", () => {
      const card = createMockCard();
      const deckToLoad = {
        cards: [{ card, quantity: 2, position: 0 }],
        name: "Loaded Deck",
        description: "A saved deck",
        format: "expanded" as const,
      };

      useDeckStore.getState().loadDeck(deckToLoad);

      const state = useDeckStore.getState();
      expect(state.cards).toHaveLength(1);
      expect(state.cards[0].quantity).toBe(2);
      expect(state.name).toBe("Loaded Deck");
      expect(state.description).toBe("A saved deck");
      expect(state.format).toBe("expanded");
      expect(state.isModified).toBe(false);
    });

    it("should replace existing state when loading", () => {
      // Set up initial state
      useDeckStore.getState().setName("Old Deck");
      useDeckStore.getState().addCard(createMockCard({ id: "old-card" }));

      // Load new deck
      const newCard = createMockCard({ id: "new-card" });
      useDeckStore.getState().loadDeck({
        cards: [{ card: newCard, quantity: 3, position: 0 }],
        name: "New Deck",
        description: "",
        format: "standard",
      });

      const state = useDeckStore.getState();
      expect(state.cards).toHaveLength(1);
      expect(state.cards[0].card.id).toBe("new-card");
      expect(state.name).toBe("New Deck");
      expect(state.isModified).toBe(false);
    });

    it("should allow loading an empty deck", () => {
      useDeckStore.getState().addCard(createMockCard());

      useDeckStore.getState().loadDeck({
        cards: [],
        name: "Empty Deck",
        description: "",
        format: "standard",
      });

      const state = useDeckStore.getState();
      expect(state.cards).toHaveLength(0);
      expect(state.name).toBe("Empty Deck");
      expect(state.isModified).toBe(false);
    });
  });

  describe("resetModified", () => {
    it("should reset modified flag", () => {
      useDeckStore.getState().setName("Test");
      expect(useDeckStore.getState().isModified).toBe(true);

      useDeckStore.getState().resetModified();
      expect(useDeckStore.getState().isModified).toBe(false);
    });
  });
});
