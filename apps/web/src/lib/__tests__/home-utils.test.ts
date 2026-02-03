import { describe, it, expect } from "vitest";
import type {
  ApiMetaSnapshot,
  ApiMetaHistoryResponse,
} from "@trainerlab/shared-types";
import {
  computeTrends,
  computeJPDivergence,
  buildJPComparisons,
  computeHeroStats,
  computeMetaMovers,
} from "../home-utils";

/**
 * Helper to create snapshots with decimal shares (0.0–1.0) matching the API format.
 * The utility functions convert these to percentage-scale internally.
 */
function makeSnapshot(
  archetypes: { name: string; share: number }[],
  overrides: Partial<ApiMetaSnapshot> = {}
): ApiMetaSnapshot {
  return {
    snapshot_date: "2025-01-15",
    region: null,
    format: "standard",
    best_of: 3,
    archetype_breakdown: archetypes.map((a) => ({
      name: a.name,
      share: a.share,
    })),
    card_usage: [],
    sample_size: 100,
    ...overrides,
  };
}

function makeHistory(snapshots: ApiMetaSnapshot[]): ApiMetaHistoryResponse {
  return { snapshots };
}

describe("computeTrends", () => {
  it("should return empty array when globalMeta is undefined", () => {
    expect(computeTrends(undefined, undefined, undefined)).toEqual([]);
  });

  it("should return empty array when archetype_breakdown is empty", () => {
    const snapshot = makeSnapshot([]);
    expect(computeTrends(snapshot, undefined, undefined)).toEqual([]);
  });

  it("should return archetypes with stable trend when no history", () => {
    const global = makeSnapshot([
      { name: "Charizard ex", share: 0.185 },
      { name: "Lugia VSTAR", share: 0.142 },
    ]);

    const result = computeTrends(global, undefined, undefined, 5);

    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({
      rank: 1,
      name: "Charizard ex",
      metaShare: 18.5,
      trend: "stable",
      trendValue: undefined,
      jpSignal: undefined,
    });
  });

  it("should detect up trend when share increases >0.5pp", () => {
    const current = makeSnapshot([{ name: "Charizard ex", share: 0.185 }]);
    const previous = makeSnapshot([{ name: "Charizard ex", share: 0.17 }]);
    const history = makeHistory([previous, current]);

    const result = computeTrends(current, history, undefined, 5);

    expect(result[0].trend).toBe("up");
    expect(result[0].trendValue).toBe(1.5);
  });

  it("should detect down trend when share decreases >0.5pp", () => {
    const current = makeSnapshot([{ name: "Charizard ex", share: 0.15 }]);
    const previous = makeSnapshot([{ name: "Charizard ex", share: 0.17 }]);
    const history = makeHistory([previous, current]);

    const result = computeTrends(current, history, undefined, 5);

    expect(result[0].trend).toBe("down");
    expect(result[0].trendValue).toBe(-2);
  });

  it("should show stable when change is within 0.5pp", () => {
    const current = makeSnapshot([{ name: "Charizard ex", share: 0.185 }]);
    const previous = makeSnapshot([{ name: "Charizard ex", share: 0.183 }]);
    const history = makeHistory([previous, current]);

    const result = computeTrends(current, history, undefined, 5);

    expect(result[0].trend).toBe("stable");
    expect(result[0].trendValue).toBe(0.2);
  });

  it("should show stable at exactly 0.5pp boundary", () => {
    const current = makeSnapshot([{ name: "Charizard ex", share: 0.185 }]);
    const previous = makeSnapshot([{ name: "Charizard ex", share: 0.18 }]);
    const history = makeHistory([previous, current]);

    const result = computeTrends(current, history, undefined, 5);

    expect(result[0].trend).toBe("stable");
    expect(result[0].trendValue).toBe(0.5);
  });

  it("should show up just above 0.5pp boundary", () => {
    const current = makeSnapshot([{ name: "Charizard ex", share: 0.186 }]);
    const previous = makeSnapshot([{ name: "Charizard ex", share: 0.18 }]);
    const history = makeHistory([previous, current]);

    const result = computeTrends(current, history, undefined, 5);

    expect(result[0].trend).toBe("up");
  });

  it("should compute JP signal when divergence >2pp", () => {
    const global = makeSnapshot([{ name: "Charizard ex", share: 0.185 }]);
    const jp = makeSnapshot([{ name: "Charizard ex", share: 0.22 }]);

    const result = computeTrends(global, undefined, jp, 5);

    expect(result[0].jpSignal).toBe(3.5);
  });

  it("should not show JP signal when divergence is <=2pp", () => {
    const global = makeSnapshot([{ name: "Charizard ex", share: 0.185 }]);
    const jp = makeSnapshot([{ name: "Charizard ex", share: 0.195 }]);

    const result = computeTrends(global, undefined, jp, 5);

    expect(result[0].jpSignal).toBeUndefined();
  });

  it("should not show JP signal at exactly 2pp boundary", () => {
    const global = makeSnapshot([{ name: "Charizard ex", share: 0.18 }]);
    const jp = makeSnapshot([{ name: "Charizard ex", share: 0.2 }]);

    const result = computeTrends(global, undefined, jp, 5);

    expect(result[0].jpSignal).toBeUndefined();
  });

  it("should respect the limit parameter", () => {
    const global = makeSnapshot([
      { name: "A", share: 0.2 },
      { name: "B", share: 0.15 },
      { name: "C", share: 0.1 },
      { name: "D", share: 0.08 },
      { name: "E", share: 0.05 },
    ]);

    const result = computeTrends(global, undefined, undefined, 3);

    expect(result).toHaveLength(3);
    expect(result[2].name).toBe("C");
  });

  it("should handle single snapshot in history (no previous to compare)", () => {
    const current = makeSnapshot([{ name: "Charizard ex", share: 0.185 }]);
    const history = makeHistory([current]);

    const result = computeTrends(current, history, undefined, 5);

    expect(result[0].trend).toBe("stable");
    expect(result[0].trendValue).toBeUndefined();
  });
});

