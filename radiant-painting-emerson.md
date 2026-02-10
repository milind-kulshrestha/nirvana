# Nirvana: AI-Powered Investment Platform — Full Implementation Plan

## Vision
Evolve the stock watchlist MVP into an AI-powered investment tracking and discovery platform. The AI agent (powered by the Anthropic Python SDK with a provider-agnostic abstraction layer) can query market data, analyze any in-app component (data + visual), propose actions with user confirmation, and provide conversational investment research. The architecture is designed to support swapping LLM providers in the future.

---

## Phase 1: AI Agent Foundation (Priority — Build First)

### Goal
Ship the core AI agent harness using the Anthropic Python SDK (direct API, not Claude Agent SDK) with custom tools, persistent sidebar, streaming responses, conversation history, toggleable memory, and a generic "send any component to AI" system.

### 1.1 New Database Models

**`backend/app/models/conversation.py`**
| Field | Type | Notes |
|-------|------|-------|
| id | Integer PK | |
| user_id | FK → users.id | CASCADE delete, indexed |
| title | String(255) | Auto-set from first user message |
| created_at | DateTime | |
| updated_at | DateTime | |

**`backend/app/models/message.py`**
| Field | Type | Notes |
|-------|------|-------|
| id | Integer PK | |
| conversation_id | FK → conversations.id | CASCADE delete, indexed |
| role | String(20) | "user" / "assistant" / "tool" |
| content | Text | |
| metadata | JSON | Tool calls, proposed actions, token usage |
| created_at | DateTime | |

**`backend/app/models/memory_fact.py`**
| Field | Type | Notes |
|-------|------|-------|
| id | Integer PK | |
| user_id | FK → users.id | CASCADE delete, indexed |
| conversation_id | FK → conversations.id | SET NULL |
| fact_type | String(50) | "preference" / "portfolio" / "strategy" / "risk_tolerance" |
| content | Text | |
| confidence | Float | 0.0–1.0 |
| created_at | DateTime | |
| expires_at | DateTime | Optional TTL |

**`backend/app/models/pending_action.py`**
| Field | Type | Notes |
|-------|------|-------|
| id | Integer PK | |
| user_id | FK → users.id | CASCADE delete |
| conversation_id | FK → conversations.id | CASCADE |
| action_type | String(50) | "create_alert" / "add_to_watchlist" / "remove_stock" |
| action_payload | JSON | Full action parameters |
| status | String(20) | "pending" / "approved" / "rejected" / "executed" |
| created_at | DateTime | |
| resolved_at | DateTime | |

**Update `backend/app/models/user.py`** — add `ai_memory_enabled = Column(Boolean, default=True)` and relationships.

### 1.2 Skill / Workflow System (Native Agent SDK Skills)

**Key insight:** The Claude Agent SDK has a **native Skill system** — skills are `SKILL.md` files with YAML frontmatter, loaded from `.claude/skills/` directories. The SDK provides a built-in `Skill` tool that Claude invokes autonomously. We leverage this native system and extend it with a DB-backed layer for user-created skills.

**Architecture: Two-tier skill system**

1. **System skills (filesystem)** — shipped as `SKILL.md` files in the project's `.claude/skills/` directory. Loaded natively by the SDK. These are our built-in investment workflows.
2. **User skills (database → filesystem bridge)** — users create skills via the UI, stored in DB, but materialized to a per-user temp directory at agent startup so the SDK can discover them natively.

#### System Skills (shipped with platform)

**Directory:** `backend/.claude/skills/` (or a configurable project skill path)

Each skill follows the Agent SDK SKILL.md format:

**`backend/.claude/skills/research-stock/SKILL.md`**
```yaml
---
name: research-stock
description: Conduct comprehensive equity research following professional analysis methodology. Use when user asks to research, analyze, or evaluate a stock.
---

## Overview
Conduct comprehensive stock research following professional equity analysis principles.

## Phase 1: Clarifying Questions
Ask user to focus the research:
1. "What's your investment horizon?" (day trade / long-term / learning)
2. "What do you want to understand?" (business model / financials / valuation / all)
3. "Any specific concerns or catalysts you're tracking?"

## Phase 2: Research
Use your tools to gather data across these areas:

**Business Understanding:**
- Use get_quote and get_news to understand current state
- Analyze competitive positioning and revenue streams

**Financial Analysis:**
- Use get_financial_ratios for P/E, P/B, P/S, margins
- Use get_price_history for trend analysis
- Assess balance sheet strength

**Valuation Context:**
- Current multiples vs historical ranges
- Peer comparison (ask user for peers or suggest)
- Growth-adjusted valuation (PEG)

**Risk & Catalysts:**
- Use get_earnings for upcoming dates
- Use get_news for recent catalysts
- Identify key risks

## Phase 3: Synthesis
Build investment thesis:
- Clear bull/bear case with specific data points
- 3-5 key metrics to track
- Risk/reward assessment
- What would change the thesis

## Phase 4: Review
Present findings and ask: "Does this analysis look good? Should I save it?"
If yes, use propose_action to save the research report.

## Output Standards
- Objective: facts over hype, acknowledge bear case
- Actionable: clear thesis with metrics to track
- Sourced: cite specific numbers from tool results
- Balanced: equal weight to risks and opportunities
```

