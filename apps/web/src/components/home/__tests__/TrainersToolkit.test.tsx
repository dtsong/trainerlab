import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { TrainersToolkit } from "../TrainersToolkit";

// Mock section-label
vi.mock("@/components/ui/section-label", () => ({
  SectionLabel: ({ label }: { label: string }) => <span>{label}</span>,
}));

describe("TrainersToolkit", () => {
  it("should render the section label", () => {
    render(<TrainersToolkit />);

    expect(screen.getByText("Trainer's Toolkit")).toBeInTheDocument();
  });

  it("should render the description text", () => {
    render(<TrainersToolkit />);

    expect(
      screen.getByText(
        "Essential community resources for competitive Pokemon TCG players."
      )
    ).toBeInTheDocument();
  });

  it("should render all four toolkit links", () => {
    render(<TrainersToolkit />);

    expect(screen.getByText("Limitless TCG")).toBeInTheDocument();
    expect(screen.getByText("PTCGO / PTCGL")).toBeInTheDocument();
    expect(screen.getByText("Pokemon TCG Subreddit")).toBeInTheDocument();
    expect(screen.getByText("PokemonCard.io")).toBeInTheDocument();
  });

  it("should render descriptions for each toolkit link", () => {
    render(<TrainersToolkit />);

    expect(
      screen.getByText("Tournament results and decklists database")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Official Pokemon Trading Card Game Online")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Community discussions and deck help")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Card prices and collection tracking")
    ).toBeInTheDocument();
  });

  it("should link to Limitless TCG with correct href", () => {
    render(<TrainersToolkit />);

    const link = screen.getByRole("link", { name: /Limitless TCG/i });
    expect(link).toHaveAttribute("href", "https://limitlesstcg.com");
  });

  it("should link to PTCGO with correct href", () => {
    render(<TrainersToolkit />);

    const link = screen.getByRole("link", { name: /PTCGO/i });
    expect(link).toHaveAttribute(
      "href",
      "https://www.pokemon.com/us/pokemon-tcg/play-online/"
    );
  });

  it("should link to Reddit with correct href", () => {
    render(<TrainersToolkit />);

    const link = screen.getByRole("link", {
      name: /Pokemon TCG Subreddit/i,
    });
    expect(link).toHaveAttribute("href", "https://www.reddit.com/r/pkmntcg/");
  });

  it("should link to PokemonCard.io with correct href", () => {
    render(<TrainersToolkit />);

    const link = screen.getByRole("link", { name: /PokemonCard\.io/i });
    expect(link).toHaveAttribute("href", "https://pokemoncard.io");
  });

  it("should open all links in new tabs", () => {
    render(<TrainersToolkit />);

    const links = screen.getAllByRole("link");
    links.forEach((link) => {
      expect(link).toHaveAttribute("target", "_blank");
      expect(link).toHaveAttribute("rel", "noopener noreferrer");
    });
  });
});
