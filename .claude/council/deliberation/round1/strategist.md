## Strategist Position — JP Archetype Data Pipeline Overhaul

**Core recommendation:** Phase this as a 3-sprint, 6-week initiative with a hard cutoff at April 10 for prediction infrastructure. Ship data trust fixes FIRST (archetype correctness + card mappings), THEN meta analysis layers, and DEFER predictive modeling to post-launch unless critical path.

**Key argument:**

The current system is fundamentally broken at the data ingestion layer — Cinderace being misidentified as "Rogue" means every downstream insight (meta shares, trends, JP signals) is corrupted. This is a **trust crisis**, not just a feature gap. The business value hierarchy is clear:

1. **Accurate archetype labels** — Without this, the entire platform is suspect. Users who see obviously wrong data will not trust predictions.
2. **JP→EN card mappings** — Enables deck-level analysis (tech cards, counts), which is the second-order value prop after meta shares.
3. **April 10 format rotation prep** — This is the marketing moment, not a feature. Users need reliable JP meta snapshots to prepare, but they don't need ML-predicted meta shares to extract value. A well-presented comparison view ("JP meta on Jan 15 looked like X, EN meta adopted it by March 20") is sufficient.
4. **Predictive modeling** — This is premium tier content (Research Pass), not MVP. Defer unless we prove the data pipeline is stable.

The proposed scope is too large to ship atomically. We need to draw clear phase boundaries with value gates at each checkpoint.

---

## Phase Recommendations

### Phase 1: Data Trust Restoration (Sprint 1, Week 1-2)

**Deliverable:** Accurate archetype labels from Limitless sprite pairs + fixed card mappings

**What's in:**

- Rewrite Limitless scraper to extract sprite-pair archetypes from HTML
- Implement auto-naming convention ("Dragapult Charizard" from sprite filenames)
- Fallback to signature card detection ONLY when Limitless has "Other"/substitute sprite
- Fix JP→EN card ID mapping pipeline (validate against known test cases)
- Database migration: add `archetype_sprites` column to `tournament_placement` table

**What's out:**

- Historical data reprocess (defer until validation proves new scraper works)
- Predictive models
- New frontend surfaces (use existing meta dashboard)

**Value gate:** Spot-check 20 recent JP tournaments. If archetype labels match community consensus (Reddit, X) at >95% accuracy, proceed. If not, iterate on scraper logic before touching historical data.

**Success metric:** Zero "Cinderace → Rogue" failures in sample data.

---

### Phase 2: Historical Reprocess + Meta Analysis (Sprint 2, Week 3-4)

**Deliverable:** Trustworthy JP meta snapshots + deck-level insights

**What's in:**

- Wipe JP tournament data (tournaments + placements + meta_snapshots where region='JP')
- Re-scrape last 90 days of JP tournaments with new pipeline
- Re-run meta computation pipeline (meta shares, JP signals, tier assignments)
- Add deck-level analysis queries:
  - Top tech cards by archetype (card inclusion rates)
  - Average card counts per archetype (e.g., "Dragapult decks run 2.3 Rare Candy on average")
  - Meta share trend charts (existing infrastructure, just needs clean data)

**What's out:**

- Predictive modeling infrastructure
- Retrospective format evolution tracking (beyond simple trend charts)
- Future-only JP cards pipeline (social media sourcing)

**Value gate:** Compare re-processed JP meta to LimitlessTCG's own meta stats page. If our meta shares diverge by >3% for top 5 archetypes, investigate. If alignment is strong, ship.

**Success metric:** JP meta dashboard shows correct archetype names, accurate meta shares, and functional JP Signal badges.

---

### Phase 3: April 10 Prep + Prediction Lite (Sprint 3, Week 5-6)

**Deliverable:** Format rotation context + basic JP→EN prediction surface

**What's in:**

- Frontend: "From Japan" page enhancements
  - Side-by-side JP vs EN meta comparison (current format)
  - "JP meta 60 days ago" vs "EN meta today" comparison (manual lag analysis, no ML)
  - April 10 rotation card survival list (already exists, just needs better presentation)
