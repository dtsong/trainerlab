import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { JPContentCard } from "../JPContentCard";

describe("JPContentCard", () => {
  const defaultProps = {
    title: "Top Decks After Nihil Zero",
    excerpt: "A look at the dominant decks in post-rotation Japan.",
    sourceUrl: "https://pokecabook.com/article/456",
    sourceName: "Pokecabook",
    contentType: "article",
    publishedDate: "2026-01-30",
    archetypeRefs: ["Charizard ex", "Raging Bolt ex", "Dragapult ex"],
  };

  it("should render the title", () => {
    render(<JPContentCard {...defaultProps} />);

    expect(screen.getByText("Top Decks After Nihil Zero")).toBeInTheDocument();
  });

  it("should render the excerpt", () => {
    render(<JPContentCard {...defaultProps} />);

    expect(
      screen.getByText("A look at the dominant decks in post-rotation Japan.")
    ).toBeInTheDocument();
  });

  it("should render the source badge", () => {
    render(<JPContentCard {...defaultProps} />);

    // sourceName rendered as a Badge and also in the TranslationBadge
    const elements = screen.getAllByText("Pokecabook");
    expect(elements.length).toBeGreaterThanOrEqual(1);
  });

  it("should render the translation badge", () => {
    render(<JPContentCard {...defaultProps} />);

    expect(screen.getByText(/Machine-translated/)).toBeInTheDocument();
  });

  it("should render the published date formatted", () => {
    render(<JPContentCard {...defaultProps} />);

    // "2026-01-30" formats via date-fns; may show Jan 29 or Jan 30
    // depending on timezone. Just verify a date is rendered.
    expect(screen.getByText(/Jan \d+, 2026/)).toBeInTheDocument();
  });

  it("should render archetype ref tags", () => {
    render(<JPContentCard {...defaultProps} />);

    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    expect(screen.getByText("Raging Bolt ex")).toBeInTheDocument();
    expect(screen.getByText("Dragapult ex")).toBeInTheDocument();
  });

  it("should limit archetype refs to 5", () => {
    const manyRefs = [
      "Charizard ex",
      "Raging Bolt ex",
      "Dragapult ex",
      "Lugia VSTAR",
      "Gardevoir ex",
      "Regidrago VSTAR",
      "Lost Zone Box",
    ];
    render(<JPContentCard {...defaultProps} archetypeRefs={manyRefs} />);

    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    expect(screen.getByText("Gardevoir ex")).toBeInTheDocument();
    // 6th and 7th should not render
    expect(screen.queryByText("Regidrago VSTAR")).not.toBeInTheDocument();
    expect(screen.queryByText("Lost Zone Box")).not.toBeInTheDocument();
  });

  it("should render 'Article' type label for article content type", () => {
    render(<JPContentCard {...defaultProps} contentType="article" />);

    expect(screen.getByText("Article")).toBeInTheDocument();
  });

  it("should render 'Tier List' type label for tier_list content type", () => {
    render(<JPContentCard {...defaultProps} contentType="tier_list" />);

    expect(screen.getByText("Tier List")).toBeInTheDocument();
  });

  it("should render external link to sourceUrl", () => {
    render(<JPContentCard {...defaultProps} />);

    const links = screen.getAllByRole("link");
    const externalLink = links.find(
      (link) => link.getAttribute("title") === "View original"
    );
    expect(externalLink).toHaveAttribute(
      "href",
      "https://pokecabook.com/article/456"
    );
    expect(externalLink).toHaveAttribute("target", "_blank");
  });

  it("should handle null title gracefully", () => {
    render(<JPContentCard {...defaultProps} title={null} />);

    expect(
      screen.queryByText("Top Decks After Nihil Zero")
    ).not.toBeInTheDocument();
    // Should still render other content
    expect(screen.getByText(/Machine-translated/)).toBeInTheDocument();
  });

  it("should handle null excerpt gracefully", () => {
    render(<JPContentCard {...defaultProps} excerpt={null} />);

    expect(
      screen.queryByText("A look at the dominant decks in post-rotation Japan.")
    ).not.toBeInTheDocument();
  });

  it("should handle null publishedDate gracefully", () => {
    render(<JPContentCard {...defaultProps} publishedDate={null} />);

    expect(screen.queryByText("Jan 30, 2026")).not.toBeInTheDocument();
  });

  it("should handle null archetypeRefs gracefully", () => {
    render(<JPContentCard {...defaultProps} archetypeRefs={null} />);

    expect(screen.queryByText("Charizard ex")).not.toBeInTheDocument();
  });

  it("should handle empty archetypeRefs array", () => {
    render(<JPContentCard {...defaultProps} archetypeRefs={[]} />);

    // No archetype tags rendered, but card should still render
    expect(screen.getByText("Top Decks After Nihil Zero")).toBeInTheDocument();
  });

  it("should handle null sourceName", () => {
    render(<JPContentCard {...defaultProps} sourceName={null} />);

    // Should still render the translation badge and type
    expect(screen.getByText(/Machine-translated/)).toBeInTheDocument();
    expect(screen.getByText("Article")).toBeInTheDocument();
  });
});
