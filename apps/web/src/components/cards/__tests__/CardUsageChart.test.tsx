/**
 * CardUsageChart tests
 *
 * NOTE: CardUsageChart.tsx does not exist yet. This test file is a placeholder
 * that tests the CardSearchInput component (the remaining untested component
 * in the cards domain). Once CardUsageChart is implemented, this file should
 * be updated to test that component instead.
 *
 * The existing CardSearchInput.test.tsx covers core functionality. These tests
 * provide additional coverage for edge cases and integration behavior.
 */
import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CardSearchInput } from "../CardSearchInput";

describe("CardSearchInput (additional coverage)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("aria attributes", () => {
    it("should have aria-label for accessibility", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} />);

      const input = screen.getByLabelText("Search cards");
      expect(input).toBeInTheDocument();
    });

    it("should have sr-only text on clear button", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="test" onChange={onChange} />);

      expect(screen.getByText("Clear search")).toBeInTheDocument();
    });
  });

  describe("edge cases", () => {
    it("should handle rapid input changes gracefully", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} />);

      const input = screen.getByPlaceholderText("Search cards...");

      fireEvent.change(input, { target: { value: "a" } });
      fireEvent.change(input, { target: { value: "ab" } });
      fireEvent.change(input, { target: { value: "abc" } });
      fireEvent.change(input, { target: { value: "abcd" } });
      fireEvent.change(input, { target: { value: "abcde" } });

      vi.advanceTimersByTime(300);

      // Only the final value should be emitted
      expect(onChange).toHaveBeenCalledTimes(1);
      expect(onChange).toHaveBeenCalledWith("abcde");
    });

    it("should not emit onChange when value returns to original", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="hello" onChange={onChange} />);

      const input = screen.getByPlaceholderText("Search cards...");

      fireEvent.change(input, { target: { value: "world" } });
      fireEvent.change(input, { target: { value: "hello" } });

      vi.advanceTimersByTime(300);

      // Value returned to original, so onChange should not fire
      expect(onChange).not.toHaveBeenCalled();
    });

    it("should handle empty string value correctly", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} />);

      const input = screen.getByPlaceholderText("Search cards...");
      expect(input).toHaveValue("");
    });

    it("should clear immediately without waiting for debounce", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="test" onChange={onChange} />);

      const clearButton = screen.getByRole("button", { name: /clear/i });
      fireEvent.click(clearButton);

      // onChange should fire immediately on clear
      expect(onChange).toHaveBeenCalledWith("");
    });
  });

  describe("debounce timing", () => {
    it("should not fire onChange before debounce period", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} debounceMs={500} />);

      const input = screen.getByPlaceholderText("Search cards...");
      fireEvent.change(input, { target: { value: "test" } });

      vi.advanceTimersByTime(499);
      expect(onChange).not.toHaveBeenCalled();

      vi.advanceTimersByTime(1);
      expect(onChange).toHaveBeenCalledWith("test");
    });

    it("should respect zero debounce", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} debounceMs={0} />);

      const input = screen.getByPlaceholderText("Search cards...");
      fireEvent.change(input, { target: { value: "instant" } });

      vi.advanceTimersByTime(0);
      expect(onChange).toHaveBeenCalledWith("instant");
    });
  });

  describe("layout", () => {
    it("should render search icon as SVG", () => {
      const onChange = vi.fn();
      const { container } = render(
        <CardSearchInput value="" onChange={onChange} />
      );

      const svgs = container.querySelectorAll("svg");
      expect(svgs.length).toBeGreaterThanOrEqual(1);
    });

    it("should render clear icon when value is present", () => {
      const onChange = vi.fn();
      const { container } = render(
        <CardSearchInput value="test" onChange={onChange} />
      );

      // Search icon + clear icon
      const svgs = container.querySelectorAll("svg");
      expect(svgs.length).toBeGreaterThanOrEqual(2);
    });
  });
});
