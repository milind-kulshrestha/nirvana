# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A desktop stock watchlist tracker with live market data powered by OpenBB and conversational AI assistant powered by Claude. Currently migrating from web app to native desktop application using Tauri.

**Tech Stack:**
- Backend: FastAPI + SQLAlchemy + SQLite/PostgreSQL
- Frontend: React + Vite + TailwindCSS + shadcn/ui
- Desktop: Tauri v2 (Rust + WebView)
- Market Data: OpenBB SDK (FMP provider)
- AI Agent: Anthropic Claude SDK with streaming tool use
- Auth: Single-user mode (desktop) or session-based (cloud)
- State: Zustand

**Current Status:** Phase 0 & 1 complete (SQLite + Tauri shell). See [Desktop Migration Plan](docs/plans/2026-02-07-desktop-app-migration.md).

## Quick Start

### Desktop Mode (Recommended - Phase 1)
```bash
# Terminal 1: Start backend (SQLite, no auth required)
cd backend
SINGLE_USER_MODE=true uvicorn app.main:app --port 6900

# Terminal 2: Start Tauri desktop app
cd frontend && npx tauri dev

# Backend will auto-start in Phase 2+
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
- No cached market data (fetched on-demand)

**Modes:**
- SQLite: `~/.nirvana/nirvana.db` (desktop mode, auto-created)
- PostgreSQL: Docker container (cloud mode, requires migrations)

### Market Data
- OpenBB SDK in `app/lib/openbb.py`
- Functions: `get_quote()`, `get_ma_200()`, `get_history()`
- Provider: FMP (Financial Modeling Prep)
- API key configured in docker-compose.yml

### Frontend Structure
- Pages: Login, Watchlists (list), WatchlistDetail
- Components: StockRow (live data), PriceChart (recharts)
- UI: shadcn/ui components in `components/ui/`
- Routing: React Router with ProtectedRoute wrapper

## Important Files

**Backend:**
- `backend/app/main.py` - FastAPI app, CORS, router registration
- `backend/app/database.py` - SQLite/PostgreSQL connection with auto-fallback
- `backend/app/config.py` - Environment config (SINGLE_USER_MODE)
- `backend/app/routes/` - API endpoints (auth, watchlists, securities, chat, skills)
- `backend/app/models/` - SQLAlchemy models
- `backend/app/lib/auth.py` - Session management + single-user bypass
- `backend/app/lib/openbb.py` - Market data integration
- `backend/app/agent/` - AI agent system (harness, tools, skills, prompts)

**Frontend:**
- `frontend/src/App.jsx` - Router setup
- `frontend/src/stores/authStore.js` - Auth state
- `frontend/src/stores/aiChatStore.js` - AI chat state
- `frontend/src/pages/` - Page components
- `frontend/src/components/` - Reusable components

**Desktop (Tauri):**
- `frontend/src-tauri/src/main.rs` - Tauri entry point
- `frontend/src-tauri/tauri.conf.json` - Window config, bundling
- `frontend/src-tauri/Cargo.toml` - Rust dependencies

**Config:**
- `docker-compose.yml` - Service configuration (cloud mode)
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node + Tauri dependencies