**Other system skills to ship:**
- `backend/data/system_skills/portfolio-review/SKILL.md` — health check across all watchlists
- `backend/data/system_skills/compare-stocks/SKILL.md` — side-by-side comparison
- `backend/data/system_skills/earnings-preview/SKILL.md` — pre-earnings analysis
- `backend/data/system_skills/watchlist-scan/SKILL.md` — scan for opportunities/risks

#### Skill Frontmatter Fields

Skills use YAML frontmatter for metadata (compatible with Claude Agent SDK format for future migration):

| Field | Usage |
|-------|-------|
| `name` | Skill identifier |
| `description` | Displayed in UI, used for intent matching |

#### How Skills Work (System Prompt Injection)

Skills are activated via **system prompt injection** — when a user selects a skill or the chat service detects matching intent, the skill's markdown content is prepended to the system prompt. The LLM then follows the skill's phases naturally using the available tools.

This approach is:
- **Provider-agnostic**: Works with any LLM that follows system prompt instructions
- **Simple**: No special SDK, no filesystem discovery, no subagent forking
- **Flexible**: Skills are just markdown — users can write whatever workflow they want
- **Future-compatible**: If we adopt Claude Agent SDK later, the SKILL.md format is already correct

#### User Skills (DB-backed)

**`backend/app/models/skill.py`**
| Field | Type | Notes |
|-------|------|-------|
| id | Integer PK | |
| user_id | FK → users.id | CASCADE delete |
| name | String(100) | Unique per user |
| description | String(500) | Displayed in UI, used for intent matching |
| content | Text | Full SKILL.md content (frontmatter + markdown) |
| is_active | Boolean | Default true |
| created_at | DateTime | |
| updated_at | DateTime | |

**`backend/app/lib/agent/skills.py`** — Skill manager
```python
class SkillManager:
    """Manages system + user skills. Skills are markdown workflows injected into the agent's system prompt."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def get_skill_content(self, skill_name: str) -> str | None:
        """Get skill content by name (checks user skills first, then system)."""
        ...

    def get_available_skills(self) -> list[dict]:
        """List all skills (system + user) for UI display."""
        ...

        return base_dir

    def get_available_skills(self) -> list[dict]:
        """List all skills (for UI display)."""
        user_skills = self.db.query(Skill).filter(
            ...
```

**How it works end-to-end:**
1. User sends message (or explicitly picks a skill from UI)
2. Chat service checks if a skill is selected or detects matching intent from skill descriptions
3. If a skill matches, its markdown content is prepended to the system prompt for this request
4. The LLM reads the skill instructions and follows the phases using the available tools
5. No special SDK needed — the LLM follows the instructions naturally
6. Skills use the same custom tools (get_quote, propose_action, etc.)
7. **Provider-agnostic**: Any LLM that follows system prompt instructions can execute skills

**Backend routes for skill CRUD:**

**`backend/app/routes/skills.py`** — prefix `/api/skills`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List all available skills (system + user) |
| GET | `/{name}` | Get skill content |
| POST | `/` | Create user skill (validates SKILL.md format) |
| PUT | `/{id}` | Update user skill |
| DELETE | `/{id}` | Delete user skill |
| GET | `/system` | List system skills only |

**Frontend skill UI:**
- **Skill picker in AISidebar** — chip list of available skills; click to invoke with `/skill-name` syntax
- **"Run skill" buttons on pages** — e.g., "Research this stock" on WatchlistDetail passes `/research-stock AAPL`
- **Skill editor** (`frontend/src/pages/SkillEditor.jsx`) — markdown editor with YAML frontmatter support, live preview
- **Skill library** (`frontend/src/pages/SkillLibrary.jsx`) — browse system + user skills, toggle active/inactive

### 1.3 Agent Harness (Anthropic Python SDK — Provider-Swappable)

**Package:** `anthropic` (Python, pip install)

**Architecture:** The agent uses the Anthropic Python SDK directly (not Claude Agent SDK) for full control over streaming, tool execution, and multi-user concurrency. This design is intentionally provider-swappable — the harness owns the tool loop and can be adapted to OpenAI, Google, or any provider that supports tool use.

**Why not Claude Agent SDK:**
- Claude Agent SDK is a CLI-oriented tool (bundles Claude Code) — not designed as an embedded library in a multi-user web service
- It assumes single-user filesystem context (`cwd`, shell access) — our agent must be sandboxed with only custom tools
- Direct API gives us full streaming control, explicit tool loop with iteration caps, and lighter dependencies
- Provider-agnostic: the tool definitions and ToolExecutor are provider-independent; only the harness's API call needs to change for a different LLM

**`backend/app/lib/agent/__init__.py`**

