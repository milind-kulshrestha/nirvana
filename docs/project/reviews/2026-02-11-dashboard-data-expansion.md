# Review: Dashboard Data Expansion
**Date:** 2026-02-11
**Changelog Entry:** [2026-02-11] - Dashboard Data Expansion
**Commits:** `da65929..e756056`
**Status:** 🔴 Not Started

---

## UI Changes to Review

### 1. OHLCV Candlestick Chart
- **What changed:** Replaced Recharts line chart with TradingView Lightweight Charts (candlestick + volume histogram overlay)
- **Where to look:** Watchlist detail → expand any stock row
- **Files:** `frontend/src/components/CandlestickChart.jsx`, `frontend/src/components/StockRow.jsx`
- **Screenshot:** <!-- paste or attach -->
- [ ] **Looks correct** — candles render, volume bars visible
- [ ] **Styling matches design system** — colors, fonts, spacing
- [ ] **Responsive/resize behavior OK** — ResizeObserver working on window resize
- [ ] **TradingView attribution** visible and links correctly
- **Feedback:**
 - get rid of period start and period end prices that are displayed below the chart
 - Is it possible to have drawing tools/indicators on the chart?
 - Change teh chart type

### 2. Multi-Period Performance Tiles
- **What changed:** Heatmap-style return badges (1D/1W/1M/3M/6M/YTD/1Y) in expanded stock panel
- **Where to look:** Watchlist detail → expand any stock row → below chart
- **Files:** `frontend/src/components/PerformanceTiles.jsx`
- **Screenshot:** <!-- paste or attach -->
- [ ] **Looks correct** — all 7 periods display with return %
- [ ] **Styling matches design system** — green/red color coding readable
- [ ] **Responsive/resize behavior OK** — tiles wrap on narrow screens
- **Feedback:**
 - Performance tiles should be moved to the stock row?

### 3. Analyst Estimates Badge
- **What changed:** Inline consensus pill (Buy/Hold/Sell + target price delta) in stock row
- **Where to look:** Watchlist detail → each stock row (collapsed view)
- **Files:** `frontend/src/components/EstimatesBadge.jsx`, `frontend/src/components/StockRow.jsx`
- **Screenshot:** <!-- paste or attach -->
- [ ] **Looks correct** — badge shows consensus + target delta
- [ ] **Styling matches design system** — pill colors, typography
- [ ] **Responsive/resize behavior OK** — doesn't overflow on small screens
- **Feedback:**
 - Not visible at all


### 4. Market Discovery Page
- **What changed:** New `/discover` route with tabbed view (Most Active, Top Gainers, Top Losers)
- **Where to look:** Navigate to `/discover` from header nav
- **Files:** `frontend/src/components/` (Discovery page component), `frontend/src/App.jsx` (route)
- **Screenshot:** <!-- paste or attach -->
- [ ] **Looks correct** — tabs switch, data populates
- [ ] **Styling matches design system** — consistent with watchlist pages
- [ ] **Responsive/resize behavior OK**
- [ ] **Watchlist "WL" badge** highlights symbols already in watchlist
- **Feedback:**
 - Need sorting functionality for top gainers/losers.
 - Can we add Mcap and Industry/Sector columns along with returns?
 - Volume is NA for all symbols in 
 - We should have a seperate tab for studying market breadth, ytd performance, etc.
 - only price change is visible in discovery page (% change is  0 % for all symbols)

### 5. Calendar Widget
- **What changed:** Upcoming earnings and dividend events sidebar with tabs
- **Where to look:** `/discover` page → right sidebar / calendar section
- **Files:** `frontend/src/components/CalendarWidget.jsx`
- **Screenshot:** <!-- paste or attach -->
- [ ] **Looks correct** — Earnings/Dividends tabs, events listed
- [ ] **Styling matches design system**
- [ ] **"My Stocks" toggle** filters to watchlist symbols
- [ ] **Countdown badges** appear for events within 7 days
- **Feedback:**
  - Earnings calender doesn't show any dates for any symbol

### 6. Navigation Updates
- **What changed:** Cross-navigation between Watchlists ↔ Discover in page headers
- **Where to look:** Header area on both Watchlist and Discover pages
- **Files:** `frontend/src/App.jsx`, relevant page components
- **Screenshot:** <!-- paste or attach -->
- [ ] **Looks correct** — links present and functional
- [ ] **Styling matches design system** — consistent header treatment
- [ ] **Active state** correctly highlights current page
- **Feedback:**
 

---

## Functional Checks

- [ ] App starts without errors (`npm run tauri dev` or backend + vite)
- [ ] Navigation between Watchlists ↔ Discover works
- [ ] Stock data loads correctly (quotes, OHLCV, performance, estimates)
- [ ] Lazy-loading on expand doesn't cause flicker or double-fetch
- [ ] Error states handled (e.g., missing API key, network failure)
- [ ] Loading states present and smooth (spinners/skeletons)
- [ ] Calendar data loads for both earnings and dividends

---

## Overall Feedback

### What works well
-

### Issues found
| # | Severity | Component | Description | Action |
|---|----------|-----------|-------------|--------|
| 1 | | | | |

### Design/UX suggestions
-

### Questions for next session
-
