# Onetricks integration status

## Investigation — October 20, 2026

- https://www.onetricks.gg/faq explains that build data comes from high-elo champion specialists, not all players.
- https://www.onetricks.gg/champions/builds/Draven exposes matchup/role/region selectors. Some advanced filters are Pro. The readable public snapshot showed patch 16.20, while this app's bundled metadata remains 16.18.1. Do not infer the counter table's patch from the build page.
- Counter pages for Draven, Twitch, Caitlyn and Ashe expose opponent win rates and gold difference at 15 minutes. Those rows describe the opponent against the page's champion specialists. The app converts rate to `1-rate` and negates gold difference when `perspective=opponent`; it does not invent an adjusted delta or use these biased cohorts as all-rank performance.
- Direct requests for public pages and robots.txt returned HTTP 429 with a Vercel security checkpoint. No alternate-domain, fingerprint, cookie, private-endpoint or CAPTCHA bypass was attempted. No supported public API was verified. The public terms at https://www.onetricks.gg/terms are not an API license.

## Implemented

A validated operator-only JSON import writes observations transactionally to SQLite. Repeat imports of identical records are idempotent. The API selects only exact champion/opponent pairs in ADC role. The UI shows source, review time, original perspective, cohort, patch, sample and limitations. Imported evidence never changes numeric scoring. There is no public upload endpoint.

The included small reviewed snapshot contains six counter observations, not a full copied dataset. It was read via indexed public pages; notes preserve the reported crawl age. Unknown patch remains null. Review time is when we inspected the snapshot, not when its games were played. Every record links its source.

## Import format

Run `python backend/scripts/import_onetricks.py <file.json>` with the app environment/database path. Input is a JSON array. Generate the current formal schema with:

```sh
cd backend
python -c "import json; from app.services.onetricks import Observation; print(json.dumps(Observation.model_json_schema(), indent=2))"
```

Required: `champion`, `opponent`, `region`, `sourceUrl`, timezone-aware `observedAt`, `acquisition` (`reviewed public page` or `authorized export`), `notes`, and `perspective` (`champion` or `opponent`). Optional `patch` is major.minor or null. `role` is ADC only. `winRate` is a fraction in [0,1], paired with integer `games`; `goldDiff15` follows the same perspective. Extra fields are rejected. Only the four focused champions are supported as the selected champion.

Optional `build` has `items` (ordered names), integer `games`, and optional `runes` (`primary`, `secondary`, `keystone`, five minor `runes`, three `shards`). It requires champion perspective, a known patch, and a source URL in the form `https://www.onetricks.gg/champions/builds/Draven?matchup=Jhin&role=bot`. Record only the exact selected matchup; never insert the all-opponents build as a matchup build. Import is an operator attestation: validation checks consistency, not whether the source actually published the supplied values.

Builds with fewer than 100 observations, a patch different from bundled metadata, or a review older than seven days display as reference-only. Matching these checks still does not establish that an item order is optimal or the source is current. Every imported build stays separate from OP.GG overall builds.

## Remaining work

Obtain reliable source access or an authorized export, inspect actual matchup-filtered item/rune records, then import and verify them. No real Onetricks item/rune records were obtained in this session. Synthetic build records exist only in isolated tests. Contact route, if desired: support@onetricks.gg. No message has been sent.
