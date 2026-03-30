# Market Data Strategy — Free Provider Coverage

**Date:** 2026-03-28
**Status:** Research complete, pending implementation decisions

---

## 1. Current Data Needs Inventory

Every piece of market data the app fetches today, where it comes from, and whether it works.

### Core Quote & Price Data

| # | Data Need | Backend Function | Current Source | Cache TTL | Status |
|---|-----------|-----------------|----------------|-----------|--------|
| 1 | **Real-time quote** (price, change, change%, volume) | `get_quote()` | OpenBB → FMP `equity.price.quote` | 15 min | **BROKEN** — FMP returns 402 for many symbols |
| 2 | **200-day MA** | `get_ma_200()` | OpenBB → FMP `equity.price.historical` + local compute | Permanent (daily_prices) | Working |
| 3 | **6-month price history** (date + close) | `get_history()` | OpenBB → FMP `equity.price.historical` | Permanent (daily_prices) | Working |
| 4 | **1-year OHLCV** (candlestick data) | `get_ohlcv()` | OpenBB → FMP `equity.price.historical` | Permanent (daily_prices) | Working |
| 5 | **Multi-period performance** (1D–1Y returns) | `get_performance()` | OpenBB → FMP `equity.price.performance` | 15 min | Working |

### Fundamental & Analyst Data

| # | Data Need | Backend Function | Current Source | Cache TTL | Status |
|---|-----------|-----------------|----------------|-----------|--------|
| 6 | **Analyst consensus** (buy/hold/sell, target price) | `get_estimates()` | OpenBB → FMP `equity.estimates.consensus` | 24 hr | Working |
| 7 | **Company fundamentals** (profile + key metrics) | `get_fundamentals()` | Direct FMP `/stable/profile` + `/stable/key-metrics` | 24 hr | Working |
| 8 | **Valuation history** (P/E, P/S, P/B, EV/EBITDA — 5yr) | `get_valuation_history()` | Direct FMP `/stable/ratios` + `/stable/key-metrics` | 24 hr | Working (annual only, limit=5) |
| 9 | **Earnings** (quarterly actuals + forward estimates) | `get_earnings()` | Direct FMP `/stable/income-statement` + `/stable/analyst-estimates` | 24 hr | Working (limit=5) |
| 10 | **Analyst coverage** (consensus + price targets + forward) | `get_analyst_coverage()` | Hybrid: `get_estimates()` + FMP `/stable/price-target-summary` + `/stable/analyst-estimates` | 24 hr | Working |

### Alternative Data

| # | Data Need | Backend Function | Current Source | Cache TTL | Status |
|---|-----------|-----------------|----------------|-----------|--------|
| 11 | **Insider trading** (Form 4 buy/sell) | `get_insider_trading()` | SEC EDGAR direct (XML parsing) | 24 hr | Working |
| 12 | **ETF metrics** (daily/intra returns, ATR, SMA50, RS, ABC) | `etf_engine.fetch_etf_row()` | yfinance (standalone) | On-demand | Working |
| 13 | **ETF holdings** (top 10) | `etf_engine.fetch_etf_holdings_sync()` | yfinance (standalone) | 24 hr | Working |

### Discovery & Calendar

| # | Data Need | Backend Function | Current Source | Cache TTL | Status |
|---|-----------|-----------------|----------------|-----------|--------|
| 14 | **Market movers** (active, gainers, losers) | `get_market_movers()` | OpenBB → FMP `equity.discovery.*` | 15 min | Working |
| 15 | **Calendar events** (earnings dates, dividends) | `get_calendar_events()` | OpenBB → FMP `equity.calendar.*` | 1 hr | Working |

### Background Jobs

| Job | Schedule | What it does |
|-----|----------|-------------|
| `refresh_quotes()` | Every 15 min (market hours) | Calls `get_quote()` for all watchlist symbols |
| `daily_snapshot()` | 6 PM ET weekdays | Calls `get_history()` (12 months) for all watchlist symbols |

### Frontend Consumers

| Component | Data Required | API Call |
|-----------|--------------|----------|
| **StockRow** (compact) | quote, MA200, estimates, performance | `GET /api/securities/{sym}?include=quote,ma200,estimates,performance` |
| **StockRow** (expanded) | + ohlcv | `GET /api/securities/{sym}?include=ohlcv,performance,estimates` |
| **CandlestickChart** | OHLCV bars | Uses ohlcv from above |
| **PerformanceTiles** | 1D/1W/1M/3M/6M/YTD/1Y returns | Uses performance from above |
| **EstimatesBadge** | Consensus type, rating, target | Uses estimates from above |
| **Fundamentals tab** | Profile + key metrics | `GET /api/securities/{sym}/fundamentals` |
| **Earnings tab** | Quarterly actuals + forward | `GET /api/securities/{sym}/earnings` |
| **Analyst tab** | Consensus + targets + forward EPS | `GET /api/securities/{sym}/analyst` |
| **Valuation tab** | Historical P/E, P/S, P/B, EV/EBITDA | `GET /api/securities/{sym}/valuation` |
| **Insider tab** | Recent Form 4 trades + 3mo summary | `GET /api/securities/{sym}/insider-trades` |
| **Discover page** | Gainers, losers, most active | `GET /api/securities/discover/{category}` |

