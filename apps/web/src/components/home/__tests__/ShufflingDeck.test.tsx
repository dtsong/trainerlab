import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { ShufflingDeck } from "../ShufflingDeck";

describe("ShufflingDeck", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should render the 'Live Data' label", () => {
    render(<ShufflingDeck />);

    expect(screen.getByText("Live Data")).toBeInTheDocument();
  });

  it("should render 8 card elements", () => {
    const { container } = render(<ShufflingDeck />);

    // Each Card renders an absolute-positioned div with a Pokeball SVG
    const cards = container.querySelectorAll("svg");
    expect(cards).toHaveLength(8);
  });

  it("should render within a container of expected dimensions", () => {
    const { container } = render(<ShufflingDeck />);

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass("relative");
    expect(wrapper).toHaveClass("w-20");
    expect(wrapper).toHaveClass("h-24");
  });

  it("should render a shadow element under the deck", () => {
    const { container } = render(<ShufflingDeck />);

    const shadow = container.querySelector(".blur-sm");
    expect(shadow).toBeInTheDocument();
  });

  it("should trigger initial shuffle after 2 seconds", () => {
    const { container } = render(<ShufflingDeck />);

    // Before the initial timeout, cards should be at their default positions
    const cardsBefore = container.querySelectorAll("svg");
    expect(cardsBefore).toHaveLength(8);

    // Advance past the initial 2-second delay
    act(() => {
      vi.advanceTimersByTime(2000);
    });

    // The component should still render all cards during shuffle
    const cardsAfter = container.querySelectorAll("svg");
    expect(cardsAfter).toHaveLength(8);
  });

  it("should complete a shuffle cycle through all phases", () => {
    render(<ShufflingDeck />);

    // Start the initial shuffle
    act(() => {
      vi.advanceTimersByTime(2000);
    });

    // Phase 2 at 300ms
    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Phase 3 at 600ms
    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Phase 4 at 900ms
    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Reset at 1200ms
    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Should still have all 8 cards after the cycle completes
    expect(screen.getByText("Live Data")).toBeInTheDocument();
  });

  it("should clean up timers on unmount", () => {
    const clearIntervalSpy = vi.spyOn(global, "clearInterval");
    const clearTimeoutSpy = vi.spyOn(global, "clearTimeout");

    const { unmount } = render(<ShufflingDeck />);

    unmount();

    expect(clearIntervalSpy).toHaveBeenCalled();
    expect(clearTimeoutSpy).toHaveBeenCalled();

    clearIntervalSpy.mockRestore();
    clearTimeoutSpy.mockRestore();
  });
});
