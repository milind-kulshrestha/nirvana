# Project Status

**Last Updated:** 2026-03-28

## Current Status: Stock Detail Tabs Expansion Complete

Nirvana's stock detail panel now features 6 tabs of rich data: Chart, Fundamentals, Earnings, Analysts, Valuation, and Insiders. All tabs lazy-load on selection with 24h DuckDB caching.

### Latest Accomplishments (2026-03-28)
- ✅ **Fundamentals tab** — Company profile (description, sector, CEO, website) + 12-metric grid (market cap, P/E, EV/EBITDA, ROE, ROA, ROIC, etc.) from FMP profile + key-metrics
- ✅ **Earnings tab** — Quarterly EPS bar chart (5 quarters, color-coded) + forward analyst estimates table (3 years of revenue/EPS/EBITDA projections)
- ✅ **Analyst Coverage tab** — Consensus rating badge (color-coded), average price target with upside %, analyst activity stats, forward estimates with analyst counts
- ✅ **Valuation tab** — 5-year historical P/E, P/S, P/B, EV/EBITDA line charts from FMP annual ratios + key-metrics
- ✅ **`_fmp_get()` helper** — Direct FMP stable API calls with config-based API key, 402/timeout error handling; replaces OpenBB wrappers for fundamental data (more reliable results)
- ✅ **StockRow refactor** — Generic `fetchTabData` helper replaces per-tab fetch functions; TabsList wraps on mobile
- ✅ **Graceful degradation** — Endpoints return partial data for ETFs/symbols with missing metrics instead of 500 errors
- ✅ **Dead code cleanup** — Removed unused `StockAnalytics.jsx` and `PriceChart.jsx`

### Previous Accomplishments (2026-03-23)
- ✅ **Insider Trades in Stock Detail** — "Insiders" tab in StockRow expanded panel
  - Data sourced from SEC EDGAR Form 4 filings (free, no API key needed)
  - 3-month buy/sell summary + 20 most recent trades, cached 24h

### Previous Accomplishments (2026-03-19)
- ✅ **FMP MCP Integration** — Agent now optionally loads Financial Modeling Prep tools via MCP server
  - `fmp_mcp.py`: `FMPMCPManager` spawns `npx financial-modeling-prep-mcp-server`, maintains SSE connection
  - Tools injected into agent at startup; gracefully skipped if Node.js/API key unavailable
  - Default tool sets: analyst, news, statements, insider-trades, earnings, dcf
- ✅ **Chat Enhancements** — Markdown rendering + context window tracker in AISidebar
  - `react-markdown` replaces plain `whitespace-pre-wrap` text rendering
  - Circular SVG token tracker: used/max tokens, color-coded (indigo→amber→red), per-model context sizes
  - `tokenUsage` state in chatStore populated from `usage` field in SSE `done` events

### Previous Accomplishments (2026-03-16)
- ✅ **ETF Dashboard** — New `/etf` page with ~180 preset ETFs across 6 categories + extensible Custom group
  - `etf_engine.py`: yfinance fetch (asyncio.to_thread), ABC rating (EMA10>EMA20>SMA50), ATR%, ATRx, VARS (volatility-adjusted RS percentile), RRS sparkline data
  - `market_cache.py`: `etf_snapshot` + `etf_holdings` DuckDB tables; atomic snapshot replace (BEGIN/COMMIT/ROLLBACK); 24h holdings TTL
  - `etf_custom_symbol.py`: SQLAlchemy model for user's custom ETF list
  - `routes/etf.py`: GET /snapshot, POST /refresh (SSE with error handling + proxy headers), GET /holdings/{symbol}, GET/POST/DELETE /custom
  - `etfStore.js`: Zustand store with SSE stream reader, buffer accumulation for partial chunks, progress tracking
  - `ETFDashboard.jsx`: AbcBadge, BarCell heatmap, RsSparkline SVG, HoldingsPopover (click-outside, aria-labels), sortable ETFTable, category tabs, Custom symbol management

### Previous Accomplishments (2026-03-16)
- ✅ **Multi-LLM Support** — LiteLLM replaces hardcoded Anthropic SDK; users can select any of 8 models
  - `models.py`: registry of 8 models across Anthropic, OpenAI, Google, Groq
  - `tool_adapter.py`: Anthropic→OpenAI tool/message format converter
  - `harness.py` rewritten: `litellm.acompletion()` with streaming delta accumulation for tool calls
  - `model` param threaded: API request → `SendMessageRequest` → `stream_chat()` → `InvestmentAgent()`
  - `GET /api/settings/models` endpoint + provider key fields in settings API
  - Model selector dropdown in AISidebar; persisted to localStorage via chatStore
  - "Additional AI Providers" card in Settings for OpenAI, Google, Groq keys + default model

