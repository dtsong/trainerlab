import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  trackEvent,
  trackAffiliateClick,
  trackBuildDeckCTA,
} from "../analytics";

describe("trackEvent", () => {
  const originalNodeEnv = process.env.NODE_ENV;
  let mockGtag: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockGtag = vi.fn();
    vi.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    // Clean up gtag from window
    if ("gtag" in window) {
      delete (window as Record<string, unknown>).gtag;
    }
    vi.restoreAllMocks();
    process.env.NODE_ENV = originalNodeEnv;
  });

  it("should call window.gtag when available", () => {
    (window as Record<string, unknown>).gtag = mockGtag;

    trackEvent({
      category: "commerce",
      action: "test_action",
      label: "test_label",
      value: 42,
    });

    expect(mockGtag).toHaveBeenCalledWith("event", "test_action", {
      event_category: "commerce",
      event_label: "test_label",
      value: 42,
    });
  });

  it("should not throw when window.gtag is not available", () => {
    expect(() =>
      trackEvent({
        category: "navigation",
        action: "page_view",
      })
    ).not.toThrow();
  });

  it("should log to console in development mode", () => {
    process.env.NODE_ENV = "development";

    trackEvent({
      category: "search",
      action: "search_query",
      label: "Charizard",
    });

    expect(console.log).toHaveBeenCalledWith("[Analytics]", {
      category: "search",
      action: "search_query",
      label: "Charizard",
      value: undefined,
    });
  });

  it("should handle event without optional label and value", () => {
    (window as Record<string, unknown>).gtag = mockGtag;

    trackEvent({
      category: "meta",
      action: "view_dashboard",
    });

    expect(mockGtag).toHaveBeenCalledWith("event", "view_dashboard", {
      event_category: "meta",
      event_label: undefined,
      value: undefined,
    });
  });

  it("should call gtag and log in development mode", () => {
    process.env.NODE_ENV = "development";
    (window as Record<string, unknown>).gtag = mockGtag;

    trackEvent({
      category: "deck_builder",
      action: "save_deck",
      label: "my-deck",
      value: 60,
    });

    expect(mockGtag).toHaveBeenCalled();
    expect(console.log).toHaveBeenCalled();
  });
});

describe("trackAffiliateClick", () => {
  let mockGtag: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockGtag = vi.fn();
    (window as Record<string, unknown>).gtag = mockGtag;
    vi.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    delete (window as Record<string, unknown>).gtag;
    vi.restoreAllMocks();
  });

  it("should track doubleHolo affiliate click with item ID", () => {
    trackAffiliateClick("doubleHolo", "card", "sv3-125");

    expect(mockGtag).toHaveBeenCalledWith(
      "event",
      "affiliate_click_doubleHolo",
      {
        event_category: "commerce",
        event_label: "card:sv3-125",
        value: undefined,
      }
    );
  });

  it("should track tcgPlayer affiliate click without item ID", () => {
    trackAffiliateClick("tcgPlayer", "deck");

    expect(mockGtag).toHaveBeenCalledWith(
      "event",
      "affiliate_click_tcgPlayer",
      {
        event_category: "commerce",
        event_label: "deck",
        value: undefined,
      }
    );
  });

  it("should track affiliate click with archetype context", () => {
    trackAffiliateClick("doubleHolo", "archetype", "dragapult-ex");

    expect(mockGtag).toHaveBeenCalledWith(
      "event",
      "affiliate_click_doubleHolo",
      {
        event_category: "commerce",
        event_label: "archetype:dragapult-ex",
        value: undefined,
      }
    );
  });
});

describe("trackBuildDeckCTA", () => {
  let mockGtag: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockGtag = vi.fn();
    (window as Record<string, unknown>).gtag = mockGtag;
    vi.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    delete (window as Record<string, unknown>).gtag;
    vi.restoreAllMocks();
  });

  it("should track CTA view", () => {
    trackBuildDeckCTA("view", "Dragapult ex");

    expect(mockGtag).toHaveBeenCalledWith("event", "build_deck_cta_view", {
      event_category: "commerce",
      event_label: "Dragapult ex",
      value: undefined,
    });
  });

  it("should track CTA primary click", () => {
    trackBuildDeckCTA("click_primary", "Charizard ex");

    expect(mockGtag).toHaveBeenCalledWith(
      "event",
      "build_deck_cta_click_primary",
      {
        event_category: "commerce",
        event_label: "Charizard ex",
        value: undefined,
      }
    );
  });

  it("should track CTA secondary click", () => {
    trackBuildDeckCTA("click_secondary", "Lugia VSTAR");

    expect(mockGtag).toHaveBeenCalledWith(
      "event",
      "build_deck_cta_click_secondary",
      {
        event_category: "commerce",
        event_label: "Lugia VSTAR",
        value: undefined,
      }
    );
  });
});
