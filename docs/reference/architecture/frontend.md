# Frontend Architecture

## Tech Stack

- **Framework**: React 19
- **Build Tool**: Vite
- **Routing**: React Router v7
- **Styling**: TailwindCSS + shadcn/ui
- **State Management**: Zustand (auth, AI chat)
- **Charts**: TradingView Lightweight Charts (candlestick + volume)
- **UI Components**: Radix UI primitives
- **AI Integration**: SSE streaming with EventSource

## Project Structure

```
frontend/src/
├── components/
│   ├── ui/              # shadcn/ui components
│   │   ├── button.jsx
│   │   ├── card.jsx
│   │   ├── dialog.jsx
│   │   ├── dropdown-menu.jsx
│   │   ├── table.jsx
│   │   └── ...
│   ├── ai/              # AI agent components
│   │   ├── AISidebar.jsx        # Chat interface
│   │   ├── AIToggleButton.jsx   # Floating toggle
│   │   └── SendToAIButton.jsx   # Context capture button
│   ├── PriceChart.jsx       # Legacy line chart (replaced by CandlestickChart)
│   ├── CandlestickChart.jsx # OHLCV candlestick + volume chart (Lightweight Charts)
│   ├── PerformanceTiles.jsx # Multi-period return heatmap tiles
│   ├── EstimatesBadge.jsx   # Analyst consensus pill badge
│   ├── CalendarWidget.jsx   # Earnings/dividends calendar widget
│   └── StockRow.jsx         # Individual stock display with expanded panel
├── pages/
│   ├── LoginNew.jsx     # Login/register page
│   ├── WatchlistsNew.jsx # Watchlist list
│   ├── WatchlistDetail.jsx # Watchlist view
│   └── Discover.jsx     # Market discovery + calendar
├── stores/
│   ├── authStore.js     # Zustand auth state
│   ├── aiChatStore.js   # Zustand AI chat state
│   └── aiComponentStore.js # Component registry
├── hooks/
│   └── useAISerializable.js # AI component registration
├── lib/
│   └── utils.js         # Tailwind utility functions
├── App.jsx              # Router setup
├── main.jsx             # React entry point
└── index.css            # Global styles
```

## Key Files

### `App.jsx`
- React Router setup with BrowserRouter
- `ProtectedRoute` component that checks auth state
- AI sidebar integration (conditionally rendered when authenticated)
- Routes:
  - `/` - LoginNew (public)
  - `/watchlists` - WatchlistsNew (protected)
  - `/watchlists/:id` - WatchlistDetail (protected)
  - `/discover` - Discover (protected)
  - `/settings` - Settings (protected)

### `stores/authStore.js`
Zustand store for authentication state:

**State:**
- `user` - Current user object `{user_id, email}` or null
- `loading` - Boolean loading state
- `error` - Error message or null

**Actions:**
- `checkAuth()` - Verify session with `/api/auth/me`
- `register(email, password)` - Register and auto-login
- `login(email, password)` - Login and set user state
- `logout()` - Clear session and user state
- `clearError()` - Reset error message

**API Communication:**
- Base URL: `http://localhost:8000`
- All requests use `credentials: 'include'` for cookies
- Returns boolean success/failure

### `stores/aiChatStore.js`
Zustand store for AI chat state and SSE streaming:

**State:**
- `messages` - Array of chat messages (user/assistant)
- `conversations` - List of conversation history
- `currentConversationId` - Active conversation ID
- `isStreaming` - Boolean streaming indicator
- `pendingActions` - Actions awaiting user approval
- `toolCalls` - Active tool executions

**Actions:**
- `sendMessage(text, componentContext)` - Send user message via SSE
- `loadConversations()` - Fetch conversation history
- `switchConversation(id)` - Load different conversation
- `confirmAction(actionId)` - Approve pending action
- `rejectAction(actionId)` - Reject pending action

**SSE Events:**
- `message` - Streaming text chunks
- `tool_call` - Tool execution started
- `tool_result` - Tool execution completed
- `pending_action` - Action requires approval
- `done` - Response complete
- `error` - Error occurred

### `stores/aiComponentStore.js`
Registry for AI-sendable components:

**State:**
- `components` - Map of componentId -> serialize function

**Actions:**
- `register(componentId, serializeFn)` - Register component
- `unregister(componentId)` - Unregister component
- `getContext(componentId)` - Get component context data

### `hooks/useAISerializable.js`
Hook for registering components as AI-sendable:

**Usage:**
```jsx
const componentId = useAISerializable(() => ({
  type: 'stock-quote',
  symbol: 'AAPL',
  price: 180.50
}));
```

**Returns:**
- `componentId` - Unique identifier for this component instance

## Pages

### LoginNew (`pages/LoginNew.jsx`)
- Tab-based UI for Login/Register
- Uses authStore for state management
- Redirects to `/watchlists` on successful auth
- Form validation and error display
- shadcn/ui components (Card, Tabs, Input, Button)

### WatchlistsNew (`pages/WatchlistsNew.jsx`)
- Lists all user's watchlists
- Create new watchlist dialog
- Delete watchlist functionality
- Navigation to individual watchlist detail
- User dropdown menu with logout
- Empty state for new users

