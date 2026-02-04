import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BuildDeckCTA } from "../BuildDeckCTA";

// Mock analytics
const mockTrackAffiliateClick = vi.fn();
const mockTrackBuildDeckCTA = vi.fn();
vi.mock("@/lib/analytics", () => ({
  trackAffiliateClick: (...args: unknown[]) => mockTrackAffiliateClick(...args),
  trackBuildDeckCTA: (...args: unknown[]) => mockTrackBuildDeckCTA(...args),
}));

// Mock affiliate
const mockGetDoubleHoloLink = vi.fn();
const mockGetTCGPlayerLink = vi.fn();
const mockEstimateDeckPrice = vi.fn();
vi.mock("@/lib/affiliate", () => ({
  getDoubleHoloLink: (...args: unknown[]) => mockGetDoubleHoloLink(...args),
  getTCGPlayerLink: (...args: unknown[]) => mockGetTCGPlayerLink(...args),
  estimateDeckPrice: (...args: unknown[]) => mockEstimateDeckPrice(...args),
}));

describe("BuildDeckCTA", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetDoubleHoloLink.mockReturnValue(
      "https://doubleholo.com/search?ref=trainerlab"
    );
    mockGetTCGPlayerLink.mockReturnValue(
      "https://tcgplayer.com/search/pokemon-tcg?ref=trainerlab"
    );
    mockEstimateDeckPrice.mockReturnValue({ low: 21, mid: 30, high: 45 });
  });

  it("should render the 'Build This Deck' title", () => {
    render(<BuildDeckCTA deckName="Charizard ex" />);

    expect(screen.getByText("Build This Deck")).toBeInTheDocument();
  });

  it("should display the price estimate", () => {
    render(<BuildDeckCTA deckName="Charizard ex" />);

    expect(screen.getByText(/Estimated: \$21 - \$45/)).toBeInTheDocument();
  });

  it("should render the DoubleHolo buy button", () => {
    render(<BuildDeckCTA deckName="Charizard ex" />);

    expect(screen.getByText("Buy on DoubleHolo")).toBeInTheDocument();
  });

  it("should render the TCGPlayer view button", () => {
    render(<BuildDeckCTA deckName="Charizard ex" />);

    expect(screen.getByText("View on TCGPlayer")).toBeInTheDocument();
  });

  it("should set correct href for DoubleHolo link", () => {
    render(<BuildDeckCTA deckName="Charizard ex" />);

    const doubleHoloLink = screen.getByText("Buy on DoubleHolo").closest("a");
    expect(doubleHoloLink).toHaveAttribute(
      "href",
      "https://doubleholo.com/search?ref=trainerlab"
    );
  });

  it("should set correct href for TCGPlayer link", () => {
    render(<BuildDeckCTA deckName="Charizard ex" />);

    const tcgPlayerLink = screen.getByText("View on TCGPlayer").closest("a");
    expect(tcgPlayerLink).toHaveAttribute(
      "href",
      "https://tcgplayer.com/search/pokemon-tcg?ref=trainerlab"
    );
  });

  it("should open links in new tab with noopener noreferrer", () => {
    render(<BuildDeckCTA deckName="Charizard ex" />);

    const doubleHoloLink = screen.getByText("Buy on DoubleHolo").closest("a");
    expect(doubleHoloLink).toHaveAttribute("target", "_blank");
    expect(doubleHoloLink).toHaveAttribute("rel", "noopener noreferrer");

    const tcgPlayerLink = screen.getByText("View on TCGPlayer").closest("a");
    expect(tcgPlayerLink).toHaveAttribute("target", "_blank");
    expect(tcgPlayerLink).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("should track CTA view on mount", () => {
    render(<BuildDeckCTA deckName="Charizard ex" />);

    expect(mockTrackBuildDeckCTA).toHaveBeenCalledWith("view", "Charizard ex");
  });

  it("should track affiliate click on DoubleHolo button click", () => {
    render(<BuildDeckCTA deckName="Charizard ex" deckId="deck-1" />);

    const doubleHoloLink = screen.getByText("Buy on DoubleHolo").closest("a")!;
    fireEvent.click(doubleHoloLink);

    expect(mockTrackAffiliateClick).toHaveBeenCalledWith(
      "doubleHolo",
      "deck",
      "deck-1"
    );
    expect(mockTrackBuildDeckCTA).toHaveBeenCalledWith(
      "click_primary",
      "Charizard ex"
    );
  });

  it("should track affiliate click on TCGPlayer button click", () => {
    render(<BuildDeckCTA deckName="Charizard ex" deckId="deck-1" />);

    const tcgPlayerLink = screen.getByText("View on TCGPlayer").closest("a")!;
    fireEvent.click(tcgPlayerLink);

    expect(mockTrackAffiliateClick).toHaveBeenCalledWith(
      "tcgPlayer",
      "deck",
      "deck-1"
    );
    expect(mockTrackBuildDeckCTA).toHaveBeenCalledWith(
      "click_secondary",
      "Charizard ex"
    );
  });

  it("should pass deckName and deckId to affiliate link generators", () => {
    render(<BuildDeckCTA deckName="Lugia VSTAR" deckId="deck-2" />);

    expect(mockGetDoubleHoloLink).toHaveBeenCalledWith("Lugia VSTAR", "deck-2");
    expect(mockGetTCGPlayerLink).toHaveBeenCalledWith("Lugia VSTAR", "deck-2");
  });

  it("should pass default cardCount of 60 to estimateDeckPrice", () => {
    render(<BuildDeckCTA deckName="Charizard ex" />);

    expect(mockEstimateDeckPrice).toHaveBeenCalledWith(60);
  });

  it("should pass custom cardCount to estimateDeckPrice", () => {
    render(<BuildDeckCTA deckName="Charizard ex" cardCount={40} />);

    expect(mockEstimateDeckPrice).toHaveBeenCalledWith(40);
  });

  it("should display the disclaimer text", () => {
    render(<BuildDeckCTA deckName="Charizard ex" />);

    expect(
      screen.getByText(
        "Prices are estimates. TrainerLab may earn a commission from purchases."
      )
    ).toBeInTheDocument();
  });

  it("should apply custom className to the card", () => {
    const { container } = render(
      <BuildDeckCTA deckName="Charizard ex" className="custom-class" />
    );

    // The outermost Card element should have the custom class
    const card = container.firstChild;
    expect(card).toHaveClass("custom-class");
  });

  it("should call getDoubleHoloLink with undefined deckId when not provided", () => {
    render(<BuildDeckCTA deckName="Charizard ex" />);

    expect(mockGetDoubleHoloLink).toHaveBeenCalledWith(
      "Charizard ex",
      undefined
    );
  });

  it("should re-track CTA view when deckName changes", () => {
    const { rerender } = render(<BuildDeckCTA deckName="Charizard ex" />);

    expect(mockTrackBuildDeckCTA).toHaveBeenCalledWith("view", "Charizard ex");

    mockTrackBuildDeckCTA.mockClear();

    rerender(<BuildDeckCTA deckName="Lugia VSTAR" />);

    expect(mockTrackBuildDeckCTA).toHaveBeenCalledWith("view", "Lugia VSTAR");
  });
});
