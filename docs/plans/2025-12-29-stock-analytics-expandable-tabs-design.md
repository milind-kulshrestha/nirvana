# Stock Analytics with Expandable Tabs - Design Document

**Date:** 2025-12-29
**Status:** Approved
**Goal:** Refactor watchlist UI to show expandable analytics below each stock with tabbed interface

## Overview

Replace the current right-panel chart layout with an expandable analytics section below each stock row. Display price history and valuation metrics (P/E, P/B, P/S ratios) in separate tabs. Reduce white space throughout the interface.

## Requirements

1. Remove right panel (reserve for future agent integration)
2. Add expandable analytics section below each stock row
3. Generic toggle button (not chart-specific)
4. Tabbed interface: "Price History" | "Valuation Metrics"
5. Display P/E, P/B, P/S ratios as three separate charts (black lines)
6. Reduce white space (top and left padding)
7. Fetch historical ratios from OpenBB (quarterly, 12 periods = 3 years)

## Architecture & Data Flow

### Backend Changes

**New OpenBB Function** (`backend/app/lib/openbb.py`):
- `get_financial_ratios(symbol, period='quarterly', limit=12)`
- Fetches P/E, P/B, P/S ratios using `obb.equity.fundamental.ratios()`
- Returns: `[{date, pe_ratio, pb_ratio, ps_ratio}, ...]`
- Handles errors: `SymbolNotFoundError`, `OpenBBTimeoutError`

**New API Endpoint** (`backend/app/routes/securities.py`):
- `GET /api/securities/{symbol}/ratios?period=quarterly&limit=12`
- Returns formatted ratios data
- Authenticated (requires current_user)

### Frontend Changes

**Component Updates:**

1. **WatchlistDetail.jsx**
   - Remove grid layout (`lg:grid-cols-3`)
   - Remove right panel entirely
   - Reduce padding: `px-3 sm:px-4 py-4` (was `px-4 sm:px-6 lg:px-8 py-8`)
   - Remove `selectedStock` state (no longer needed)

2. **StockRow.jsx**
   - Add state: `const [expanded, setExpanded] = useState(false)`
   - Add chevron toggle button (before remove button)
   - Remove `onSelect` prop and click handler
   - Conditionally render `<StockAnalytics>` when expanded
   - Reduce padding: `p-3` (was `p-4`)

3. **New Component: StockAnalytics.jsx**
   - Fetches price history and ratios in parallel
   - Tabbed interface using shadcn/ui Tabs
   - Manages loading/error states per tab
   - Tabs: "Price History" | "Valuation Metrics"

4. **PriceChart.jsx** (existing)
   - Move from right panel to first tab in StockAnalytics
   - No structural changes needed

5. **New Component: ValuationChart.jsx**
   - Three separate charts stacked vertically
   - P/E Ratio (top)
   - P/B Ratio (middle)
   - P/S Ratio (bottom)
   - Each chart: 200px height, black line, recharts LineChart
   - Title above each chart

## Data Flow

```
User clicks toggle → StockRow sets expanded=true
                  → StockAnalytics mounts
                  → Parallel fetch:
                      - GET /api/securities/{symbol}?include=history
                      - GET /api/securities/{symbol}/ratios
                  → Cache both datasets
                  → Tab switching uses cached data (no re-fetch)
```

## Component Structure

```
WatchlistDetail
├── StockRow (MSFT)
│   ├── Toggle button ▶
│   └── StockAnalytics (expanded)
│       ├── Tabs: ["Price History", "Valuation Metrics"]
│       ├── Tab 1: PriceChart
│       └── Tab 2: ValuationChart
│           ├── P/E Ratio chart
│           ├── P/B Ratio chart
│           └── P/S Ratio chart
├── StockRow (NVDA)
│   └── Toggle button ▼ (collapsed)
└── StockRow (AAPL)
    └── Toggle button ▼ (collapsed)
```

## Implementation Details

### Backend: OpenBB Integration

```python
def get_financial_ratios(symbol: str, period: str = "quarterly", limit: int = 12) -> list[dict]:
    """Fetch historical financial ratios (P/E, P/B, P/S)."""
    try:
        data = obb.equity.fundamental.ratios(
            symbol=symbol,
            period=period,
            limit=limit,
            provider="fmp"
        )

        if not data or not data.results:
            raise SymbolNotFoundError(f"No ratios data for {symbol}")

        return [
            {
                "date": result.date.strftime("%Y-%m-%d"),
                "pe_ratio": float(result.price_earnings_ratio) if hasattr(result, 'price_earnings_ratio') else None,
                "pb_ratio": float(result.price_to_book_ratio) if hasattr(result, 'price_to_book_ratio') else None,
                "ps_ratio": float(result.price_to_sales_ratio) if hasattr(result, 'price_to_sales_ratio') else None,
            }
            for result in data.results
        ]
    except Exception as e:
        if "timeout" in str(e).lower():
            raise OpenBBTimeoutError(f"Timeout fetching ratios for {symbol}")
        raise SymbolNotFoundError(f"Error fetching ratios: {str(e)}")
```

