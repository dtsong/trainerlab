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
    expect(screen.getByTestId("update-window-copy")).toHaveTextContent(
      "Expected update window: by Tuesday UTC after the latest major."
    );
  });

  it("renders no-data copy for official cadence", () => {
    const freshness: ApiDataFreshness = {
      status: "no_data",
      cadence_profile: "tpci_event_cadence",
      message: "No official data yet.",
    };

    render(<DataFreshnessBanner freshness={freshness} />);

    expect(screen.getByTestId("update-window-copy")).toHaveTextContent(
      "Expected first official signal by Tuesday UTC post-major."
    );
  });

  it("renders grassroots cadence window for stale data", () => {
    const freshness: ApiDataFreshness = {
      status: "stale",
      cadence_profile: "grassroots_daily_cadence",
      message: "Data may be delayed.",
    };

    render(<DataFreshnessBanner freshness={freshness} />);

    expect(screen.getByTestId("update-window-copy")).toHaveTextContent(
      "Expected update window: within 24-48 hours."
    );
  });

  it("omits expected window copy for fresh status", () => {
    const freshness: ApiDataFreshness = {
      status: "fresh",
      cadence_profile: "default_cadence",
      message: "Fresh data available.",
    };

    render(<DataFreshnessBanner freshness={freshness} />);

    expect(screen.queryByTestId("update-window-copy")).not.toBeInTheDocument();
  });
});
