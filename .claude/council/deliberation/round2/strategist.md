# Strategist Round 2 -- Challenge & Synthesis

## Revised Timeline: Phase 1 Shipped in ~1 Day, Not 2 Weeks

Phase 1 was scoped at 2 weeks. It shipped in roughly a day. That tells us two things: (1) the implementation complexity was overestimated, which means the remaining phases are probably smaller than projected too, and (2) the architecture decisions are now proven in code, not just design docs, which de-risks everything downstream.

**Updated timeline (aggressive but realistic):**

| Phase                                          | Original    | Revised     | Rationale                                                        |
| ---------------------------------------------- | ----------- | ----------- | ---------------------------------------------------------------- |
| Phase 1: Data Trust (scraper fix + normalizer) | Weeks 1-2   | DONE        | PR #312 merged                                                   |
| Phase 2: Validation + Historical Reprocess     | Weeks 3-4   | Week 2-3    | Normalizer exists; validation is the blocker, not implementation |
| Phase 3: Frontend polish + April 10 prep       | Weeks 5-6   | Week 4      | Comparison views use existing meta endpoints with clean data     |
| **Total**                                      | **6 weeks** | **4 weeks** | **Ship by ~March 7 instead of April 5**                          |

The 2-week buffer before April 10 is pure upside -- time for polish, bug fixes, content (Lab Note), and marketing prep. Do not fill this buffer with new scope.

---

## Challenges to Other Agents

### Advocate: "Format Forecast Widget in MVP" -- DEFERRED

**Their position:** Put a "Format Forecast" widget on the homepage as the primary discovery entry point, with confidence badges, prediction modals, and historical accuracy tracking.

**My response: Defer to post-April 10.** Here is why:

1. **We have zero prediction accuracy data.** The Advocate's own design includes a "Historical Accuracy Tracker" showing "High confidence: 85% accurate." We cannot display that because we have never made a prediction. Shipping a forecast widget with no track record is the exact "premature prediction launch" risk I flagged in Round 1.

2. **The widget requires new backend endpoints.** "Top N archetypes coming to EN soon, sorted by predicted impact" does not exist today. Building it requires defining what "predicted impact" means, computing confidence scores, and creating a new API surface. That is 3-5 days of work for a feature we cannot validate.

3. **The core user need is served without it.** A competitive player preparing for April 10 needs: (a) accurate JP meta shares, (b) side-by-side JP vs EN comparison, (c) card-level insights. All of these are served by clean data in the existing `/meta/japan` page. The Forecast widget is the _polish_ layer, not the _value_ layer.

**What IS in MVP from the Advocate's position:**

- Sprite-based archetype display in the existing meta dashboard (sprites are already scraped and stored)
- BO1 context banner (already exists, just needs to be persistent rather than dismissible)
- JP Signal badges on the meta dashboard (already computed, just needs clean data)

**What is deferred:**

- Homepage Format Forecast widget
- Prediction confidence system (high/medium/low badges)
- Historical accuracy tracker
- Prediction detail modal

The Advocate's user journey analysis is strong. The information hierarchy problem is real. But the fix for launch is **better data in existing surfaces**, not **new surfaces with unvalidated data**.

---

### Skeptic: "Full Root-Cause Before Re-scrape" -- PARTIALLY ACCEPTED

**Their position:** Trace the Cinderace EX error end-to-end with specific tournament URLs and database records before any reprocessing. Full audit trail with validation gates at every layer.

**My response: Accept the canary testing requirement. Reject the full forensic audit as a blocker.**

The Skeptic is right that we need validation before bulk reprocessing. But Phase 1 already addressed the root cause: the broken `img.pokemon` CSS selector that was producing garbage archetype labels. The `ArchetypeNormalizer` now has a 4-level priority chain (sprite_lookup, auto_derive, signature_card, text_label) with `archetype_detection_method` stored for every placement. This IS the audit trail.

**What I accept from the Skeptic:**

- Canary test on 10-20 recent JP tournaments before bulk reprocess (1 day of effort)
- 95% archetype accuracy threshold against Limitless ground truth (compare our labels to what Limitless shows)
- Monitoring for sprite extraction success rate in production

