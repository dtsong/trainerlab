import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ArchetypeSprites } from "../ArchetypeSprites";

describe("ArchetypeSprites", () => {
  const spriteUrls = [
    "https://example.com/sprite1.png",
    "https://example.com/sprite2.png",
  ];

  it("should render sprites correctly", () => {
    render(
      <ArchetypeSprites spriteUrls={spriteUrls} archetypeName="Charizard ex" />
    );

    const container = screen.getByTestId("archetype-sprites");
    expect(container).toBeInTheDocument();

    const images = container.querySelectorAll("img");
    expect(images).toHaveLength(2);
    expect(images[0]).toHaveAttribute("src", spriteUrls[0]);
    expect(images[1]).toHaveAttribute("src", spriteUrls[1]);
  });

  it("should use correct alt text", () => {
    render(
      <ArchetypeSprites spriteUrls={spriteUrls} archetypeName="Gardevoir ex" />
    );

    const images = screen.getAllByAltText("Gardevoir ex");
    expect(images).toHaveLength(2);
  });

  it("should render sm size by default (24x24)", () => {
    render(
      <ArchetypeSprites
        spriteUrls={["https://example.com/sprite.png"]}
        archetypeName="Test"
      />
    );

    const img = screen.getByAltText("Test");
    expect(img).toHaveAttribute("width", "24");
    expect(img).toHaveAttribute("height", "24");
  });

  it("should render md size when specified (32x32)", () => {
    render(
      <ArchetypeSprites
        spriteUrls={["https://example.com/sprite.png"]}
        archetypeName="Test"
        size="md"
      />
    );

    const img = screen.getByAltText("Test");
    expect(img).toHaveAttribute("width", "32");
    expect(img).toHaveAttribute("height", "32");
  });

  it("should render max 3 sprites", () => {
    const manyUrls = [
      "https://example.com/1.png",
      "https://example.com/2.png",
      "https://example.com/3.png",
      "https://example.com/4.png",
      "https://example.com/5.png",
    ];

    render(<ArchetypeSprites spriteUrls={manyUrls} archetypeName="Multi" />);

    const container = screen.getByTestId("archetype-sprites");
    const images = container.querySelectorAll("img");
    expect(images).toHaveLength(3);
  });

  it("should return null for empty spriteUrls", () => {
    const { container } = render(
      <ArchetypeSprites spriteUrls={[]} archetypeName="Empty" />
    );

    expect(screen.queryByTestId("archetype-sprites")).not.toBeInTheDocument();
    expect(container.innerHTML).toBe("");
  });

  it("should hide image on error (not show broken icon)", () => {
    render(
      <ArchetypeSprites
        spriteUrls={["https://example.com/broken.png"]}
        archetypeName="Broken"
      />
    );

    const img = screen.getByAltText("Broken");
    fireEvent.error(img);

    expect(img).toHaveStyle("display: none");
  });

  it("should set loading=lazy on all images", () => {
    render(<ArchetypeSprites spriteUrls={spriteUrls} archetypeName="Lazy" />);

    const images = screen.getAllByAltText("Lazy");
    images.forEach((img) => {
      expect(img).toHaveAttribute("loading", "lazy");
    });
  });

  it("should use inline-flex layout", () => {
    render(<ArchetypeSprites spriteUrls={spriteUrls} archetypeName="Layout" />);

    const container = screen.getByTestId("archetype-sprites");
    expect(container).toHaveClass("inline-flex", "items-center", "gap-1");
  });

  it("should apply custom className", () => {
    render(
      <ArchetypeSprites
        spriteUrls={spriteUrls}
        archetypeName="Custom"
        className="my-custom-class"
      />
    );

    const container = screen.getByTestId("archetype-sprites");
    expect(container).toHaveClass("my-custom-class");
  });
});
