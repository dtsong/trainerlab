# Limitless Labs Evaluation (Issue #349)

Purpose: evaluate `https://labs.limitlesstcg.com` as an early signal source for major events (post-major fast-follow), and decide whether/how to incorporate it into TrainerLab ops.

## What Limitless Labs Is

Limitless Labs is an "experimental" Limitless site that provides standings + metagame analysis for events where detailed standings can be derived from external tournament platforms (explicitly mentioned: `rk9.gg` and `playlatam.net`).

It contains event pages with:

- Standings (with records, tie rates, and optional decklist links)
- Per-event metagame breakdown pages (`/<event_id>/decks`) with deck share + aggregated records
- Day 1 / Day 2 / conversion views via query params

## Why It Matters For TrainerLab

TrainerLab's operational goal is to detect whether post-major official data is available quickly enough (Mon/Tue UTC fast-follow) and avoid "stuck" freshness gating in `/meta` and `/tournaments`.

Limitless Labs can act as a _leading indicator_ because:

- It can surface standings + archetype distribution quickly when RK9/playlatam data is available.
- The per-event decks view is a compact summary that is easier to consume than scraping decklists.

## What Data Is Available (Observed)

Example event page:

- `https://labs.limitlesstcg.com/0053/standings`

Observed fields:

- Event name, date range, player count, tie percentage
- Explicit upstream links (e.g., RK9 pairings + roster)
- Standings table (player name, country, points, record, tie-breakers)
- Deck archetype link per player (and optional decklist link)

Example metagame page:

- `https://labs.limitlesstcg.com/0053/decks`

Observed fields:

- Archetype label + count
- Share percentage
- Aggregated record and win%
- Variants toggle via `?combine`
- Views via `?day=1`, `?day=2`, `?conversion`

## Coverage + Limitations

- Not all events are present; coverage depends on whether RK9/playlatam provides sufficient data.
- Appears focused on major TPCI-style events (Regionals/Internationals/Worlds/Specials) rather than grassroots.
- Japan coverage is likely limited (JP events typically are not on RK9/playlatam).

## Data Quality Notes

Limitless Labs states that standings are computed outside the official tournament software and "might contain errors".

Practical implication:

- Good for _signal_ and early ops checks.
- Risky as a single source of truth for canonical tournament results.

## Compliance / Risk

The site is ad-supported and intended for human browsing.

`https://labs.limitlesstcg.com/robots.txt` does not include explicit allow/deny rules in the fetched version; it contains a content-signal explanation but no concrete signals.

If we integrate:

- Minimize scraping volume (majors only; low-frequency polling).
- Prefer extracting aggregated metagame tables over standings/player rows.
- Avoid ingesting or storing player names if not needed (PII minimization).
- Attribute Limitless clearly in UI and docs.

## Integration Options

1. Signal-only (recommended first step)

- Use per-event `/<id>/decks` as a readiness signal for "data exists".
- Only ingest: event_id, event_end_date, players, archetype counts/shares, and timestamp.
- Do not ingest: player names, individual decklists.

2. Full ingestion

- Parse standings + decklists for each player.
- Higher operational complexity and higher privacy/compliance risk.

3. Go direct to upstream (RK9 / playlatam)

- Potentially more stable/official for the raw data.
- Requires separate parsers/auth/rate-limit handling per upstream.

## Recommendation

Adopt Limitless Labs as an _early major-event signal_ source, not as canonical truth.

Suggested implementation approach:

- Add a lightweight "major readiness" job that checks the newest known major event id(s) and attempts to parse the `/<id>/decks` table.
- Treat the presence of a non-trivial metagame table as "partial" readiness.
- Keep TrainerLab's primary snapshots anchored on our existing ingestion + verification.

Follow-up tasks (if we proceed):

- Define stable mapping between TrainerLab tournaments and Limitless Labs ids.
- Implement a parser for the `/<id>/decks` table (counts + shares + day filters).
- Add attribution + source coverage annotations: `Limitless Labs (via RK9/playlatam)`.
