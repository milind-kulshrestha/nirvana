# Nirvana Backend Architecture

## Overview

The Nirvana backend is a FastAPI-based application that provides market data analysis and AI-powered investment insights. It uses a dual-database architecture with SQLite for application state and DuckDB for market data caching.

## Architecture Diagrams

- **Backend Overview**: `@/Users/mk/Documents/Work/nirvana/docs/reference/architecture/backend-overview.excalidraw`
- **Chat Flow**: `@/Users/mk/Documents/Work/nirvana/docs/reference/architecture/chat-flow.excalidraw`

## Core Components

### 1. FastAPI Application (`app/main.py`)

The main application entry point that:
- Configures CORS middleware for frontend communication
- Registers API route handlers
- Manages startup/shutdown lifecycle events
- Initializes databases, scheduler, and MCP servers

**Key startup events:**
- `init_database()` - Creates SQLite tables in single-user mode
- `configure_openbb()` - Sets up OpenBB with FMP API credentials
- `start_fmp_mcp()` - Launches FMP MCP server for enhanced data access
- `start_scheduler()` - Starts background market data refresh jobs

### 2. API Routes (`app/routes/`)

**Authentication** (`/api/auth`)
- Login/logout with session cookies
- Single-user mode auto-creates `local@nirvana.app` user

**Chat** (`/api/chat`)
- `POST /send` - Stream AI responses via Server-Sent Events (SSE)
- `GET /conversations` - List user conversations
- `GET /conversations/{id}/messages` - Get conversation history
- `POST /actions/{id}/confirm` - Execute pending actions

**Watchlists** (`/api/watchlists`)
- CRUD operations for stock watchlists
- Add/remove securities from watchlists

**Market Data** (`/api/market`)
- Quote data, historical prices, fundamentals
- Market movers (gainers, losers, most active)
- Calendar events (earnings, dividends)

**ETF** (`/api/etf`)
- ETF snapshot data with relative strength analysis
- Custom ETF symbol management

### 3. Data Layer

#### SQLite Database (`~/.nirvana/nirvana.db`)

**Purpose**: Application state and user data

**Configuration**:
- WAL mode for better concurrency
- Foreign keys enabled
- Auto-created on startup in single-user mode

**Tables**:
- `users` - User accounts
- `watchlists` - User watchlists
- `watchlist_items` - Securities in watchlists
- `conversations` - AI chat conversations
- `messages` - Chat message history
- `memory_facts` - AI memory (user preferences, portfolio info)
- `pending_actions` - Actions requiring user confirmation
- `skills` - Custom AI skills
- `etf_custom_symbols` - User-defined ETF symbols

#### DuckDB Database (`~/.nirvana/market_data.duckdb`)

**Purpose**: Market data cache layer (optimized for analytical queries)

**Tables**:
- `quotes_cache` - Real-time quotes (15-minute TTL)
- `daily_prices` - Historical OHLCV data
- `fundamentals` - Company fundamentals (24-hour TTL)
- `etf_snapshot` - ETF relative strength data

**Why DuckDB?**
- Columnar storage optimized for time-series data
- Fast analytical queries on market data
- Separate from transactional SQLite database
- No external database server required

### 4. Service Layer

#### ChatService (`app/services/chat_service.py`)

Manages AI agent conversations:
- Creates/retrieves conversations
- Saves user and assistant messages
- Streams chat responses via async generator
- Extracts and stores memory facts
- Maintains conversation context (last 20 messages)

#### OpenBB Integration (`app/lib/openbb.py`)

Market data fetching with intelligent caching:

**Cache-first strategy:**
1. Check DuckDB cache
2. If miss or stale, fetch from OpenBB/FMP API
3. Cache result before returning

**Key functions:**
- `get_quote(symbol)` - Current price, change, volume
- `get_history(symbol, months)` - Historical prices for charts
- `get_ma_200(symbol)` - 200-day moving average
- `get_performance(symbol)` - Multi-period returns
- `get_estimates(symbol)` - Analyst consensus
- `get_insider_trading(symbol)` - SEC Form 4 filings
- `get_market_movers(category)` - Discovery data

