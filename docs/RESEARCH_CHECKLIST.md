# Research & Validation Checklist

> Track research tasks, validation activities, and their outcomes

---

## Data Source Research

### pokemontcg.io API

- [ ] **Test API access** - Create account, get API key if needed
- [ ] **Document rate limits** - What are the constraints?
- [ ] **Test data completeness** - Does it have all recent sets?
- [ ] **Check update frequency** - How quickly do new sets appear?
- [ ] **Evaluate image hosting** - Can we hotlink? Any restrictions?

**Findings:**

```
[Document findings here after research]
```

---

### LimitlessTCG Data Access

- [ ] **Explore public data** - What's available without partnership?
- [ ] **Check for API** - Is there a public or partner API?
- [ ] **Draft partnership email** - Prepare outreach
- [ ] **Send outreach** - Contact Limitless team
- [ ] **Evaluate scraping as fallback** - Feasibility, ethics, ToS

**Findings:**

```
[Document findings here after research]
```

**Outreach template:**

```
Subject: Data Partnership Inquiry - Competitive Pokemon TCG Tools

Hi [Limitless Team],

I'm building an open-source tool to help competitive Pokemon TCG players
with tournament preparation and deck building. I've long admired the work
you've done with LimitlessTCG - it's the definitive resource for tournament data.

I'm reaching out to explore whether there might be an opportunity to
access tournament data through an API or data partnership. My goal is to
build analysis tools on top of your data (with full attribution) that
complement rather than compete with your platform.

Specifically, I'm looking to:
- Display meta share trends and analysis
- Show card inclusion rates across successful lists
- Help players compare their builds to tournament-performing lists

I'd be happy to discuss attribution, linking back to Limitless for full
data, or any other arrangement that works for you.

Would you be open to a brief conversation about this?

Best,
[Your name]
```

---

### Training Court Integration

- [ ] **Review GitHub repo** - Understand architecture
- [ ] **Assess integration options** - Fork, contribute, or separate?
- [ ] **Reach out to maintainer** - Discuss collaboration
- [ ] **Document decision** - Build own vs. integrate

**Findings:**

```
[Document findings here after research]
```

---

## Technical Validation

### Supabase Evaluation

- [ ] **Create test project** - Set up free tier
- [ ] **Test auth flow** - Email/password, OAuth
- [ ] **Test pgvector** - Embedding storage and search
- [ ] **Evaluate free tier limits** - Sufficient for MVP?
- [ ] **Document costs at scale** - 1K, 10K, 100K users

**Findings:**

```
[Document findings here after research]
```

---

### Embedding Model Comparison

- [ ] **Test Claude embeddings** - Quality, latency, cost
- [ ] **Test open-source options** - sentence-transformers, etc.
- [ ] **Compare on sample queries** - "bench damage", "draw cards"
- [ ] **Calculate cost projections** - For full card database
- [ ] **Document decision** - Which model to use

**Findings:**

```
[Document findings here after research]
```

---

### Hosting Cost Analysis

| Scale             | Supabase | Vercel | Railway | Claude API | Total |
| ----------------- | -------- | ------ | ------- | ---------- | ----- |
| MVP (100 users)   |          |        |         |            |       |
| Growth (1K users) |          |        |         |            |       |
| Scale (10K users) |          |        |         |            |       |

---

## User Validation

### Creator/Coach Conversations

| Person | Role | Date | Key Feedback | Follow-up Needed |
| ------ | ---- | ---- | ------------ | ---------------- |
|        |      |      |              |                  |
|        |      |      |              |                  |
|        |      |      |              |                  |

**Common themes:**

```
[Synthesize feedback themes here]
```

---

### Beta Tester Recruitment

| Person | Persona             | Confirmed? | Contact | Notes |
| ------ | ------------------- | ---------- | ------- | ----- |
|        | Aspiring Competitor |            |         |       |
|        | Aspiring Competitor |            |         |       |
|        | Grinder             |            |         |       |
|        | Grinder             |            |         |       |
|        | Creator/Coach       |            |         |       |

---

### Feature Priority Survey

**Survey questions:**

