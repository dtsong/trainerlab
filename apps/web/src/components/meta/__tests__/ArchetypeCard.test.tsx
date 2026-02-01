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

  it("should show 'No key cards defined' when no key cards", () => {
    const archetypeWithoutCards: Archetype = {
      name: "Rogue Deck",
      share: 0.02,
    };

    render(<ArchetypeCard archetype={archetypeWithoutCards} />);

    expect(screen.getByText("No key cards defined")).toBeInTheDocument();
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
});