### Discover (`pages/Discover.jsx`)
- Market discovery page with movers table and calendar sidebar
- Three tabs: Most Active, Top Gainers, Top Losers
- Fetches from `/api/market/movers`
- Highlights stocks already in user's watchlists
- Integrated CalendarWidget in sidebar
- Cross-navigation to Watchlists page

### WatchlistDetail (`pages/WatchlistDetail.jsx`)
- Displays stocks in a watchlist
- Add stock by ticker symbol
- Remove stocks from watchlist
- Fetches live market data for each stock
- Shows loading skeletons during data fetch
- Uses StockRow component for each stock

## Components

### StockRow (`components/StockRow.jsx`)
- Displays single stock with live data
- Collapsed bar: symbol, price, change, volume, MA200 badge, estimates badge
- Expanded panel: lazy-loads OHLCV, performance, and estimates via separate API call
  - `CandlestickChart` for OHLCV data
  - `PerformanceTiles` for multi-period returns
- Remove button and AI context button
- Loading state with skeleton UI

### CandlestickChart (`components/CandlestickChart.jsx`)
- OHLCV candlestick chart using TradingView Lightweight Charts
- Volume histogram overlay with color-coded bars
- ResizeObserver for responsive container sizing
- AI-serializable for context capture
- TradingView attribution link (required)

### PerformanceTiles (`components/PerformanceTiles.jsx`)
- Heatmap-style period return badges (1D/1W/1M/3M/6M/YTD/1Y)
- Color-coded: green shades for positive, red shades for negative
- Only renders periods with available data

### EstimatesBadge (`components/EstimatesBadge.jsx`)
- Compact pill showing analyst consensus (Strong Buy/Buy/Hold/Sell/Strong Sell)
- Shows target price delta as percentage
- Tooltip with exact target price

### CalendarWidget (`components/CalendarWidget.jsx`)
- Tabbed view: Earnings and Dividends
- "My Stocks" / "All" filter toggle (client-side filtering against watchlist symbols)
- Countdown badges for events within 7 days
- Scrollable event list with watchlist highlighting

### PriceChart (`components/PriceChart.jsx`)
- Legacy 6-month line chart using Recharts (replaced by CandlestickChart in expanded panel)

### UI Components (`components/ui/`)
shadcn/ui components built on Radix UI:
- `button` - Button variants (default, destructive, outline, ghost)
- `card` - Card container with header, content, footer
- `dialog` - Modal dialogs
- `dropdown-menu` - Dropdown menus
- `table` - Table components
- `input` - Form inputs
- `label` - Form labels
- `badge` - Status badges
- `separator` - Visual dividers
- `avatar` - User avatars
- `skeleton` - Loading placeholders

## State Management

### Authentication Flow
1. App loads, calls `checkAuth()` in useEffect
2. authStore checks `/api/auth/me` for existing session
3. If valid, sets user state and loading=false
4. ProtectedRoute checks user state before rendering
5. If no user, redirects to login page

### Data Fetching Pattern
Components manage their own data fetching:
- Use React hooks (useState, useEffect)
- Fetch data on mount or when dependencies change
- Show loading state during fetch
- Handle errors gracefully
- Update UI on success

Example from StockRow:
```javascript
useEffect(() => {
  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/securities/${symbol}?include=quote,ma200,history`);
      const data = await res.json();
      setStockData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  fetchData();
}, [symbol]);
```

## Routing

### Protected Routes
- Wrapped in `ProtectedRoute` component
- Checks `user` from authStore
- Redirects to `/` if not authenticated
- Shows loading spinner while checking auth

### Navigation
- React Router's `useNavigate` hook for programmatic navigation
- `Link` component for declarative links
- `useParams` hook to access URL parameters (e.g., watchlist ID)

## Styling

### TailwindCSS
- Utility-first CSS framework
- Configured in `tailwind.config.js`
- Custom theme colors and animations
- Responsive design utilities

### shadcn/ui
- Pre-built accessible components
- Customizable via Tailwind classes
- Based on Radix UI primitives
- Copy-paste into codebase (not npm package)

### Class Utilities
- `lib/utils.js` - `cn()` function for conditional classes
- Uses `clsx` and `tailwind-merge` to combine class names

## Development

### Commands
```bash
npm run dev      # Start dev server (localhost:5173)
npm run build    # Production build
npm run preview  # Preview production build
npm run lint     # ESLint
```

### Hot Module Replacement
- Vite provides instant HMR
- React Fast Refresh for component updates
- State preserved during edits

### API Integration
- Backend must be running on `http://localhost:8000`
- CORS configured to allow `http://localhost:5173`
- Session cookies automatically sent with requests

## Important Notes

### API Base URL
Hardcoded in authStore and pages: `http://localhost:8000`

To change for production, search and replace or use environment variable.

### Authentication
- Session cookie managed by browser
- `credentials: 'include'` required on all fetch requests
- No manual token storage needed

### Error Handling
- API errors displayed in UI
- Form validation before submission
- Network errors caught and displayed
- User-friendly error messages

### Performance
- React 19 concurrent features
- Skeleton loading states for better UX
- Lazy loading not implemented (small app)
- Lightweight Charts (~45KB) replaces Recharts (~200KB) for financial charts
- Lazy loading of expanded panel data (OHLCV/performance/estimates fetched on expand)
