# Recommendation model v1.0

This is a deterministic teaching model, not a statistical win-rate predictor. Source: `backend/app/services/scoring.py`. All champion traits, pair synergies and lane ratings are hand-authored sample inputs in `backend/app/data/champions.json`.

## Eligibility and validation

Only champions in the personal pool whose supported roles include the requested role are eligible. Champions already picked by either team are excluded. The API rejects unknown champions, duplicate picks, champions on both teams, invalid roles, empty pools, more than 4 allies or 5 enemies, comfort outside integer 1–5, and lane opponents not on the enemy team. Jungle requests cannot specify a lane opponent. If no candidate remains, return HTTP 422 with a usable message. Partial drafts and fewer than three eligible candidates are supported with explicit warnings.

## Formula

Each factor is clamped to [0, 1], multiplied by its weight, then rounded to two decimals. The total is the sum of these rounded contributions, rounded to two decimals. Weights total 100. Sort descending by score, with alphabetical champion name as a stable tie-break. Return up to three candidates.

| Factor | Weight | Calculation |
| --- | ---: | --- |
| Lane matchup | 20 | `(rating + 1) / 2`. Curated rating in [-1, 1]. Unknown or unselected gives 0.5; never implies an even lane. |
| Comfort | 15 | User rating / 5. Default 3 / 5. |
| Frontline | 10 | Team-need formula below; target 4. |
| Engage | 7 | Team-need formula; target 4. |
| Carry protection | 7 | Team-need formula; target 4. |
| Crowd control | 7 | Team-need formula; target 5. |
| Scaling | 7 | Team-need formula; target 7. |
| Damage balance | 10 | `1 - 2 * abs(physical_share - 0.5)` after adding the candidate. |
| Ally synergy | 7 | `min(1, 0.5 + 0.25 * curated_pair_count)`; pairs are symmetric. |
| Enemy threats | 10 | Neutral 0.5 plus explicit conditional bonuses below, capped at 1. |

**Team-need formula:** Champion traits are ordinal 0–3 sample ratings. Let `allied_total` be the sum before the candidate joins. `need = clamp((target - allied_total) / target)`. Contribution is `0.5 + 0.5 * need * candidate_trait / 3`. Existing coverage earns neutral credit for all candidates; useful traits receive bonuses when a gap exists. This intentionally favors balanced team completion over repeating an already-filled role. It is a simple teaching heuristic, not an optimized model.

**Damage mix:** Equally average each champion's physicalShare, including the candidate. Magic share is one minus physical share. This does not model items, gold, time, true damage, or each champion's actual damage output. The UI labels it an illustrative profile.

**Threat bonuses:** Add 0.3 for the armor tag against enemy physical share >= 60%; add `0.2 * peel / 3` when any enemy has the dive tag; add 0.15 for the isolate tag when an enemy has frontline 3. These represent only explicit sample interactions. Malphite's armor bonus does not imply immunity to Darius's true damage; the curated lane penalty and explanation remain present.

## Guides and explanations

Rune pages and core items are sample champion-specific guides derived from archetypes with overrides. Situational items respond to enemy damage, healing and dive tags. An item already in the core guide is omitted from the situational list. Purchases are suggestions, not a fixed mandatory order.

Template explanations always work offline. The optional OpenAI service receives only scored facts, uses a fixed provider URL and a 12-second timeout, and returns prose mapped to champion names. It cannot change ranks, scores, factors, runes, or items. Invalid/missing/failed responses fall back to templates. AI text can still be imperfect; the visible score breakdown remains the source of truth.

## Data provenance and limits

- 38 supported champions; not the full League roster.
- Five curated lane matchups, all versus Darius, chosen for the required demo. Others are explicitly unrated.
- Static champion names, titles, and portraits plus item names/costs are pinned to Riot Data Dragon **14.24.1** for a reproducible historical sample. They are not current-patch data.
- No player account data, Riot API key, live match API, scraped statistics, win rates, or hidden gameplay information.
- No lane-role inference from enemy order; the user explicitly selects the lane opponent.
- Updating static metadata does not update heuristic traits or builds. Validate and version these separately.

To replace the sample model, keep the API schemas stable, introduce a new catalog/statistics provider behind `services/`, calibrate weights on a documented dataset, and add matchup coverage tests before claiming statistical accuracy.

## Required example with default comfort

| Rank | Champion | Fit score | Main tradeoff |
| --- | --- | ---: | --- |
| 1 | Mordekaiser | 59.54 | Closer sample Darius lane and magic damage; less initiation/protection. |
| 2 | Ornn | 57.23 | Frontline and curated ally synergies; difficult sample Darius lane. |
| 3 | Malphite | 56.22 | Engage, Orianna synergy, armor against physical profiles; Darius still threatens extended trades and true damage. |

These are version-1 fixture results, not empirical champion performance. Changing comfort or picks can change the ordering.
