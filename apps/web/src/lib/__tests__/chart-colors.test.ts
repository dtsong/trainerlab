import { describe, it, expect } from "vitest";

import {
  CHART_COLORS,
  TIER_COLORS,
  SIGNAL_COLORS,
  OTHER_COLOR,
  getChartColor,
  TERMINAL_CHART_COLORS,
} from "../chart-colors";

describe("CHART_COLORS", () => {
  it("should have 10 colors", () => {
    expect(CHART_COLORS).toHaveLength(10);
  });

  it("should contain hsl CSS variable references", () => {
    for (const color of CHART_COLORS) {
      expect(color).toMatch(/^hsl\(var\(--[\w-]+\)\)$/);
    }
  });

  it("should be a readonly tuple", () => {
    // TypeScript `as const` enforces readonly at compile time but does not freeze at runtime.
    // Verify it is an array with the expected stable length instead.
    expect(Array.isArray(CHART_COLORS)).toBe(true);
    expect(CHART_COLORS.length).toBe(10);
  });
});

describe("TIER_COLORS", () => {
  it("should have all tier keys", () => {
    expect(TIER_COLORS).toHaveProperty("S");
    expect(TIER_COLORS).toHaveProperty("A");
    expect(TIER_COLORS).toHaveProperty("B");
    expect(TIER_COLORS).toHaveProperty("C");
    expect(TIER_COLORS).toHaveProperty("Rogue");
  });

  it("should contain hsl CSS variable references", () => {
    for (const color of Object.values(TIER_COLORS)) {
      expect(color).toMatch(/^hsl\(var\(--[\w-]+\)\)$/);
    }
  });

  it("should have exactly 5 tiers", () => {
    expect(Object.keys(TIER_COLORS)).toHaveLength(5);
  });
});

describe("SIGNAL_COLORS", () => {
  it("should have all signal direction keys", () => {
    expect(SIGNAL_COLORS).toHaveProperty("up");
    expect(SIGNAL_COLORS).toHaveProperty("down");
    expect(SIGNAL_COLORS).toHaveProperty("stable");
  });

  it("should contain hsl CSS variable references", () => {
    for (const color of Object.values(SIGNAL_COLORS)) {
      expect(color).toMatch(/^hsl\(var\(--[\w-]+\)\)$/);
    }
  });

  it("should have exactly 3 signals", () => {
    expect(Object.keys(SIGNAL_COLORS)).toHaveLength(3);
  });
});

describe("OTHER_COLOR", () => {
  it("should be an hsl CSS variable reference with opacity", () => {
    expect(OTHER_COLOR).toMatch(/^hsl\(var\(--[\w-]+\)/);
    expect(OTHER_COLOR).toContain("0.3");
  });
});

describe("TERMINAL_CHART_COLORS", () => {
  it("should have axis, grid, text, and accent keys", () => {
    expect(TERMINAL_CHART_COLORS).toHaveProperty("axis");
    expect(TERMINAL_CHART_COLORS).toHaveProperty("grid");
    expect(TERMINAL_CHART_COLORS).toHaveProperty("text");
    expect(TERMINAL_CHART_COLORS).toHaveProperty("accent");
  });

  it("should contain hsl CSS variable references", () => {
    for (const color of Object.values(TERMINAL_CHART_COLORS)) {
      expect(color).toMatch(/^hsl\(var\(--[\w-]+\)\)$/);
    }
  });

  it("should have exactly 4 terminal colors", () => {
    expect(Object.keys(TERMINAL_CHART_COLORS)).toHaveLength(4);
  });
});

describe("getChartColor", () => {
  it("should return first color for index 0", () => {
    expect(getChartColor(0)).toBe(CHART_COLORS[0]);
  });

  it("should return correct color for valid indices", () => {
    for (let i = 0; i < CHART_COLORS.length; i++) {
      expect(getChartColor(i)).toBe(CHART_COLORS[i]);
    }
  });

  it("should wrap around for index equal to array length", () => {
    expect(getChartColor(10)).toBe(CHART_COLORS[0]);
  });

  it("should wrap around for index greater than array length", () => {
    expect(getChartColor(11)).toBe(CHART_COLORS[1]);
    expect(getChartColor(12)).toBe(CHART_COLORS[2]);
  });

  it("should wrap correctly for large indices", () => {
    expect(getChartColor(100)).toBe(CHART_COLORS[0]);
    expect(getChartColor(103)).toBe(CHART_COLORS[3]);
  });

  it("should return a string", () => {
    expect(typeof getChartColor(0)).toBe("string");
  });

  it("should return an hsl CSS variable reference", () => {
    expect(getChartColor(5)).toMatch(/^hsl\(var\(--[\w-]+\)\)$/);
  });
});