### Previous Accomplishments (2026-03-15)
- ✅ **Dexter Agent Loop** — Scratchpad-backed context management ported from Dexter TypeScript architecture
  - `scratchpad.py` (new): JSONL log, soft tool limits, Jaccard similarity dedup, context clearing
  - `build_iteration_prompt` rebuilds user turn each loop with accumulated tool results
  - `build_system_prompt` now includes rich `TOOL_PROSE` descriptions and skill injection
  - `heartbeat` tool: view/update `~/.nirvana/HEARTBEAT.md` monitoring checklist
  - `skill` tool: invoke registered skill workflows (deduplication via scratchpad)
  - Context overflow recovery: catches `BadRequestError`, retries with fewer tool results
  - New SSE events: `tool_limit`, `context_cleared`
- ✅ **OHLCV Candlestick Charts** - Replaced Recharts with TradingView Lightweight Charts (candlestick + volume)
- ✅ **Performance Tiles** - Multi-period return heatmap (1D through 1Y) in expanded panel
- ✅ **Analyst Estimates** - Consensus Buy/Hold/Sell badge with target price delta inline in StockRow
- ✅ **Market Discovery Page** - New `/discover` route with Most Active / Gainers / Losers tables
- ✅ **Calendar Widget** - Earnings & dividends calendar with watchlist filtering
- ✅ **Market API Routes** - `GET /api/market/movers` and `GET /api/market/calendar`
- ✅ **Navigation** - Cross-navigation between Watchlists and Discover pages
- ✅ **Phase 2: Python Sidecar** - Auto-start/stop backend from Tauri
  - Sidecar wrapper with readiness signal
  - Rust lifecycle management (spawn on launch, kill on exit)
  - Startup splash screen with health check polling
- ✅ **Phase 3: First-Run & Settings** - User-friendly configuration
  - Settings API with config.json persistence
  - Settings page with API key management and test buttons
  - First-run onboarding wizard
- ✅ **Phase 4: Local Data Pipeline** - Background caching
  - DuckDB market data cache with TTL
  - Cache-first OpenBB integration (graceful fallback)
  - APScheduler for quote refresh during market hours
- ✅ **Phase 5: Agent Enhancements** - New AI capabilities
  - Price monitor creation, report export, DuckDB SQL queries
  - Model upgraded to claude-sonnet-4-5
- ✅ **Phase 6: Distribution** - Build and release pipeline
  - GitHub Actions CI for macOS/Windows builds
  - Tauri auto-updater, landing page

### Project Features ✅
- ✅ User registration and login (optional in single-user mode)
- ✅ Create and manage multiple watchlists
- ✅ Add/remove stocks to watchlists
- ✅ Real-time stock quotes
- ✅ 200-day moving average indicators
- ✅ OHLCV candlestick charts (TradingView Lightweight Charts)
- ✅ Multi-period performance tiles (1D/1W/1M/3M/6M/YTD/1Y)
- ✅ Analyst consensus estimates (Buy/Hold/Sell badge)
- ✅ Responsive UI with shadcn/ui components
- ✅ Secure session-based authentication (or single-user bypass)
- ✅ **Database Flexibility**
  - ✅ SQLite for local desktop mode
  - ✅ PostgreSQL for multi-user/cloud mode
- ✅ **Desktop Application**
  - ✅ Native Tauri v2 shell (macOS/Windows)
  - ✅ Packaged .dmg installer
  - ✅ Auto-start Python sidecar
  - ✅ Startup splash screen
  - ✅ Auto-updater
- ✅ **Settings & Onboarding**
  - ✅ Settings page (API keys, data preferences)
  - ✅ First-run onboarding wizard
  - ✅ Config.json-based persistence
- ✅ **Market Data Caching**
  - ✅ DuckDB cache (quotes, daily prices, fundamentals)
  - ✅ Background scheduler (quote refresh, daily snapshots)
  - ✅ Cache-first API pattern with graceful fallback
- ✅ **Market Discovery & Calendar**
  - ✅ Market movers: Most Active, Top Gainers, Top Losers
  - ✅ Upcoming calendar: earnings and dividends
  - ✅ Watchlist-filtered and market-wide views
  - ✅ Discover page with integrated calendar sidebar