**`backend/app/lib/agent/harness.py`** — Core agent with streaming tool loop
```python
import anthropic
from app.lib.agent.tools import TOOL_DEFINITIONS, ToolExecutor
from app.lib.agent.prompts import build_system_prompt

MAX_TOOL_ITERATIONS = 10

class InvestmentAgent:
    """Manages agent lifecycle for a user session."""

    def __init__(self, user_id: int, db: Session, conversation_id: int | None = None):
        self.user_id = user_id
        self.db = db
        self.conversation_id = conversation_id
        self.tool_executor = ToolExecutor(db, user_id)
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        # Build system prompt with memory facts
        memory_facts = self._get_memory_facts()
        self.system_prompt = build_system_prompt(memory_facts)

    async def stream_response(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        """Stream agent response with tool use loop.

        Yields events: token, tool_call, tool_result, action_proposed, done, error.
        Loops up to MAX_TOOL_ITERATIONS when agent uses tools.
        """
        iteration = 0
        current_messages = list(messages)

        while iteration < MAX_TOOL_ITERATIONS:
            iteration += 1
            async with self.client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=self.system_prompt,
                messages=current_messages,
                tools=TOOL_DEFINITIONS,
            ) as stream:
                # Stream tokens, collect tool calls
                # Execute tools, append results, loop if needed
                ...
```

**Key design points:**
- Direct Anthropic API — no CLI dependency, no filesystem access
- Own tool loop with `MAX_TOOL_ITERATIONS=10` cap to prevent runaway costs
- `TOOL_DEFINITIONS` are plain JSON dicts — portable to any provider's tool format
- `ToolExecutor` is provider-independent — receives tool name + input, returns result
- Streaming via `messages.stream()` yields tokens in real-time
- **Future provider swap**: Replace `anthropic.AsyncAnthropic` with any SDK that supports streaming + tool use; keep `TOOL_DEFINITIONS`, `ToolExecutor`, and all other layers unchanged

**`backend/app/lib/agent/tools.py`** — Tool definitions + executor (provider-agnostic)

```python
# Tool definitions are plain JSON — portable across LLM providers
TOOL_DEFINITIONS = [
    {
        "name": "get_quote",
        "description": "Get real-time quote for a stock symbol",
        "input_schema": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}
    },
    # ... 7 more tools (get_watchlists, get_watchlist_items, get_price_history,
    #     get_financial_ratios, search_symbol, propose_action, get_user_memory)
]

class ToolExecutor:
    """Executes tool calls from the AI agent. Provider-independent."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    async def execute(self, tool_name: str, tool_input: dict) -> str:
        handler = getattr(self, f"_handle_{tool_name}", None)
        if not handler:
            return f"Unknown tool: {tool_name}"
        return str(await handler(tool_input))

    async def _handle_get_quote(self, input: dict) -> dict: ...
    async def _handle_get_watchlists(self, input: dict) -> list: ...
    async def _handle_propose_action(self, input: dict) -> dict:
        # Creates PendingAction record, returns confirmation request
        ...
    # ... etc
```

**`backend/app/lib/agent/prompts.py`** — System prompt templates
```
You are an AI investment research assistant. You help users track stocks,
analyze portfolios, and understand market trends.

CAPABILITIES (via tools):
- Look up real-time quotes, price history, and financial ratios
- Access the user's watchlists and holdings
- Search for stocks/ETFs by name or ticker
- Get market news for any symbol
- Get earnings calendar and results

ACTIONS (require user confirmation):
- You can PROPOSE actions using the propose_action tool:
  - "create_alert": Set price/technical alerts
  - "add_to_watchlist": Add a stock to a watchlist
  - "remove_stock": Remove a stock from a watchlist
- The user must confirm before any action executes.
- Always explain what the action will do before proposing it.

COMPONENT CONTEXT:
When the user sends you component data (charts, stock rows, watchlist views),
analyze both the structured data AND the visual screenshot if provided.
Reference specific data points in your analysis.

{memory_context}

GUIDELINES:
- Be concise but insightful
- Cite specific numbers from tool results
- Never give specific buy/sell recommendations
- Acknowledge uncertainty
- Remind users to do their own research
```

### 1.3 Chat Service

**`backend/app/services/chat_service.py`**
- Creates `InvestmentAgent` per request with user-specific context
- Manages conversation persistence (save user messages + assistant responses)
- Injects memory facts into system prompt when memory enabled
- Handles component context (structured data + base64 image) as multimodal input
- Streams agent output via SSE
- After response: extracts memory facts (separate cheap LLM call via Anthropic SDK directly, not the agent)
- Context window: last 20 messages replayed as conversation history

**`backend/app/services/action_executor.py`**
- `execute_pending_action(action_id, user_id)` — executes confirmed actions
- Maps action_type to handler: `_execute_create_alert()`, `_execute_add_to_watchlist()`, etc.
- Updates PendingAction status to "executed"
- Returns result summary

### 1.4 Backend Routes