describe("computeJPDivergence", () => {
  it("should return no divergence when both are undefined", () => {
    const result = computeJPDivergence(undefined, undefined);
    expect(result.hasSignificantDivergence).toBe(false);
    expect(result.message).toBe("");
  });

  it("should return no divergence when JP data is empty", () => {
    const global = makeSnapshot([{ name: "Charizard ex", share: 0.185 }]);
    const result = computeJPDivergence(global, makeSnapshot([]));
    expect(result.hasSignificantDivergence).toBe(false);
  });

  it("should detect divergence when JP has archetypes not in global top 10", () => {
    const global = makeSnapshot([
      { name: "Charizard ex", share: 0.185 },
      { name: "Lugia VSTAR", share: 0.142 },
    ]);
    const jp = makeSnapshot([
      { name: "Raging Bolt ex", share: 0.22 },
      { name: "Charizard ex", share: 0.15 },
    ]);

    const result = computeJPDivergence(global, jp);

    expect(result.hasSignificantDivergence).toBe(true);
    expect(result.message).toContain("Raging Bolt ex");
  });

  it("should detect divergence when share difference >5pp", () => {
    const global = makeSnapshot([
      { name: "Charizard ex", share: 0.1 },
      { name: "Lugia VSTAR", share: 0.142 },
    ]);
    const jp = makeSnapshot([{ name: "Charizard ex", share: 0.22 }]);

    const result = computeJPDivergence(global, jp);

    expect(result.hasSignificantDivergence).toBe(true);
    expect(result.message).toContain("Charizard ex");
  });

  it("should not detect divergence at exactly 5pp share difference", () => {
    const global = makeSnapshot([{ name: "Charizard ex", share: 0.1 }]);
    const jp = makeSnapshot([{ name: "Charizard ex", share: 0.15 }]);

    const result = computeJPDivergence(global, jp);

    expect(result.hasSignificantDivergence).toBe(false);
  });

  it("should detect divergence just above 5pp share difference", () => {
    const global = makeSnapshot([{ name: "Charizard ex", share: 0.1 }]);
    const jp = makeSnapshot([{ name: "Charizard ex", share: 0.151 }]);

    const result = computeJPDivergence(global, jp);

    expect(result.hasSignificantDivergence).toBe(true);
  });

  it("should show no divergence when metas are similar", () => {
    const global = makeSnapshot([
      { name: "Charizard ex", share: 0.185 },
      { name: "Lugia VSTAR", share: 0.142 },
      { name: "Gardevoir ex", share: 0.12 },
    ]);
    const jp = makeSnapshot([
      { name: "Charizard ex", share: 0.17 },
      { name: "Lugia VSTAR", share: 0.135 },
    ]);

    const result = computeJPDivergence(global, jp);

    expect(result.hasSignificantDivergence).toBe(false);
  });

  it("should list multiple divergent archetypes with 'and'", () => {
    const global = makeSnapshot([{ name: "Charizard ex", share: 0.185 }]);
    const jp = makeSnapshot([
      { name: "Raging Bolt ex", share: 0.22 },
      { name: "Terapagos ex", share: 0.15 },
    ]);

    const result = computeJPDivergence(global, jp);

    expect(result.hasSignificantDivergence).toBe(true);
    expect(result.message).toContain("Raging Bolt ex and Terapagos ex");
  });
});

