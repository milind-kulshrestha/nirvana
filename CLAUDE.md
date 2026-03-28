# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A native desktop stock watchlist tracker with live market data powered by OpenBB and conversational AI assistant powered by Claude.

**Tech Stack:**
- Backend: FastAPI + SQLAlchemy + SQLite/PostgreSQL
- Frontend: React + Vite + TailwindCSS + shadcn/ui
- Desktop: Tauri v2 (Rust + WebView) with Python sidecar
- Market Data: OpenBB SDK (FMP provider) + DuckDB cache
- AI Agent: Anthropic Claude SDK (claude-sonnet-4-5) with streaming tool use
- Background: APScheduler for market data refresh
- Auth: Single-user mode (desktop) or session-based (cloud)
- State: Zustand
- CI/CD: GitHub Actions with Tauri build action

**Current Status:** All phases complete (0-6). Desktop migration done. See [Desktop Migration Plan](docs/plans/2026-02-07-desktop-app-migration.md).

## Quick Start

### Desktop Mode (Recommended)
```bash
# Tauri auto-starts the Python backend sidecar
cd frontend && npx tauri dev

# Or start backend manually for development:
# Terminal 1: Backend
SINGLE_USER_MODE=true uvicorn app.main:app --port 6900
# Terminal 2: Frontend only
cd frontend && npm run dev
```

### Web Mode (Legacy - Still Supported)
```bash
# Start backend + database
docker-compose up -d
docker-compose exec backend alembic upgrade head

# Start frontend
cd frontend && npm install && npm run dev

# Access at http://localhost:5173
# API docs at http://localhost:8000/docs
```

## Common Commands

### Backend
**Desktop Mode:**
```bash
SINGLE_USER_MODE=true uvicorn app.main:app --port 6900  # Start with SQLite
# No Docker, no migrations, no auth required
```

**Cloud Mode (PostgreSQL):**
```bash
docker-compose up -d                        # Start services
docker-compose logs -f backend              # View logs
docker-compose restart backend              # Restart after changes
docker-compose exec backend pytest          # Run tests
docker-compose exec backend alembic upgrade head  # Run migrations
alembic revision --autogenerate -m "msg"    # Create migration
```

### Frontend & Desktop
```bash
cd frontend
npm run dev                                 # Vite dev server (web mode)
npx tauri dev                               # Tauri dev mode (desktop)
npx tauri build                             # Build .app/.dmg/.exe
npm run build                               # Production web build
npm run lint                                # Lint code
```

### Database
```bash
docker-compose exec db psql -U user -d watchlist  # Access PostgreSQL
```

## Documentation

Comprehensive documentation organized by category:

### 🚀 Getting Started
- **[Quick Start Guide](docs/getting-started/quick-start.md)** - Installation and setup
- **[Development Guide](docs/getting-started/development.md)** - Development workflow and debugging

### 📚 Guides  
- **[Authentication Guide](docs/guides/authentication.md)** - Session-based auth implementation
- **[Database Setup](docs/guides/database-setup.md)** - PostgreSQL configuration and migrations

### 📖 Reference Documentation
- **[Architecture](docs/reference/architecture/)** - System design and structure
  - [Backend Architecture](docs/reference/architecture/backend.md) - FastAPI structure, routes, models
  - [Frontend Architecture](docs/reference/architecture/frontend.md) - React components, state, routing
  - [Desktop Architecture](docs/reference/architecture/desktop.md) - Tauri shell, SQLite, sidecar
  - [Database Schema](docs/reference/architecture/database.md) - SQLite/PostgreSQL tables, relationships
  - [AI Agent Architecture](docs/reference/architecture/ai-agent.md) - Conversational AI system
- **[External APIs](docs/reference/external/)** - Third-party integrations
  - [OpenBB Reference](docs/reference/external/openbb.md) - Market data API usage and examples

### 📊 Project Management
- **[Project Status](docs/project/status.md)** - Current development progress
- **[Changelog](docs/project/changelog.md)** - Version history and updates

### 🤝 Contributing
- **[Code Style Guide](docs/contributing/code-style.md)** - Coding conventions and standards
- **[Testing Guidelines](docs/contributing/testing.md)** - Testing strategy and best practices
- **[Pull Request Process](docs/contributing/pull-requests.md)** - PR guidelines and review process

**Documentation Index:** [docs/README.md](docs/README.md)

## Key Architecture Notes

### Authentication Flow
**Desktop Mode (SINGLE_USER_MODE=true):**
- Auto-creates default user (`local@nirvana.app`) on startup
- `get_current_user` dependency injects default user automatically
- No session validation required

