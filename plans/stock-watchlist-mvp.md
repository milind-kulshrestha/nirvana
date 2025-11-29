# Stock Watchlist Tracker - V1 MVP

**Created**: 2025-11-28
**Timeline**: 2-3 weeks
**Philosophy**: Ship the simplest thing that works, then iterate based on real user feedback

---

## Executive Summary

Build a minimal viable stock watchlist tracker that lets users:
1. Create multiple watchlists
2. Add stocks/crypto by ticker symbol
3. View live prices and key metrics (current price, 200-day MA, volume)
4. See basic price charts

**What we're NOT building in V1**: Agents, complex caching, background jobs, alert systems, or any "future-ready" infrastructure.

---

## Core User Stories

### Must Have (V1)
- [ ] As a user, I can register and log in with email/password
- [ ] As a user, I can create multiple named watchlists
- [ ] As a user, I can search for stocks by ticker and add them to watchlists
- [ ] As a user, I can remove stocks from watchlists
- [ ] As a user, I can view current price, 200-day MA, and volume for each stock
- [ ] As a user, I can see a 6-month price chart for each stock
- [ ] As a user, I can refresh data on-demand to get latest prices

### Won't Have (V1)
- ❌ AI agents or automation
- ❌ Real-time price updates (WebSockets)
- ❌ Alerts or notifications
- ❌ Background data refresh
- ❌ Social features or shared watchlists
- ❌ Portfolio tracking (just watchlists)
- ❌ Advanced technical indicators beyond MA

---

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ (SQLite for local dev)
- **ORM**: SQLAlchemy 2.0 with direct queries (no service/repository layers)
- **Auth**: Session-based with signed cookies (no JWT complexity)
- **Market Data**: OpenBB Python SDK (yfinance provider)

### Frontend
- **Framework**: React 18+ with Vite
- **Styling**: TailwindCSS + shadcn/ui components
- **Charts**: Recharts (simple, well-documented)
- **State**: Zustand (lightweight, no Redux boilerplate)
- **HTTP**: fetch API (no axios needed)

### Infrastructure
- **Development**: Docker Compose (PostgreSQL + app)
- **Production**: Single Docker container deployment
- **No**: Redis, Celery, message queues, or microservices

---

## Database Schema

### Simplified 3-Table Design

```python
# users table
User {
    id: Integer (PK, autoincrement)
    email: String(255, unique, indexed)
    password_hash: String(255)
    created_at: Timestamp
    updated_at: Timestamp
}

# watchlists table
Watchlist {
    id: Integer (PK, autoincrement)
    user_id: Integer (FK → users.id, CASCADE)
    name: String(50)
    created_at: Timestamp
    updated_at: Timestamp
}

# watchlist_items table
WatchlistItem {
    id: Integer (PK, autoincrement)
    watchlist_id: Integer (FK → watchlists.id, CASCADE)
    symbol: String(20)  # e.g., "AAPL", "BTC-USD"
    added_at: Timestamp

    UNIQUE(watchlist_id, symbol)  # No duplicates in same watchlist
}
```

**No separate tables for**:
- ❌ `SecurityMetadata` - fetch from OpenBB on-demand
- ❌ `CurrentMetrics` - calculate live, don't persist
- ❌ `HistoricalPrices` - fetch from OpenBB on-demand (revisit if slow)

### Indexes (Start Minimal)

```sql
-- Primary keys auto-indexed
-- Add these only:
CREATE INDEX idx_watchlist_user_id ON watchlists(user_id);
CREATE INDEX idx_watchlist_item_watchlist_id ON watchlist_items(watchlist_id);
```

**Add more indexes later** when you measure slow queries.

---

## API Design

### RESTful Endpoints (9 Total)

#### Authentication (3 endpoints)
```
POST   /api/auth/register
  Request: { email, password }
  Response: { user_id, email }

POST   /api/auth/login
  Request: { email, password }
  Response: { user_id, email }
  Sets: session cookie

POST   /api/auth/logout
  Response: 204 No Content
  Clears: session cookie
```

#### Watchlists (5 endpoints)
```
GET    /api/watchlists
  Response: [{ id, name, created_at, items_count }]

POST   /api/watchlists
  Request: { name }
  Response: { id, name, created_at }

DELETE /api/watchlists/{id}
  Response: 204 No Content

POST   /api/watchlists/{id}/items
  Request: { symbol }
  Response: { id, symbol, added_at, quote: {...} }

DELETE /api/watchlists/{id}/items/{item_id}
  Response: 204 No Content
```

