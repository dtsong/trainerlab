import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
      />
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

  it("should open dialog when trigger button is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<DateRangePicker value={defaultDateRange} onChange={onChange} />);

    await user.click(screen.getByTestId("date-range-picker"));

    expect(screen.getByText("Select Date Range")).toBeInTheDocument();
    expect(screen.getByText("Last 7 days")).toBeInTheDocument();
    expect(screen.getByText("Last 30 days")).toBeInTheDocument();
    expect(screen.getByText("Last 90 days")).toBeInTheDocument();
  });

  it("should call onChange when preset button is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<DateRangePicker value={defaultDateRange} onChange={onChange} />);

    await user.click(screen.getByTestId("date-range-picker"));
    await user.click(screen.getByText("Last 7 days"));

    expect(onChange).toHaveBeenCalledTimes(1);
    const call = onChange.mock.calls[0][0];
    expect(call.start).toBeInstanceOf(Date);
    expect(call.end).toBeInstanceOf(Date);
  });

  it("should close dialog when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<DateRangePicker value={defaultDateRange} onChange={onChange} />);

    await user.click(screen.getByTestId("date-range-picker"));
    expect(screen.getByText("Select Date Range")).toBeInTheDocument();

    await user.click(screen.getByText("Cancel"));

    await waitFor(() => {
      expect(screen.queryByText("Select Date Range")).not.toBeInTheDocument();
    });
    expect(onChange).not.toHaveBeenCalled();
  });

  it("should show error when start date is after end date", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<DateRangePicker value={defaultDateRange} onChange={onChange} />);

    await user.click(screen.getByTestId("date-range-picker"));

    // Set start date after end date
    const startInput = screen.getByLabelText("Start Date");
    const endInput = screen.getByLabelText("End Date");

    await user.clear(startInput);
    await user.type(startInput, "2025-02-15");
    await user.clear(endInput);
    await user.type(endInput, "2025-01-01");

    await user.click(screen.getByText("Apply"));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Start date must be before end date"
    );
    expect(onChange).not.toHaveBeenCalled();
  });

  it("should call onChange with date range when Apply is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<DateRangePicker value={defaultDateRange} onChange={onChange} />);

    await user.click(screen.getByTestId("date-range-picker"));
    await user.click(screen.getByText("Apply"));

    expect(onChange).toHaveBeenCalled();
    const call = onChange.mock.calls[onChange.mock.calls.length - 1][0];
    expect(call.start).toBeInstanceOf(Date);
    expect(call.end).toBeInstanceOf(Date);
    expect(call.start.getTime()).toBeLessThan(call.end.getTime());
  });
});