describe("buildJPComparisons", () => {
  it("should return empty array when data is undefined", () => {
    expect(buildJPComparisons(undefined, undefined)).toEqual([]);
  });

  it("should return empty when global has no archetypes", () => {
    const jp = makeSnapshot([{ name: "A", share: 0.2 }]);
    expect(buildJPComparisons(makeSnapshot([]), jp)).toEqual([]);
  });

  it("should return empty when JP has no archetypes", () => {
    const global = makeSnapshot([{ name: "A", share: 0.2 }]);
    expect(buildJPComparisons(global, makeSnapshot([]))).toEqual([]);
  });

  it("should build correct comparisons", () => {
    const global = makeSnapshot([
      { name: "Charizard ex", share: 0.185 },
      { name: "Lugia VSTAR", share: 0.142 },
    ]);
    const jp = makeSnapshot([
      { name: "Raging Bolt ex", share: 0.221 },
      { name: "Charizard ex", share: 0.158 },
    ]);

    const result = buildJPComparisons(global, jp, 2);

    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({
      rank: 1,
      jpName: "Raging Bolt ex",
      jpShare: 22.1,
      enName: "Charizard ex",
      enShare: 18.5,
      divergence: 100, // Not in global, so 100% divergence
    });
    expect(result[1].jpName).toBe("Charizard ex");
    expect(result[1].enName).toBe("Lugia VSTAR");
  });

  it("should respect limit parameter", () => {
    const global = makeSnapshot([
      { name: "A", share: 0.2 },
      { name: "B", share: 0.15 },
      { name: "C", share: 0.1 },
    ]);
    const jp = makeSnapshot([
      { name: "X", share: 0.22 },
      { name: "Y", share: 0.18 },
      { name: "Z", share: 0.12 },
    ]);

    expect(buildJPComparisons(global, jp, 2)).toHaveLength(2);
  });

  it("should handle fewer archetypes than limit", () => {
    const global = makeSnapshot([{ name: "A", share: 0.2 }]);
    const jp = makeSnapshot([{ name: "X", share: 0.22 }]);

    const result = buildJPComparisons(global, jp, 3);
    expect(result).toHaveLength(1);
  });
});

describe("computeHeroStats", () => {
  it("should format all values correctly", () => {
    const result = computeHeroStats(47, 12500, 3);

    expect(result.tournamentCount).toBe("47");
    expect(result.decklistCount).toBe("12k+");
    expect(result.upcomingEvents).toBe("3");
  });

  it("should show '--' for undefined values", () => {
    const result = computeHeroStats(undefined, undefined, undefined);

    expect(result.tournamentCount).toBe("--");
    expect(result.decklistCount).toBe("--");
    expect(result.upcomingEvents).toBe("--");
  });

  it("should format thousands as 'Xk+'", () => {
    expect(computeHeroStats(0, 1000, 0).decklistCount).toBe("1k+");
    expect(computeHeroStats(0, 5500, 0).decklistCount).toBe("5k+");
    expect(computeHeroStats(0, 999, 0).decklistCount).toBe("999");
  });

  it("should handle zero values", () => {
    const result = computeHeroStats(0, 0, 0);

    expect(result.tournamentCount).toBe("0");
    expect(result.decklistCount).toBe("0");
    expect(result.upcomingEvents).toBe("0");
  });
});

