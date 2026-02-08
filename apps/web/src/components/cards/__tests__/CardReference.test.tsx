import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { CardReference } from "../CardReference";

vi.mock("next/image", () => ({
  default: (props: Record<string, unknown>) => <img {...props} />,
}));

describe("CardReference", () => {
  it("renders card name when provided", () => {
    render(<CardReference cardId="sv4-54" cardName="Charizard ex" />);

    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    expect(screen.getByText("sv4-54")).toBeInTheDocument();
  });

  it("falls back to card ID when name is null", () => {
    render(<CardReference cardId="sv4-54" cardName={null} />);

    expect(screen.getByText("sv4-54")).toBeInTheDocument();
  });

  it("falls back to card ID when name is undefined", () => {
    render(<CardReference cardId="sv4-54" />);

    expect(screen.getByText("sv4-54")).toBeInTheDocument();
  });

  it("renders badge variant with outline badge", () => {
    const { container } = render(
      <CardReference cardId="sv4-54" cardName="Charizard ex" variant="badge" />
    );

    // Badge component renders with badge classes
    const badge = container.querySelector("[class*='rounded-full']");
    expect(badge).toBeInTheDocument();
  });

  it("renders inline variant by default", () => {
    const { container } = render(
      <CardReference cardId="sv4-54" cardName="Charizard ex" />
    );

    // Inline variant has hover:bg-muted/50 class
    const inline = container.querySelector("[class*='hover']");
    expect(inline).toBeInTheDocument();
  });

  it("shows thumbnail when showThumbnail is true", () => {
    render(
      <CardReference
        cardId="sv4-54"
        cardName="Charizard ex"
        imageSmall="https://example.com/card.png"
        showThumbnail
      />
    );

    // CardImage renders an img with the card name as alt
    const thumbnail = screen.getByAltText("Charizard ex");
    expect(thumbnail).toBeInTheDocument();
  });

  it("does not show thumbnail when showThumbnail is false", () => {
    render(
      <CardReference
        cardId="sv4-54"
        cardName="Charizard ex"
        imageSmall="https://example.com/card.png"
      />
    );

    // Without showThumbnail, there should be no thumbnail img
    // The hover card image is in a portal, not in the main render
    expect(screen.queryByAltText("Charizard ex")).not.toBeInTheDocument();
  });

  it("does not render hover card when imageSmall is null", () => {
    const { container } = render(
      <CardReference cardId="sv4-54" cardName="Charizard ex" />
    );

    // No HoverCard trigger should exist
    expect(container.querySelector("[data-state]")).not.toBeInTheDocument();
  });

  it("renders hover card trigger when imageSmall is provided", () => {
    const { container } = render(
      <CardReference
        cardId="sv4-54"
        cardName="Charizard ex"
        imageSmall="https://example.com/card.png"
      />
    );

    // HoverCard trigger has data-state attribute
    const trigger = container.querySelector("[data-state]");
    expect(trigger).toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(
      <CardReference
        cardId="sv4-54"
        cardName="Charizard ex"
        className="custom-test-class"
      />
    );

    const el = document.querySelector(".custom-test-class");
    expect(el).toBeInTheDocument();
  });

  it("shows card ID sub-label when name is present", () => {
    render(<CardReference cardId="sv4-54" cardName="Charizard ex" />);

    // Name in sans font, ID in mono font as sub-label
    const idLabel = screen.getByText("sv4-54");
    expect(idLabel).toBeInTheDocument();
    expect(idLabel.className).toContain("font-mono");
  });
});
