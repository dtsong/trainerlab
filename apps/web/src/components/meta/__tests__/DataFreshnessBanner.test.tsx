import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { DataFreshnessBanner } from "../DataFreshnessBanner";

import type { ApiDataFreshness } from "@trainerlab/shared-types";

describe("DataFreshnessBanner", () => {
  it("renders nothing when freshness is missing", () => {
    const { container } = render(<DataFreshnessBanner freshness={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders source coverage when provided", () => {
    const freshness: ApiDataFreshness = {
      status: "partial",
      cadence_profile: "tpci_event_cadence",
      snapshot_date: "2026-02-10",
      sample_size: 12,
      source_coverage: ["Limitless", "RK9", "pokemon.com"],
      message: "Partial data available.",
    };

    render(<DataFreshnessBanner freshness={freshness} />);

    expect(screen.getByTestId("data-freshness-banner")).toBeInTheDocument();
    expect(
      screen.getByText("Sources: Limitless, RK9, pokemon.com")
    ).toBeInTheDocument();
  });
});
