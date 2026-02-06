# Advocate Position — Japanese Meta Intelligence for International Players

## Core recommendation

Surface Japanese meta insights through a graduated discovery journey: from actionable "what's coming" predictions on the homepage, to deep archetype-level analysis for users actively preparing for format rotations, with clear visual signaling of confidence levels and BO1 context throughout.

## Key argument: Product thinking around competitive player needs

When a competitive player opens TrainerLab 60 days before an April format rotation, they're not thinking "I want to explore Japanese City League data." They're thinking: **"What deck should I be testing for Louisville?"**

The product's job is to bridge that gap. Japanese data is valuable not because it's exotic, but because it's **predictive**. The current `/meta/japan` page treats JP meta as a separate curiosity, when it should be the answer to "what's coming next?"

The user journey should mirror the mental model of competitive preparation:

1. **Discovery (Homepage):** User sees a "Format Forecast" widget showing archetypes trending in Japan that will be legal internationally soon. This is the hook — immediate value without needing to understand the mechanics of BO1 or City Leagues.

2. **Exploration (Meta Dashboard):** User clicks into an archetype and sees a timeline: "This deck is 18% of Japan meta (last 30 days), estimated 12-15% internationally when legal (April 10)." The divergence is explained visually, not buried in text.

3. **Preparation (From Japan):** User who wants the full picture visits `/meta/japan` and gets: archetype evolution over time, card count changes (the "Charizard lists are cutting Pidgeot" insight), and explicit BO1 disclaimers on control decks.

4. **Execution (Deck Builder):** User builds a deck and gets a "JP Signal" indicator if key cards are trending in Japan, with a tooltip: "This card is in 45% of Charizard lists in Japan vs 12% internationally — consider testing."

The current implementation has good bones (7 distinct components, rich data types, thoughtful BO1 context banner) but the **information hierarchy is inverted**. It surfaces raw data before answering the user's question: "Should I care, and why?"

## User journey: How does a competitive player discover and use JP meta insights?

### Entry Point 1: Homepage (Passive Discovery)

- User lands on TrainerLab homepage
- Sees "Format Forecast" section with 3-4 cards showing archetypes legal in Japan, coming internationally
- Each card shows: archetype name, sprite visual, JP meta share, estimated EN date, confidence badge
- One-click to archetype detail or "From Japan" page

### Entry Point 2: Meta Dashboard (Contextual Discovery)

- User browses meta dashboard, sees familiar archetypes
- Notices a "JP Signal" badge on certain archetypes with >5% divergence
- Tooltip explains: "This archetype is performing differently in Japan (BO1). Click to compare."
- One-click to side-by-side JP vs EN view

### Entry Point 3: Search/Direct (Intentional Discovery)

- User searches "Charizard Japan" or navigates to `/meta/japan`
- Lands on full JP intelligence page with all components
- This is the "power user" flow for deep research

### Core Flow: From Awareness to Action

1. **See the signal** (Homepage widget or meta dashboard badge)
2. **Understand the context** (BO1 banner, confidence indicators, divergence explanation)
3. **Explore the data** (Archetype trends, card adoption, deck evolution)
4. **Apply the insight** (Build/test deck with JP-informed choices)

### Critical UX Principle: Progressive Disclosure

Don't make users wade through City League results to get to "Dragapult Charizard is going to be good." Lead with the insight, layer in the evidence.

## Information hierarchy: What data matters most to show first?

### Priority 1: Predictive Signals (Above the fold)

**What users need immediately:**

- Archetypes legal in Japan, coming to EN soon (with dates)
- Top 3-5 archetypes by JP meta share (with visual comparison to EN)
- "Format Forecast" summary: "When set X drops, expect archetype Y to gain share"

**Why this first:**
Because this answers "Should I care?" Users won't scroll if they don't see value.

### Priority 2: Context & Confidence (Persistent)

**What users need to trust the data:**

- BO1 vs BO3 indicator (always visible, not just a banner you dismiss)
- Confidence levels on predictions ("High: This archetype already exists" vs "Medium: New archetype, early results")
- Sample size indicators ("Based on 1,200 decks" vs "Based on 45 decks — early signal")

**Why this matters:**
Misplaced confidence in Japanese data can hurt users. A control deck that's 3% in Japan isn't necessarily bad — the format penalizes it. Users must know this.

### Priority 3: Archetype-Level Insights (On-demand)

**What users need when they commit to research:**

