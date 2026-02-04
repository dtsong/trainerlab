import { describe, it, expect } from "vitest";

import { cn } from "../utils";

describe("cn", () => {
  it("should return empty string for no arguments", () => {
    expect(cn()).toBe("");
  });

  it("should return single class name", () => {
    expect(cn("text-red-500")).toBe("text-red-500");
  });

  it("should merge multiple class names", () => {
    expect(cn("text-red-500", "bg-blue-500")).toBe("text-red-500 bg-blue-500");
  });

  it("should handle conditional classes", () => {
    const isActive = true;
    const isDisabled = false;

    expect(cn("base", isActive && "active", isDisabled && "disabled")).toBe(
      "base active"
    );
  });

  it("should handle undefined and null inputs", () => {
    expect(cn("base", undefined, null, "end")).toBe("base end");
  });

  it("should handle empty string inputs", () => {
    expect(cn("base", "", "end")).toBe("base end");
  });

  it("should merge conflicting Tailwind classes (last wins)", () => {
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500");
  });

  it("should merge conflicting padding classes", () => {
    expect(cn("p-4", "p-2")).toBe("p-2");
  });

  it("should merge conflicting margin classes", () => {
    expect(cn("mt-4", "mt-2")).toBe("mt-2");
  });

  it("should not merge non-conflicting Tailwind classes", () => {
    expect(cn("text-red-500", "bg-blue-500", "p-4")).toBe(
      "text-red-500 bg-blue-500 p-4"
    );
  });

  it("should handle array inputs via clsx", () => {
    expect(cn(["text-red-500", "bg-blue-500"])).toBe(
      "text-red-500 bg-blue-500"
    );
  });

  it("should handle object inputs via clsx", () => {
    expect(cn({ "text-red-500": true, "bg-blue-500": false })).toBe(
      "text-red-500"
    );
  });

  it("should handle mixed inputs", () => {
    expect(
      cn("base", ["array-class"], { "object-class": true }, undefined)
    ).toBe("base array-class object-class");
  });

  it("should merge conflicting display classes", () => {
    expect(cn("block", "inline")).toBe("inline");
  });

  it("should merge responsive variants correctly", () => {
    expect(cn("md:p-4", "md:p-2")).toBe("md:p-2");
  });

  it("should handle boolean false values gracefully", () => {
    expect(cn("base", false, "end")).toBe("base end");
  });
});
