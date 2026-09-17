# Recommendation model v2.0

The deterministic engine combines observed OP.GG statistics with explicitly labeled heuristic team composition. No LLM assigns points. Source: `backend/app/services/scoring.py`.

## Eligibility

The full bundled Riot roster is recognized. Candidates must be in the pool, have the requested role in their role map, and not already be picked by either team. Unknown names, duplicate picks, invalid roles, conflicting teams, invalid comfort, and lane opponents outside the enemy team are rejected. Up to 250 pool entries are accepted. Jungle has no lane-opponent field. Partial drafts and fewer than three eligible candidates are supported.

## Scoring

Each normalized factor is clamped to [0,1], multiplied by its weight and rounded to two decimals. Sum the contributions to produce a 0–100 fit score. Sort descending, then alphabetically on a tie. Scores are not win probabilities.

| Factor | Weight | Source / rule |
| --- | ---: | --- |
| Observed role performance | 10 | OP.GG role match win rate; neutral if missing, different/unknown patch, or under 100 games. |
| Lane matchup | 20 | OP.GG selected-champion head-to-head match outcome; neutral when missing/insufficient. Historical sample only when live statistics are explicitly disabled. |
| Comfort | 15 | User rating / 5; default 3 / 5. |
| Frontline | 8 | Heuristic team need; target 4. |
| Engage | 6 | Heuristic team need; target 4. |
| Carry protection | 6 | Heuristic team need; target 4. |
| Crowd control | 6 | Heuristic team need; target 5. |
| Scaling | 6 | Heuristic team need; target 7. |
| Damage balance | 8 | Equal-weight heuristic physical/magic mix. |
| Ally synergy | 6 | Curated pairs, not empirical synergy statistics. |
| Enemy threats | 9 | Explicit heuristic armor/peel/isolation interactions. |

Weights total **100** across eleven factors.

### Empirical factors

Require the provider's major/minor patch to match the bundled Data Dragon major/minor patch and at least 100 observations. The provider's trend patch is the response-level patch marker; individual row patch metadata is not exposed. Unknown/different-patch data is visible but excluded from scoring and build selection.

For a reported win rate `p` and sample `n`:

```text
posterior = (p*n + 0.5*200) / (n+200)
factor = clamp(0.5 + 5*(posterior-0.5))
```

The 200 neutral pseudo-games damp small samples. Ten percentage points above/below 50% spans the full factor range before clamping. This is an understandable MVP weighting choice, not a fitted predictive model. Confidence intervals and opponent-strength adjustment are not implemented. A missing factor gets 0.5 (neutral).

Both OP.GG counter collections use **my_win_rate** for the selected champion. A high opponent win rate in `weak_counters` must never become a bonus for the selected champion. The service returns selected counters, not every matchup. Missing pairs do not inherit an old sample rating while live mode is enabled.

### Heuristic factors

Traits are ordinal ratings from 0 to 3 for the original 38 reviewed sample profiles. Other champions have null/unreviewed traits, not zero. If the candidate or any ally lacks reviewed traits, corresponding team-need factors receive neutral credit. Unknown allied profiles are listed and no unfounded deficiency/damage split is displayed.

For known traits, `need = clamp((target-allied_total)/target)` and `factor = 0.5 + 0.5*need*candidate_trait/3`. Existing coverage receives neutral credit; filling a gap earns a bonus.

Damage balance is `1 - 2*abs(physical_share-0.5)`, with equal champion weighting including the candidate. Unknown profiles receive neutral credit. This ignores gold, time, itemization, true damage and actual damage contributions.

Synergy is `min(1,0.5+0.25*curated_pair_count)`, with symmetric pair lookup. Absence receives neutral credit. Enemy-threat credit starts at 0.5: +0.3 armor tag against >=60% physical profiles, +0.2*peel/3 against any dive tag, +0.15 isolation tag against a frontline-3 enemy. Unknown threat profiles receive neutral credit.

## Guides

Matching-patch OP.GG core combinations and rune pages with at least 100 observations replace historical guides. Missing guides remain explicitly labeled historical 14.24 samples for the original 38 champions; other missing guides are unavailable. Situational items and general game plans remain heuristic. The UI labels each guide independently, because one response may have a build but no rune page.

## Provider behavior

Four concurrent requests, 18-second aggregate budget, six-hour local cache. Expired cache entries trigger refetch; errors return neutral statistical credit and visible warnings. Responses are decoded without eval and validated for champion/role identity and valid probability/sample ranges. Statistics can move rankings; tests isolate that behavior from composition factors.

The optional explanation model receives scored facts and cannot change the ranking or builds. Provider metadata and exact factor contributions remain visible independently of prose.
