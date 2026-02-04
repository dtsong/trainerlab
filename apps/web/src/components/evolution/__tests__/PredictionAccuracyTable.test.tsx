import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PredictionAccuracyTable } from "../PredictionAccuracyTable";
import { safeFormatDate } from "@/lib/date-utils";
import type { ApiArchetypePrediction } from "@trainerlab/shared-types";

const mockPredictions: ApiArchetypePrediction[] = [
  {
    id: "pred-1",
    archetype_id: "Charizard ex",
    target_tournament_id: "t-1",
    predicted_meta_share: { low: 0.08, mid: 0.12, high: 0.16 },
    predicted_day2_rate: null,
    predicted_tier: "A",
    likely_adaptations: null,
    confidence: null,
    methodology: null,
    actual_meta_share: 0.115,
    accuracy_score: 0.92,
    created_at: "2024-06-01T00:00:00Z",
  },
  {
    id: "pred-2",
    archetype_id: "Lugia VSTAR",
    target_tournament_id: "t-1",
    predicted_meta_share: { low: 0.05, mid: 0.08, high: 0.11 },
    predicted_day2_rate: null,
    predicted_tier: "B",
    likely_adaptations: null,
    confidence: null,
    methodology: null,
    actual_meta_share: 0.03,
    accuracy_score: 0.45,
    created_at: "2024-06-01T00:00:00Z",
  },
  {
    id: "pred-3",
    archetype_id: "Gardevoir ex",
    target_tournament_id: "t-1",
    predicted_meta_share: null,
    predicted_day2_rate: null,
    predicted_tier: "S",
    likely_adaptations: null,
    confidence: null,
    methodology: null,
    actual_meta_share: null,
    accuracy_score: null,
    created_at: "2024-06-01T00:00:00Z",
  },
];