- ✅ **ETF Dashboard**
  - ✅ ~180 preset ETFs across 6 categories (Indices, S&P Style, Sectors, Industries, Countries)
  - ✅ Technical indicators: ABC Rating, ATR%, ATRx, VARS percentile rank
  - ✅ RS sparkline charts (inline SVG, 20 bars)
  - ✅ Holdings popover (top-10, lazy-loaded, 24h cache)
  - ✅ Manual refresh with SSE progress stream
  - ✅ User-extensible Custom ETF group
- ✅ **AI Agent Integration**
  - ✅ Conversational AI assistant (multi-provider via LiteLLM)
  - ✅ **Multi-LLM model selector** — 8 models across Anthropic, OpenAI, Google, Groq
  - ✅ Stock research and analysis tools
  - ✅ 5 pre-built investment skills
  - ✅ Streaming chat with SSE
  - ✅ Memory and personalization
  - ✅ Pending action approval workflow
  - ✅ Context-aware component integration
  - ✅ Price monitor creation
  - ✅ Report export to disk
  - ✅ DuckDB SQL queries from agent
  - ✅ Scratchpad-backed loop (Dexter architecture)
  - ✅ Soft tool limits with Jaccard similarity dedup
  - ✅ Context overflow recovery
  - ✅ `heartbeat` tool (HEARTBEAT.md monitoring checklist)
  - ✅ `skill` tool with deduplication
  - ✅ **FMP MCP server** — optional Node.js subprocess; injects analyst/news/DCF/filings tools
  - ✅ **Markdown rendering** in chat (react-markdown + tailwind typography)
  - ✅ **Context window tracker** — circular SVG token gauge per model

### Technical Stack
- **Backend**: FastAPI + SQLAlchemy + SQLite/PostgreSQL
- **Frontend**: React 19 + Vite + TailwindCSS + shadcn/ui
- **Desktop Shell**: Tauri v2 (Rust + WebView)
- **State**: Zustand for auth and AI chat management
- **Charts**: TradingView Lightweight Charts for candlestick + volume visualization
- **Market Data**: OpenBB SDK with FMP provider + DuckDB cache
- **Caching**: DuckDB for market data, APScheduler for background refresh
- **Auth**: Session cookies (or single-user bypass) with itsdangerous + bcrypt
- **AI**: LiteLLM (multi-provider) — Anthropic Claude, OpenAI GPT-4o, Google Gemini, Groq Llama
- **CI/CD**: GitHub Actions with Tauri build action

### Next Steps
1. **Install APScheduler** - `pip install apscheduler` in `.venv` (scheduler currently skipped with warning)
2. **Code signing** - Apple Developer ID + Windows signing cert
3. **Python bundling** - Embed Python runtime in app bundle for distribution
4. **API base URL** - Make frontend API URL configurable (currently hardcoded)
5. **Provider key validation** — Add "Test" buttons for OpenAI/Google/Groq keys in Settings (mirrors Anthropic pattern)

### Future Enhancements
1. MCP server support (OpenBB, file I/O, DuckDB)
2. Additional investment analysis skills
3. Chart pattern recognition
4. News sentiment analysis
5. Earnings transcript analysis

### Blockers
- Code signing certificates needed for distribution
- Python bundling script needs platform-specific implementation

---

## Milestone History

### Completed Milestones

#### Milestone 10: ETF Dashboard (Mar 16, 2026) ✅
- New `/etf` page: preset screener for ~180 ETFs across 6 categories + Custom group
- `etf_engine.py`: yfinance fetch (asyncio.to_thread), ABC/ATR/VARS computation, RRS sparkline data (20 floats, no matplotlib)
- `market_cache.py`: atomic DuckDB snapshot replace (BEGIN/COMMIT/ROLLBACK); 24h holdings TTL cache
- `routes/etf.py`: 6 endpoints; SSE refresh with error handling + `X-Accel-Buffering` proxy headers (matching chat.py)
- `ETFDashboard.jsx`: AbcBadge, BarCell heatmap, RsSparkline SVG, HoldingsPopover (click-outside, aria-labels), sortable ETFTable
- `etfStore.js`: SSE stream with buffer accumulation for partial chunks; reader cleanup in finally block
- `EtfCustomSymbol` SQLAlchemy model; nav links added to WatchlistsNew + Discover