---

## 2. Available Free Providers

### Provider Comparison Matrix

| Provider | API Key | Rate Limit (Free) | Quotes | Historical | Fundamentals | Earnings | Estimates | Insider | Institutional | Discovery |
|----------|---------|-------------------|--------|------------|-------------|----------|-----------|---------|---------------|-----------|
| **yfinance** | None | ~2 req/s (practical) | Yes | Yes (decades) | Yes (4yr annual + quarterly) | Yes | Yes | Yes | Yes | Yes |
| **FMP** | Yes | 250 req/day | Partial (402 on some symbols) | Yes | Yes (limit=5, annual only for ratios) | Yes (limit=5) | Yes | No (402) | No | Yes |
| **SEC EDGAR** | None (User-Agent only) | 10 req/s | No | No | Yes (XBRL 10-K/10-Q) | Yes (from filings) | No | Yes (Form 4) | Yes (13F) | No |
| **Tiingo** | Yes | 50 symbols/hr, ~500 req/day | Yes (IEX real-time) | Yes (30+ years EOD) | Limited | No | No | No | No | No |
| **Alpha Vantage** | Yes | 25 req/day | Yes | Yes | Yes | Yes | No | No | No | No |
| **Polygon** | Yes | 5 req/min (EOD only) | No (EOD only) | Yes | Limited | No | No | No | No | No |

### Key Insight

**yfinance is already a dependency** (used in `etf_engine.py`) but only for ETF data. It provides virtually everything FMP's free tier restricts — quarterly ratios, full earnings history, analyst targets, insider transactions, institutional holdings — with zero API key and zero daily request cap.

The practical risk (Yahoo blocking) is mitigated by:
- DuckDB cache layer (15-min quotes, 24-hr fundamentals)
- Desktop app = single user, not server-scale traffic
- Adding small delays between bulk fetches

---

## 3. Recommended Provider Hierarchy

### By Data Type

| Data Need | Primary | Fallback 1 | Fallback 2 | Notes |
|-----------|---------|------------|------------|-------|
| **Quotes** | yfinance | FMP `/stable/profile` | Tiingo IEX | yfinance `.fast_info` is lightweight; FMP profile has price/change/volume |
| **Historical OHLCV** | yfinance | FMP via OpenBB | Tiingo | yfinance has decades of data, all intervals |
| **Performance (multi-period)** | Compute from cached OHLCV | FMP via OpenBB | — | Can self-compute 1D/1W/1M/etc. from daily_prices cache |
| **200-day MA** | Compute from cached OHLCV | — | — | Already self-computed, just needs OHLCV data |
| **Fundamentals (profile)** | FMP `/stable/profile` | yfinance `.info` | — | FMP profile works on free tier for all symbols |
| **Fundamentals (ratios)** | yfinance `.info` | FMP `/stable/key-metrics` | — | yfinance has PE, PB, PS etc. in `.info`; FMP limited to annual, limit=5 |
| **Valuation history** | yfinance quarterly financials + compute | FMP `/stable/ratios` | — | Compute P/E etc. from price + EPS over time |
| **Earnings (quarterly)** | yfinance `.quarterly_income_stmt` | FMP `/stable/income-statement` | SEC EDGAR 10-Q | yfinance has 4-8 quarters; FMP capped at 5 |
| **Earnings (forward estimates)** | yfinance `.earnings_estimate` + `.revenue_estimate` | FMP `/stable/analyst-estimates` | — | yfinance has current/next quarter and year estimates |
| **Analyst consensus** | yfinance `.recommendations` | FMP `estimates.consensus` | — | yfinance gives firm-level buy/hold/sell history |
| **Analyst price targets** | yfinance `.analyst_price_targets` | FMP `/stable/price-target-summary` | — | yfinance: current/low/high/mean/median |
| **Insider trading** | SEC EDGAR Form 4 (current impl) | yfinance `.insider_transactions` | — | EDGAR is authoritative; yfinance as simpler fallback |
| **Institutional holdings** | yfinance `.institutional_holders` | SEC EDGAR 13F | — | Not currently implemented — free to add |
| **Discovery (movers)** | FMP via OpenBB | yfinance via OpenBB | — | Both work; FMP currently integrated |
| **Calendar (earnings dates)** | yfinance `.earnings_dates` | FMP via OpenBB | — | yfinance more reliable for dates |
| **ETF metrics** | yfinance (current impl) | — | — | Already working |

