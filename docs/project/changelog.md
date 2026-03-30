# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

## [2026-03-29] - Agent-Native UI Redesign

### Added
- **AppShell layout** — New `layout/AppShell.jsx` with `LeftSidebar`, `RightRail`, `TopBar`, `ComposeBar` replacing the old floating sidebar pattern
- **Agent Hub** — New `/` home page (`AgentHub.jsx`) as the AI agent workspace with canvas and compose bar
- **Canvas system** — `canvas/CanvasBlock.jsx`, `CanvasStream.jsx`, `WelcomeState.jsx` + `canvasStore.js` for agent-generated artifact blocks
- **Chat rearchitecture** — `chat/ChatMessageList.jsx` in dedicated directory; compose bar moved to layout shell
- **Right rail panels** — `rightrail/RunSteps.jsx`, `SkillsPalette.jsx`, `SourcesPanel.jsx` for agent workflow visibility
- **Context chips** — `topbar/ContextChipPicker.jsx` + `ContextChips.jsx` for attaching watchlists/stocks/datasets to prompts; `attachedContexts` state in `aiContextStore.js`
- **Command palette** — `CommandPalette.jsx` with keyboard shortcut support (`useKeyboardShortcuts.js` hook)
- **Error boundary** — `ErrorBoundary.jsx` wraps page content in AppShell
- **Layout store** — `layoutStore.js` (Zustand) for panel visibility state
- **Design system overhaul** — Apple-inspired color palette (blue primary `#0071e3`, system red, success green, warning orange), SF system fonts, semantic CSS variables, `fade-in-up` animation, `success`/`warning` Tailwind color tokens

### Changed
- **App.jsx** — Split into `App` (startup/auth) + `AuthenticatedApp` (onboarding + AppShell); routes render inside `<Outlet>` within AppShell
- **Routing** — Login moved to `/login`; home `/` is now AgentHub; unauthenticated redirect targets `/login`
- **shadcn/ui components** — `badge.jsx`, `button.jsx`, `card.jsx`, `dialog.jsx`, `input.jsx`, `skeleton.jsx` updated with refined styling
- **Page restyling** — `Discover.jsx`, `ETFDashboard.jsx`, `Settings.jsx`, `WatchlistDetail.jsx`, `WatchlistsNew.jsx` simplified and restyled
- **Tailwind config** — System font stacks, transition durations/easings, `success`/`warning` color tokens, `fade-in-up` keyframes
- **index.css** — Full CSS variable overhaul for light and dark themes with semantic naming

### Removed
- **`AISidebar.jsx`** — Replaced by AppShell layout with canvas + compose bar
- **`AIToggleButton.jsx`** — No longer needed; agent is always accessible via AppShell
- **`App.css`** — Styles moved to index.css / Tailwind
- **`Login.jsx`** — Superseded by `LoginNew.jsx`
- **`Watchlists.jsx`** — Superseded by `WatchlistsNew.jsx`

## [2026-03-28] - Stock Detail Tabs Expansion

### Added
- **Fundamentals tab** — Company profile + 12-metric grid (market cap, P/E, EV/EBITDA, ROE, etc.)
  - `Fundamentals.jsx` (new): company description, sector/industry badges, CEO, website link, metrics grid
  - `get_fundamentals(symbol)` in `openbb.py`: FMP profile + key-metrics with 24h cache
  - `GET /api/securities/{symbol}/fundamentals` endpoint
- **Earnings tab** — Quarterly EPS bar chart + forward analyst estimates
  - `Earnings.jsx` (new): Recharts BarChart (green/red by sign) + forward estimates table
  - `get_earnings(symbol)` in `openbb.py`: FMP income-statement (quarterly, limit=5) + analyst-estimates (annual)
  - `GET /api/securities/{symbol}/earnings` endpoint
- **Analyst Coverage tab** — Consensus rating, price target summary, forward estimates
  - `AnalystCoverage.jsx` (new): consensus badge with color-coded rating, avg price target with upside %, analyst activity stats, forward estimates table
  - `get_analyst_coverage(symbol)` in `openbb.py`: combines consensus + price-target-summary + analyst-estimates
  - `GET /api/securities/{symbol}/analyst` endpoint
- **Valuation tab** — 5-year historical P/E, P/S, P/B, EV/EBITDA line charts
  - `ValuationChart.jsx` (rewritten): 4 stacked Recharts LineCharts with distinct colors, fiscal year X-axis
  - `get_valuation_history(symbol)` in `openbb.py`: FMP ratios + key-metrics (annual, limit=5) merged by date
  - `GET /api/securities/{symbol}/valuation` endpoint
