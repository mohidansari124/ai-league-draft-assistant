# Data-source investigation — 2026-09-17

## Implemented: Riot Data Dragon

Official documentation: https://developer.riotgames.com/docs/lol#data-dragon

Refreshed 2026-10-20: the versions endpoint returned **16.21.1**. Its champion.json contains **173 champions**. All names, stable numeric/string IDs, titles and identification portraits are included. Per-champion endpoints also supply passive/Q/W/E/R descriptions, classes, resource type and base stats for all 173 champions. Descriptions are stripped of markup and rendered as plain React text. Item names/costs are retained as static metadata. Data Dragon does not supply match win rates, matchup performance or optimal builds.

## Implemented: OP.GG public MCP

Official repository and supported tools: https://github.com/opgginc/opgg-mcp

Endpoint: https://mcp-api.op.gg/mcp

The repository documents a Streamable HTTP interface and tools for champion analysis and lane metadata. Direct read-only calls succeeded without an API key. The application calls `lol_get_champion_analysis` with ranked, requested role, all tiers and an explicit field selection. The roster refresh uses `lol_list_lane_meta_champions` for observed role associations.

Observed response facts:

- Champion analysis reports role win rate/sample count, core item combination, rune page, selected strong/weak counters and a trends patch/update timestamp.
- Counter collections both expose `my_win_rate`; weak-counter `counter_win_rate` is the opponent's rate and must not be substituted.
- The response format can be compact declarative classes. A restricted AST decoder supports only objects, lists and scalar literals; it never evaluates executable provider text.
- Requests may canonicalize champion names (for example KAI_SA becomes KAISA). Identity checks normalize punctuation and accept the Riot identifier.
- There is no region filter in the published champion-analysis schema. Region is therefore unknown/provider-default, not labeled KR, NA or Global.
- Rate values can be rounded. Displays preserve the provider's reported rate rather than suggesting unavailable precision.
- Selected counters are not a complete matchup matrix. Missing data is not synthesized.
- Trend patch is the patch marker exposed with the champion-analysis response. The interface does not expose a separate patch for each row, or a parameter to choose the patch. That provenance limit is retained.

Only short-lived runtime responses are cached in ignored `.cache/opgg/`; raw statistical responses are not committed. Live errors do not break the demo. No third-party plugin or scraping service is required.

## Researched, not integrated: U.GG

Official FAQ: https://u.gg/faq

U.GG states that its statistics originate from Riot's API. I did not find a documented public statistics integration in the official material reviewed. This does not establish that no partnership API exists. The app does not reverse-engineer U.GG's private frontend endpoints or claim to use its data.

## Researched, not integrated: FOW.LOL

Site: https://www.fow.lol/

The public site provides champion analysis, but I did not find a documented third-party statistics API in the material reviewed. It remains a possible future provider if a supported interface becomes available. No FOW statistics are used or blended into the current results.

## Replacement boundary

Providers live in `backend/app/services/`. A future provider should expose validated champion identity, role, queue, patch, rank, region, sample counts, perspective-correct matchup rates, fetch time, source links and observed builds. Do not blend aggregates with different patch/region/rank scopes as though they were interchangeable.


## Focused ADC notebook — reviewed 2026-09-17

The default pool is Draven, Twitch, Caitlyn and Ashe. All 173 champions remain selectable. The focused pool shows up to four results; other pools retain the top-three behavior.

`backend/app/data/adc_advice.json` contains short editorial paraphrases of mechanics advice from the four Mobalytics champion guides and ten counter pages (Draven, Twitch, Caitlyn, Ashe, Jinx, Jhin, Ezreal, Kai'Sa, Vayne, Samira), plus enemy-threat notes for Nautilus and Lux. Each displayed note links its guide or counter page. URL pattern: `https://mobalytics.gg/lol/champions/{slug}/guide` or `/counters`; Kai'Sa uses `kaisa`.

The notebook combines the player's champion plan with opposing-champion notes. These are NOT 36 independently validated pair guides, and no win rates are extracted from these pages. They do not affect ranking. Threat notes trigger on enemy presence without guessing a support role. Unsupported opponents receive an explicit coverage notice. Advice is restricted to the four champions in ADC role.

Review date is our editorial retrieval date, not the publisher's update date or a claim that all advice is current-patch optimized. Mechanic summaries deliberately omit obsolete purchases present in some source prose. Build/rune data still comes from the existing OP.GG provider when sufficient and patch-matched, otherwise its labeled fallback. The new purchase-decision section is app-authored qualitative guidance; it does not prescribe opponent-specific rune pages or item orders.

There is no LoLalytics scraper, Reddit feed, or Onetricks ingestion in this implementation. Future sources need their own access and quality checks. This narrow library can be replaced or expanded independently of the statistics adapter.


## Onetricks evidence update — 2026-10-20

A SQLite-backed reviewed-observation import and UI are now implemented. Six dated public counter-page observations are included as an explicit import batch. Their patches are unknown; they do not influence ranking. Live fetching hit a security checkpoint, and no matchup-specific build/rune data was verified. See [Onetricks status](ONETRICKS.md) for source interpretation, format and remaining work. This supersedes the earlier statement that no Onetricks ingestion exists: reviewed JSON imports now work, live scraping does not.
