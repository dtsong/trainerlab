import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChartSkeleton } from "../ChartSkeleton";

describe("ChartSkeleton", () => {
  it("should render without errors", () => {
    const { container } = render(<ChartSkeleton />);

    expect(container).toBeTruthy();
  });

  it("should display loading text", () => {
    render(<ChartSkeleton />);

    expect(screen.getByText("Loading chart...")).toBeInTheDocument();
  });

  it("should have animate-pulse class for loading animation", () => {
    const { container } = render(<ChartSkeleton />);

    expect(container.firstChild).toHaveClass("animate-pulse");
  });

  it("should use default height of 350px", () => {
    const { container } = render(<ChartSkeleton />);

    expect(container.firstChild).toHaveStyle({ height: "350px" });
  });

  it("should accept a custom height", () => {
    const { container } = render(<ChartSkeleton height={500} />);

    expect(container.firstChild).toHaveStyle({ height: "500px" });
  });

  it("should apply custom className", () => {
    const { container } = render(<ChartSkeleton className="custom-class" />);

    expect(container.firstChild).toHaveClass("custom-class");
  });

  it("should have full width", () => {
    const { container } = render(<ChartSkeleton />);

    expect(container.firstChild).toHaveClass("w-full");
  });

  it("should have rounded corners", () => {
    const { container } = render(<ChartSkeleton />);

    expect(container.firstChild).toHaveClass("rounded-lg");
  });
});
