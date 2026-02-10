import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { RotationBriefingHeader } from "../RotationBriefingHeader";

describe("RotationBriefingHeader", () => {
  beforeEach(() => {
    // Fix "now" to 2026-02-07 so day calculations are deterministic
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-02-07T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should render the post-rotation phase briefing", () => {
    render(<RotationBriefingHeader phase="post-rotation" />);

    expect(screen.getByText(/SV9\+ format/)).toBeInTheDocument();
    expect(screen.getByText(/January 23/)).toBeInTheDocument();
  });

  it("should show days of post-rotation data pill", () => {
    render(<RotationBriefingHeader phase="post-rotation" />);

    // 2026-02-07 minus 2026-01-23 = 15 days
    expect(
      screen.getByText(/15 days of post-rotation data/)
    ).toBeInTheDocument();
  });

  it("should mention the April 10 rotation date", () => {
    render(<RotationBriefingHeader phase="post-rotation" />);

    expect(screen.getByText("April 10")).toBeInTheDocument();
  });

  it("should show countdown box with days until rotation", () => {
    render(<RotationBriefingHeader phase="post-rotation" />);

    const countdown = screen.getByTestId("rotation-countdown");
    expect(countdown).toBeInTheDocument();
    // differenceInDays(2026-04-10, 2026-02-07T12:00:00Z) = 61
    expect(countdown).toHaveTextContent("61");
    expect(countdown).toHaveTextContent(/days until/);
    expect(countdown).toHaveTextContent(/EN rotation/);
  });

  it("should show source attribution", () => {
    render(<RotationBriefingHeader phase="post-rotation" />);

    expect(screen.getByText(/Limitless TCG/)).toBeInTheDocument();
    expect(screen.getByText(/Pokecabook/)).toBeInTheDocument();
    expect(screen.getByText(/Pokekameshi/)).toBeInTheDocument();
  });

  it("should return null for unified phase", () => {
    const { container } = render(<RotationBriefingHeader phase="unified" />);

    expect(container.innerHTML).toBe("");
  });

  it("should render pre-rotation phase", () => {
    render(<RotationBriefingHeader phase="pre-rotation" />);

    // pre-rotation is not "unified", so it should render
    expect(screen.getByText(/SV9\+ format/)).toBeInTheDocument();
  });

  it("should show unified badge when rotation date has passed", () => {
    // Set time to after the EN_ROTATION_DATE (2026-04-10)
    vi.setSystemTime(new Date("2026-05-01T12:00:00Z"));

    render(<RotationBriefingHeader phase="post-rotation" />);

    const unified = screen.getByTestId("rotation-unified");
    expect(unified).toBeInTheDocument();
    expect(unified).toHaveTextContent(/Formats Unified/);
    // No countdown should be visible
    expect(screen.queryByTestId("rotation-countdown")).not.toBeInTheDocument();
  });

  it("should use amber styling when within 14 days of rotation", () => {
    // Set time to 10 days before rotation
    vi.setSystemTime(new Date("2026-03-31T12:00:00Z"));

    render(<RotationBriefingHeader phase="post-rotation" />);

    const countdown = screen.getByTestId("rotation-countdown");
    // Should have amber border styling for urgency
    expect(countdown.className).toContain("amber");
  });

  it("should use teal styling when more than 14 days away", () => {
    render(<RotationBriefingHeader phase="post-rotation" />);

    const countdown = screen.getByTestId("rotation-countdown");
    // Should have teal border styling (not urgent)
    expect(countdown.className).toContain("teal");
  });
});
