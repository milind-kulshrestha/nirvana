# Historical Valuation Metrics Feature Design

**Date:** 2025-12-29
**Status:** Approved
**Metrics:** P/E Ratio, EV/EBITDA
**Visualization:** Dual y-axis timeline chart combined with price data

## Overview

Add historical valuation metrics (P/E Ratio and EV/EBITDA) to the stock watchlist detail view. Display metrics as timeline charts combined with existing price charts using a dual y-axis approach.

## Architecture & Data Flow

### Backend Architecture

New module `app/lib/openbb_fundamentals.py` alongside existing `openbb.py` for fundamental data operations.

**New OpenBB Functions:**
1. `get_historical_fundamentals(symbol, months=6)` - Fetches historical earnings, EBITDA, shares outstanding, debt, and cash
2. `calculate_historical_pe(symbol, months=6)` - Combines price history with earnings data to compute P/E ratio over time
3. `calculate_historical_ev_ebitda(symbol, months=6)` - Computes EV/EBITDA using market cap, debt, cash, and EBITDA

### Data Flow

```
User selects stock
    ↓
Frontend requests /api/securities/{symbol}?include=quote,ma200,valuation_history
    ↓
Backend checks cache (in-memory) for recent valuation data
    ↓
If cache miss: Fetch from OpenBB (price history + fundamentals) → Calculate ratios → Cache for 1 hour
    ↓
Return combined data: { quote, ma_200, valuation_history: [{ date, pe_ratio, ev_ebitda }] }
    ↓
Frontend PriceChart component renders dual y-axis chart with Recharts
```

### API Enhancement

Extend existing `/api/securities/{symbol}` endpoint to support `include=valuation_history` query parameter. Maintains consistency with current pattern (`include=quote,ma200`).

## Backend Implementation

### OpenBB Data Requirements

**P/E Ratio Calculation:**
- Historical prices (via `obb.equity.price.historical`)
- Earnings per Share (EPS) from `obb.equity.fundamental.metrics` or `obb.equity.fundamental.earnings`
- Formula: `P/E = Price / EPS`

**EV/EBITDA Calculation:**
- Market Cap = Price × Shares Outstanding
- Enterprise Value = Market Cap + Total Debt - Cash
- Required data: `shares_outstanding`, `total_debt`, `cash_and_equivalents`, `ebitda`
- Formula: `EV/EBITDA = (Market Cap + Debt - Cash) / EBITDA`

### File Structure

```
backend/app/lib/openbb_fundamentals.py
  - get_fundamental_data(symbol) → fetches latest fundamental metrics
  - get_historical_valuation_metrics(symbol, months=6) → returns list of {date, pe_ratio, ev_ebitda}

backend/app/routes/securities.py (modify existing)
  - Update GET /securities/{symbol} to handle include=valuation_history
```

### Caching Strategy

- In-memory cache with TTL of 1 hour (fundamental data changes infrequently)
- Cache key format: `valuation:{symbol}:{months}:{date}`
- Graceful fallback if OpenBB data is incomplete (return None for missing metrics)

### Error Handling

- If fundamental data unavailable → return `valuation_history: null` (chart shows price only)
- If partial data (e.g., have P/E but not EV/EBITDA) → return what's available
- Log errors but don't fail the entire request

## Frontend Implementation

### PriceChart Component Updates

Enhance existing `PriceChart.jsx` component to support dual y-axis visualization.

**Component Changes:**
- Fetch valuation_history along with price history
- Add toggle controls for "Price", "P/E Ratio", "EV/EBITDA" (checkboxes or chips)
- Use Recharts `<ComposedChart>` with dual `<YAxis>` components
  - Left Y-axis: Stock price (primary)
  - Right Y-axis: Valuation metrics (secondary)
- Three line series:
  1. Price line (blue, solid, left axis)
  2. P/E Ratio line (green, dashed, right axis)
  3. EV/EBITDA line (purple, dashed, right axis)

### API Integration

```javascript
const response = await fetch(
  `${API_BASE}/api/securities/${symbol}?include=history,valuation_history`,
  { credentials: 'include' }
);
const data = await response.json();
// Expected structure:
// {
//   history: [{date, close}],
//   valuation_history: [{date, pe_ratio, ev_ebitda}]
// }
```

### Visual Design

- Legend shows metric-to-color mapping
- Tooltip on hover displays all values for selected date
- If valuation data is null/unavailable, display "Fundamental data unavailable" message
- Maintain existing 6-month time range to align with price data

## Testing Strategy

### Backend Tests

```python
# tests/test_openbb_fundamentals.py
- test_get_historical_valuation_metrics_success()
- test_get_historical_valuation_metrics_invalid_symbol()
- test_calculate_pe_ratio_with_negative_earnings()
- test_ev_ebitda_with_missing_debt_data()
- test_caching_behavior()
```

### Frontend Tests

- Test dual y-axis rendering with mock data
- Test toggle controls show/hide lines correctly
- Test graceful degradation when `valuation_history` is null
- Test tooltip displays all metrics for selected date

## Edge Cases

### 1. Negative Earnings (Negative P/E)
**Problem:** Unprofitable companies have negative or undefined P/E
**Solution:** Return `null` for P/E when earnings ≤ 0, chart skips those points

### 2. Missing Fundamental Data
**Problem:** Some stocks (especially small caps) may lack complete data
**Solution:** Return partial data or null, show chart with available metrics only

### 3. Data Alignment
**Problem:** Price history is daily, fundamental data might be quarterly
**Solution:** Forward-fill fundamental values (use last known value until next earnings report)

### 4. Extreme Outliers
**Problem:** Very high P/E ratios (>1000) can skew chart scale
**Solution:** Cap display at reasonable max (e.g., 100) or use logarithmic scale for right y-axis

## Implementation Timeline

**Phase 1: Backend Foundation**
- Create `openbb_fundamentals.py` module
- Implement fundamental data fetching functions
- Add valuation metric calculations
- Implement caching layer

**Phase 2: API Integration**
- Extend `/api/securities/{symbol}` endpoint
- Add `include=valuation_history` support
- Write backend tests

**Phase 3: Frontend Visualization**
- Update `PriceChart.jsx` for dual y-axis
- Add toggle controls for metrics
- Implement responsive tooltip
- Handle error states

**Phase 4: Testing & Refinement**
- End-to-end testing
- Edge case validation
- Performance optimization
- Documentation updates