1. What's the most time-consuming part of tournament preparation?
2. What tools do you currently use? What's missing?
3. Which feature would you most want?
   - Meta dashboard with trends
   - Smart deck builder with stats
   - Natural language card search
   - Matchup guides
   - Performance tracker
4. Would you pay $5-10/month for premium features?
5. Anything else you wish existed?

**Survey results:**

```
[Document survey results here]
```

---

## Monetization Research

### Advertising Networks

- [ ] **Research ad networks for gaming/hobby sites**
  - Google AdSense (baseline)
  - Mediavine (requires 50K sessions/month)
  - Ezoic (lower threshold)
  - Direct ad sales

- [ ] **Estimate CPM rates for TCG audience**
  - General gaming: $2-5 CPM
  - Niche hobby: potentially higher
  - Document findings

**Findings:**

```
[Document findings here after research]
```

---

### Affiliate Programs

| Partner              | Program    | Commission | Notes                         |
| -------------------- | ---------- | ---------- | ----------------------------- |
| TCGPlayer            | Affiliate  | ~5%        | Primary card marketplace      |
| eBay Partner Network | Affiliate  | 1-4%       | Alternative marketplace       |
| Amazon               | Associates | 1-3%       | Accessories, sleeves, etc.    |
| Card Cavern          | ?          | TBD        | Research if they have program |
| Full Grip Games      | ?          | TBD        | Research if they have program |

- [ ] **Apply to TCGPlayer affiliate program**
- [ ] **Research other card shop affiliate options**
- [ ] **Estimate revenue potential**

---

### Sponsorship Outreach

**Potential sponsors to research:**

- [ ] Ultra Pro (sleeves, deck boxes)
- [ ] Dragon Shield (sleeves)
- [ ] Local game stores / online retailers
- [ ] Tournament organizers
- [ ] Other Pokemon TCG content creators (cross-promo)

**Sponsorship package draft:**

```
[Create sponsorship deck when traffic justifies]
```

---

### Pricing Research

- [ ] **Survey: Would you pay $5/month for Pro features?**
- [ ] **Competitive pricing analysis:**
  - Metafy coaching rates
  - Patreon tiers for Pokemon creators
  - Other TCG tool subscriptions

**Survey results:**

```
[Document survey results here]
```

---

### Payment Infrastructure

- [ ] **Evaluate payment processors:**
  - Stripe (standard, 2.9% + $0.30)
  - Paddle (handles tax compliance)
  - LemonSqueezy (indie-friendly)
  - Gumroad (simple but higher fees)

- [ ] **Consider:** Do we need to handle payments ourselves or use a platform?

**Decision:**

```
[Document decision here]
```

---

## Japanese Data Research

### LimitlessTCG Japan Coverage

- [ ] **Explore https://limitlesstcg.com/tournaments/jp**
  - What data is available?
  - How far back does coverage go?
  - Are archetypes classified consistently with international?

- [ ] **Document tournament types covered:**
  - City Leagues
  - Champions Leagues
  - Japan Championships

**Findings:**

```
[Document findings here after research]
```

---

### Japanese Card Mapping

- [ ] **Research Japanese card name conventions**
- [ ] **Find existing Japanese ↔ English card mappings**
  - Bulbapedia?
  - Official Pokemon sources?
  - Community resources?

- [ ] **Identify cards legal in Japan but not international**
  - How to track release windows?
  - Official sources for set release dates?

**Resources found:**

```
[Document resources here]
```

---

### BO1 vs BO3 Analysis

- [ ] **Research how BO1 affects meta in other games**
  - MTG Arena BO1 vs BO3
  - Hearthstone (primarily BO1)

