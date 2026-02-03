import { describe, it, expect, beforeEach } from "vitest";
import { useDeckStore } from "../deckStore";
import type { ApiCardSummary } from "@trainerlab/shared-types";

// Helper to create mock cards
function createMockCard(
  overrides: Partial<ApiCardSummary> = {}
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

    it("should clear name and description", () => {
      useDeckStore.getState().setName("My Deck");
      useDeckStore.getState().setDescription("A test deck");
      useDeckStore.getState().addCard(createMockCard());

      useDeckStore.getState().clearDeck();

      const state = useDeckStore.getState();
      expect(state.name).toBe("");
      expect(state.description).toBe("");
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

  describe("computed getters", () => {
    describe("totalCards", () => {
      it("should return 0 for empty deck", () => {
        expect(useDeckStore.getState().totalCards()).toBe(0);
      });

      it("should sum quantities of all cards", () => {
        useDeckStore.getState().addCard(createMockCard({ id: "card-1" }));
        useDeckStore.getState().addCard(createMockCard({ id: "card-1" })); // qty 2
        useDeckStore.getState().addCard(createMockCard({ id: "card-2" })); // qty 1
        expect(useDeckStore.getState().totalCards()).toBe(3);
      });
    });

    describe("pokemonCount", () => {
      it("should count only Pokemon cards", () => {
        useDeckStore
          .getState()
          .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));
        useDeckStore
          .getState()
          .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));
        useDeckStore
          .getState()
          .addCard(createMockCard({ id: "t1", supertype: "Trainer" }));
        expect(useDeckStore.getState().pokemonCount()).toBe(2);
      });
    });

    describe("trainerCount", () => {
      it("should count only Trainer cards", () => {
        useDeckStore
          .getState()
          .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));
        useDeckStore
          .getState()
          .addCard(createMockCard({ id: "t1", supertype: "Trainer" }));
        useDeckStore
          .getState()
          .addCard(createMockCard({ id: "t1", supertype: "Trainer" }));
        useDeckStore
          .getState()
          .addCard(createMockCard({ id: "t1", supertype: "Trainer" }));
        expect(useDeckStore.getState().trainerCount()).toBe(3);
      });
    });

    describe("energyCount", () => {
      it("should count only Energy cards", () => {
        useDeckStore
          .getState()
          .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));
        useDeckStore.getState().addCard(createBasicEnergyCard());
        useDeckStore.getState().addCard(createBasicEnergyCard());
        expect(useDeckStore.getState().energyCount()).toBe(2);
      });
    });

    describe("supertypeCounts", () => {
      it("should return counts by supertype", () => {
        useDeckStore
          .getState()
          .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));
        useDeckStore
          .getState()
          .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));
        useDeckStore
          .getState()
          .addCard(createMockCard({ id: "t1", supertype: "Trainer" }));
        useDeckStore.getState().addCard(createBasicEnergyCard());

        const counts = useDeckStore.getState().supertypeCounts();
        expect(counts).toEqual({
          Pokemon: 2,
          Trainer: 1,
          Energy: 1,
        });
      });

      it("should return zeros for empty deck", () => {
        const counts = useDeckStore.getState().supertypeCounts();
        expect(counts).toEqual({
          Pokemon: 0,
          Trainer: 0,
          Energy: 0,
        });
      });
    });

    describe("isValid", () => {
      it("should return false for empty deck", () => {
        expect(useDeckStore.getState().isValid()).toBe(false);
      });

      it("should return false for deck with < 60 cards", () => {
        for (let i = 0; i < 10; i++) {
          useDeckStore.getState().addCard(createBasicEnergyCard());
        }
        expect(useDeckStore.getState().isValid()).toBe(false);
      });

      it("should return true for deck with exactly 60 cards", () => {
        // Add 60 basic energy cards
        const energy = createBasicEnergyCard();
        for (let i = 0; i < 60; i++) {
          useDeckStore.getState().addCard(energy);
        }
        expect(useDeckStore.getState().isValid()).toBe(true);
      });
    });

    describe("cardsByType", () => {
      it("should group cards by supertype", () => {
        const pokemon = createMockCard({
          id: "p1",
          supertype: "Pokemon",
          name: "Pikachu",
        });
        const trainer = createMockCard({
          id: "t1",
          supertype: "Trainer",
          name: "Pokeball",
        });
        const energy = createBasicEnergyCard();

        useDeckStore.getState().addCard(pokemon);
        useDeckStore.getState().addCard(trainer);
        useDeckStore.getState().addCard(energy);

        const grouped = useDeckStore.getState().cardsByType();
        expect(grouped.Pokemon).toHaveLength(1);
        expect(grouped.Trainer).toHaveLength(1);
        expect(grouped.Energy).toHaveLength(1);
        expect(grouped.Pokemon[0].card.name).toBe("Pikachu");
      });

      it("should return empty arrays for missing types", () => {
        useDeckStore
          .getState()
          .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));
        const grouped = useDeckStore.getState().cardsByType();
        expect(grouped.Pokemon).toHaveLength(1);
        expect(grouped.Trainer).toHaveLength(0);
        expect(grouped.Energy).toHaveLength(0);
      });
    });
  });
});