**Error handling:**
- `SymbolNotFoundError` - Invalid ticker
- `OpenBBTimeoutError` - API timeout

### 5. AI Agent Layer

#### InvestmentAgent (`app/lib/agent/harness.py`)

Streaming AI agent with tool use capabilities:

**Architecture:**
- Uses LiteLLM for multi-provider LLM access (Anthropic, OpenAI, Google, Groq)
- Scratchpad-based context management (100k token threshold)
- Tool execution with deduplication and rate limiting
- Streaming response with SSE events

**Context Management:**
- Keeps last 5 tool results when approaching context limit
- Clears oldest tool results to stay under 100k tokens
- Rebuilds iteration prompts with accumulated context

**Event Types:**
- `token` - Streamed text content
- `tool_call` - Tool invocation
- `tool_result` - Tool execution result
- `action_proposed` - Action requiring confirmation
- `context_cleared` - Context window management
- `done` - Final response with usage stats
- `error` - Error occurred

#### ToolExecutor (`app/lib/agent/tools.py`)

Executes agent tools:
- `get_quote` - Fetch stock quote
- `search` - Web search for information
- `get_fundamentals` - Company fundamentals
- `get_insider_trades` - Insider trading activity
- `propose_action` - Propose action requiring user approval
- `skill` - Execute custom skills

#### Scratchpad (`app/lib/agent/scratchpad.py`)

Context window management:
- Tracks tool usage and results
- Estimates token count
- Implements tool deduplication
- Manages context clearing strategy

### 6. Background Scheduler (`app/lib/scheduler.py`)

APScheduler-based background jobs:

**Job 1: Refresh Quotes**
- Schedule: Every 15 minutes, Mon-Fri, 9:30 AM - 3:45 PM ET
- Action: Fetch fresh quotes for all watchlist symbols
- Purpose: Keep cache warm during market hours

**Job 2: Daily Snapshot**
- Schedule: 6:00 PM ET, Mon-Fri
- Action: Fetch end-of-day prices for all watchlist symbols
- Purpose: Capture closing prices and historical data

### 7. Configuration (`app/config.py`)

Settings with priority: environment variables > config.json > defaults

**Key settings:**
- `SINGLE_USER_MODE` - Bypass authentication, use SQLite
- `DATABASE_URL` - Auto-switches to SQLite in single-user mode
- `OPENBB_API_KEY` / `FMP_API_KEY` - Market data API key
- `ANTHROPIC_API_KEY` - Claude API key
- `OPENAI_API_KEY` - GPT API key
- `GOOGLE_API_KEY` - Gemini API key
- `GROQ_API_KEY` - Groq API key
- `DEFAULT_MODEL` - Default LLM model

## Request Flow Examples

### Chat Request Flow

1. **Frontend** sends `POST /api/chat/send` with message content
2. **ChatService** saves user message to SQLite `messages` table
3. **ChatService** creates `InvestmentAgent` with user context
4. **InvestmentAgent** loads memory facts from SQLite
5. **InvestmentAgent** calls LiteLLM with messages + tool definitions
6. **LLM** streams response (text tokens or tool calls)
7. If tool calls:
   - **ToolExecutor** executes tools (e.g., `get_quote("AAPL")`)
   - **OpenBB** checks DuckDB cache, fetches if needed
   - Results added to **Scratchpad**
   - **Agent** calls LLM again with tool results
8. Loop continues until LLM returns final text response
9. **ChatService** saves assistant message to SQLite
10. **ChatService** extracts memory facts (background)
11. Response streamed to frontend via SSE

### Market Data Request Flow

1. **Frontend** requests quote via `GET /api/market/quote/{symbol}`
2. **Market route** calls `openbb.get_quote(symbol)`
3. **OpenBB** checks DuckDB `quotes_cache` table
4. If cache hit (< 15 min old): return cached data
5. If cache miss:
   - Fetch from FMP API via OpenBB SDK
   - Cache result in DuckDB
   - Return data
