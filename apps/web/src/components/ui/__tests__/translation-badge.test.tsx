import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationBadge } from "../translation-badge";

describe("TranslationBadge", () => {
  it("should render 'Machine-translated' text", () => {
    render(<TranslationBadge />);

    expect(screen.getByText(/Machine-translated/)).toBeInTheDocument();
  });

  it("should show source link when sourceUrl is provided", () => {
    render(
      <TranslationBadge
        sourceUrl="https://pokecabook.com/article/123"
        sourceName="Pokecabook"
      />
    );

    const link = screen.getByRole("link", { name: "Pokecabook" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "https://pokecabook.com/article/123");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("should show 'Original' as link text when sourceName is not provided", () => {
    render(<TranslationBadge sourceUrl="https://example.com/article" />);

    const link = screen.getByRole("link", { name: "Original" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "https://example.com/article");
  });

  it("should omit source link when sourceUrl is not provided", () => {
    render(<TranslationBadge />);

    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("should omit source link when sourceUrl is undefined", () => {
    render(<TranslationBadge sourceUrl={undefined} sourceName="Pokecabook" />);

    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });
});
