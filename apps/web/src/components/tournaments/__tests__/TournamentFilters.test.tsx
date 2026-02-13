import React from "react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TournamentFilters } from "../TournamentFilters";

// Mock pointer capture and scroll APIs for Radix UI compatibility in jsdom
beforeAll(() => {
  HTMLElement.prototype.hasPointerCapture = vi.fn().mockReturnValue(false);
  HTMLElement.prototype.setPointerCapture = vi.fn();
  HTMLElement.prototype.releasePointerCapture = vi.fn();
  HTMLElement.prototype.scrollIntoView = vi.fn();
  Element.prototype.scrollIntoView = vi.fn();
});

describe("TournamentFilters", () => {
  const defaultProps = {
    format: "all" as const,
    majorFormatKey: "all" as const,
    season: "all" as const,
    onFormatChange: vi.fn(),
    onMajorFormatChange: vi.fn(),
    onSeasonChange: vi.fn(),
  };

  it("should render format select", () => {
    render(<TournamentFilters {...defaultProps} />);

    expect(screen.getByText("All Formats")).toBeInTheDocument();
  });

  it("should display the selected format", () => {
    render(<TournamentFilters {...defaultProps} format="standard" />);

    expect(screen.getByText("Standard")).toBeInTheDocument();
  });

  it("should display Expanded when expanded format is selected", () => {
    render(<TournamentFilters {...defaultProps} format="expanded" />);

    expect(screen.getByText("Expanded")).toBeInTheDocument();
  });

  it("should call onFormatChange when a format is selected", async () => {
    const onFormatChange = vi.fn();
    render(
      <TournamentFilters {...defaultProps} onFormatChange={onFormatChange} />
    );

    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    const option = await screen.findByText("Standard");
    fireEvent.click(option);

    expect(onFormatChange).toHaveBeenCalledWith("standard");
  });

  it("should render and change major format when major filters are enabled", async () => {
    const onMajorFormatChange = vi.fn();
    render(
      <TournamentFilters
        {...defaultProps}
        showMajorFilters={true}
        onMajorFormatChange={onMajorFormatChange}
      />
    );

    const comboboxes = screen.getAllByRole("combobox");
    fireEvent.click(comboboxes[1]);

    const option = await screen.findByText("SVI-ASC (Mar 2026)");
    fireEvent.click(option);

    expect(onMajorFormatChange).toHaveBeenCalledWith("svi-asc");
  });

  it("should update displayed value when props change", () => {
    const { rerender } = render(<TournamentFilters {...defaultProps} />);

    expect(screen.getByText("All Formats")).toBeInTheDocument();

    rerender(<TournamentFilters {...defaultProps} format="expanded" />);

    expect(screen.getByText("Expanded")).toBeInTheDocument();
  });
});
