import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BuildItBanner } from "../BuildItBanner";

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({
    children,
    asChild,
    ...props
  }: {
    children: React.ReactNode;
    asChild?: boolean;
    className?: string;
    variant?: string;
  }) => <div {...props}>{children}</div>,
}));

describe("BuildItBanner", () => {
  it("should render with selected archetype name", () => {
    render(<BuildItBanner selectedArchetype="Charizard ex" />);

    expect(screen.getByText("Build Charizard ex")).toBeInTheDocument();
  });

  it("should render with top deck name when no archetype selected", () => {
    render(<BuildItBanner topDeckName="Lugia VSTAR" />);

    expect(screen.getByText("Build Lugia VSTAR")).toBeInTheDocument();
  });

  it("should render with default 'the top deck' when no names provided", () => {
    render(<BuildItBanner />);

    expect(screen.getByText("Build the top deck")).toBeInTheDocument();
  });

  it("should prefer selectedArchetype over topDeckName", () => {
    render(
      <BuildItBanner
        selectedArchetype="Charizard ex"
        topDeckName="Lugia VSTAR"
      />
    );

    expect(screen.getByText("Build Charizard ex")).toBeInTheDocument();
    expect(screen.queryByText("Lugia VSTAR")).not.toBeInTheDocument();
  });

  it("should render the partner stores subtitle", () => {
    render(<BuildItBanner />);

    expect(
      screen.getByText("Get the cards you need from our partner stores")
    ).toBeInTheDocument();
  });

  it("should render Build Deck button", () => {
    render(<BuildItBanner />);

    expect(screen.getByText("Build Deck")).toBeInTheDocument();
  });

  it("should render TCGPlayer button", () => {
    render(<BuildItBanner />);

    expect(screen.getByText("TCGPlayer")).toBeInTheDocument();
  });

  it("should link Build Deck to deck builder with archetype param", () => {
    render(<BuildItBanner selectedArchetype="Charizard ex" />);

    const buildLink = screen.getByText("Build Deck").closest("a");
    expect(buildLink).toHaveAttribute(
      "href",
      "/decks/new?archetype=Charizard%20ex"
    );
  });

  it("should link Build Deck to deck builder without param when no archetype", () => {
    render(<BuildItBanner />);

    const buildLink = screen.getByText("Build Deck").closest("a");
    expect(buildLink).toHaveAttribute("href", "/decks/new");
  });

  it("should link TCGPlayer to external site", () => {
    render(<BuildItBanner />);

    const tcgLink = screen.getByText("TCGPlayer").closest("a");
    expect(tcgLink).toHaveAttribute(
      "href",
      "https://www.tcgplayer.com/search/pokemon-product/product"
    );
  });

  it("should open TCGPlayer link in a new tab", () => {
    render(<BuildItBanner />);

    const tcgLink = screen.getByText("TCGPlayer").closest("a");
    expect(tcgLink).toHaveAttribute("target", "_blank");
    expect(tcgLink).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("should apply custom className", () => {
    const { container } = render(<BuildItBanner className="custom-class" />);

    expect(container.firstChild).toHaveClass("custom-class");
  });
});