- Trend lines (is this archetype rising, stable, falling in Japan?)
- Card count evolution (are lists getting greedier, more consistent, more tech-heavy?)
- Divergence comparison (how does this deck's JP performance differ from EN?)

**Current implementation has this (MetaTrendChart, CardCountEvolution, MetaDivergence) — good.**

### Priority 4: Granular Data (Deep dive)

**What users need when they're locked in:**

- City League results feed (who played what, when, where)
- Card innovation tracker (new cards seeing play)
- New archetype watch (JP-exclusive strategies)

**Current implementation has this — also good.**

### What's Missing: The Bridge

The current `/meta/japan` page jumps straight to Priority 3-4. There's no Priority 1 entry point. It's like opening a restaurant with no menu — you have to walk into the kitchen and ask the chef what's cooking.

## Archetype display: How should sprite-derived archetypes appear in the UI?

### The Archetype Naming Convention (Limitless sprite filenames)

The plan is to auto-derive archetype names from Limitless sprite filenames like "dragapult-charizard.png" → "Dragapult Charizard". This is smart because:

- It leverages community convention (players already recognize these)
- It's parseable and consistent
- It ties to visual identity (the sprite itself)

### UI Representation: Lead with Visuals

**Archetype Card Component (Homepage/Dashboard):**

```
┌─────────────────────────────────┐
│ [Sprite: 2-3 Pokemon heads]     │  ← Visual identity, recognizable
│                                  │
│ Dragapult Charizard              │  ← Archetype name from sprite
│ JP: 18.2% | EN: (April 10)      │  ← Meta share + availability
│                                  │
│ [Badge: High Confidence]         │  ← Prediction confidence
│ [Badge: JP Signal +6%]           │  ← Divergence indicator
└─────────────────────────────────┘
```

**Key UX decisions:**

1. **Sprite first**: Competitive players recognize archetypes visually before reading names. "That's the Dragapult deck" is faster than parsing text.
2. **Archetype name from sprites**: Use the derived name (e.g., "Dragapult Charizard") not generic labels ("Dragon deck"). Specificity builds trust.
3. **Dual context**: Always show both JP share and EN expectation. Don't make users guess which meta they're looking at.
4. **Badge system**: Use color-coded badges for confidence (green = high, yellow = medium, gray = low) and divergence (red = overperforming in JP, blue = underperforming).

### Accessibility Considerations

- Sprites must have alt text with full archetype name
- Color-coded badges must also use icons (not color alone)
- Screen reader should announce: "Dragapult Charizard archetype, Japan meta share 18.2%, estimated English legal date April 10, high confidence prediction"

### Responsive Design

**Mobile (320-768px):**

- Stack sprite above text
- Reduce sprite size (48x48 → 32x32)
- Abbreviate labels (JP → J, EN → E)
- Expand on tap for full detail

**Tablet (768-1024px):**

- 2-column grid for archetype cards
- Full labels, medium sprites (64x64)

**Desktop (1024px+):**

- 3-4 column grid
- Large sprites (96x96), full detail visible

## Prediction UX: How should predictive insights be surfaced without misleading users?

### The Core Tension

Predictive features are the platform's differentiation, but **bad predictions erode trust faster than good predictions build it**. The UX must communicate uncertainty honestly while still being useful.

### Confidence Levels (3-tier system)

**High Confidence (Green):**

- Archetype already exists in EN meta, Japan just has new cards
- Large sample size (1000+ decks)
- Historical precedent (previous sets showed similar transfer rate)
- **UI:** Solid green badge, "High confidence" label
- **Copy:** "This archetype is expected to gain share when set X releases."

**Medium Confidence (Yellow):**

- New archetype enabled by JP-only cards, but uses familiar engine
- Moderate sample size (100-500 decks)
- BO1 vs BO3 implications unclear
- **UI:** Outlined yellow badge, "Emerging" label
- **Copy:** "Early results suggest this archetype may be competitive. BO1 vs BO3 impact unknown."

**Low Confidence (Gray):**

- New archetype with <100 decks
- Heavily reliant on cards that may not transfer well (control in BO1)
- No historical precedent
- **UI:** Dashed gray badge, "Early signal" label
- **Copy:** "Very early data. This archetype may or may not transfer to international play."

### Prediction Display Components

**1. Forecast Widget (Homepage)**

```
┌─────────────────────────────────────────────────┐
│ Format Forecast: April 10 Rotation              │
│                                                  │
│ [Archetype Card] [Archetype Card] [Archetype Card]
│                                                  │
│ Based on 30 days of Japan City League data      │
│ [View full analysis →]                          │
└─────────────────────────────────────────────────┘
```

**2. Prediction Detail Modal**
When user clicks an archetype with predictions:

```
┌─────────────────────────────────────────────────┐
│ Dragapult Charizard — Format Forecast           │
│                                                  │
│ Current Status:                                  │
│ • Japan (BO1): 18.2% meta share                 │
│ • International (BO3): Not yet legal            │
│                                                  │
│ Prediction:                                      │
│ • Estimated EN share: 12-15%                    │
│ • Confidence: High                              │
│ • Legal date: April 10, 2026                    │
│                                                  │
│ Why this prediction:                            │
│ • Large sample size (1,200+ decks)              │
│ • Similar archetype performed well in EN before │
│ • Cards favor BO3 play (not penalized by ties)  │
│                                                  │
│ Key cards enabling this deck:                   │
│ • [Card name] (JP release: Jan 1, EN: April 10) │
│ • [Card name] (Already legal internationally)   │
│                                                  │
│ [View deck lists →] [Build this deck →]        │
└─────────────────────────────────────────────────┘
```

**3. Historical Accuracy Tracker**
Once predictions resolve (after EN set releases), show accuracy:

```
┌─────────────────────────────────────────────────┐
│ Prediction Accuracy                             │
│                                                  │
│ Last 3 format rotations:                        │
│ • High confidence: 85% accurate (±3% share)     │
│ • Medium confidence: 60% accurate (±5% share)   │
│ • Low confidence: 40% accurate (±8% share)      │
│                                                  │
│ [See all past predictions →]                    │
└─────────────────────────────────────────────────┘
```

This transparency is crucial. Users will trust "we're right 85% of the time on high-confidence calls" more than implied perfection.

### What NOT to Do (Anti-patterns)

1. **Don't hide uncertainty**: Don't say "this deck will be 15%" when you mean "12-18%, probably."
2. **Don't over-predict**: Don't forecast every archetype. Focus on high/medium confidence only.
3. **Don't bury disclaimers**: The BO1 context isn't fine print — it's core to the prediction.
4. **Don't forget to resolve predictions**: If you predict a deck will be 15% and it's 8%, admit it and explain why. This builds long-term trust.

## Risks if ignored

### Risk 1: Users misinterpret Japanese data and make bad deck choices

If a competitive player sees "Snorlax Stall is 8% of Japan meta" and doesn't understand BO1 tie rules, they might invest in a deck that's systematically disadvantaged in international BO3. They lose matches, blame the platform, churn.

**Mitigation:** BO1 context must be persistent (not dismissible), and control/stall archetypes must have explicit warnings ("This archetype is penalized by Japan's BO1 tie rules and may perform better internationally").

### Risk 2: Poor mobile experience fragments the user base

Competitive players are increasingly mobile-first (browsing at League, on lunch break, commuting). If the Japan page is desktop-only, you lose 40-60% of potential users. The meta divergence comparison, card innovation table, and trend charts must reflow gracefully on 375px screens.

**Mitigation:** Mobile-first design with collapsible tables, horizontal scrollable cards, and simplified views. Desktop is additive, not primary.

### Risk 3: Information overload buries the value proposition

The current `/meta/japan` page has 7 sections, 16 components, rich data — but no clear entry point. A user who doesn't already know why they're there will bounce. The platform becomes "for data nerds only" instead of "for competitive players who want an edge."

**Mitigation:** Progressive disclosure. Lead with the "why should I care" (Format Forecast widget on homepage), layer in the evidence (archetype pages), reserve the full data buffet for users who opt into it.

## Dependencies on other agents' domains

### Architect (Data Pipeline)

- **Need:** Accurate archetype labeling from Limitless sprite filenames. If the archetype derivation is wrong ("Dragapult Charizard" mislabeled as "Dragon deck"), the entire UX collapses. Users won't trust generic labels.
- **Need:** Prediction confidence scoring logic. The UX displays confidence levels (high/medium/low), but the backend must calculate them based on sample size, historical accuracy, BO1 bias factors, etc.
- **Need:** API endpoints for Format Forecast widget (homepage) that return "top N archetypes coming to EN soon, sorted by predicted impact."

### Craftsman (Frontend Implementation)

- **Need:** Sprite display component that handles multi-Pokemon archetypes gracefully (e.g., stacking 2-3 Pokemon heads, not stretching a single image).
- **Need:** Responsive chart components. The current MetaTrendChart and CardCountEvolutionChart must reflow for mobile without losing readability.
- **Need:** Prediction modal with expandable "Why this prediction?" section. This is complex UI state (closed by default, expands on click, includes nested card lists).

### Skeptic (Testing & Edge Cases)

- **Need:** Validation that BO1 disclaimers actually prevent user confusion. Run usability tests where users interpret Japanese data — do they understand the tie rule implications?
- **Need:** Edge case testing for archetypes with no English translation yet. How does the UI handle "JP-only archetype with no direct EN equivalent"?
- **Need:** Accessibility audit. Are screen readers announcing sprite-based archetype names correctly? Are confidence badges distinguishable without color?

### Strategist (Product Roadmap)

- **Need:** Decision on when to launch Format Forecast widget. If the archetype labeling isn't accurate yet, launching predictions early will hurt trust. Sequence matters.
- **Need:** Decision on prediction resolution frequency. How often do we update "estimated EN share" as more Japan data comes in? Daily? Weekly? This impacts user expectations.
- **Need:** Prioritization of homepage redesign vs `/meta/japan` improvements. The current Japan page is functional but not discoverable. Should we polish it first, or build the homepage hook first?