- **`_fmp_get(path, params)`** helper in `openbb.py` — Direct FMP stable API calls with config-based API key, 402/timeout error handling

### Changed
- **`StockRow.jsx`** — Expanded panel now has 6 tabs (Chart, Fundamentals, Earnings, Analysts, Valuation, Insiders). Generic `fetchTabData` helper replaces per-tab fetch functions. TabsList wraps on mobile.
- **Backend endpoints** — `get_fundamentals()` and `get_valuation_history()` wrap FMP calls in try/except for graceful ETF/partial data handling

### Removed
- **`StockAnalytics.jsx`** — Dead code, never integrated into StockRow
- **`PriceChart.jsx`** — Only used by StockAnalytics, replaced by CandlestickChart

### Notes
- FMP plan caps `limit` parameter to 5 for ratios, key-metrics, income-statement, analyst-estimates
- FMP v3 endpoints are deprecated (403); all calls use `/stable/` endpoints via `_fmp_get()` or OpenBB SDK
- Quarterly ratios/key-metrics return 402 (premium only); annual data used for valuation charts

## [2026-03-23] - Insider Trades in Stock Detail

### Added
- **Insider Trades tab** in StockRow expanded panel (alongside Chart tab)
  - `InsiderTrades.jsx` (new): summary bar (buy/sell stacked bar + stats) + trade table
  - Tabbed interface via shadcn/ui Tabs: "Chart" (default) + "Insider Trades" (lazy-loaded)
- **`get_insider_trading(symbol)`** in `openbb.py` — fetches Form 4 insider trades from SEC EDGAR
  - Looks up company CIK from `sec.gov/files/company_tickers.json` (in-memory cache)
  - Fetches recent Form 4 filings from EDGAR submissions API
  - Parses Form 4 XML to extract buy (P) and sell (S) transactions
  - Filters out non-trade transactions (RSU vesting M, tax withholding F, gifts G)
  - Computes trade value from shares * price
  - Cached in DuckDB fundamentals table with 24h TTL
- **`GET /api/securities/{symbol}/insider-trades`** endpoint in `securities.py`
  - Returns 3-month buy/sell summary (counts + values + net) + up to 20 most recent trades
- **Design doc**: `docs/plans/2026-03-22-insider-trades-design.md`

### Changed
- **`StockRow.jsx`** — expanded panel now uses Tabs component instead of flat CandlestickChart
- **`openbb.py`** — added `httpx` and `xml.etree.ElementTree` imports for SEC EDGAR integration

### Notes
- Originally planned to use OpenBB/FMP for insider data, but FMP per-symbol insider trading endpoints require a paid plan (402 Restricted). Switched to SEC EDGAR Form 4 filings (free public data).

## [2026-03-19] - FMP MCP Integration + Chat Enhancements

### Added
- **`backend/app/lib/fmp_mcp.py`** (new) — FMP MCP server lifecycle manager
  - `FMPMCPManager` class: spawns `financial-modeling-prep-mcp-server` via `npx` on app startup
  - Maintains persistent SSE connection via `mcp.client.sse.sse_client`
  - `get_tools()` — returns FMP tools in Anthropic format (cached after first call)
  - `call_tool(name, args)` — executes FMP MCP tool, returns string result
  - `is_fmp_tool(name)` — routes dispatch in `tools.py`
  - Graceful degradation: if Node.js unavailable or API key missing, agent continues with built-in tools only
  - Default tool sets: `analyst, news, statements, insider-trades, earnings, dcf`
- **`react-markdown@10.1`** + **`@tailwindcss/typography@0.5`** dependencies
- **Markdown rendering** in AISidebar chat messages — replaces `whitespace-pre-wrap` plain text
- **Context window tracker** in AISidebar — circular SVG progress indicator with token counts
  - Shows used/max tokens; color-coded: indigo → amber → red at 50% / 80%
  - Breakdown: input tokens + output tokens
  - Per-model context windows: 200k (Claude), 128k (GPT-4o, Groq), 1M / 2M (Gemini)
- **`tokenUsage` state** in `chatStore.js` — populated from `usage` field in SSE `done` events

