# Stock Detail Tabs Expansion Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 5 new tabs to the stock detail expanded panel: Fundamentals, Earnings, Analyst Coverage, Valuation, and Sentiment.

**Architecture:** Each tab follows the lazy-load pattern established by Insider Trades — backend endpoint with DuckDB cache, frontend component receiving data as props, wired into StockRow.jsx with on-demand fetching when the tab is selected. All FMP data fetched via direct `httpx` calls (not OpenBB wrappers) for consistent error handling and to work around OpenBB limit=1 restrictions.

**Tech Stack:** FastAPI + httpx (backend), React + Recharts + lightweight-charts (frontend), DuckDB (cache), FMP stable API + StockTwits API (data sources)

---

## Data Source Availability (FMP Plan)

Verified on 2026-03-24 against current FMP subscription:

| Endpoint | Status | Notes |
|----------|--------|-------|
| `/stable/profile?symbol=X` | OK | Company info, market cap, sector |
| `/stable/income-statement?symbol=X&period=quarter&limit=5` | OK | Quarterly revenue, EPS |
| `/stable/ratios?symbol=X&limit=5` | OK | **Annual only**, P/E, P/S, P/B |
| `/stable/key-metrics?symbol=X&limit=5` | OK | **Annual only**, EV/EBITDA, ROE |
| `/stable/analyst-estimates?symbol=X&period=annual&limit=5` | OK | Forward revenue/EPS estimates |
| `/stable/price-target-summary?symbol=X` | OK | Aggregated analyst price targets |
| `obb.equity.estimates.consensus(symbol, provider="fmp")` | OK | Already used for EstimatesBadge |
| StockTwits `/api/2/streams/symbol/X.json` | OK | Free, no auth, 200 req/hr |
| `/stable/earning-surprises` | 404 | Not available |
| `/stable/ratios` (quarterly) | 402 | Premium only |
| `/stable/key-metrics` (quarterly) | 402 | Premium only |
| `obb.equity.fundamental.historical_eps` | 402 | Premium only |
| `obb.equity.estimates.price_target` | 402 | Premium only |

---

## Existing Code Reference

**Pattern to follow (Insider Trades):**
- Backend fetch: `backend/app/lib/openbb.py` → `get_insider_trading()` (cache-first → API → cache-write)
- Backend route: `backend/app/routes/securities.py` → `GET /{symbol}/insider-trades`
- Frontend component: `frontend/src/components/InsiderTrades.jsx` (pure, receives `data` prop)
- Tab integration: `frontend/src/components/StockRow.jsx` (lazy fetch on tab select)

**Existing unused components to replace/update:**
- `frontend/src/components/ValuationChart.jsx` — renders P/E, P/B, P/S line charts (Recharts). Will be updated for new data shape.
- `frontend/src/components/StockAnalytics.jsx` — standalone analytics container. Won't be used (tabs live in StockRow instead).

**FMP API helper:** All new backend functions will use a shared `_fmp_get()` helper for direct FMP stable API calls with API key from config, consistent error handling, and timeout.

---

## Task 0: FMP API Helper

**Files:**
- Modify: `backend/app/lib/openbb.py`

Add a reusable helper for direct FMP stable API calls, following the pattern already used for SEC EDGAR (`httpx` + config-based API key).

**Step 1: Write the helper function**

Add to `backend/app/lib/openbb.py` after the SEC EDGAR helpers section:

```python
# ---------------------------------------------------------------------------
# Direct FMP API helpers
# ---------------------------------------------------------------------------

def _fmp_get(path: str, params: dict | None = None) -> list | dict:
    """GET from FMP stable API with API key from config.

    Args:
        path: URL path after /stable/ (e.g. "profile")
        params: Query params (symbol, limit, period, etc.)

    Returns:
        Parsed JSON response (list or dict).

    Raises:
        SymbolNotFoundError: on 404 or empty response.
        OpenBBTimeoutError: on timeout.
    """
    from app.lib.config_manager import get_config
    api_key = get_config().get("fmp_api_key", "")
    if not api_key:
        raise SymbolNotFoundError("FMP API key not configured")

    url = f"https://financialmodelingprep.com/stable/{path}"
    all_params = {**(params or {}), "apikey": api_key}

    try:
        resp = httpx.get(url, params=all_params, timeout=10)
        if resp.status_code == 402:
            raise SymbolNotFoundError(f"FMP endpoint restricted: {path}")
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and len(data) == 0:
            raise SymbolNotFoundError(f"No data from FMP for {path}")
        return data
    except httpx.TimeoutException:
        raise OpenBBTimeoutError(f"FMP timeout: {path}")
    except (SymbolNotFoundError, OpenBBTimeoutError):
        raise
    except Exception as e:
        raise SymbolNotFoundError(f"FMP error for {path}: {e}")
```

**Step 2: Verify the helper works**

```bash
cd backend && python -c "
from app.lib.openbb import _fmp_get
data = _fmp_get('profile', {'symbol': 'AAPL'})
print(type(data), len(data) if isinstance(data, list) else 'dict')
"
```

**Step 3: Commit**

```bash
git add backend/app/lib/openbb.py
git commit -m "feat: add _fmp_get helper for direct FMP stable API calls"
```

---

## Task 1: Fundamentals Tab

**Goal:** Show company overview and key financial metrics in a clean grid layout.

**Data source:** `/stable/profile` + `/stable/key-metrics?limit=1`

