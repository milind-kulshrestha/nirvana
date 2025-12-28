# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack stock watchlist tracker with live market data powered by OpenBB.

**Tech Stack:**
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: React + Vite + TailwindCSS + shadcn/ui
- Market Data: OpenBB SDK (FMP provider)
- Auth: Session-based with signed cookies
- State: Zustand

## Quick Start

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
```bash
docker-compose up -d                        # Start services
docker-compose logs -f backend              # View logs
docker-compose restart backend              # Restart after changes
docker-compose exec backend pytest          # Run tests
docker-compose exec backend alembic upgrade head  # Run migrations
alembic revision --autogenerate -m "msg"    # Create migration
```

### Frontend
```bash
cd frontend
npm run dev                                 # Dev server
npm run build                               # Production build
npm run lint                                # Lint code
```

### Database
```bash
docker-compose exec db psql -U user -d watchlist  # Access PostgreSQL
```

## Documentation

Detailed architecture and development information:

- **[Backend Architecture](docs/backend-architecture.md)** - FastAPI structure, routes, models, OpenBB integration
- **[Frontend Architecture](docs/frontend-architecture.md)** - React structure, state management, routing, components
- **[Database](docs/database.md)** - PostgreSQL schema, relationships, migrations
- **[Development Guide](docs/development.md)** - Setup, workflows, debugging, troubleshooting
- **[OpenBB Reference](docs/openbb-reference.md)** - OpenBB Python library API reference, examples, technical indicators

## Key Architecture Notes

### Authentication Flow
- Session-based with HTTP-only cookies (itsdangerous)
- Backend: `app/lib/auth.py` handles bcrypt hashing and session tokens
- Frontend: `stores/authStore.js` manages auth state via Zustand
- Protected routes check session via `get_current_user` dependency

### Database Schema
```
User (1) ──────< (many) Watchlist (1) ──────< (many) WatchlistItem
```
- CASCADE deletes throughout
- No cached market data (fetched on-demand)

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
- `backend/app/routes/` - API endpoints (auth, watchlists, securities)
- `backend/app/models/` - SQLAlchemy models
- `backend/app/lib/auth.py` - Session management
- `backend/app/lib/openbb.py` - Market data integration

**Frontend:**
- `frontend/src/App.jsx` - Router setup
- `frontend/src/stores/authStore.js` - Auth state
- `frontend/src/pages/` - Page components
- `frontend/src/components/` - Reusable components

**Config:**
- `docker-compose.yml` - Service configuration
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node dependencies