### Changed
- **`main.py`** — `start_fmp_mcp()` / `stop_fmp_mcp()` startup/shutdown lifecycle hooks
- **`harness.py`** — `fmp_tools = await fmp_mcp.get_tools()` merged with `TOOL_DEFINITIONS` on each agent run
- **`tools.py`** — routes `execute_tool()` to `fmp_mcp.call_tool()` when `fmp_mcp.is_fmp_tool(name)` is true
- **`tailwind.config.js`** — added `@tailwindcss/typography` plugin

## [2026-03-16] - ETF Dashboard

### Added
- **`backend/app/lib/etf_engine.py`** (new) — ETF data engine
  - `STOCK_GROUPS` — 6 preset categories: Indices, S&P Style, Sel Sectors, EW Sectors, Industries, Countries (~180 ETFs)
  - `LEVERAGED_ETFS` — 44 symbols mapped to long/short ETF lists
  - `calculate_abc_rating()` — EMA10 > EMA20 > SMA50 trend scoring
  - `calculate_atr()` / `calculate_rrs()` — volatility + relative strength vs SPY
  - `get_rrs_chart_data(n=20)` — returns 20-point float list; `np.isfinite()` guard for NaN/inf
  - `fetch_etf_row(symbol, group)` — synchronous yfinance fetch wrapped for asyncio
  - `fetch_etf_holdings_sync(symbol)` — top-10 holdings; `pd.isna(idx)` index guard
  - `stream_etf_refresh(custom_symbols)` — async generator yielding `progress/error/complete` SSE events
- **`backend/app/lib/market_cache.py`** — two new DuckDB tables:
  - `etf_snapshot` — wiped + rewritten atomically on each refresh (BEGIN/COMMIT/ROLLBACK)
  - `etf_holdings` — lazy, per-symbol, 24h TTL
  - `save_etf_snapshot()`, `get_etf_snapshot()`, `save_etf_holdings()`, `get_etf_holdings()`
- **`backend/app/models/etf_custom_symbol.py`** (new) — `EtfCustomSymbol` SQLAlchemy model (`symbol` PK, `added_at`)
- **`backend/app/routes/etf.py`** (new) — 6 endpoints:
  - `GET /api/etf/snapshot` — cached snapshot; fallback `{"groups": {}, "built_at": null}`
  - `POST /api/etf/refresh` — SSE stream with error handling + `X-Accel-Buffering: no` header
  - `GET /api/etf/holdings/{symbol}` — cache-first, lazy yfinance fetch on miss
  - `GET/POST/DELETE /api/etf/custom/{symbol}` — custom ETF CRUD (POST returns 409 on duplicate)
- **`frontend/src/stores/etfStore.js`** (new) — Zustand store
  - `fetchSnapshot()`, `fetchCustomSymbols()`, `startRefresh()`, `addCustomSymbol()`, `removeCustomSymbol()`
  - SSE reader with `TextDecoder({stream: true})` + buffer accumulation for partial chunks
  - `finally` block releases reader lock; resets stuck `refreshing` status
- **`frontend/src/pages/ETFDashboard.jsx`** (new) — full page component
  - `AbcBadge` — colored dot (blue=A, green=B, amber=C)
  - `BarCell` — heatmap cell with green/red background bar
  - `RsSparkline` — 20-bar inline SVG (guard: `data.length < 2`)
  - `HoldingsPopover` — lazy-loaded, click-outside to close, weight bars, aria-label/expanded
  - `ETFTable` — sortable 10-column table with leveraged ETF chips
  - Category tabs (GROUP_ORDER), progress bar, Custom symbol input, empty state, loading skeleton
  - Derived `effectiveGroup` for stale-tab guard (avoids setState-in-effect)
- **`yfinance>=0.2.40`** + **`scipy>=1.11.0`** added to `requirements.txt`

### Changed
- **`main.py`** — registers `etf_routes.router` at `/api/etf`
- **`models/__init__.py`** + **`database.py`** — `EtfCustomSymbol` added to model registry
- **`frontend/src/App.jsx`** — `/etf` protected route added
- **`frontend/src/pages/WatchlistsNew.jsx`** + **`Discover.jsx`** — ETF nav links added (BarChart2 icon)

### Tests Added
- `backend/tests/test_etf_cache.py` — 4 DuckDB cache function tests
- `backend/tests/test_etf_model.py` — 2 SQLAlchemy model tests
- `backend/tests/test_etf_engine.py` — 9 computation + fetch function tests
- `backend/tests/test_etf_routes.py` — 9 route tests (snapshot fallback, SSE, holdings, custom CRUD + 409/404)
- `frontend/src/stores/etfStore.test.js` — 3 Zustand store tests

