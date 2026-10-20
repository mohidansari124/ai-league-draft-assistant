# Draftwise — AI League Draft Assistant

A working CS4800 Software Engineering with AI MVP. Enter a League draft, choose a personal champion pool, and get up to three contextual recommendations with transparent scores, matchup notes, runes, item suggestions, and a game plan.

**React + TypeScript + Vite + Tailwind CSS frontend; Python + FastAPI backend; SQLite database.** Includes all 173 champions in Riot Data Dragon 16.21.1 and real OP.GG statistics through its official public MCP service. Works without API keys. No login or accounts.

## Run on Windows (PowerShell)

Install Python 3.12 and Node.js 24 LTS, then reopen PowerShell. The tested environment uses Python 3.12.14, Node 24.19.0, and pnpm 11.19.0. Git is needed to clone the repository.

```powershell
git clone https://github.com/mohidansari124/ai-league-draft-assistant.git
cd ai-league-draft-assistant
py -3.12 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt
npm.cmd install --global pnpm@11.19.0
cd frontend
pnpm.cmd install --frozen-lockfile
cd ..
./.venv/Scripts/python.exe scripts/dev.py
```

Open **http://127.0.0.1:5173**. API health: http://127.0.0.1:8000/api/health. Interactive API docs: http://127.0.0.1:8000/docs. Press **Ctrl+C** in the launcher terminal to stop both servers. No environment file is needed for the demo.

The private repository requires GitHub access. If Python is installed as `python` instead of the Windows `py` launcher, use `python -m venv .venv` with Python 3.12. Dependencies and browser testing binaries require internet for their initial installation; live OP.GG queries require internet. The roster and heuristic fallback work offline.

### Run frontend and backend separately

From the repository root, terminal 1:

```powershell
./.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Terminal 2, from the repository root:

```powershell
cd frontend
pnpm.cmd dev
```

Vite proxies `/api` to port 8000. Both servers bind to localhost. A Docker/EC2 deployment configuration is prepared; see [deployment](docs/DEPLOYMENT.md). No cloud deployment has been performed.

## Demonstration

The app starts with the personal ADC example. **Load example** loads the original top-lane demonstration:

- Role: Top
- Pool: Ornn, Garen, Malphite, Mordekaiser; comfort defaults to 3 / 5
- Allies: Jarvan IV, Orianna, Jinx, Lulu
- Enemies: Darius, Lee Sin, Zed, Samira, Nautilus
- Lane opponent: Darius

Click **Analyze draft**, inspect the three ranked picks, and open **Build & runes** and **Score breakdown**. Click a different recommendation to inspect its full guide. Return to the draft to change comfort, picks or role and compare. Changing role clears the draft and loads a starter pool for that role. Teams may be incomplete. The pool picker supports multiple selections; all pickers support search and Escape to close.

## Architecture

```text
frontend/
  src/App.tsx               Draft builder, picker, results UI
  src/api.ts                Typed API boundary and error handling
  src/types.ts              Frontend request/response types
  src/styles.css            Responsive dark interface + Tailwind
  public/portraits/         Bundled champion thumbnails
  tests/app.spec.ts         Real browser workflow checks
backend/
  app/main.py               FastAPI routes and CORS
  app/models.py             Validation and response models
  app/data/                 Curated champion profiles and sample guides
  app/services/catalog.py   Local game-data boundary
  app/services/scoring.py   Deterministic statistical/heuristic ranking
  app/services/opgg.py      Official OP.GG MCP adapter and 6-hour local cache
  app/services/explanations.py  Optional AI prose, safe fallback
  app/services/data_dragon.py   Riot static metadata adapter
  scripts/sync_data.py      Optional pinned metadata/portrait refresh
  tests/                    Scoring, validation, AI fallback tests