describe("PredictionAccuracyTable", () => {
  it("should render empty state when no predictions", () => {
    render(<PredictionAccuracyTable predictions={[]} />);

    expect(screen.getByText("No scored predictions yet")).toBeInTheDocument();
  });

  it("should render table headers", () => {
    render(<PredictionAccuracyTable predictions={mockPredictions} />);

    expect(screen.getByText("Archetype")).toBeInTheDocument();
    expect(screen.getByText("Tier")).toBeInTheDocument();
    expect(screen.getByText("Predicted")).toBeInTheDocument();
    expect(screen.getByText("Actual")).toBeInTheDocument();
    expect(screen.getByText("Accuracy")).toBeInTheDocument();
    expect(screen.getByText("Date")).toBeInTheDocument();
  });

  it("should render archetype IDs", () => {
    render(<PredictionAccuracyTable predictions={mockPredictions} />);

    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    expect(screen.getByText("Lugia VSTAR")).toBeInTheDocument();
    expect(screen.getByText("Gardevoir ex")).toBeInTheDocument();
  });

  it("should render tier badges for valid tiers", () => {
    render(<PredictionAccuracyTable predictions={mockPredictions} />);

    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
    expect(screen.getByText("S")).toBeInTheDocument();
  });

  it("should render dash for invalid tier", () => {
    const invalidTier: ApiArchetypePrediction[] = [
      {
        ...mockPredictions[0],
        id: "pred-invalid",
        predicted_tier: "Unknown",
      },
    ];

    render(<PredictionAccuracyTable predictions={invalidTier} />);

    // The em dash is rendered for invalid tiers
    const cells = screen.getAllByRole("cell");
    const tierCell = cells[1]; // Tier column
    expect(tierCell.textContent).toContain("\u2014");
  });

  it("should display predicted meta share percentage", () => {
    render(<PredictionAccuracyTable predictions={mockPredictions} />);

    expect(screen.getByText("12.0%")).toBeInTheDocument();
    expect(screen.getByText("8.0%")).toBeInTheDocument();
  });

  it("should display dash for null predicted meta share", () => {
    render(<PredictionAccuracyTable predictions={[mockPredictions[2]]} />);

    const cells = screen.getAllByRole("cell");
    // Find the predicted column cell (index 2)
    const predictedCell = cells[2];
    expect(predictedCell.textContent).toContain("\u2014");
  });

  it("should display actual meta share percentage", () => {
    render(<PredictionAccuracyTable predictions={mockPredictions} />);

    expect(screen.getByText("11.5%")).toBeInTheDocument();
    expect(screen.getByText("3.0%")).toBeInTheDocument();
  });

  it("should display dash for null actual meta share", () => {
    render(<PredictionAccuracyTable predictions={[mockPredictions[2]]} />);

    const cells = screen.getAllByRole("cell");
    // Actual column (index 3)
    const actualCell = cells[3];
    expect(actualCell.textContent).toContain("\u2014");
  });

  it("should display accuracy score as percentage", () => {
    render(<PredictionAccuracyTable predictions={mockPredictions} />);

    expect(screen.getByText("92%")).toBeInTheDocument();
    expect(screen.getByText("45%")).toBeInTheDocument();
  });

  it("should display dash for null accuracy score", () => {
    render(<PredictionAccuracyTable predictions={[mockPredictions[2]]} />);

    const cells = screen.getAllByRole("cell");
    // Accuracy column (index 4)
    const accuracyCell = cells[4];
    expect(accuracyCell.textContent).toContain("\u2014");
  });

  it("should display formatted date", () => {
    render(<PredictionAccuracyTable predictions={mockPredictions} />);

    // safeFormatDate formats the date using "MMM d" format
    const expectedDate = safeFormatDate("2024-06-01T00:00:00Z", "MMM d");
    const dateCells = screen.getAllByText(expectedDate);
    expect(dateCells.length).toBe(3);
  });

  it("should apply green color for high accuracy scores (>= 0.8)", () => {
    render(<PredictionAccuracyTable predictions={[mockPredictions[0]]} />);

    // accuracy_score = 0.92, should have green text
    const accuracyText = screen.getByText("92%");
    expect(accuracyText).toHaveClass("text-green-500");
  });

  it("should apply amber color for medium accuracy scores (>= 0.5)", () => {
    const mediumAccuracy: ApiArchetypePrediction[] = [
      {
        ...mockPredictions[0],
        accuracy_score: 0.65,
      },
    ];

    render(<PredictionAccuracyTable predictions={mediumAccuracy} />);

    const accuracyText = screen.getByText("65%");
    expect(accuracyText).toHaveClass("text-amber-500");
  });

  it("should apply red color for low accuracy scores (< 0.5)", () => {
    render(<PredictionAccuracyTable predictions={[mockPredictions[1]]} />);

    // accuracy_score = 0.45, should have red text
    const accuracyText = screen.getByText("45%");
    expect(accuracyText).toHaveClass("text-red-500");
  });

  it("should apply custom className", () => {
    const { container } = render(
      <PredictionAccuracyTable
        predictions={mockPredictions}
        className="custom-class"
      />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });

  it("should apply custom className to empty state", () => {
    const { container } = render(
      <PredictionAccuracyTable predictions={[]} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });

  it("should render null tier as dash", () => {
    const nullTier: ApiArchetypePrediction[] = [
      {
        ...mockPredictions[0],
        predicted_tier: null,
      },
    ];

    render(<PredictionAccuracyTable predictions={nullTier} />);

    const cells = screen.getAllByRole("cell");
    const tierCell = cells[1];
    expect(tierCell.textContent).toContain("\u2014");
  });

  it("should render all valid tier badges", () => {
    const allTiers: ApiArchetypePrediction[] = [
      "S",
      "A",
      "B",
      "C",
      "Rogue",
    ].map((tier, i) => ({
      ...mockPredictions[0],
      id: `pred-tier-${i}`,
      archetype_id: `archetype-${tier}`,
      predicted_tier: tier,
    }));

    render(<PredictionAccuracyTable predictions={allTiers} />);

    expect(screen.getByText("S")).toBeInTheDocument();
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
    expect(screen.getByText("C")).toBeInTheDocument();
    expect(screen.getByText("Rogue")).toBeInTheDocument();
  });

  it("should handle prediction with null created_at gracefully", () => {
    const nullDate: ApiArchetypePrediction[] = [
      {
        ...mockPredictions[0],
        created_at: null,
      },
    ];

    render(<PredictionAccuracyTable predictions={nullDate} />);

    // safeFormatDate returns em dash for null
    const cells = screen.getAllByRole("cell");
    const dateCell = cells[5];
    expect(dateCell.textContent).toContain("\u2014");
  });
});
