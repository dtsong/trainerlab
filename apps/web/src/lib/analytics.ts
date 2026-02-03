/**
 * Analytics tracking utilities.
 */

type EventCategory =
  | "commerce"
  | "navigation"
  | "deck_builder"
  | "meta"
  | "search";

interface AnalyticsEvent {
  category: EventCategory;
  action: string;
  label?: string;
  value?: number;
}

/**
 * Track a custom analytics event.
 */
export function trackEvent({
  category,
  action,
  label,
  value,
}: AnalyticsEvent): void {
  // In production, this would send to Google Analytics or similar
  if (typeof window !== "undefined" && "gtag" in window) {
    (window as { gtag: (...args: unknown[]) => void }).gtag("event", action, {
      event_category: category,
      event_label: label,
      value: value,
    });
  }

  // Development logging
  if (process.env.NODE_ENV === "development") {
    console.log("[Analytics]", { category, action, label, value });
  }
}

/**
 * Track affiliate link click.
 */
export function trackAffiliateClick(
  affiliate: "doubleHolo" | "tcgPlayer",
  context: "deck" | "card" | "archetype",
  itemId?: string
): void {
  trackEvent({
    category: "commerce",
    action: `affiliate_click_${affiliate}`,
    label: `${context}${itemId ? `:${itemId}` : ""}`,
  });
}

/**
 * Track deck build CTA interaction.
 */
export function trackBuildDeckCTA(
  action: "view" | "click_primary" | "click_secondary",
  deckName: string
): void {
  trackEvent({
    category: "commerce",
    action: `build_deck_cta_${action}`,
    label: deckName,
  });
}
