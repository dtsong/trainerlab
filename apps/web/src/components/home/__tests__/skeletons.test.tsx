import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  SpecimenCardSkeleton,
  IndexCardSkeleton,
  ComparisonRowSkeleton,
} from "../skeletons";

describe("SpecimenCardSkeleton", () => {
  it("should render without crashing", () => {
    const { container } = render(<SpecimenCardSkeleton />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("should have animate-pulse elements for loading effect", () => {
    const { container } = render(<SpecimenCardSkeleton />);
    const pulseElements = container.querySelectorAll(".animate-pulse");
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it("should render rank badge skeleton placeholder", () => {
    const { container } = render(<SpecimenCardSkeleton />);
    const rankBadge = container.querySelector(".rounded-full.animate-pulse");
    expect(rankBadge).toBeInTheDocument();
  });

  it("should render card image skeleton placeholder", () => {
    const { container } = render(<SpecimenCardSkeleton />);
    const imagePlaceholder = container.querySelector(".h-24.w-16");
    expect(imagePlaceholder).toBeInTheDocument();
  });

  it("should render name skeleton placeholder", () => {
    const { container } = render(<SpecimenCardSkeleton />);
    const namePlaceholder = container.querySelector(".h-4.w-20");
    expect(namePlaceholder).toBeInTheDocument();
  });

  it("should render button skeleton placeholder", () => {
    const { container } = render(<SpecimenCardSkeleton />);
    const buttonPlaceholder = container.querySelector(".h-6.w-16");
    expect(buttonPlaceholder).toBeInTheDocument();
  });

  it("should have notebook-cream background styling", () => {
    const { container } = render(<SpecimenCardSkeleton />);
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv.className).toContain("bg-notebook-cream");
  });

  it("should have tape effect element", () => {
    const { container } = render(<SpecimenCardSkeleton />);
    const tapeEffect = container.querySelector(".rotate-12");
    expect(tapeEffect).toBeInTheDocument();
  });
});

describe("IndexCardSkeleton", () => {
  it("should render without crashing", () => {
    const { container } = render(<IndexCardSkeleton />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("should have animate-pulse elements for loading effect", () => {
    const { container } = render(<IndexCardSkeleton />);
    const pulseElements = container.querySelectorAll(".animate-pulse");
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it("should have notebook-cream background styling", () => {
    const { container } = render(<IndexCardSkeleton />);
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv.className).toContain("bg-notebook-cream");
  });

  it("should render paper clip decoration", () => {
    const { container } = render(<IndexCardSkeleton />);
    const paperClip = container.querySelector(".rounded-t-full");
    expect(paperClip).toBeInTheDocument();
  });

  it("should render ruled lines background", () => {
    const { container } = render(<IndexCardSkeleton />);
    const ruledLines = container.querySelector(".bg-ruled-lines");
    expect(ruledLines).toBeInTheDocument();
  });

  it("should render header icon placeholder", () => {
    const { container } = render(<IndexCardSkeleton />);
    const iconPlaceholder = container.querySelector(".h-5.w-5");
    expect(iconPlaceholder).toBeInTheDocument();
  });

  it("should render 3 item skeleton rows", () => {
    const { container } = render(<IndexCardSkeleton />);
    // Each item has a container div, look for the repeating pattern
    const itemContainers = container.querySelectorAll(".space-y-4 > div");
    expect(itemContainers.length).toBe(3);
  });
});

describe("ComparisonRowSkeleton", () => {
  it("should render without crashing", () => {
    const { container } = render(<ComparisonRowSkeleton />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("should use a 2-column grid layout", () => {
    const { container } = render(<ComparisonRowSkeleton />);
    const grid = container.firstChild as HTMLElement;
    expect(grid.className).toContain("grid-cols-2");
  });

  it("should have animate-pulse elements for loading effect", () => {
    const { container } = render(<ComparisonRowSkeleton />);
    const pulseElements = container.querySelectorAll(".animate-pulse");
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it("should render two columns of content", () => {
    const { container } = render(<ComparisonRowSkeleton />);
    const grid = container.firstChild as HTMLElement;
    // Should have 2 direct children (the two columns)
    expect(grid.children.length).toBe(2);
  });

  it("should have a border separator between columns", () => {
    const { container } = render(<ComparisonRowSkeleton />);
    const secondColumn = container.querySelector(".border-l");
    expect(secondColumn).toBeInTheDocument();
  });

  it("should render icon placeholders in both columns", () => {
    const { container } = render(<ComparisonRowSkeleton />);
    const iconPlaceholders = container.querySelectorAll(".h-4.w-4");
    expect(iconPlaceholders.length).toBe(2);
  });

  it("should render name placeholders in both columns", () => {
    const { container } = render(<ComparisonRowSkeleton />);
    const namePlaceholders = container.querySelectorAll(".h-4.w-24");
    expect(namePlaceholders.length).toBe(2);
  });

  it("should render stat placeholders in both columns", () => {
    const { container } = render(<ComparisonRowSkeleton />);
    const statPlaceholders = container.querySelectorAll(".h-3.w-10");
    expect(statPlaceholders.length).toBe(2);
  });
});