- Backend: Simple trend endpoint
  - "This archetype went from 8% JP share to 15% EN share over 60 days" (statistical summary, not forecasting)
- Content: Lab Note explaining the pipeline changes + data reprocess
- Analytics: Track engagement with JP comparison views (measure value before investing in predictions)

**What's out:**

- ML-based meta share forecasting ("Dragapult will be 12% of meta in May")
- Confidence intervals, prediction accuracy tracking
- Retrospective format evolution narrative generation

**Value gate:** Ship on April 5 (5 days before rotation). If engagement with JP comparison views is high (>30% of meta dashboard users visit "From Japan" page), invest in predictive modeling post-launch. If low, deprioritize.

**Success metric:** Zero user complaints about archetype mislabeling in the 5 days before April 10.

---

## MVP Definition

**Minimum viable improvement** = Phase 1 + Phase 2 (4 weeks).

This fixes the data trust issue and delivers the core value prop: "See the Japanese meta accurately, compare it to international meta, and make informed deck building decisions." Users don't need predictions to extract value — they need **reliable snapshots** and **clear comparisons**.

Phase 3 is marketing polish for the April 10 moment. If we're behind schedule, we can ship Phase 1+2 on March 25 and still provide value. The comparison views don't require new infrastructure — just a date-range filter on existing meta snapshot queries.

---

## April 10 Deadline Analysis

**MUST be done before April 10:**

- ✅ Phase 1 (archetype accuracy fix) — **Critical path**
- ✅ Phase 2 (historical reprocess) — **Critical path**
- ❌ Phase 3 (prediction surface) — **Nice to have, not critical**

**Reasoning:** April 10 is the format rotation. Competitive players will be preparing their decks in the 2-4 weeks BEFORE rotation, not on the day. If we ship clean JP meta data by March 25, users have 2 weeks to analyze and build decks. That's sufficient.

The "prediction" narrative is marketing fluff unless we have >6 months of validation data proving our models are accurate. Shipping unvalidated predictions on April 5 risks **negative trust** if they're wrong. Better to ship proven data than speculative forecasts.

**What CAN come after April 10:**

- Predictive modeling infrastructure (Research Pass feature, not MVP)
- Retrospective format evolution tracking ("How did this archetype adapt over 6 months?")
- Future-only JP cards pipeline (social media sourcing)
- ML-based meta share forecasting

These are all **compound value** features — they require months of clean data to train/validate. Shipping them prematurely is worse than not shipping at all.

---

## Risks if Ignored

- **Data trust crisis escalates:** Every day Cinderace is mislabeled, users lose confidence. If we take 8 weeks to fix this, we've burned the closed beta goodwill.
- **Scope creep kills April 10 deadline:** Trying to ship predictive models + historical reprocess + new frontend surfaces in 6 weeks means we ship nothing. Draw hard phase boundaries.
- **Premature prediction launch damages credibility:** Shipping "Dragapult will be 15% of meta in May" without validation data means if we're wrong, users remember. Underpromise, overdeliver.

---

## Dependencies on Other Agents

### Architect

- Schema design for storing sprite-pair archetypes alongside card data
- Database migration strategy for wiping/reprocessing JP data without downtime
- Pipeline architecture: Should re-scraping be a one-time script or a new admin endpoint?
- How do we handle "Other" sprite fallback logic in the archetype detector?

### Advocate

- UX for "From Japan" page comparison views (side-by-side meta, trend charts)
- How to present deck-level insights (tech cards, card counts) without overwhelming users
- What's the right messaging for "We reprocessed your data" announcement? (Lab Note content strategy)
- April 10 marketing moment: What's the hero message? ("Prepare for rotation with JP intelligence"?)

### Risk (Glitch)

