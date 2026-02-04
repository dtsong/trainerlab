import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ArchetypeSurvival } from "../ArchetypeSurvival";

import type { ApiRotationImpact } from "@trainerlab/shared-types";

describe("ArchetypeSurvival", () => {
  const baseImpact: ApiRotationImpact = {
    id: "impact-1",
    format_transition: "F-to-G",
    archetype_id: "arch-1",
    archetype_name: "Charizard ex",
    survival_rating: "adapts",
    rotating_cards: [
      {
        card_name: "Battle VIP Pass",
        count: 4,
        role: "consistency",
        replacement: "Buddy-Buddy Poffin",
      },
      { card_name: "Forest Seal Stone", count: 1, role: "finisher" },
    ],
    analysis: "Loses consistency tools but gains new support.",
    jp_evidence: "JP meta shows continued viability at 8% share.",
    jp_survival_share: 0.08,
  };

  it("should render the archetype name", () => {
    render(<ArchetypeSurvival impact={baseImpact} />);

    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
  });

  it("should render the survival badge", () => {
    render(<ArchetypeSurvival impact={baseImpact} />);

    expect(screen.getByText("Adapts")).toBeInTheDocument();
  });

  it("should display JP survival share when provided", () => {
    render(<ArchetypeSurvival impact={baseImpact} />);

    expect(screen.getByText(/JP Post-Rotation Share:/)).toBeInTheDocument();
    expect(screen.getByText(/8\.0%/)).toBeInTheDocument();
  });

  it("should not display JP survival share when null", () => {
    const impactWithoutJP: ApiRotationImpact = {
      ...baseImpact,
      jp_survival_share: null,
    };

    render(<ArchetypeSurvival impact={impactWithoutJP} />);

    expect(
      screen.queryByText(/JP Post-Rotation Share:/)
    ).not.toBeInTheDocument();
  });

  it("should not display JP survival share when undefined", () => {
    const impactWithoutJP: ApiRotationImpact = {
      ...baseImpact,
      jp_survival_share: undefined,
    };

    render(<ArchetypeSurvival impact={impactWithoutJP} />);

    expect(
      screen.queryByText(/JP Post-Rotation Share:/)
    ).not.toBeInTheDocument();
  });

  it("should show 'Show details' button when details exist", () => {
    render(<ArchetypeSurvival impact={baseImpact} />);

    expect(screen.getByText("Show details")).toBeInTheDocument();
  });

  it("should not show details toggle when no details exist", () => {
    const minimalImpact: ApiRotationImpact = {
      id: "impact-2",
      format_transition: "F-to-G",
      archetype_id: "arch-2",
      archetype_name: "Simple Deck",
      survival_rating: "thrives",
    };

    render(<ArchetypeSurvival impact={minimalImpact} />);

    expect(screen.queryByText("Show details")).not.toBeInTheDocument();
    expect(screen.queryByText("Hide details")).not.toBeInTheDocument();
  });

  it("should expand details on button click", () => {
    render(<ArchetypeSurvival impact={baseImpact} />);

    // Initially details are hidden
    expect(screen.queryByText("Rotating Cards")).not.toBeInTheDocument();

    // Click to expand
    fireEvent.click(screen.getByText("Show details"));

    // Now details should be visible
    expect(screen.getByText("Rotating Cards")).toBeInTheDocument();
    expect(screen.getByText("Hide details")).toBeInTheDocument();
  });

  it("should collapse details when clicking 'Hide details'", () => {
    render(<ArchetypeSurvival impact={baseImpact} />);

    // Expand
    fireEvent.click(screen.getByText("Show details"));
    expect(screen.getByText("Rotating Cards")).toBeInTheDocument();

    // Collapse
    fireEvent.click(screen.getByText("Hide details"));
    expect(screen.queryByText("Rotating Cards")).not.toBeInTheDocument();
  });

  it("should show rotating cards with names and counts when expanded", () => {
    render(<ArchetypeSurvival impact={baseImpact} />);

    fireEvent.click(screen.getByText("Show details"));

    expect(screen.getByText("Battle VIP Pass")).toBeInTheDocument();
    expect(screen.getByText("Forest Seal Stone")).toBeInTheDocument();
  });

  it("should display card roles when available", () => {
    render(<ArchetypeSurvival impact={baseImpact} />);

    fireEvent.click(screen.getByText("Show details"));

    expect(screen.getByText("consistency")).toBeInTheDocument();
    expect(screen.getByText("finisher")).toBeInTheDocument();
  });

  it("should display replacement suggestions when available", () => {
    render(<ArchetypeSurvival impact={baseImpact} />);

    fireEvent.click(screen.getByText("Show details"));

    expect(screen.getByText(/Buddy-Buddy Poffin/)).toBeInTheDocument();
  });

  it("should display analysis when available and expanded", () => {
    render(<ArchetypeSurvival impact={baseImpact} />);

    fireEvent.click(screen.getByText("Show details"));

    expect(screen.getByText("Analysis")).toBeInTheDocument();
    expect(
      screen.getByText("Loses consistency tools but gains new support.")
    ).toBeInTheDocument();
  });

  it("should display JP evidence when available and expanded", () => {
    render(<ArchetypeSurvival impact={baseImpact} />);

    fireEvent.click(screen.getByText("Show details"));

    expect(screen.getByText("JP Evidence")).toBeInTheDocument();
    expect(
      screen.getByText("JP meta shows continued viability at 8% share.")
    ).toBeInTheDocument();
  });

  it("should show details toggle when only analysis is present", () => {
    const analysisOnlyImpact: ApiRotationImpact = {
      id: "impact-3",
      format_transition: "F-to-G",
      archetype_id: "arch-3",
      archetype_name: "Analysis Only",
      survival_rating: "crippled",
      analysis: "Some analysis text.",
    };

    render(<ArchetypeSurvival impact={analysisOnlyImpact} />);

    expect(screen.getByText("Show details")).toBeInTheDocument();
  });

  it("should show details toggle when only jp_evidence is present", () => {
    const jpOnlyImpact: ApiRotationImpact = {
      id: "impact-4",
      format_transition: "F-to-G",
      archetype_id: "arch-4",
      archetype_name: "JP Only",
      survival_rating: "dies",
      jp_evidence: "Some JP evidence.",
    };

    render(<ArchetypeSurvival impact={jpOnlyImpact} />);

    expect(screen.getByText("Show details")).toBeInTheDocument();
  });

  it("should render different survival ratings correctly", () => {
    const diesImpact: ApiRotationImpact = {
      ...baseImpact,
      survival_rating: "dies",
    };

    render(<ArchetypeSurvival impact={diesImpact} />);

    expect(screen.getByText("Dies")).toBeInTheDocument();
  });
});