scripts/dev.py              Start/stop both local servers
docs/SCORING.md              Exact scoring formulas and limitations
```

Data → scoring → explanation are deliberately separate. A deterministic engine combines observed OP.GG statistics with labeled heuristic factors; an LLM never decides the rankings. Read [the scoring specification](docs/SCORING.md) for weights, sample assumptions, and replacement points.

## API

- `GET /api/health`: health and scoring version
- `GET /api/champions`: supported catalog and data provenance
- `POST /api/analyze`: structured recommendations and composition notes

Example request:

```json
{
  "role": "top",
  "championPool": ["Ornn", "Garen", "Malphite", "Mordekaiser"],
  "allies": ["Jarvan IV", "Orianna", "Jinx", "Lulu"],
  "enemies": ["Darius", "Lee Sin", "Zed", "Samira", "Nautilus"],
  "laneOpponent": "Darius",
  "comfort": {"Ornn": 3, "Garen": 3, "Malphite": 3, "Mordekaiser": 3}
}
```

Response contains `recommendations` (rank, score, factor contributions, explanation, matchup, runes, core items, situational items, game plan), `composition`, `warnings`, `excluded`, and model/data provenance. Bad drafts return 422 with a useful detail message. Already-picked and role-incompatible pool entries are excluded; no eligible entries is an error. Unknown matchups receive neutral credit and are labeled unrated.

## Tests and production build

From the repository root:

```powershell
cd backend
../.venv/Scripts/python.exe -m pytest -q
cd ../frontend
pnpm.cmd build
pnpm.cmd exec playwright install chromium
pnpm.cmd test:e2e
cd ..
```

Browser tests start the two servers automatically if needed. They cover the required example, results tabs, champion search, duplicate prevention, comfort selection, all roles, partial drafts, empty pools, failure recovery, keyboard modal behavior and 390px mobile layout. Screenshots go to `.test-artifacts/`, which is not committed. Playwright traces are retained for failing tests.

The build outputs `frontend/dist/`. Serving that static build in production still requires routing `/api` to FastAPI; the included Docker image serves it alongside FastAPI; cloud deployment is pending.

## Optional AI explanations

```powershell
Copy-Item .env.example .env
```

Edit the root `.env` locally:

```dotenv
EXPLANATION_PROVIDER=openai
OPENAI_API_KEY=your_local_key
OPENAI_MODEL=gpt-4.1-mini
```

Restart the backend. `EXPLANATION_PROVIDER=template` (the default) or an absent key keeps deterministic explanations. An explicitly enabled OpenAI provider sends scored champion facts to the Responses API; no account/player data is collected. API usage may incur charges. Timeout, transport failure or invalid output falls back to templates without changing scores. The API key is read only on the backend and `.env` is ignored by Git. Live paid inference is not required for any test.

## Real statistics and the full roster

**173 champions**, including the latest roster entries, are selectable across the draft. Riot Data Dragon **16.21.1** supplies names, titles, portraits and static item metadata. Observed OP.GG role shares determine the initial role map (at least 10% of that champion's observed games in the role); this is not a prohibition on creative off-meta picks. In the personal pool, the app currently filters by supported roles.

`STATS_PROVIDER=opgg` is the default. No OP.GG or Riot API key is required for the public MCP integration. Requests fetch statistics only for eligible pool champions. Results are cached locally under ignored `.cache/opgg/` for six hours, with a maximum of four concurrent requests and an 18-second overall statistics budget. No website HTML is scraped and no private website endpoints are used.

The result UI shows source, provider patch, role sample count, match win rate, retrieval time, cache state, and rank/region scope. The request asks for **ranked / all ranks**. The provider does not expose a region parameter; the app explicitly says **Provider default (not exposed)**. Reported win rates may be rounded by the provider.

Only statistics on the same major/minor patch as the bundled Riot roster, with at least **100 games**, influence scores. Small samples are shrunk toward 50%. OP.GG returns selected strong/weak counter matchups, **not every opponent pair**. A missing matchup receives neutral credit and is labeled unrated; its absence is not proof of an even matchup. These are match outcomes, not lane-win rates or a user's predicted win probability.

Observed core builds and rune pages replace old sample guides when available on the matching patch with at least 100 observations. Build-completion outcomes are affected by game length and gold and are not causal estimates. When missing, the 38 original historical guides remain clearly labeled **Historical sample guide (14.24)**. New champions without a verified guide show **Unavailable**, rather than invented items/runes.

The original 38 composition profiles remain **heuristic sample ratings**; other champions' frontline/engage/peel/etc. traits are unreviewed and receive neutral credit. Unknown allied traits do not count as zero strength. Situational-item and general game-plan advice remain heuristic. All 173 champions can be analyzed, but statistical and heuristic coverage are separate.

Disable external calls with `STATS_PROVIDER=disabled` in the root `.env`, then restart the backend. Provider failures fall back safely and display a warning. Expired cached data is not silently scored as current data.

### Refresh for a new patch or champion release

```powershell
./.venv/Scripts/python.exe backend/scripts/sync_data.py
```

The script fetches the latest published Data Dragon version, refreshes the entire roster and portraits, and refreshes observed role mappings through OP.GG when available. Existing reviewed profiles are preserved; new profiles are explicitly unrated. Restart the backend afterward. To pin a version, add `--version 16.21.1`. Refreshing metadata does not calibrate heuristic traits or update the historical fallback guides.

See [data-source research](docs/DATA_SOURCES.md) for OP.GG, U.GG and FOW findings, and [the scoring specification](docs/SCORING.md) for the exact formulas.

## Troubleshooting

- **Cannot reach API:** start the backend on port 8000; check `/api/health`; click Try again.
- **Port already in use:** stop the old dev terminal with Ctrl+C before launching a second copy.
- **PowerShell script policy:** use `npm.cmd` and `pnpm.cmd`; the Python environment does not need activation.
- **pnpm blocked esbuild:** the committed `pnpm-workspace.yaml` explicitly permits only esbuild's build script. Use the documented pnpm version.
- **OneDrive locks:** if your sync client locks dependency files, pause syncing for installation or clone to a normal local development folder.
- **No recommendations:** add an available champion supported in your role; a champion cannot be picked on both teams.

## Sources

- [Riot Data Dragon documentation](https://developer.riotgames.com/docs/lol#data-dragon)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [Tailwind with Vite](https://tailwindcss.com/docs/installation/using-vite)
- [OpenAI text generation / Responses API](https://developers.openai.com/api/docs/guides/text)

Draftwise is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.


### Personal ADC mode

The app starts with Draven, Twitch, Caitlyn and Ashe and an editable example lane. It compares all four eligible picks and includes a source-linked ADC matchup notebook for ten common ADC opponents, with extra threat notes for Nautilus and Lux. Other champions and roles remain available. `Load example` restores the original top-lane demo.

The notebook is a small reviewed mechanics library, separate from live OP.GG statistics. It does not supply matchup win rates, matchup-specific builds or rune substitutions. Each note links its evidence and shows its review date; unreviewed opponents are labeled. See [data sources](docs/DATA_SOURCES.md).


## Persistence, Onetricks evidence, and CI

Saved drafts persist in SQLite, including champion pool, comfort and empty team-role slots. Use **Saved drafts** in the builder to save, reload or delete. Drafts are scoped to an anonymous HttpOnly browser cookie. They survive server restarts; clearing cookies loses access. There are no cross-device accounts. By default the database is `.data/draftwise.sqlite3`, excluded from Git. Override `DATABASE_PATH` for a persistent cloud volume.

New APIs: `GET /api/drafts`, `POST /api/drafts` with `{name, draft}`, and `DELETE /api/drafts/{id}`. Saving rejects unknown champions and invalid drafts. Each browser can retain up to 50 drafts.

Onetricks evidence is stored in the same database and shown separately from OP.GG. Import the small reviewed research snapshot:

```powershell
./.venv/Scripts/python.exe backend/scripts/import_onetricks.py backend/app/data/onetricks_reviewed.json
```

This batch contains six matchup observations for the focused champions, reviewed from indexed public counter pages on October 20, 2026. Their source patch is unknown and some source crawls are older: these are **reference snapshots, not current live data**. It contains no matchup-specific builds. Direct HTTP access encountered a security checkpoint, and no scraper bypass is implemented. [Onetricks import format and limits](docs/ONETRICKS.md).

GitHub Actions runs backend tests, frontend format/build checks, browser flows and a container persistence smoke test on pushes/PRs. The Docker/EC2 configuration is prepared but **not deployed**. [Deployment instructions](docs/DEPLOYMENT.md).

### Champion toolkit coverage

The bundled Riot 16.21.1 snapshot includes passive and Q/W/E/R descriptions, classes, resource type and base stats for every one of the 173 champions. Each recommendation shows its kit alongside the selected lane opponent, with source links. These facts remain available offline and do not change the heuristic scoring. The build tab also links to champion-specific OP.GG and Onetricks research pages.

Empty statistics, matchup, rune, item and Onetricks panels are omitted. Existing observations keep their patch/sample/source disclosures; missing empirical inputs still receive neutral scoring, explained in Score breakdown. Full-roster kit coverage does not mean full-roster verified matchup or build coverage. `sync_data.py` now fetches complete kits before publishing a refreshed snapshot.