**`backend/app/routes/chat.py`** — prefix `/api/chat`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/conversations` | List conversations (paginated) |
| POST | `/conversations` | Create new conversation |
| GET | `/conversations/{id}/messages` | Get messages |
| DELETE | `/conversations/{id}` | Delete conversation |
| POST | `/send` | Send message → SSE streaming agent response |
| POST | `/send-with-context` | Send message + component context (JSON + image) |
| POST | `/actions/{id}/confirm` | Confirm a pending action |
| POST | `/actions/{id}/reject` | Reject a pending action |
| GET | `/actions/pending` | List pending actions for user |

**SSE format:**
```
data: {"type": "token", "content": "..."}\n\n
data: {"type": "tool_call", "tool": "get_quote", "input": {...}}\n\n
data: {"type": "tool_result", "tool": "get_quote", "output": {...}}\n\n
data: {"type": "action_proposed", "action_id": 1, "description": "..."}\n\n
data: {"type": "skill_invoked", "skill_name": "research-stock"}\n\n
data: {"type": "done", "conversation_id": 123}\n\n
```

### 1.5 Generic Component-to-AI System (Frontend)

**Core concept:** Any React component can register as "AI-sendable" via a hook. When the user clicks "Send to AI", the component's structured data AND a visual screenshot are captured and sent to the agent.

**`frontend/src/stores/aiContextStore.js`** (Zustand)
```javascript
// Registry of AI-sendable components
const useAIContextStore = create((set, get) => ({
  registeredComponents: {},  // { componentId: { serialize: fn, ref: domRef } }

  registerComponent: (id, serializeFn, domRef) =>
    set(s => ({ registeredComponents: { ...s.registeredComponents, [id]: { serialize: serializeFn, ref: domRef } } })),

  unregisterComponent: (id) =>
    set(s => { const { [id]: _, ...rest } = s.registeredComponents; return { registeredComponents: rest }; }),

  // Capture structured data + visual for a specific component
  captureComponent: async (id) => {
    const comp = get().registeredComponents[id];
    if (!comp) return null;
    const structuredData = comp.serialize();
    let screenshot = null;
    if (comp.ref?.current) {
      const { toPng } = await import('html-to-image');
      screenshot = await toPng(comp.ref.current);  // base64 PNG
    }
    return { componentId: id, data: structuredData, screenshot };
  },

  // Capture ALL registered components on current page
  capturePageContext: async () => {
    const components = get().registeredComponents;
    const results = {};
    for (const [id, comp] of Object.entries(components)) {
      results[id] = { data: comp.serialize() };
      // Only capture visuals for explicitly requested components
    }
    return results;
  },
}));
```

**`frontend/src/hooks/useAISerializable.js`**
```javascript
import { useEffect, useRef } from 'react';
import useAIContextStore from '../stores/aiContextStore';

export function useAISerializable(componentId, serializeFn) {
  const ref = useRef(null);
  const register = useAIContextStore(s => s.registerComponent);
  const unregister = useAIContextStore(s => s.unregisterComponent);

  useEffect(() => {
    register(componentId, serializeFn, ref);
    return () => unregister(componentId);
  }, [componentId, serializeFn]);

  return ref;  // Attach to component's root DOM element
}
```

**Usage in components:**

```jsx
// StockRow.jsx
function StockRow({ item, quote, ma_200 }) {
  const aiRef = useAISerializable(`stock-${item.symbol}`, () => ({
    type: 'StockRow',
    symbol: item.symbol,
    quote: { price: quote?.price, change: quote?.change, change_percent: quote?.change_percent, volume: quote?.volume },
    indicators: { ma_200, isAboveMA: quote?.price > ma_200 },
  }));

  return <div ref={aiRef}>...</div>;
}