#### Market Data (1 endpoint)
```
GET    /api/securities/{symbol}
  Query: ?include=quote,ma200,history
  Response: {
    symbol: "AAPL",
    name: "Apple Inc.",
    quote: {
      price: 185.50,
      change: 2.50,
      change_percent: 1.37,
      volume: 52430000
    },
    ma_200: 175.40,
    history: [
      { date: "2024-11-28", close: 185.50 },
      ...
    ]
  }
```

### Error Response Format

```json
{
  "error": {
    "code": "SYMBOL_NOT_FOUND",
    "message": "Symbol 'XYZ' not found",
    "status": 404
  }
}
```

**Standard HTTP codes**: 200, 201, 204, 400, 401, 404, 500

---

## Project Structure

```
financial-tracker/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings (5 env vars)
│   │   ├── database.py          # SQLAlchemy setup
│   │   │
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── watchlist.py
│   │   │   └── watchlist_item.py
│   │   │
│   │   ├── routes/              # API endpoints (no services)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── watchlists.py
│   │   │   └── securities.py
│   │   │
│   │   └── lib/                 # Utilities
│   │       ├── __init__.py
│   │       ├── openbb.py        # OpenBB integration
│   │       ├── auth.py          # Password hashing, sessions
│   │       └── validators.py   # Input validation
│   │
│   ├── tests/                   # Request tests only
│   │   ├── test_auth.py
│   │   ├── test_watchlists.py
│   │   └── conftest.py
│   │
│   ├── alembic/                 # DB migrations
│   │   └── versions/
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── WatchlistCard.jsx
│   │   │   ├── StockRow.jsx
│   │   │   ├── PriceChart.jsx
│   │   │   └── SearchBar.jsx
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Watchlists.jsx
│   │   │   └── WatchlistDetail.jsx
│   │   ├── stores/
│   │   │   └── authStore.js     # Zustand store
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
└── README.md
```

**Key differences from original**:
- ✂️ No `/services` directory
- ✂️ No `/repositories` directory
- ✂️ No `/integrations` directory
- ✂️ No `/agents` directory
- ✂️ Minimal `/lib` instead of complex layers

---

## Implementation Plan

### Week 1: Foundation

#### Day 1-2: Backend Setup
- [ ] Initialize FastAPI project
- [ ] Set up SQLAlchemy with 3 models (User, Watchlist, WatchlistItem)
- [ ] Create Alembic migrations
- [ ] Implement session-based auth (register, login, logout)
- [ ] Write auth tests

**Files**: `app/models/*.py`, `app/routes/auth.py`, `app/lib/auth.py`

#### Day 3-4: Watchlist CRUD
- [ ] Implement watchlist endpoints (GET, POST, DELETE)
- [ ] Implement watchlist items endpoints (POST, DELETE)
- [ ] Add input validation (symbol format, name length)
- [ ] Write watchlist tests

**Files**: `app/routes/watchlists.py`, `tests/test_watchlists.py`

#### Day 5: OpenBB Integration
- [ ] Integrate OpenBB SDK
- [ ] Implement quote fetching
- [ ] Implement 200-day MA calculation
- [ ] Implement 6-month history fetching
- [ ] Handle errors (symbol not found, API timeout)

**Files**: `app/lib/openbb.py`, `app/routes/securities.py`

### Week 2: Frontend

#### Day 6-7: Auth & Watchlist List
- [ ] Set up React + Vite + TailwindCSS
- [ ] Create login/register pages
- [ ] Implement Zustand auth store
- [ ] Create watchlists list page
- [ ] Add create/delete watchlist functionality

**Files**: `src/pages/Login.jsx`, `src/pages/Watchlists.jsx`, `src/stores/authStore.js`

#### Day 8-9: Watchlist Detail
- [ ] Create watchlist detail page
- [ ] Implement stock search and add
- [ ] Display live quotes (price, change, volume)
- [ ] Show 200-day MA with color coding (above/below)
- [ ] Add remove stock functionality

**Files**: `src/pages/WatchlistDetail.jsx`, `src/components/StockRow.jsx`

#### Day 10: Charts
- [ ] Integrate Recharts
- [ ] Create 6-month price chart component
- [ ] Add basic loading states
- [ ] Handle chart data fetching

**Files**: `src/components/PriceChart.jsx`

### Week 3: Polish & Deploy

#### Day 11-12: UI Polish
- [ ] Improve loading states and error messages
- [ ] Add mobile responsiveness
- [ ] Improve form validation feedback
- [ ] Add refresh button with loading indicator

#### Day 13: Testing & Fixes
- [ ] Test full user flow
- [ ] Fix bugs discovered during testing
- [ ] Add missing error handling
- [ ] Basic security check (SQL injection, XSS)

