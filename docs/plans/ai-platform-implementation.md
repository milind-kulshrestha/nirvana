# Nirvana: AI-Powered Investment Platform — Implementation Plan (Revised)

## Vision
Evolve the stock watchlist MVP into an AI-powered investment tracking and discovery platform for retail investors. AI agent powered by Anthropic Python SDK (provider-swappable) with tool access, streaming responses, and conversational investment research.

**Target:** MVP for 2-3 users (self + friends). Expansion deferred.

---

## What's Already Built (Phase 1 — COMPLETE)

The core AI agent foundation is fully implemented and deployed.

### Backend — Done
- **Models:** Conversation, Message, MemoryFact, PendingAction, Skill (all migrated via `e4889cd8305d`)
- **User model:** `ai_memory_enabled` field added
- **Agent harness** (`backend/app/lib/agent/harness.py`): Streaming tool loop, MAX_TOOL_ITERATIONS=10, Anthropic API
- **Agent tools** (`backend/app/lib/agent/tools.py`): 8 tools — get_quote, get_watchlists, get_watchlist_items, get_price_history, get_financial_ratios (placeholder), search_symbol, propose_action, get_user_memory
- **Agent prompts** (`backend/app/lib/agent/prompts.py`): System prompt with memory injection
- **Skills manager** (`backend/app/lib/agent/skills.py`): System + user skill discovery from filesystem
- **5 system skills** in `backend/data/system_skills/`: research-stock, compare-stocks, earnings-preview, portfolio-review, watchlist-scan
- **Chat service** (`backend/app/services/chat_service.py`): Streaming, conversation persistence, memory extraction
- **Action executor** (`backend/app/services/action_executor.py`): add_to_watchlist, remove_stock, create_alert (placeholder)
- **Chat routes** (`backend/app/routes/chat.py`): Full CRUD + SSE streaming + action confirm/reject
- **Skills routes** (`backend/app/routes/skills.py`): Full CRUD for user skills
- **Config:** ANTHROPIC_API_KEY in config.py + docker-compose.yml
- **Dependency:** `anthropic>=0.40.0` in requirements.txt

### Frontend — Done
- **AISidebar** (`frontend/src/components/AISidebar.jsx`): Messages, tool call indicators, pending action cards, conversation history, suggestions
- **AIToggleButton** (`frontend/src/components/AIToggleButton.jsx`): Floating toggle
- **SendToAIButton** (`frontend/src/components/SendToAIButton.jsx`): Captures component context via aiContextStore
- **chatStore** (`frontend/src/stores/chatStore.js`): Full SSE parsing (token, tool_call, tool_result, action_proposed, done, error)
- **aiContextStore** (`frontend/src/stores/aiContextStore.js`): Component registry + screenshot capture
- **useAISerializable** hook (`frontend/src/hooks/useAISerializable.js`)
- **StockRow** + **PriceChart**: Both have `useAISerializable` + `SendToAIButton`
- **App.jsx**: AIOverlay (AISidebar + AIToggleButton) for logged-in users
- **Dependency:** `html-to-image: ^1.11.0` in package.json

### Architecture Decisions (Locked In)
- **Direct Anthropic API** (not Claude Agent SDK) — multi-user web service, sandboxed tools, full streaming control, provider-swappable
- **SSE for streaming** — unidirectional, works with FastAPI StreamingResponse
- **Propose + Confirm pattern** — PendingAction model, user approves before execution
- **Component-to-AI** — useAISerializable hook + structured data serialization

---

## Deferred Features (Removed from MVP)

These exist in code but are **not priorities** — will be revisited later:

| Feature | Status | Notes |
|---------|--------|-------|
| **Memory extraction** | Code exists (harness.py `extract_memory_facts`) | Underspecified — no dedup, no confidence logic. Leave code in place but don't invest further. |
| **User skill CRUD** | Code exists (Skill model, skills routes) | No user-created skills for MVP. Keep system skills only. Routes can stay but no frontend UI needed. |
| **Screenshot capture** | Code exists (aiContextStore `html-to-image`) | Structured data is sufficient. Skip screenshot sending for now. |
| **Skill editor/library pages** | Not built | Removed from plan entirely. |

