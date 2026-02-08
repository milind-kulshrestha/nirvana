# Nirvana Desktop App Migration Plan

> Migrate from web app to Tauri + Python sidecar desktop application.
> Each phase is independently shippable. Don't start the next phase until the current one works.

## Architecture

```
Nirvana.app
├── src-tauri/              # Rust shell (~10MB)
├── frontend/               # Existing React + shadcn/ui (reused as-is)
└── python-core/            # Python sidecar
    ├── server.py            # FastAPI (localhost only, no auth)
    ├── db.py                # SQLite via SQLAlchemy
    ├── data/                # OpenBB SDK integration
    ├── agent/               # Claude Agent SDK
    └── scheduler.py         # Background data refresh
```

---

## Phase 0: Prep — Decouple from Postgres & Auth (1-2 days)

**Goal:** Make the backend runnable with SQLite and without auth, so it works as a single-user local app.

### Tasks

1. **Add SQLite support to `database.py`**
   - Detect `DATABASE_URL` — if not set, default to `sqlite:///~/.nirvana/nirvana.db`
   - Remove `psycopg2-binary` as hard dependency (optional for Postgres mode)

2. **Make auth optional**
   - Add a `SINGLE_USER_MODE=true` env var
   - When enabled, skip session cookie checks — inject a default local user
   - Keep auth code intact for potential future web/cloud mode

3. **Replace Alembic with auto-create for SQLite**
   - On first run, `Base.metadata.create_all(engine)` for SQLite
   - Keep Alembic for Postgres path

4. **Test the backend runs standalone**
   ```bash
   SINGLE_USER_MODE=true uvicorn app.main:app --port 6900
   ```
   - Frontend at `localhost:5173` talks to `localhost:6900`
   - Everything works with SQLite, no Docker, no Postgres

### What you keep
- All existing models, routes, services, agent code — unchanged
- Frontend — unchanged (still talks to `/api/*`)

### What changes
- `database.py` — 10 lines added for SQLite fallback
- `auth.py` — 15 lines added for single-user bypass
- `main.py` — skip Alembic in SQLite mode

---

## Phase 1: Tauri Shell (1-2 days)

**Goal:** Wrap the existing frontend in Tauri. Python backend still runs separately.

### Tasks

1. **Install Tauri CLI**
   ```bash
   cargo install create-tauri-app
   npm install @tauri-apps/cli @tauri-apps/api
   ```

2. **Initialize Tauri in the project root**
   ```bash
   npx tauri init
   ```
   - Set `devUrl` to `http://localhost:5173` (Vite dev server)
   - Set `frontendDist` to `../frontend/dist` (production build)

3. **Configure `tauri.conf.json`**
   ```json
   {
     "app": {
       "title": "Nirvana",
       "width": 1280,
       "height": 800
     },
     "build": {
       "devUrl": "http://localhost:5173",
       "frontendDist": "../frontend/dist"
     }
   }
   ```

4. **Dev workflow**
   ```bash
   # Terminal 1: Python backend
   SINGLE_USER_MODE=true uvicorn app.main:app --port 6900

   # Terminal 2: Tauri dev (starts Vite + native window)
   npx tauri dev
   ```

### Result
- Native macOS/Windows window running your React app
- Backend still runs manually in a terminal
- No functionality changes — just a window instead of a browser tab

---

## Phase 2: Python Sidecar (2-3 days)

**Goal:** Tauri automatically starts/stops the Python backend.

### Tasks

1. **Create `python-core/server.py`** — thin wrapper around existing backend
   ```python
   """Nirvana local server — started by Tauri as a sidecar."""
   import uvicorn
   import sys
   import os

   # Point to existing backend code
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
   os.environ.setdefault('SINGLE_USER_MODE', 'true')
   os.environ.setdefault('DATABASE_URL', 'sqlite:///~/.nirvana/nirvana.db')

   if __name__ == '__main__':
       uvicorn.run('app.main:app', host='127.0.0.1', port=6900)
   ```

2. **Register sidecar in Tauri config**
   ```json
   {
     "plugins": {
       "shell": {
         "sidecar": {
           "python-core": {
             "command": "python3",
             "args": ["python-core/server.py"]
           }
         }
       }
     }
   }
   ```

3. **Start sidecar from Rust `main.rs`**
   - Spawn Python process on app launch
   - Kill it on app quit
   - Health-check `localhost:6900/docs` before loading frontend

4. **Frontend: wait for backend**
   - Add a simple "Starting Nirvana..." splash while sidecar boots (~2-3 seconds)

### Result
- Double-click Nirvana.app → Python starts automatically → app loads
- Close window → Python stops
- Single process from user's perspective

---

## Phase 3: First-Run & Settings (1-2 days)

**Goal:** User can configure API keys without touching `.env` files.

### Tasks

1. **Add settings route to backend**
   ```
   GET  /api/settings        → current config (keys masked)
   PUT  /api/settings        → update keys, save to ~/.nirvana/config.json
   ```

2. **Settings page in frontend**
   - API Keys section: Anthropic key, FMP key (with test buttons)
   - Data section: refresh interval, market hours
   - About section: version, links

3. **First-run detection**
   - If `~/.nirvana/config.json` doesn't exist → show onboarding
   - Step 1: "Enter your Anthropic API key" (with link to get one)
   - Step 2: "Enter your FMP API key" (with link)
   - Step 3: "You're ready"

