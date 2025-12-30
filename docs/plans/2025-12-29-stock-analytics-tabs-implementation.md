# Stock Analytics with Expandable Tabs - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor watchlist UI to show expandable analytics below each stock with tabbed interface for price history and valuation metrics.

**Architecture:** Add OpenBB function and API endpoint for financial ratios. Create expandable StockAnalytics component with tabs. Move chart from right panel to inline below stock rows. Support P/E, P/B, P/S ratio charts.

**Tech Stack:** FastAPI, OpenBB SDK (FMP provider), React, Recharts, shadcn/ui Tabs, TailwindCSS

---

## Task 1: Backend - Add Financial Ratios Function

**Files:**
- Modify: `backend/app/lib/openbb.py` (add new function after `get_history`)

**Step 1: Add get_financial_ratios function**

Add this function to `backend/app/lib/openbb.py`:

```python
def get_financial_ratios(symbol: str, period: str = "quarterly", limit: int = 12) -> list[dict]:
    """
    Fetch historical financial ratios (P/E, P/B, P/S).

    Args:
        symbol: Stock ticker symbol
        period: 'quarterly' or 'annual' (default: quarterly)
        limit: Number of periods to fetch (default: 12)

    Returns:
        List of dicts: [{date, pe_ratio, pb_ratio, ps_ratio}, ...]

    Raises:
        SymbolNotFoundError: If symbol not found
        OpenBBTimeoutError: If API times out
    """
    try:
        data = obb.equity.fundamental.ratios(
            symbol=symbol,
            period=period,
            limit=limit,
            provider="fmp"
        )

        if not data or not data.results:
            raise SymbolNotFoundError(f"No ratios data for {symbol}")

        # Transform to frontend format
        ratios_list = []
        for result in data.results:
            ratio_dict = {
                "date": result.date.strftime("%Y-%m-%d") if hasattr(result, 'date') else str(result.period_ending),
                "pe_ratio": float(result.price_earnings_ratio) if hasattr(result, 'price_earnings_ratio') and result.price_earnings_ratio else None,
                "pb_ratio": float(result.price_to_book_ratio) if hasattr(result, 'price_to_book_ratio') and result.price_to_book_ratio else None,
                "ps_ratio": float(result.price_to_sales_ratio) if hasattr(result, 'price_to_sales_ratio') and result.price_to_sales_ratio else None,
            }
            ratios_list.append(ratio_dict)

        return ratios_list

    except SymbolNotFoundError:
        raise
    except Exception as e:
        if "timeout" in str(e).lower():
            raise OpenBBTimeoutError(f"Timeout fetching ratios for {symbol}")
        raise SymbolNotFoundError(f"Error fetching ratios: {str(e)}")
```

**Step 2: Test the function manually**

Start Docker services and test in Python shell:

```bash
docker-compose up -d
docker-compose exec backend python -c "
from app.lib import openbb
ratios = openbb.get_financial_ratios('AAPL', period='quarterly', limit=4)
print(ratios)
"
```

Expected: JSON array with 4 quarters of ratio data

**Step 3: Commit**

```bash
git add backend/app/lib/openbb.py
git commit -m "feat(backend): add get_financial_ratios function to OpenBB lib"
```

---

## Task 2: Backend - Add Ratios API Endpoint

**Files:**
- Modify: `backend/app/routes/securities.py` (add new endpoint after existing endpoints)

**Step 1: Add ratios endpoint**

Add this endpoint to `backend/app/routes/securities.py`:

```python
@router.get("/{symbol}/ratios")
async def get_security_ratios(
    symbol: str,
    period: str = "quarterly",
    limit: int = 12,
    current_user: User = Depends(get_current_user)
):
    """Get historical financial ratios for a security."""
    try:
        ratios = openbb.get_financial_ratios(symbol.upper(), period, limit)
        return ratios
    except openbb.SymbolNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except openbb.OpenBBTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
```

**Step 2: Restart backend**

```bash
docker-compose restart backend
```

**Step 3: Test the endpoint**

```bash
curl -X GET "http://localhost:8000/api/securities/AAPL/ratios?period=quarterly&limit=4" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -s | python -m json.tool
```

Expected: 200 OK with JSON array of ratios

**Step 4: Commit**

```bash
git add backend/app/routes/securities.py
git commit -m "feat(backend): add /ratios endpoint for financial metrics"
```

---

## Task 3: Frontend - Install Tabs Component

**Files:**
- Modify: `frontend/package.json` (dependencies updated)
- Create: `frontend/src/components/ui/tabs.jsx`

