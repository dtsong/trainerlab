import React from "react";
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { CardFiltersSkeleton } from "../CardFiltersSkeleton";

describe("CardFiltersSkeleton", () => {
  describe("basic rendering", () => {
    it("should render without errors", () => {
      const { container } = render(<CardFiltersSkeleton />);
      expect(container.firstChild).toBeInTheDocument();
    });

    it("should render four skeleton filter placeholders", () => {
      const { container } = render(<CardFiltersSkeleton />);

      const skeletonItems = container.querySelectorAll(".animate-pulse");
      expect(skeletonItems).toHaveLength(4);
    });
  });

  describe("dimensions", () => {
    it("should render the third skeleton wider than the others", () => {
      const { container } = render(<CardFiltersSkeleton />);

      const skeletonItems = container.querySelectorAll(".animate-pulse");

      // First, second, and fourth should be 140px wide
      expect(skeletonItems[0]).toHaveClass("w-[140px]");
      expect(skeletonItems[1]).toHaveClass("w-[140px]");
      // Third should be 180px wide (the set filter)
      expect(skeletonItems[2]).toHaveClass("w-[180px]");
      // Fourth should be 140px wide
      expect(skeletonItems[3]).toHaveClass("w-[140px]");
    });

    it("should render all skeletons with correct height", () => {
      const { container } = render(<CardFiltersSkeleton />);

      const skeletonItems = container.querySelectorAll(".animate-pulse");
      skeletonItems.forEach((item) => {
        expect(item).toHaveClass("h-10");
      });
    });
  });

  describe("className handling", () => {
    it("should accept custom className", () => {
      const { container } = render(
        <CardFiltersSkeleton className="custom-skeleton" />
      );

      expect(container.firstChild).toHaveClass("custom-skeleton");
    });

    it("should preserve default flex layout classes", () => {
      const { container } = render(<CardFiltersSkeleton />);

      expect(container.firstChild).toHaveClass("flex");
      expect(container.firstChild).toHaveClass("flex-wrap");
      expect(container.firstChild).toHaveClass("gap-3");
      expect(container.firstChild).toHaveClass("items-center");
    });
  });

  describe("styling", () => {
    it("should apply animate-pulse to all skeleton items", () => {
      const { container } = render(<CardFiltersSkeleton />);

      const skeletonItems = container.querySelectorAll(".animate-pulse");
      expect(skeletonItems.length).toBe(4);
    });

    it("should apply rounded-md to all skeleton items", () => {
      const { container } = render(<CardFiltersSkeleton />);

      const skeletonItems = container.querySelectorAll(".rounded-md");
      expect(skeletonItems.length).toBe(4);
    });

    it("should apply bg-muted to all skeleton items", () => {
      const { container } = render(<CardFiltersSkeleton />);

      const skeletonItems = container.querySelectorAll(".bg-muted");
      expect(skeletonItems.length).toBe(4);
    });
  });
});
