# Interview Transcript: JP Archetype Data Pipeline Overhaul

## Round 1

**Q:** When you say archetypes are 'getting lost in translation' — have you noticed specific symptoms?
**A:** All of the above — too many Rogues, name mismatches, missing JP data, and meta shares looking wrong. Specific example: Cinderace EX was identified as an emerging archetype in Japan which is completely wrong — likely a card mis-mapping issue. JP-to-EN card mapping is not straightforward and needs improvement.

**Q:** Would you prefer Limitless as truth, hybrid, or replace entirely?
**A:** Limitless should be the primary source of truth — it's the de-facto standard for competitive Pokemon TCG. Some rogue decks get labeled "Other" with the Substitute plush sprite on Limitless. We can come up with our own labels for those cases, but Limitless labels will be better for the vast majority.

**Q:** What level of predictive analysis?
**A:** All three levels. Meta share tracking for high-level trends. Deck-level insights (tech cards, core card counts, innovations) — these can be the difference between winning a tournament or not. Predictive model with confidence scores. The core value prop: discover patterns, surface insights, save users from dumpster-diving through scattered sources, and let them focus on refining decklists, testing ideas, planning for matchups, and being ready for Regionals/ICs/Worlds.

**Q:** Historical data integrity?
**A:** Full re-process. Can't trust current data, no end users yet, so clean slate is fine.

## Round 2

**Q:** For the Limitless sprite-to-archetype mapping: should we build a maintained mapping table, auto-derive from sprites, or use LLM assist?
**A:** Auto-derive from sprites. This is what the community does — every deck has 1-2 flagship Pokemon that define the strategy (e.g., "Dragapult Dusknoir", "Dragapult Charizard", "Dragapult Noctowl"). LLMs should be saved for more important tasks.

**Q:** Regarding the card ID mapping problem (Cinderace EX misidentification): what's the ideal fix?
**A:** Both — fix card mapping AND use sprite-based archetypes. Limitless already does proper JP→EN card mapping (e.g., Rocket's Honchkrow has both EN and JP pages linked). For future-only JP cards (like Meowth EX from Nihil Zero), we'll need a separate pipeline sourcing English translations from X/BlueSky accounts that share translations as soon as JP cards are revealed.

**Q:** For the predictive model: post-rotation viability or broader meta forecasting?
**A:** Both. Current format needs meta analysis using international card pool + tournament data. Future format analysis as new JP cards emerge. The platform should handle: current format meta, future format predictions, and retrospective format evolution analysis — all three time horizons. Key sources: limitlesstcg.com/cards, limitlesstcg.com/tournaments, play.limitlesstcg.com/tournaments.

## Round 3 — Council Assembly

**Q:** Approve 6-member council (Architect, Skeptic, Scout, Strategist, Craftsman, Advocate)?
**A:** Add Operator and Chronicler too — full 8-member council. Operator should examine infrastructure improvements (security, cloud cost savings). Chronicler should update all docs/ and markdown files so the work is shareable with other AI agents and human developers.