---

## Phase 2: Hardening & Context Management (NEXT)

### Goal
Make the existing AI chat production-ready: token management, rate limiting, Redis for caching, and skill picker UI.

### 2.1 Token Counting & Auto-Summarization

**Problem:** Current `chat_service.py` replays last 20 messages naively. A single research-stock skill run can consume 10+ messages with tool calls. Two of those = blown context window.

**Solution:** Token-aware context management with auto-summarization at 80% capacity.

**`backend/app/lib/agent/context_manager.py`** (new)
```python
class ContextManager:
    """Token-aware conversation context management."""

    MODEL_CONTEXT_LIMIT = 200_000  # Claude Sonnet 4
    SUMMARIZATION_THRESHOLD = 0.8  # 80% = 160k tokens
    RESERVED_FOR_RESPONSE = 4_096  # max_tokens setting

    def prepare_messages(self, conversation_id: int, system_prompt: str) -> list[dict]:
        """Build message list that fits within context window.

        1. Count tokens for system prompt + all messages
        2. If under threshold, return all messages
        3. If over threshold, summarize older messages and prepend summary
        """

    def _count_tokens(self, messages: list[dict], system: str) -> int:
        """Count tokens using anthropic.count_tokens() or tiktoken estimate."""

    async def _summarize_messages(self, messages: list[dict]) -> str:
        """Summarize older messages using a cheap model (Haiku).
        Returns a concise summary preserving key facts, decisions, and data points."""
```

**Modify `backend/app/services/chat_service.py`:**
- Replace `MAX_CONTEXT_MESSAGES = 20` with `ContextManager.prepare_messages()`
- ContextManager decides how many messages to include based on token count
- When over 80% threshold: summarize oldest messages into a single "summary" message, keep recent messages verbatim

**Token counting approach:**
- Use `anthropic` SDK's token counting if available, else estimate at ~4 chars/token
- Count system prompt + all message content + tool definitions
- Budget: `MODEL_CONTEXT_LIMIT - RESERVED_FOR_RESPONSE - system_prompt_tokens - tool_definition_tokens`

### 2.2 Rate Limiting + Redis

**Add Redis to `docker-compose.yml`:**
```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 5s
    retries: 5
```

**`backend/app/lib/rate_limiter.py`** (new)
```python
class RateLimiter:
    """Per-user rate limiting using Redis INCR + EXPIRE."""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def check_rate_limit(self, user_id: int, limit: int = 30, window: int = 60) -> bool:
        """Returns True if request is allowed. 30 requests/minute default."""
```

**Apply to `/api/chat/send`** as a FastAPI dependency.

**`backend/requirements.txt`** — add: `redis>=5.0.0`

**`backend/app/config.py`** — add: `REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")`

### 2.3 Skill Picker in Sidebar

**Modify `frontend/src/components/AISidebar.jsx`:**
- Add skill chip list above the input bar
- Fetch available skills from `GET /api/skills` (system skills only)
- Click a skill chip → prefill input with skill invocation (e.g., "Research AAPL")
- Visual indicator when a skill is active

**Modify `backend/app/services/chat_service.py`:**
- Detect skill invocation in user message (e.g., starts with `/research-stock` or matches skill description)
- If skill detected, prepend skill markdown content to system prompt for this request
- Emit `{"type": "skill_invoked", "skill_name": "..."}` SSE event

### 2.4 Error Handling for Data Source Failures

**Modify `backend/app/lib/agent/tools.py`:**
- All OpenBB tool handlers already catch `SymbolNotFoundError` and `OpenBBTimeoutError`
- Add retry logic (1 retry with 2s delay) for transient failures
- Return structured error messages the agent can reason about (e.g., "OpenBB is temporarily unavailable, try again in a moment")

### 2.5 Files to Create/Modify

**Create:**
- `backend/app/lib/agent/context_manager.py`
- `backend/app/lib/rate_limiter.py`

**Modify:**
- `backend/app/services/chat_service.py` — use ContextManager, skill injection
- `backend/app/lib/agent/tools.py` — retry logic
- `backend/app/config.py` — REDIS_URL
- `docker-compose.yml` — add redis service, REDIS_URL env var
- `backend/requirements.txt` — add redis
- `frontend/src/components/AISidebar.jsx` — skill picker chips

