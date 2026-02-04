import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { WhyTrainerLab } from "../WhyTrainerLab";

// Mock section-label
vi.mock("@/components/ui/section-label", () => ({
  SectionLabel: ({ label }: { label: string }) => <span>{label}</span>,
}));

describe("WhyTrainerLab", () => {
  it("should render the section label", () => {
    render(<WhyTrainerLab />);

    expect(screen.getByText("Why TrainerLab")).toBeInTheDocument();
  });

  it("should render the section annotation", () => {
    render(<WhyTrainerLab />);

    expect(
      screen.getByText("Your competitive edge in Pokemon TCG research")
    ).toBeInTheDocument();
  });

  it("should render all three value proposition titles", () => {
    render(<WhyTrainerLab />);

    expect(screen.getByText("Data-Driven")).toBeInTheDocument();
    expect(screen.getByText("Japan Insights")).toBeInTheDocument();
    expect(screen.getByText("All-in-One")).toBeInTheDocument();
  });

  it("should render the Data-Driven description", () => {
    render(<WhyTrainerLab />);

    expect(
      screen.getByText(/Real tournament results, not theory/)
    ).toBeInTheDocument();
  });

  it("should render the Japan Insights description", () => {
    render(<WhyTrainerLab />);

    expect(screen.getByText(/Stay ahead of the meta/)).toBeInTheDocument();
  });

  it("should render the All-in-One description", () => {
    render(<WhyTrainerLab />);

    expect(
      screen.getByText(
        /Meta analysis, deck building, and card database in one place/
      )
    ).toBeInTheDocument();
  });

  it("should render annotations for each value prop", () => {
    render(<WhyTrainerLab />);

    expect(screen.getByText("12k+ decklists")).toBeInTheDocument();
    expect(screen.getByText("2-3 months ahead")).toBeInTheDocument();
    expect(screen.getByText("Everything you need")).toBeInTheDocument();
  });

  it("should render three notebook binding hole decorations", () => {
    const { container } = render(<WhyTrainerLab />);

    // The binding holes are rendered as 3 div elements with rounded-full class
    const bindingHoles = container.querySelectorAll(
      ".rounded-full.border-2.border-notebook-grid"
    );
    expect(bindingHoles).toHaveLength(3);
  });
});
