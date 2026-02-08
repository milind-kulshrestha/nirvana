# Backend Architecture

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL 15 with SQLAlchemy ORM
- **Authentication**: Session-based with signed cookies (itsdangerous)
- **Market Data**: OpenBB SDK (FMP provider)
- **AI Agent**: Anthropic Claude SDK with streaming tool use
- **Migrations**: Alembic

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
│   │   └── skills.py    # AI skills CRUD
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
│   │   ├── openbb.py    # Market data integration
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
- `DATABASE_URL` - PostgreSQL connection string
- `CORS_ORIGINS` - Comma-separated allowed origins
- `ANTHROPIC_API_KEY` - Claude API key for AI agent
- `CLAUDE_MODEL` - Model name (default: claude-3-5-sonnet-20241022)
- `CLAUDE_MAX_TOKENS` - Max response tokens (default: 4096)
- `FMP_API_KEY` - Financial Modeling Prep API key for OpenBB

### `app/database.py`
- SQLAlchemy engine creation
- SessionLocal factory
- Base class for models
- `get_db()` dependency for route injection

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

**Authentication Flow:**
1. User submits credentials
2. Backend validates and creates signed session token
3. Token stored in HTTP-only cookie (7-day expiry)
4. Protected routes use `get_current_user` dependency
5. Dependency validates session cookie and retrieves User object

### Watchlists (`app/routes/watchlists.py`)
- `GET /api/watchlists` - List user's watchlists
- `POST /api/watchlists` - Create new watchlist
- `DELETE /api/watchlists/{id}` - Delete watchlist
- `POST /api/watchlists/{id}/items` - Add stock to watchlist
- `DELETE /api/watchlists/{id}/items/{item_id}` - Remove stock

### Securities (`app/routes/securities.py`)
- `GET /api/securities/{symbol}?include=quote,ma200,history`
- Returns market data based on include parameter

## Utilities

### `app/lib/auth.py`
- `hash_password(password)` - bcrypt hashing
- `verify_password(plain, hashed)` - bcrypt verification
- `create_session_token(user_id)` - Generate signed token
- `decode_session_token(token)` - Validate and decode token

Session tokens use itsdangerous URLSafeTimedSerializer with SECRET_KEY.

### `app/lib/openbb.py`
OpenBB SDK integration:

- `get_quote(symbol)` - Returns `{price, change, change_percent, volume}`
  - Uses `obb.equity.price.quote(symbol, provider="fmp")`

- `get_ma_200(symbol)` - Returns 200-day simple moving average
  - Fetches 250 days of historical data
  - Calculates average of last 200 closing prices

- `get_history(symbol, months=6)` - Returns list of `{date, close}`
  - Uses `obb.equity.price.historical(symbol, provider="fmp")`

**Error Handling:**
- `SymbolNotFoundError` - Invalid or unknown symbol
- `OpenBBTimeoutError` - API request timeout

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

**Docker Compose (recommended):**
```bash
docker-compose up -d
docker-compose exec backend alembic upgrade head
docker-compose logs -f backend
```

**Local:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
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
