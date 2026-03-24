# Insider Trades — Stock Detail View

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add insider trading data (summary bar + trade table) to the stock detail expanded panel in StockRow.

**Architecture:** Backend adds `get_insider_trading()` to OpenBB lib with DuckDB cache (24h TTL), exposed via new REST endpoint. Frontend adds tabs to the StockRow expanded panel ("Chart" + "Insider Trades"), with a new InsiderTrades component showing a buy/sell summary bar and trade table.

**Tech Stack:** OpenBB SDK (FMP provider), DuckDB, FastAPI, React, TailwindCSS, shadcn/ui Tabs

---

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Location | StockRow expanded panel (tabbed) | This is the actual stock detail view |
| Data source | OpenBB SDK (`obb.equity.ownership.insider_trading`) | Consistent with existing pipeline |
| Cache | DuckDB `fundamentals` table (JSON blob, 24h TTL) | Reuses existing cache pattern — no new table needed |
| Summary lookback | 3 months | Recent enough to be actionable |
| Trade limit | 20 most recent | Enough history without over-fetching |

---

### Task 1: DuckDB cache for insider trades

**Files:**
- Modify: `backend/app/lib/market_cache.py` (no changes needed — reuse `fundamentals` table with key `{SYMBOL}:insider_trades`)

No code changes needed. The existing `get_cached_fundamentals()` / `cache_fundamentals()` functions already support arbitrary keys with 24h TTL. We'll use the key pattern `{SYMBOL}:insider_trades`, same approach as estimates (`{SYMBOL}:estimates`).

**Step 1: Verify the pattern works**

Confirm by reading `openbb.py:437-444` — `get_estimates` already uses `cache_fundamentals` with key `{SYMBOL}:estimates`. We'll follow this exact pattern.

No commit needed — this is just confirmation.

---

### Task 2: OpenBB `get_insider_trading()` function

**Files:**
- Modify: `backend/app/lib/openbb.py` (append after `get_estimates` function, ~line 476)
- Test: `backend/tests/test_insider_trades.py` (create)

**Step 1: Write the failing test**

Create `backend/tests/test_insider_trades.py`:

```python
"""Tests for insider trading data functions."""
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import duckdb


@pytest.fixture
def mock_cache(monkeypatch):
    """In-memory DuckDB for cache isolation."""
    conn = duckdb.connect(":memory:")
    monkeypatch.setattr("app.lib.market_cache._connection", conn)
    from app.lib import market_cache
    market_cache._init_tables(conn)
    return conn


def _make_openbb_result(trades_data):
    """Create a mock OpenBB response with insider trading results."""
    mock_results = []
    for t in trades_data:
        r = MagicMock()
        r.filing_date = t.get("filing_date")
        r.transaction_date = t.get("transaction_date")
        r.owner_name = t.get("owner_name")
        r.owner_title = t.get("owner_title")
        r.transaction_type = t.get("transaction_type")
        r.acquisition_or_disposition = t.get("acquisition_or_disposition")
        r.securities_transacted = t.get("securities_transacted")
        r.price = t.get("price")
        r.value = t.get("value")
        mock_results.append(r)
    mock_resp = MagicMock()
    mock_resp.results = mock_results
    return mock_resp


class TestGetInsiderTrading:
    def test_returns_normalized_trades(self, mock_cache):
        from app.lib.openbb import get_insider_trading

        mock_data = _make_openbb_result([
            {
                "filing_date": "2026-03-15",
                "transaction_date": "2026-03-14",
                "owner_name": "Jane Doe",
                "owner_title": "CEO",
                "transaction_type": "P-Purchase",
                "acquisition_or_disposition": "A",
                "securities_transacted": 5000.0,
                "price": 150.0,
                "value": 750000.0,
            },
            {
                "filing_date": "2026-03-10",
                "transaction_date": "2026-03-09",
                "owner_name": "John Smith",
                "owner_title": "CFO",
                "transaction_type": "S-Sale",
                "acquisition_or_disposition": "D",
                "securities_transacted": 10000.0,
                "price": 148.0,
                "value": 1480000.0,
            },
        ])

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.return_value = mock_data
            result = get_insider_trading("AAPL")

        assert len(result) == 2
        assert result[0]["insider_name"] == "Jane Doe"
        assert result[0]["insider_title"] == "CEO"
        assert result[0]["transaction_type"] == "buy"
        assert result[0]["shares"] == 5000
        assert result[0]["value"] == 750000.0

        assert result[1]["transaction_type"] == "sell"

    def test_caches_result(self, mock_cache):
        from app.lib.openbb import get_insider_trading

        mock_data = _make_openbb_result([{
            "filing_date": "2026-03-15",
            "transaction_date": "2026-03-14",
            "owner_name": "Jane Doe",
            "owner_title": "CEO",
            "transaction_type": "P-Purchase",
            "acquisition_or_disposition": "A",
            "securities_transacted": 5000.0,
            "price": 150.0,
            "value": 750000.0,
        }])

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.return_value = mock_data
            # First call hits API
            get_insider_trading("AAPL")
            # Second call should use cache (no additional API call)
            result = get_insider_trading("AAPL")

        assert mock_obb.equity.ownership.insider_trading.call_count == 1
        assert len(result) == 1

    def test_empty_results(self, mock_cache):
        from app.lib.openbb import get_insider_trading

        mock_resp = MagicMock()
        mock_resp.results = []

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.return_value = mock_resp
            result = get_insider_trading("AAPL")

        assert result == []
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_insider_trades.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_insider_trading' from 'app.lib.openbb'`

