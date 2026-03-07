# Backend Architecture

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (desktop mode) or PostgreSQL 15 (cloud mode) with SQLAlchemy ORM
- **Authentication**: Session-based with signed cookies (itsdangerous) or single-user bypass
- **Market Data**: OpenBB SDK (FMP provider)
- **AI Agent**: Anthropic Claude SDK with streaming tool use
- **Migrations**: Alembic (PostgreSQL) or auto-create (SQLite)
- **Desktop Shell**: Tauri v2 (optional - for native app packaging)

## Project Structure

```
backend/
├── app/
│   ├── models/          # SQLAlchemy models
│   │   ├── user.py
│   │   ├── watchlist.py
│   │   ├── watchlist_item.py
│   │   ├── conversation.py    # AI chat sessions
│   │   ├── message.py         # Chat messages
│   │   ├── memory_fact.py     # User memory
│   │   ├── pending_action.py  # Actions awaiting approval
│   │   └── skill.py           # AI agent skills
│   ├── routes/          # API endpoints
│   │   ├── auth.py      # Authentication endpoints
│   │   ├── watchlists.py # Watchlist CRUD
│   │   ├── securities.py # Market data
│   │   ├── chat.py      # AI chat SSE streaming
│   │   ├── skills.py    # AI skills CRUD
│   │   └── settings.py  # Settings API + first-run detection
│   ├── services/        # Business logic
│   │   ├── chat_service.py     # Chat orchestration
│   │   └── action_executor.py  # Action execution
│   ├── agent/           # AI agent core
│   │   ├── harness.py   # InvestmentAgent (streaming loop)
│   │   ├── tools.py     # Tool definitions & executor
│   │   ├── skills.py    # Skill manager
│   │   ├── prompts.py   # System prompt template
│   │   └── system_skills/ # Pre-built skills
│   │       ├── research-stock.md
│   │       ├── portfolio-review.md
│   │       ├── compare-stocks.md
│   │       ├── earnings-preview.md
│   │       └── watchlist-scan.md
│   ├── lib/             # Utilities
│   │   ├── auth.py      # Password & session management
│   │   ├── openbb.py    # Market data integration (cache-first)
│   │   ├── market_cache.py # DuckDB market data cache
│   │   ├── scheduler.py # Background data refresh (APScheduler)
│   │   ├── config_manager.py # ~/.nirvana/config.json manager
│   │   └── validators.py # Input validation
│   ├── config.py        # Settings
│   ├── database.py      # DB connection
│   └── main.py          # FastAPI app
├── tests/               # Tests (pytest)
├── alembic/             # DB migrations
├── requirements.txt
└── Dockerfile
```

## Key Files

### `app/main.py`
- FastAPI app initialization
- CORS middleware configuration
- Router registration (/api/auth, /api/watchlists, /api/securities, /api/chat, /api/skills)
- OpenBB startup configuration (writes FMP_API_KEY to ~/.openbb_platform/user_settings.json)

### `app/config.py`
Environment-based settings:
- `DEBUG` - Enable debug mode
- `SECRET_KEY` - Session signing key (itsdangerous)
- `DATABASE_URL` - Database connection string (defaults to SQLite if not set)
- `SINGLE_USER_MODE` - Enable single-user desktop mode (bypasses auth)
- `CORS_ORIGINS` - Comma-separated allowed origins
- `ANTHROPIC_API_KEY` - Claude API key for AI agent
- `CLAUDE_MODEL` - Model name (default: claude-3-5-sonnet-20241022)
- `CLAUDE_MAX_TOKENS` - Max response tokens (default: 4096)
- `FMP_API_KEY` - Financial Modeling Prep API key for OpenBB

### `app/database.py`
- SQLAlchemy engine creation (SQLite or PostgreSQL)
- Automatic SQLite fallback when `DATABASE_URL` not set
- Auto-create tables on startup for SQLite mode
- SessionLocal factory
- Base class for models
- `get_db()` dependency for route injection

**Database Modes:**
- **SQLite Mode** (default): No `DATABASE_URL` set
  - Uses `sqlite:///~/.nirvana/nirvana.db`
  - Auto-creates tables on startup (no Alembic)
  - Ideal for single-user desktop application
- **PostgreSQL Mode**: `DATABASE_URL` set
  - Uses provided PostgreSQL connection string
  - Requires Alembic migrations
  - Ideal for multi-user cloud deployments

## Models

### User (`app/models/user.py`)
- `id` (Integer, primary key)
- `email` (String, unique, indexed)
- `password_hash` (String) - bcrypt hashed
- `created_at` (DateTime)
- Relationship: `watchlists` (one-to-many)

### Watchlist (`app/models/watchlist.py`)
- `id` (Integer, primary key)
- `name` (String)
- `user_id` (Integer, foreign key to User)
- `created_at` (DateTime)
- Relationships: `user` (many-to-one), `items` (one-to-many)

### WatchlistItem (`app/models/watchlist_item.py`)
- `id` (Integer, primary key)
- `watchlist_id` (Integer, foreign key to Watchlist)
- `symbol` (String) - stock ticker
- `added_at` (DateTime)
- Relationship: `watchlist` (many-to-one)

## Routes

### Authentication (`app/routes/auth.py`)
- `POST /api/auth/register` - Create new user
- `POST /api/auth/login` - Login and set session cookie
- `POST /api/auth/logout` - Clear session cookie
- `GET /api/auth/me` - Get current user info

