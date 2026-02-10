# Dashboard Data Expansion — Feature Spec

**Created**: 2026-02-09  
**Status**: Draft  
**Provider**: FMP (via OpenBB Platform v4.1)  
**Data Validation**: All endpoints verified against FMP free-tier — see `workspace/reports/fmp_equity_report_AAPL_*.html`

---

## Overview

Expand Nirvana's market data layer beyond the current quote + MA200 + 6-month history to include OHLCV price data, multi-period performance, earnings estimates, market discovery feeds, and calendar events. All data sourced exclusively from FMP via OpenBB.

### Current State

| Layer | What Exists | Files |
|-------|------------|-------|
| **Backend lib** | `get_quote()`, `get_ma_200()`, `get_history()` | `backend/app/lib/openbb.py` |
| **Backend route** | `GET /api/securities/{symbol}?include=quote,ma200,history` | `backend/app/routes/securities.py` |
| **Cache** | DuckDB: `daily_prices`, `quotes_cache`, `fundamentals` tables | `backend/app/lib/market_cache.py` |
| **Frontend** | `StockRow` (quote + MA200 badge), `PriceChart` (6-mo close-only line) | `frontend/src/components/` |

### What's New

| # | Feature | Priority |
|---|---------|----------|
| 1 | **Extended Price Data** — OHLCV 250 days + multi-period performance | High |
| 2 | **Earnings Estimates** — consensus ratings & targets | High |
| 3 | **Market Discovery** — most active, top gainers, top losers | High |
| 4 | **Calendar** — upcoming dividends & earnings | High |

---

## Feature 1: Extended Price Data

### Problem
- `PriceChart` only renders close prices as a line chart
- No OHLCV data exposed to frontend (open/high/low/volume already cached in DuckDB but not served)
- No multi-period performance summary (1D, 5D, 1M, 3M, 6M, YTD, 1Y)

### FMP Data Available

**`obb.equity.price.historical`** — 250 rows, 9 columns:
```
open, high, low, close, volume, vwap, date, change, change_percent
```

**`obb.equity.price.performance`** — 1 row, 12 columns:
```
one_day_return, one_week_return, one_month_return, three_month_return,
six_month_return, ytd_return, one_year_return, three_year_return,
five_year_return, ten_year_return, max_return, symbol
```

### Backend Changes

#### `backend/app/lib/openbb.py`

**New function: `get_ohlcv()`**
```python
def get_ohlcv(symbol: str, days: int = 365) -> list[dict]:
    """
    Fetch OHLCV daily bars (up to 250 trading days).
    Returns: list of {date, open, high, low, close, volume}
    Cache: DuckDB daily_prices (already exists)
    """
```

**New function: `get_performance()`**
```python
def get_performance(symbol: str) -> dict:
    """
    Fetch multi-period return summary.
    Returns: {one_day, one_week, one_month, three_month, six_month, ytd, one_year, ...}
    Cache: DuckDB quotes_cache with TTL 15 min (reuse existing)
    """
```

#### `backend/app/routes/securities.py`

Extend `?include=` to accept `ohlcv` and `performance`:

```
GET /api/securities/{symbol}?include=quote,ma200,ohlcv,performance
```

**New response fields:**
```python
class OHLCVData(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class PerformanceData(BaseModel):
    one_day_return: Optional[float]
    one_week_return: Optional[float]
    one_month_return: Optional[float]
    three_month_return: Optional[float]
    six_month_return: Optional[float]
    ytd_return: Optional[float]
    one_year_return: Optional[float]

class SecurityResponse(BaseModel):
    # ... existing fields ...
    ohlcv: Optional[list[OHLCVData]] = None
    performance: Optional[PerformanceData] = None
```

### Frontend Changes

- **`PriceChart.jsx`** — Add candlestick/OHLCV mode toggle alongside existing line chart. Add volume bars below chart.
- **`StockRow.jsx`** — Add performance sparkline or colored return badges (1D, 1M, YTD, 1Y).
- **New component: `PerformanceTiles.jsx`** — Heatmap-style tiles showing multi-period returns with green/red coloring.

### Cache Strategy
- OHLCV: Already stored in `daily_prices` table. Serve from cache, backfill on miss.
- Performance: Store in `quotes_cache` as JSON with 15-min TTL (same as quotes).

---

## Feature 2: Earnings Estimates

### Problem
No analyst consensus data available in the app. Users can't see buy/hold/sell ratings or price targets.