**Cloud Mode:**
- Session-based with HTTP-only cookies (itsdangerous)
- Backend: `app/lib/auth.py` handles bcrypt hashing and session tokens
- Frontend: `stores/authStore.js` manages auth state via Zustand
- Protected routes check session via `get_current_user` dependency

### Database
**Schema:**
```
User (1) ──────< (many) Watchlist (1) ──────< (many) WatchlistItem
User (1) ──────< (many) Conversation (1) ──────< (many) Message
User (1) ──────< (many) MemoryFact
User (1) ──────< (many) PendingAction
```
- CASCADE deletes throughout
- Market data cached separately in DuckDB

**Modes:**
- SQLite: `~/.nirvana/nirvana.db` (desktop mode, auto-created)
- DuckDB: `~/.nirvana/market_data.duckdb` (market data cache)
- PostgreSQL: Docker container (cloud mode, requires migrations)

### Market Data
- OpenBB SDK in `app/lib/openbb.py` (cache-first, graceful fallback)
- DuckDB cache in `app/lib/market_cache.py` (quotes 15min TTL, fundamentals 24h TTL)
- Background scheduler in `app/lib/scheduler.py` (APScheduler)
- Functions: `get_quote()`, `get_ma_200()`, `get_history()`, `get_ohlcv()`, `get_performance()`, `get_estimates()`, `get_insider_trading()`, `get_fundamentals()`, `get_earnings()`, `get_analyst_coverage()`
- Provider: FMP (Financial Modeling Prep) via OpenBB SDK or direct `_fmp_get()` helper
- Insider trades: SEC EDGAR Form 4 filings (FMP insider endpoints are restricted)
- API keys via `~/.nirvana/config.json` or env vars

#### FMP API Constraints (Current Plan)
- **Use `/stable/` endpoints only** — v3 (`/api/v3/`) returns 403 "Legacy Endpoint"
- **`limit` parameter capped at 5** for ratios, key-metrics, income-statement, analyst-estimates
- **Quarterly period restricted** for ratios and key-metrics (402) — annual only
- **Restricted endpoints (402/404):** `historical_eps`, `price_target`, `estimates.historical`, `earning-surprises`, `social-sentiments`, `insider-trading` (per-symbol)
- **Direct FMP calls preferred** over OpenBB wrappers for fundamental data — use `_fmp_get(path, params)` helper which reads API key from `config_manager`, handles 402/timeout errors
- **Config access:** Use `config_manager.get("fmp_api_key", "")` (not `get_config()`)

### Settings & Config
- `~/.nirvana/config.json` stores API keys and preferences
- Settings API: `GET/PUT /api/settings`, `GET /api/settings/status`
- First-run onboarding wizard detects missing keys

### Frontend Structure
- Pages: Login, Watchlists (list), WatchlistDetail, Settings
- Components: StockRow (live data), PriceChart (recharts)
- UI: shadcn/ui components in `components/ui/`
- Routing: React Router with ProtectedRoute wrapper

## Important Files

**Backend:**
- `backend/app/main.py` - FastAPI app, CORS, router registration, scheduler startup
- `backend/app/database.py` - SQLite/PostgreSQL connection with auto-fallback
- `backend/app/config.py` - Environment + config.json settings
- `backend/app/routes/` - API endpoints (auth, watchlists, securities, chat, skills, settings)
- `backend/app/models/` - SQLAlchemy models
- `backend/app/lib/auth.py` - Session management + single-user bypass
- `backend/app/lib/openbb.py` - Market data integration (cache-first)
- `backend/app/lib/market_cache.py` - DuckDB market data cache
- `backend/app/lib/scheduler.py` - Background data refresh (APScheduler)
- `backend/app/lib/config_manager.py` - ~/.nirvana/config.json manager
- `backend/app/lib/agent/` - AI agent system (harness, tools, skills, prompts)

**Frontend:**
- `frontend/src/App.jsx` - Router setup + startup health check + onboarding
- `frontend/src/stores/authStore.js` - Auth state
- `frontend/src/stores/aiChatStore.js` - AI chat state
- `frontend/src/pages/` - Page components (incl. Settings)
- `frontend/src/components/` - Reusable components (incl. StartupScreen, OnboardingWizard)

**Desktop (Tauri):**
- `frontend/src-tauri/src/lib.rs` - Sidecar lifecycle management
- `frontend/src-tauri/tauri.conf.json` - Window config, shell scope, updater
- `frontend/src-tauri/Cargo.toml` - Rust dependencies

**Sidecar:**
- `python-core/server.py` - Python backend sidecar wrapper

**Config & CI:**
- `docker-compose.yml` - Service configuration (cloud mode)
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node + Tauri dependencies
- `.github/workflows/release.yml` - CI/CD for macOS/Windows builds
