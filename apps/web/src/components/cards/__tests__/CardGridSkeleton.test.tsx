import React from "react";
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { CardGridSkeleton } from "../CardGridSkeleton";

describe("CardGridSkeleton", () => {
  describe("basic rendering", () => {
    it("should render without errors", () => {
      const { container } = render(<CardGridSkeleton />);
      expect(container.firstChild).toBeInTheDocument();
    });

    it("should render 12 skeleton cards by default", () => {
      const { container } = render(<CardGridSkeleton />);

      // Each card skeleton has a container div with flex flex-col gap-2
      const cardSkeletons = container.querySelectorAll(".flex.flex-col.gap-2");
      expect(cardSkeletons).toHaveLength(12);
    });
  });

  describe("count prop", () => {
    it("should render custom number of skeleton cards", () => {
      const { container } = render(<CardGridSkeleton count={6} />);

      const cardSkeletons = container.querySelectorAll(".flex.flex-col.gap-2");
      expect(cardSkeletons).toHaveLength(6);
    });

    it("should render 1 skeleton card", () => {
      const { container } = render(<CardGridSkeleton count={1} />);

      const cardSkeletons = container.querySelectorAll(".flex.flex-col.gap-2");
      expect(cardSkeletons).toHaveLength(1);
    });

    it("should render 24 skeleton cards", () => {
      const { container } = render(<CardGridSkeleton count={24} />);

      const cardSkeletons = container.querySelectorAll(".flex.flex-col.gap-2");
      expect(cardSkeletons).toHaveLength(24);
    });
  });

  describe("card skeleton structure", () => {
    it("should render card image skeleton with correct dimensions", () => {
      const { container } = render(<CardGridSkeleton count={1} />);

      const imageSkeletons = container.querySelectorAll(".rounded-lg.bg-muted");
      expect(imageSkeletons.length).toBeGreaterThanOrEqual(1);

      const imageSkeleton = imageSkeletons[0] as HTMLElement;
      expect(imageSkeleton).toHaveStyle({ width: "160px", height: "224px" });
    });

    it("should render card name skeleton placeholder", () => {
      const { container } = render(<CardGridSkeleton count={1} />);

      // Name skeleton: h-4 w-3/4
      const nameSkeleton = container.querySelector(".h-4.w-3\\/4");
      expect(nameSkeleton).toBeInTheDocument();
    });

    it("should render card type skeleton placeholder", () => {
      const { container } = render(<CardGridSkeleton count={1} />);

      // Type skeleton: h-3 w-1/2
      const typeSkeleton = container.querySelector(".h-3.w-1\\/2");
      expect(typeSkeleton).toBeInTheDocument();
    });
  });

  describe("className handling", () => {
    it("should accept custom className", () => {
      const { container } = render(
        <CardGridSkeleton className="custom-grid" />
      );

      expect(container.firstChild).toHaveClass("custom-grid");
    });

    it("should preserve grid layout classes", () => {
      const { container } = render(<CardGridSkeleton />);

      expect(container.firstChild).toHaveClass("grid");
      expect(container.firstChild).toHaveClass("gap-4");
    });
  });

  describe("animation", () => {
    it("should apply animate-pulse to skeleton elements", () => {
      const { container } = render(<CardGridSkeleton count={1} />);

      const animatedElements = container.querySelectorAll(".animate-pulse");
      // Each card has multiple animated elements (image, name, type)
      expect(animatedElements.length).toBeGreaterThanOrEqual(3);
    });

    it("should include shimmer effect on card image skeleton", () => {
      const { container } = render(<CardGridSkeleton count={1} />);

      // The shimmer is a gradient div inside the image skeleton
      const shimmerElement = container.querySelector(".bg-gradient-to-r");
      expect(shimmerElement).toBeInTheDocument();
    });
  });
});
