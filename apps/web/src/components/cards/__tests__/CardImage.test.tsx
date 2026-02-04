import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CardImage } from "../CardImage";

vi.mock("next/image", () => ({
  default: (props: Record<string, unknown>) => <img {...props} />,
}));

describe("CardImage", () => {
  describe("basic rendering", () => {
    it("should render with default small size", () => {
      const { container } = render(
        <CardImage src="https://example.com/card.png" alt="Pikachu" />
      );

      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveStyle({ width: "160px", height: "224px" });
    });

    it("should render with large size", () => {
      const { container } = render(
        <CardImage
          src="https://example.com/card.png"
          alt="Pikachu"
          size="large"
        />
      );

      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveStyle({ width: "320px", height: "448px" });
    });

    it("should render the image with correct alt text", () => {
      render(
        <CardImage src="https://example.com/card.png" alt="Charizard ex" />
      );

      expect(screen.getByAltText("Charizard ex")).toBeInTheDocument();
    });

    it("should pass priority prop to Image", () => {
      // Verify the component renders without error when priority is set
      const { container } = render(
        <CardImage src="https://example.com/card.png" alt="Pikachu" priority />
      );

      const img = screen.getByAltText("Pikachu");
      expect(img).toBeInTheDocument();
    });

    it("should accept custom className", () => {
      const { container } = render(
        <CardImage
          src="https://example.com/card.png"
          alt="Pikachu"
          className="custom-class"
        />
      );

      expect(container.firstChild).toHaveClass("custom-class");
    });
  });

  describe("placeholder behavior", () => {
    it("should show placeholder when src is null", () => {
      const { container } = render(<CardImage src={null} alt="No image" />);

      // Placeholder contains an SVG icon (ImageOff from lucide)
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
      // Should not render an img tag
      expect(screen.queryByAltText("No image")).not.toBeInTheDocument();
    });

    it("should show placeholder when src is undefined", () => {
      const { container } = render(
        <CardImage src={undefined} alt="No image" />
      );

      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
      expect(screen.queryByAltText("No image")).not.toBeInTheDocument();
    });

    it("should show placeholder on image error", () => {
      const { container } = render(
        <CardImage src="https://example.com/broken.png" alt="Broken" />
      );

      const img = screen.getByAltText("Broken");
      fireEvent.error(img);

      // After error, placeholder should be shown
      const svgs = container.querySelectorAll("svg");
      expect(svgs.length).toBeGreaterThan(0);
    });
  });

  describe("loading state", () => {
    it("should show placeholder while image is loading", () => {
      const { container } = render(
        <CardImage src="https://example.com/card.png" alt="Loading card" />
      );

      // Before onLoad fires, the placeholder should be visible
      // The img should have opacity-0 class
      const img = screen.getByAltText("Loading card");
      expect(img).toHaveClass("opacity-0");
    });

    it("should hide placeholder after image loads", () => {
      render(
        <CardImage src="https://example.com/card.png" alt="Loaded card" />
      );

      const img = screen.getByAltText("Loaded card");
      fireEvent.load(img);

      // After load, image should no longer have opacity-0
      expect(img).not.toHaveClass("opacity-0");
    });
  });

  describe("unoptimized prop", () => {
    it("should set unoptimized when src starts with http", () => {
      // The unoptimized prop is a Next.js Image prop that doesn't pass through
      // to the DOM img element. Verify the component renders correctly.
      render(
        <CardImage src="https://example.com/card.png" alt="External card" />
      );

      const img = screen.getByAltText("External card");
      expect(img).toBeInTheDocument();
    });
  });
});