- Data integrity validation: How do we verify the new scraper produces correct archetypes?
- Rollback strategy if re-scraping fails midway
- Limitless scraping fragility: What's our fallback if they change HTML structure?
- Card mapping accuracy: How do we validate JP→EN mappings at scale?

### Quality (QA Bot)

- Test strategy for scraper changes (mock HTML fixtures vs live scraping in CI?)
- Validation tests for archetype naming logic (sprite filename → archetype name)
- Data quality checks post-reprocess (spot-check sample tournaments)
- Regression tests to prevent "Cinderace → Rogue" failures

### Research

- Deep dive into Limitless HTML structure for sprite extraction
- Sprite filename conventions (case sensitivity, delimiter patterns)
- Card mapping source reliability (where does Limitless get JP→EN mappings?)
- Predictive modeling feasibility study (statistical trends vs ML, data requirements)

### Operations

- Monitoring for scraper failures post-deployment
- Pipeline scheduling: Should re-scraping be a one-time admin action or automated?
- Performance impact of re-processing 90 days of tournaments
- Alerting if archetype detection confidence drops below threshold

---

## Trade-offs Explicit

### Option A: Ship all 3 phases atomically (8 weeks)

- **Pro:** Complete solution, predictive models live at launch
- **Con:** High risk of missing April 10 deadline, no incremental validation

### Option B: Ship Phase 1+2 first, defer predictions (4 weeks) ← **RECOMMENDED**

- **Pro:** Fixes trust crisis fast, validates scraper before investing in predictions, hits April 10 window
- **Con:** No "sexy" prediction feature for launch marketing

### Option C: Ship Phase 1 only, manual reprocess (2 weeks)

- **Pro:** Fastest path to archetype accuracy
- **Con:** Leaves historical data corrupted, users see inconsistent meta shares for weeks

**Recommended:** Option B. Predictive modeling is a premium feature that requires validation. Shipping broken predictions is worse than not shipping them.

---

## Implementation Notes

**Database wipe strategy:**

```sql
-- Phase 2: Wipe JP data for reprocess
DELETE FROM tournament_placements WHERE tournament_id IN (SELECT id FROM tournaments WHERE region = 'JP');
DELETE FROM meta_snapshots WHERE region = 'JP' AND computed_at >= '2024-11-01';
DELETE FROM tournaments WHERE region = 'JP' AND date >= '2024-11-01';
```

**Scraper validation checklist (before reprocess):**

- [ ] Test on 5 recent JP tournaments (known archetypes)
- [ ] Verify sprite extraction handles multi-card archetypes ("Dragapult Charizard")
- [ ] Confirm fallback to signature card detection when sprite is "Other"
- [ ] Validate JP→EN card mapping lookups (spot-check 10 decklists)

**Phased rollout:**

- Week 1-2: Ship Phase 1, validate on new tournaments only (don't touch historical data)
- Week 3: If validation passes, trigger historical reprocess
- Week 4: Re-run meta computation, verify JP signals, ship updated "From Japan" page
- Week 5-6: Polish comparison views, ship Lab Note, prepare April 10 messaging

**Feature flags:**

- `enable_sprite_archetypes` (default: false in prod until Phase 1 validated)
- `enable_jp_predictions` (default: false, post-April 10 feature)

---

**Timeline summary:**

- **Phase 1 (Data Trust):** Weeks 1-2 → Ship March 15
- **Phase 2 (Reprocess):** Weeks 3-4 → Ship March 29
- **Phase 3 (April 10 Prep):** Weeks 5-6 → Ship April 5
- **Post-April 10:** Predictive modeling (Research Pass feature), format evolution tracking

**Non-negotiables for MVP:**

- Archetype accuracy >95% (validated against community consensus)
- JP→EN card mapping correctness (zero decklists with unmapped card IDs)
- No "Cinderace → Rogue" failures in production

**Acceptable compromises:**

- No ML-based predictions for MVP (manual comparison views sufficient)
- No retrospective format evolution (defer to Phase 4)
- No future-only JP cards pipeline (manual curation for April 10, automate later)
