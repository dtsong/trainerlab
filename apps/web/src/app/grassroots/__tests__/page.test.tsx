import { describe, it, expect, vi } from "vitest";

vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
}));

import { redirect } from "next/navigation";

describe("GrassrootsPage", () => {
  it("should redirect to tournaments with grassroots category", async () => {
    const { default: GrassrootsPage } = await import("../page");

    try {
      GrassrootsPage();
    } catch {
      // redirect throws in Next.js
    }

    expect(redirect).toHaveBeenCalledWith("/tournaments?category=grassroots");
  });
});
