import React from "react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TournamentTypeFilter } from "../TournamentTypeFilter";

// Mock pointer capture and scroll APIs for Radix UI compatibility in jsdom
beforeAll(() => {
  HTMLElement.prototype.hasPointerCapture = vi.fn().mockReturnValue(false);
  HTMLElement.prototype.setPointerCapture = vi.fn();
  HTMLElement.prototype.releasePointerCapture = vi.fn();
  HTMLElement.prototype.scrollIntoView = vi.fn();
  Element.prototype.scrollIntoView = vi.fn();
});

describe("TournamentTypeFilter", () => {
  it("should render with default value", () => {
    const onChange = vi.fn();
    render(<TournamentTypeFilter value="all" onChange={onChange} />);

    expect(screen.getByTestId("tournament-type-filter")).toBeInTheDocument();
  });

  it("should display All Tournaments when selected", () => {
    const onChange = vi.fn();
    render(<TournamentTypeFilter value="all" onChange={onChange} />);

    expect(screen.getByText("All Tournaments")).toBeInTheDocument();
  });

  it("should display Official when selected", () => {
    const onChange = vi.fn();
    render(<TournamentTypeFilter value="official" onChange={onChange} />);

    expect(screen.getByText("Official (Regionals/ICs)")).toBeInTheDocument();
  });

  it("should display Grassroots when selected", () => {
    const onChange = vi.fn();
    render(<TournamentTypeFilter value="grassroots" onChange={onChange} />);

    expect(screen.getByText("Grassroots (Leagues)")).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    const onChange = vi.fn();
    render(
      <TournamentTypeFilter
        value="all"
        onChange={onChange}
        className="custom-class"
      />
    );

    expect(screen.getByTestId("tournament-type-filter")).toHaveClass(
      "custom-class"
    );
  });

  it("should call onChange when a type is selected", async () => {
    const onChange = vi.fn();
    render(<TournamentTypeFilter value="all" onChange={onChange} />);

    // Open the select dropdown
    const trigger = screen.getByTestId("tournament-type-filter");
    fireEvent.click(trigger);

    // Wait for dropdown to appear and select Official
    const officialOption = await screen.findByText("Official (Regionals/ICs)");
    fireEvent.click(officialOption);

    expect(onChange).toHaveBeenCalledWith("official");
  });

  it("should pass value correctly to Select component", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <TournamentTypeFilter value="all" onChange={onChange} />
    );

    expect(screen.getByText("All Tournaments")).toBeInTheDocument();

    rerender(<TournamentTypeFilter value="official" onChange={onChange} />);
    expect(screen.getByText("Official (Regionals/ICs)")).toBeInTheDocument();

    rerender(<TournamentTypeFilter value="grassroots" onChange={onChange} />);
    expect(screen.getByText("Grassroots (Leagues)")).toBeInTheDocument();
  });

  it("should have aria-label for accessibility", () => {
    const onChange = vi.fn();
    render(<TournamentTypeFilter value="all" onChange={onChange} />);

    expect(screen.getByTestId("tournament-type-filter")).toHaveAttribute(
      "aria-label",
      "Filter by tournament type"
    );
  });
});