**What I reject as a blocker:**

- Full end-to-end trace of the original Cinderace bug through specific tournament URLs. The bug was in the CSS selector. The selector is fixed. The old code path is gone. Forensic archaeology on dead code costs 2-3 days and delivers zero user value.
- "Validation gates at every layer" before reprocessing. We have `archetype_detection_method` on every placement now. That IS the validation gate. We can query "how many placements used each detection method" after reprocess and spot problems instantly.

The Skeptic's scraping fragility analysis is valuable for long-term resilience, but it should not block Phase 2. Schedule it as a parallel workstream (structured logging, HTML change detection) that runs alongside the reprocess.

---

### Architect: Mostly Aligned

The Architect's 3-layer architecture (ingestion, normalization, analysis) is exactly what PR #312 implemented. The `raw_archetype` + `archetype_detection_method` columns provide the auditability they wanted. The `archetype_sprites` lookup table is live. Schema is sound.

One minor push: the Architect proposed a 5-phase migration spanning 5 weeks. With Phase 1 done, Phases 2-3 (backfill raw data + normalization cutover) collapse into a single "validate and reprocess" step. Do not artificially separate them -- they are the same operation.

---

### Operator: Well-Scoped

The Operator's infrastructure analysis is solid and the cost projections ($2.20 for full reprocess) confirm this is operationally cheap. The structured logging recommendation is good but should be a parallel workstream, not a blocker. The min_instances=0 recommendation (saving $62/month) is a free win -- do it now.

---

### Craftsman and Chronicler: Proportional Response Needed

The Craftsman wants golden datasets, shadow mode, staging DB dry runs, and a 4-phase rollout. The Chronicler wants 10 documentation updates, an ADR, a data dictionary, and memory bank updates.

Both are right in principle. Both propose more process than this project needs right now.

**From Craftsman -- accept:**

- 5-10 golden dataset fixtures for JP tournaments (2-3 hours of work, high ROI)
- Regression baseline capture before reprocess (snapshot current meta shares)
- Rollback plan (backup table before reprocess)

**From Craftsman -- defer:**

- Shadow mode (1 week of parallel running). The normalizer is already unit-tested against 37 test cases. Canary test on 10-20 real tournaments is sufficient.
- Staging DB dry run. The reprocess is cheap ($2.20), reversible (backup table), and the normalizer logic is tested. A staging environment for a one-time operation is over-engineered.

**From Chronicler -- accept:**

- Update CLAUDE.md current focus section (5 minutes)
- Update MEMORY.md with archetype detection notes (5 minutes)

**From Chronicler -- defer:**

- DATA_DICTIONARY.md, ADR, OPERATIONS.md, 6 other doc updates. These are valuable but they are documentation debt, not launch blockers. Schedule after April 10.

---

## MVP Scope Lock

Given Phase 1 is done, the MVP for launch is:

### IN (Must ship before April 10)

1. **Canary validation** -- Test normalizer against 10-20 recent JP tournaments, verify >95% archetype accuracy vs Limitless ground truth. (1 day)
2. **Golden dataset fixtures** -- Capture 5-10 JP tournament HTML files with expected outputs as regression tests. (0.5 day)
3. **Historical reprocess** -- Wipe JP tournament placements from last 90 days, re-scrape with new normalizer pipeline. Capture regression baseline first. (2 days including monitoring)
4. **Meta recomputation** -- Re-run meta snapshot computation for JP region with clean data. Verify JP Signal badges and meta shares look correct. (0.5 day)
5. **Existing frontend with clean data** -- The `/meta/japan` page, meta dashboard, and JP Signal badges already exist. They just need correct data flowing through them. No new frontend work required. (0 days)
6. **BO1 disclaimer persistence** -- Make the BO1 context banner non-dismissible on JP data views. (0.5 day)

**Total MVP effort: ~5 days of work (1 week)**

### OUT (Deferred post-April 10)