### 2.6 Verification
1. Start long conversation (10+ tool-heavy messages) → verify context doesn't blow up, older messages get summarized
2. Send 31 messages in 60 seconds → verify rate limit kicks in
3. Click skill chip in sidebar → verify skill content injected into system prompt
4. Kill OpenBB container → verify agent returns graceful error message

---

## Phase 3: Expandable Stock Analytics + Valuation Metrics

### Goal
Richer stock data UI with expandable rows, valuation charts, and AI-sendable analytics.

### 3.1 Backend

**`backend/app/lib/openbb_fundamentals.py`** (new)
- `get_financial_ratios(symbol, period="quarterly", limit=12)` — P/E, P/B, P/S via `obb.equity.fundamental.ratios()`
- `get_historical_valuation_metrics(symbol, months=6)` — historical P/E, EV/EBITDA

**`backend/app/routes/securities.py`** (modify)
- Add `GET /{symbol}/ratios?period=quarterly&limit=12`
- Extend `GET /{symbol}?include=valuation_history`

### 3.2 Frontend

**`frontend/src/components/StockAnalytics.jsx`** (new)
- Mounts when stock row expanded
- Parallel fetch: price history + ratios
- Tabs: "Price History" | "Valuation Metrics"
- Caches data — tab switching doesn't re-fetch
- `useAISerializable` — serializes all analytics data

**`frontend/src/components/ValuationChart.jsx`** (new)
- Three stacked LineCharts (P/E, P/B, P/S), each 200px, black lines
- `useAISerializable` + `SendToAIButton` overlay

**Modify `frontend/src/components/StockRow.jsx`:**
- Add `expanded` state + chevron toggle
- Render `<StockAnalytics>` below when expanded
- Remove `onSelect` prop

**Modify `frontend/src/pages/WatchlistDetail.jsx`:**
- Remove right panel grid layout (right panel = AISidebar now)
- Remove `selectedStock` state
- Full-width stock list

### 3.3 Agent Tool Updates
- Implement `get_financial_ratios` tool handler (currently placeholder)
- Use new `openbb_fundamentals.py`

### 3.4 Verification
1. Expand stock row → tabs render with Price History + Valuation Metrics
2. Click SendToAI on ValuationChart → agent receives ratio data
3. Stock with missing fundamentals → graceful degradation

---

## Phase 4: Data Pipeline & Caching

### Goal
Multi-source data with Redis caching. News feed. Enriches AI agent context.

### 4.1 Redis Cache Service

**`backend/app/services/cache_service.py`** (new)
- Redis-backed (already available from Phase 2)
- TTL: quotes=60s, ratios=3600s, news=300s, history=3600s
- get/set/invalidate

### 4.2 Data Source Abstraction

**`backend/app/lib/data_sources/`** package:
- `base.py` — Abstract `DataSource`
- `openbb_source.py` — Wraps existing OpenBB lib
- `finnhub_source.py` — Finnhub client (free: 60 req/min)
- `registry.py` — Priority-based fallback

### 4.3 News

**`backend/app/models/news_article.py`** — news storage with JSON `symbols` field (portable)

**`backend/app/routes/news.py`** — `GET /api/news/{symbol}`, `GET /api/news/watchlist/{id}`

**`frontend/src/components/NewsFeed.jsx`** — compact news cards, `useAISerializable` enabled

### 4.4 Agent Tool Updates
- `get_news` tool → real aggregated data
- `get_quote` tool → cache layer
- New `get_market_news` tool for general market news

### 4.5 Dependencies
- `backend/requirements.txt` — add: `finnhub-python>=2.4.0`

### 4.6 Verification
1. `GET /api/news/AAPL` → aggregated results
2. Ask agent "What's the latest news on AAPL?" → uses get_news tool
3. Second request within TTL → cache hit (check Redis)

---

## Phase 5: Alerts & Notifications

### Goal
Celery background processing. Alert evaluation engine. In-app notifications.

### 5.1 Infrastructure

**`docker-compose.yml`** — add celery-worker + celery-beat (Redis broker already in place)

