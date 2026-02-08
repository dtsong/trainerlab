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
    expect(
      screen.getByText(/January 23 when Nihil Zero released/)
    ).toBeInTheDocument();
  });

  it("should show days of post-rotation data pill", () => {
    render(<RotationBriefingHeader phase="post-rotation" />);

    // 2026-02-07 minus 2026-01-23 = 15 days
    expect(
      screen.getByText(/15 days of post-rotation data/)
    ).toBeInTheDocument();
  });

  it("should show days until international rotation pill", () => {
    render(<RotationBriefingHeader phase="post-rotation" />);

    // differenceInDays(2026-04-10, 2026-02-07T12:00:00Z) = 61
    expect(
      screen.getByText(/61 days until international rotation/)
    ).toBeInTheDocument();
  });

  it("should show source attribution", () => {
    render(<RotationBriefingHeader phase="post-rotation" />);

    expect(screen.getByText(/Limitless TCG tournaments/)).toBeInTheDocument();
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

  it("should hide international rotation pill when date has passed", () => {
    // Set time to after the EN_ROTATION_DATE (2026-04-10)
    vi.setSystemTime(new Date("2026-05-01T12:00:00Z"));

    render(<RotationBriefingHeader phase="post-rotation" />);

    expect(
      screen.queryByText(/days until international rotation/)
    ).not.toBeInTheDocument();
  });
});