- Format Forecast homepage widget
- Prediction confidence system
- Prediction detail modal
- Historical accuracy tracker
- New API endpoints for "predicted impact"
- ML-based meta share forecasting
- Retrospective format evolution views
- DATA_DICTIONARY.md and other documentation
- Structured logging overhaul
- Limitless HTML change detection system
- Shadow mode / staging DB dry run

### FAST-FOLLOW (April 10 - April 30)

- Side-by-side JP vs EN meta comparison view on `/meta/japan`
- "JP meta 60 days ago vs EN meta today" comparison (manual lag analysis)
- Lab Note announcing pipeline improvements
- Documentation cleanup (CLAUDE.md, data dictionary, ADR)

---

## Key Tensions Resolved

### Is "Format Forecast" in MVP?

**No.** It requires new endpoints, unvalidated predictions, and confidence scoring that does not exist. Ship clean data in existing surfaces first. If engagement with `/meta/japan` is high after clean data ships, build Forecast as a Phase 4 feature.

### Should historical reprocess happen now or after more validation?

**After canary validation, not after full forensic audit.** Canary test on 10-20 tournaments (1 day). If accuracy is >95%, proceed with bulk reprocess. The normalizer is unit-tested with 37 test cases and the detection method is stored on every record for post-hoc analysis.

### What is the acceptance criteria for archetype accuracy?

**>95% match against Limitless's own archetype labels, measured on 20 recent JP tournaments.** Specifically:

- For each tournament, compare our `archetype` field to what Limitless shows as the deck identity
- Count matches. "Match" means same archetype identity (allow for minor naming variations like "Charizard ex" vs "Charizard")
- If accuracy is 95%+, proceed with reprocess
- If accuracy is 90-95%, investigate the 5-10% mismatches, fix sprite map or fallback logic, re-test
- If accuracy is <90%, something is fundamentally broken -- stop and debug

---

## Prioritized Backlog (Ordered)

| #   | Item                                       | Size       | Value    | Notes                                    |
| --- | ------------------------------------------ | ---------- | -------- | ---------------------------------------- |
| 1   | Canary validation (10-20 JP tournaments)   | S (1d)     | Critical | Gate for everything else                 |
| 2   | Golden dataset fixtures (5-10 tournaments) | S (0.5d)   | High     | Regression safety net                    |
| 3   | Regression baseline capture                | XS (2h)    | High     | Snapshot current meta shares before wipe |
| 4   | Historical JP reprocess (90 days)          | M (2d)     | Critical | Core value delivery                      |
| 5   | Meta recomputation for JP                  | S (0.5d)   | Critical | Makes clean data visible                 |
| 6   | BO1 banner persistence fix                 | XS (0.5d)  | Medium   | UX trust signal                          |
| 7   | CLAUDE.md + MEMORY.md updates              | XS (10min) | Medium   | Agent knowledge hygiene                  |
| 8   | Cloud Run min_instances=0                  | XS (10min) | Medium   | Saves $62/month                          |
| 9   | Side-by-side JP vs EN comparison view      | M (2-3d)   | High     | Fast-follow for April 10                 |
| 10  | Lab Note: "Improved JP Meta Intelligence"  | S (1d)     | Medium   | Marketing for April 10                   |
| 11  | Structured logging for pipeline            | M (2-3d)   | Medium   | Operational visibility                   |
| 12  | Format Forecast widget (homepage)          | L (5d)     | High     | Post-April 10, needs prediction infra    |
| 13  | Prediction confidence system               | L (5d)     | Medium   | Requires historical accuracy data        |
| 14  | DATA_DICTIONARY.md + ADR                   | M (2d)     | Medium   | Documentation debt                       |

Items 1-8 are the MVP (approximately 1 week of effort). Items 9-10 are the April 10 fast-follow. Items 11-14 are post-launch.

---

## Final Word

Phase 1 shipping fast is a signal: the team executes well on focused scope. Do not reward that by expanding scope. The path to April 10 is: validate the normalizer, reprocess JP data, and let clean data flow through existing surfaces. Everything else is a fast-follow. Ship small. Ship correct. Ship soon.