**Authentication Modes:**

*Multi-User Mode (default):*
1. User submits credentials
2. Backend validates and creates signed session token
3. Token stored in HTTP-only cookie (7-day expiry)
4. Protected routes use `get_current_user` dependency
5. Dependency validates session cookie and retrieves User object

*Single-User Mode (`SINGLE_USER_MODE=true`):*
1. On startup, creates default user if not exists (email: `local@nirvana.app`)
2. `get_current_user` dependency automatically injects default user
3. No session validation required
4. Registration/login endpoints still work but are optional
5. Ideal for local desktop application

### Watchlists (`app/routes/watchlists.py`)
- `GET /api/watchlists` - List user's watchlists
- `POST /api/watchlists` - Create new watchlist
- `DELETE /api/watchlists/{id}` - Delete watchlist
- `POST /api/watchlists/{id}/items` - Add stock to watchlist
- `DELETE /api/watchlists/{id}/items/{item_id}` - Remove stock

### Securities (`app/routes/securities.py`)
- `GET /api/securities/{symbol}?include=quote,ma200,history`
  - Returns market data based on include parameter
- `GET /api/securities/{symbol}/ratios`
  - Returns historical financial ratios (P/E, P/B, P/S)
  - Requires authentication (uses `get_current_user` dependency)

## Utilities

### `app/lib/auth.py`
- `hash_password(password)` - bcrypt hashing
- `verify_password(plain, hashed)` - bcrypt verification
- `create_session_token(user_id)` - Generate signed token
- `decode_session_token(token)` - Validate and decode token

Session tokens use itsdangerous URLSafeTimedSerializer with SECRET_KEY.

### `app/lib/openbb.py`
OpenBB SDK integration with DuckDB cache layer:

- `get_quote(symbol)` - Returns `{price, change, change_percent, volume}`
  - Checks DuckDB cache first (TTL: 15 minutes)
  - Falls back to `obb.equity.price.quote(symbol, provider="fmp")`
  - Caches result on fetch

- `get_ma_200(symbol)` - Returns 200-day simple moving average
  - Tries computing from cached daily_prices first (needs >= 200 rows)
  - Falls back to fetching 250 days of historical data from OpenBB
  - Caches fetched history for future use

- `get_history(symbol, months=6)` - Returns list of `{date, close}`
  - Checks DuckDB cache for date range coverage
  - Falls back to `obb.equity.price.historical(symbol, provider="fmp")`
  - Caches full OHLCV data on fetch

All cache operations wrapped in try/except for graceful degradation if DuckDB is unavailable.

- `get_financial_ratios(symbol)` - Returns list of `{date, pe_ratio, pb_ratio, ps_ratio}`
  - Uses `obb.equity.fundamental.ratios(symbol, provider="fmp")`
  - Returns TTM (trailing twelve months) data on FMP free tier
  - Helper functions: `_format_date()`, `_safe_float_attr()` for DRY code

**Error Handling:**
- `SymbolNotFoundError` - Invalid or unknown symbol
- `OpenBBTimeoutError` - API request timeout

### `app/lib/market_cache.py`
DuckDB-based market data cache at `~/.nirvana/market_data.duckdb`:
- `get_cached_quote()` / `cache_quote()` - Quote snapshots (15 min TTL)
- `get_cached_history()` / `cache_history()` - Daily OHLCV prices
- `get_cached_fundamentals()` / `cache_fundamentals()` - Fundamentals (24h TTL)
- Thread-safe singleton connection with lazy init

### `app/lib/scheduler.py`
Background scheduler using APScheduler (AsyncIOScheduler):
- `refresh_quotes` - Every 15 min, Mon-Fri, 9:00 AM - 3:45 PM ET
- `daily_snapshot` - 6:00 PM ET weekdays (12 months of history per symbol)
- Refreshes all symbols across user watchlists

### `app/lib/config_manager.py`
Thread-safe configuration manager for `~/.nirvana/config.json`:
- Read/write API keys and preferences
- Env vars override config.json values
- Lazy loading with in-memory cache

### `app/lib/validators.py`
Input validation functions for email and password requirements.

## Database Migrations

Uses Alembic for schema versioning:

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

Migrations stored in `backend/alembic/versions/`.

## Development Notes

### Running the Backend

**Desktop Mode (SQLite + Single User):**
```bash
cd backend
SINGLE_USER_MODE=true uvicorn app.main:app --port 6900
# No Docker, Postgres, or auth required
# Perfect for local development or desktop app
```

**Docker Compose (PostgreSQL + Multi-User):**
```bash
docker-compose up -d
docker-compose exec backend alembic upgrade head
docker-compose logs -f backend
# Requires Docker and PostgreSQL
# Ideal for cloud deployments
```

**Local Development (PostgreSQL):**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
# Requires local PostgreSQL running
```

### Testing

```bash
cd backend
pytest
```

### OpenBB Configuration

- FMP_API_KEY configured via environment variable
- On startup, FastAPI writes key to `~/.openbb_platform/user_settings.json`
- All OpenBB calls specify `provider="fmp"`
- Uses free yfinance data if no FMP key provided

### Session Security

- HTTP-only cookies prevent XSS attacks
- Signed tokens prevent tampering (itsdangerous)
- SameSite=lax protects against CSRF
- Secure flag enabled in production (HTTPS only)
- 7-day expiration with max_age validation
