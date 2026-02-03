/**
 * Chart color palette using design tokens.
 *
 * These colors map to CSS variables defined in globals.css.
 * For recharts (which needs actual color values), we use
 * hsl() with CSS custom properties.
 */

// Archetype-based color palette for charts
// Uses CSS variables for consistency with design system
export const CHART_COLORS = [
  "hsl(var(--archetype-water))", // blue
  "hsl(var(--archetype-grass))", // green
  "hsl(var(--archetype-lightning))", // yellow
  "hsl(var(--archetype-fire))", // red/orange
  "hsl(var(--teal-500))", // teal (primary brand)
  "hsl(var(--archetype-psychic))", // purple
  "hsl(var(--archetype-fighting))", // orange
  "hsl(var(--archetype-darkness))", // indigo
  "hsl(var(--archetype-dragon))", // violet
  "hsl(var(--archetype-fairy))", // pink
] as const;

// Tier colors for charts
export const TIER_COLORS = {
  S: "hsl(var(--tier-s))",
  A: "hsl(var(--tier-a))",
  B: "hsl(var(--tier-b))",
  C: "hsl(var(--tier-c))",
  Rogue: "hsl(var(--tier-rogue))",
} as const;

// Signal colors for trend indicators
export const SIGNAL_COLORS = {
  up: "hsl(var(--signal-up))",
  down: "hsl(var(--signal-down))",
  stable: "hsl(var(--signal-stable))",
} as const;

// Neutral color for aggregated "Other" bucket in charts
export const OTHER_COLOR = "hsl(var(--muted-foreground) / 0.3)";

// Get color by index with wrapping
export function getChartColor(index: number): string {
  return CHART_COLORS[index % CHART_COLORS.length];
}

// Terminal theme colors for dark panels
export const TERMINAL_CHART_COLORS = {
  axis: "hsl(var(--terminal-muted))",
  grid: "hsl(var(--terminal-border))",
  text: "hsl(var(--terminal-text))",
  accent: "hsl(var(--terminal-accent))",
} as const;
