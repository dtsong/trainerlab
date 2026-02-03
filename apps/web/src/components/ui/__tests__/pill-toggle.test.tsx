import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PillToggle } from "../pill-toggle";

const defaultOptions = [
  { value: "week", label: "Week" },
  { value: "month", label: "Month" },
  { value: "year", label: "Year" },
];

describe("PillToggle", () => {
  describe("basic rendering", () => {
    it("should render all options", () => {
      const onChange = vi.fn();
      render(
        <PillToggle options={defaultOptions} value="week" onChange={onChange} />
      );

      expect(screen.getByText("Week")).toBeInTheDocument();
      expect(screen.getByText("Month")).toBeInTheDocument();
      expect(screen.getByText("Year")).toBeInTheDocument();
    });

    it("should highlight the selected option", () => {
      const onChange = vi.fn();
      render(
        <PillToggle
          options={defaultOptions}
          value="month"
          onChange={onChange}
        />
      );

      const selectedButton = screen.getByRole("button", { name: "Month" });
      expect(selectedButton).toHaveAttribute("aria-pressed", "true");
      expect(selectedButton).toHaveClass("bg-teal-500");
    });

    it("should not highlight unselected options", () => {
      const onChange = vi.fn();
      render(
        <PillToggle
          options={defaultOptions}
          value="month"
          onChange={onChange}
        />
      );

      const unselectedButton = screen.getByRole("button", { name: "Week" });
      expect(unselectedButton).toHaveAttribute("aria-pressed", "false");
      expect(unselectedButton).not.toHaveClass("bg-teal-500");
    });
  });

  describe("selection behavior", () => {
    it("should call onChange when clicking an option", () => {
      const onChange = vi.fn();
      render(
        <PillToggle options={defaultOptions} value="week" onChange={onChange} />
      );

      fireEvent.click(screen.getByText("Month"));
      expect(onChange).toHaveBeenCalledWith("month");
    });

    it("should call onChange when clicking already selected option", () => {
      const onChange = vi.fn();
      render(
        <PillToggle options={defaultOptions} value="week" onChange={onChange} />
      );

      fireEvent.click(screen.getByText("Week"));
      expect(onChange).toHaveBeenCalledWith("week");
    });
  });

  describe("keyboard navigation", () => {
    it("should navigate with arrow right key", async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      render(
        <PillToggle options={defaultOptions} value="week" onChange={onChange} />
      );

      const container = screen.getByTestId("pill-toggle");
      await user.click(screen.getByText("Week"));
      await user.keyboard("{ArrowRight}");

      expect(onChange).toHaveBeenCalledWith("month");
    });

    it("should navigate with arrow left key", async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      render(
        <PillToggle
          options={defaultOptions}
          value="month"
          onChange={onChange}
        />
      );

      await user.click(screen.getByText("Month"));
      await user.keyboard("{ArrowLeft}");

      expect(onChange).toHaveBeenCalledWith("week");
    });

    it("should wrap around from last to first with arrow right", async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      render(
        <PillToggle options={defaultOptions} value="year" onChange={onChange} />
      );

      await user.click(screen.getByText("Year"));
      await user.keyboard("{ArrowRight}");

      expect(onChange).toHaveBeenCalledWith("week");
    });

    it("should wrap around from first to last with arrow left", async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      render(
        <PillToggle options={defaultOptions} value="week" onChange={onChange} />
      );

      await user.click(screen.getByText("Week"));
      await user.keyboard("{ArrowLeft}");

      expect(onChange).toHaveBeenCalledWith("year");
    });
  });

  describe("size variants", () => {
    it("should render small size by default", () => {
      const onChange = vi.fn();
      render(
        <PillToggle options={defaultOptions} value="week" onChange={onChange} />
      );

      const button = screen.getByRole("button", { name: "Week" });
      expect(button).toHaveClass("px-3", "py-1", "text-sm");
    });

    it("should render small size when size='sm'", () => {
      const onChange = vi.fn();
      render(
        <PillToggle
          options={defaultOptions}
          value="week"
          onChange={onChange}
          size="sm"
        />
      );

      const button = screen.getByRole("button", { name: "Week" });
      expect(button).toHaveClass("px-3", "py-1", "text-sm");
    });

    it("should render medium size when size='md'", () => {
      const onChange = vi.fn();
      render(
        <PillToggle
          options={defaultOptions}
          value="week"
          onChange={onChange}
          size="md"
        />
      );

      const button = screen.getByRole("button", { name: "Week" });
      expect(button).toHaveClass("px-4", "py-1.5", "text-base");
    });
  });

  describe("className handling", () => {
    it("should accept custom className", () => {
      const onChange = vi.fn();
      render(
        <PillToggle
          options={defaultOptions}
          value="week"
          onChange={onChange}
          className="custom-class"
        />
      );

      const container = screen.getByTestId("pill-toggle");
      expect(container).toHaveClass("custom-class");
    });
  });

  describe("accessibility", () => {
    it("should have role group", () => {
      const onChange = vi.fn();
      render(
        <PillToggle options={defaultOptions} value="week" onChange={onChange} />
      );

      expect(screen.getByRole("group")).toBeInTheDocument();
    });

    it("should have aria-pressed on buttons", () => {
      const onChange = vi.fn();
      render(
        <PillToggle options={defaultOptions} value="week" onChange={onChange} />
      );

      const buttons = screen.getAllByRole("button");
      expect(buttons[0]).toHaveAttribute("aria-pressed", "true");
      expect(buttons[1]).toHaveAttribute("aria-pressed", "false");
      expect(buttons[2]).toHaveAttribute("aria-pressed", "false");
    });
  });

  describe("input validation", () => {
    it("should not render when options array is empty", () => {
      const onChange = vi.fn();
      const { container } = render(
        <PillToggle options={[]} value="" onChange={onChange} />
      );
      expect(container.firstChild).toBeNull();
    });

    it("should not highlight any option when value doesn't match", () => {
      const onChange = vi.fn();
      render(
        <PillToggle
          options={defaultOptions}
          value="nonexistent"
          onChange={onChange}
        />
      );

      const buttons = screen.getAllByRole("button");
      buttons.forEach((button) => {
        expect(button).toHaveAttribute("aria-pressed", "false");
      });
    });
  });
});