describe("computeMetaMovers", () => {
  it("should return empty array when no data", () => {
    expect(computeMetaMovers(undefined, undefined)).toEqual([]);
  });

  it("should return empty when no history", () => {
    const current = makeSnapshot([{ name: "A", share: 0.2 }]);
    expect(computeMetaMovers(current, undefined)).toEqual([]);
  });

  it("should return empty when history has no archetypes", () => {
    const current = makeSnapshot([{ name: "A", share: 0.2 }]);
    const history = makeHistory([makeSnapshot([])]);
    expect(computeMetaMovers(current, history)).toEqual([]);
  });

  it("should identify archetypes with significant changes", () => {
    const old = makeSnapshot([
      { name: "A", share: 0.1 },
      { name: "B", share: 0.15 },
      { name: "C", share: 0.12 },
    ]);
    const current = makeSnapshot([
      { name: "A", share: 0.15 },
      { name: "B", share: 0.11 },
      { name: "C", share: 0.123 },
    ]);
    const history = makeHistory([old, current]);

    const result = computeMetaMovers(current, history, 3);

    expect(result).toHaveLength(2); // C is under 0.5pp threshold
    expect(result[0].name).toBe("A");
    expect(result[0].changeDirection).toBe("up");
    expect(result[0].changeValue).toBe(5);
    expect(result[1].name).toBe("B");
    expect(result[1].changeDirection).toBe("down");
    expect(result[1].changeValue).toBe(4);
  });

  it("should sort by magnitude of change", () => {
    const old = makeSnapshot([
      { name: "A", share: 0.1 },
      { name: "B", share: 0.2 },
    ]);
    const current = makeSnapshot([
      { name: "A", share: 0.12 },
      { name: "B", share: 0.12 },
    ]);
    const history = makeHistory([old, current]);

    const result = computeMetaMovers(current, history, 3);

    expect(result[0].name).toBe("B"); // -8 > +2
    expect(result[1].name).toBe("A");
  });

  it("should respect limit", () => {
    const old = makeSnapshot([
      { name: "A", share: 0.1 },
      { name: "B", share: 0.15 },
      { name: "C", share: 0.12 },
    ]);
    const current = makeSnapshot([
      { name: "A", share: 0.15 },
      { name: "B", share: 0.1 },
      { name: "C", share: 0.08 },
    ]);
    const history = makeHistory([old, current]);

    const result = computeMetaMovers(current, history, 2);

    expect(result).toHaveLength(2);
  });

  it("should treat new archetypes as rising from 0", () => {
    const old = makeSnapshot([{ name: "A", share: 0.1 }]);
    const current = makeSnapshot([
      { name: "A", share: 0.1 },
      { name: "B", share: 0.08 },
    ]);
    const history = makeHistory([old, current]);

    const result = computeMetaMovers(current, history, 3);

    expect(result).toHaveLength(1);
    expect(result[0].name).toBe("B");
    expect(result[0].changeDirection).toBe("up");
    expect(result[0].changeValue).toBe(8);
  });

  it("should exclude archetypes at exactly 0.5pp change boundary", () => {
    const old = makeSnapshot([{ name: "A", share: 0.1 }]);
    const current = makeSnapshot([{ name: "A", share: 0.105 }]);
    const history = makeHistory([old, current]);

    const result = computeMetaMovers(current, history, 3);

    expect(result).toHaveLength(0);
  });

  it("should compare against oldest snapshot when history has 3+ entries", () => {
    const oldest = makeSnapshot([{ name: "A", share: 0.1 }]);
    const middle = makeSnapshot([{ name: "A", share: 0.14 }]);
    const current = makeSnapshot([{ name: "A", share: 0.16 }]);
    const history = makeHistory([oldest, middle, current]);

    const result = computeMetaMovers(current, history, 3);

    // Should compare current (16%) vs oldest (10%) = +6pp, not vs middle (14%) = +2pp
    expect(result[0].changeValue).toBe(6);
  });
});