**`backend/celery_app.py`** — Beat schedule:
- `evaluate_all_alerts` — every 60s
- `refresh_watchlist_quotes` — every 300s
- `cleanup_expired_cache` — hourly

**`backend/requirements.txt`** — add: `celery>=5.3.0`

### 5.2 Models
- `backend/app/models/alert.py` — alert_type, condition (JSON), is_active, triggered_at
- `backend/app/models/notification.py` — type, title, message, is_read

### 5.3 Alert Evaluator
**`backend/app/services/alert_evaluator.py`** — plugin-style `_evaluate_{alert_type}()` handlers using cached quotes

### 5.4 Routes
- `/api/alerts` — CRUD (max 50 active per user)
- `/api/notifications` — list, mark read, unread count

### 5.5 Frontend
- `NotificationBell.jsx` — header bell + dropdown (poll every 30s)
- `AlertsPage.jsx` — list/create/manage alerts

### 5.6 Agent Integration
- `propose_action` → `"create_alert"` now actually creates alerts
- New `get_alerts` tool for querying existing alerts

---

## Phase 6: Earnings + Portfolio Reports

### 6.1 Earnings
- `backend/app/models/earnings.py` — earnings data + cached AI summary
- `backend/app/services/earnings_service.py` — calendar + AI summarization
- `backend/app/routes/earnings.py` — `/api/earnings/calendar`, `/{symbol}/{quarter}`
- `frontend/src/pages/EarningsCalendar.jsx` — timeline view, `useAISerializable`

### 6.2 Portfolio Reports
- `backend/app/services/portfolio_report.py` — gathers data, generates structured report
- `backend/app/routes/reports.py` — `POST /api/reports/portfolio-summary` (streaming)
- `frontend/src/pages/PortfolioReport.jsx` — rendered markdown report

---

## Phase 7: Testing & Production Hardening

### 7.1 Testing
**Backend** (`backend/tests/`):
- `unit/test_agent_tools.py`, `test_context_manager.py`, `test_alert_evaluator.py`, `test_cache_service.py`, `test_rate_limiter.py`
- `integration/test_chat_routes.py`, `test_watchlist_routes.py`, `test_alert_routes.py`

**Frontend** (`frontend/src/__tests__/`):
- `AISidebar.test.jsx`, `SendToAIButton.test.jsx`, `useAISerializable.test.js`, `chatStore.test.js`

### 7.2 Production Config
- `docker-compose.prod.yml`, production Dockerfiles
- `.env.example` with all required vars

### 7.3 Observability
- Structured JSON logging
- Health endpoints: `/health`, `/health/redis`, `/health/celery`
- Token usage tracking per user (for future billing)

### 7.4 Security
- Input sanitization on chat endpoint
- CORS tightening for production
- Image upload validation (if screenshots re-enabled later)

---

## Cost Optimization

| Category | Strategy |
|----------|----------|
| Agent calls | max_tokens=4096, tool loop cap=10, token counting |
| Context window | Auto-summarization at 80% capacity |
| Market data | Tiered TTL caching via Redis (60s–3600s) |
| Data sources | Free tier first (OpenBB/FMP), Finnhub fallback |
| Alert eval | Batch on cached data, no live API per alert |
| Infrastructure | Single Celery worker; Redis dual-use (broker + cache) |
| Rate limiting | 30 req/min per user on chat endpoint |

---

## Open Questions

1. **LLM provider swap** — Architecture supports it. If adding OpenAI/Google, create `LLMProvider` abstraction in `backend/app/lib/agent/providers/`. Tool definitions need minor format translation.
2. **Billing/tiers** — Deferred. Track token usage per user for future.
3. **Email/push notifications** — Extensible via Notification model `type` field, not implemented yet.
4. **Earnings transcript source** — Evaluate free sources (SEC EDGAR). May need scraping.
5. **WebSocket upgrade** — SSE is sufficient for now. If bidirectional communication needed (real-time alerts, collaborative features), retrofit WebSockets later.
6. **Memory system** — Code exists but needs design work: dedup strategy, confidence scoring, fact updates, expiry logic. Revisit after core chat is validated.