**Files:**
- Modify: `backend/app/lib/openbb.py` — add `get_fundamentals()`
- Modify: `backend/app/routes/securities.py` — add `GET /{symbol}/fundamentals`
- Create: `frontend/src/components/Fundamentals.jsx`
- Modify: `frontend/src/components/StockRow.jsx` — add tab

### Backend

**Step 1: Add `get_fundamentals()` to openbb.py**

```python
def get_fundamentals(symbol: str) -> dict:
    """Fetch company profile + key metrics. Cache 24h."""
    cache_key = f"{symbol.upper()}:fundamentals"

    try:
        from app.lib.market_cache import get_cached_fundamentals
        cached = get_cached_fundamentals(cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache read failed for fundamentals %s", symbol)

    profile = _fmp_get("profile", {"symbol": symbol})
    metrics = _fmp_get("key-metrics", {"symbol": symbol, "limit": 1})

    p = profile[0] if isinstance(profile, list) else profile
    m = metrics[0] if isinstance(metrics, list) else metrics

    result = {
        "company_name": p.get("companyName"),
        "sector": p.get("sector"),
        "industry": p.get("industry"),
        "description": p.get("description"),
        "ceo": p.get("ceo"),
        "employees": p.get("fullTimeEmployees"),
        "website": p.get("website"),
        "market_cap": m.get("marketCap"),
        "enterprise_value": m.get("enterpriseValue"),
        "pe_ratio": m.get("peRatio"),  # from key-metrics or profile
        "ev_to_ebitda": m.get("evToEBITDA"),
        "ev_to_sales": m.get("evToSales"),
        "roe": m.get("returnOnEquity"),
        "roa": m.get("returnOnAssets"),
        "roic": m.get("returnOnInvestedCapital"),
        "current_ratio": m.get("currentRatio"),
        "debt_to_equity": None,  # from ratios if needed
        "revenue_per_share": m.get("revenuePerShare") if "revenuePerShare" in m else None,
        "free_cash_flow_yield": m.get("freeCashFlowYield"),
        "dividend_yield": p.get("lastDividend"),
        "beta": p.get("beta"),
        "52w_range": p.get("range"),
    }

    try:
        from app.lib.market_cache import cache_fundamentals
        cache_fundamentals(cache_key, result)
    except Exception:
        logger.debug("Cache write failed for fundamentals %s", symbol)

    return result
```

**Step 2: Add route to securities.py**

```python
@router.get("/{symbol}/fundamentals")
async def get_fundamentals_route(symbol: str):
    """Get company fundamentals (profile + key metrics)."""
    symbol = symbol.upper()
    try:
        data = get_fundamentals(symbol)
        return data
    except (SymbolNotFoundError, OpenBBTimeoutError) as e:
        raise HTTPException(status_code=404, detail=str(e))
```

Add `get_fundamentals` to the imports from `app.lib.openbb`.

**Step 3: Commit backend**

```bash
git add backend/app/lib/openbb.py backend/app/routes/securities.py
git commit -m "feat: add GET /{symbol}/fundamentals endpoint with profile + key metrics"
```

### Frontend

**Step 4: Create `Fundamentals.jsx`**

Display a company header (name, sector, description) + a 3-column metrics grid. Format large numbers ($B, $M), percentages, and ratios.