## [2026-03-16] - Multi-LLM Support via LiteLLM

### Added
- **`backend/app/lib/agent/models.py`** (new) — Model registry with 8 supported models across 4 providers
  - Anthropic: Claude Sonnet 4.6, Claude Opus 4.6, Claude Haiku 4.5
  - OpenAI: GPT-4o, GPT-4o Mini
  - Google: Gemini 2.0 Flash, Gemini 1.5 Pro
  - Groq: Llama 3.3 70B
  - `DEFAULT_MODEL`, `MEMORY_EXTRACTION_MODEL`, `MODEL_IDS` constants
- **`backend/app/lib/agent/tool_adapter.py`** (new) — Anthropic→OpenAI format converter
  - `anthropic_tools_to_openai()` — converts `input_schema` to `parameters`, wraps in `{"type": "function"}`
  - `convert_messages_to_openai()` — prepends `{"role": "system"}` message from system prompt kwarg
- **`GET /api/settings/models`** — Returns model registry for frontend dropdowns (no `config_key` exposed)
- **`litellm>=1.40.0`** dependency added to `requirements.txt`
- **Model selector dropdown** in AISidebar header — disabled while streaming, fetches models on mount
- **"Additional AI Providers" card** in Settings page — OpenAI, Google, Groq key inputs + default model selector
- **`selectedModel` state** in `chatStore.js` — persisted to `localStorage` under key `nirvana_selected_model`
- New config keys: `openai_api_key`, `google_api_key`, `groq_api_key`, `default_model` in `DEFAULT_CONFIG` and `SECRET_KEYS`
- New `Settings` properties: `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `DEFAULT_MODEL`
- New `UpdateSettingsRequest` fields: `openai_api_key`, `google_api_key`, `groq_api_key`, `default_model`
- Vitest + happy-dom test infrastructure for frontend unit tests

### Changed
- **`harness.py`** — Full rewrite from Anthropic SDK to LiteLLM
  - `InvestmentAgent.__init__` accepts `model: str | None` parameter; validates against `MODEL_IDS`, falls back to `DEFAULT_MODEL`
  - Removed `self.client` (Anthropic SDK instance); replaced with `litellm.acompletion()` calls
  - New `_build_litellm_kwargs()` helper: converts messages + tools to OpenAI format, injects per-provider `api_key`
  - Streaming loop: accumulates tool call fragments by `delta.tool_calls[n].index` across chunks; parses args after `finish_reason="tool_calls"`
  - `extract_memory_facts()` uses `litellm.acompletion()` with `stream=False`; catches `Exception` instead of `anthropic.*`
  - Error handling: `litellm.ContextWindowExceededError` replaces `anthropic.BadRequestError`
- **`chat.py`** — `SendMessageRequest` gains `model: Optional[str] = None`; passed to `service.stream_chat()`
- **`chat_service.py`** — `stream_chat()` signature gains `model=None`; passed to `InvestmentAgent()`
- **`settings.py`** — `UpdateSettingsRequest` extended with provider keys and `default_model`
- **`chatStore.js`** — `sendMessage()` includes `model: get().selectedModel` in request body
- **`AISidebar.jsx`** — Fetches `/api/settings/models` on mount; renders `<select>` below header title row
- **`Settings.jsx`** — Loads/saves provider keys and `default_model`; new "Additional AI Providers" card

### Tests Added
- `backend/tests/test_config_multi_llm.py` — 3 tests for DEFAULT_CONFIG and SECRET_KEYS
- `backend/tests/test_tool_adapter.py` — 3 tests for format conversion functions
- `backend/tests/test_harness_litellm.py` — streaming token + done event test with mocked litellm
- `backend/tests/test_chat_model_routing.py` — model field on request schema + model threading to agent
- `backend/tests/test_settings_multi_llm.py` — UpdateSettingsRequest fields + /models endpoint
- `frontend/src/stores/chatStore.test.js` — selectedModel state and localStorage persistence

## [2026-03-15] - Dexter Agent Loop Port

### Added
- **`backend/app/lib/agent/scratchpad.py`** (new) — Append-only JSONL scratchpad for agent work
  - Writes `~/.nirvana/scratchpad/{timestamp}_{md5}.jsonl` per query
  - Tracks tool call counts and Jaccard similarity across queries for soft-limit warnings
  - `clear_oldest_tool_results(keep_count)` for in-memory context management (never modifies file)
  - `has_executed_skill(name)` for skill deduplication
  - `estimate_tokens(system, query)` for context threshold checks
- **`heartbeat` tool** — View/update `~/.nirvana/HEARTBEAT.md` periodic monitoring checklist
- **`skill` tool** — Invoke a registered skill workflow by name; returns SKILL.md content

### Changed
- **`harness.py`** — Full rewrite of `stream_response` loop to scratchpad-backed architecture
  - Static `context_messages` (prior turns) + rebuilt `current_prompt` per iteration
  - Context threshold management: clears oldest tool results when estimated tokens > 100,000
  - Hard overflow retry: catches `BadRequestError`, clears aggressively, retries up to 2 times
  - New SSE event types: `tool_limit` (soft limit warning), `context_cleared`
  - Constants: `CONTEXT_THRESHOLD=100_000`, `KEEP_TOOL_USES=5`, `OVERFLOW_KEEP_TOOL_USES=3`, `MAX_OVERFLOW_RETRIES=2`
  - `InvestmentAgent.__init__` now passes `skill_manager` to `ToolExecutor` and injects available skills into system prompt
- **`prompts.py`** — Full rewrite with Dexter-style architecture
  - `TOOL_PROSE` dict: rich 3–6 sentence descriptions for all 13 tools
  - `build_system_prompt(memory_facts, available_skills)` — structured sections (tools, policy, skills, heartbeat, memory, guidelines)
  - `build_iteration_prompt(query, tool_results, usage_status)` — rebuilds user turn each iteration with accumulated tool data
- **`skills.py`** — Added two new methods
  - `get_skills_for_prompt()` — returns system + user skill metadata for prompt injection (user overrides system on name collision)
  - `load_skill_content(name)` — loads full SKILL.md content (user DB first, then system files)
- **`tools.py`** — `ToolExecutor.__init__` now accepts `skill_manager` param; added `_handle_heartbeat`, `_handle_skill`

## [2026-02-11] - Dashboard Data Expansion

### Added
- **OHLCV Candlestick Charts** - Replaced Recharts line chart with TradingView Lightweight Charts
  - `CandlestickChart.jsx` component with candlestick + volume histogram overlay
  - `get_ohlcv()` backend function with DuckDB cache (1-year daily bars)
  - ResizeObserver for responsive chart sizing
  - TradingView attribution link
- **Multi-Period Performance Tiles** - Heatmap-style return badges in expanded panel
  - `PerformanceTiles.jsx` showing 1D/1W/1M/3M/6M/YTD/1Y returns
  - `get_performance()` backend function via OpenBB price.performance (15-min cache)
  - Color-coded: green shades for positive, red shades for negative
- **Analyst Estimates Badge** - Inline consensus pill in StockRow
  - `EstimatesBadge.jsx` showing Buy/Hold/Sell with target price delta
  - `get_estimates()` backend function via OpenBB estimates.consensus (24h cache)
- **Market Discovery Page** - New `/discover` route for market-wide browsing
  - Tabbed view: Most Active, Top Gainers, Top Losers
  - `get_market_movers()` backend function via OpenBB equity.discovery (15-min cache)
  - `GET /api/market/movers?category=active|gainers|losers` endpoint
  - Watchlist symbol highlighting with "WL" badge
  - Calendar sidebar integration
- **Calendar Widget** - Upcoming earnings and dividend events
  - `CalendarWidget.jsx` with Earnings/Dividends tabs
  - Watchlist-filtered view ("My Stocks") with toggle to "All"
  - `get_calendar_events()` backend function via OpenBB equity.calendar (1h cache)
  - `GET /api/market/calendar?type=earnings|dividends&days=30` endpoint
  - Countdown badges for events within 7 days
- **Navigation** - Watchlists <-> Discover cross-navigation in page headers

### Changed
- `StockRow.jsx` - Lazy-loads OHLCV, performance, and estimates on expand (separate API call)
- `securities.py` - Extended `?include=` parameter to support `ohlcv`, `performance`, `estimates`
- `market_cache.py` - Added `get_cached_quote_with_ttl()` for configurable TTL
- `main.py` - Registered new market router at `/api/market`

### Dependencies Added
- Frontend: `lightweight-charts` (TradingView Lightweight Charts, ~45KB)

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