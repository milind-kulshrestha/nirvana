# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

## [2025-12-29] - Stock Analytics with Expandable Tabs

### Added
- **Expandable stock analytics** below each stock row with chevron toggle button
- **Tabbed interface** for organizing analytics: "Price History" | "Valuation Metrics"
- **Financial ratios charts** displaying P/E, P/B, and P/S ratios
  - Three separate charts (200px height each)
  - Black line styling for all ratio charts
  - Interactive tooltips with formatted dates and values
- **New backend endpoint** `GET /api/securities/{symbol}/ratios`
  - Returns historical financial ratios (P/E, P/B, P/S)
  - Requires authentication
  - Uses OpenBB equity.fundamental.ratios endpoint
- **New frontend components**:
  - `StockAnalytics.jsx` - Tabbed container with parallel data fetching
  - `ValuationChart.jsx` - Three-chart display for financial ratios
  - `Tabs` component from shadcn/ui
- **Helper functions** in `backend/app/lib/openbb.py`:
  - `_format_date()` - DRY date formatting
  - `_safe_float_attr()` - Safe attribute extraction from OpenBB results
  - `get_financial_ratios()` - Fetch P/E, P/B, P/S ratios

### Changed
- **Removed right panel** from WatchlistDetail (reserved for future agent integration)
- **Single-column layout** with all analytics inline below stocks
- **Reduced white space** throughout UI:
  - Header padding: `py-3 px-3 sm:px-4`
  - Main content: `py-4 px-3 sm:px-4`
  - Stock rows: `p-3`
- **StockRow component** now has expandable analytics section
  - Independent expand/collapse state per row
  - Smooth transitions
  - Generic toggle button (not chart-specific)
- **PriceChart component** now accepts optional `data` prop
  - Prevents redundant API calls when used in StockAnalytics
  - Backward compatible (fetches data if not provided)

### Fixed
- **Race condition prevention** in StockAnalytics component
  - Cleanup function cancels in-flight requests on unmount
  - Prevents stale data from overwriting current state
- **Silent API error handling** - Errors now displayed to users instead of showing "No data available"
- **Prop validation** - Components validate required props before attempting API calls

### Technical Details
- **Parallel data fetching** using `Promise.all()` in StockAnalytics
- **Data caching** - Tab switching doesn't re-fetch data
- **Comprehensive error handling**: 404 (symbol not found), 504 (timeout), 500 (internal)
- **DRY code improvements** with helper functions
- **FMP free tier limitation**: Returns TTM (trailing twelve months) data only, no historical quarterly data
- **19 commits** with two-stage code review (spec compliance + code quality)
- **Updated documentation**: CLAUDE.md, frontend-architecture.md, backend-architecture.md
- **Testing notes** documented in TESTING_NOTES.md

## [2025-12-27] - CORS Configuration Fix

### Fixed
- Improved CORS configuration for preflight requests
- Added explicit OPTIONS method support
- Added `expose_headers` and `max_age` to CORS middleware

### Technical Details
- Updated `backend/app/main.py` with comprehensive CORS settings
- Ensures proper cross-origin authentication with credentials

## [2025-12-27] - Frontend and Documentation

### Added
- Complete React frontend with Vite and TailwindCSS
- shadcn/ui component library integration
- Login/Register page (LoginNew.jsx)
- Watchlists listing page (WatchlistsNew.jsx)
- Watchlist detail page with live stock data (WatchlistDetail.jsx)
- StockRow component for displaying live market data
- PriceChart component using Recharts for 6-month price history
- Zustand store for authentication state management
- Comprehensive project documentation in `docs/`
  - Backend Architecture reference
  - Frontend Architecture reference
  - Database schema reference
  - OpenBB API reference
  - Development guide
  - Project status tracking
  - Changelog
- CLAUDE.md for AI assistant context
- CORS configuration in FastAPI backend

### Technical Details
- Frontend runs on http://localhost:5173
- Backend API on http://localhost:8000
- Session-based authentication with HTTP-only cookies
- Live market data from OpenBB SDK
- Responsive design with TailwindCSS utilities
- Documentation structure in `docs/reference/` for technical references

## [2025-11-29] - Initial Backend (Week 1)

### Added
- FastAPI backend with SQLAlchemy ORM
- PostgreSQL database integration
- User authentication system
  - Session-based auth with signed cookies (itsdangerous)
  - Bcrypt password hashing
  - Login, register, logout endpoints
- Database models
  - User model with email and password
  - Watchlist model for user's watchlists
  - WatchlistItem model for stocks in watchlists
- Watchlist management endpoints
  - Create, list, delete watchlists
  - Add/remove stocks from watchlists
- Securities endpoint for market data
  - Real-time stock quotes
  - 200-day moving average
  - Historical price data
- OpenBB SDK integration
  - FMP (Financial Modeling Prep) provider
  - Quote, MA, and historical data fetching
  - Custom error handling
- Alembic database migrations
- Docker Compose setup
  - PostgreSQL service
  - Backend service with hot reload
- Environment-based configuration
- Input validation and error handling

### Technical Details
- PostgreSQL 15 with cascade deletes
- OpenBB Platform for market data
- Session tokens with 7-day expiration
- RESTful API design
- Automatic API docs at /docs endpoint