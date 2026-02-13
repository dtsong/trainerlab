import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { CountdownBadge } from "../CountdownBadge";

describe("CountdownBadge", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows Today and pulses for a same-day date", () => {
    vi.setSystemTime(new Date("2026-02-13T12:00:00.000Z"));
    render(<CountdownBadge date="2026-02-13" />);

    const badge = screen.getByText("Today");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("motion-safe:animate-pulse");
  });

  it("shows Tomorrow for next-day date", () => {
    vi.setSystemTime(new Date("2026-02-13T12:00:00.000Z"));
    render(<CountdownBadge date="2026-02-14" />);
    expect(screen.getByText("Tomorrow")).toBeInTheDocument();
  });

  it("shows Starts in Xd Yh within 7 days when time is provided", () => {
    vi.setSystemTime(new Date("2026-02-13T00:00:00.000Z"));
    render(<CountdownBadge date="2026-02-15T14:00:00.000Z" />);

    const badge = screen.getByText(/Starts in/i);
    expect(badge.textContent).toContain("2d");
    expect(badge.textContent).toContain("14h");
  });
});