4. **Backend reads keys from `~/.nirvana/config.json`** instead of env vars
   - Env vars still work as override (for dev)

### Result
- Clean first-run experience
- No `.env` files for end users
- Settings accessible from the app

---

## Phase 4: Local Data Pipeline (3-5 days)

**Goal:** Background data refresh + local caching. This is where desktop starts to shine.

### Tasks

1. **Add DuckDB for market data**
   ```
   pip install duckdb
   ```
   - SQLite stays for app state (watchlists, conversations, memory)
   - DuckDB for: `daily_prices`, `quotes_cache`, `fundamentals`

2. **Cache layer in `openbb.py`**
   - `get_quote()` → check DuckDB cache (< 15 min old?) → return cached or fetch
   - `get_history()` → check DuckDB → only fetch missing days → append
   - `get_ma_200()` → compute from cached `daily_prices` (no API call)

3. **Background scheduler**
   ```python
   # python-core/scheduler.py
   from apscheduler.schedulers.asyncio import AsyncIOScheduler

   scheduler = AsyncIOScheduler()

   @scheduler.scheduled_job('interval', minutes=15)
   async def refresh_quotes():
       """Refresh watchlist quotes during market hours."""
       ...

   @scheduler.scheduled_job('cron', hour=18)
   async def daily_snapshot():
       """End-of-day price snapshot."""
       ...
   ```

4. **Start scheduler alongside FastAPI**

### Result
- Quotes refresh automatically in the background
- Historical data accumulates locally over time
- MA200, charts load instantly from cache
- Dramatically fewer API calls

---

## Phase 5: Claude Agent SDK (3-5 days)

**Goal:** Replace hand-rolled agent harness with the Claude Agent SDK.

### Tasks

1. **Install SDK**
   ```
   pip install claude-agent-sdk  # or whatever the package name is at that point
   ```

2. **Migrate `harness.py` → SDK-based agent**
   - Replace the manual `while iteration < MAX_TOOL_ITERATIONS` loop
   - Register existing tools (`get_quote`, `get_watchlists`, etc.) as SDK tools
   - Keep streaming SSE to frontend

3. **Add MCP server support**
   - `openbb-mcp` — expose all OpenBB endpoints to the agent
   - Local file MCP — agent can read/write `~/.nirvana/exports/`
   - DuckDB MCP — agent can query market data directly

4. **Add new agent capabilities**
   - `create_monitor` tool — agent sets up background price alerts
   - `export_report` tool — agent generates and saves analysis to disk
   - `query_market_data` tool — agent runs SQL against DuckDB

5. **Keep `stream_chat` SSE contract identical** — frontend doesn't change

### Result
- More capable agent with less code
- MCP gives the agent access to OpenBB's full API surface
- Agent can create persistent monitors, export files, query local data

---

## Phase 6: Distribution (2-3 days)

**Goal:** Produce signed, installable binaries.

### Tasks

1. **Bundle Python with the app**
   - Use `python-build-standalone` for embedded Python
   - Pre-install deps into `python-core/site-packages/`
   - Test on clean machine (no Python installed)

2. **Code signing**
   - Apple Developer ID ($99/year) → sign + notarize
   - Windows code signing cert (~$200/year)

3. **GitHub Actions CI**
   ```yaml
   on:
     push:
       tags: ['v*']
   jobs:
     build:
       strategy:
         matrix:
           platform: [macos-latest, windows-latest]
       steps:
         - uses: tauri-apps/tauri-action@v0
   ```

4. **Auto-updater**
   - Tauri built-in updater checks GitHub Releases
   - User sees "Update available" dialog

5. **Landing page**
   - Simple page with download buttons per OS
   - Can be a GitHub Pages site initially

### Result
- Users download a `.dmg` or `.exe`, install, and run
- Updates delivered automatically

---

## What Gets Reused vs Rewritten

| Component | Reuse? | Notes |
|---|---|---|
| React frontend (pages, components, stores) | **100%** | Unchanged — still talks to `/api/*` |
| FastAPI routes (watchlists, securities, chat, skills) | **95%** | Remove auth dependency in single-user mode |
| SQLAlchemy models | **90%** | Swap Postgres types for SQLite-compatible |
| `openbb.py` | **80%** | Add caching layer on top |
| Agent tools (`tools.py`) | **100%** | Unchanged — register as SDK tools |
| Agent harness (`harness.py`) | **0%** | Replaced by Claude Agent SDK |
| Agent prompts (`prompts.py`) | **100%** | Reused in SDK agent |
| Auth (`auth.py`) | **0%** | Not needed in single-user desktop |
| Alembic migrations | **0%** | SQLite uses auto-create |
| Docker / docker-compose | **0%** | Not needed |

---

## Order of Operations

```
Phase 0 (prep)          ██░░░░░░░░  1-2 days   ← START HERE
Phase 1 (tauri shell)   ████░░░░░░  1-2 days
Phase 2 (sidecar)       ██████░░░░  2-3 days
Phase 3 (settings)      ████████░░  1-2 days
                        ─── MVP: usable desktop app ───
Phase 4 (data pipeline) ██████████  3-5 days
Phase 5 (agent SDK)     ██████████  3-5 days
Phase 6 (distribution)  ██████████  2-3 days
                        ─── v1.0: distributable product ───
```

**Total: ~15-22 days of focused work to go from current web app to distributable desktop app.**

Phases 0-3 get you a working desktop app with the same features you have today.
Phases 4-6 are where the desktop form factor starts paying dividends.
