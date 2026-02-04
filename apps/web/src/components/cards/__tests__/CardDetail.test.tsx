import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { CardDetail } from "../CardDetail";
import type { ApiCard } from "@trainerlab/shared-types";

vi.mock("next/image", () => ({
  default: (props: Record<string, unknown>) => <img {...props} />,
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

function createMockCard(overrides: Partial<ApiCard> = {}): ApiCard {
  return {
    id: "sv1-1",
    local_id: "1",
    name: "Pikachu",
    supertype: "Pokemon",
    set_id: "sv1",
    image_small: "https://example.com/small.png",
    image_large: "https://example.com/large.png",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("CardDetail", () => {
  describe("basic rendering", () => {
    it("should render the card name as heading", () => {
      const card = createMockCard({ name: "Charizard ex" });
      render(<CardDetail card={card} />);

      expect(
        screen.getByRole("heading", { name: "Charizard ex" })
      ).toBeInTheDocument();
    });

    it("should render the card image", () => {
      const card = createMockCard({
        name: "Pikachu",
        image_large: "https://example.com/pikachu-large.png",
      });
      render(<CardDetail card={card} />);

      const img = screen.getByAltText("Pikachu");
      expect(img).toBeInTheDocument();
    });

    it("should render the supertype badge", () => {
      const card = createMockCard({ supertype: "Pokemon" });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Pokemon")).toBeInTheDocument();
    });

    it("should accept a custom className", () => {
      const card = createMockCard();
      const { container } = render(
        <CardDetail card={card} className="custom-class" />
      );

      expect(container.firstChild).toHaveClass("custom-class");
    });
  });

  describe("HP display", () => {
    it("should render HP badge when HP is provided", () => {
      const card = createMockCard({ hp: 120 });
      render(<CardDetail card={card} />);

      expect(screen.getByText("120 HP")).toBeInTheDocument();
    });

    it("should not render HP badge when HP is null", () => {
      const card = createMockCard({ hp: null });
      render(<CardDetail card={card} />);

      expect(screen.queryByText(/HP$/)).not.toBeInTheDocument();
    });
  });

  describe("Japanese name", () => {
    it("should render Japanese name when provided", () => {
      const card = createMockCard({ japanese_name: "ピカチュウ" });
      render(<CardDetail card={card} />);

      expect(screen.getByText("ピカチュウ")).toBeInTheDocument();
    });

    it("should not render Japanese name when null", () => {
      const card = createMockCard({ japanese_name: null });
      render(<CardDetail card={card} />);

      expect(screen.queryByText("ピカチュウ")).not.toBeInTheDocument();
    });
  });

  describe("subtypes and types", () => {
    it("should render subtypes as badges", () => {
      const card = createMockCard({ subtypes: ["Stage 1", "ex"] });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Stage 1")).toBeInTheDocument();
      expect(screen.getByText("ex")).toBeInTheDocument();
    });

    it("should render types as badges", () => {
      const card = createMockCard({ types: ["Fire", "Water"] });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Fire")).toBeInTheDocument();
      expect(screen.getByText("Water")).toBeInTheDocument();
    });

    it("should handle no subtypes", () => {
      const card = createMockCard({ subtypes: null });
      render(<CardDetail card={card} />);

      // Should render without errors
      expect(
        screen.getByRole("heading", { name: card.name })
      ).toBeInTheDocument();
    });
  });

  describe("abilities", () => {
    it("should render abilities section when abilities exist", () => {
      const card = createMockCard({
        abilities: [
          {
            name: "Volt Absorb",
            type: "Ability",
            effect: "Heals 30 damage.",
          },
        ],
      });
      render(<CardDetail card={card} />);

      expect(
        screen.getByRole("heading", { name: "Abilities" })
      ).toBeInTheDocument();
      expect(screen.getByText("Volt Absorb")).toBeInTheDocument();
      expect(screen.getByText("Ability")).toBeInTheDocument();
      expect(screen.getByText("Heals 30 damage.")).toBeInTheDocument();
    });

    it("should not render abilities section when abilities is null", () => {
      const card = createMockCard({ abilities: null });
      render(<CardDetail card={card} />);

      expect(
        screen.queryByRole("heading", { name: "Abilities" })
      ).not.toBeInTheDocument();
    });

    it("should not render abilities section when abilities is empty", () => {
      const card = createMockCard({ abilities: [] });
      render(<CardDetail card={card} />);

      expect(
        screen.queryByRole("heading", { name: "Abilities" })
      ).not.toBeInTheDocument();
    });
  });

  describe("attacks", () => {
    it("should render attacks section when attacks exist", () => {
      const card = createMockCard({
        attacks: [
          {
            name: "Thunderbolt",
            cost: ["Lightning", "Colorless"],
            damage: "120",
            effect: "Discard all Energy.",
          },
        ],
      });
      render(<CardDetail card={card} />);

      expect(
        screen.getByRole("heading", { name: "Attacks" })
      ).toBeInTheDocument();
      expect(screen.getByText("Thunderbolt")).toBeInTheDocument();
      expect(screen.getByText("120")).toBeInTheDocument();
      expect(
        screen.getByText("Cost: Lightning, Colorless")
      ).toBeInTheDocument();
      expect(screen.getByText("Discard all Energy.")).toBeInTheDocument();
    });

    it("should not render attacks section when attacks is null", () => {
      const card = createMockCard({ attacks: null });
      render(<CardDetail card={card} />);

      expect(
        screen.queryByRole("heading", { name: "Attacks" })
      ).not.toBeInTheDocument();
    });

    it("should not render attacks section when attacks is empty", () => {
      const card = createMockCard({ attacks: [] });
      render(<CardDetail card={card} />);

      expect(
        screen.queryByRole("heading", { name: "Attacks" })
      ).not.toBeInTheDocument();
    });

    it("should render attack without damage", () => {
      const card = createMockCard({
        attacks: [
          {
            name: "Growl",
            cost: ["Colorless"],
            damage: null,
            effect: "Reduces damage.",
          },
        ],
      });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Growl")).toBeInTheDocument();
      expect(screen.getByText("Reduces damage.")).toBeInTheDocument();
    });
  });

  describe("details section", () => {
    it("should render set name", () => {
      const card = createMockCard({
        set: {
          id: "sv1",
          name: "Scarlet & Violet",
          series: "Scarlet & Violet",
        },
      });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Set")).toBeInTheDocument();
      expect(screen.getByText("Scarlet & Violet")).toBeInTheDocument();
    });

    it("should render set_id when set name is unavailable", () => {
      const card = createMockCard({ set: null, set_id: "sv1" });
      render(<CardDetail card={card} />);

      expect(screen.getByText("sv1")).toBeInTheDocument();
    });

    it("should render card number", () => {
      const card = createMockCard({ number: "025" });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Number")).toBeInTheDocument();
      expect(screen.getByText("025")).toBeInTheDocument();
    });

    it("should render rarity", () => {
      const card = createMockCard({ rarity: "Rare Holo" });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Rarity")).toBeInTheDocument();
      expect(screen.getByText("Rare Holo")).toBeInTheDocument();
    });

    it("should render evolves_from", () => {
      const card = createMockCard({ evolves_from: "Pichu" });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Evolves From")).toBeInTheDocument();
      expect(screen.getByText("Pichu")).toBeInTheDocument();
    });

    it("should render evolves_to", () => {
      const card = createMockCard({ evolves_to: ["Raichu", "Raichu GX"] });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Evolves To")).toBeInTheDocument();
      expect(screen.getByText("Raichu, Raichu GX")).toBeInTheDocument();
    });

    it("should render retreat cost", () => {
      const card = createMockCard({ retreat_cost: 2 });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Retreat Cost")).toBeInTheDocument();
      expect(screen.getByText("2")).toBeInTheDocument();
    });

    it("should render weaknesses", () => {
      const card = createMockCard({
        weaknesses: [{ type: "Fighting", value: "x2" }],
      });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Weakness")).toBeInTheDocument();
      expect(screen.getByText("Fighting x2")).toBeInTheDocument();
    });

    it("should render resistances", () => {
      const card = createMockCard({
        resistances: [{ type: "Metal", value: "-30" }],
      });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Resistance")).toBeInTheDocument();
      expect(screen.getByText("Metal -30")).toBeInTheDocument();
    });

    it("should render regulation mark", () => {
      const card = createMockCard({ regulation_mark: "G" });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Regulation Mark")).toBeInTheDocument();
      expect(screen.getByText("G")).toBeInTheDocument();
    });
  });

  describe("format legality", () => {
    it("should show Standard: Legal when standard is true", () => {
      const card = createMockCard({
        legalities: { standard: true, expanded: false },
      });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Standard: Legal")).toBeInTheDocument();
      expect(screen.getByText("Expanded: Not Legal")).toBeInTheDocument();
    });

    it("should show Expanded: Legal when expanded is true", () => {
      const card = createMockCard({
        legalities: { standard: false, expanded: true },
      });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Standard: Not Legal")).toBeInTheDocument();
      expect(screen.getByText("Expanded: Legal")).toBeInTheDocument();
    });

    it("should show Not Legal for both when legalities is null", () => {
      const card = createMockCard({ legalities: null });
      render(<CardDetail card={card} />);

      expect(screen.getByText("Standard: Not Legal")).toBeInTheDocument();
      expect(screen.getByText("Expanded: Not Legal")).toBeInTheDocument();
    });
  });

  describe("rules", () => {
    it("should render rules section when rules exist", () => {
      const card = createMockCard({
        rules: [
          "When your Pokemon ex is Knocked Out, your opponent takes 2 Prize cards.",
        ],
      });
      render(<CardDetail card={card} />);

      expect(
        screen.getByRole("heading", { name: "Rules" })
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "When your Pokemon ex is Knocked Out, your opponent takes 2 Prize cards."
        )
      ).toBeInTheDocument();
    });

    it("should not render rules section when rules is null", () => {
      const card = createMockCard({ rules: null });
      render(<CardDetail card={card} />);

      expect(
        screen.queryByRole("heading", { name: "Rules" })
      ).not.toBeInTheDocument();
    });

    it("should not render rules section when rules is empty", () => {
      const card = createMockCard({ rules: [] });
      render(<CardDetail card={card} />);

      expect(
        screen.queryByRole("heading", { name: "Rules" })
      ).not.toBeInTheDocument();
    });

    it("should render multiple rules as list items", () => {
      const card = createMockCard({
        rules: ["Rule one.", "Rule two."],
      });
      render(<CardDetail card={card} />);

      const listItems = screen.getAllByRole("listitem");
      expect(listItems).toHaveLength(2);
      expect(screen.getByText("Rule one.")).toBeInTheDocument();
      expect(screen.getByText("Rule two.")).toBeInTheDocument();
    });
  });
});