**Step 1: Install shadcn/ui tabs component**

```bash
cd frontend
npx shadcn@latest add tabs
```

**Step 2: Verify tabs component exists**

```bash
ls -la src/components/ui/tabs.jsx
```

Expected: File exists

**Step 3: Commit**

```bash
git add src/components/ui/tabs.jsx package.json package-lock.json
git commit -m "feat(frontend): add shadcn/ui tabs component"
```

---

## Task 4: Frontend - Create ValuationChart Component

**Files:**
- Create: `frontend/src/components/ValuationChart.jsx`

**Step 1: Create ValuationChart component**

Create `frontend/src/components/ValuationChart.jsx`:

```jsx
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export default function ValuationChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        No valuation data available
      </div>
    );
  }

  const chartConfig = {
    height: 200,
    margin: { top: 5, right: 20, left: 10, bottom: 5 }
  };

  const renderMetricChart = (dataKey, title) => (
    <div className="mb-6 last:mb-0" key={dataKey}>
      <h4 className="text-sm font-semibold text-gray-700 mb-2">{title}</h4>
      <ResponsiveContainer width="100%" height={chartConfig.height}>
        <LineChart data={data} margin={chartConfig.margin}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(date) => {
              const d = new Date(date);
              return `${d.getMonth() + 1}/${String(d.getDate()).slice(-2)}`;
            }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => value?.toFixed(1) || ''}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            labelFormatter={(date) => new Date(date).toLocaleDateString()}
            formatter={(value) => [value?.toFixed(2) || 'N/A', title]}
          />
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke="#000000"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );

  return (
    <div className="p-4">
      {renderMetricChart('pe_ratio', 'P/E Ratio')}
      {renderMetricChart('pb_ratio', 'P/B Ratio')}
      {renderMetricChart('ps_ratio', 'P/S Ratio')}
    </div>
  );
}
```

**Step 2: Verify component syntax**

```bash
npm run lint src/components/ValuationChart.jsx
```

Expected: No new errors (ignore pre-existing config errors)

**Step 3: Commit**

```bash
git add src/components/ValuationChart.jsx
git commit -m "feat(frontend): add ValuationChart component for ratio metrics"
```

---

## Task 5: Frontend - Create StockAnalytics Component

**Files:**
- Create: `frontend/src/components/StockAnalytics.jsx`

**Step 1: Create StockAnalytics component**

Create `frontend/src/components/StockAnalytics.jsx`:

```jsx
import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import PriceChart from './PriceChart';
import ValuationChart from './ValuationChart';

const API_BASE = 'http://localhost:8000';

export default function StockAnalytics({ symbol }) {
  const [activeTab, setActiveTab] = useState('price');
  const [priceData, setPriceData] = useState(null);
  const [ratiosData, setRatiosData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const [priceRes, ratiosRes] = await Promise.all([
          fetch(`${API_BASE}/api/securities/${symbol}?include=history`, {
            credentials: 'include',
          }),
          fetch(`${API_BASE}/api/securities/${symbol}/ratios?period=quarterly&limit=12`, {
            credentials: 'include',
          })
        ]);

        if (priceRes.ok) {
          const data = await priceRes.json();
          setPriceData(data.history || []);
        }

        if (ratiosRes.ok) {
          const data = await ratiosRes.json();
          setRatiosData(data);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [symbol]);

  if (loading) {
    return (
      <div className="bg-gray-50 border-t border-gray-200 p-4">
        <div className="text-center text-gray-500 py-8">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-50 border-t border-gray-200 p-4">
        <div className="text-center text-red-600 py-8">Error loading data: {error}</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 border-t border-gray-200 p-4">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="price">Price History</TabsTrigger>
          <TabsTrigger value="valuation">Valuation Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="price" className="mt-0">
          {priceData && priceData.length > 0 ? (
            <div className="bg-white rounded-lg p-4">
              <PriceChart symbol={symbol} data={priceData} />
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">No price data available</div>
          )}
        </TabsContent>

        <TabsContent value="valuation" className="mt-0">
          {ratiosData && ratiosData.length > 0 ? (
            <div className="bg-white rounded-lg">
              <ValuationChart data={ratiosData} />
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">No valuation data available</div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

**Step 2: Verify component syntax**

```bash
npm run lint src/components/StockAnalytics.jsx
```

Expected: No new errors

**Step 3: Commit**

```bash
git add src/components/StockAnalytics.jsx
git commit -m "feat(frontend): add StockAnalytics tabbed component"
```

---

## Task 6: Frontend - Update PriceChart to Accept Data Prop

**Files:**
- Modify: `frontend/src/components/PriceChart.jsx`

**Step 1: Update PriceChart to accept data prop**

Modify `frontend/src/components/PriceChart.jsx` to accept optional `data` prop:

Find the component signature (line 14) and update:

```jsx
export default function PriceChart({ symbol, data: externalData }) {
```

Then update the useEffect to skip fetching if data is provided (around line 19-46):

```jsx
useEffect(() => {
  if (!symbol || externalData) return; // Skip fetch if data provided

  const fetchChartData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/securities/${symbol}?include=history`,
        { credentials: 'include' }
      );

      if (response.ok) {
        const stockData = await response.json();
        setData(stockData.history || []);
      } else {
        setError('Failed to load chart data');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  fetchChartData();
}, [symbol, externalData]);
```

Add this after the useEffect:

```jsx
// Use external data if provided, otherwise use fetched data
const chartData = externalData || data;
```

Then update all references to `data` in the render to use `chartData`:

- Line 59: `if (error || !chartData || chartData.length === 0) {`
- Line 73: `const prices = chartData.map((d) => d.close);`
- Line 81: `const firstPrice = chartData[0]?.close || 0;`
- Line 82: `const lastPrice = chartData[chartData.length - 1]?.close || 0;`
- Line 94: `<LineChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>`

**Step 2: Verify component syntax**

```bash
npm run lint src/components/PriceChart.jsx
```

Expected: No new errors

**Step 3: Commit**

```bash
git add src/components/PriceChart.jsx
git commit -m "refactor(frontend): make PriceChart accept optional data prop"
```

---

## Task 7: Frontend - Update StockRow Component

**Files:**
- Modify: `frontend/src/components/StockRow.jsx`

**Step 1: Add imports and state**

At the top of `frontend/src/components/StockRow.jsx`, add import:

```jsx
import { useState } from 'react';
import StockAnalytics from './StockAnalytics';
```

Update the component signature (line 1) and add state:

```jsx
export default function StockRow({ item, onRemove }) {
  const [expanded, setExpanded] = useState(false);
```

**Step 2: Remove onSelect and isSelected**

Remove these props from the function signature and remove any code that uses them (the onClick handler on line 55 and the border styling on line 57).

Update the main container (around line 54-59):

```jsx
<div className="bg-white rounded-lg shadow-sm p-3 border-2 border-transparent hover:border-gray-200 transition">
```

Remove the onClick handler from this div.

**Step 3: Add toggle button**

Add the toggle button before the remove button (around line 100-113):

```jsx
{/* Analytics Toggle Button */}
<button
  onClick={(e) => {
    e.stopPropagation();
    setExpanded(!expanded);
  }}
  className="text-gray-600 hover:text-gray-900 transition p-2 mr-2"
  title={expanded ? "Hide analytics" : "Show analytics"}
>
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d={expanded ? "M19 9l-7 7-7-7" : "M9 5l7 7-7 7"}
    />
  </svg>
</button>

{/* Remove Button */}
<button
```

**Step 4: Add StockAnalytics below**

After the closing `</div>` of the main row content (before the final closing div, around line 121), add:

```jsx
    </div>

    {/* Analytics Panel */}
    {expanded && <StockAnalytics symbol={item.symbol} />}
  </div>
```

**Step 5: Update padding**

Change `p-4` to `p-3` in the main container (line 54).

**Step 6: Verify component syntax**

```bash
npm run lint src/components/StockRow.jsx
```

Expected: No new errors

**Step 7: Commit**

```bash
git add src/components/StockRow.jsx
git commit -m "feat(frontend): add expandable analytics to StockRow"
```

---

## Task 8: Frontend - Update WatchlistDetail Layout

**Files:**
- Modify: `frontend/src/pages/WatchlistDetail.jsx`

**Step 1: Remove selectedStock state**

Remove the line (around line 17):

```jsx
const [selectedStock, setSelectedStock] = useState(null);
```

**Step 2: Update header padding**

Update header padding (line 156):

```jsx
<div className="max-w-7xl mx-auto px-3 sm:px-4 py-3">
```

**Step 3: Update main content padding**

Update main content padding (line 189):

```jsx
<main className="max-w-7xl mx-auto px-3 sm:px-4 py-4">
```

**Step 4: Remove grid layout and right panel**

Replace the grid layout (lines 190-234) with single column:

```jsx
<main className="max-w-7xl mx-auto px-3 sm:px-4 py-4">
  {/* Stocks List */}
  {items.length === 0 ? (
    <div className="bg-white rounded-lg shadow-sm p-12 text-center">
      <p className="text-gray-500 mb-4">No stocks in this watchlist</p>
      <button
        onClick={() => setShowAddModal(true)}
        className="text-indigo-600 hover:text-indigo-700 font-medium"
      >
        Add your first stock
      </button>
    </div>
  ) : (
    <div className="space-y-1.5">
      {items.map((item) => (
        <StockRow
          key={item.id}
          item={item}
          onRemove={() => removeStock(item.id)}
        />
      ))}
    </div>
  )}

  {items.length >= 50 && (
    <div className="mt-4 text-center text-sm text-gray-500">
      Maximum stocks reached (50/50)
    </div>
  )}
</main>
```

**Step 5: Update stock row spacing**

Change `space-y-2` to `space-y-1.5` in the stocks container.

**Step 6: Update StockRow props**

Remove `onSelect` and `isSelected` props from StockRow component calls (around line 206-211).

**Step 7: Verify component syntax**

```bash
npm run lint src/pages/WatchlistDetail.jsx
```

Expected: No new errors

**Step 8: Commit**

```bash
git add src/pages/WatchlistDetail.jsx
git commit -m "refactor(frontend): remove right panel and reduce white space"
```

---

## Task 9: Manual Testing

**Files:**
- None (testing only)

**Step 1: Start the application**

```bash
# In terminal 1 (backend)
docker-compose up -d
docker-compose logs -f backend

# In terminal 2 (frontend)
cd frontend
npm run dev
```

**Step 2: Test basic functionality**

1. Open http://localhost:5173
2. Login with test credentials
3. Open a watchlist
4. Verify stocks display correctly
5. Click chevron icon on a stock row
6. Verify analytics panel expands below
7. Verify "Price History" tab shows chart
8. Click "Valuation Metrics" tab
9. Verify P/E, P/B, P/S charts display
10. Click chevron again to collapse
11. Verify panel collapses

**Step 3: Test edge cases**

1. Expand multiple stocks at once - verify all work independently
2. Test with a stock that has missing ratio data
3. Test on mobile viewport (resize browser)
4. Verify tabs are responsive

**Step 4: Document any issues**

Create notes file if issues found:

```bash
echo "# Manual Testing Notes" > TESTING_NOTES.md
echo "" >> TESTING_NOTES.md
echo "## Issues Found:" >> TESTING_NOTES.md
```

---

## Task 10: Update Documentation

**Files:**
- Modify: `CLAUDE.md` (update frontend architecture section)
- Modify: `docs/reference/architecture/frontend.md` (if exists)

**Step 1: Update CLAUDE.md**

Update the Frontend Structure section in `CLAUDE.md`:

```markdown
### Frontend Structure
- Pages: Login, Watchlists (list), WatchlistDetail
- Components:
  - StockRow (live data, expandable analytics)
  - StockAnalytics (tabbed analytics panel)
  - PriceChart (recharts, price history)
  - ValuationChart (recharts, P/E, P/B, P/S ratios)
- UI: shadcn/ui components in `components/ui/`
- Routing: React Router with ProtectedRoute wrapper
```

**Step 2: Commit documentation**

```bash
git add CLAUDE.md
git commit -m "docs: update frontend structure for analytics feature"
```

---

## Task 11: Final Verification and Cleanup

**Files:**
- None

**Step 1: Run full build**

```bash
cd frontend
npm run build
```

Expected: Build succeeds with no errors

**Step 2: Check git status**

```bash
git status
```

Expected: Working tree clean (all changes committed)

**Step 3: Review commit history**

```bash
git log --oneline -15
```

Expected: Clean, descriptive commits for each task

**Step 4: Push branch** (optional, if ready for review)

```bash
git push -u origin feature/stock-analytics-tabs
```

---

## Summary

**Total Tasks:** 11
**Estimated Time:** 2-3 hours
**Key Dependencies:** OpenBB SDK (FMP provider), shadcn/ui Tabs
**Testing:** Manual testing required (no automated tests in current project)

**Success Criteria:**
- ✅ Backend endpoint returns financial ratios
- ✅ StockRow has expandable analytics panel
- ✅ Tabs switch between price and valuation views
- ✅ All three ratio charts display correctly
- ✅ Right panel removed, white space reduced
- ✅ No console errors
- ✅ Mobile responsive
