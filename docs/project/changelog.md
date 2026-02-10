# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

## [2026-02-08] - Event Loop Blocking & UI Consistency Fix

### Fixed
- **ConfigManager deadlock** - `threading.Lock()` replaced with `threading.RLock()` in `config_manager.py`. The non-reentrant lock caused `/api/settings/status` to deadlock on first call, which blocked the onboarding check and made the app display a grey "Starting backend..." screen indefinitely.
- **Scheduler event loop blocking** - Switched `AsyncIOScheduler` to `BackgroundScheduler` in `scheduler.py`. The async scheduler shared uvicorn's event loop, causing API requests to hang when scheduler jobs ran. `BackgroundScheduler` runs jobs in a thread pool, keeping the event loop free.

### Changed
- **WatchlistDetail page** - Migrated from hardcoded Tailwind colors to shadcn/ui theme tokens and components:
  - Replaced `bg-gray-50/white`, `text-gray-*`, `bg-indigo-*` with `bg-background`, `bg-card`, `text-foreground`, `text-muted-foreground`, `text-primary`
  - Replaced HTML `<button>` elements with shadcn `<Button>` component
  - Replaced custom modal with shadcn `<Dialog>` component
  - Replaced raw `<input>` with shadcn `<Input>` and `<Label>`
- **ProtectedRoute loading state** - Updated to use `bg-background` and `text-muted-foreground` theme tokens
- **App layout** - Restructured to flex layout with AI sidebar integration

## [2026-02-08] - Desktop App Migration (Phases 2-6)

### Added
- **Phase 2: Python Sidecar** - Tauri auto-starts/stops Python backend
  - `python-core/server.py` sidecar wrapper with readiness signal (`NIRVANA_BACKEND_READY`)
  - Rust sidecar management in `lib.rs` (spawn on launch, kill on exit)
  - Shell plugin scope configuration for `python3` command
  - `tauri-plugin-process` for exit handling
  - Frontend startup splash screen with health check polling (500ms interval, 15s timeout)
- **Phase 3: First-Run & Settings** - User-friendly configuration
  - `GET/PUT /api/settings` routes with masked key display
  - `GET /api/settings/status` for first-run detection
  - `~/.nirvana/config.json` configuration manager (thread-safe, lazy-loaded)
  - Settings page with API Keys, Data, and About sections
  - First-run onboarding wizard (step-by-step API key setup with skip option)
  - shadcn/ui Switch component added
  - Settings accessible from navigation gear icon
- **Phase 4: Local Data Pipeline** - Background caching
  - DuckDB market data cache (`~/.nirvana/market_data.duckdb`)
  - Tables: `daily_prices`, `quotes_cache`, `fundamentals`
  - Cache layer with TTL (quotes: 15 min, fundamentals: 24 hours)
  - `openbb.py` now checks cache first, falls back to API (graceful degradation)
  - Background scheduler via APScheduler
    - Quote refresh every 15 min during market hours (Mon-Fri, 9:00 AM - 3:45 PM ET)
    - Daily snapshot at 6:00 PM ET for end-of-day prices
- **Phase 5: Agent Enhancements** - New AI capabilities
  - `create_monitor` tool - background price alerts stored in `~/.nirvana/monitors.json`
  - `export_report` tool - markdown reports saved to `~/.nirvana/exports/`
  - `query_market_data` tool - read-only SQL against DuckDB cache (SELECT only, 500 row cap)
  - Model updated to `claude-sonnet-4-5-20250929`
  - System prompt expanded with monitoring, reports, and data query sections
- **Phase 6: Distribution** - Build and release pipeline
  - GitHub Actions release workflow (`.github/workflows/release.yml`)
  - Build matrix: macOS + Windows, triggered on `v*` tags
  - Tauri auto-updater plugin (`tauri-plugin-updater`)
  - Python bundling helper script (`scripts/bundle-python.sh`)
  - Product landing page (`docs/landing/index.html`)
  - Distribution architecture documentation

### Changed
- `backend/app/config.py` - API keys now read from `config.json` as fallback (env vars still override)
- `backend/app/main.py` - Registers settings router, starts/stops scheduler and OpenBB config from config.json
- `frontend/src-tauri/src/lib.rs` - Complete rewrite with sidecar lifecycle management
- `frontend/src-tauri/tauri.conf.json` - Shell scope, updater plugin configuration
- `frontend/src-tauri/Cargo.toml` - Added tauri-plugin-process, tauri-plugin-updater
- `frontend/src/App.jsx` - Startup health check gate, settings route, onboarding overlay

### Dependencies Added
- Backend: `duckdb>=1.0.0`, `apscheduler>=3.10.0`
- Rust: `tauri-plugin-process`, `tauri-plugin-updater`

## [2026-02-07] - Desktop App Migration (Phase 0 & 1)

### Added
- **SQLite Database Support** - Dual-mode database configuration
  - Automatic SQLite fallback when `DATABASE_URL` not set
  - Default path: `sqlite:///~/.nirvana/nirvana.db`
  - Auto-create tables on startup (no Alembic for SQLite)
  - PostgreSQL support preserved for multi-user/cloud deployments
- **Single-User Mode** - Local desktop authentication bypass
  - `SINGLE_USER_MODE=true` env var
  - Auto-creates default local user on first run
  - Skips session cookie validation
  - Auth infrastructure preserved for future cloud mode
- **Tauri v2 Desktop Shell** - Native application wrapper
  - Initialized in `frontend/src-tauri/`
  - 1280x800 native window
  - Shell plugin configured for future Python sidecar
  - Successfully builds Nirvana.app + .dmg installer
  - Icons for macOS and Windows platforms