### Backend: API Endpoint

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

### Frontend: StockAnalytics Component

```jsx
export default function StockAnalytics({ symbol }) {
  const [activeTab, setActiveTab] = useState('price');
  const [priceData, setPriceData] = useState(null);
  const [ratiosData, setRatiosData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [priceRes, ratiosRes] = await Promise.all([
          fetch(`http://localhost:8000/api/securities/${symbol}?include=history`, {
            credentials: 'include'
          }),
          fetch(`http://localhost:8000/api/securities/${symbol}/ratios?period=quarterly&limit=12`, {
            credentials: 'include'
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

  return (
    <div className="bg-gray-50 border-t border-gray-200 p-4">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="price">Price History</TabsTrigger>
          <TabsTrigger value="valuation">Valuation Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="price">
          {loading ? (
            <div>Loading chart...</div>
          ) : priceData ? (
            <PriceChart symbol={symbol} data={priceData} />
          ) : (
            <div>No price data available</div>
          )}
        </TabsContent>

        <TabsContent value="valuation">
          {loading ? (
            <div>Loading ratios...</div>
          ) : ratiosData ? (
            <ValuationChart data={ratiosData} />
          ) : (
            <div>No valuation data available</div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### Frontend: ValuationChart Component

```jsx
export default function ValuationChart({ data }) {
  const chartConfig = {
    height: 200,
    margin: { top: 5, right: 20, left: 10, bottom: 5 }
  };

  const renderMetricChart = (dataKey, title) => (
    <div className="mb-6">
      <h4 className="text-sm font-semibold text-gray-700 mb-2">{title}</h4>
      <ResponsiveContainer width="100%" height={chartConfig.height}>
        <LineChart data={data} margin={chartConfig.margin}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(date) => {
              const d = new Date(date);
              return `${d.getMonth() + 1}/${d.getDate().toString().slice(-2)}`;
            }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => value.toFixed(1)}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
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

### Frontend: StockRow Toggle Button

```jsx
{/* Add before remove button */}
<button
  onClick={(e) => {
    e.stopPropagation();
    setExpanded(!expanded);
  }}
  className="text-gray-600 hover:text-gray-900 transition p-2"
  title="Show analytics"
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

{/* Add below main row content */}
{expanded && <StockAnalytics symbol={item.symbol} />}
```

## UI/UX Details

### White Space Reduction

**Header:**
- Padding: `py-3` (was `py-4`)
- Container: `px-3 sm:px-4` (was `px-4 sm:px-6 lg:px-8`)

**Main Content:**
- Padding: `px-3 sm:px-4 py-4` (was `px-4 sm:px-6 lg:px-8 py-8`)

**Stock Rows:**
- Padding: `p-3` (was `p-4`)
- Gap between rows: `space-y-1.5` (was `space-y-2`)

### Styling

**StockAnalytics Panel:**
- Background: `bg-gray-50`
- Border: `border-t border-gray-200`
- Padding: `p-4`
- Smooth transitions for expand/collapse

**Charts:**
- All lines: Black (`#000000`)
- Grid: Light gray (`#e5e7eb`)
- Height: 200px per chart
- No dots on lines (except active point)

**Tabs:**
- Use shadcn/ui Tabs component
- Clean, minimal style

## Mobile Responsiveness

- Charts maintain full width on mobile
- Tabs remain horizontal (scrollable if needed)
- Volume column already hidden on mobile (`hidden md:block`)
- All charts stack vertically

## Error Handling

**Backend:**
- `SymbolNotFoundError` → 404 response
- `OpenBBTimeoutError` → 504 response
- Invalid parameters → 400 response

**Frontend:**
- Loading states: Skeleton/spinner per tab
- Error states: User-friendly message per tab
- Missing data: "No data available" message
- Failed fetches: Show error, allow retry

## Testing Considerations

1. Test with stocks that have incomplete ratio data
2. Test expand/collapse transitions
3. Test parallel data fetching
4. Test tab switching performance
5. Test mobile responsiveness
6. Test error states (invalid symbol, timeout)
7. Test with many expanded stocks (memory/performance)

## Future Enhancements

- Add more tabs (ROE, debt ratios, etc.)
- Add date range selector
- Cache ratios data in localStorage
- Add comparison mode (overlay multiple stocks)
- Export chart data to CSV
