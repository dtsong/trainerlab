import { describe, expect, it } from "vitest";

import {
  buildPathWithQuery,
  mergeSearchParams,
  parseEnumParam,
  parseIntParam,
  parseStringParam,
} from "../url-state";

describe("url-state helpers", () => {
  describe("parseEnumParam", () => {
    it("returns default for missing value", () => {
      expect(parseEnumParam(null, ["all", "standard"], "all")).toBe("all");
    });

    it("returns parsed value when valid", () => {
      expect(parseEnumParam("standard", ["all", "standard"], "all")).toBe(
        "standard"
      );
    });

    it("returns default for invalid values", () => {
      expect(parseEnumParam("bad", ["all", "standard"], "all")).toBe("all");
    });
  });

  describe("parseIntParam", () => {
    it("parses valid ints in range", () => {
      expect(parseIntParam("3", { defaultValue: 1, min: 1, max: 10 })).toBe(3);
    });

    it("returns default for invalid numbers", () => {
      expect(parseIntParam("foo", { defaultValue: 1, min: 1 })).toBe(1);
    });

    it("returns default when outside range", () => {
      expect(parseIntParam("0", { defaultValue: 1, min: 1 })).toBe(1);
      expect(parseIntParam("99", { defaultValue: 1, max: 10 })).toBe(1);
    });
  });

  describe("parseStringParam", () => {
    it("trims by default", () => {
      expect(parseStringParam("  pikachu  ")).toBe("pikachu");
    });

    it("returns default for null", () => {
      expect(parseStringParam(null, { defaultValue: "" })).toBe("");
    });
  });

  describe("mergeSearchParams", () => {
    it("sets and removes params with defaults", () => {
      const current = new URLSearchParams("q=pikachu&page=2");
      const query = mergeSearchParams(
        current,
        {
          q: "charizard",
          page: 1,
          format: "all",
          category: "japan",
        },
        { page: 1, format: "all" }
      );
      expect(query).toBe("q=charizard&category=japan");
    });

    it("removes params when value is nullish or empty", () => {
      const current = new URLSearchParams("q=pikachu&set_id=sv1");
      const query = mergeSearchParams(current, { q: "", set_id: null });
      expect(query).toBe("");
    });
  });

  describe("buildPathWithQuery", () => {
    it("builds path with query", () => {
      expect(buildPathWithQuery("/cards", "q=pika")).toBe("/cards?q=pika");
    });

    it("returns path when query empty", () => {
      expect(buildPathWithQuery("/cards", "")).toBe("/cards");
    });
  });
});