- **Dependencies**
  - Backend: `bcrypt` explicitly added (was transitive)
  - Backend: `psycopg2-binary` now optional (not needed for SQLite)
  - Frontend: `@tauri-apps/cli` and `@tauri-apps/api`
- **Documentation**
  - Desktop app migration plan in `docs/plans/2026-02-07-desktop-app-migration.md`
  - 6-phase roadmap from web to distributable desktop app

### Changed
- `backend/app/database.py` - Detect database type, auto-create SQLite tables
- `backend/app/config.py` - Add `SINGLE_USER_MODE` configuration
- `backend/app/routes/auth.py` - Inject default user in single-user mode
- `backend/app/main.py` - Skip Alembic in SQLite mode

### Technical Details
- Backend can now run standalone with `SINGLE_USER_MODE=true uvicorn app.main:app`
- No Docker, Postgres, or authentication required for local desktop use
- Tauri dev mode: `npx tauri dev` (starts Vite + native window)
- Production build: `npx tauri build` (creates .app + .dmg)
- All existing features (watchlists, AI agent, market data) work unchanged

## [2026-02-07] - AI Agent Integration

### Added
- **AI Agent System** - Complete conversational AI assistant for stock analysis
  - Database models: Conversation, Message, MemoryFact, PendingAction, Skill
  - Backend agent infrastructure using Anthropic SDK
  - Tool execution framework (stock quotes, watchlists, price history, symbol search)
  - Skill management system with filesystem and database integration
  - Memory fact extraction for personalized recommendations
  - Streaming chat harness with SSE support
- **Chat Service & API** - Backend service layer and REST/SSE endpoints
  - `/api/chat/*` - Conversation CRUD, streaming chat, action confirmation
  - `/api/skills/*` - Skill CRUD operations
  - SSE streaming for real-time AI responses
  - Action executor for watchlist operations requiring user approval
- **System Skills** - 5 pre-built investment analysis skills
  - `research-stock` - Comprehensive equity research methodology
  - `portfolio-review` - Watchlist health check and analysis
  - `compare-stocks` - Side-by-side stock comparison
  - `earnings-preview` - Pre-earnings analysis framework
  - `watchlist-scan` - Quick scan for opportunities and risks
- **Frontend AI Components**
  - `AISidebar` - Fixed right panel with chat interface, conversation history, tool indicators
  - `AIToggleButton` - Floating button to open/close AI sidebar
  - `SendToAIButton` - Context capture for AI-enabled components
  - `useAISerializable` - Hook for registering components as AI-sendable
- **Frontend State Management**
  - `aiChatStore` - Zustand store for chat state with SSE streaming
  - `aiComponentStore` - Component-to-AI context registry
- **Dependencies**
  - Backend: `anthropic` SDK for Claude API integration
  - Frontend: `html-to-image` for visual context capture
  - Environment: `ANTHROPIC_API_KEY` configuration

### Technical Details
- AI agent uses Claude via Anthropic SDK with streaming tool use
- Pending actions require explicit user approval via frontend
- Memory facts stored per user for personalized assistance
- Skills can be system-provided or user-defined (stored in database)
- Frontend components can register themselves for AI context capture
- SSE (Server-Sent Events) for real-time streaming responses
- Tool execution includes watchlist CRUD, quote fetching, symbol search, price history

## [2025-12-27] - CORS Configuration Fix

### Fixed
- Improved CORS configuration for preflight requests
- Added explicit OPTIONS method support
- Added `expose_headers` and `max_age` to CORS middleware

### Technical Details
- Updated `backend/app/main.py` with comprehensive CORS settings
- Ensures proper cross-origin authentication with credentials

## [2025-12-27] - Frontend and Documentation

### Added
- Complete React frontend with Vite and TailwindCSS
- shadcn/ui component library integration
- Login/Register page (LoginNew.jsx)
- Watchlists listing page (WatchlistsNew.jsx)
- Watchlist detail page with live stock data (WatchlistDetail.jsx)
- StockRow component for displaying live market data
- PriceChart component using Recharts for 6-month price history
- Zustand store for authentication state management
- Comprehensive project documentation in `docs/`
  - Backend Architecture reference
  - Frontend Architecture reference
  - Database schema reference
  - OpenBB API reference
  - Development guide
  - Project status tracking
  - Changelog
- CLAUDE.md for AI assistant context
- CORS configuration in FastAPI backend

### Technical Details
- Frontend runs on http://localhost:5173
- Backend API on http://localhost:8000
- Session-based authentication with HTTP-only cookies
- Live market data from OpenBB SDK
- Responsive design with TailwindCSS utilities
- Documentation structure in `docs/reference/` for technical references

## [2025-11-29] - Initial Backend (Week 1)

### Added
- FastAPI backend with SQLAlchemy ORM
- PostgreSQL database integration
- User authentication system
  - Session-based auth with signed cookies (itsdangerous)
  - Bcrypt password hashing
  - Login, register, logout endpoints
- Database models
  - User model with email and password
  - Watchlist model for user's watchlists
  - WatchlistItem model for stocks in watchlists
- Watchlist management endpoints
  - Create, list, delete watchlists
  - Add/remove stocks from watchlists
- Securities endpoint for market data
  - Real-time stock quotes
  - 200-day moving average
  - Historical price data
- OpenBB SDK integration
  - FMP (Financial Modeling Prep) provider
  - Quote, MA, and historical data fetching
  - Custom error handling
- Alembic database migrations
- Docker Compose setup
  - PostgreSQL service
  - Backend service with hot reload
- Environment-based configuration
- Input validation and error handling

### Technical Details
- PostgreSQL 15 with cascade deletes
- OpenBB Platform for market data
- Session tokens with 7-day expiration
- RESTful API design
- Automatic API docs at /docs endpoint