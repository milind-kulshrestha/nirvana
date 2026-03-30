# Frontend Architecture

## Tech Stack

- **Framework**: React 19
- **Build Tool**: Vite
- **Routing**: React Router v7
- **Styling**: TailwindCSS + shadcn/ui
- **State Management**: Zustand (auth, AI chat)
- **Charts**: Recharts
- **UI Components**: Radix UI primitives
- **AI Integration**: SSE streaming with EventSource

## Project Structure

```
frontend/src/
├── components/
│   ├── ui/              # shadcn/ui components (badge, button, card, dialog, input, skeleton, tabs, etc.)
│   ├── layout/          # App shell & navigation
│   │   ├── AppShell.jsx       # Main layout: LeftSidebar + Outlet + RightRail + CommandPalette
│   │   ├── LeftSidebar.jsx    # Nav sidebar (watchlists, discover, ETFs, settings)
│   │   ├── RightRail.jsx      # Agent context panels (run steps, skills, sources)
│   │   ├── TopBar.jsx         # Page header with context chips
│   │   └── ComposeBar.jsx     # Message input for AI agent
│   ├── canvas/          # Agent workspace canvas
│   │   ├── CanvasBlock.jsx    # Rendered artifact block
│   │   ├── CanvasStream.jsx   # Streaming artifact display
│   │   └── WelcomeState.jsx   # Empty state for Agent Hub
│   ├── chat/            # Chat components
│   │   └── ChatMessageList.jsx # Message thread display
│   ├── rightrail/       # Right rail panels
│   │   ├── RunSteps.jsx       # Agent execution steps
│   │   ├── SkillsPalette.jsx  # Available agent skills
│   │   └── SourcesPanel.jsx   # Referenced data sources
│   ├── topbar/          # Top bar components
│   │   ├── ContextChipPicker.jsx  # Attach context to prompts
│   │   └── ContextChips.jsx       # Display attached contexts
│   ├── CommandPalette.jsx  # ⌘K command launcher
│   ├── ErrorBoundary.jsx   # Error boundary wrapper
│   ├── StockRow.jsx        # Stock display with 6-tab expandable detail
│   ├── CandlestickChart.jsx # TradingView Lightweight Charts
│   ├── SendToAIButton.jsx  # Context capture button
│   └── ...
├── pages/
│   ├── AgentHub.jsx        # AI agent workspace (home page)
│   ├── LoginNew.jsx        # Login/register page
│   ├── WatchlistsNew.jsx   # Watchlist list
│   ├── WatchlistDetail.jsx # Watchlist view with stocks
│   ├── Discover.jsx        # Market movers (gainers/losers/active)
│   ├── ETFDashboard.jsx    # ETF screening dashboard
│   └── Settings.jsx        # API keys & preferences
├── stores/
│   ├── authStore.js        # Zustand auth state
│   ├── aiChatStore.js      # Zustand AI chat state
│   ├── aiContextStore.js   # Context chips + component registry
│   ├── canvasStore.js      # Canvas blocks state
│   ├── layoutStore.js      # Panel visibility state
│   ├── chatStore.js        # Chat UI state
│   └── etfStore.js         # ETF dashboard state
├── hooks/
│   ├── useAISerializable.js    # AI component registration
│   └── useKeyboardShortcuts.js # Global keyboard shortcuts
├── lib/
│   └── utils.js         # Tailwind utility functions
├── App.jsx              # Router setup + startup + onboarding
├── main.jsx             # React entry point
└── index.css            # Global styles + design tokens
```

## Key Files

### `App.jsx`
- React Router setup with BrowserRouter
- `ProtectedRoute` component that checks auth state (redirects to `/login`)
- Split into `App` (startup health check, auth init) and `AuthenticatedApp` (onboarding + AppShell)
- Routes render inside `AppShell` via React Router `<Outlet>`
- Routes:
  - `/login` - LoginNew (public)
  - `/` - AgentHub (protected, AI workspace)
  - `/watchlists` - WatchlistsNew (protected)
  - `/watchlists/:id` - WatchlistDetail (protected)
  - `/discover` - Discover (protected)
  - `/etf` - ETFDashboard (protected)
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

### `stores/aiContextStore.js`
Combined registry for AI-sendable components and context chips:

**State:**
- `attachedContexts` - Array of context chips attached to compose bar (`{ id, type, label, data }`)
- `registeredComponents` - Map of componentId -> serialize function

**Actions:**
- `attachContext(item)` / `detachContext(id)` / `clearContexts()` — Manage context chips
- `register(componentId, serializeFn)` / `unregister(componentId)` / `getContext(componentId)` — Component registry

### `stores/canvasStore.js`
Zustand store for agent canvas workspace:

**State:**
- Canvas blocks (agent-generated artifacts)
- Stream state for live generation

### `stores/layoutStore.js`
Zustand store for panel visibility (sidebar, right rail, etc.)

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
- Single-column layout (right panel removed for future agent integration)
- Displays stocks in a watchlist
- Add stock by ticker symbol
- Remove stocks from watchlist
- Fetches live market data for each stock
- Shows loading skeletons during data fetch
- Uses StockRow component for each stock
- Reduced white space (compact padding throughout)

## Components

### Layout (`components/layout/`)
- **AppShell** — Top-level layout with `LeftSidebar` + main content `<Outlet>` + `RightRail` (on AgentHub only) + `CommandPalette`
- **LeftSidebar** — Navigation sidebar with links to watchlists, discover, ETFs, settings
- **RightRail** — Agent context panels (run steps, skills palette, sources) shown on Agent Hub
- **TopBar** — Page header with context chips for attaching data to prompts
- **ComposeBar** — Message input bar for composing AI agent prompts

### Canvas (`components/canvas/`)
- **CanvasBlock** — Rendered artifact block from agent output
- **CanvasStream** — Streaming artifact display during generation
- **WelcomeState** — Empty state shown on Agent Hub before first interaction

### StockRow (`components/StockRow.jsx`)
- Displays single stock with live data
- 6-tab expandable detail panel: Chart, Fundamentals, Earnings, Analysts, Valuation, Insiders
- Generic `fetchTabData` helper for lazy-loading tab content
- Loading state with skeleton UI

### UI Components (`components/ui/`)
shadcn/ui components built on Radix UI:
- `button` - Button variants (default, destructive, outline, ghost)
- `card` - Card container with header, content, footer
- `dialog` - Modal dialogs
- `dropdown-menu` - Dropdown menus
- `table` - Table components
- `tabs` - Tabbed interface (Tabs, TabsList, TabsTrigger, TabsContent)
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
