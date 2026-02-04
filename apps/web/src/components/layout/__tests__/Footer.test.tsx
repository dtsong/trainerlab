import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Footer } from "../Footer";

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

describe("Footer", () => {
  it("should render the TrainerLab brand name", () => {
    render(<Footer />);
    expect(screen.getByText("TrainerLab")).toBeInTheDocument();
  });

  it("should render the tagline", () => {
    render(<Footer />);
    expect(
      screen.getByText("Competitive intelligence platform for Pokemon TCG")
    ).toBeInTheDocument();
  });

  it("should render brand link pointing to home", () => {
    render(<Footer />);
    const brandLink = screen.getByText("TrainerLab").closest("a");
    expect(brandLink).toHaveAttribute("href", "/");
  });

  describe("product links", () => {
    it("should render Cards link", () => {
      render(<Footer />);
      const link = screen.getByText("Cards").closest("a");
      expect(link).toHaveAttribute("href", "/cards");
    });

    it("should render Decks link", () => {
      render(<Footer />);
      const link = screen.getByText("Decks").closest("a");
      expect(link).toHaveAttribute("href", "/decks");
    });

    it("should render Meta link", () => {
      render(<Footer />);
      const link = screen.getByText("Meta").closest("a");
      expect(link).toHaveAttribute("href", "/meta");
    });
  });

  describe("resource links", () => {
    it("should render Documentation link", () => {
      render(<Footer />);
      const link = screen.getByText("Documentation").closest("a");
      expect(link).toHaveAttribute("href", "/docs");
    });

    it("should render API link", () => {
      render(<Footer />);
      const link = screen.getByText("API").closest("a");
      expect(link).toHaveAttribute("href", "/api");
    });
  });

  describe("legal links", () => {
    it("should render Privacy link", () => {
      render(<Footer />);
      const link = screen.getByText("Privacy").closest("a");
      expect(link).toHaveAttribute("href", "/privacy");
    });

    it("should render Terms link", () => {
      render(<Footer />);
      const link = screen.getByText("Terms").closest("a");
      expect(link).toHaveAttribute("href", "/terms");
    });
  });

  describe("section headers", () => {
    it("should render Product section header", () => {
      render(<Footer />);
      expect(screen.getByText("Product")).toBeInTheDocument();
    });

    it("should render Resources section header", () => {
      render(<Footer />);
      expect(screen.getByText("Resources")).toBeInTheDocument();
    });

    it("should render Legal section header", () => {
      render(<Footer />);
      expect(screen.getByText("Legal")).toBeInTheDocument();
    });
  });

  describe("social links", () => {
    it("should render GitHub link with correct href", () => {
      render(<Footer />);
      const githubLink = screen.getByText("GitHub").closest("a");
      expect(githubLink).toHaveAttribute(
        "href",
        "https://github.com/trainerlab"
      );
    });

    it("should render Twitter link with correct href", () => {
      render(<Footer />);
      const twitterLink = screen.getByText("Twitter").closest("a");
      expect(twitterLink).toHaveAttribute(
        "href",
        "https://twitter.com/trainerlab"
      );
    });

    it("should open social links in new tab", () => {
      render(<Footer />);
      const githubLink = screen.getByText("GitHub").closest("a");
      expect(githubLink).toHaveAttribute("target", "_blank");
      expect(githubLink).toHaveAttribute("rel", "noopener noreferrer");
    });
  });

  describe("copyright", () => {
    it("should display the current year in copyright", () => {
      render(<Footer />);
      const currentYear = new Date().getFullYear();
      expect(
        screen.getByText(
          `\u00A9 ${currentYear} TrainerLab. All rights reserved.`
        )
      ).toBeInTheDocument();
    });

    it("should display the Pokemon trademark notice", () => {
      render(<Footer />);
      expect(
        screen.getByText(/Pokemon and all related trademarks/)
      ).toBeInTheDocument();
    });
  });

  it("should render within a footer element", () => {
    render(<Footer />);
    const footer = document.querySelector("footer");
    expect(footer).toBeInTheDocument();
  });
});
