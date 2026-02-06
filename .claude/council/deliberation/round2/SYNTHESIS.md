# Round 2 Synthesis — JP Archetype Data Pipeline Overhaul

**Date:** 2026-02-06
**Agents:** Architect, Strategist, Skeptic, Craftsman, Scout, Operator, Chronicler, Advocate

---

## 1. Universal Convergence (All 8 Agents Agree)

1. **Phase 1 was a clean success.** PR #312 delivered the right architecture. The `ArchetypeNormalizer` priority chain, provenance columns, and 37 tests are solid foundations.

2. **Canary validation before historical reprocess.** Test the normalizer against 10-20 recent JP tournaments, verify >95% accuracy against Limitless ground truth. This is a gate, not optional.

3. **Golden dataset fixtures required.** Capture 5+ real Limitless JP tournament HTML files with hand-validated expected outputs as regression tests. The current synthetic fixture is insufficient.

4. **Do NOT wipe historical data.** Backfill in place. Preserve `raw_archetype` and `raw_archetype_sprites` for provenance. Re-normalize existing rows using the normalizer, do not DELETE and re-scrape.

5. **DB-backed sprite map before bulk reprocess.** Wire `ArchetypeNormalizer` to the `archetype_sprites` table (which already exists from migration 022). The hardcoded `SPRITE_ARCHETYPE_MAP` should seed the table, not be the runtime source.

6. **Defer ML-based predictions.** Ship descriptive JP intelligence (meta shares, comparisons, divergences) for April 10. Quantitative forecasting requires a complete prediction cycle to calibrate.

7. **Structured logging in the normalizer.** Add JSON-structured log entries for every `resolve()` call before reprocessing historical data.

---

## 2. Concrete Bugs Found

### CRITICAL: `derive_name_from_key` hyphenation bug (Skeptic, Craftsman)

- `"chien-pao-baxcalibur"` → `"Chien Pao Baxcalibur"` (WRONG, should be `"Chien-Pao Baxcalibur"`)
- Cannot distinguish separator hyphens from name hyphens
- Masked today by `SPRITE_ARCHETYPE_MAP` coverage, but `auto_derive` is the fallback for NEW archetypes
- **Fix required before reprocess** (add to map or fix the method)

### HIGH: Regex mismatch between scraper and normalizer (Skeptic)

- Scraper: `r"/([a-zA-Z_-]+)\.png"` — NO digits
- Normalizer: `r"/([a-zA-Z0-9_-]+)\.png"` — WITH digits
- If Limitless ever uses `mewtwo2.png`, the scraper silently drops it
- **Fix: align to `[a-zA-Z0-9_-]+` in both places**

### HIGH: Mega Evolution `-mega` suffix (Scout)

- Limitless uses `absol-mega.png`, `kangaskhan-mega.png` for Mega archetypes
- `auto_derive` produces `"Absol Mega"` instead of community name `"Mega Absol Box"`
- Mega archetypes total ~15% of current JP meta
- **Fix: add all `-mega` sprite keys to `SPRITE_ARCHETYPE_MAP`**

### HIGH: Sprite map coverage gap (Scout)

