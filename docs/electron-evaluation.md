# Electron Framework Evaluation for Nirvana Desktop App

## Executive Summary

This document evaluates Electron as a framework for packaging Nirvana (a React + FastAPI stock watchlist tracker) as a desktop application. Electron is a viable option but comes with meaningful trade-offs. Alternative frameworks (Tauri, Neutralinojs) are also assessed.

---

## Current Architecture

| Layer     | Technology                         |
|-----------|------------------------------------|
| Frontend  | React 19 + Vite 7 + TailwindCSS   |
| Backend   | FastAPI + SQLAlchemy + PostgreSQL   |
| Data      | OpenBB SDK (FMP provider)          |
| Auth      | Session-based HTTP-only cookies    |
| State     | Zustand                            |
| Infra     | Docker Compose                     |

The frontend communicates with the backend via REST calls to `http://localhost:8000` with `credentials: 'include'`. The backend depends on a PostgreSQL database and the OpenBB Python SDK for market data.

---

## Electron Overview

Electron embeds Chromium and Node.js to render web apps as native desktop windows. It uses a **main process** (Node.js, manages windows/system APIs) and **renderer processes** (Chromium, runs the web UI).

### What Electron Would Provide

- Native window chrome, system tray, desktop notifications
- Auto-update mechanism (electron-updater)
- OS-level keyboard shortcuts and file system access
- Code signing and installers for Windows, macOS, Linux via electron-builder/electron-forge
- Access to Node.js APIs from the main process (spawn child processes, TCP sockets, etc.)

---

## Compatibility with Nirvana

### Frontend (High Compatibility)

The React + Vite frontend would run inside Electron's Chromium renderer with minimal changes:

- Vite's build output (`npm run build`) produces static HTML/JS/CSS that Electron can load directly
- shadcn/ui, Radix UI, Recharts, TailwindCSS all work in Electron without modification
- Zustand state management is framework-agnostic and works as-is

**Required changes:**
- Replace hardcoded `http://localhost:8000` API base URL with a configurable value (environment variable or Electron IPC)
- Add an Electron main process entry point (`main.js`) to create a `BrowserWindow` and load the built frontend

### Backend (Significant Complexity)

The backend is a Python service with heavy dependencies (FastAPI, SQLAlchemy, PostgreSQL, OpenBB). Packaging this inside Electron introduces the core architectural challenge:

**Option A: Bundle the Python backend inside Electron**
- Use `child_process.spawn()` from Electron's main process to start the FastAPI server
- Requires bundling a Python runtime (e.g., via PyInstaller or embedded Python)
- PostgreSQL would need to be replaced with SQLite or bundled separately
- OpenBB SDK + FMP provider must be packaged with all native dependencies
- Significantly increases app size (Python runtime alone ~30-80 MB, plus dependencies)
- Complex build pipeline per platform

**Option B: Keep the backend as a separate service**
- Electron app connects to a remote or locally-running backend
- Simpler Electron setup but defeats the purpose of a self-contained desktop app
- Still requires Docker or a hosted backend

**Option C: Move data-fetching logic to Node.js**
- Rewrite OpenBB/FMP calls as Node.js services in Electron's main process
- Replace SQLAlchemy/PostgreSQL with a local store (SQLite via better-sqlite3, or IndexedDB)
- Significant rewrite effort but produces the cleanest desktop architecture

---

## Trade-off Analysis

### Advantages of Electron

| Advantage               | Relevance to Nirvana                                              |
|-------------------------|-------------------------------------------------------------------|
| Mature ecosystem        | electron-builder, electron-forge, auto-updater are battle-tested  |
| Cross-platform          | Single codebase for Windows, macOS, Linux                         |
| Web tech reuse          | React frontend works with zero UI changes                         |
| Native OS integration   | System tray for price alerts, notifications, global shortcuts     |
| Large community         | Extensive documentation, Stack Overflow coverage, npm packages    |

### Disadvantages of Electron