- [ ] **Document expected differences:**
  - Consistency premium in BO1
  - Aggro/speed favored
  - Tech cards less valuable (can't sideboard)
  - Matchup spread less important than raw power

**Analysis:**

```
[Document analysis here]
```

---

### Content Opportunity Validation

- [ ] **Search for existing "Japan meta report" content**
  - Who produces this currently?
  - How frequently?
  - What's the quality?

- [ ] **Gauge demand:**
  - Ask in Discord: "Would Japan meta reports be useful?"
  - Check if creators mention Japanese meta

**Findings:**

```
[Document findings here]
```

---

### Translation Infrastructure

- [ ] **Build TCG terminology glossary**
  - Core game terms (ワザ, 特性, etc.)
  - Tournament terms (優勝, ベスト4, etc.)
  - Meta analysis terms (環境, 採用率, etc.)

- [ ] **Test LLM translation quality**
  - Sample Pokecabook article through Claude
  - Sample Pokecabook article through GPT-4
  - Compare with DeepL
  - Document which handles TCG terminology best

- [ ] **Build card name mapping table**
  - Source from Bulbapedia
  - Source from TCGdex API
  - Cover top 200 competitive cards initially

- [ ] **Identify bilingual validator candidates**
  - Japanese players who compete internationally
  - English speakers in Japan
  - Reach out to 2-3 candidates

**Translation test results:**

```
[Document findings here]
```

---

### Japanese Source Outreach

| Source                   | Contact Method        | Status | Notes                            |
| ------------------------ | --------------------- | ------ | -------------------------------- |
| LimitlessTCG             | Same as main outreach |        | Ask about JP data specifically   |
| Pokecabook               | Twitter @pokeca_book  |        | May need Japanese outreach       |
| ポケカ飯                 | Twitter @pokekameshi  |        | Statistical focus aligns with us |
| pokemoncard.io (arelios) | Site contact          |        | Already doing English JP reports |

**Outreach notes:**

```
[Document findings here]
```

---

## Legal/Compliance

- [ ] **Review Pokemon Company fan content policy**
- [ ] **Review pokemontcg.io terms of service**
- [ ] **Review LimitlessTCG terms of service**
- [ ] **Draft platform ToS** (can defer post-MVP)
- [ ] **Determine image usage policy**

**Findings:**

```
[Document findings here after research]
```

---

## Community Presence

### Discord Server Planning

- [ ] **Choose server name**
- [ ] **Plan channel structure**
- [ ] **Draft server rules**
- [ ] **Set up roles**
- [ ] **Decide launch timing** - Before or after MVP?

**Channel structure draft:**

```
# INFORMATION
- welcome
- announcements
- roadmap

# GENERAL
- general-chat
- meta-discussion

# FEEDBACK
- feature-requests
- bug-reports
- beta-testing

# RESOURCES
- useful-links
- faq
```

---

### Content Calendar (Post-Launch)

| Week   | Content Type | Topic                        | Status |
| ------ | ------------ | ---------------------------- | ------ |
| Launch | Announcement | Platform launch post         |        |
| +1     | Article      | "State of the Meta" snapshot |        |
| +2     | Tutorial     | How to use deck builder      |        |
| +3     | Article      | Meta trends analysis         |        |
| +4     | Feature      | New feature announcement     |        |

---

## Decision Log

Track key decisions and rationale.

| Date | Decision                            | Options Considered | Rationale                           |
| ---- | ----------------------------------- | ------------------ | ----------------------------------- |
|      | Stack: Next.js + FastAPI + Supabase | Various            | Backend expertise, cost, simplicity |
|      |                                     |                    |                                     |
|      |                                     |                    |                                     |

---

## Blockers & Risks

| Risk                                | Likelihood | Impact | Mitigation                                        | Status |
| ----------------------------------- | ---------- | ------ | ------------------------------------------------- | ------ |
| LimitlessTCG says no to partnership | Medium     | High   | Build scraper fallback, focus on analysis layer   | Open   |
| Hosting costs exceed budget         | Low        | Medium | Aggressive caching, free tier limits              | Open   |
| Low adoption                        | Medium     | High   | Validate before building, creator partnerships    | Open   |
| Pokemon Company legal action        | Low        | High   | Follow fan content guidelines, attribute properly | Open   |

---

## Next Actions

Priority order for immediate execution:

1. [ ] **Test pokemontcg.io API** - Validate data access (1 hour)
2. [ ] **Draft LimitlessTCG outreach** - Personalize template above (30 min)
3. [ ] **Set up Supabase project** - Test free tier (1 hour)
4. [ ] **Schedule creator conversations** - 2-3 people this week
5. [ ] **Create Discord server** - Basic setup for community building