#### Day 14: Deployment
- [ ] Create production Dockerfile
- [ ] Set up PostgreSQL (managed service or container)
- [ ] Deploy backend + frontend
- [ ] Test in production environment

---

## OpenBB Integration Details

### Data Fetching Strategy

```python
# app/lib/openbb.py

from openbb import obb
from datetime import datetime, timedelta

def get_quote(symbol: str) -> dict:
    """Fetch current quote for symbol."""
    try:
        data = obb.equity.price.quote(symbol=symbol, provider="yfinance")
        return {
            "price": data.results[0].price,
            "change": data.results[0].change,
            "change_percent": data.results[0].change_percent,
            "volume": data.results[0].volume
        }
    except Exception as e:
        raise SymbolNotFoundError(f"Symbol {symbol} not found")

def get_ma_200(symbol: str) -> float:
    """Calculate 200-day moving average."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=250)  # Extra buffer

    historical = obb.equity.price.historical(
        symbol=symbol,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        provider="yfinance"
    )

    # Calculate SMA manually or use pandas
    prices = [day.close for day in historical.results[-200:]]
    return sum(prices) / len(prices)

def get_history(symbol: str, months: int = 6) -> list:
    """Fetch historical prices for charting."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)

    historical = obb.equity.price.historical(
        symbol=symbol,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        provider="yfinance"
    )

    return [
        {"date": day.date, "close": day.close}
        for day in historical.results
    ]
```

### Error Handling

```python
# app/routes/securities.py

from fastapi import HTTPException

@router.get("/securities/{symbol}")
async def get_security(symbol: str):
    try:
        quote = get_quote(symbol)
        ma_200 = get_ma_200(symbol)
        history = get_history(symbol)

        return {
            "symbol": symbol.upper(),
            "quote": quote,
            "ma_200": ma_200,
            "history": history
        }
    except SymbolNotFoundError:
        raise HTTPException(404, detail=f"Symbol {symbol} not found")
    except OpenBBTimeoutError:
        raise HTTPException(503, detail="Market data temporarily unavailable")
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        raise HTTPException(500, detail="Internal server error")
```

---

## Configuration

### Environment Variables (.env)

```bash
# Essential 5 variables only

# App
DEBUG=true
SECRET_KEY=your-secret-key-here-generate-with-openssl

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/watchlist

# OpenBB (optional, for premium features)
OPENBB_API_KEY=

# CORS
CORS_ORIGINS=http://localhost:5173
```

### Dependencies (requirements.txt)

