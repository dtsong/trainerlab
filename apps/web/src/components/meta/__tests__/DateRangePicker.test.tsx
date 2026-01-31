import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DateRangePicker } from "../DateRangePicker";

describe("DateRangePicker", () => {
  const defaultDateRange = {
    start: new Date("2025-01-01T12:00:00"),
    end: new Date("2025-01-31T12:00:00"),
  };

  it("should render the trigger button", () => {
    const onChange = vi.fn();
    render(<DateRangePicker value={defaultDateRange} onChange={onChange} />);

    expect(screen.getByTestId("date-range-picker")).toBeInTheDocument();
  });

  it("should display a date range", () => {
    const onChange = vi.fn();
    render(<DateRangePicker value={defaultDateRange} onChange={onChange} />);

    // Match any date format with month names
    const button = screen.getByTestId("date-range-picker");
    expect(button).toHaveTextContent(/Jan.*-.*Jan.*2025/);
  });

  it("should have calendar icon", () => {
    const onChange = vi.fn();
    render(<DateRangePicker value={defaultDateRange} onChange={onChange} />);

    // The button contains an SVG calendar icon
    const button = screen.getByTestId("date-range-picker");
    expect(button.querySelector("svg")).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    const onChange = vi.fn();
    render(
      <DateRangePicker
        value={defaultDateRange}
        onChange={onChange}
        className="custom-class"
      />,
    );

    expect(screen.getByTestId("date-range-picker")).toHaveClass("custom-class");
  });

  it("should format different date ranges correctly", () => {
    const onChange = vi.fn();
    const differentRange = {
      start: new Date("2024-06-15T12:00:00"),
      end: new Date("2024-07-15T12:00:00"),
    };
    render(<DateRangePicker value={differentRange} onChange={onChange} />);

    const button = screen.getByTestId("date-range-picker");
    expect(button).toHaveTextContent(/Jun.*-.*Jul.*2024/);
  });
});