6. **Route** returns JSON response to frontend

## Database Schema Highlights

### SQLite Tables

**conversations**
- `id`, `user_id`, `title`, `created_at`, `updated_at`
- One-to-many with messages

**messages**
- `id`, `conversation_id`, `role` (user/assistant), `content`, `metadata_json`, `created_at`
- Stores full chat history

**memory_facts**
- `id`, `user_id`, `conversation_id`, `fact_type`, `content`, `created_at`
- AI-extracted user preferences and context

**pending_actions**
- `id`, `user_id`, `conversation_id`, `action_type`, `description`, `payload_json`, `status`
- Actions requiring user confirmation

### DuckDB Tables

**quotes_cache**
- `symbol` (PK), `data` (JSON), `fetched_at`
- 15-minute TTL for real-time quotes

**daily_prices**
- `symbol`, `date` (composite PK), `open`, `high`, `low`, `close`, `volume`
- Historical OHLCV data

**fundamentals**
- `symbol` (PK), `data` (JSON), `fetched_at`
- 24-hour TTL for company fundamentals

## Key Design Patterns

### Cache-First Data Access
All market data requests check cache before hitting external APIs, reducing latency and API costs.

### Dual Database Architecture
- SQLite for transactional data (ACID guarantees)
- DuckDB for analytical data (columnar, fast aggregations)

### Streaming Responses
AI chat uses SSE for real-time token streaming, improving perceived performance.

### Context Window Management
Scratchpad automatically manages LLM context to stay under token limits while preserving recent tool results.

### Single-User Mode
Simplified deployment for desktop app - no authentication, auto-created user, local SQLite database.

### Background Refresh
Scheduler pre-fetches market data during trading hours, keeping cache warm for instant responses.

## File Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings management
│   ├── database.py             # SQLite/SQLAlchemy setup
│   ├── routes/                 # API endpoints
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── watchlists.py
│   │   ├── market.py
│   │   └── etf.py
│   ├── services/               # Business logic
│   │   ├── chat_service.py
│   │   └── action_executor.py
│   ├── lib/                    # Utilities
│   │   ├── auth.py
│   │   ├── openbb.py           # Market data with cache
│   │   ├── market_cache.py     # DuckDB cache layer
│   │   ├── scheduler.py        # Background jobs
│   │   ├── fmp_mcp.py          # FMP MCP server
│   │   └── agent/              # AI agent components
│   │       ├── harness.py      # InvestmentAgent
│   │       ├── tools.py        # Tool definitions
│   │       ├── scratchpad.py   # Context management
│   │       └── prompts.py      # System prompts
│   └── models/                 # SQLAlchemy models
│       ├── user.py
│       ├── conversation.py
│       ├── message.py
│       └── watchlist.py
├── requirements.txt
└── alembic/                    # Database migrations (PostgreSQL only)
```

## Technology Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy** - ORM for SQLite
- **DuckDB** - Analytical database for market data
- **OpenBB** - Market data SDK (wraps FMP API)
- **LiteLLM** - Multi-provider LLM routing
- **APScheduler** - Background job scheduling
- **Pydantic** - Data validation
- **bcrypt** - Password hashing

## Performance Optimizations

1. **DuckDB caching** - Reduces API calls by 90%+
2. **Streaming responses** - Improves perceived latency
3. **Background refresh** - Pre-warms cache during market hours
4. **Context management** - Prevents token overflow errors
5. **Connection pooling** - Reuses database connections
6. **WAL mode** - Improves SQLite concurrency

## Security Considerations

- Session-based authentication with signed cookies
- Password hashing with bcrypt
- CORS configuration for frontend
- Single-user mode bypasses auth (desktop app only)
- API keys stored in config.json (not in database)
- No sensitive data in logs

## Future Enhancements

- Migration to Claude Agent SDK (replacing custom harness)
- MCP server integration for computer use
- Local DuckDB analytics pipelines
- Enhanced memory system with vector search
- Multi-user support with PostgreSQL
