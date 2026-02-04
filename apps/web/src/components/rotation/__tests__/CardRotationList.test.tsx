import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CardRotationList } from "../CardRotationList";

import type { ApiRotationImpact } from "@trainerlab/shared-types";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

// Mock next/image
vi.mock("next/image", () => ({
  default: (props: React.ImgHTMLAttributes<HTMLImageElement>) => (
    <img {...props} />
  ),
}));

describe("CardRotationList", () => {
  const mockImpacts: ApiRotationImpact[] = [
    {
      id: "impact-1",
      format_transition: "F-to-G",
      archetype_id: "arch-1",
      archetype_name: "Charizard ex",
      survival_rating: "adapts",
      rotating_cards: [
        { card_name: "Battle VIP Pass", count: 4, role: "consistency" },
        { card_name: "Forest Seal Stone", count: 1, role: "finisher" },
      ],
    },
    {
      id: "impact-2",
      format_transition: "F-to-G",
      archetype_id: "arch-2",
      archetype_name: "Lugia VSTAR",
      survival_rating: "dies",
      rotating_cards: [
        { card_name: "Battle VIP Pass", count: 4, role: "consistency" },
        { card_name: "Archeops", count: 2, role: "engine" },
      ],
    },
    {
      id: "impact-3",
      format_transition: "F-to-G",
      archetype_id: "arch-3",
      archetype_name: "Gardevoir ex",
      survival_rating: "thrives",
      rotating_cards: [
        { card_name: "Forest Seal Stone", count: 1, role: "utility" },
      ],
    },
  ];

  it("should render the search input", () => {
    render(<CardRotationList impacts={mockImpacts} />);

    expect(
      screen.getByPlaceholderText("Search cards or archetypes...")
    ).toBeInTheDocument();
  });

  it("should display the total card count", () => {
    render(<CardRotationList impacts={mockImpacts} />);

    // Battle VIP Pass (2 archetypes), Forest Seal Stone (2 archetypes), Archeops (1 archetype) = 3 unique cards
    expect(screen.getByText("3 cards rotating")).toBeInTheDocument();
  });

  it("should render card names", () => {
    render(<CardRotationList impacts={mockImpacts} />);

    expect(screen.getByText("Battle VIP Pass")).toBeInTheDocument();
    expect(screen.getByText("Forest Seal Stone")).toBeInTheDocument();
    expect(screen.getByText("Archeops")).toBeInTheDocument();
  });

  it("should display archetype badges for each card", () => {
    render(<CardRotationList impacts={mockImpacts} />);

    // Battle VIP Pass appears in Charizard ex and Lugia VSTAR
    const charizardBadges = screen.getAllByText("Charizard ex");
    expect(charizardBadges.length).toBeGreaterThanOrEqual(1);
    // Lugia VSTAR appears in both Battle VIP Pass and Archeops
    const lugiaBadges = screen.getAllByText("Lugia VSTAR");
    expect(lugiaBadges.length).toBeGreaterThanOrEqual(1);
  });

  it("should show 'archetypes affected' count for each card", () => {
    render(<CardRotationList impacts={mockImpacts} />);

    // Battle VIP Pass and Forest Seal Stone each affect 2 archetypes
    const twoArchetypeLabels = screen.getAllByText("2 archetypes affected");
    expect(twoArchetypeLabels.length).toBe(2);
    // Archeops affects 1 archetype
    expect(screen.getByText("1 archetype affected")).toBeInTheDocument();
  });

  it("should sort cards by number of archetypes affected (descending)", () => {
    render(<CardRotationList impacts={mockImpacts} />);

    const cardNames = screen
      .getAllByText(/(Battle VIP Pass|Forest Seal Stone|Archeops)/)
      .filter((el) => el.classList.contains("font-medium"));

    // Battle VIP Pass (2 archetypes) and Forest Seal Stone (2 archetypes) should come before Archeops (1)
    const texts = cardNames.map((el) => el.textContent);
    const archeopsIndex = texts.indexOf("Archeops");
    const bvpIndex = texts.indexOf("Battle VIP Pass");

    expect(bvpIndex).toBeLessThan(archeopsIndex);
  });

  it("should filter cards by card name when searching", () => {
    render(<CardRotationList impacts={mockImpacts} />);

    const searchInput = screen.getByPlaceholderText(
      "Search cards or archetypes..."
    );
    fireEvent.change(searchInput, { target: { value: "Archeops" } });

    expect(screen.getByText("Archeops")).toBeInTheDocument();
    expect(screen.getByText("1 cards rotating")).toBeInTheDocument();
    expect(screen.queryByText("Battle VIP Pass")).not.toBeInTheDocument();
  });

  it("should filter cards by archetype name when searching", () => {
    render(<CardRotationList impacts={mockImpacts} />);

    const searchInput = screen.getByPlaceholderText(
      "Search cards or archetypes..."
    );
    fireEvent.change(searchInput, { target: { value: "Lugia" } });

    // Lugia VSTAR has Battle VIP Pass and Archeops
    expect(screen.getByText("Battle VIP Pass")).toBeInTheDocument();
    expect(screen.getByText("Archeops")).toBeInTheDocument();
    expect(screen.queryByText("Forest Seal Stone")).not.toBeInTheDocument();
  });

  it("should show 'No cards found' message when search yields no results", () => {
    render(<CardRotationList impacts={mockImpacts} />);

    const searchInput = screen.getByPlaceholderText(
      "Search cards or archetypes..."
    );
    fireEvent.change(searchInput, { target: { value: "Nonexistent Card" } });

    expect(screen.getByText("0 cards rotating")).toBeInTheDocument();
    expect(screen.getByText(/No cards found matching/)).toBeInTheDocument();
  });

  it("should handle empty impacts array", () => {
    render(<CardRotationList impacts={[]} />);

    expect(screen.getByText("0 cards rotating")).toBeInTheDocument();
  });

  it("should handle impacts with no rotating cards", () => {
    const impactsWithoutCards: ApiRotationImpact[] = [
      {
        id: "impact-1",
        format_transition: "F-to-G",
        archetype_id: "arch-1",
        archetype_name: "Charizard ex",
        survival_rating: "thrives",
      },
    ];

    render(<CardRotationList impacts={impactsWithoutCards} />);

    expect(screen.getByText("0 cards rotating")).toBeInTheDocument();
  });

  it("should show '+N more' when an archetype has more than 5 archetypes", () => {
    const manyArchetypeImpacts: ApiRotationImpact[] = Array.from(
      { length: 7 },
      (_, i) => ({
        id: `impact-${i}`,
        format_transition: "F-to-G",
        archetype_id: `arch-${i}`,
        archetype_name: `Archetype ${i}`,
        survival_rating: "adapts" as const,
        rotating_cards: [{ card_name: "Shared Card", count: 1 }],
      })
    );

    render(<CardRotationList impacts={manyArchetypeImpacts} />);

    expect(screen.getByText("+2 more")).toBeInTheDocument();
  });

  it("should perform case-insensitive search", () => {
    render(<CardRotationList impacts={mockImpacts} />);

    const searchInput = screen.getByPlaceholderText(
      "Search cards or archetypes..."
    );
    fireEvent.change(searchInput, { target: { value: "battle vip" } });

    expect(screen.getByText("Battle VIP Pass")).toBeInTheDocument();
  });
});