```jsx
// frontend/src/components/Fundamentals.jsx
export default function Fundamentals({ data }) {
  if (!data) {
    return <div className="text-center text-muted-foreground py-8">No fundamentals data available</div>;
  }

  const fmt = (v, type) => {
    if (v == null) return '—';
    if (type === 'dollar') {
      if (Math.abs(v) >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
      if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
      if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
      return `$${v.toFixed(2)}`;
    }
    if (type === 'pct') return `${(v * 100).toFixed(1)}%`;
    if (type === 'ratio') return v.toFixed(2);
    if (type === 'int') return v.toLocaleString();
    return String(v);
  };

  const metrics = [
    { label: 'Market Cap', value: fmt(data.market_cap, 'dollar') },
    { label: 'Enterprise Value', value: fmt(data.enterprise_value, 'dollar') },
    { label: 'P/E Ratio', value: fmt(data.pe_ratio, 'ratio') },
    { label: 'EV/EBITDA', value: fmt(data.ev_to_ebitda, 'ratio') },
    { label: 'EV/Sales', value: fmt(data.ev_to_sales, 'ratio') },
    { label: 'ROE', value: fmt(data.roe, 'pct') },
    { label: 'ROA', value: fmt(data.roa, 'pct') },
    { label: 'ROIC', value: fmt(data.roic, 'pct') },
    { label: 'Current Ratio', value: fmt(data.current_ratio, 'ratio') },
    { label: 'FCF Yield', value: fmt(data.free_cash_flow_yield, 'pct') },
    { label: 'Beta', value: fmt(data.beta, 'ratio') },
    { label: '52W Range', value: data['52w_range'] || '—' },
  ];

  return (
    <div className="space-y-4">
      {/* Company Header */}
      {data.description && (
        <p className="text-sm text-muted-foreground line-clamp-3">{data.description}</p>
      )}
      <div className="flex gap-4 text-xs text-muted-foreground">
        {data.sector && <span>{data.sector}</span>}
        {data.industry && <span>• {data.industry}</span>}
        {data.employees && <span>• {data.employees.toLocaleString()} employees</span>}
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
        {metrics.map(({ label, value }) => (
          <div key={label} className="bg-muted/50 rounded-lg p-2.5">
            <div className="text-xs text-muted-foreground">{label}</div>
            <div className="text-sm font-semibold font-mono text-foreground">{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 5: Wire into StockRow.jsx**

Add state, fetch function, tab trigger, and tab content following the insider trades pattern. (See Task 6 for full integration of all tabs.)

**Step 6: Commit frontend**

```bash
git add frontend/src/components/Fundamentals.jsx
git commit -m "feat: add Fundamentals component with company profile and metrics grid"
```

---

## Task 2: Earnings Tab

**Goal:** Show quarterly EPS trend (last 8 quarters from income statements) + forward annual estimates.

**Data sources:**
- `/stable/income-statement?symbol=X&period=quarter&limit=8` — actual quarterly EPS
- `/stable/analyst-estimates?symbol=X&period=annual&limit=3` — forward estimates

**Note:** `earning-surprises` endpoint returns 404 on current FMP plan, so we cannot show beat/miss data directly. Instead we show the EPS trajectory and forward analyst consensus.

**Files:**
- Modify: `backend/app/lib/openbb.py` — add `get_earnings()`
- Modify: `backend/app/routes/securities.py` — add `GET /{symbol}/earnings`
- Create: `frontend/src/components/Earnings.jsx`

### Backend

**Step 1: Add `get_earnings()` to openbb.py**

```python
def get_earnings(symbol: str) -> dict:
    """Fetch quarterly EPS history + forward annual estimates. Cache 24h."""
    cache_key = f"{symbol.upper()}:earnings"

    try:
        from app.lib.market_cache import get_cached_fundamentals
        cached = get_cached_fundamentals(cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache read failed for earnings %s", symbol)

    # Quarterly actuals from income statement
    quarterly = []
    try:
        data = _fmp_get("income-statement", {
            "symbol": symbol, "period": "quarter", "limit": 8,
        })
        for q in data:
            quarterly.append({
                "date": q.get("date"),
                "period": q.get("period"),         # Q1, Q2, Q3, Q4
                "fiscal_year": q.get("fiscalYear"),
                "revenue": q.get("revenue"),
                "net_income": q.get("netIncome"),
                "eps": q.get("eps"),
                "eps_diluted": q.get("epsDiluted"),
            })
    except (SymbolNotFoundError, OpenBBTimeoutError):
        pass

    # Forward annual estimates
    forward = []
    try:
        data = _fmp_get("analyst-estimates", {
            "symbol": symbol, "period": "annual", "limit": 3,
        })
        for est in data:
            forward.append({
                "date": est.get("date"),
                "revenue_avg": est.get("revenueAvg"),
                "revenue_low": est.get("revenueLow"),
                "revenue_high": est.get("revenueHigh"),
                "eps_avg": est.get("epsAvg"),
                "eps_low": est.get("epsLow"),
                "eps_high": est.get("epsHigh"),
                "ebitda_avg": est.get("ebitdaAvg"),
                "net_income_avg": est.get("netIncomeAvg"),
            })
    except (SymbolNotFoundError, OpenBBTimeoutError):
        pass

    result = {"quarterly": quarterly, "forward": forward}

    try:
        from app.lib.market_cache import cache_fundamentals
        cache_fundamentals(cache_key, result)
    except Exception:
        logger.debug("Cache write failed for earnings %s", symbol)

    return result
```

**Step 2: Add route**

```python
@router.get("/{symbol}/earnings")
async def get_earnings_route(symbol: str):
    """Get quarterly EPS history + forward estimates."""
    symbol = symbol.upper()
    try:
        data = get_earnings(symbol)
        return data
    except (SymbolNotFoundError, OpenBBTimeoutError) as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Step 3: Commit backend**

```bash
git add backend/app/lib/openbb.py backend/app/routes/securities.py
git commit -m "feat: add GET /{symbol}/earnings endpoint with quarterly EPS + forward estimates"
```

### Frontend

**Step 4: Create `Earnings.jsx`**

Show:
1. **EPS bar chart** — last 8 quarters, bars colored by QoQ growth direction
2. **Forward estimates table** — next 3 fiscal years with revenue/EPS ranges

```jsx
// frontend/src/components/Earnings.jsx
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

export default function Earnings({ data }) {
  if (!data) {
    return <div className="text-center text-muted-foreground py-8">No earnings data available</div>;
  }

  const { quarterly = [], forward = [] } = data;

  // Reverse so oldest first for chart
  const chartData = [...quarterly].reverse().map(q => ({
    label: `${q.period} ${q.fiscal_year}`,
    eps: q.eps_diluted ?? q.eps,
    revenue: q.revenue,
  }));

  const fmt = (v) => {
    if (v == null) return '—';
    if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
    if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
    return `$${v.toFixed(2)}`;
  };

  return (
    <div className="space-y-6">
      {/* Quarterly EPS Chart */}
      {chartData.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-foreground mb-2">Quarterly EPS (Diluted)</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} />
              <YAxis tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                     tickFormatter={v => `$${v.toFixed(2)}`} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                  color: 'hsl(var(--foreground))',
                }}
                formatter={(value) => [`$${value?.toFixed(2)}`, 'EPS']}
              />
              <Bar dataKey="eps" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={entry.eps >= 0 ? 'hsl(var(--success))' : 'hsl(var(--destructive))'}
                    fillOpacity={0.8}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Forward Estimates Table */}
      {forward.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-foreground mb-2">Forward Estimates (Annual)</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-muted-foreground text-left">
                  <th className="pb-2 font-medium">FY</th>
                  <th className="pb-2 font-medium">Revenue</th>
                  <th className="pb-2 font-medium">EPS</th>
                  <th className="pb-2 font-medium">EBITDA</th>
                </tr>
              </thead>
              <tbody>
                {forward.map((est) => (
                  <tr key={est.date} className="border-b border-border/50">
                    <td className="py-2 font-mono text-foreground">{est.date?.slice(0, 4)}</td>
                    <td className="py-2 font-mono">{fmt(est.revenue_avg)}</td>
                    <td className="py-2 font-mono">
                      {est.eps_avg != null ? `$${est.eps_avg.toFixed(2)}` : '—'}
                      {est.eps_low != null && est.eps_high != null && (
                        <span className="text-xs text-muted-foreground ml-1">
                          ({`$${est.eps_low.toFixed(2)}–$${est.eps_high.toFixed(2)}`})
                        </span>
                      )}
                    </td>
                    <td className="py-2 font-mono">{fmt(est.ebitda_avg)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {quarterly.length === 0 && forward.length === 0 && (
        <div className="text-center text-muted-foreground py-8">No earnings data available</div>
      )}
    </div>
  );
}
```

**Step 5: Commit frontend**

```bash
git add frontend/src/components/Earnings.jsx
git commit -m "feat: add Earnings component with quarterly EPS chart and forward estimates table"
```

---

## Task 3: Analyst Coverage Tab

**Goal:** Show analyst consensus summary, price target distribution, and forward revenue/EPS estimates.

**Data sources:**
- `obb.equity.estimates.consensus()` — already implemented as `get_estimates()`
- `/stable/price-target-summary?symbol=X` — aggregated price target stats
- `/stable/analyst-estimates?symbol=X&period=annual&limit=3` — reuse from earnings

**Files:**
- Modify: `backend/app/lib/openbb.py` — add `get_analyst_coverage()`
- Modify: `backend/app/routes/securities.py` — add `GET /{symbol}/analyst`
- Create: `frontend/src/components/AnalystCoverage.jsx`

### Backend

**Step 1: Add `get_analyst_coverage()` to openbb.py**

```python
def get_analyst_coverage(symbol: str) -> dict:
    """Fetch analyst consensus + price targets + forward estimates. Cache 24h."""
    cache_key = f"{symbol.upper()}:analyst"

    try:
        from app.lib.market_cache import get_cached_fundamentals
        cached = get_cached_fundamentals(cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache read failed for analyst %s", symbol)

    # Consensus (reuse existing function)
    consensus = {}
    try:
        consensus = get_estimates(symbol)
    except (SymbolNotFoundError, OpenBBTimeoutError):
        pass

    # Price target summary
    price_targets = {}
    try:
        data = _fmp_get("price-target-summary", {"symbol": symbol})
        pt = data[0] if isinstance(data, list) and data else data
        price_targets = {
            "last_month_count": pt.get("lastMonthCount"),
            "last_month_avg": pt.get("lastMonthAvgPriceTarget"),
            "last_quarter_count": pt.get("lastQuarterCount"),
            "last_quarter_avg": pt.get("lastQuarterAvgPriceTarget"),
            "last_year_count": pt.get("lastYearCount"),
            "last_year_avg": pt.get("lastYearAvgPriceTarget"),
            "all_time_count": pt.get("allTimeCount"),
            "all_time_avg": pt.get("allTimeAvgPriceTarget"),
        }
    except (SymbolNotFoundError, OpenBBTimeoutError):
        pass

    # Forward estimates (same data as earnings, but focused on revenue/eps ranges)
    forward = []
    try:
        data = _fmp_get("analyst-estimates", {
            "symbol": symbol, "period": "annual", "limit": 3,
        })
        for est in data:
            forward.append({
                "date": est.get("date"),
                "revenue_avg": est.get("revenueAvg"),
                "revenue_low": est.get("revenueLow"),
                "revenue_high": est.get("revenueHigh"),
                "eps_avg": est.get("epsAvg"),
                "eps_low": est.get("epsLow"),
                "eps_high": est.get("epsHigh"),
                "num_analysts_revenue": est.get("numberOfAnalystsRevenue"),
                "num_analysts_eps": est.get("numberOfAnalystsEPS"),
            })
    except (SymbolNotFoundError, OpenBBTimeoutError):
        pass

    result = {
        "consensus": consensus,
        "price_targets": price_targets,
        "forward_estimates": forward,
    }

    try:
        from app.lib.market_cache import cache_fundamentals
        cache_fundamentals(cache_key, result)
    except Exception:
        logger.debug("Cache write failed for analyst %s", symbol)

    return result
```

**Step 2: Add route**

```python
@router.get("/{symbol}/analyst")
async def get_analyst_route(symbol: str):
    """Get analyst coverage: consensus, price targets, forward estimates."""
    symbol = symbol.upper()
    try:
        data = get_analyst_coverage(symbol)
        return data
    except (SymbolNotFoundError, OpenBBTimeoutError) as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Step 3: Commit backend**

```bash
git add backend/app/lib/openbb.py backend/app/routes/securities.py
git commit -m "feat: add GET /{symbol}/analyst endpoint with consensus + price targets"
```

### Frontend

**Step 4: Create `AnalystCoverage.jsx`**

Show:
1. **Consensus badge** — rating type (Buy/Hold/Sell) + numeric score
2. **Price target summary** — current price vs average target, with last month/quarter/year counts
3. **Forward estimates** — compact table

```jsx
// frontend/src/components/AnalystCoverage.jsx
export default function AnalystCoverage({ data, currentPrice }) {
  if (!data) {
    return <div className="text-center text-muted-foreground py-8">No analyst data available</div>;
  }

  const { consensus = {}, price_targets: pt = {}, forward_estimates: fwd = [] } = data;

  const ratingColor = {
    'Strong Buy': 'text-success', 'Buy': 'text-success',
    'Hold': 'text-warning',
    'Sell': 'text-destructive', 'Strong Sell': 'text-destructive',
  };

  const fmt = (v) => {
    if (v == null) return '—';
    if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
    return `$${v.toFixed(2)}`;
  };

  const upside = pt.last_year_avg && currentPrice
    ? ((pt.last_year_avg - currentPrice) / currentPrice * 100).toFixed(1)
    : null;

  return (
    <div className="space-y-5">
      {/* Consensus + Price Target Row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Consensus */}
        <div className="bg-muted/50 rounded-lg p-3">
          <div className="text-xs text-muted-foreground mb-1">Consensus Rating</div>
          <div className={`text-lg font-bold ${ratingColor[consensus.consensus_type] || 'text-foreground'}`}>
            {consensus.consensus_type || '—'}
          </div>
          {consensus.consensus_rating && (
            <div className="text-xs text-muted-foreground">
              Score: {consensus.consensus_rating.toFixed(2)} / 5
            </div>
          )}
        </div>

        {/* Price Target */}
        <div className="bg-muted/50 rounded-lg p-3">
          <div className="text-xs text-muted-foreground mb-1">Avg Price Target</div>
          <div className="text-lg font-bold font-mono text-foreground">
            {pt.last_year_avg ? `$${pt.last_year_avg.toFixed(2)}` : '—'}
          </div>
          {upside && (
            <div className={`text-xs font-medium ${parseFloat(upside) >= 0 ? 'text-success' : 'text-destructive'}`}>
              {parseFloat(upside) >= 0 ? '+' : ''}{upside}% vs current
            </div>
          )}
        </div>
      </div>

      {/* Price Target Timeline */}
      {(pt.last_month_count || pt.last_quarter_count) && (
        <div className="flex gap-6 text-xs text-muted-foreground">
          {pt.last_month_count > 0 && (
            <span>Last month: {pt.last_month_count} analysts, avg ${pt.last_month_avg?.toFixed(2)}</span>
          )}
          {pt.last_quarter_count > 0 && (
            <span>Last quarter: {pt.last_quarter_count} analysts, avg ${pt.last_quarter_avg?.toFixed(2)}</span>
          )}
        </div>
      )}

      {/* Forward Estimates Table */}
      {fwd.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-foreground mb-2">Forward Estimates</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-muted-foreground text-left">
                  <th className="pb-2 font-medium">FY</th>
                  <th className="pb-2 font-medium">Revenue</th>
                  <th className="pb-2 font-medium">EPS Range</th>
                  <th className="pb-2 font-medium"># Analysts</th>
                </tr>
              </thead>
              <tbody>
                {fwd.map((est) => (
                  <tr key={est.date} className="border-b border-border/50">
                    <td className="py-2 font-mono text-foreground">{est.date?.slice(0, 4)}</td>
                    <td className="py-2 font-mono">{fmt(est.revenue_avg)}</td>
                    <td className="py-2 font-mono">
                      {est.eps_avg != null ? `$${est.eps_avg.toFixed(2)}` : '—'}
                      {est.eps_low != null && (
                        <span className="text-xs text-muted-foreground ml-1">
                          (${est.eps_low.toFixed(2)}–${est.eps_high?.toFixed(2)})
                        </span>
                      )}
                    </td>
                    <td className="py-2 text-muted-foreground">{est.num_analysts_eps ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
```

**Step 5: Commit frontend**

```bash
git add frontend/src/components/AnalystCoverage.jsx
git commit -m "feat: add AnalystCoverage component with consensus, price targets, and estimates"
```

---

## Task 4: Valuation Tab

**Goal:** Show 5-year historical valuation multiples as line charts: P/E, P/S, P/B, EV/EBITDA.

**Data source:** `/stable/ratios?symbol=X&limit=5` + `/stable/key-metrics?symbol=X&limit=5`

**Note:** Only annual data available on current FMP plan (limit capped at 5). This gives 5 annual data points which is enough for a useful trend.

**Files:**
- Modify: `backend/app/lib/openbb.py` — add `get_valuation_history()`
- Modify: `backend/app/routes/securities.py` — add `GET /{symbol}/valuation`
- Modify: `frontend/src/components/ValuationChart.jsx` — update for new data shape + add EV/EBITDA

### Backend

**Step 1: Add `get_valuation_history()` to openbb.py**

```python
def get_valuation_history(symbol: str) -> list[dict]:
    """Fetch 5-year annual valuation multiples. Cache 24h."""
    cache_key = f"{symbol.upper()}:valuation"

    try:
        from app.lib.market_cache import get_cached_fundamentals
        cached = get_cached_fundamentals(cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache read failed for valuation %s", symbol)

    ratios = _fmp_get("ratios", {"symbol": symbol, "limit": 5})
    metrics = _fmp_get("key-metrics", {"symbol": symbol, "limit": 5})

    # Index metrics by date for merging
    metrics_by_date = {m["date"]: m for m in metrics} if isinstance(metrics, list) else {}

    result = []
    for r in (ratios if isinstance(ratios, list) else []):
        date = r.get("date")
        m = metrics_by_date.get(date, {})
        result.append({
            "date": date,
            "fiscal_year": r.get("fiscalYear"),
            "pe_ratio": r.get("priceToEarningsRatio"),
            "ps_ratio": r.get("priceToSalesRatio"),
            "pb_ratio": r.get("priceToBookRatio"),
            "ev_to_ebitda": m.get("evToEBITDA"),
            "ev_to_sales": m.get("evToSales"),
            "peg_ratio": r.get("priceToEarningsGrowthRatio"),
        })

    # Sort oldest first for chart display
    result.sort(key=lambda x: x["date"] or "")

    try:
        from app.lib.market_cache import cache_fundamentals
        cache_fundamentals(cache_key, result)
    except Exception:
        logger.debug("Cache write failed for valuation %s", symbol)

    return result
```

**Step 2: Add route**

```python
@router.get("/{symbol}/valuation")
async def get_valuation_route(symbol: str):
    """Get historical valuation multiples (5-year annual)."""
    symbol = symbol.upper()
    try:
        data = get_valuation_history(symbol)
        return data
    except (SymbolNotFoundError, OpenBBTimeoutError) as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Step 3: Commit backend**

```bash
git add backend/app/lib/openbb.py backend/app/routes/securities.py
git commit -m "feat: add GET /{symbol}/valuation endpoint with 5-year ratio history"
```

### Frontend

**Step 4: Update `ValuationChart.jsx`**

The existing component renders P/E, P/B, P/S using Recharts LineChart. Update it to:
- Accept the new data shape (array with `pe_ratio`, `ps_ratio`, `pb_ratio`, `ev_to_ebitda`)
- Add EV/EBITDA chart
- Use fiscal year labels on X axis
- Use theme-aware colors

Replace the existing `ValuationChart.jsx` content:

```jsx
// frontend/src/components/ValuationChart.jsx
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';

export default function ValuationChart({ data }) {
  if (!data || data.length === 0) {
    return <div className="text-center text-muted-foreground py-8">No valuation data available</div>;
  }

  const charts = [
    { key: 'pe_ratio', title: 'P/E Ratio', color: '#0071e3' },
    { key: 'ps_ratio', title: 'P/S Ratio', color: '#34c759' },
    { key: 'pb_ratio', title: 'P/B Ratio', color: '#ff9500' },
    { key: 'ev_to_ebitda', title: 'EV/EBITDA', color: '#af52de' },
  ];

  return (
    <div className="space-y-4">
      {charts.map(({ key, title, color }) => {
        const hasData = data.some(d => d[key] != null);
        if (!hasData) return null;
        return (
          <div key={key}>
            <h4 className="text-sm font-semibold text-foreground mb-1">{title}</h4>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="fiscal_year"
                  tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                  tickFormatter={v => v?.toFixed(1)}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    color: 'hsl(var(--foreground))',
                  }}
                  labelFormatter={v => `FY ${v}`}
                  formatter={v => [v?.toFixed(2) ?? 'N/A', title]}
                />
                <Line
                  type="monotone" dataKey={key} stroke={color}
                  strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }}
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );
      })}
    </div>
  );
}
```

**Step 5: Commit frontend**

```bash
git add frontend/src/components/ValuationChart.jsx
git commit -m "feat: update ValuationChart with EV/EBITDA and new data shape from FMP ratios"
```

---

## Task 5: Sentiment Tab

**Goal:** Show social sentiment from StockTwits — bullish/bearish gauge + recent messages.

**Data source:** StockTwits API (free, no auth, 200 req/hr limit)
- `https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json`
- Returns 30 messages with optional `entities.sentiment.basic` = "Bullish" | "Bearish" | null

**Files:**
- Modify: `backend/app/lib/openbb.py` — add `get_sentiment()`
- Modify: `backend/app/routes/securities.py` — add `GET /{symbol}/sentiment`
- Create: `frontend/src/components/Sentiment.jsx`

### Backend

**Step 1: Add `get_sentiment()` to openbb.py**

```python
def get_sentiment(symbol: str) -> dict:
    """Fetch social sentiment from StockTwits. Cache 15 min."""
    cache_key = f"{symbol.upper()}:sentiment"

    try:
        from app.lib.market_cache import get_cached_quote
        cached = get_cached_quote(cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache read failed for sentiment %s", symbol)

    try:
        resp = httpx.get(
            f"https://api.stocktwits.com/api/2/streams/symbol/{symbol.upper()}.json",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        raise OpenBBTimeoutError(f"StockTwits timeout for {symbol}")
    except Exception as e:
        raise SymbolNotFoundError(f"StockTwits error for {symbol}: {e}")

    messages = data.get("messages", [])
    symbol_info = data.get("symbol", {})

    bullish = 0
    bearish = 0
    recent = []

    for msg in messages:
        sentiment = (msg.get("entities") or {}).get("sentiment") or {}
        basic = sentiment.get("basic")
        if basic == "Bullish":
            bullish += 1
        elif basic == "Bearish":
            bearish += 1

        recent.append({
            "id": msg.get("id"),
            "body": msg.get("body", "")[:280],
            "created_at": msg.get("created_at"),
            "sentiment": basic,
            "username": (msg.get("user") or {}).get("username"),
        })

    total_with_sentiment = bullish + bearish
    result = {
        "bullish": bullish,
        "bearish": bearish,
        "total_messages": len(messages),
        "bullish_pct": round(bullish / total_with_sentiment * 100) if total_with_sentiment > 0 else None,
        "watchlist_count": symbol_info.get("watchlist_count"),
        "messages": recent[:15],
    }

    try:
        from app.lib.market_cache import cache_quote
        cache_quote(cache_key, result)
    except Exception:
        logger.debug("Cache write failed for sentiment %s", symbol)

    return result
```

**Step 2: Add route**

```python
@router.get("/{symbol}/sentiment")
async def get_sentiment_route(symbol: str):
    """Get social sentiment from StockTwits."""
    symbol = symbol.upper()
    try:
        data = get_sentiment(symbol)
        return data
    except (SymbolNotFoundError, OpenBBTimeoutError) as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Step 3: Commit backend**

```bash
git add backend/app/lib/openbb.py backend/app/routes/securities.py
git commit -m "feat: add GET /{symbol}/sentiment endpoint with StockTwits data"
```

### Frontend

**Step 4: Create `Sentiment.jsx`**

Show:
1. **Sentiment gauge** — bullish vs bearish bar (like insider trades summary bar pattern)
2. **Stats row** — total messages, watchlist count
3. **Message feed** — recent StockTwits messages with sentiment badges

```jsx
// frontend/src/components/Sentiment.jsx
export default function Sentiment({ data }) {
  if (!data) {
    return <div className="text-center text-muted-foreground py-8">No sentiment data available</div>;
  }

  const { bullish, bearish, total_messages, bullish_pct, watchlist_count, messages = [] } = data;
  const totalTagged = bullish + bearish;

  const sentimentColor = {
    Bullish: 'bg-success/20 text-success',
    Bearish: 'bg-destructive/20 text-destructive',
  };

  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h`;
    return `${Math.floor(hrs / 24)}d`;
  };

  return (
    <div className="space-y-4">
      {/* Sentiment Gauge */}
      {totalTagged > 0 && (
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-success font-medium">Bullish {bullish}</span>
            <span className="text-destructive font-medium">Bearish {bearish}</span>
          </div>
          <div className="h-3 rounded-full overflow-hidden bg-muted flex">
            <div
              className="bg-success transition-all"
              style={{ width: `${bullish_pct || 0}%` }}
            />
            <div
              className="bg-destructive transition-all"
              style={{ width: `${100 - (bullish_pct || 0)}%` }}
            />
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="flex gap-4 text-xs text-muted-foreground">
        <span>{total_messages} messages</span>
        {totalTagged > 0 && <span>{totalTagged} with sentiment</span>}
        {watchlist_count && <span>{watchlist_count.toLocaleString()} watchers</span>}
      </div>

      {/* Message Feed */}
      {messages.length > 0 && (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {messages.map((msg) => (
            <div key={msg.id} className="text-sm border-b border-border/50 pb-2">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-xs font-medium text-muted-foreground">@{msg.username}</span>
                <span className="text-xs text-muted-foreground">{timeAgo(msg.created_at)}</span>
                {msg.sentiment && (
                  <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${sentimentColor[msg.sentiment] || ''}`}>
                    {msg.sentiment}
                  </span>
                )}
              </div>
              <p className="text-foreground text-sm leading-snug">{msg.body}</p>
            </div>
          ))}
        </div>
      )}

      {/* Attribution */}
      <div className="text-xs text-muted-foreground text-center pt-2">
        Data from StockTwits
      </div>
    </div>
  );
}
```

**Step 5: Commit frontend**

```bash
git add frontend/src/components/Sentiment.jsx
git commit -m "feat: add Sentiment component with StockTwits gauge and message feed"
```

---

## Task 6: Wire All Tabs into StockRow

**Goal:** Integrate all 5 new tabs into the expanded stock panel with lazy loading.

**Files:**
- Modify: `frontend/src/components/StockRow.jsx`

### Changes

**Step 1: Add imports**

```jsx
import Fundamentals from './Fundamentals';
import Earnings from './Earnings';
import AnalystCoverage from './AnalystCoverage';
import ValuationChart from './ValuationChart';
import Sentiment from './Sentiment';
```

**Step 2: Add state variables** (after existing state declarations)

```jsx
const [fundamentalsData, setFundamentalsData] = useState(null);
const [fundamentalsLoading, setFundamentalsLoading] = useState(false);
const [earningsData, setEarningsData] = useState(null);
const [earningsLoading, setEarningsLoading] = useState(false);
const [analystData, setAnalystData] = useState(null);
const [analystLoading, setAnalystLoading] = useState(false);
const [valuationData, setValuationData] = useState(null);
const [valuationLoading, setValuationLoading] = useState(false);
const [sentimentData, setSentimentData] = useState(null);
const [sentimentLoading, setSentimentLoading] = useState(false);
```

**Step 3: Add generic tab-fetch helper** (after existing fetchInsiderTrades)

Replace the individual fetch functions with a generic helper to avoid repetition:

```jsx
const fetchTabData = useCallback(async (endpoint, setter, loadingSetter, currentData, currentLoading) => {
  if (currentData || currentLoading) return;
  loadingSetter(true);
  try {
    const response = await fetch(
      `${API_BASE}/api/securities/${item.symbol}/${endpoint}`,
      { credentials: 'include' }
    );
    if (response.ok) {
      const data = await response.json();
      setter(data);
    }
  } catch (err) {
    console.error(`Error fetching ${endpoint} for ${item.symbol}:`, err);
  } finally {
    loadingSetter(false);
  }
}, [item.symbol]);
```

**Step 4: Update tab `onValueChange` handler**

```jsx
onValueChange={(val) => {
  setActiveTab(val);
  const fetchers = {
    insider: () => fetchTabData('insider-trades', setInsiderData, setInsiderLoading, insiderData, insiderLoading),
    fundamentals: () => fetchTabData('fundamentals', setFundamentalsData, setFundamentalsLoading, fundamentalsData, fundamentalsLoading),
    earnings: () => fetchTabData('earnings', setEarningsData, setEarningsLoading, earningsData, earningsLoading),
    analyst: () => fetchTabData('analyst', setAnalystData, setAnalystLoading, analystData, analystLoading),
    valuation: () => fetchTabData('valuation', setValuationData, setValuationLoading, valuationData, valuationLoading),
    sentiment: () => fetchTabData('sentiment', setSentimentData, setSentimentLoading, sentimentData, sentimentLoading),
  };
  fetchers[val]?.();
}}
```

**Step 5: Add TabsTriggers**

```jsx
<TabsList>
  <TabsTrigger value="chart">Chart</TabsTrigger>
  <TabsTrigger value="fundamentals">Fundamentals</TabsTrigger>
  <TabsTrigger value="earnings">Earnings</TabsTrigger>
  <TabsTrigger value="analyst">Analysts</TabsTrigger>
  <TabsTrigger value="valuation">Valuation</TabsTrigger>
  <TabsTrigger value="insider">Insiders</TabsTrigger>
  <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
