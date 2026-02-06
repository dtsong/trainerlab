import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ConfidenceBadge } from "../confidence-badge";

describe("ConfidenceBadge", () => {
  it("should render high confidence with green styling", () => {
    render(<ConfidenceBadge confidence="high" sampleSize={200} />);
    const badge = screen.getByTestId("confidence-badge");
    expect(badge).toHaveTextContent("High");
    expect(badge).toHaveAttribute("title", "200 placements");
    expect(badge.className).toMatch(/emerald/);
  });

  it("should render medium confidence with amber styling", () => {
    render(<ConfidenceBadge confidence="medium" sampleSize={75} />);
    const badge = screen.getByTestId("confidence-badge");
    expect(badge).toHaveTextContent("Med");
    expect(badge.className).toMatch(/amber/);
  });

  it("should render low confidence with slate styling", () => {
    render(
      <ConfidenceBadge
        confidence="low"
        sampleSize={20}
        freshnessLabel="updated 10 days ago"
      />
    );
    const badge = screen.getByTestId("confidence-badge");
    expect(badge).toHaveTextContent("Low");
    expect(badge).toHaveAttribute(
      "title",
      "20 placements, updated 10 days ago"
    );
    expect(badge.className).toMatch(/slate/);
  });

  it("should accept custom className", () => {
    render(
      <ConfidenceBadge confidence="high" sampleSize={500} className="ml-2" />
    );
    const badge = screen.getByTestId("confidence-badge");
    expect(badge).toHaveClass("ml-2");
  });
});
