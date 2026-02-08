# Nirvana Documentation

A full-stack stock watchlist tracker with live market data powered by OpenBB.

## Quick Navigation

### 🚀 Getting Started
- **[Quick Start](getting-started/quick-start.md)** - Get up and running in minutes
- **[Development Guide](getting-started/development.md)** - Development workflow and setup

### 📚 Guides
- **[Authentication](guides/authentication.md)** - Auth flow and session management
- **[Database Setup](guides/database-setup.md)** - Database configuration and migrations

### 📖 Reference
- **[Architecture](reference/architecture/)** - System architecture documentation
  - [Backend Architecture](reference/architecture/backend.md)
  - [Frontend Architecture](reference/architecture/frontend.md)
  - [Desktop Architecture](reference/architecture/desktop.md) - Tauri desktop app
  - [Database Schema](reference/architecture/database.md)
  - [AI Agent Architecture](reference/architecture/ai-agent.md) - Conversational AI system
- **[External APIs](reference/external/)** - Third-party integrations
  - [OpenBB Reference](reference/external/openbb.md)

### 📊 Project Management
- **[Project Status](project/status.md)** - Current development status
- **[Changelog](project/changelog.md)** - Version history and changes

### 🤝 Contributing
- **[Code Style](contributing/code-style.md)** - Coding conventions
- **[Testing](contributing/testing.md)** - Testing guidelines
- **[Pull Requests](contributing/pull-requests.md)** - PR process

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite/PostgreSQL
- **Frontend:** React + Vite + TailwindCSS + shadcn/ui
- **Desktop:** Tauri v2 (Rust + WebView)
- **Market Data:** OpenBB SDK (FMP provider)
- **AI Agent:** Anthropic Claude SDK with streaming tool use
- **Auth:** Session-based or single-user bypass
- **State:** Zustand

## Quick Start

### Desktop Mode (Recommended)
```bash
# Terminal 1: Start backend (SQLite, no auth)
cd backend
SINGLE_USER_MODE=true uvicorn app.main:app --port 6900

# Terminal 2: Start Tauri desktop app
cd frontend && npx tauri dev
```

### Web Mode (Legacy)
```bash
# Start backend + database
docker-compose up -d
docker-compose exec backend alembic upgrade head

# Start frontend
cd frontend && npm install && npm run dev

# Access at http://localhost:5173
# API docs at http://localhost:8000/docs
```

For detailed setup instructions, see [Quick Start Guide](getting-started/quick-start.md).