### The Strategy in One Sentence

> **yfinance primary for quotes + fundamentals + earnings + estimates, FMP for profile/discovery where it's reliable, SEC EDGAR for insider/institutional filings, self-compute performance metrics from cached OHLCV.**

---

## 4. Architecture Assessment

### What We Have Today

```
Frontend → Backend API routes → openbb.py functions → { OpenBB SDK, _fmp_get(), SEC EDGAR }
                                                            ↓
                                                     DuckDB Cache Layer
```

**Current architecture does NOT have fallback support.** Each `get_*()` function calls one source. If it fails, it raises an exception. There's no retry-with-different-provider logic.

### What We Need

```
Frontend → Backend API routes → openbb.py functions → Provider Chain
                                                        ├─ Try: yfinance
                                                        ├─ Fallback: FMP
                                                        └─ Fallback: SEC EDGAR
                                                            ↓
                                                     DuckDB Cache Layer
```

### Proposed Architecture Pattern

```python
def get_quote(symbol: str) -> dict:
    """Fetch quote with provider fallback chain."""
    cached = _try_cached_quote(symbol)
    if cached is not None:
        return cached

    providers = [
        ("yfinance", _get_quote_yfinance),
        ("fmp", _get_quote_fmp),
    ]

    last_error = None
    for name, fetch_fn in providers:
        try:
            data = fetch_fn(symbol)
            _try_cache_quote(symbol, data)
            return data
        except Exception as e:
            logger.warning(f"Quote from {name} failed for {symbol}: {e}")
            last_error = e

    raise SymbolNotFoundError(f"All providers failed for {symbol}: {last_error}")
```

This pattern:
- Keeps the DuckDB cache as first check (no change)
- Tries providers in priority order
- Logs which provider failed and why
- Only raises SymbolNotFoundError if ALL providers fail
- Easy to add/remove/reorder providers

### Implementation Scope

Each `get_*()` function needs a provider-specific fetch function:

| Function | yfinance impl needed | FMP impl exists | SEC impl exists |
|----------|---------------------|-----------------|-----------------|
| `get_quote` | New: `_get_quote_yfinance()` | Refactor existing | — |
| `get_history` / `get_ohlcv` | New: `_get_ohlcv_yfinance()` | Existing (OpenBB) | — |
| `get_performance` | New: compute from OHLCV cache | Existing (OpenBB) | — |
| `get_estimates` | New: `_get_estimates_yfinance()` | Existing (OpenBB) | — |
| `get_fundamentals` | New: `_get_fundamentals_yfinance()` | Existing (_fmp_get) | — |
| `get_valuation_history` | New: `_get_valuation_yfinance()` | Existing (_fmp_get) | — |
| `get_earnings` | New: `_get_earnings_yfinance()` | Existing (_fmp_get) | — |
| `get_analyst_coverage` | New: `_get_analyst_yfinance()` | Existing (hybrid) | — |
| `get_insider_trading` | — | — | Existing (EDGAR) |

### Dependencies

yfinance is already installed (used by `etf_engine.py`). No new packages needed.

---

## 5. Known Issues to Fix

| Issue | Impact | Root Cause | Fix |
|-------|--------|-----------|-----|
| `get_quote()` returns 402 for many symbols | **All prices show $0** | FMP `equity.price.quote` restricted on free plan | Switch to yfinance primary |
| All errors become `SymbolNotFoundError` | API failures treated as invalid symbol | `openbb.py` catch-all converts all exceptions | Separate error types, add fallback |
| `addStock()` doesn't check `stockRes.ok` | Stock added but shows no data | Missing response status check | Already fixed (this session) |
| Delete button doesn't work | Can't remove watchlists | Missing `e.stopPropagation()` in Link | Already fixed (this session) |
| `get_analyst_coverage()` defined twice | Code duplication | Copy-paste | Remove duplicate |
| No force-refresh bypass | Refresh button retries same failing source | No cache bypass mechanism | Add `?force=true` query param |
| `get_performance()` external dependency | Could self-compute | Uses FMP endpoint unnecessarily | Compute from cached daily_prices |

---

## 6. Open Questions

1. **Tiingo as tertiary fallback?** — Free tier is decent (50 symbols/hr, IEX real-time quotes). Worth adding a Tiingo API key for redundancy? Or keep it simple with yfinance + FMP?

2. **Self-compute performance?** — We have daily_prices in DuckDB. We could compute 1D/1W/1M/3M/6M/YTD/1Y returns ourselves instead of calling an external API. Eliminates a dependency but adds computation logic.

3. **Institutional holdings?** — yfinance provides `.institutional_holders` for free. Do we want to add this as a new tab? It's zero-cost data.

4. **Migration order** — Should we migrate all functions at once, or start with `get_quote()` (the broken one) and add yfinance incrementally?
