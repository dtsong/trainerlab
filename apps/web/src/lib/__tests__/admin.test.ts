import { describe, it, expect } from "vitest";

import { isAdminEmail, ADMIN_EMAILS } from "../admin";

describe("ADMIN_EMAILS", () => {
  it("should be a non-empty readonly array", () => {
    expect(ADMIN_EMAILS.length).toBeGreaterThan(0);
    expect(Array.isArray(ADMIN_EMAILS)).toBe(true);
  });

  it("should contain known admin email", () => {
    expect(ADMIN_EMAILS).toContain("daniel@appraisehq.ai");
  });
});

describe("isAdminEmail", () => {
  it("should return true for admin email", () => {
    expect(isAdminEmail("daniel@appraisehq.ai")).toBe(true);
  });

  it("should return false for non-admin email", () => {
    expect(isAdminEmail("user@example.com")).toBe(false);
  });

  it("should return false for null", () => {
    expect(isAdminEmail(null)).toBe(false);
  });

  it("should return false for undefined", () => {
    expect(isAdminEmail(undefined)).toBe(false);
  });

  it("should return false for empty string", () => {
    expect(isAdminEmail("")).toBe(false);
  });

  it("should be case-sensitive", () => {
    expect(isAdminEmail("Daniel@appraisehq.ai")).toBe(false);
    expect(isAdminEmail("DANIEL@APPRAISEHQ.AI")).toBe(false);
  });

  it("should return false for partial match", () => {
    expect(isAdminEmail("daniel@appraisehq")).toBe(false);
    expect(isAdminEmail("daniel")).toBe(false);
  });

  it("should return false for email with extra whitespace", () => {
    expect(isAdminEmail(" daniel@appraisehq.ai")).toBe(false);
    expect(isAdminEmail("daniel@appraisehq.ai ")).toBe(false);
  });

  it("should return false for similar but different emails", () => {
    expect(isAdminEmail("daniel@appraisehq.com")).toBe(false);
    expect(isAdminEmail("dan@appraisehq.ai")).toBe(false);
  });
});