// PriceChart.jsx
function PriceChart({ symbol, data }) {
  const aiRef = useAISerializable(`chart-${symbol}`, () => ({
    type: 'PriceChart',
    symbol,
    dataPoints: data.length,
    dateRange: { from: data[0]?.date, to: data[data.length-1]?.date },
    priceRange: { min: Math.min(...data.map(d => d.close)), max: Math.max(...data.map(d => d.close)) },
    data,  // Full time series
  }));

  return <div ref={aiRef}>...</div>;
}
```

**`frontend/src/components/SendToAIButton.jsx`**
- Small icon button overlaid on any AI-registered component
- On click: captures component data + screenshot → opens AISidebar with pre-filled context
- Uses `aiContextStore.captureComponent(componentId)`

**`frontend/src/components/AISidebar.jsx`**
- Fixed right panel (w-96), slides in/out
- Header: "AI Assistant" + "New Chat" + close
- Conversation history (collapsible)
- Messages with user/assistant/tool-call bubbles
- **Action confirmation UI**: when agent proposes action, show confirmation card with approve/reject buttons
- **Component context indicator**: shows "Analyzing: PriceChart (AAPL)" when context attached
- Contextual action chips (dynamic per page)
- Input bar with send button
- Streaming via SSE with ReadableStream parsing

**`frontend/src/components/AIToggleButton.jsx`**
- Floating button (bottom-right) to toggle sidebar

**`frontend/src/stores/chatStore.js`** (Zustand)
- State: `messages`, `conversations`, `currentConversationId`, `isStreaming`, `pendingActions`
- Actions: `sendMessage(content, componentContext?)`, `confirmAction(id)`, `rejectAction(id)`, `loadConversations()`, etc.
- SSE parsing handles token/tool_call/tool_result/action_proposed event types

### 1.6 Config & Dependencies

**`backend/requirements.txt`** — add:
```
anthropic>=0.40.0
```

**`frontend/package.json`** — add:
```
html-to-image: ^1.11.0
```

**`backend/app/config.py`** — add:
```python
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
```

**`docker-compose.yml`** — add `ANTHROPIC_API_KEY` env var.

**Migration:** `alembic revision --autogenerate -m "Add conversation, message, memory_fact, pending_action models"`

### 1.7 Risks
- **API cost** — each agent turn may involve multiple LLM calls for tool use loops → monitor token usage, set `max_tokens=4096`, cap at `MAX_TOOL_ITERATIONS=10`
- **Tool loop runaway** — agent could call tools excessively → explicit iteration cap in harness.py
- **Screenshot size** — base64 PNGs can be large → compress to JPEG, cap at 1MB, resize before sending
- **Memory extraction accuracy** — use separate cheap Anthropic API call (not agent) for fact extraction

---

## Phase 2: Expandable Stock Analytics + Valuation Metrics

### Goal
Implement the two approved design documents. All new components get `useAISerializable` hooks so they're immediately sendable to AI.

### 2.1 Backend

**`backend/app/lib/openbb_fundamentals.py`** (new)
- `get_financial_ratios(symbol, period="quarterly", limit=12)` — P/E, P/B, P/S via `obb.equity.fundamental.ratios()`
- `get_historical_valuation_metrics(symbol, months=6)` — historical P/E, EV/EBITDA

**`backend/app/routes/securities.py`** (modify)
- Add `GET /{symbol}/ratios?period=quarterly&limit=12`
- Extend `GET /{symbol}?include=valuation_history`

### 2.2 Frontend

**`frontend/src/components/StockAnalytics.jsx`** (new)
- Mounts when stock row expanded
- Parallel fetch: price history + ratios
- Tabs: "Price History" | "Valuation Metrics"
- Caches data — tab switching doesn't re-fetch
- **`useAISerializable`** — serializes all analytics data for AI

**`frontend/src/components/ValuationChart.jsx`** (new)
- Three stacked LineCharts (P/E, P/B, P/S), each 200px, black lines
- **`useAISerializable`** — serializes ratio data + visual ref
- **`<SendToAIButton>`** overlay for quick AI analysis

**Modify `frontend/src/components/StockRow.jsx`**
- Add `expanded` state + chevron toggle
- Render `<StockAnalytics>` below when expanded
- Remove `onSelect` prop

**Modify `frontend/src/pages/WatchlistDetail.jsx`**
- Remove right panel grid layout (right panel = AISidebar now)
- Remove `selectedStock` state
- Reduce padding per design doc

**Modify `frontend/src/components/PriceChart.jsx`**
- Dual y-axis support for valuation overlay
- **`<SendToAIButton>`** overlay

### 2.3 Agent Tool Updates
- Update `get_financial_ratios` tool to use new `openbb_fundamentals.py`
- Agent can now analyze valuation metrics when user asks

---

## Phase 3: Data Pipeline & Caching Infrastructure

### Goal
Multi-source data architecture with aggressive caching. Enriches AI agent context.

### 3.1 Database Models

**`backend/app/models/cached_data.py`**
| Field | Type | Notes |
|-------|------|-------|
| id | Integer PK | |
| symbol | String(20) | Indexed |
| data_type | String(50) | "quote" / "ratios" / "news" / "history" |
| data | JSON | |
| source | String(50) | "openbb" / "finnhub" |
| created_at | DateTime | |
| expires_at | DateTime | Indexed |

Unique constraint: (symbol, data_type, source).

**`backend/app/models/news_article.py`**
| Field | Type | Notes |
|-------|------|-------|
| id | Integer PK | |
| external_id | String(255) | Unique dedup key |
| title | String(500) | |
| summary | Text | |
| url | String(1000) | |
| source | String(100) | |
| published_at | DateTime | Indexed |
| symbols | ARRAY(String) | Related tickers |
| sentiment | String(20) | positive/negative/neutral |

### 3.2 Data Source Abstraction

**`backend/app/lib/data_sources/`** package:
- **`base.py`** — Abstract `DataSource` (get_quote, get_fundamentals, get_news, health_check, rate_limit)
- **`openbb_source.py`** — Wraps existing OpenBB lib
- **`finnhub_source.py`** — Finnhub client (free: 60 req/min)
- **`registry.py`** — `DataSourceRegistry` with priority-based fallback

### 3.3 Cache Service

**`backend/app/services/cache_service.py`**
- PostgreSQL-backed initially (Redis in Phase 4)
- TTL: quotes=60s, ratios=3600s, news=300s, history=3600s
- get/set/invalidate/cleanup_expired

### 3.4 Routes

**`backend/app/routes/news.py`** — prefix `/api/news`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/{symbol}` | News for a symbol |
| GET | `/watchlist/{id}` | News for all symbols in watchlist |

### 3.5 Frontend

**`frontend/src/components/NewsFeed.jsx`** — compact news card list, `useAISerializable` enabled.

