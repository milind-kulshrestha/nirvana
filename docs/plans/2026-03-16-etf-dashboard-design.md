# ETF Dashboard — Design

**Date:** 2026-03-16
**Status:** Approved

## Overview

New dedicated ETF Dashboard page at `/etf` — a pre-built screener for ~180 ETFs across 6 preset categories (Indices, S&P Style, Sectors, EW Sectors, Industries, Countries) plus a user-extensible Custom group. Data fetched from Yahoo Finance (yfinance), refreshed manually by the user, cached in DuckDB.

## Architecture

```
User opens /etf
    → GET /api/etf/snapshot  → DuckDB cache hit → render immediately
                              → cache miss      → show empty state + "Refresh" prompt

User clicks Refresh
    → POST /api/etf/refresh  → yfinance fetch (180 ETFs + custom)
                             → SSE progress stream (per-ETF updates)
                             → writes to DuckDB etf_snapshot table
                             → frontend re-fetches on complete

User adds custom ETF
    → POST /api/etf/custom/{symbol}  → stored in SQLite
    → included in next Refresh run
```

## New Files

| File | Purpose |
|------|---------|
| `backend/app/lib/etf_engine.py` | yfinance fetch + ABC/ATR/VARS computation (ported from market_dashboard build_data.py) |
| `backend/app/routes/etf.py` | API endpoints |
| `frontend/src/pages/ETFDashboard.jsx` | New page component |
| `frontend/src/stores/etfStore.js` | Zustand store for ETF state |

## Reused Infrastructure

- DuckDB (`market_cache.py` pattern) for ETF snapshot storage
- SQLite + SQLAlchemy for user's custom ETF list
- SSE pattern from chat for refresh progress

## API Endpoints

```
GET    /api/etf/snapshot          # Full cached snapshot (all groups + metrics)
POST   /api/etf/refresh           # SSE stream — triggers yfinance fetch, emits progress
GET    /api/etf/holdings/{symbol} # Top 10 holdings (lazy, 24h TTL)
GET    /api/etf/custom            # User's custom ETF symbols
POST   /api/etf/custom/{symbol}   # Add symbol to custom group
DELETE /api/etf/custom/{symbol}   # Remove from custom group
```

## Data Schema

### Snapshot Response

```json
{
  "built_at": "2026-03-16T20:30:00Z",
  "groups": {
    "Indices": [
      {
        "ticker": "SPY",
        "daily": 0.4, "intra": 0.1, "5d": 1.2, "20d": 3.1,
        "atr_pct": 0.9, "dist_sma50_atr": 1.3,
        "rs": 72, "abc": "A",
        "long": ["SPXL", "UPRO"], "short": ["SPXS", "SH"],
        "rrs_chart": [0.1, 0.2, -0.1, ...]
      }
    ],
    "Custom": []
  },
  "column_ranges": {
    "Indices": { "daily": [-2.1, 1.8], "intra": [-1.2, 0.9], "5d": [-5.0, 4.2], "20d": [-8.0, 7.1] }
  }
}
```

**Key design decision:** RS sparkline data sent as raw `rrs_chart` float array (20 values) instead of PNG — rendered client-side as inline SVG. Eliminates matplotlib dependency and file I/O.

### DuckDB Tables

```sql
-- ETF metrics snapshot (wiped + rewritten on each refresh)
CREATE TABLE IF NOT EXISTS etf_snapshot (
  symbol        TEXT,
  group_name    TEXT,
  built_at      TIMESTAMP,
  daily         REAL,
  intra         REAL,
  d5            REAL,
  d20           REAL,
  atr_pct       REAL,
  dist_sma50_atr REAL,
  rs            REAL,
  abc           TEXT,
  long_etfs     TEXT,   -- JSON array string
  short_etfs    TEXT,   -- JSON array string
  rrs_chart     TEXT    -- JSON array string (20 floats)
);

-- ETF holdings cache (lazy, per-symbol, 24h TTL)
CREATE TABLE IF NOT EXISTS etf_holdings (
  symbol      TEXT PRIMARY KEY,
  data        TEXT,       -- JSON: [{"symbol": "AAPL", "weight": 0.072}, ...]
  fetched_at  TIMESTAMP
);
```

### SQLite Model

New `EtfCustomSymbol` SQLAlchemy model:

```python
class EtfCustomSymbol(Base):
    __tablename__ = "etf_custom_symbols"
    symbol    = Column(String, primary_key=True)
    added_at  = Column(DateTime, default=datetime.utcnow)
```

## etf_engine.py — Porting Strategy

From `market_dashboard/scripts/build_data.py`:

| Keep verbatim | Change |
|---------------|--------|
| `STOCK_GROUPS` dict | — |
| `LEVERAGED_ETFS` dict | — |
| `calculate_abc_rating()` | — |
| `calculate_atr()` | — |
| `calculate_rrs()` | — |
| `calculate_sma/ema()` | — |
| `get_stock_data()` | Remove chart file I/O; return `rrs_chart` list instead |
| `create_rs_chart_png()` | **Replace** with `get_rrs_chart_data()` → `list[float]` (20 values) |
| `fetch_etf_holdings()` | Keep logic; write to DuckDB instead of JSON files |

yfinance is synchronous — wrap calls in `asyncio.to_thread()` for FastAPI async compatibility.

## SSE Refresh Events

```python
{ "type": "progress", "symbol": "SPY",  "done": 12,  "total": 180 }
{ "type": "error",    "symbol": "XYZ",  "msg": "no data" }
{ "type": "complete", "built_at": "2026-03-16T20:31:00Z" }
```

## Frontend — Page Layout

```
ETFDashboard.jsx
├── Header bar
│   ├── Title "ETF Dashboard"
│   ├── Last updated timestamp
│   └── [Refresh] button + progress bar during refresh
│
├── Category tabs
│   └── Indices | S&P Style | Sectors | EW Sectors | Industries | Countries | Custom
│
└── ETFTable.jsx (per group)
    ├── Sortable columns: Ticker | ABC | Daily | Intra | 5D | 20D | ATR% | ATRx | VARS | Chart
    ├── Color-coded cells (green/red heatmap bars, ABC dot badges: blue=A, green=B, amber=C)
    ├── RS sparkline SVG inline per row (20-bar chart, yellow SMA line)
    ├── Long/Short leveraged ETF chips (clickable → highlight that symbol)
    └── Holdings popover on [H] click — top 10 holdings with weight bars
```

**Custom tab:** Input + button at bottom: `[SYMBOL___] [+ Add]`. Symbol validated on next Refresh.

**Navigation:** "ETF" link in sidebar between Watchlists and Discover.

## Zustand Store (etfStore.js)

```js
{
  snapshot: null,       // full snapshot object
  status: 'idle',       // 'idle' | 'loading' | 'refreshing' | 'error'
  progress: { done: 0, total: 0, current: '' },
  customSymbols: [],    // fetched from API
}
```

No localStorage persistence — snapshot lives in DuckDB.

## Out of Scope

- Automatic scheduled refresh (manual only)
- TradingView chart integration in this page (existing chart panel handles individual tickers)
- Economic calendar widget (already on Discover page)
- Market breadth widget
