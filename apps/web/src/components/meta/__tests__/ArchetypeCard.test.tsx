import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ArchetypeCard } from "../ArchetypeCard";
import type { Archetype } from "@trainerlab/shared-types";

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

// Mock ArchetypeSprites
vi.mock("../ArchetypeSprites", () => ({
  ArchetypeSprites: ({
    spriteUrls,
    archetypeName,
  }: {
    spriteUrls: string[];
    archetypeName: string;
  }) => (
    <span data-testid="archetype-sprites" data-name={archetypeName}>
      {spriteUrls.length} sprites
    </span>
  ),
}));

describe("ArchetypeCard", () => {
  const mockArchetype: Archetype = {
    name: "Charizard ex",
    share: 0.153,
    keyCards: ["sv4-54", "sv3-6"],
  };

  it("should render archetype name", () => {
    render(<ArchetypeCard archetype={mockArchetype} />);

    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
  });

  it("should render meta share percentage", () => {
    render(<ArchetypeCard archetype={mockArchetype} />);

    expect(screen.getByText("15.3%")).toBeInTheDocument();
  });

  it("should link to archetype detail page", () => {
    render(<ArchetypeCard archetype={mockArchetype} />);

    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/meta/archetype/Charizard%20ex");
  });

  it("should render without sprites when no spriteUrls", () => {
    const archetypeWithoutCards: Archetype = {
      name: "Rogue Deck",
      share: 0.02,
    };

    render(<ArchetypeCard archetype={archetypeWithoutCards} />);

    expect(screen.getByText("Rogue Deck")).toBeInTheDocument();
    expect(screen.queryByTestId("archetype-sprites")).not.toBeInTheDocument();
  });

  it("should have data-testid for testing", () => {
    render(<ArchetypeCard archetype={mockArchetype} />);

    expect(screen.getByTestId("archetype-card")).toBeInTheDocument();
  });

  it("should format percentage to one decimal place", () => {
    const archetypeWithLongDecimal: Archetype = {
      name: "Test Deck",
      share: 0.12345,
    };

    render(<ArchetypeCard archetype={archetypeWithLongDecimal} />);

    expect(screen.getByText("12.3%")).toBeInTheDocument();
  });

  it("should render sprites when spriteUrls are available", () => {
    const archetypeWithSprites: Archetype = {
      name: "Charizard ex",
      share: 0.15,
      spriteUrls: ["https://sprites.example.com/charizard.png"],
    };
    render(<ArchetypeCard archetype={archetypeWithSprites} />);
    expect(screen.getByTestId("archetype-sprites")).toBeInTheDocument();
  });

  it("should not render sprites when spriteUrls absent", () => {
    const archetypeNoSprites: Archetype = {
      name: "Rogue Deck",
      share: 0.02,
    };
    render(<ArchetypeCard archetype={archetypeNoSprites} />);
    expect(screen.getByText("Rogue Deck")).toBeInTheDocument();
    expect(screen.queryByTestId("archetype-sprites")).not.toBeInTheDocument();
  });

  it("should not render sprites when spriteUrls is empty array", () => {
    const archetypeEmptySprites: Archetype = {
      name: "Test Deck",
      share: 0.05,
      spriteUrls: [],
    };
    render(<ArchetypeCard archetype={archetypeEmptySprites} />);
    expect(screen.getByText("Test Deck")).toBeInTheDocument();
    expect(screen.queryByTestId("archetype-sprites")).not.toBeInTheDocument();
  });
});
