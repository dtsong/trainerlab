# Advocate Final Position -- JP Archetype Pipeline Phase 2

**Date:** 2026-02-06
**Agent:** Advocate (Green Lens)

---

## 1. Revised Recommendation

**Ship the smallest possible frontend PR in parallel with backend Phase 2 work. The user has seen zero visual improvements from Phase 1. Every day the backend gets better without the frontend reflecting it is a day we lose trust-building opportunity.**

The three frontend deliverables for Phase 2 are:

1. **Archetype sprite display** -- the single highest-impact visual change. Competitive players identify decks by their Pokemon silhouettes, not by parsing "Dragapult Charizard ex." Sprites transform walls of text into scannable visual information.
2. **Persistent BO1 context** -- the dismissible banner is a one-time education. Persistent inline labels prevent JP data misinterpretation on every subsequent visit.
3. **Information hierarchy reorder** -- lead with divergence (why JP data matters to you), follow with raw data (what the numbers are). This is the difference between a dashboard and a reference table.

All three ship as tasks #16-18 in the Round 2 synthesis plan. No new API endpoints. No prediction widgets. No homepage redesign. This is information design work using data Phase 1 already produces.

---

## 2. Concessions Made

### Dropped: Format Forecast Homepage Widget

**Why:** Requires a new API endpoint, homepage layout changes, and editorial content ("what this means for your deck choice"). The Strategist correctly identified that this is a Phase 3 / post-April 10 deliverable. The engineering cost is disproportionate to the beta user base who already knows to visit `/meta/japan`.

### Dropped: Prediction Confidence Badges

**Why:** Without 6+ months of historical prediction data, displaying "High / Medium / Low" confidence is theater, not information. The Strategist and Skeptic are right that descriptive intelligence (what IS different) should ship before prescriptive intelligence (what we THINK will happen). The `archetype_detection_method` provenance column exists in the backend but surfacing it as a user-facing confidence badge is premature.

### Dropped: Historical Accuracy Tracker

**Why:** No predictions exist to track yet. This is a chicken-and-egg problem. Ship the data, let users form their own predictions, then build tracking infrastructure when there is something to track.

### Modified: Full Mobile-First Redesign

**Original position:** Rethink the Japan page for mobile from scratch.
**Revised:** The existing responsive grid (`grid gap-6 md:grid-cols-2`, `sm:grid-cols-2 lg:grid-cols-3`) is adequate for beta. Mobile optimization is a polish pass, not a Phase 2 gate. The sprites will render at 32x32 on mobile viewports, which is sufficient for recognition.

---

## 3. Non-Negotiables

These are UX requirements that must be in Phase 2. They are not negotiable because each one prevents a specific user harm.

### 3.1 Archetype Sprites Must Ship Before Reprocess Completion

**User harm if absent:** After reprocess, archetype names will change. Old: "Rogue." New: "Cinderace ex." The user sees different names in the trend chart with no visual continuity. Sprites provide that continuity -- even if the text label changes, the Cinderace silhouette is recognizable.

**Specification:**

- New component: `ArchetypeSprites` at `/apps/web/src/components/meta/ArchetypeSprites.tsx`
- Props: `spriteUrls: string[]`, `archetypeName: string`, `size?: "sm" | "md"` (sm=24px for inline legends, md=32px for cards)
- Renders 1-3 sprite images inline, sourced from `raw_archetype_sprites` on placements (already stored as `JSONB` on `tournament_placements.raw_archetype_sprites`)
- Falls back to no image (not a broken image icon) if sprites are empty or fail to load. Use `onError` handler to hide the `<img>`.
- Alt text: `alt={archetypeName}` for screen readers
- Used in: `MetaPieChart` legend items, `MetaDivergenceComparison` archetype rows, `CityLeagueResultsFeed` archetype badges

**Backend requirement:** The meta API response (`ApiArchetype`) must include a `sprite_urls: string[]` field. This requires:

- Adding `sprite_urls?: string[] | null` to `ApiArchetype` in `packages/shared-types/src/meta.ts`
- Populating it from the `archetype_sprites` table or from the most recent placement's `raw_archetype_sprites` in the meta snapshot builder

**Accessibility:**

- Sprites are decorative when accompanied by text name (use `role="img"` with `aria-label`)
- Must not be the sole identifier of an archetype -- text name is always present alongside
- Images must have explicit `width` and `height` attributes to prevent layout shift

### 3.2 BO1 Context Must Persist Across Sessions

**User harm if absent:** Sarah dismisses the BO1 banner on her first visit. She returns two weeks later and sees "Lugia VSTAR -- 14.2% meta share." She compares this mentally to the EN meta where Lugia is 8%. She thinks: "Lugia is way bigger in Japan, I should prepare for it." But the 14.2% is inflated by BO1 (Lugia's speed advantage in untimed single games). Without BO1 context, she over-indexes on a format artifact.

**Specification:**

- The dismissible banner (`BO1ContextBanner`) stays as-is for the detailed explanation
- Add persistent "(BO1)" labels to ALL section headers on the Japan page. The current implementation already does this for "Archetype Breakdown (BO1)" and "Meta Trends (BO1)" at lines 195 and 211 of `page.tsx`. Extend to:
  - "City League Results (BO1)" -- currently just "City League Results"
  - "JP vs International Meta" comparison headers -- currently "Japan (BO1)" on the JP column but the section header has no BO1 annotation
  - "Card Intelligence" section -- add "(BO1 data)" to subtitle
- Store dismissal state in `localStorage` so the banner respects the user's choice across page refreshes, rather than resetting on every navigation (current behavior: `useState(false)` resets on every mount)

**Implementation detail for BO1 banner persistence:**

```typescript
// In BO1ContextBanner.tsx
const STORAGE_KEY = "trainerlab-bo1-banner-dismissed";
const [dismissed, setDismissed] = useState(() => {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(STORAGE_KEY) === "true";
});
const handleDismiss = () => {
  setDismissed(true);
  localStorage.setItem(STORAGE_KEY, "true");
};
```

### 3.3 Divergence Comparison Must Be Above Raw Data

**User harm if absent:** The current page layout puts the pie chart (Section 1) above the divergence comparison (Section 4). A user who visits `/meta/japan` to understand how Japan's meta differs from their region must scroll past: pie chart, trend chart, card adoption rates, upcoming cards, and city league results before reaching the divergence view. This buries the "why should I care" behind the "here's a bunch of numbers."

**Specification -- Reorder sections in `apps/web/src/app/meta/japan/page.tsx`:**

Current order:

1. JP Meta Overview (pie chart + trend chart)
2. Card Intelligence (adoption rates + upcoming cards)
3. City League Results
4. JP vs EN Divergence
5. Card Count Evolution
6. Card Innovation Tracker
7. New Archetype Watch

Proposed order:

1. **JP vs EN Divergence** (moved from 4 to 1 -- "what's different and why you should care")
2. JP Meta Overview (pie chart + trend chart -- "here's the raw data")
3. Card Intelligence (adoption rates + upcoming cards)
4. City League Results
5. Card Count Evolution
6. Card Innovation Tracker
7. New Archetype Watch

**Rationale:** The divergence comparison answers the user's primary question: "How is Japan different from my meta?" The pie chart answers a secondary question: "What does the JP meta look like in absolute terms?" Lead with the answer to the primary question.

This is a single section reorder in `page.tsx` -- moving the `<MetaDivergenceComparison />` section block (currently lines 243-246) above the JP Meta Overview section (currently lines 147-227). Estimated: 15 minutes of work, zero risk.

---

## 4. Implementation Notes

### Component: `ArchetypeSprites`

**File:** `/apps/web/src/components/meta/ArchetypeSprites.tsx`

```typescript
interface ArchetypeSpritesProps {
  spriteUrls: string[];
  archetypeName: string;
  size?: "sm" | "md";
  className?: string;
}
```

- `sm` size: 24x24px, for use in legend rows, table cells, inline badges
- `md` size: 32x32px, for use in cards, headers, prominent displays
- Max 3 sprites rendered (matches the 1-3 sprite pairs from Limitless)
- Each sprite is an `<img>` with `loading="lazy"`, explicit `width`/`height`, and `onError` hide
- Wrap in a `<span>` or `<div>` with `className="inline-flex items-center gap-1"` for inline layout
- Export from `/apps/web/src/components/meta/index.ts`

### Integration Points

**MetaPieChart legend** (`/apps/web/src/components/meta/MetaPieChart.tsx`, line 142-175):

- Add `ArchetypeSprites` before the text name in each legend button
- Requires `spriteUrls` to be available on the slice data, which means the `Archetype` type needs `spriteUrls?: string[]` and the `SliceData` type needs to carry it through

**MetaDivergenceComparison rows** (`/apps/web/src/components/japan/MetaDivergenceComparison.tsx`, line 24):

- Add `ArchetypeSprites` at the start of `ArchetypeRow`, before the archetype name span
- The `ApiArchetype` type needs `sprite_urls` added (backend + shared-types change)

**CityLeagueResultsFeed badges** (`/apps/web/src/components/japan/CityLeagueResultsFeed.tsx`, line 110-116):

- Replace or augment the archetype badge in `TournamentItem` header with sprites
- This requires the `ApiTopPlacement` type to include `sprite_urls`

### Shared Types Changes

**`packages/shared-types/src/meta.ts`:**

```typescript
// Add to ApiArchetype
export interface ApiArchetype {
  name: string;
  share: number;
  sample_decks?: string[] | null;
  key_cards?: string[] | null;
  sprite_urls?: string[] | null; // NEW -- from archetype_sprites table
}

// Add to frontend Archetype
export interface Archetype {
  name: string;
  share: number;
  sampleDecks?: string[];
  keyCards?: string[];
  spriteUrls?: string[]; // NEW
}
```

### Backend Change Required

The meta snapshot endpoint must include `sprite_urls` when returning archetype breakdowns. Two options:

**Option A (preferred -- minimal):** Join through the `archetype_sprites` table during meta snapshot computation. For each archetype name in the breakdown, look up its `sprite_urls` from the `archetype_sprites` table where `archetype_name` matches.

**Option B (fallback):** Aggregate `raw_archetype_sprites` from the most recent placements for each archetype. This is noisier but works without the `archetype_sprites` table being fully populated.

### Page Reorder

In `/apps/web/src/app/meta/japan/page.tsx`, move the divergence section (lines 243-246):

```tsx
{
  /* Section 4: JP vs EN Divergence */
}
<section>
  <MetaDivergenceComparison />
</section>;
```

To immediately after the BO1 Context Banner (after line 144), renumbering sections accordingly.

### What This Does NOT Include

- No new API endpoints (sprites come through existing meta snapshot endpoint)
- No homepage changes (Japan page only)
- No prediction widgets or confidence systems
- No mobile-specific layouts beyond existing responsive grid
- No animation or transition effects
- No new data fetching hooks (reuses existing `useCurrentMeta`)

---

## 5. Success Criteria

After these three changes ship, the Japan meta page should pass this user story test:

> Sarah opens `/meta/japan`. She immediately sees "JP vs International Meta" with Pokemon sprite icons next to each archetype name. She can visually scan which archetypes are different between JP and EN in under 5 seconds. Every section is labeled "(BO1)" so she knows the format context. She scrolls down to see the pie chart and trend data for deeper analysis. She does not need to dismiss a banner, perform mental math, or scroll past four sections to find what she came for.

**Measurable:**

- Time to first useful insight: under 10 seconds (divergence view is above the fold)
- Zero instances of archetype names without sprites (for archetypes in the sprite map)
- BO1 context visible on every section of the page without user interaction
- `ArchetypeSprites` component has 100% test coverage (render, fallback, accessibility)
- No layout shift from lazy-loaded sprite images (explicit width/height)