### 3.6 Agent Tool Updates
- `get_news` tool now queries real aggregated data
- `get_quote` tool now uses cache layer

### 3.7 Dependencies
**`backend/requirements.txt`** — add: `finnhub-python>=2.4.0`

### 3.8 Caching TTL
| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Quotes | 60s | Freshness vs cost |
| Fundamentals | 1 hour | Changes quarterly |
| News | 5 min | Moderate freshness |
| Historical | 1 hour | Stable intraday |

---

## Phase 4: Background Processing & Alerts

### Goal
Celery + Redis. Alert evaluation engine. In-app notifications. Agent can propose alert creation.

### 4.1 Infrastructure

**`docker-compose.yml`** — add:
- `redis` (redis:7-alpine)
- `celery-worker` (`celery -A celery_app worker`)
- `celery-beat` (`celery -A celery_app beat`)

**`backend/celery_app.py`** — Beat schedule:
- `evaluate_all_alerts` — every 60s
- `refresh_watchlist_quotes` — every 300s
- `cleanup_expired_cache` — hourly
- `cleanup_old_notifications` — daily

**`backend/requirements.txt`** — add: `celery>=5.3.0`, `redis>=5.0.0`

### 4.2 Database Models

**`backend/app/models/alert.py`**
| Field | Type | Notes |
|-------|------|-------|
| id | Integer PK | |
| user_id | FK → users.id | CASCADE, indexed |
| symbol | String(20) | Indexed |
| alert_type | String(50) | price_above/price_below/percent_change/ma_crossover/volume_spike |
| condition | JSON | `{"threshold": 150, "period": "daily"}` |
| is_active | Boolean | Default true |
| triggered_at | DateTime | |
| created_at | DateTime | |

**`backend/app/models/notification.py`**
| Field | Type | Notes |
|-------|------|-------|
| id | Integer PK | |
| user_id | FK → users.id | CASCADE, indexed |
| alert_id | FK → alerts.id | SET NULL |
| type | String(50) | alert_triggered/system/ai_insight |
| title | String(255) | |
| message | Text | |
| is_read | Boolean | Default false, indexed |
| created_at | DateTime | |

### 4.3 Alert Evaluator

**`backend/app/services/alert_evaluator.py`**
- Plugin-style handlers: `_evaluate_{alert_type}()`
- Uses cached quotes — no live API calls per alert
- Types: price_above, price_below, percent_change, ma_crossover, volume_spike

### 4.4 Routes

**`backend/app/routes/alerts.py`** — `/api/alerts` — CRUD (max 50 active per user)
**`backend/app/routes/notifications.py`** — `/api/notifications` — list, mark read, unread count

### 4.5 Frontend

- **`frontend/src/stores/notificationStore.js`** — poll unread count every 30s
- **`frontend/src/stores/alertStore.js`** — CRUD
- **`frontend/src/components/NotificationBell.jsx`** — header bell + dropdown
- **`frontend/src/pages/AlertsPage.jsx`** — list/create/manage alerts

### 4.6 Agent Integration
- Agent's `propose_action` tool can propose `"create_alert"` with full condition config
- User confirms in sidebar → `action_executor.py` creates the alert
- Agent can also query existing alerts via new `get_alerts` tool

### 4.7 Migrate Cache to Redis
Move CacheService to Redis now that it's available. Dual-use: Celery broker + cache.

---

## Phase 5: Earnings + Portfolio Reports

### Goal
Earnings calendar with AI summaries. AI-generated portfolio reports. (PDF upload removed per requirements.)

### 5.1 Earnings

**`backend/app/models/earnings.py`**
| Field | Type | Notes |
|-------|------|-------|
| id | Integer PK | |
| symbol | String(20) | Indexed |
| report_date | Date | Indexed |
| fiscal_quarter | String(10) | "Q1 2025" |
| eps_estimate / eps_actual | Float | |
| revenue_estimate / revenue_actual | Float | |
| surprise_percent | Float | |
| ai_summary | Text | Cached AI summary |

**`backend/app/services/earnings_service.py`**
- `get_earnings_calendar(symbols, days_ahead=30)`
- `summarize_earnings(symbol, quarter)` — AI summary, cached

**`backend/app/routes/earnings.py`** — `/api/earnings`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/calendar` | Upcoming earnings for watchlist |
| GET | `/{symbol}/{quarter}` | Detail + AI summary |

### 5.2 Portfolio Reports

**`backend/app/services/portfolio_report.py`**
- Gathers all symbols + quotes via agent tools
- Generates: overview, performance, risk, watchpoints
- Returns structured JSON with markdown report

**`backend/app/routes/reports.py`** — `/api/reports`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/portfolio-summary` | Generate AI portfolio report (streaming) |

### 5.3 Frontend
- **`frontend/src/pages/EarningsCalendar.jsx`** — timeline view, `useAISerializable`
- **`frontend/src/components/EarningsCard.jsx`** — results + AI summary
- **`frontend/src/pages/PortfolioReport.jsx`** — rendered markdown report

### 5.4 Agent Tool Updates
- `get_earnings` tool now returns real data
- New `generate_report` tool for portfolio summaries within chat

