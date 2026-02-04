import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { JPAlertBanner } from "../JPAlertBanner";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

// Mock hooks
const mockUseHomeMetaData = vi.fn();

vi.mock("@/hooks/useMeta", () => ({
  useHomeMetaData: () => mockUseHomeMetaData(),
}));

// Mock home-utils
const mockComputeJPDivergence = vi.fn();

vi.mock("@/lib/home-utils", () => ({
  computeJPDivergence: (...args: unknown[]) => mockComputeJPDivergence(...args),
}));

describe("JPAlertBanner", () => {
  const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
      getItem: vi.fn((key: string) => store[key] ?? null),
      setItem: vi.fn((key: string, value: string) => {
        store[key] = value;
      }),
      removeItem: vi.fn((key: string) => {
        delete store[key];
      }),
      clear: vi.fn(() => {
        store = {};
      }),
    };
  })();

  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
    Object.defineProperty(window, "localStorage", {
      value: localStorageMock,
      writable: true,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should return null when there is no significant divergence", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: undefined,
      jpMeta: undefined,
    });

    mockComputeJPDivergence.mockReturnValue({
      hasSignificantDivergence: false,
      message: "",
    });

    const { container } = render(<JPAlertBanner />);

    expect(container.firstChild).toBeNull();
  });

  it("should render the alert banner when divergence is significant and not dismissed", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: { archetype_breakdown: [] },
      jpMeta: { archetype_breakdown: [] },
    });

    mockComputeJPDivergence.mockReturnValue({
      hasSignificantDivergence: true,
      message:
        "Japan's meta is diverging: Dragapult ex showing significant differences from the global meta.",
    });

    render(<JPAlertBanner />);

    expect(
      screen.getByText(
        /Japan's meta is diverging: Dragapult ex showing significant differences/
      )
    ).toBeInTheDocument();
  });

  it("should render a role='alert' element", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: { archetype_breakdown: [] },
      jpMeta: { archetype_breakdown: [] },
    });

    mockComputeJPDivergence.mockReturnValue({
      hasSignificantDivergence: true,
      message: "Japan's meta is diverging.",
    });

    render(<JPAlertBanner />);

    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("should render a 'View JP Meta' link to /meta/japan", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: { archetype_breakdown: [] },
      jpMeta: { archetype_breakdown: [] },
    });

    mockComputeJPDivergence.mockReturnValue({
      hasSignificantDivergence: true,
      message: "Japan's meta is diverging.",
    });

    render(<JPAlertBanner />);

    const link = screen.getByRole("link", { name: /View JP Meta/i });
    expect(link).toHaveAttribute("href", "/meta/japan");
  });

  it("should render a dismiss button with aria-label", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: { archetype_breakdown: [] },
      jpMeta: { archetype_breakdown: [] },
    });

    mockComputeJPDivergence.mockReturnValue({
      hasSignificantDivergence: true,
      message: "Japan's meta is diverging.",
    });

    render(<JPAlertBanner />);

    expect(
      screen.getByRole("button", { name: /Dismiss alert/i })
    ).toBeInTheDocument();
  });

  it("should dismiss the banner when the dismiss button is clicked", async () => {
    const user = userEvent.setup();

    mockUseHomeMetaData.mockReturnValue({
      globalMeta: { archetype_breakdown: [] },
      jpMeta: { archetype_breakdown: [] },
    });

    mockComputeJPDivergence.mockReturnValue({
      hasSignificantDivergence: true,
      message: "Japan's meta is diverging.",
    });

    const { container } = render(<JPAlertBanner />);

    // Banner should be visible
    expect(screen.getByRole("alert")).toBeInTheDocument();

    // Click dismiss
    await user.click(screen.getByRole("button", { name: /Dismiss alert/i }));

    // Banner should be gone
    expect(container.firstChild).toBeNull();
  });

  it("should save dismiss timestamp to localStorage on dismiss", async () => {
    const user = userEvent.setup();

    mockUseHomeMetaData.mockReturnValue({
      globalMeta: { archetype_breakdown: [] },
      jpMeta: { archetype_breakdown: [] },
    });

    mockComputeJPDivergence.mockReturnValue({
      hasSignificantDivergence: true,
      message: "Japan's meta is diverging.",
    });

    render(<JPAlertBanner />);

    await user.click(screen.getByRole("button", { name: /Dismiss alert/i }));

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "trainerlab_jp_alert_dismissed",
      expect.any(String)
    );
  });

  it("should not render when previously dismissed within 24 hours", () => {
    // Set dismissed timestamp to 1 hour ago
    const oneHourAgo = Date.now() - 60 * 60 * 1000;
    localStorageMock.getItem.mockReturnValue(String(oneHourAgo));

    mockUseHomeMetaData.mockReturnValue({
      globalMeta: { archetype_breakdown: [] },
      jpMeta: { archetype_breakdown: [] },
    });

    mockComputeJPDivergence.mockReturnValue({
      hasSignificantDivergence: true,
      message: "Japan's meta is diverging.",
    });

    const { container } = render(<JPAlertBanner />);

    expect(container.firstChild).toBeNull();
  });
});
