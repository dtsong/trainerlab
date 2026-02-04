import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MatchupSpread, type MatchupData } from "../MatchupSpread";

describe("MatchupSpread", () => {
  const mockMatchups: MatchupData[] = [
    {
      opponent: "Lugia VSTAR",
      winRate: 0.6,
      sampleSize: 120,
      confidence: "high",
    },
    {
      opponent: "Gardevoir ex",
      winRate: 0.45,
      sampleSize: 80,
      confidence: "high",
    },
    {
      opponent: "Lost Zone Box",
      winRate: 0.5,
      sampleSize: 30,
      confidence: "medium",
    },
    {
      opponent: "Rogue Deck",
      winRate: 0.7,
      sampleSize: 10,
      confidence: "low",
    },
  ];

  it("should render matchup opponent names", () => {
    render(<MatchupSpread matchups={mockMatchups} />);

    expect(screen.getByText("Lugia VSTAR")).toBeInTheDocument();
    expect(screen.getByText("Gardevoir ex")).toBeInTheDocument();
    expect(screen.getByText("Lost Zone Box")).toBeInTheDocument();
    expect(screen.getByText("Rogue Deck")).toBeInTheDocument();
  });

  it("should render win rate percentages", () => {
    render(<MatchupSpread matchups={mockMatchups} />);

    expect(screen.getByText("60%")).toBeInTheDocument();
    expect(screen.getByText("45%")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByText("70%")).toBeInTheDocument();
  });

  it("should render sample sizes", () => {
    render(<MatchupSpread matchups={mockMatchups} />);

    expect(screen.getByText("n=120")).toBeInTheDocument();
    expect(screen.getByText("n=80")).toBeInTheDocument();
    expect(screen.getByText("n=30")).toBeInTheDocument();
    expect(screen.getByText("n=10")).toBeInTheDocument();
  });

  it("should show empty state when no matchups", () => {
    render(<MatchupSpread matchups={[]} />);

    expect(
      screen.getByText("No matchup data available yet")
    ).toBeInTheDocument();
  });

  it("should render confidence explanation text", () => {
    render(<MatchupSpread matchups={mockMatchups} />);

    expect(
      screen.getByText(/Based on tournament results/i)
    ).toBeInTheDocument();
  });

  it("should limit displayed matchups to 5", () => {
    const manyMatchups: MatchupData[] = Array.from({ length: 8 }, (_, i) => ({
      opponent: `Opponent ${i + 1}`,
      winRate: 0.5 + i * 0.02,
      sampleSize: 50 + i * 10,
      confidence: "high" as const,
    }));

    render(<MatchupSpread matchups={manyMatchups} />);

    expect(screen.getByText("Opponent 5")).toBeInTheDocument();
    expect(screen.queryByText("Opponent 6")).not.toBeInTheDocument();
  });

  it("should show sample size as title attribute", () => {
    render(<MatchupSpread matchups={mockMatchups} />);

    const sampleSizeEl = screen.getByText("n=120");
    expect(sampleSizeEl.closest("[title]")).toHaveAttribute(
      "title",
      "120 games"
    );
  });

  it("should apply custom className", () => {
    const { container } = render(
      <MatchupSpread matchups={mockMatchups} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });

  it("should not render confidence text when matchups are empty", () => {
    render(<MatchupSpread matchups={[]} />);

    expect(
      screen.queryByText(/Based on tournament results/i)
    ).not.toBeInTheDocument();
  });
});
