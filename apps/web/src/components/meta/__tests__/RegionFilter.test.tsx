import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { RegionFilter } from "../RegionFilter";

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
      />,
    );

    expect(screen.getByTestId("region-filter")).toHaveClass("custom-class");
  });
});
