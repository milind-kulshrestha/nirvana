# Desktop Architecture

## Overview

Nirvana is transitioning from a web application to a native desktop application using Tauri v2. The desktop architecture wraps the existing React frontend in a native shell while maintaining the FastAPI backend.

## Tech Stack

- **Shell**: Tauri v2 (Rust + WebView)
- **Frontend**: React 19 + Vite (unchanged from web version)
- **Backend**: FastAPI + SQLite (runs as sidecar process)
- **Database**: SQLite for local desktop use
- **Auth**: Single-user mode (no authentication required)

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│              Nirvana.app                        │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │   Tauri Shell (Rust)                      │  │
│  │   - Window management                     │  │
│  │   - Process lifecycle                     │  │
│  │   - Sidecar orchestration (future)        │  │
│  └───────────────────────────────────────────┘  │
│                      │                          │
│  ┌───────────────────────────────────────────┐  │
│  │   WebView (React Frontend)                │  │
│  │   - UI components (shadcn/ui)             │  │
│  │   - State management (Zustand)            │  │
│  │   - API client                            │  │
│  └───────────────────────────────────────────┘  │
│                      │                          │
│                      ↓ HTTP                     │
│              localhost:6900                     │
└─────────────────────────────────────────────────┘
                       │
                       ↓
        ┌──────────────────────────┐
        │  Python Backend          │
        │  (Manual - Phase 1)      │
        │  (Sidecar - Phase 2+)    │
        │                          │
        │  FastAPI + SQLite        │
        │  ~/.nirvana/nirvana.db   │
        └──────────────────────────┘
```

## Migration Phases

### Phase 0: Prep ✅ COMPLETE
**Goal:** Make backend runnable with SQLite and without auth.

**Changes:**
- Added SQLite auto-fallback in `database.py`
- Added `SINGLE_USER_MODE` auth bypass
- Auto-create tables on startup (no Alembic for SQLite)
- Made `psycopg2-binary` optional

**Result:** Backend runs standalone with `SINGLE_USER_MODE=true uvicorn app.main:app`

### Phase 1: Tauri Shell ✅ COMPLETE
**Goal:** Wrap frontend in native window.

**Changes:**
- Initialized Tauri v2 in `frontend/src-tauri/`
- Configured 1280x800 window
- Added Tauri dependencies (`@tauri-apps/cli`, `@tauri-apps/api`)
- Successfully builds Nirvana.app + .dmg

**Dev Workflow:**
```bash
# Terminal 1: Backend (manual)
SINGLE_USER_MODE=true uvicorn app.main:app --port 6900

# Terminal 2: Tauri dev mode
cd frontend && npx tauri dev
```

**Result:** Native macOS window running React app. Backend still manual.

### Phase 2: Python Sidecar 🚧 NEXT
**Goal:** Auto-start/stop Python backend from Tauri.

**Planned Changes:**
- Create `python-core/server.py` wrapper
- Register sidecar in `tauri.conf.json`
- Spawn Python process on app launch
- Health-check backend before loading frontend
- Kill backend on app quit

**Result:** Double-click Nirvana.app → everything starts automatically.

### Phase 3: First-Run & Settings
**Goal:** User-friendly configuration without `.env` files.

**Planned Features:**
- Settings UI for API keys (Anthropic, FMP)
- First-run onboarding flow
- Config stored in `~/.nirvana/config.json`

### Phase 4: Local Data Pipeline
**Goal:** Background data refresh and caching.

**Planned Features:**
- DuckDB for market data caching
- Background scheduler for quote refresh
- Drastically reduced API calls

### Phase 5: Claude Agent SDK
**Goal:** Enhanced AI capabilities with MCP support.

**Planned Changes:**
- Replace hand-rolled agent harness with SDK
- MCP servers for OpenBB, file I/O, DuckDB

### Phase 6: Distribution
**Goal:** Signed, installable binaries.

**Planned Features:**
- Code signing (Apple Developer ID, Windows cert)
- Auto-updater
- GitHub Releases CI/CD
- Landing page

## Project Structure

```
nirvana/
├── frontend/
│   ├── src/                    # React app (unchanged)
│   ├── src-tauri/              # Tauri shell ✅
│   │   ├── src/
│   │   │   ├── main.rs         # Entry point
│   │   │   └── lib.rs          # Tauri commands
│   │   ├── icons/              # App icons
│   │   ├── Cargo.toml          # Rust dependencies
│   │   └── tauri.conf.json     # Tauri config
│   ├── package.json
│   └── vite.config.js
├── backend/                    # Python backend (modified for SQLite)
│   └── app/
│       ├── database.py         # ✅ SQLite auto-fallback
│       ├── config.py           # ✅ SINGLE_USER_MODE
│       └── routes/auth.py      # ✅ Local user injection
└── python-core/                # 🚧 Future sidecar wrapper
    └── server.py