</TabsList>
```

**Step 6: Add TabsContent blocks** (after existing insider tab content)

```jsx
<TabsContent value="fundamentals" className="mt-4">
  {fundamentalsLoading ? (
    <div className="flex items-center justify-center h-32">
      <div className="text-muted-foreground">Loading fundamentals...</div>
    </div>
  ) : (
    <Fundamentals data={fundamentalsData} />
  )}
</TabsContent>

<TabsContent value="earnings" className="mt-4">
  {earningsLoading ? (
    <div className="flex items-center justify-center h-32">
      <div className="text-muted-foreground">Loading earnings...</div>
    </div>
  ) : (
    <Earnings data={earningsData} />
  )}
</TabsContent>

<TabsContent value="analyst" className="mt-4">
  {analystLoading ? (
    <div className="flex items-center justify-center h-32">
      <div className="text-muted-foreground">Loading analyst coverage...</div>
    </div>
  ) : (
    <AnalystCoverage data={analystData} currentPrice={price} />
  )}
</TabsContent>

<TabsContent value="valuation" className="mt-4">
  {valuationLoading ? (
    <div className="flex items-center justify-center h-32">
      <div className="text-muted-foreground">Loading valuation data...</div>
    </div>
  ) : (
    <ValuationChart data={valuationData} />
  )}
