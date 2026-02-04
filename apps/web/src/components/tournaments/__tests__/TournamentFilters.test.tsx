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
    region: "all",
    format: "all" as const,
    tier: "major" as const,
    onRegionChange: vi.fn(),
    onFormatChange: vi.fn(),
    onTierChange: vi.fn(),
  };

  it("should render all three filter selects", () => {
    render(<TournamentFilters {...defaultProps} />);

    expect(screen.getByText("All Regions")).toBeInTheDocument();
    expect(screen.getByText("All Formats")).toBeInTheDocument();
    expect(screen.getByText("Major")).toBeInTheDocument();
  });

  it("should display the selected region", () => {
    render(<TournamentFilters {...defaultProps} region="NA" />);

    expect(screen.getByText("North America")).toBeInTheDocument();
  });

  it("should display the selected format", () => {
    render(<TournamentFilters {...defaultProps} format="standard" />);

    expect(screen.getByText("Standard")).toBeInTheDocument();
  });

  it("should display the selected tier", () => {
    render(<TournamentFilters {...defaultProps} tier="grassroots" />);

    expect(screen.getByText("Grassroots")).toBeInTheDocument();
  });

  it("should display Europe when EU is selected", () => {
    render(<TournamentFilters {...defaultProps} region="EU" />);

    expect(screen.getByText("Europe")).toBeInTheDocument();
  });

  it("should display Japan when JP is selected", () => {
    render(<TournamentFilters {...defaultProps} region="JP" />);

    expect(screen.getByText("Japan")).toBeInTheDocument();
  });

  it("should display Latin America when LATAM is selected", () => {
    render(<TournamentFilters {...defaultProps} region="LATAM" />);

    expect(screen.getByText("Latin America")).toBeInTheDocument();
  });

  it("should display Oceania when OCE is selected", () => {
    render(<TournamentFilters {...defaultProps} region="OCE" />);

    expect(screen.getByText("Oceania")).toBeInTheDocument();
  });

  it("should display Expanded when expanded format is selected", () => {
    render(<TournamentFilters {...defaultProps} format="expanded" />);

    expect(screen.getByText("Expanded")).toBeInTheDocument();
  });

  it("should call onRegionChange when a region is selected", async () => {
    const onRegionChange = vi.fn();
    render(
      <TournamentFilters {...defaultProps} onRegionChange={onRegionChange} />
    );

    // Open the region dropdown (first trigger)
    const triggers = screen.getAllByRole("combobox");
    fireEvent.click(triggers[0]);

    // Select North America
    const option = await screen.findByText("North America");
    fireEvent.click(option);

    expect(onRegionChange).toHaveBeenCalledWith("NA");
  });

  it("should call onFormatChange when a format is selected", async () => {
    const onFormatChange = vi.fn();
    render(
      <TournamentFilters {...defaultProps} onFormatChange={onFormatChange} />
    );

    // Open the format dropdown (second trigger)
    const triggers = screen.getAllByRole("combobox");
    fireEvent.click(triggers[1]);

    // Select Standard
    const option = await screen.findByText("Standard");
    fireEvent.click(option);

    expect(onFormatChange).toHaveBeenCalledWith("standard");
  });

  it("should call onTierChange when a tier is selected", async () => {
    const onTierChange = vi.fn();
    render(<TournamentFilters {...defaultProps} onTierChange={onTierChange} />);

    // Open the tier dropdown (third trigger)
    const triggers = screen.getAllByRole("combobox");
    fireEvent.click(triggers[2]);

    // Select Grassroots
    const option = await screen.findByText("Grassroots");
    fireEvent.click(option);

    expect(onTierChange).toHaveBeenCalledWith("grassroots");
  });

  it("should update displayed values when props change", () => {
    const { rerender } = render(<TournamentFilters {...defaultProps} />);

    expect(screen.getByText("All Regions")).toBeInTheDocument();

    rerender(<TournamentFilters {...defaultProps} region="JP" />);

    expect(screen.getByText("Japan")).toBeInTheDocument();
  });
});
