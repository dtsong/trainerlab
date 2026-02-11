import { describe, expect, it } from "vitest";

import { humanizeSlug, parseOgPath, stripPngSuffix } from "../utils";

describe("og utils", () => {
  it("parses widget og path", () => {
    expect(parseOgPath(["w_12345.png"])).toEqual({
      type: "widget",
      id: "12345",
    });
  });

  it("parses meta og path", () => {
    expect(parseOgPath(["meta.png"])).toEqual({ type: "meta" });
  });

  it("parses lab notes og path", () => {
    expect(parseOgPath(["lab-notes", "weekly-meta-report.png"])).toEqual({
      type: "lab-note",
      slug: "weekly-meta-report",
    });
  });

  it("parses evolution og path", () => {
    expect(parseOgPath(["evolution", "charizard-journey.png"])).toEqual({
      type: "evolution",
      slug: "charizard-journey",
    });
  });

  it("parses archetype og path", () => {
    expect(parseOgPath(["archetypes", "dragapult-ex.png"])).toEqual({
      type: "archetype",
      id: "dragapult-ex",
    });
  });

  it("returns null for unsupported path", () => {
    expect(parseOgPath(["unknown.png"])).toBeNull();
  });

  it("strips png suffix case-insensitively", () => {
    expect(stripPngSuffix("sample.PNG")).toBe("sample");
  });

  it("humanizes slugs", () => {
    expect(humanizeSlug("post-rotation_meta")).toBe("Post Rotation Meta");
  });
});
