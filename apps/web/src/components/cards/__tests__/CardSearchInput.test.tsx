import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CardSearchInput } from "../CardSearchInput";

describe("CardSearchInput", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("basic rendering", () => {
    it("should render with default placeholder", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} />);

      expect(
        screen.getByPlaceholderText("Search cards..."),
      ).toBeInTheDocument();
    });

    it("should render with custom placeholder", () => {
      const onChange = vi.fn();
      render(
        <CardSearchInput
          value=""
          onChange={onChange}
          placeholder="Find Pokemon..."
        />,
      );

      expect(
        screen.getByPlaceholderText("Find Pokemon..."),
      ).toBeInTheDocument();
    });

    it("should render search icon", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} />);

      // Search icon is rendered as SVG
      const input = screen.getByPlaceholderText("Search cards...");
      const container = input.closest("div");
      expect(container?.querySelector("svg")).toBeInTheDocument();
    });

    it("should display initial value", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="Pikachu" onChange={onChange} />);

      expect(screen.getByDisplayValue("Pikachu")).toBeInTheDocument();
    });
  });

  describe("clear button", () => {
    it("should not show clear button when input is empty", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} />);

      expect(
        screen.queryByRole("button", { name: /clear/i }),
      ).not.toBeInTheDocument();
    });

    it("should show clear button when input has value", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="test" onChange={onChange} />);

      expect(
        screen.getByRole("button", { name: /clear/i }),
      ).toBeInTheDocument();
    });

    it("should clear input when clear button is clicked", async () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="test" onChange={onChange} />);

      const clearButton = screen.getByRole("button", { name: /clear/i });
      fireEvent.click(clearButton);

      expect(onChange).toHaveBeenCalledWith("");
    });
  });

  describe("debounced onChange", () => {
    it("should not call onChange immediately on input", async () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} />);

      const input = screen.getByPlaceholderText("Search cards...");
      fireEvent.change(input, { target: { value: "Charizard" } });

      expect(onChange).not.toHaveBeenCalled();
    });

    it("should call onChange after debounce delay", async () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} />);

      const input = screen.getByPlaceholderText("Search cards...");
      fireEvent.change(input, { target: { value: "Charizard" } });

      vi.advanceTimersByTime(300);

      expect(onChange).toHaveBeenCalledWith("Charizard");
    });

    it("should use custom debounce delay", async () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} debounceMs={500} />);

      const input = screen.getByPlaceholderText("Search cards...");
      fireEvent.change(input, { target: { value: "Mewtwo" } });

      vi.advanceTimersByTime(300);
      expect(onChange).not.toHaveBeenCalled();

      vi.advanceTimersByTime(200);
      expect(onChange).toHaveBeenCalledWith("Mewtwo");
    });

    it("should cancel pending debounce on new input", async () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} />);

      const input = screen.getByPlaceholderText("Search cards...");

      fireEvent.change(input, { target: { value: "Pika" } });
      vi.advanceTimersByTime(200);

      fireEvent.change(input, { target: { value: "Pikachu" } });
      vi.advanceTimersByTime(300);

      expect(onChange).toHaveBeenCalledTimes(1);
      expect(onChange).toHaveBeenCalledWith("Pikachu");
    });
  });

  describe("external value sync", () => {
    it("should sync when external value changes", () => {
      const onChange = vi.fn();
      const { rerender } = render(
        <CardSearchInput value="old" onChange={onChange} />,
      );

      expect(screen.getByDisplayValue("old")).toBeInTheDocument();

      rerender(<CardSearchInput value="new" onChange={onChange} />);

      expect(screen.getByDisplayValue("new")).toBeInTheDocument();
    });

    it("should not call onChange when value is synced from external", () => {
      const onChange = vi.fn();
      const { rerender } = render(
        <CardSearchInput value="initial" onChange={onChange} />,
      );

      rerender(<CardSearchInput value="initial" onChange={onChange} />);
      vi.advanceTimersByTime(300);

      expect(onChange).not.toHaveBeenCalled();
    });
  });

  describe("className handling", () => {
    it("should accept custom className", () => {
      const onChange = vi.fn();
      render(
        <CardSearchInput
          value=""
          onChange={onChange}
          className="custom-class"
        />,
      );

      const input = screen.getByPlaceholderText("Search cards...");
      const container = input.closest("div.relative");
      expect(container).toHaveClass("custom-class");
    });
  });

  describe("accessibility", () => {
    it("should have search input type", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="" onChange={onChange} />);

      const input = screen.getByPlaceholderText("Search cards...");
      expect(input).toHaveAttribute("type", "search");
    });

    it("should have accessible clear button", () => {
      const onChange = vi.fn();
      render(<CardSearchInput value="test" onChange={onChange} />);

      const clearButton = screen.getByRole("button", { name: /clear search/i });
      expect(clearButton).toBeInTheDocument();
    });
  });
});
