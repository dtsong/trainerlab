import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { CardGrid } from "../CardGrid";
import type { ApiCardSummary } from "@trainerlab/shared-types";

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

function createMockCardSummary(
  overrides: Partial<ApiCardSummary> = {}
): ApiCardSummary {
  return {
    id: "sv1-1",
    name: "Pikachu",
    supertype: "Pokemon",
    set_id: "sv1",
    image_small: "https://example.com/small.png",
    ...overrides,
  };
}

describe("CardGrid", () => {
  describe("empty state", () => {
    it("should show empty message when cards array is empty", () => {
      render(<CardGrid cards={[]} />);

      expect(screen.getByText("No cards found")).toBeInTheDocument();
      expect(
        screen.getByText("Try adjusting your search or filters")
      ).toBeInTheDocument();
    });
  });

  describe("card rendering", () => {
    it("should render cards in a grid", () => {
      const cards = [
        createMockCardSummary({ id: "sv1-1", name: "Pikachu" }),
        createMockCardSummary({ id: "sv1-2", name: "Charizard" }),
        createMockCardSummary({ id: "sv1-3", name: "Blastoise" }),
      ];
      render(<CardGrid cards={cards} />);

      expect(screen.getByText("Pikachu")).toBeInTheDocument();
      expect(screen.getByText("Charizard")).toBeInTheDocument();
      expect(screen.getByText("Blastoise")).toBeInTheDocument();
    });

    it("should render card links with correct href", () => {
      const cards = [createMockCardSummary({ id: "sv1-25", name: "Pikachu" })];
      render(<CardGrid cards={cards} />);

      const link = screen.getByRole("link", { name: /Pikachu/i });
      expect(link).toHaveAttribute("href", "/investigate/card/sv1-25");
    });

    it("should render card images with alt text", () => {
      const cards = [
        createMockCardSummary({
          id: "sv1-1",
          name: "Pikachu",
          image_small: "https://example.com/pikachu.png",
        }),
      ];
      render(<CardGrid cards={cards} />);

      expect(screen.getByAltText("Pikachu")).toBeInTheDocument();
    });

    it("should display card supertype", () => {
      const cards = [
        createMockCardSummary({
          id: "sv1-1",
          name: "Pikachu",
          supertype: "Pokemon",
        }),
      ];
      render(<CardGrid cards={cards} />);

      expect(screen.getByText(/Pokemon/)).toBeInTheDocument();
    });

    it("should display card types when available", () => {
      const cards = [
        createMockCardSummary({
          id: "sv1-1",
          name: "Pikachu",
          supertype: "Pokemon",
          types: ["Lightning"],
        }),
      ];
      render(<CardGrid cards={cards} />);

      expect(screen.getByText("Pokemon - Lightning")).toBeInTheDocument();
    });

    it("should display multiple types joined by slash", () => {
      const cards = [
        createMockCardSummary({
          id: "sv1-1",
          name: "Dual Type Card",
          supertype: "Pokemon",
          types: ["Fire", "Water"],
        }),
      ];
      render(<CardGrid cards={cards} />);

      expect(screen.getByText("Pokemon - Fire/Water")).toBeInTheDocument();
    });

    it("should handle cards with null types", () => {
      const cards = [
        createMockCardSummary({
          id: "sv1-1",
          name: "Trainer Card",
          supertype: "Trainer",
          types: null,
        }),
      ];
      render(<CardGrid cards={cards} />);

      expect(screen.getByText("Trainer")).toBeInTheDocument();
    });

    it("should handle cards with empty types array", () => {
      const cards = [
        createMockCardSummary({
          id: "sv1-1",
          name: "Energy Card",
          supertype: "Energy",
          types: [],
        }),
      ];
      render(<CardGrid cards={cards} />);

      expect(screen.getByText("Energy")).toBeInTheDocument();
    });
  });

  describe("className handling", () => {
    it("should accept custom className", () => {
      const cards = [createMockCardSummary()];
      const { container } = render(
        <CardGrid cards={cards} className="custom-grid" />
      );

      expect(container.firstChild).toHaveClass("custom-grid");
    });

    it("should not apply grid className to empty state", () => {
      const { container } = render(
        <CardGrid cards={[]} className="custom-grid" />
      );

      // Empty state uses a different layout, not the grid
      expect(container.firstChild).not.toHaveClass("custom-grid");
    });
  });

  describe("multiple cards", () => {
    it("should render the correct number of cards", () => {
      const cards = Array.from({ length: 6 }, (_, i) =>
        createMockCardSummary({
          id: `sv1-${i + 1}`,
          name: `Card ${i + 1}`,
        })
      );
      render(<CardGrid cards={cards} />);

      const links = screen.getAllByRole("link");
      expect(links).toHaveLength(6);
    });
  });
});