### FMP Data Available

**`obb.equity.estimates.consensus`** — 1 row, 5 columns:
```
symbol, name, consensus_type (buy/hold/sell/strong_buy/strong_sell),
consensus_rating (numeric), target_price
```

### Backend Changes

#### `backend/app/lib/openbb.py`

**New function: `get_estimates()`**
```python
def get_estimates(symbol: str) -> dict:
    """
    Fetch analyst consensus estimates.
    Returns: {consensus_type, consensus_rating, target_price}
    Cache: DuckDB fundamentals table with 24h TTL
    """
```

#### `backend/app/routes/securities.py`

Extend `?include=` to accept `estimates`:

```
GET /api/securities/{symbol}?include=quote,estimates
```

**New response field:**
```python
class EstimatesData(BaseModel):
    consensus_type: Optional[str] = None     # "buy", "hold", "sell", etc.
    consensus_rating: Optional[float] = None  # numeric score
    target_price: Optional[float] = None

class SecurityResponse(BaseModel):
    # ... existing fields ...
    estimates: Optional[EstimatesData] = None
```

### Frontend Changes

- **`StockRow.jsx`** — Add consensus badge (Buy/Hold/Sell with color coding) and target price vs current price indicator.
- **New component: `EstimatesBadge.jsx`** — Pill-shaped badge: green for Buy/Strong Buy, yellow for Hold, red for Sell. Shows target price delta.

### Cache Strategy
- Store in `fundamentals` table as JSON with 24h TTL (already exists).

---

## Feature 3: Market Discovery

### Problem
No market-wide view. Users can only see stocks they've manually added to watchlists.

### FMP Data Available

**`obb.equity.discovery.active`** — 50 rows, 6 columns:
```
symbol, name, price, change, change_percent, volume
```

**`obb.equity.discovery.gainers`** — 50 rows, 6 columns (same schema)

**`obb.equity.discovery.losers`** — 50 rows, 6 columns (same schema)

### Backend Changes

#### `backend/app/lib/openbb.py`

**New function: `get_market_movers()`**
```python
def get_market_movers(category: str = "active") -> list[dict]:
    """
    Fetch market discovery data.
    Args:
        category: "active" | "gainers" | "losers"
    Returns: list of {symbol, name, price, change, change_percent, volume}
    Cache: DuckDB quotes_cache with key 'discovery:{category}', TTL 15 min
    """
```

#### `backend/app/routes/securities.py` (or new route file)

**New endpoints:**
```
GET /api/market/movers?category=active    # default
GET /api/market/movers?category=gainers
GET /api/market/movers?category=losers
```

**Response:**
```python
class MarketMover(BaseModel):
    symbol: str
    name: Optional[str] = None
    price: float
    change: float
    change_percent: float
    volume: int

class MarketMoversResponse(BaseModel):
    category: str
    items: list[MarketMover]
    fetched_at: str
```

### Frontend Changes

- **New page or dashboard section: `MarketDiscovery.jsx`** — Tabbed view (Active / Gainers / Losers) with sortable table.
- Each row is clickable → navigates to stock detail or adds to watchlist.
- Auto-refresh every 15 minutes or manual refresh button.

### Cache Strategy
- New key pattern in `quotes_cache`: symbol = `_discovery:active`, `_discovery:gainers`, `_discovery:losers`.
- TTL: 15 minutes (same as quotes).

---

## Feature 4: Calendar

### Problem
No visibility into upcoming market events (earnings dates, dividend ex-dates).

### FMP Data Available

**`obb.equity.calendar.earnings`** — 25 rows, 5 columns:
```
symbol, name, date, eps_estimated, fiscal_date_ending
```

**`obb.equity.calendar.dividend`** — 20 rows, 9 columns:
```
symbol, date, label, adj_dividend, dividend, record_date,
payment_date, declaration_date, ex_dividend_date
```

### Backend Changes

#### `backend/app/lib/openbb.py`

**New function: `get_calendar_events()`**
```python
def get_calendar_events(event_type: str = "earnings", days_ahead: int = 30) -> list[dict]:
    """
    Fetch upcoming calendar events.
    Args:
        event_type: "earnings" | "dividends"
        days_ahead: lookahead window (default 30)
    Returns: list of event dicts
    Cache: DuckDB quotes_cache with key '_calendar:{type}', TTL 1 hour
    """
```