- 24 entries cover ~67% of JP meta share
- 13 archetypes >0.5% JP meta share are MISSING
- Coverage must reach 80%+ before reprocess (Skeptic's threshold)
- **Fix: expand to 40+ entries covering current JP meta**

---

## 3. Key Tensions Resolved

### Documentation timing

- **Chronicler:** CODEMAP.md + CLAUDE.md MUST update before Phase 2 (45 min)
- **Strategist:** Defer most docs to post-launch
- **Resolution:** CODEMAP.md + CLAUDE.md updates (45 min) before Phase 2 code. ADR + DATA_DICTIONARY.md during Phase 2, not after.

### Shadow mode vs canary testing

- **Craftsman:** Proposed shadow mode (1 week parallel run)
- **Architect, Operator, Strategist:** Reject as overengineered for closed beta
- **Resolution:** Skip shadow mode. Canary test (10-20 tournaments) + `archetype_detection_method` column provides equivalent signal without infrastructure.

### Frontend work timing

- **Advocate:** Ship sprite display PR in parallel with backend Phase 2
- **Strategist:** Clean data first, frontend follows
- **Resolution:** Small frontend PR (sprites + persistent BO1) CAN run in parallel. No new API endpoints or prediction widgets until data is clean.

### Reprocess approach

- **Strategist Round 1:** Wipe JP data and re-scrape
- **Architect + Skeptic + Operator:** Backfill in place (re-fetch HTML, extract sprites, re-normalize)
- **Resolution:** Backfill in place. ~200 standings pages at 0.5 req/sec = 7 min. Paginated via Cloud Tasks. Under $3 compute.

---

## 4. Recommended Phase 2 Plan

### Pre-reprocess (2-3 days)

| #   | Task                                              | Owner      | Effort  |
| --- | ------------------------------------------------- | ---------- | ------- |
| 1   | Update CODEMAP.md + CLAUDE.md                     | Chronicler | 45 min  |
| 2   | Fix regex mismatch (align `[a-zA-Z0-9_-]+`)       | Skeptic    | 30 min  |
| 3   | Expand SPRITE_ARCHETYPE_MAP to 40+ entries        | Scout      | 2-3 hrs |
| 4   | Wire normalizer to `archetype_sprites` DB table   | Architect  | 4-6 hrs |
| 5   | Add structured logging to `resolve()`             | Operator   | 2 hrs   |
| 6   | Build `reprocess-archetypes` endpoint (paginated) | Operator   | 4-8 hrs |

### Validation (1 day)

| #   | Task                                     | Owner      | Effort |
| --- | ---------------------------------------- | ---------- | ------ |
| 7   | Capture 5 golden dataset fixtures        | Craftsman  | 3 hrs  |
| 8   | Canary test: 10-20 recent JP tournaments | Strategist | 4 hrs  |
| 9   | Verify >95% accuracy vs Limitless        | Skeptic    | 2 hrs  |
| 10  | Verify detection method distribution     | Skeptic    | 1 hr   |

### Reprocess (1-2 days)

| #   | Task                                       | Owner     | Effort |
| --- | ------------------------------------------ | --------- | ------ |
| 11  | Snapshot current JP meta shares (baseline) | Craftsman | 1 hr   |
| 12  | Dry-run reprocess on 50 tournaments        | Operator  | 2 hrs  |
| 13  | Full production reprocess                  | Operator  | 3 hrs  |
| 14  | Recompute JP meta snapshots                | Architect | 1 hr   |
| 15  | Post-reprocess validation                  | Skeptic   | 1 hr   |

### Parallel frontend (1-2 days)

| #   | Task                                                          | Owner    | Effort |
| --- | ------------------------------------------------------------- | -------- | ------ |
| 16  | `ArchetypeSprites` component (32x48px inline sprites)         | Advocate | 4 hrs  |
| 17  | BO1 banner persistence (non-dismissible or persistent labels) | Advocate | 2 hrs  |
| 18  | Reorder Japan page: divergence above pie chart                | Advocate | 2 hrs  |

**Total: ~1.5-2 weeks. Ship by ~Feb 21. Buffer until April 10 for polish.**

---

## 5. Explicitly Deferred (Post-April 10)

- Format Forecast homepage widget (Advocate) — requires prediction infra
- Prediction confidence system (High/Medium/Low badges)
- Historical accuracy tracker
- ML-based meta share forecasting
- Full `limitless.py` decomposition into submodules (Craftsman)
- `archetype_version` column (Architect concedes: over-engineering)
- `reprocessing_batch` table (Architect rejects: unnecessary)
- Staging DB dry run (Strategist rejects: one-time operation)
- Prometheus metrics (Architect rejects: structured logs sufficient for beta)

---

## 6. Non-Negotiables (Unanimous or Near-Unanimous)

1. **Do not DELETE existing tournament data.** Backfill in place. (Architect, Skeptic, Operator)
2. **Golden datasets before bulk reprocess.** (Craftsman, Skeptic, Strategist)
3. **>95% accuracy gate on canary test.** (Strategist, Skeptic)
4. **Wire DB table before reprocess.** (Skeptic, Architect, Scout)
5. **Fix bugs found in code review** — regex mismatch, sprite map coverage. (Skeptic, Scout)
6. **CODEMAP.md + CLAUDE.md updates before Phase 2 code.** (Chronicler)
7. **Structured logging before reprocess.** (Operator, Craftsman)

---

## 7. Agent Concessions

| Agent      | Dropped From Round 1                                                            |
| ---------- | ------------------------------------------------------------------------------- |
| Architect  | `archetype_version` column, shadow mode, 5-phase migration (collapsed to 3)     |
| Strategist | "Wipe and re-scrape" approach → accepts backfill in place                       |
| Skeptic    | "Full forensic audit as blocker" → accepts parallel validation with hard gate   |
| Craftsman  | Shadow mode (1 week) → accepts canary test + provenance column as sufficient    |
| Chronicler | Full doc suite as Phase 2 blocker → CODEMAP.md + CLAUDE.md only as prerequisite |
| Advocate   | Format Forecast in MVP → defers to post-April 10                                |
| Operator   | Prometheus metrics → accepts structured logging for beta                        |
| Scout      | No concessions (first positions held)                                           |