---

## Phase 6: Testing, Production Hardening & Observability

### 6.1 Testing

**Backend** (`backend/tests/`):
```
unit/
  test_agent_tools.py        — mock each custom tool
  test_alert_evaluator.py    — all alert type evaluations
  test_cache_service.py      — TTL, get/set, cleanup
  test_data_sources.py       — each source + registry fallback
  test_action_executor.py    — pending action execution
integration/
  test_auth_routes.py
  test_watchlist_routes.py
  test_chat_routes.py        — conversation lifecycle + streaming
  test_alert_routes.py
  test_earnings_routes.py
```

**Frontend** (`frontend/src/__tests__/`):
```
components/AISidebar.test.jsx
components/SendToAIButton.test.jsx
hooks/useAISerializable.test.js
stores/chatStore.test.js
stores/aiContextStore.test.js
```

### 6.2 Production Config
- `docker-compose.prod.yml`, `Dockerfile.prod` (backend + frontend)
- `.env.example` with all required vars

### 6.3 Observability
- Structured JSON logging
- Sentry error tracking
- Health endpoints: `/health`, `/health/redis`, `/health/celery`
- Token usage tracking per user (for future billing)

### 6.4 Security
- Rate limiting on `/api/chat/send` (per-user)
- Image upload validation (type, size ≤ 1MB after compression)
- Input sanitization
- CORS tightening

---

## Architecture Decisions

### Anthropic Python SDK (Direct API) vs Claude Agent SDK
**Decision: Direct Anthropic API — provider-swappable**
- **Multi-user web service fit**: Agent SDK is CLI-oriented (single user, filesystem access); direct API works natively in FastAPI with concurrent requests
- **Sandboxed by design**: Only our 8 custom tools available — no filesystem, shell, or web browsing
- **Full streaming control**: Own the SSE event stream, map to custom event types (token, tool_call, action_proposed, etc.)
- **Provider-swappable**: Tool definitions are plain JSON dicts, ToolExecutor is provider-independent; only the harness API call needs to change for OpenAI/Google/etc.
- **Explicit tool loop**: `MAX_TOOL_ITERATIONS=10` prevents runaway costs; we control exactly how tool results flow back
- **Lighter dependencies**: Just `anthropic` package, no CLI binary bundled in Docker
- **Trade-off**: We maintain the tool loop ourselves (~50 lines), but gain full control and provider flexibility

### Component-to-AI: Structured Data + Visual Screenshot
**Decision: Dual format (JSON + base64 image)**
- Structured data: enables precise numerical analysis ("your P/E is 25.3")
- Visual screenshot: enables pattern recognition on charts (trends, crossovers)
- `html-to-image` for capture (more reliable than html2canvas for React)
- Images compressed to JPEG, ≤ 1MB, before sending as base64 in multimodal message

### Agent Actions: Propose + Confirm Pattern
**Decision: PendingAction model with user confirmation**
- Agent calls `propose_action` tool → creates PendingAction record
- Frontend shows confirmation card in sidebar
- User approves → `action_executor.py` runs the action
- Prevents accidental modifications, builds user trust
- Actions: create_alert, add_to_watchlist, remove_stock (extensible)

### SSE for Streaming
**Decision: Server-Sent Events**
- Simple, HTTP-based, works with FastAPI StreamingResponse
- Rich event types: token, tool_call, tool_result, action_proposed, done
- Sufficient for unidirectional streaming

### Memory: Extracted Facts
- Cheap separate API call after each conversation turn
- ~500 tokens injected into system prompt
- User can view/delete facts (future UI)

---

## Cost Optimization

| Category | Strategy |
|----------|----------|
| Agent calls | Set max_tokens, monitor tool loop depth |
| Memory extraction | Separate cheap API call (Haiku), not via agent |
| Market data | Tiered TTL caching (60s–3600s) |
| Data sources | Free tier first (OpenBB/FMP), Finnhub fallback |
| Alert eval | Batch on cached data, no live API per alert |
| Infrastructure | Single Celery worker; Redis dual-use |
| Screenshots | JPEG compression, ≤ 1MB cap |

---

## Critical Files by Phase

### Phase 1 (AI Agent Foundation + Skills)
- **Create:** `backend/app/models/conversation.py`, `message.py`, `memory_fact.py`, `pending_action.py`, `skill.py`
- **Create:** `backend/app/lib/agent/harness.py`, `tools.py`, `prompts.py`, `skills.py`
- **Create:** `backend/app/services/chat_service.py`, `action_executor.py`
- **Create:** `backend/app/routes/chat.py`, `skills.py`
- **Create:** `backend/data/system_skills/` — markdown files for each built-in skill (research-stock.md, portfolio-review.md, compare-stocks.md, earnings-preview.md, watchlist-scan.md)
- **Create:** `frontend/src/stores/chatStore.js`, `aiContextStore.js`
- **Create:** `frontend/src/hooks/useAISerializable.js`
- **Create:** `frontend/src/components/AISidebar.jsx`, `AIToggleButton.jsx`, `SendToAIButton.jsx`, `SkillPicker.jsx`
- **Create:** `frontend/src/pages/SkillLibrary.jsx`, `SkillEditor.jsx`
- **Modify:** `backend/app/models/user.py`, `backend/app/config.py`, `backend/app/main.py`
- **Modify:** `frontend/src/App.jsx`, `frontend/src/components/StockRow.jsx`, `frontend/src/components/PriceChart.jsx`
- **Modify:** `backend/requirements.txt` (add anthropic)
- **Modify:** `frontend/package.json` (add html-to-image)
- **Modify:** `docker-compose.yml` (ANTHROPIC_API_KEY)