#### Milestone 9: Multi-LLM Support via LiteLLM (Mar 16, 2026) ✅
- Replaced Anthropic SDK with LiteLLM — supports Anthropic, OpenAI, Google, Groq
- `models.py`: MODEL_REGISTRY with 8 models; `DEFAULT_MODEL`, `MEMORY_EXTRACTION_MODEL` constants
- `tool_adapter.py`: Anthropic→OpenAI format conversion (tools + messages)
- `harness.py` rewrite: `litellm.acompletion()`, streaming delta accumulation, per-provider API key injection
- `model` param threaded: `SendMessageRequest` → `stream_chat()` → `InvestmentAgent()`
- `GET /api/settings/models` + provider key fields in settings API + config
- Model selector in AISidebar (dropdown, localStorage-persisted); provider key inputs in Settings page
- 14 new tests (12 backend, 2 frontend); vitest + happy-dom test infrastructure added

#### Milestone 8: Dexter Agent Loop Port (Mar 15, 2026) ✅
- Scratchpad-backed context management (`scratchpad.py`) — JSONL per query, soft limits, Jaccard dedup
- Full `harness.py` loop rewrite: static context + rebuilt iteration prompt, context overflow recovery
- `prompts.py` rewrite: `TOOL_PROSE` dict (13 tools), `build_system_prompt`, `build_iteration_prompt`
- `skills.py`: `get_skills_for_prompt()`, `load_skill_content()` for system + user skills
- `tools.py`: `heartbeat` tool (HEARTBEAT.md), `skill` tool (SKILL.md content), `skill_manager` wired in
- New SSE event types: `tool_limit` (soft limit warning), `context_cleared`

#### Milestone 7: Dashboard Data Expansion (Feb 11, 2026) ✅
- OHLCV candlestick charts with TradingView Lightweight Charts (replacing Recharts)
- Multi-period performance tiles (heatmap-style 1D-1Y returns)
- Analyst consensus estimates badge (Buy/Hold/Sell + target price)
- Market Discovery page at `/discover` with movers tables + calendar sidebar
- Calendar widget with earnings/dividends tabs and watchlist filtering
- 5 new backend functions: get_ohlcv, get_performance, get_estimates, get_market_movers, get_calendar_events
- New `/api/market/movers` and `/api/market/calendar` endpoints
- Extended securities API with ohlcv, performance, estimates include options
- Cross-navigation between Watchlists and Discover pages

#### Milestone 6: Desktop App Migration - Phases 2-6 (Feb 8, 2026) ✅
- Python sidecar with auto-start/stop from Tauri (readiness signal, graceful shutdown)
- Startup splash screen with health check polling
- Settings API + config.json persistence (thread-safe ConfigManager)
- Settings page with API key management and first-run onboarding wizard
- DuckDB market data cache (daily_prices, quotes_cache, fundamentals)
- Cache-first OpenBB integration with graceful fallback
- Background scheduler (APScheduler) for quote refresh during market hours
- 3 new agent tools: create_monitor, export_report, query_market_data
- Agent model upgraded to claude-sonnet-4-5
- GitHub Actions CI for macOS/Windows builds
- Tauri auto-updater plugin
- Product landing page
- Distribution documentation

#### Milestone 5: Desktop App Migration - Phase 0 & 1 (Feb 7, 2026) ✅
- SQLite database support with automatic fallback
- SINGLE_USER_MODE for auth bypass (local desktop use)
- Auto-create tables on startup (no Alembic for SQLite)
- PostgreSQL support preserved for potential cloud mode
- Tauri v2 shell initialized with native window
- Successfully builds Nirvana.app + .dmg installer
- Shell plugin configured for future Python sidecar
- All existing functionality works in desktop window

#### Milestone 4: AI Agent Integration (Feb 7, 2026) ✅
- Complete AI agent system using Anthropic Claude SDK
- Database models for conversations, messages, memory, actions, skills
- Backend agent infrastructure with tool execution framework
- Chat service with SSE streaming support
- 5 pre-built investment analysis system skills
- Frontend AI sidebar with conversation history
- Context capture from stock components
- Pending action approval workflow
- Memory fact extraction for personalization

#### Milestone 3: CORS & Deployment Prep (Dec 27, 2025) ✅
- Fixed CORS preflight request handling
- Comprehensive CORS middleware configuration
- Ready for frontend-backend integration testing

#### Milestone 2: Frontend Development (Dec 27, 2025) ✅
- Complete React frontend with Vite
- Login/Register pages with tab interface
- Watchlist management interface
- Live stock data display with charts
- Zustand state management
- shadcn/ui component library
- Responsive design with TailwindCSS

#### Milestone 1: Backend API (Nov 29, 2025) ✅
- FastAPI backend with SQLAlchemy
- PostgreSQL database with Alembic migrations
- User authentication (register/login/logout)
- Watchlist CRUD operations
- Stock market data endpoints (quote, MA200, history)
- OpenBB SDK integration
- Docker Compose setup
- Comprehensive error handling