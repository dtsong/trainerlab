# Advocate Round 2 -- Challenge & Synthesis

## 1. User Impact of Phase 1: What Changed and What Users See

Phase 1 (PR #312) fixed the backend. The `ArchetypeNormalizer` with its sprite_lookup priority chain means newly scraped JP tournaments now produce correct archetype labels instead of "Rogue" or misidentified decks. The `sprite_urls: list[str]` field on `LimitlessPlacement` means the backend now carries visual identity data.

**What the user sees today: nothing different.** The frontend has not changed. The `/meta/japan` page still renders `archetype.name` as plain text in the `MetaPieChart`, `MetaTrendChart`, and `MetaDivergenceComparison`. The `ArchetypeCard` component (at `/apps/web/src/components/meta/ArchetypeCard.tsx`) uses `cardImages` for key card art, but has no concept of sprite URLs. The BO1 context banner is dismissible and does not resurface.

This is the gap: the backend now produces better data, but the user experience is identical. Archetype names are more accurate, which improves trust passively, but we have not leveraged the new `sprite_urls` or `archetype_provenance` columns in any user-facing way.

**What users SHOULD see after Phase 1 lands in production:**

1. Archetype sprites next to archetype names everywhere they appear -- pie chart legend, trend chart legend, divergence comparison rows, archetype cards grid. This is the single highest-value visual change because competitive players identify decks by their Pokemon, not by reading "Dragapult Charizard ex."

2. The archetype names themselves should be noticeably more accurate. If the historical reprocess (Phase 2) has not happened yet, there will be a visible discontinuity -- old data shows "Rogue" for Cinderace decks, new data shows "Cinderace ex." This is confusing without a brief note explaining "Data quality improved on [date]."

3. The `MetaDivergenceComparison` component already does the right thing structurally (side-by-side JP BO1 vs International BO3), but the matching logic uses `archetype.name` string equality. If Phase 1 produces slightly different canonical names than the EN pipeline, some legitimate divergences will show as "JP Only" / "EN Only" when they are actually the same archetype with a naming mismatch. This is a latent UX bug.

## 2. Challenges to Other Agents

### Strategist: "Defer predictions to post-launch"

**Their position:** Predictions are "marketing fluff" without 6+ months of validation. Ship clean data and comparison views. Defer predictive modeling entirely.

**My response: Modify.** The Strategist is right that ML-based meta share forecasting (predict "15% share in May") is premature. But they are conflating two different things:

- **Predictive modeling** (statistical forecasting) -- yes, defer this.
- **Divergence signals** (showing that JP and EN metas differ, with context about why) -- this is not prediction, it is observation. It already exists in `MetaDivergenceComparison`. It just needs to be surfaced better.

The Strategist's Phase 3 actually includes "side-by-side JP vs EN meta comparison" and "JP meta 60 days ago vs EN meta today." That is exactly what I am advocating for as the Format Forecast widget, just without the word "forecast." Call it "What's Different in Japan" or "JP Divergence Watch." The user value is identical: a competitive player preparing for April 10 sees which archetypes are performing differently in Japan and can decide for themselves whether to test those decks.

The Strategist says "ship on April 5" for Phase 3. I agree with the date but disagree with the characterization that this is "nice to have." A competitive player who visits TrainerLab in late March and sees only raw pie charts with no "here's what this means for you" interpretation will bounce. They will go to Twitter threads and YouTube videos that do exactly this interpretation work manually. The comparison view is not a prediction -- it is the core value proposition of having JP data at all.

**What I am NOT asking for:** Confidence intervals, accuracy tracking, ML models, or any numeric prediction of future EN meta shares. What I AM asking for: surface the JP vs EN divergence prominently (not buried as Section 4 of 7 on the Japan page), add the BO1 context inline per-archetype (not as a dismissible banner), and show sprite visuals so users can quickly scan.

### Craftsman: Backend testing focus over user-facing improvements

**Their position:** Golden datasets, data quality gates, shadow mode rollout, regression baselines. All essential.

**My response: Maintain their priorities, ADD a frontend work item.** The Craftsman's testing strategy is exactly right for the backend. But their entire position focuses on pipeline correctness with zero mention of what the user sees. They mention "Advocate (User Impact)" as a dependency for "what user-facing metrics change after reprocess" -- but that is the extent of it.

The risk is that we spend Weeks 1-4 making the data perfect and then spend Weeks 5-6 in a rush to build frontend surfaces. The smallest frontend PR (see Section 5 below) can ship in parallel with backend validation work. It does not require the historical reprocess. It works with whatever data is currently in production.

### Architect: Three-layer pipeline design

**Their position:** Raw ingestion, normalization, analysis layers with versioned archetype mappings.

**My response: Strong support.** The `raw_archetype` field is critical for auditability, and the `archetype_detection_method` column directly enables a UX feature I want: showing provenance badges when confidence is lower. If the user sees an archetype labeled via "signature_card" fallback rather than "sprite" primary, we could show a subtle indicator that this label is less certain. This aligns with the confidence-level system from my Round 1 position.

One UX concern: the Architect proposes alphabetical ordering for sprite keys ("charizard-dragapult" not "dragapult-charizard"). The community convention on Limitless uses the order displayed on the page, which typically puts the primary attacker first. Alphabetical ordering is better for deduplication but worse for user recognition. I recommend storing alphabetically for lookups but displaying in Limitless's original order for the user.

### Skeptic: Root cause analysis before re-scrape

**Their position:** Trace the Cinderace failure end-to-end before any bulk operations.

**My response: Fully agree, AND note that Phase 1 already addressed this.** The PR #312 fixed `_parse_jp_placement_row()` and replaced the broken `img.pokemon` CSS selector. The Skeptic's concern about "where exactly does Limitless store sprite-pair combos" has been answered by the implementation: `_extract_archetype_and_sprites_from_images()` now extracts from the actual HTML structure. The canary testing the Skeptic wants (10 recent JP tournaments, >95% accuracy) should happen before Phase 2 reprocess. That is compatible with shipping a small frontend PR now.

## 3. Why Simple Divergence Signals Matter for April 10

The Strategist frames April 10 as a "marketing moment." From the user's perspective, it is a decision deadline. Here is the user story:

Sarah is a competitive player. She has a Regional Championship on April 19. The format rotation happens April 10, meaning new cards from the latest set become legal. She knows Japan has been playing with these cards for months. She opens TrainerLab on March 20 to start preparing.

**Scenario A (current state):** Sarah navigates to `/meta/japan`. She sees a pie chart of JP archetypes (BO1), a trend chart, and eventually scrolls to Section 4 to find "JP vs International Meta." She sees two columns of text-only archetype names with percentages. Some say "JP Only" in a red badge. She has to mentally process: "OK, Dragapult Charizard is 18% in Japan and not on the international list... that means it uses the new cards... so it will probably show up after April 10." She does this work herself. She might get it right. She might also misinterpret a BO1-inflated aggro deck as a future BO3 staple.

**Scenario B (what I am proposing):** Sarah lands on `/meta/japan`. The first thing she sees, above the pie chart, is a "JP Divergence Watch" card that shows 3-4 archetypes with sprites, their JP meta share, and a one-line note: "Uses cards legal internationally April 10" or "BO1-favored -- may underperform in BO3." Sarah immediately knows which decks to test and which to be cautious about. She clicks into one and sees the full comparison view.

Scenario B does not require any prediction engine. It requires:

- Sprite display (Phase 1 backend already provides `sprite_urls`)
- A reorganized information hierarchy (put divergence above raw data)
- Inline BO1 context per archetype (not a global banner)

The engineering cost is a single React component and a reordering of the Japan page sections. This is not "predictive modeling." It is information design.

## 4. Key UX Priorities for Phase 2

### Priority 1: Sprite Display in Meta Dashboard

**User value:** Instant visual archetype recognition. Players know "that deck" by its Pokemon, not by parsing text.

**Implementation:** Create an `ArchetypeSprites` component that renders 1-3 sprite images from the `sprite_urls` array. Use it in: `ArchetypeCard`, `MetaDivergenceComparison` rows, `CityLeagueResultsFeed` entries. The sprites are small (32x32 on mobile, 48x48 on desktop), loaded from Limitless CDN (`r2.limitlesstcg.net`). Add alt text with the archetype name for accessibility.

**Accessibility:** Sprites must have `alt={archetypeName}`. Color-coded badges (JP Signal, JP Only) must also have icons or text labels, not just color. The existing implementation already uses text labels, which is good.

### Priority 2: BO1 Context Inline, Not Dismissible

**User value:** Users cannot misinterpret JP data if the BO1 context is always visible where data is displayed.

**Current problem:** The `BO1ContextBanner` at `/apps/web/src/components/meta/BO1ContextBanner.tsx` is dismissible (`useState(false)` on click). Once dismissed, there is zero BO1 context anywhere on the page. A user could dismiss it on their first visit, return a week later, and see JP meta shares with no format context.

**Proposal:** Keep the dismissible banner for the detailed explanation, but add a persistent "(BO1)" tag on every chart title and section header on the Japan page. The existing code already does this partially -- "Archetype Breakdown (BO1)" and "Meta Trends (BO1)" in the Japan page. Extend this to the divergence comparison and archetype cards. Additionally, for control/stall archetypes specifically (identifiable by archetype name patterns), add a brief inline note: "BO1-favored: tie = double loss penalizes slow decks."

### Priority 3: JP vs EN Comparison View (Minimum Viable)

**User value:** See divergence at a glance without mental math.

**Current state:** `MetaDivergenceComparison` already shows side-by-side columns. This is functional but passive -- the user has to scan both columns and spot differences themselves.

**Minimum improvement:** Add a small inline bar visualization next to each archetype name showing the share delta. For example: "Dragapult Charizard -- JP: 18.2% | EN: 12.1% | [green bar indicating +6.1pp]". This makes divergence scannable without reading numbers. The existing `isDivergent` check (>5% difference) and "JP Signal" badge are a good start. Extend this with a tiny horizontal bar that makes magnitude visible.

### Priority 4 (Post-April 10): Format Forecast Entry Point on Homepage

**User value:** Passive discovery of JP intelligence for users who do not know to visit `/meta/japan`.

This is the one item I am willing to defer past April 10, per the Strategist's phasing. It requires a homepage redesign and a new API endpoint. It is not needed for users who already know about the Japan page. But it IS needed for user acquisition -- new visitors to TrainerLab should see "we have something competitors don't" immediately.

## 5. The Smallest Frontend PR That Delivers User Value

**PR scope: "Add archetype sprite display to Japan meta page"**

This is a single PR that can ship in parallel with backend Phase 2 work:

1. **New component: `ArchetypeSprites`** (~40 lines). Takes `spriteUrls: string[]` and renders 1-3 small sprite images inline. Falls back to nothing if no sprites. Includes alt text.

2. **Update `MetaDivergenceComparison`** to render sprites next to archetype names in both JP and EN columns. This requires the meta API to return `sprite_urls` in the archetype breakdown response (backend change: add `sprite_urls` to the `ApiArchetype` serializer).

3. **Reorder Japan page sections:** Move `MetaDivergenceComparison` from Section 4 to Section 1 (above the pie chart). The divergence is the "why should I care" -- the pie chart is the "here's the raw data." Lead with insight, follow with evidence.

4. **Make BO1 banner non-dismissible** OR add persistent "(BO1)" labels to all section headers (the latter is simpler and less intrusive).

**Estimated effort:** 1-2 days frontend work, plus a small backend change to include `sprite_urls` in the meta API response.

**What this does NOT include:** Homepage changes, prediction widgets, confidence badges, mobile-specific layouts, or any new API endpoints. Those are all follow-ups.

**Why this is the right first PR:** It uses data that Phase 1 already produces. It improves the experience for users who already visit `/meta/japan`. It requires no new backend infrastructure. And it sets up the component library (`ArchetypeSprites`) that every subsequent feature will use.
