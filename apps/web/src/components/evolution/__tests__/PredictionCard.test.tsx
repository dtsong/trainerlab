import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PredictionCard } from "../PredictionCard";
import type { ApiArchetypePrediction } from "@trainerlab/shared-types";

const mockPrediction: ApiArchetypePrediction = {
  id: "pred-1",
  archetype_id: "charizard-ex",
  target_tournament_id: "t-1",
  predicted_meta_share: { low: 0.08, mid: 0.12, high: 0.16 },
  predicted_day2_rate: { low: 0.15, mid: 0.22, high: 0.3 },
  predicted_tier: "A",
  likely_adaptations: [
    { type: "tech", description: "Counter Catcher tech" },
    { description: "Increase Rare Candy count" },
  ],
  confidence: 0.78,
  methodology: null,
  actual_meta_share: null,
  accuracy_score: null,
  created_at: "2024-06-01T00:00:00Z",
};

describe("PredictionCard", () => {
  it("should render the prediction title", () => {
    render(<PredictionCard prediction={mockPrediction} />);

    expect(screen.getByText("Prediction")).toBeInTheDocument();
  });

  it("should render tier badge for valid tiers", () => {
    render(<PredictionCard prediction={mockPrediction} />);

    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("should not render tier badge for invalid tiers", () => {
    const invalidTier: ApiArchetypePrediction = {
      ...mockPrediction,
      predicted_tier: "Unknown",
    };

    render(<PredictionCard prediction={invalidTier} />);

    expect(screen.queryByText("Unknown")).not.toBeInTheDocument();
  });

  it("should not render tier badge when tier is null", () => {
    const noTier: ApiArchetypePrediction = {
      ...mockPrediction,
      predicted_tier: null,
    };

    render(<PredictionCard prediction={noTier} />);

    // Should still render the card without crashing
    expect(screen.getByText("Prediction")).toBeInTheDocument();
  });

  it("should display expected meta share range", () => {
    render(<PredictionCard prediction={mockPrediction} />);

    expect(screen.getByText("Expected Meta Share")).toBeInTheDocument();
    expect(screen.getByText("8.0% - 16.0%")).toBeInTheDocument();
    expect(screen.getByText("Most likely: 12.0%")).toBeInTheDocument();
  });

  it("should display expected day 2 rate range", () => {
    render(<PredictionCard prediction={mockPrediction} />);

    expect(screen.getByText("Expected Day 2 Rate")).toBeInTheDocument();
    expect(screen.getByText("15.0% - 30.0%")).toBeInTheDocument();
  });

  it("should display confidence progress bar", () => {
    render(<PredictionCard prediction={mockPrediction} />);

    expect(screen.getByText("Confidence")).toBeInTheDocument();
    expect(screen.getByText("78%")).toBeInTheDocument();
  });

  it("should not display confidence when null", () => {
    const noConfidence: ApiArchetypePrediction = {
      ...mockPrediction,
      confidence: null,
    };

    render(<PredictionCard prediction={noConfidence} />);

    expect(screen.queryByText("Confidence")).not.toBeInTheDocument();
  });

  it("should not display meta share section when null", () => {
    const noMetaShare: ApiArchetypePrediction = {
      ...mockPrediction,
      predicted_meta_share: null,
    };

    render(<PredictionCard prediction={noMetaShare} />);

    expect(screen.queryByText("Expected Meta Share")).not.toBeInTheDocument();
  });

  it("should not display day 2 rate section when null", () => {
    const noDay2: ApiArchetypePrediction = {
      ...mockPrediction,
      predicted_day2_rate: null,
    };

    render(<PredictionCard prediction={noDay2} />);

    expect(screen.queryByText("Expected Day 2 Rate")).not.toBeInTheDocument();
  });

  it("should render likely adaptations", () => {
    render(<PredictionCard prediction={mockPrediction} />);

    expect(screen.getByText("Expected Adaptations")).toBeInTheDocument();
    expect(screen.getByText("Counter Catcher tech")).toBeInTheDocument();
    expect(screen.getByText("Increase Rare Candy count")).toBeInTheDocument();
  });

  it("should not render adaptations section when empty", () => {
    const noAdaptations: ApiArchetypePrediction = {
      ...mockPrediction,
      likely_adaptations: null,
    };

    render(<PredictionCard prediction={noAdaptations} />);

    expect(screen.queryByText("Expected Adaptations")).not.toBeInTheDocument();
  });

  it("should not render adaptations section when array is empty", () => {
    const emptyAdaptations: ApiArchetypePrediction = {
      ...mockPrediction,
      likely_adaptations: [],
    };

    render(<PredictionCard prediction={emptyAdaptations} />);

    expect(screen.queryByText("Expected Adaptations")).not.toBeInTheDocument();
  });

  it("should display actual result when resolved", () => {
    const resolved: ApiArchetypePrediction = {
      ...mockPrediction,
      actual_meta_share: 0.115,
      accuracy_score: 0.85,
    };

    render(<PredictionCard prediction={resolved} />);

    expect(screen.getByText(/Actual result:/)).toBeInTheDocument();
    expect(screen.getByText("11.5%")).toBeInTheDocument();
    expect(screen.getByText("(85% accurate)")).toBeInTheDocument();
  });

  it("should not display actual result when not resolved", () => {
    render(<PredictionCard prediction={mockPrediction} />);

    expect(screen.queryByText(/Actual result:/)).not.toBeInTheDocument();
  });

  it("should display actual result without accuracy when score is null", () => {
    const noAccuracy: ApiArchetypePrediction = {
      ...mockPrediction,
      actual_meta_share: 0.1,
      accuracy_score: null,
    };

    render(<PredictionCard prediction={noAccuracy} />);

    expect(screen.getByText(/Actual result:/)).toBeInTheDocument();
    expect(screen.getByText("10.0%")).toBeInTheDocument();
    expect(screen.queryByText(/accurate/)).not.toBeInTheDocument();
  });

  it("should apply custom className", () => {
    const { container } = render(
      <PredictionCard prediction={mockPrediction} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });

  it("should render all valid tier types", () => {
    const tiers = ["S", "A", "B", "C", "Rogue"] as const;

    for (const tier of tiers) {
      const prediction: ApiArchetypePrediction = {
        ...mockPrediction,
        predicted_tier: tier,
      };

      const { unmount } = render(<PredictionCard prediction={prediction} />);
      expect(screen.getByText(tier)).toBeInTheDocument();
      unmount();
    }
  });

  it("should handle adaptation with only type and no description", () => {
    const typeOnly: ApiArchetypePrediction = {
      ...mockPrediction,
      likely_adaptations: [{ type: "removal" }],
    };

    render(<PredictionCard prediction={typeOnly} />);

    expect(screen.getByText("removal")).toBeInTheDocument();
  });

  it("should show 'Unknown' for adaptation without type or description", () => {
    const noTypeOrDesc: ApiArchetypePrediction = {
      ...mockPrediction,
      likely_adaptations: [{}],
    };

    render(<PredictionCard prediction={noTypeOrDesc} />);

    expect(screen.getByText("Unknown")).toBeInTheDocument();
  });
});
