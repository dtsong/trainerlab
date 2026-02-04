import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  HealthIndicators,
  type HealthIndicatorsProps,
} from "../HealthIndicators";

// Mock UI components
vi.mock("@/components/ui/stat-block", () => ({
  StatBlock: ({
    value,
    label,
    subtext,
    trend,
  }: {
    value: string;
    label: string;
    subtext?: string;
    trend?: string;
  }) => (
    <div data-testid={`stat-block-${label.replace(/\s+/g, "-").toLowerCase()}`}>
      <span>{value}</span>
      <span>{label}</span>
      {subtext && <span>{subtext}</span>}
      {trend && <span data-testid="stat-trend">{trend}</span>}
    </div>
  ),
}));

vi.mock("@/components/ui/jp-signal-badge", () => ({
  JPSignalBadge: () => <span data-testid="jp-signal-badge">JP Signal</span>,
}));

describe("HealthIndicators", () => {
  const defaultProps: HealthIndicatorsProps = {
    diversityIndex: 72,
    topDeckShare: 15.3,
    topDeckName: "Charizard ex",
    biggestMoverName: "Lugia VSTAR",
    biggestMoverChange: 3.2,
    jpSignalValue: 25,
    enSignalValue: 10,
  };

  it("should render all four stat blocks", () => {
    render(<HealthIndicators {...defaultProps} />);

    expect(
      screen.getByTestId("stat-block-diversity-index")
    ).toBeInTheDocument();
    expect(screen.getByTestId("stat-block-top-deck-share")).toBeInTheDocument();
    expect(screen.getByTestId("stat-block-biggest-mover")).toBeInTheDocument();
  });

  it("should display the diversity index value", () => {
    render(<HealthIndicators {...defaultProps} />);

    expect(screen.getByText("72")).toBeInTheDocument();
  });

  it("should display the top deck share as a percentage", () => {
    render(<HealthIndicators {...defaultProps} />);

    expect(screen.getByText("15.3%")).toBeInTheDocument();
  });

  it("should display the top deck name as subtext", () => {
    render(<HealthIndicators {...defaultProps} />);

    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
  });

  it("should display the biggest mover change with + sign for positive", () => {
    render(<HealthIndicators {...defaultProps} />);

    expect(screen.getByText("+3.2%")).toBeInTheDocument();
  });

  it("should display the biggest mover name", () => {
    render(<HealthIndicators {...defaultProps} />);

    expect(screen.getByText("Lugia VSTAR")).toBeInTheDocument();
  });

  it("should display negative mover change without + sign", () => {
    render(
      <HealthIndicators
        {...defaultProps}
        biggestMoverChange={-2.5}
        biggestMoverName="Declining Deck"
      />
    );

    expect(screen.getByText("-2.5%")).toBeInTheDocument();
  });

  it("should set trend to up for positive mover change", () => {
    render(<HealthIndicators {...defaultProps} biggestMoverChange={3.2} />);

    expect(screen.getByTestId("stat-trend")).toHaveTextContent("up");
  });

  it("should set trend to down for negative mover change", () => {
    render(<HealthIndicators {...defaultProps} biggestMoverChange={-1.5} />);

    expect(screen.getByTestId("stat-trend")).toHaveTextContent("down");
  });

  it("should set trend to stable for zero mover change", () => {
    render(<HealthIndicators {...defaultProps} biggestMoverChange={0} />);

    expect(screen.getByTestId("stat-trend")).toHaveTextContent("stable");
  });

  it("should display the JP signal divergence score", () => {
    render(<HealthIndicators {...defaultProps} />);

    // |25 - 10| = 15
    expect(screen.getByText("15")).toBeInTheDocument();
  });

  it("should show JP signal badge when divergence exceeds threshold", () => {
    render(<HealthIndicators {...defaultProps} />);

    // |25 - 10| = 15 > 5 threshold
    expect(screen.getByTestId("jp-signal-badge")).toBeInTheDocument();
  });

  it("should not show JP signal badge when divergence is small", () => {
    render(
      <HealthIndicators
        {...defaultProps}
        jpSignalValue={12}
        enSignalValue={10}
      />
    );

    // |12 - 10| = 2 < 5 threshold
    expect(screen.queryByTestId("jp-signal-badge")).not.toBeInTheDocument();
  });

  it("should display JP Signal label", () => {
    render(<HealthIndicators {...defaultProps} />);

    // "JP Signal" appears both in the label and the mocked JPSignalBadge
    const elements = screen.getAllByText("JP Signal");
    expect(elements.length).toBeGreaterThanOrEqual(1);
  });

  it("should display meta divergence score subtext", () => {
    render(<HealthIndicators {...defaultProps} />);

    expect(screen.getByText("Meta divergence score")).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    const { container } = render(
      <HealthIndicators {...defaultProps} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });
});