```txt
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9

# OpenBB
openbb==4.1.0

# Auth
passlib[bcrypt]==1.7.4

# Utilities
python-dotenv==1.0.0
pydantic==2.5.0

# Database
alembic==1.13.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

**Removed from original**:
- ❌ redis (no caching layer)
- ❌ celery (no background jobs)
- ❌ python-jose (using sessions, not JWT)
- ❌ pandas, numpy (OpenBB includes these)
- ❌ pydantic-settings (overkill for 5 env vars)

---

## Testing Strategy

### Pragmatic Testing Approach

**Focus on request tests** (integration-style) instead of separate unit tests:

```python
# tests/test_watchlists.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_watchlist(client: AsyncClient, auth_token):
    response = await client.post(
        "/api/watchlists",
        json={"name": "Tech Stocks"},
        cookies={"session": auth_token}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tech Stocks"
    assert "id" in data

@pytest.mark.asyncio
async def test_add_stock_to_watchlist(client: AsyncClient, watchlist_id, auth_token):
    response = await client.post(
        f"/api/watchlists/{watchlist_id}/items",
        json={"symbol": "AAPL"},
        cookies={"session": auth_token}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "quote" in data  # Includes live quote
```

**No coverage requirements** - just test critical paths:
- Auth flow (register, login, logout)
- Watchlist CRUD
- Add/remove stocks
- Error cases (401, 404, 500)

---

## What We're Explicitly NOT Building

### Deferred to V2+ (Based on User Feedback)

1. **Caching Layer**
   - Start without Redis
   - If OpenBB calls are slow, add in-memory Python dict cache
   - Only add Redis if you need distributed caching

2. **Background Jobs**
   - No Celery, no scheduled refresh
   - Users manually refresh on-demand
   - Add background refresh only if users request it

3. **Real-time Updates**
   - No WebSockets, no SSE
   - Manual refresh button only
   - Add live updates only if critical for user experience

4. **Advanced Features**
   - Alerts and notifications
   - Portfolio tracking (vs watchlists)
   - Social features
   - Backtesting
   - AI agents

5. **Performance Optimization**
   - No premature indexes
   - No response caching
   - No database query optimization
   - Add optimizations when you measure actual slowness

6. **Production Hardening**
   - Basic rate limiting (FastAPI built-in)
   - Simple logging (uvicorn default)
   - No monitoring/alerting
   - Add when you have production traffic

---

## Success Criteria

### V1 is complete when:

- ✅ Users can register and log in
- ✅ Users can create watchlists with custom names
- ✅ Users can add stocks by ticker symbol
- ✅ Users see live price, 200-day MA, and volume
- ✅ Users see 6-month price chart
- ✅ Mobile-responsive UI works
- ✅ Core flows have request tests
- ✅ Deployed and accessible via URL

### V1 is NOT blocked by:

- ❌ Test coverage percentage
- ❌ Response time benchmarks
- ❌ Advanced error handling
- ❌ Perfect UI design
- ❌ Comprehensive documentation

**Philosophy**: Ship working software, get users, iterate based on real feedback.

---

## Architecture Principles (Learned from Review)

### 1. No Premature Abstraction
- Direct SQLAlchemy queries in routes (no repositories)
- Direct OpenBB calls in lib (no provider pattern)
- No service layer until complexity demands it

### 2. No Future-Proofing
- Build for current requirements only
- Refactor when you add features, not before
- Delete all "future" or "placeholder" code

### 3. Convention Over Configuration
- Hardcode limits (10 watchlists, 50 items) - change code when needed
- No feature flags or config system
- Environment variables only for secrets and environment-specific values

### 4. Simplicity Over Flexibility
- One auth method (sessions)
- One data provider (OpenBB/yfinance)
- One frontend framework (React)
- Decide and commit, don't over-engineer for "flexibility"

### 5. Ship and Learn
- V1 in 2-3 weeks, not 8 weeks
- Get real users
- Add complexity based on measured problems
- Delete features users don't use

---

## Deployment

### Development (Docker Compose)

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: watchlist
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/watchlist
      DEBUG: "true"
    depends_on:
      - db
    volumes:
      - ./backend:/app

volumes:
  postgres_data:
```

### Production (Simple Container Deploy)

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Deployment options** (pick one):
- Railway.app (easiest)
- Fly.io
- DigitalOcean App Platform
- Heroku
- AWS/GCP (overkill for V1)

---

## Migration Path (If Needed Later)

When you outgrow this simple architecture, here's the migration path:

### When to add Service Layer
- Business logic in routes exceeds 50 lines
- Same logic used in multiple routes
- Complex multi-model operations

### When to add Caching
- OpenBB API calls consistently > 2 seconds
- Same symbols fetched repeatedly
- User complaints about speed

### When to add Background Jobs
- Users request automatic refresh
- Data staleness becomes a problem
- Scheduled reports or alerts needed

### When to add Agents
- Clear user demand for AI features
- Manual analysis too time-consuming
- Specific automation requests from users

**Rule**: Refactor when pain is felt, not when pain is imagined.

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| OpenBB API rate limits | Use yfinance provider (generous free tier). Add caching only if hit limits. |
| Symbol validation | Validate ticker format (regex). Let OpenBB return 404 for invalid symbols. |
| Slow queries | Add indexes when you measure slow queries. Don't pre-optimize. |
| Security vulnerabilities | Use SQLAlchemy (prevents SQL injection). Sanitize inputs. HTTPS in prod. |
| Scope creep | Ruthlessly defer features to V2. Ship minimal V1 in 3 weeks. |

---

## Questions Resolved

### Why no JWT?
**Answer**: Sessions are simpler, more secure (no token exposure), and sufficient for V1. FastAPI has excellent session support.

### Why no Redis?
**Answer**: 100 concurrent users don't need distributed caching. PostgreSQL can handle this easily. Add Redis when you measure cache misses.

### Why no repositories?
**Answer**: SQLAlchemy IS your repository. Adding another layer is premature abstraction.

### Why no service layer?
**Answer**: Your routes are simple CRUD. When logic gets complex, refactor. Don't add layers preemptively.

### Why no historical data table?
**Answer**: Fetch from OpenBB on-demand. Only persist if API calls are consistently slow (> 3 seconds).

---

## Next Steps

1. **Review this plan** - confirm simplified scope aligns with your goals
2. **Answer open questions**:
   - Deployment platform preference? (Railway, Fly.io, DigitalOcean)
   - Any must-have features missing from V1?
   - Timeline: 2-3 weeks realistic for you?

3. **Start implementation** using `/compounding-engineering:workflows:work plans/stock-watchlist-mvp.md`

---

**Remember**: Your V1 should be embarrassingly simple. Ship it, get users, learn what they actually need. Then add complexity **only where proven necessary**.

Complexity is easy to add, hard to remove. Start minimal.