### Phase 2 (Stock Analytics)
- **Create:** `backend/app/lib/openbb_fundamentals.py`
- **Create:** `frontend/src/components/StockAnalytics.jsx`, `ValuationChart.jsx`
- **Modify:** `backend/app/routes/securities.py`
- **Modify:** `frontend/src/components/StockRow.jsx`, `PriceChart.jsx`
- **Modify:** `frontend/src/pages/WatchlistDetail.jsx`

### Phase 3 (Data Pipeline)
- **Create:** `backend/app/models/cached_data.py`, `news_article.py`
- **Create:** `backend/app/lib/data_sources/base.py`, `openbb_source.py`, `finnhub_source.py`, `registry.py`
- **Create:** `backend/app/services/cache_service.py`
- **Create:** `backend/app/routes/news.py`
- **Create:** `frontend/src/components/NewsFeed.jsx`

### Phase 4 (Alerts)
- **Create:** `backend/celery_app.py`, `backend/app/models/alert.py`, `notification.py`
- **Create:** `backend/app/services/alert_evaluator.py`, `backend/app/tasks/alerts.py`
- **Create:** `backend/app/routes/alerts.py`, `notifications.py`
- **Create:** `frontend/src/stores/notificationStore.js`, `alertStore.js`
- **Create:** `frontend/src/components/NotificationBell.jsx`, `frontend/src/pages/AlertsPage.jsx`
- **Modify:** `docker-compose.yml`

### Phase 5 (Earnings + Reports)
- **Create:** `backend/app/models/earnings.py`
- **Create:** `backend/app/services/earnings_service.py`, `portfolio_report.py`
- **Create:** `backend/app/routes/earnings.py`, `reports.py`
- **Create:** `frontend/src/pages/EarningsCalendar.jsx`, `PortfolioReport.jsx`, `frontend/src/components/EarningsCard.jsx`

### Phase 6 (Testing + Production)
- **Create:** All test files, `docker-compose.prod.yml`, Dockerfiles, `.env.example`

---

## Verification Plan

**Phase 1:**
1. `docker-compose up -d && docker-compose exec backend alembic upgrade head`
2. Register/login → open AI sidebar → send "What are my watchlists?" → verify agent calls `get_watchlists` tool and streams response
3. Click `SendToAIButton` on a StockRow → verify structured data + screenshot sent → agent analyzes it
4. Ask agent "Set an alert for AAPL above $200" → verify action_proposed event → confirm → verify alert created
5. Start new conversation → verify history persists
6. Select "research-stock" skill from skill picker → send "Research AAPL" → verify skill content is injected into system prompt → agent follows skill phases (asks clarifying questions, then gathers data via tools, then synthesizes)
7. GET `/api/skills` → verify system skills listed → POST `/api/skills` to create custom skill → verify it appears in skill list
8. Send "Research NVDA" with matching skill auto-detected from description → verify skill instructions are followed

**Phase 2:**
1. Expand stock row → verify tabs render with Price History + Valuation Metrics
2. Click SendToAI on ValuationChart → verify agent receives ratio data
3. Test stock with missing fundamentals → graceful degradation

**Phase 3:**
1. `GET /api/news/AAPL` → aggregated results
2. Ask agent "What's the latest news on AAPL?" → uses get_news tool
3. Second request within TTL → cache hit

**Phase 4:**
1. `docker-compose up -d` with redis + celery → all services healthy
2. Create alert → Celery evaluates → notification appears
3. NotificationBell shows unread count

**Phase 5:**
1. `GET /api/earnings/calendar` → upcoming earnings
2. Ask agent "Summarize my portfolio" → streaming report
3. EarningsCalendar page renders with AI summary expandable

**Phase 6:**
1. `docker-compose exec backend pytest` — all pass
2. `cd frontend && npm test` — all pass

---

## Open Questions

1. **LLM provider swap** — Architecture supports swapping providers. If adding OpenAI/Google, create a `LLMProvider` abstraction in `backend/app/lib/agent/providers/` with `stream_with_tools()` method. Tool definitions need minor format translation (Anthropic → OpenAI function calling).
2. **Billing/tiers** — Deferred. Track token usage per user for future.
3. **Email/push notifications** — Extensible via Notification model `type` field, not implemented yet.
4. **Earnings transcript source** — Evaluate free sources (SEC EDGAR, Seeking Alpha). May need scraping.
5. **Skill auto-detection** — Currently skills are manually selected by user. Future: use skill descriptions to auto-match user intent in chat_service.py before sending to LLM.
