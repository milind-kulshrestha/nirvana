# Frontend Architecture

## Tech Stack

- **Framework**: React 19
- **Build Tool**: Vite
- **Routing**: React Router v7
- **Styling**: TailwindCSS + shadcn/ui
- **State Management**: Zustand
- **Charts**: Recharts
- **UI Components**: Radix UI primitives

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
│   ├── PriceChart.jsx   # 6-month price history chart
│   └── StockRow.jsx     # Individual stock display
├── pages/
│   ├── LoginNew.jsx     # Login/register page
│   ├── WatchlistsNew.jsx # Watchlist list
│   └── WatchlistDetail.jsx # Watchlist view
├── stores/
│   └── authStore.js     # Zustand auth state
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
- Routes:
  - `/` - LoginNew (public)
  - `/watchlists` - WatchlistsNew (protected)
  - `/watchlists/:id` - WatchlistDetail (protected)

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
- Fetches quote, MA200, and 6-month history from `/api/securities/{symbol}`
- Shows:
  - Symbol and current price
  - Price change (colored red/green)
  - 200-day moving average
  - Volume
  - Price chart (via PriceChart component)
- Remove button
- Loading state with skeleton UI

### PriceChart (`components/PriceChart.jsx`)
- 6-month price history chart using Recharts
- Line chart with area fill
- Responsive container
- Formatted axes and tooltips
- Gradient fill under line

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
- Chart data memoization via Recharts
