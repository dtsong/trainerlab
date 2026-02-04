import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { safeFormatDate } from "../date-utils";

describe("safeFormatDate", () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("should format valid ISO date string", () => {
    const result = safeFormatDate("2024-06-15", "MMMM d, yyyy");
    expect(result).toBe("June 15, 2024");
  });

  it("should format valid ISO datetime string", () => {
    const result = safeFormatDate("2024-06-15T12:30:00Z", "MMM d, yyyy HH:mm");
    // Timezone-agnostic: just verify it parses and formats correctly
    expect(result).toMatch(/Jun 15, 2024 \d{2}:\d{2}/);
  });

  it("should return fallback for null input", () => {
    const result = safeFormatDate(null, "MMMM d, yyyy");
    expect(result).toBe("—");
  });

  it("should return fallback for undefined input", () => {
    const result = safeFormatDate(undefined, "MMMM d, yyyy");
    expect(result).toBe("—");
  });

  it("should return fallback for empty string input", () => {
    const result = safeFormatDate("", "MMMM d, yyyy");
    expect(result).toBe("—");
  });

  it("should return custom fallback when provided", () => {
    const result = safeFormatDate(null, "MMMM d, yyyy", "N/A");
    expect(result).toBe("N/A");
  });

  it("should return fallback for invalid date string", () => {
    const result = safeFormatDate("not-a-date", "MMMM d, yyyy");
    expect(result).toBe("—");
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      "Invalid date format:",
      "not-a-date"
    );
  });

  it("should return fallback for malformed date string", () => {
    const result = safeFormatDate("2024-13-45", "MMMM d, yyyy");
    expect(result).toBe("—");
    expect(consoleErrorSpy).toHaveBeenCalled();
  });

  it("should handle different format strings", () => {
    const dateStr = "2024-06-15";

    expect(safeFormatDate(dateStr, "yyyy-MM-dd")).toBe("2024-06-15");
    expect(safeFormatDate(dateStr, "MM/dd/yyyy")).toBe("06/15/2024");
    expect(safeFormatDate(dateStr, "d MMM yyyy")).toBe("15 Jun 2024");
    expect(safeFormatDate(dateStr, "EEE, MMM d")).toBe("Sat, Jun 15");
  });

  it("should handle dates with time zones", () => {
    const result = safeFormatDate(
      "2024-06-15T18:30:00-05:00",
      "yyyy-MM-dd HH:mm"
    );
    expect(result).toMatch(/2024-06-15/);
  });

  it("should handle dates at boundaries", () => {
    expect(safeFormatDate("2024-01-01", "MMMM d, yyyy")).toBe("January 1, 2024");
    expect(safeFormatDate("2024-12-31", "MMMM d, yyyy")).toBe(
      "December 31, 2024"
    );
  });

  it("should handle leap year date", () => {
    const result = safeFormatDate("2024-02-29", "MMMM d, yyyy");
    expect(result).toBe("February 29, 2024");
  });

  it("should return fallback for non-leap year Feb 29", () => {
    const result = safeFormatDate("2023-02-29", "MMMM d, yyyy");
    expect(result).toBe("—");
    expect(consoleErrorSpy).toHaveBeenCalled();
  });

  it("should handle very old dates", () => {
    const result = safeFormatDate("1990-01-15", "MMMM d, yyyy");
    expect(result).toBe("January 15, 1990");
  });

  it("should handle future dates", () => {
    const result = safeFormatDate("2050-12-25", "MMMM d, yyyy");
    expect(result).toBe("December 25, 2050");
  });
});
