import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { ScrollToTop } from "../ScrollToTop";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/"),
}));

const mockUsePathname = vi.mocked(
  (await import("next/navigation")).usePathname
);

describe("ScrollToTop", () => {
  const mockScrollTo = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePathname.mockReturnValue("/");
    window.scrollTo = mockScrollTo;
  });

  it("should scroll to top on mount", () => {
    render(<ScrollToTop />);

    expect(mockScrollTo).toHaveBeenCalledWith({
      top: 0,
      behavior: "instant",
    });
  });

  it("should scroll to top when pathname changes", () => {
    const { rerender } = render(<ScrollToTop />);

    mockScrollTo.mockClear();
    mockUsePathname.mockReturnValue("/meta");
    rerender(<ScrollToTop />);

    expect(mockScrollTo).toHaveBeenCalledWith({
      top: 0,
      behavior: "instant",
    });
  });

  it("should render nothing", () => {
    const { container } = render(<ScrollToTop />);
    expect(container.firstChild).toBeNull();
  });
});
