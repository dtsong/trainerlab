# Interview Summary: JP Archetype Data Pipeline Overhaul

## Core Intent

Fix the broken data pipeline for Japanese tournament archetype labeling by adopting LimitlessTCG's sprite-pair archetype system as the source of truth, fixing JP→EN card ID mappings, and building multi-layered predictive intelligence (meta shares, deck-level insights, predictive models) to help international competitors prepare for the April 10 rotation and beyond.

## Key Decisions Made

- **Limitless as primary archetype source**: Use sprite-pair combinations from LimitlessTCG as the authoritative archetype labels, with our own detection as fallback for unlabeled/rogue decks
- **Auto-derive archetype names from sprites**: No maintained mapping table — generate names like "Dragapult Charizard" directly from sprite filenames (community convention)
- **Fix card ID mappings AND use sprite archetypes**: Both are needed — sprites for archetype labels, card mappings for deck-level analysis
- **Full data reprocess**: Wipe and re-scrape all JP tournament data with the new pipeline — no trust in current data
- **Three time horizons**: Current format meta, future format predictions (post-rotation), and retrospective format evolution
- **Future JP cards**: Cards not yet in EN will need a separate pipeline (social media translations from X/BlueSky)

## Open Questions for Deliberation

- How to handle Limitless's "Other"/Substitute sprite for truly rogue decks — when to apply our own detection?
- Architecture for the predictive model: statistical trend analysis vs ML-based forecasting
- How to normalize BO1 (JP) vs BO3 (international) meta differences in predictions
- Schema changes needed to store sprite-derived archetypes alongside card-level data
- Pipeline for future-only JP cards (social media sourcing is complex and fragile)
- How to handle format evolution tracking (retrospective analysis) at the data model level

## Perspective Relevance Scores

| Perspective     | Score (0-5) | Rationale                                                                                                |
| --------------- | ----------- | -------------------------------------------------------------------------------------------------------- |
| Architecture    | 5           | Major data model changes, pipeline redesign, new scraping logic, schema evolution                        |
| User Experience | 3           | Frontend impact — archetype displays, prediction surfaces, Japan page improvements                       |
| Risk            | 5           | Data integrity crisis (Cinderace misidentification), scraping fragility, card mapping accuracy           |
| Quality         | 4           | Need testing strategy for scrapers, validation of archetype labels, data integrity checks                |
| Research        | 4           | Need to understand Limitless HTML structure deeply, card mapping sources, predictive modeling approaches |
| Strategy        | 4           | Phasing a large initiative (fix data → build insights → predictive model), MVP scoping                   |
| Operations      | 3           | Pipeline scheduling, reprocessing infrastructure, monitoring for data quality                            |
| Documentation   | 1           | Minimal docs needed beyond code documentation                                                            |