**Step 3: Write minimal implementation**

Append to `backend/app/lib/openbb.py` (after `get_calendar_events`, ~line 645):

```python
def get_insider_trading(symbol: str) -> list[dict]:
    """
    Fetch insider trades for symbol via OpenBB (FMP provider).

    Checks DuckDB fundamentals cache first (24h TTL, key: {SYMBOL}:insider_trades).
    On miss, fetches from OpenBB and caches the result.

    Args:
        symbol: Stock ticker symbol

    Returns:
        List of dicts with date, insider_name, insider_title,
        transaction_type ('buy'/'sell'), shares, value.
        Sorted newest-first, limited to 20 most recent.
    """
    cache_key = f"{symbol.upper()}:insider_trades"

    # --- cache hit? ---
    try:
        from app.lib.market_cache import get_cached_fundamentals
        cached = get_cached_fundamentals(cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache read failed for insider trades %s", symbol)

    # --- cache miss: fetch from OpenBB ---
    try:
        data = obb.equity.ownership.insider_trading(symbol=symbol, provider="fmp")

        if not data or not data.results:
            # Cache empty result to avoid re-fetching
            try:
                from app.lib.market_cache import cache_fundamentals
                cache_fundamentals(cache_key, [])
            except Exception:
                pass
            return []

        trades = []
        for row in data.results:
            # Determine buy vs sell from transaction_type or acquisition_or_disposition
            txn_type_raw = getattr(row, "transaction_type", "") or ""
            acq_disp = getattr(row, "acquisition_or_disposition", "") or ""

            if "purchase" in txn_type_raw.lower() or txn_type_raw.startswith("P") or acq_disp == "A":
                txn_type = "buy"
            elif "sale" in txn_type_raw.lower() or txn_type_raw.startswith("S") or acq_disp == "D":
                txn_type = "sell"
            else:
                txn_type = txn_type_raw.lower() or "other"

            # Use transaction_date if available, fall back to filing_date
            date_val = getattr(row, "transaction_date", None) or getattr(row, "filing_date", None)
            date_str = _format_date(date_val) if date_val else None

            shares_val = getattr(row, "securities_transacted", None)
            price_val = getattr(row, "price", None)
            value_val = getattr(row, "value", None)

            # Compute value if not provided but shares and price are
            if value_val is None and shares_val is not None and price_val is not None:
                try:
                    value_val = float(shares_val) * float(price_val)
                except (TypeError, ValueError):
                    pass

            trades.append({
                "date": date_str,
                "insider_name": getattr(row, "owner_name", None) or getattr(row, "reporting_name", None),
                "insider_title": getattr(row, "owner_title", None) or getattr(row, "reporting_title", None),
                "transaction_type": txn_type,
                "shares": int(float(shares_val)) if shares_val is not None else None,
                "value": float(value_val) if value_val is not None else None,
            })

        # Sort newest-first, limit to 20
        trades.sort(key=lambda t: t["date"] or "", reverse=True)
        trades = trades[:20]

        # Cache with 24h TTL
        try:
            from app.lib.market_cache import cache_fundamentals
            cache_fundamentals(cache_key, trades)
        except Exception:
            logger.debug("Cache write failed for insider trades %s", symbol)

        return trades

    except Exception as e:
        logger.warning("Failed to fetch insider trades for %s: %s", symbol, e)
        return []
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_insider_trades.py -v`
Expected: 3 PASSED