```

## Configuration Files

### `frontend/src-tauri/tauri.conf.json`
```json
{
  "productName": "Nirvana",
  "identifier": "com.nirvana.app",
  "version": "0.1.0",
  "build": {
    "devUrl": "http://localhost:5173",
    "frontendDist": "../dist"
  },
  "app": {
    "windows": [
      {
        "title": "Nirvana",
        "width": 1280,
        "height": 800,
        "resizable": true,
        "fullscreen": false
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  },
  "plugins": {
    "shell": {
      "open": true
    }
  }
}
```

## Development Workflow

### Phase 1 (Current)

**Start Backend Manually:**
```bash
cd backend
SINGLE_USER_MODE=true uvicorn app.main:app --port 6900
```

**Start Tauri Dev Mode:**
```bash
cd frontend
npx tauri dev
```

- Tauri launches Vite dev server (http://localhost:5173)
- Opens native window with React app
- Hot reload works as usual
- Backend must be started separately

### Production Build

**Build Desktop App:**
```bash
cd frontend
npx tauri build
```

**Output:**
- macOS: `frontend/src-tauri/target/release/bundle/macos/Nirvana.app`
- macOS DMG: `frontend/src-tauri/target/release/bundle/dmg/Nirvana_0.1.0_x64.dmg`
- Windows: `frontend/src-tauri/target/release/bundle/msi/Nirvana_0.1.0_x64.msi`

## Database Location

**SQLite Mode:**
- Location: `~/.nirvana/nirvana.db`
- Auto-created on first run
- Contains all user data (watchlists, conversations, memory)

**PostgreSQL Mode (legacy):**
- Still supported via `DATABASE_URL` env var
- Requires Docker Compose
- Use for multi-user cloud deployments

## Authentication

**Single-User Mode (Desktop):**
- Default user: `local@nirvana.app`
- Auto-created on startup
- No login required
- All API calls use default user

**Multi-User Mode (Cloud):**
- Standard session-based auth
- Requires login/register
- Session cookies with 7-day expiry

## Key Differences from Web Version

| Aspect | Web Version | Desktop Version |
|--------|-------------|-----------------|
| **Database** | PostgreSQL (Docker) | SQLite (~/.nirvana/) |
| **Auth** | Session cookies | Single-user bypass |
| **Deployment** | Docker Compose | Native .app/.exe |
| **Updates** | Git pull + rebuild | Auto-updater (future) |
| **Backend Start** | `docker-compose up` | Auto-start sidecar (future) |
| **Frontend** | Browser tab | Native window |

## Benefits of Desktop Architecture

1. **No Docker Required** - Simpler setup for end users
2. **Offline-First** - Local SQLite database
3. **Native Experience** - OS-level window management
4. **Auto-Updates** - Seamless version upgrades (future)
5. **Background Tasks** - Persistent data refresh (future)
6. **Local MCP Servers** - Enhanced AI capabilities (future)

## Known Limitations (Phase 1)

- Backend must be started manually (no sidecar yet)
- No first-run setup UI (requires manual .env configuration)
- No background data refresh
- No auto-updates
- No code signing (apps appear as "unidentified developer")

These will be addressed in Phases 2-6.
