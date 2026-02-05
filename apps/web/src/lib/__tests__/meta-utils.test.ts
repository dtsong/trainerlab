import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  isValidRegion,
  parseRegion,
  parseDays,
  transformSnapshot,
  safeFormatDate,
  getErrorMessage,
  groupArchetypes,
} from "../meta-utils";
import { ApiError } from "../api";
import type { ApiMetaSnapshot, Archetype } from "@trainerlab/shared-types";

describe("meta-utils", () => {
  // Suppress console.warn for expected warnings during tests
  const originalWarn = console.warn;
  beforeEach(() => {
    console.warn = vi.fn();
  });
  afterEach(() => {
    console.warn = originalWarn;
  });

  describe("isValidRegion", () => {
    it("should return true for valid regions", () => {
      expect(isValidRegion("global")).toBe(true);
      expect(isValidRegion("NA")).toBe(true);
      expect(isValidRegion("EU")).toBe(true);
      expect(isValidRegion("JP")).toBe(true);
      expect(isValidRegion("LATAM")).toBe(true);
      expect(isValidRegion("OCE")).toBe(true);
    });

    it("should return false for invalid regions", () => {
      expect(isValidRegion("invalid")).toBe(false);
      expect(isValidRegion("")).toBe(false);
      expect(isValidRegion("na")).toBe(false); // case-sensitive
      expect(isValidRegion("GLOBAL")).toBe(false);
    });

    it("should return false for null", () => {
      expect(isValidRegion(null)).toBe(false);
    });
  });

  describe("parseRegion", () => {
    it("should return the value if valid", () => {
      expect(parseRegion("NA")).toBe("NA");
      expect(parseRegion("JP")).toBe("JP");
      expect(parseRegion("global")).toBe("global");
    });

    it("should return default for null/undefined", () => {
      expect(parseRegion(null)).toBe("global");
      expect(parseRegion(undefined)).toBe("global");
    });

    it("should return custom default for null/undefined", () => {
      expect(parseRegion(null, "NA")).toBe("NA");
      expect(parseRegion(undefined, "EU")).toBe("EU");
    });

    it("should return default for invalid strings and log warning", () => {
      expect(parseRegion("invalid")).toBe("global");
      expect(console.warn).toHaveBeenCalledWith(
        '[parseRegion] Invalid region "invalid", using default "global"'
      );
    });

    it("should not log warning for null/undefined", () => {
      parseRegion(null);
      parseRegion(undefined);
      expect(console.warn).not.toHaveBeenCalled();
    });
  });

  describe("parseDays", () => {
    it("should return the value if valid", () => {
      expect(parseDays("7")).toBe(7);
      expect(parseDays("30")).toBe(30);
      expect(parseDays("90")).toBe(90);
      expect(parseDays("365")).toBe(365);
    });

    it("should return default for null/undefined", () => {
      expect(parseDays(null)).toBe(30);
      expect(parseDays(undefined)).toBe(30);
    });

    it("should return custom default for null/undefined", () => {
      expect(parseDays(null, 7)).toBe(7);
      expect(parseDays(undefined, 90)).toBe(90);
    });

    it("should return default for empty string", () => {
      expect(parseDays("")).toBe(30);
    });

    it("should return default and log warning for invalid values", () => {
      expect(parseDays("abc")).toBe(30);
      expect(console.warn).toHaveBeenCalledWith(
        '[parseDays] Invalid days value "abc", using default 30'
      );
    });

    it("should return default and log warning for out of range values", () => {
      expect(parseDays("0")).toBe(30);
      expect(parseDays("-5")).toBe(30);
      expect(parseDays("366")).toBe(30);
      expect(parseDays("1000")).toBe(30);
    });

    it("should accept boundary values", () => {
      expect(parseDays("1")).toBe(1);
      expect(parseDays("365")).toBe(365);
    });
  });

  describe("transformSnapshot", () => {
    const mockApiSnapshot: ApiMetaSnapshot = {
      snapshot_date: "2025-01-15",
      region: "NA",
      format: "standard",
      best_of: 3,
      archetype_breakdown: [
        { name: "Charizard ex", share: 0.15, key_cards: ["sv4-54", "sv3-6"] },
        { name: "Gardevoir ex", share: 0.12, key_cards: null },
      ],
      card_usage: [
        { card_id: "sv4-54", inclusion_rate: 0.85, avg_copies: 3.2 },
        { card_id: "sv3-6", inclusion_rate: 0.72, avg_copies: 2.8 },
      ],
      sample_size: 500,
    };

    it("should transform snake_case to camelCase", () => {
      const result = transformSnapshot(mockApiSnapshot);

      expect(result.snapshotDate).toBe("2025-01-15");
      expect(result.bestOf).toBe(3);
      expect(result.sampleSize).toBe(500);
    });

    it("should validate and preserve valid regions", () => {
      const result = transformSnapshot(mockApiSnapshot);
      expect(result.region).toBe("NA");
    });

    it("should return null for invalid regions", () => {
      const invalidSnapshot = { ...mockApiSnapshot, region: "INVALID" };
      const result = transformSnapshot(invalidSnapshot);
      expect(result.region).toBeNull();
    });

    it("should preserve null region", () => {
      const nullRegionSnapshot = { ...mockApiSnapshot, region: null };
      const result = transformSnapshot(nullRegionSnapshot);
      expect(result.region).toBeNull();
    });

    it("should transform archetype breakdown", () => {
      const result = transformSnapshot(mockApiSnapshot);

      expect(result.archetypeBreakdown).toHaveLength(2);
      expect(result.archetypeBreakdown[0]).toEqual({
        name: "Charizard ex",
        share: 0.15,
        keyCards: ["sv4-54", "sv3-6"],
      });
    });

    it("should convert null key_cards to undefined", () => {
      const result = transformSnapshot(mockApiSnapshot);
      expect(result.archetypeBreakdown[1].keyCards).toBeUndefined();
    });

    it("should transform card usage", () => {
      const result = transformSnapshot(mockApiSnapshot);

      expect(result.cardUsage).toHaveLength(2);
      expect(result.cardUsage[0]).toEqual({
        cardId: "sv4-54",
        inclusionRate: 0.85,
        avgCopies: 3.2,
      });
    });
  });

  describe("safeFormatDate", () => {
    const mockFormat = vi.fn((date: Date, format: string) => {
      return `formatted-${format}`;
    });
    const mockParseISO = vi.fn((dateString: string) => new Date(dateString));

    beforeEach(() => {
      mockFormat.mockClear();
      mockParseISO.mockClear();
    });

    it("should format valid date strings", () => {
      const result = safeFormatDate(
        "2025-01-15",
        "MMM d, yyyy",
        mockFormat,
        mockParseISO
      );

      expect(result).toBe("formatted-MMM d, yyyy");
      expect(mockParseISO).toHaveBeenCalledWith("2025-01-15");
    });

    it("should return raw value for invalid dates and log warning", () => {
      const invalidParseISO = () => new Date("invalid");
      const result = safeFormatDate(
        "not-a-date",
        "MMM d",
        mockFormat,
        invalidParseISO
      );

      expect(result).toBe("not-a-date");
      expect(console.warn).toHaveBeenCalledWith(
        "[safeFormatDate] Invalid date value:",
        "not-a-date"
      );
    });

    it("should return raw value when format throws and log warning", () => {
      const throwingFormat = () => {
        throw new Error("Format error");
      };

      const result = safeFormatDate(
        "2025-01-15",
        "MMM d",
        throwingFormat,
        mockParseISO
      );

      expect(result).toBe("2025-01-15");
      expect(console.warn).toHaveBeenCalled();
    });

    it("should return raw value when parseISO throws and log warning", () => {
      const throwingParseISO = () => {
        throw new Error("Parse error");
      };

      const result = safeFormatDate(
        "2025-01-15",
        "MMM d",
        mockFormat,
        throwingParseISO
      );

      expect(result).toBe("2025-01-15");
      expect(console.warn).toHaveBeenCalled();
    });
  });

  describe("getErrorMessage", () => {
    it("should handle network errors (status 0)", () => {
      const error = new ApiError("Network error", 0);
      expect(getErrorMessage(error)).toBe(
        "Unable to connect to the server. Please check your internet connection."
      );
    });

    it("should handle server errors (5xx)", () => {
      const error500 = new ApiError("Internal Server Error", 500);
      expect(getErrorMessage(error500)).toBe(
        "Server error. Please try again later."
      );

      const error503 = new ApiError("Service Unavailable", 503);
      expect(getErrorMessage(error503)).toBe(
        "Server error. Please try again later."
      );
    });

    it("should handle 404 errors with default message", () => {
      const error = new ApiError("Not Found", 404);
      expect(getErrorMessage(error)).toBe(
        "Meta data not found for the selected filters."
      );
    });

    it("should handle 404 errors with custom context", () => {
      const error = new ApiError("Not Found", 404);
      expect(getErrorMessage(error, "Japan meta")).toBe(
        "Japan meta data not found for the selected filters."
      );
    });

    it("should handle other client errors", () => {
      const error400 = new ApiError("Bad Request", 400);
      expect(getErrorMessage(error400)).toBe(
        "Error loading data (400). Please try again."
      );

      const error403 = new ApiError("Forbidden", 403);
      expect(getErrorMessage(error403)).toBe(
        "Error loading data (403). Please try again."
      );
    });

    it("should handle non-ApiError errors", () => {
      const error = new Error("Some error");
      expect(getErrorMessage(error)).toBe(
        "An unexpected error occurred. Please try again."
      );
    });

    it("should handle non-Error values", () => {
      expect(getErrorMessage("string error")).toBe(
        "An unexpected error occurred. Please try again."
      );
      expect(getErrorMessage(null)).toBe(
        "An unexpected error occurred. Please try again."
      );
      expect(getErrorMessage(undefined)).toBe(
        "An unexpected error occurred. Please try again."
      );
    });
  });

  describe("groupArchetypes", () => {
    function makeArchetype(name: string, share: number): Archetype {
      return { name, share };
    }

    it("should return empty displayed array and null other for empty input", () => {
      const result = groupArchetypes([]);
      expect(result.displayed).toEqual([]);
      expect(result.other).toBeNull();
    });

    it("should return all archetypes as displayed with null other when count <= topN", () => {
      const archetypes = [
        makeArchetype("Charizard ex", 0.15),
        makeArchetype("Gardevoir ex", 0.12),
        makeArchetype("Lugia VSTAR", 0.1),
      ];

      const result = groupArchetypes(archetypes);

      expect(result.displayed).toEqual(archetypes);
      expect(result.other).toBeNull();
    });

    it("should group archetypes exceeding topN into other bucket", () => {
      const archetypes = [
        makeArchetype("Deck A", 0.2),
        makeArchetype("Deck B", 0.15),
        makeArchetype("Deck C", 0.1),
        makeArchetype("Deck D", 0.08),
        makeArchetype("Deck E", 0.05),
      ];

      const result = groupArchetypes(archetypes, { topN: 3 });

      expect(result.displayed).toHaveLength(3);
      expect(result.displayed.map((a) => a.name)).toEqual([
        "Deck A",
        "Deck B",
        "Deck C",
      ]);

      expect(result.other).not.toBeNull();
      expect(result.other!.count).toBe(2);
      expect(result.other!.share).toBeCloseTo(0.13);
      expect(result.other!.archetypes.map((a) => a.name)).toEqual([
        "Deck D",
        "Deck E",
      ]);
    });

    it("should sort archetypes by share descending before grouping", () => {
      // Provide archetypes in non-sorted order
      const archetypes = [
        makeArchetype("Low", 0.02),
        makeArchetype("High", 0.3),
        makeArchetype("Mid", 0.1),
        makeArchetype("Other1", 0.01),
      ];

      const result = groupArchetypes(archetypes, { topN: 2 });

      expect(result.displayed[0].name).toBe("High");
      expect(result.displayed[1].name).toBe("Mid");
      expect(result.other!.archetypes[0].name).toBe("Low");
      expect(result.other!.archetypes[1].name).toBe("Other1");
    });

    it("should put all archetypes into other when topN is 0", () => {
      const archetypes = [
        makeArchetype("Deck A", 0.5),
        makeArchetype("Deck B", 0.3),
        makeArchetype("Deck C", 0.2),
      ];

      const result = groupArchetypes(archetypes, { topN: 0 });

      expect(result.displayed).toHaveLength(0);
      expect(result.other).not.toBeNull();
      expect(result.other!.count).toBe(3);
      expect(result.other!.share).toBeCloseTo(1.0);
    });

    it("should return all as displayed with null other when count equals topN", () => {
      const archetypes = [
        makeArchetype("Deck A", 0.4),
        makeArchetype("Deck B", 0.35),
        makeArchetype("Deck C", 0.25),
      ];

      const result = groupArchetypes(archetypes, { topN: 3 });

      expect(result.displayed).toEqual(archetypes);
      expect(result.other).toBeNull();
    });

    it("should use default topN of 8", () => {
      const archetypes = Array.from({ length: 10 }, (_, i) =>
        makeArchetype(`Deck ${i + 1}`, (10 - i) / 100)
      );

      const result = groupArchetypes(archetypes);

      expect(result.displayed).toHaveLength(8);
      expect(result.other).not.toBeNull();
      expect(result.other!.count).toBe(2);
      expect(result.other!.share).toBeCloseTo(0.01 + 0.02);
    });
  });
});
