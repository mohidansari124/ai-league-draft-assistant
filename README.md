# Draftwise — AI League Draft Assistant

A working CS4800 Software Engineering with AI MVP. Enter a League draft, choose a personal champion pool, and get up to three contextual recommendations with transparent scores, matchup notes, runes, item suggestions, and a game plan.

**React + TypeScript + Vite + Tailwind CSS frontend; Python + FastAPI backend.** Works without API keys. No login or accounts.

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

The private repository requires GitHub access. If Python is installed as `python` instead of the Windows `py` launcher, use `python -m venv .venv` with Python 3.12. Dependencies and browser testing binaries require internet for their initial installation; normal template-mode use does not.

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

Vite proxies `/api` to port 8000. Both servers bind to localhost. No production deployment is configured.

## Demonstration

The app starts with the required example. **Load example** resets it at any time:

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
  app/services/scoring.py   Pure deterministic ranking
  app/services/explanations.py  Optional AI prose, safe fallback
  app/services/data_dragon.py   Riot static metadata adapter
  scripts/sync_data.py      Optional pinned metadata/portrait refresh
  tests/                    Scoring, validation, AI fallback tests
scripts/dev.py              Start/stop both local servers
docs/SCORING.md              Exact scoring formulas and limitations
```

Data → scoring → explanation are deliberately separate. Neither a live API nor an LLM decides the rankings. Read [the scoring specification](docs/SCORING.md) for weights, sample assumptions, and replacement points.

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

The build outputs `frontend/dist/`. Serving that static build in production still requires routing `/api` to FastAPI; a production host is intentionally out of scope.

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

## Sample data and assets

38 champions cover all five roles. Traits, five Darius matchups, synergies, runes and builds are **educational samples**, not current-patch recommendations or win-rate statistics. Riot Data Dragon **14.24.1** supplies historical champion names/titles/portraits and an item metadata snapshot; small identification portraits are bundled locally. No splash art, Riot logos or scraped recommendation data are used. Without portraits, cards fall back to initials.

To refresh the same pinned static snapshot (optional; internet required):

```powershell
./.venv/Scripts/python.exe backend/scripts/sync_data.py
```

Changing the adapter's version does not update the handwritten scoring model or guides. Review these separately before presenting the app as current. Draft fit scores are not win probabilities; play, coordination and patch changes matter.

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