#### New route: `backend/app/routes/market.py`

```
GET /api/market/calendar?type=earnings&days=30
GET /api/market/calendar?type=dividends&days=30
```

**Response:**
```python
class EarningsEvent(BaseModel):
    symbol: str
    name: Optional[str] = None
    date: str
    eps_estimated: Optional[float] = None
    fiscal_date_ending: Optional[str] = None

class DividendEvent(BaseModel):
    symbol: str
    date: str
    ex_dividend_date: Optional[str] = None
    dividend: Optional[float] = None
    payment_date: Optional[str] = None
    declaration_date: Optional[str] = None

class CalendarResponse(BaseModel):
    event_type: str
    events: list[EarningsEvent] | list[DividendEvent]
    fetched_at: str
```

### Frontend Changes

- **New component: `CalendarWidget.jsx`** — Tabbed (Earnings / Dividends) with date-sorted event list.
- Highlight watchlist stocks that appear in upcoming events.
- Countdown badges for events within 7 days.

### Cache Strategy
- Store in `quotes_cache` with keys `_calendar:earnings`, `_calendar:dividends`.
- TTL: 1 hour (events don't change frequently).

---

## New Route Structure

```
backend/app/routes/
├── auth.py              # existing
├── watchlists.py        # existing
├── securities.py        # existing — extended with ohlcv, performance, estimates
├── market.py            # NEW — movers + calendar endpoints
├── chat.py              # existing
├── settings.py          # existing
└── skills.py            # existing
```

---

## DuckDB Cache Table Changes

No new tables needed. Reuse existing tables with key conventions:

| Data | Table | Key Pattern | TTL |
|------|-------|-------------|-----|
| OHLCV | `daily_prices` | `{SYMBOL}` | Append-only, no TTL |
| Performance | `quotes_cache` | `{SYMBOL}:performance` | 15 min |
| Estimates | `fundamentals` | `{SYMBOL}` | 24 hours |
| Discovery | `quotes_cache` | `_discovery:{category}` | 15 min |
| Calendar | `quotes_cache` | `_calendar:{type}` | 1 hour |

---

## Implementation Order

| Step | Feature | Scope | Depends On |
|------|---------|-------|------------|
| 1 | Extended Price (OHLCV + Performance) | Extend existing `openbb.py` + `securities.py` | Nothing |
| 2 | Earnings Estimates | Add to `openbb.py` + extend `securities.py` | Nothing |
| 3 | Market Discovery | New `get_market_movers()` + new `market.py` route | Nothing |
| 4 | Calendar | New `get_calendar_events()` + extend `market.py` | Step 3 (shares route file) |
| 5 | Frontend: Enhanced `PriceChart` + `PerformanceTiles` | OHLCV + Performance components | Step 1 |
| 6 | Frontend: `EstimatesBadge` in `StockRow` | Estimates display | Step 2 |
| 7 | Frontend: `MarketDiscovery` page/section | Discovery UI | Step 3 |
| 8 | Frontend: `CalendarWidget` | Calendar UI | Step 4 |

Steps 1–3 are independent and can be parallelized. Step 4 depends on 3 only for the shared route file.

---

## FMP Tier Limitations

Verified on current FMP API key (free tier). These endpoints are **blocked** (402):

| Endpoint | Error | Notes |
|----------|-------|-------|
| `fundamental.income/balance/cash` with `limit` param | Premium Query Parameter | Works without `limit` (returns 5 periods) |
| `estimates.forward_eps/forward_ebitda` | Premium Query Parameter | Blocked |
| `estimates.price_target` | Restricted Endpoint | Blocked |
| `ownership.insider_trading/institutional/major_holders` | Restricted Endpoint | Blocked |
| `equity.screener` | Restricted Endpoint | Blocked |
| `calendar.ipo` | Restricted Endpoint | Blocked |
| `fundamental.dividends/employee_count/historical_eps` | Premium Query Parameter | Blocked |

**All 4 features in this spec use only free-tier endpoints.**

---

## Open Questions

1. **Market Discovery placement** — New top-level page, or a section within the existing dashboard?
2. **Calendar scope** — Market-wide calendar, or filtered to watchlist symbols only?
3. **OHLCV chart library** — Stick with Recharts (add bar chart for volume), or switch to a candlestick-capable library (e.g., lightweight-charts)?
4. **Performance tiles** — Show in `StockRow` inline, or in the expanded panel below the chart?