**Step 5: Commit**

```bash
git add backend/app/lib/openbb.py backend/tests/test_insider_trades.py
git commit -m "feat: add get_insider_trading() to OpenBB lib with DuckDB cache"
```

---

### Task 3: REST endpoint for insider trades

**Files:**
- Modify: `backend/app/routes/securities.py` (add new route after existing ones, ~line 170)

**Step 1: Write the failing test**

Append to `backend/tests/test_insider_trades.py`:

```python
from fastapi.testclient import TestClient


@pytest.fixture
def client(mock_cache, monkeypatch):
    """Test client with mocked auth (single-user mode)."""
    monkeypatch.setenv("SINGLE_USER_MODE", "true")
    from app.main import app
    return TestClient(app)


class TestInsiderTradesEndpoint:
    def test_returns_trades_with_summary(self, client):
        mock_trades = [
            {
                "filing_date": "2026-03-15",
                "transaction_date": "2026-03-14",
                "owner_name": "Jane Doe",
                "owner_title": "CEO",
                "transaction_type": "P-Purchase",
                "acquisition_or_disposition": "A",
                "securities_transacted": 5000.0,
                "price": 150.0,
                "value": 750000.0,
            },
            {
                "filing_date": "2026-02-10",
                "transaction_date": "2026-02-09",
                "owner_name": "John Smith",
                "owner_title": "CFO",
                "transaction_type": "S-Sale",
                "acquisition_or_disposition": "D",
                "securities_transacted": 10000.0,
                "price": 148.0,
                "value": 1480000.0,
            },
        ]
        mock_data = _make_openbb_result(mock_trades)

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.return_value = mock_data
            response = client.get("/api/securities/AAPL/insider-trades")

        assert response.status_code == 200
        body = response.json()
        assert "summary" in body
        assert "trades" in body
        assert body["summary"]["total_buys"] == 1
        assert body["summary"]["total_sells"] == 1
        assert body["summary"]["buy_value"] == 750000.0
        assert body["summary"]["sell_value"] == 1480000.0
        assert body["summary"]["net_value"] == 750000.0 - 1480000.0
        assert len(body["trades"]) == 2

    def test_empty_insider_trades(self, client):
        mock_resp = MagicMock()
        mock_resp.results = []

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.return_value = mock_resp
            response = client.get("/api/securities/AAPL/insider-trades")

        assert response.status_code == 200
        body = response.json()
        assert body["summary"]["total_buys"] == 0
        assert body["summary"]["total_sells"] == 0
        assert body["trades"] == []
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_insider_trades.py::TestInsiderTradesEndpoint -v`
Expected: FAIL — 404 (route doesn't exist yet)

**Step 3: Write minimal implementation**

Append to `backend/app/routes/securities.py`:

```python
from datetime import datetime, timedelta


@router.get("/{symbol}/insider-trades")
async def get_insider_trades(symbol: str):
    """
    Get insider trading data for a symbol.

    Returns:
        summary: Aggregated buy/sell stats for last 3 months
        trades: Up to 20 most recent insider trades
    """
    from app.lib.openbb import get_insider_trading

    symbol = symbol.upper()
    trades = get_insider_trading(symbol)

    # Compute summary for last 3 months
    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    recent = [t for t in trades if t.get("date") and t["date"] >= cutoff]

    buys = [t for t in recent if t["transaction_type"] == "buy"]
    sells = [t for t in recent if t["transaction_type"] == "sell"]

    buy_value = sum(t["value"] for t in buys if t["value"] is not None)
    sell_value = sum(t["value"] for t in sells if t["value"] is not None)

    return {
        "summary": {
            "total_buys": len(buys),
            "total_sells": len(sells),
            "buy_value": buy_value,
            "sell_value": sell_value,
            "net_value": buy_value - sell_value,
            "period": "3m",
        },
        "trades": trades,
    }
```

Also add `get_insider_trading` to the import in securities.py line 7-9:

```python
from app.lib.openbb import (
    get_quote, get_ma_200, get_history, get_ohlcv, get_performance, get_estimates,
    get_insider_trading,
    SymbolNotFoundError, OpenBBTimeoutError,
)
```

And remove the local import inside the function since we'll import at the top.

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_insider_trades.py -v`
Expected: 5 PASSED

**Step 5: Commit**

```bash
git add backend/app/routes/securities.py backend/tests/test_insider_trades.py
git commit -m "feat: add GET /api/securities/{symbol}/insider-trades endpoint"
```

---

### Task 4: Frontend InsiderTrades component

**Files:**
- Create: `frontend/src/components/InsiderTrades.jsx`

**Step 1: Create the component**

```jsx
import { Badge } from './ui/badge';

function formatValue(value) {
  if (value == null) return '—';
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

function formatShares(shares) {
  if (shares == null) return '—';
  if (shares >= 1_000_000) return `${(shares / 1_000_000).toFixed(1)}M`;
  if (shares >= 1_000) return `${(shares / 1_000).toFixed(1)}K`;
  return shares.toLocaleString();
}

export default function InsiderTrades({ data }) {
  if (!data) return null;

  const { summary, trades } = data;

  const totalTrades = summary.total_buys + summary.total_sells;
  const buyPct = totalTrades > 0 ? (summary.total_buys / totalTrades) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="bg-card rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
            Last 3 months
          </span>
          {totalTrades === 0 && (
            <span className="text-sm text-muted-foreground">No insider trades</span>
          )}
        </div>

        {totalTrades > 0 && (
          <>
            {/* Stacked bar */}
            <div className="h-3 rounded-full overflow-hidden flex bg-muted mb-3">
              {buyPct > 0 && (
                <div
                  className="bg-success transition-all"
                  style={{ width: `${buyPct}%` }}
                />
              )}
              {buyPct < 100 && (
                <div
                  className="bg-destructive transition-all"
                  style={{ width: `${100 - buyPct}%` }}
                />
              )}
            </div>

            {/* Stats text */}
            <div className="flex items-center gap-2 text-sm flex-wrap">
              <span className="text-success font-medium">
                {summary.total_buys} {summary.total_buys === 1 ? 'buy' : 'buys'} ({formatValue(summary.buy_value)})
              </span>
              <span className="text-muted-foreground">·</span>
              <span className="text-destructive font-medium">
                {summary.total_sells} {summary.total_sells === 1 ? 'sell' : 'sells'} ({formatValue(summary.sell_value)})
              </span>
              <span className="text-muted-foreground">·</span>
              <span className={`font-medium ${summary.net_value >= 0 ? 'text-success' : 'text-destructive'}`}>
                Net: {summary.net_value >= 0 ? '+' : ''}{formatValue(summary.net_value)}
              </span>
            </div>
          </>
        )}
      </div>

      {/* Trade table */}
      {trades.length > 0 && (
        <div className="bg-card rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase tracking-wide">
                <th className="px-4 py-2">Date</th>
                <th className="px-4 py-2">Insider</th>
                <th className="px-4 py-2 hidden md:table-cell">Title</th>
                <th className="px-4 py-2">Type</th>
                <th className="px-4 py-2 text-right">Shares</th>
                <th className="px-4 py-2 text-right">Value</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade, i) => (
                <tr key={i} className="border-b border-border last:border-0 hover:bg-muted/50">
                  <td className="px-4 py-2 font-mono text-xs">{trade.date || '—'}</td>
                  <td className="px-4 py-2 truncate max-w-[150px]" title={trade.insider_name}>
                    {trade.insider_name || '—'}
                  </td>
                  <td className="px-4 py-2 truncate max-w-[120px] hidden md:table-cell text-muted-foreground" title={trade.insider_title}>
                    {trade.insider_title || '—'}
                  </td>
                  <td className="px-4 py-2">
                    <Badge
                      variant={trade.transaction_type === 'buy' ? 'default' : 'destructive'}
                      className={`text-xs ${
                        trade.transaction_type === 'buy'
                          ? 'bg-success/15 text-success hover:bg-success/25 border-0'
                          : 'bg-destructive/15 text-destructive hover:bg-destructive/25 border-0'
                      }`}
                    >
                      {trade.transaction_type === 'buy' ? 'Buy' : 'Sell'}
                    </Badge>
                  </td>
                  <td className="px-4 py-2 text-right font-mono">{formatShares(trade.shares)}</td>
                  <td className="px-4 py-2 text-right font-mono">{formatValue(trade.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

**Step 2: Verify it renders (manual)**

Component is pure — takes `{ data }` prop with `{ summary, trades }` shape. No API calls. Will be wired in Task 5.

**Step 3: Commit**

```bash
git add frontend/src/components/InsiderTrades.jsx
git commit -m "feat: add InsiderTrades component with summary bar and trade table"
```

---

### Task 5: Wire InsiderTrades into StockRow expanded panel

**Files:**
- Modify: `frontend/src/components/StockRow.jsx`

**Step 1: Add imports and state** (at top of StockRow.jsx)

Add imports:
```jsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import InsiderTrades from './InsiderTrades';
```

Add state (after `expandedLoading` state, ~line 19):
```jsx
const [insiderData, setInsiderData] = useState(null);
const [insiderLoading, setInsiderLoading] = useState(false);
```

**Step 2: Add fetch function for insider trades**

Add a new `useEffect` after the existing expanded-data effect (~line 57):

```jsx
// Fetch insider trades when "insider" tab is selected
const [activeTab, setActiveTab] = useState('chart');

const fetchInsiderTrades = useCallback(async () => {
  if (insiderData || insiderLoading) return;
  setInsiderLoading(true);
  try {
    const response = await fetch(
      `${API_BASE}/api/securities/${item.symbol}/insider-trades`,
      { credentials: 'include' }
    );
    if (response.ok) {
      const data = await response.json();
      setInsiderData(data);
    }
  } catch (err) {
    console.error(`Error fetching insider trades for ${item.symbol}:`, err);
  } finally {
    setInsiderLoading(false);
  }
}, [item.symbol, insiderData, insiderLoading]);
```

**Step 3: Replace the expanded panel content**

Replace the current expanded panel (lines 200-214):

```jsx
{/* Expandable dropdown panel */}
{isExpanded && (
  <div className="border-t border-border p-4 space-y-4">
    <Tabs value={activeTab} onValueChange={(val) => {
      setActiveTab(val);
      if (val === 'insider' && !insiderData && !insiderLoading) {
        fetchInsiderTrades();
      }
    }}>
      <TabsList>
        <TabsTrigger value="chart">Chart</TabsTrigger>
        <TabsTrigger value="insider">Insider Trades</TabsTrigger>
      </TabsList>

      <TabsContent value="chart" className="mt-4">
        {expandedLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-muted-foreground">Loading chart data...</div>
          </div>
        ) : (
          <CandlestickChart
            symbol={item.symbol}
            ohlcv={expandedData?.ohlcv || []}
          />
        )}
      </TabsContent>

      <TabsContent value="insider" className="mt-4">
        {insiderLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-muted-foreground">Loading insider trades...</div>
          </div>
        ) : (
          <InsiderTrades data={insiderData} />
        )}
      </TabsContent>
    </Tabs>
  </div>
)}
```

**Step 4: Verify manually**

Run: `cd frontend && npm run dev`
- Expand a stock row → should see "Chart" and "Insider Trades" tabs
- Chart tab shows candlestick chart (existing behavior)
- Click "Insider Trades" tab → loads and shows data

**Step 5: Commit**

```bash
git add frontend/src/components/StockRow.jsx
git commit -m "feat: add Insider Trades tab to stock detail expanded panel"
```

---

## Files Changed Summary

| File | Change |
|------|--------|
| `backend/app/lib/openbb.py` | Add `get_insider_trading()` function |
| `backend/app/routes/securities.py` | Add `GET /{symbol}/insider-trades` endpoint |
| `backend/tests/test_insider_trades.py` | Create — tests for openbb function + endpoint |
| `frontend/src/components/InsiderTrades.jsx` | Create — summary bar + trade table component |
| `frontend/src/components/StockRow.jsx` | Add tabs to expanded panel, wire InsiderTrades |
