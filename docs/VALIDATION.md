# Full-roster and real-statistics validation

Verified on Windows with Python 3.12.14 and Node.js 24.19.0.

- **47 passing backend tests**: existing scoring/API checks plus all 173 champions, actual influence of statistical inputs on ranking, low-sample shrinkage, wrong/unknown patches, selected-champion counter perspective, safe compact-response parsing, identity aliases, cache hit/expiry, failures, and unreviewed trait neutrality.
- **6 passing browser scenarios**: original draft/results flows, all roles, partial drafts, pool/search/editing, failures, keyboard focus, mobile overflow, and adding champions outside the original sample roster.
- **Production build passes** with TypeScript and Vite.
- **Real provider smoke checks** succeeded for the four demonstration top champions, Kai'Sa, Nunu & Willump, Akali and Locke. These are real OP.GG responses, separate from mocked unit tests.
- A browser smoke check against the live-enabled local servers confirmed OP.GG mode, patch 16.18, real sample counts, observed core builds/runes for all three recommendations, no browser runtime errors, and no horizontal overflow at 390px.
- Desktop and mobile screenshots under ignored `.test-artifacts/` were visually reviewed.
- No paid AI inference was used. Explanations remain deterministic by default.

The source does not expose every matchup or a region filter. Composition traits remain heuristic, with unreviewed champions handled neutrally. See DATA_SOURCES.md and SCORING.md for precise scope.