</TabsContent>

<TabsContent value="sentiment" className="mt-4">
  {sentimentLoading ? (
    <div className="flex items-center justify-center h-32">
      <div className="text-muted-foreground">Loading sentiment...</div>
    </div>
  ) : (
    <Sentiment data={sentimentData} />
  )}
</TabsContent>
```

**Step 7: Remove stale insider fetch callback**

The existing `fetchInsiderTrades` useCallback can be removed since the generic `fetchTabData` handles all tabs now. Update the insider tab's data flow to use the generic helper too.

**Step 8: Commit integration**

```bash
git add frontend/src/components/StockRow.jsx
git commit -m "feat: wire all new tabs into StockRow expanded panel with lazy loading"
```

---

## Task 7: Cleanup & Polish

**Step 1:** Delete `frontend/src/components/StockAnalytics.jsx` — it was never integrated and is now fully replaced by the tabs in StockRow.

**Step 2:** Verify all new endpoints return gracefully for symbols with missing data (e.g., newly listed stocks, ETFs). Each backend function should return empty/partial data rather than throwing.

**Step 3:** Test tab switching — ensure no duplicate fetches, loading states clear properly, data persists when switching back to a previously loaded tab.

**Step 4:** Check responsive layout — tabs should wrap on mobile. The TabsList may need horizontal scrolling on narrow screens.

**Step 5: Commit cleanup**

```bash
git add -A
git commit -m "chore: remove unused StockAnalytics component, polish tab responsive layout"
```

---

## Tab Order Summary

| Tab | Data Source | Cache | TTL |
|-----|-----------|-------|-----|
| Chart | OpenBB `get_ohlcv()` | `daily_prices` | persistent |
| Fundamentals | FMP `/stable/profile` + `/stable/key-metrics` | `fundamentals` | 24h |
| Earnings | FMP `/stable/income-statement` + `/stable/analyst-estimates` | `fundamentals` | 24h |
| Analysts | FMP `/stable/price-target-summary` + `get_estimates()` + `/stable/analyst-estimates` | `fundamentals` | 24h |
| Valuation | FMP `/stable/ratios` + `/stable/key-metrics` | `fundamentals` | 24h |
| Insiders | SEC EDGAR Form 4 | `fundamentals` | 24h |
| Sentiment | StockTwits API | `quotes_cache` | 15min |