| Disadvantage                  | Impact on Nirvana                                                       |
|-------------------------------|-------------------------------------------------------------------------|
| **Bundle size: 150-300+ MB**  | Chromium (~120 MB) + Node.js + Python runtime + dependencies            |
| **Memory usage: 200-500 MB**  | Chromium per-window overhead; a stock tracker shouldn't need this        |
| **Python bundling complexity** | OpenBB SDK has native deps; cross-platform PyInstaller builds are fragile|
| **PostgreSQL dependency**      | Must switch to SQLite or embed PostgreSQL — either requires migration work|
| **Security surface**           | Chromium + Node.js + Python = large attack surface for a finance app     |
| **Startup time**               | Cold start 3-5s+ with bundled Python backend                            |
| **Update size**                | Full Chromium in every update unless using delta updates                 |

---

## Alternatives Comparison

### Tauri (Rust-based, uses OS webview)

| Factor            | Electron                     | Tauri                              |
|-------------------|------------------------------|------------------------------------|
| Bundle size       | 150-300+ MB                  | 5-15 MB (uses system WebView)      |
| Memory            | 200-500 MB                   | 50-100 MB                          |
| Backend language  | Node.js (main process)       | Rust (can invoke Python via sidecar)|
| Maturity          | Very mature                  | Stable (v2 released)               |
| Auto-update       | Built-in                     | Built-in                           |
| OS integration    | Full                         | Full                               |
| Python bundling   | child_process.spawn          | Sidecar pattern (documented)       |
| Build complexity  | Medium                       | Medium (requires Rust toolchain)   |

Tauri's **sidecar** feature is designed for bundling external binaries (like a PyInstaller-packaged backend), making it a better architectural fit for Nirvana's Python backend.

### Neutralinojs

- Extremely lightweight (~5 MB), uses OS webview
- Limited ecosystem and community compared to Electron/Tauri
- No built-in sidecar or Python bundling support
- Less suitable for a production finance application

### Progressive Web App (PWA)

- Zero distribution overhead — works from the browser
- Service workers enable offline caching of the UI
- No native OS integration (system tray, global shortcuts)
- Still requires a hosted or local backend
- Simplest path if native features aren't essential

---

## Recommended Approach

### If native desktop features are required:

**Use Tauri over Electron.** Rationale:

1. **Smaller footprint** — A stock tracker running in the background should be lightweight. Tauri's 5-15 MB bundle and ~50 MB memory usage vs. Electron's 150+ MB bundle and 200+ MB memory is a meaningful difference.
2. **Sidecar support** — Tauri has first-class support for bundling external binaries. The FastAPI backend can be compiled with PyInstaller and shipped as a Tauri sidecar, with Tauri managing the process lifecycle.
3. **SQLite migration** — Either framework requires dropping PostgreSQL for local use. SQLAlchemy supports SQLite with minimal model changes (remove PostgreSQL-specific types, handle SQLite limitations).
4. **Security** — Financial applications benefit from Tauri's smaller attack surface (Rust core, no bundled Chromium).

### If native desktop features are not essential:

**Use a PWA.** Add a service worker and web manifest to the existing Vite build. This gives installability and offline UI caching with zero architectural changes.

---

## Migration Effort Estimate (Electron)

If Electron is chosen despite the trade-offs, here is the scope of work:

### Phase 1: Electron Shell (frontend only, connects to Docker backend)
- Add `electron-builder` and main process entry point
- Configure `BrowserWindow` to load Vite build output
- Make API base URL configurable
- Set up build scripts for dev and production

### Phase 2: Local Database
- Replace PostgreSQL with SQLite in SQLAlchemy config
- Create Alembic migration for SQLite compatibility
- Test all queries for SQLite dialect differences

### Phase 3: Bundled Backend
- Package FastAPI app with PyInstaller (per platform)
- Electron main process spawns Python subprocess on startup
- Health-check loop to wait for backend readiness
- Graceful shutdown on app close

### Phase 4: Distribution
- Code signing (macOS notarization, Windows Authenticode)
- Auto-update via electron-updater + GitHub Releases or S3
- Platform-specific installers (DMG, NSIS, AppImage)

---

## Conclusion

Electron **can** package Nirvana as a desktop app, but the Python backend dependency makes it an awkward fit. The core challenge is not Electron itself — it's bundling a Python + PostgreSQL backend into a desktop application. This complexity exists regardless of the desktop framework chosen.

**Recommendation:** If the goal is a standalone desktop app, evaluate Tauri with a PyInstaller sidecar first. If the goal is broader distribution without native features, a PWA is the lowest-effort path. Electron is best suited for projects where the entire stack is JavaScript/TypeScript.
