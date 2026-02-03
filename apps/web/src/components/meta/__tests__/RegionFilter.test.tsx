import React from "react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { RegionFilter } from "../RegionFilter";

// Mock pointer capture and scroll APIs for Radix UI compatibility in jsdom
beforeAll(() => {
  HTMLElement.prototype.hasPointerCapture = vi.fn().mockReturnValue(false);
  HTMLElement.prototype.setPointerCapture = vi.fn();
  HTMLElement.prototype.releasePointerCapture = vi.fn();
  HTMLElement.prototype.scrollIntoView = vi.fn();
  Element.prototype.scrollIntoView = vi.fn();
});

describe("RegionFilter", () => {
  it("should render with default value", () => {
    const onChange = vi.fn();
    render(<RegionFilter value="global" onChange={onChange} />);

    expect(screen.getByTestId("region-filter")).toBeInTheDocument();
  });

  it("should display Global when selected", () => {
    const onChange = vi.fn();
    render(<RegionFilter value="global" onChange={onChange} />);

    expect(screen.getByText("Global")).toBeInTheDocument();
  });

  it("should display Japan when selected", () => {
    const onChange = vi.fn();
    render(<RegionFilter value="JP" onChange={onChange} />);

    expect(screen.getByText("Japan")).toBeInTheDocument();
  });

  it("should display North America when selected", () => {
    const onChange = vi.fn();
    render(<RegionFilter value="NA" onChange={onChange} />);

    expect(screen.getByText("North America")).toBeInTheDocument();
  });

  it("should display Europe when selected", () => {
    const onChange = vi.fn();
    render(<RegionFilter value="EU" onChange={onChange} />);

    expect(screen.getByText("Europe")).toBeInTheDocument();
  });

  it("should display Latin America when selected", () => {
    const onChange = vi.fn();
    render(<RegionFilter value="LATAM" onChange={onChange} />);

    expect(screen.getByText("Latin America")).toBeInTheDocument();
  });

  it("should display Oceania when selected", () => {
    const onChange = vi.fn();
    render(<RegionFilter value="OCE" onChange={onChange} />);

    expect(screen.getByText("Oceania")).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    const onChange = vi.fn();
    render(
      <RegionFilter
        value="global"
        onChange={onChange}
        className="custom-class"
      />
    );

    expect(screen.getByTestId("region-filter")).toHaveClass("custom-class");
  });

  it("should call onChange when a region is selected", async () => {
    const onChange = vi.fn();
    render(<RegionFilter value="global" onChange={onChange} />);

    // Open the select dropdown
    const trigger = screen.getByTestId("region-filter");
    fireEvent.click(trigger);

    // Wait for dropdown to appear and select Japan
    const japanOption = await screen.findByText("Japan");
    fireEvent.click(japanOption);

    expect(onChange).toHaveBeenCalledWith("JP");
  });

  it("should pass value correctly to Select component", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <RegionFilter value="NA" onChange={onChange} />
    );

    // Check initial value is displayed
    expect(screen.getByText("North America")).toBeInTheDocument();

    // Rerender with different value
    rerender(<RegionFilter value="EU" onChange={onChange} />);
    expect(screen.getByText("Europe")).toBeInTheDocument();
  });
});
