# Agent Workspace Architecture

> Evolve Nirvana from a watchlist app with an AI sidebar into an agent-native platform where the AI can run analytics, produce interactive visualizations, and pin auto-refreshing artifacts to a dashboard.
> Each phase is independently shippable. Don't start the next phase until the current one works.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│                                                  │
│  ┌──────────┐  ┌────────────────────────────┐   │
│  │ AISidebar│  │   /workspace               │   │
│  │ (quick)  │  │                             │   │
│  │          │  │  Chat    │  ArtifactPanel   │   │
│  │          │  │  Pane    │  ┌─────────────┐ │   │
│  │          │  │          │  │ArtifactRender│ │   │
│  │          │  │          │  │  (charts,   │ │   │
│  │          │  │          │  │   tables,   │ │   │
│  │          │  │          │  │   metrics)  │ │   │
│  │          │  │          │  └─────────────┘ │   │
│  └──────────┘  └────────────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  /dashboard (pinned artifacts grid)       │   │
│  └──────────────────────────────────────────┘   │
├──────────────────────────────────────────────────┤
│                   Backend                        │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Agent   │  │  Code    │  │  Artifact    │  │
│  │  Harness │──│ Executor │  │  Store +     │  │
│  │(existing)│  │  (new)   │  │  Scheduler   │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  Existing: OpenBB, DuckDB, Market Cache   │   │
│  └──────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

**Three new subsystems:**
1. **Code Executor** — Sandboxed subprocess runner for agent-generated Python analytics
2. **Artifact System** — Chart specs, rendering, pinning, and scheduled refresh
3. **Workspace UI** — Full-width research canvas at `/workspace`

The existing agent harness, tools, chat API, and sidebar are unchanged — they gain new capabilities through new tools, not rewrites.

---

## Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Code execution | Backend subprocess | Full Python package access, sidecar already running with market data infra. WASM (Pyodide) too limited for finance libs. |
| Workspace UI | Separate `/workspace` route | Sidebar stays for quick chat. Research sessions need full screen. Sidebar gets "Open in Workspace" link. |
| Pinned artifact refresh | Declarative spec, not stored code | `pin_spec` references registered functions + args. Safe, serializable, survives code changes. No arbitrary code on a schedule. |
| Sandbox model | Subprocess + whitelist | Process isolation (separate memory, killable on timeout). No Docker dependency. Whitelist safe imports only. |
| Visualization | ChartSpec → existing components | Agent returns typed JSON specs. `<ArtifactRenderer>` maps them to existing Recharts/lightweight-charts components. Consistent look, reusable, serializable. |

---

## Phase 1: Code Executor

**Goal:** Agent can generate and run Python analytics code in a sandboxed subprocess, returning structured results.

### New Files

- `backend/app/lib/agent/code_executor.py`

### Design

The executor receives Python code + a data context declaration from the agent, pre-fetches the requested data, injects it as a `DATA` dict, and runs the code in a subprocess.

**Execution flow:**

1. Agent calls `run_analysis` tool with `code` and `data_context`
2. Executor pre-fetches data based on `data_context` (symbols, watchlist items, price history) using existing OpenBB/DuckDB infrastructure
3. Writes a temp Python script:
   - **Prelude:** whitelisted imports + `DATA` dict + `RESULT()` function
   - **Agent code:** appended after prelude
4. Runs via `subprocess.run()` with:
   - Timeout: 30 seconds
   - Memory limit: 512MB (ulimit)
   - Working directory: temp dir (no filesystem access to app)
5. Script calls `RESULT({...})` which writes JSON to a known output path
6. Executor reads result JSON, returns to agent

**Whitelisted imports:**

```python
import pandas as pd
import numpy as np
import math
import statistics
import json
import datetime
from collections import *
from itertools import *
```

**Prelude template:**

```python
import sys, json

# Pre-loaded market data
DATA = json.loads(sys.stdin.read())

# Result function — call once with final output
def RESULT(obj):
    with open(sys.argv[1], 'w') as f:
        json.dump(obj, f)

# Whitelisted imports
import pandas as pd
import numpy as np
# ... etc
```

**Result format:**

```python
RESULT({
    "summary": "AAPL shows strong relative momentum vs SPY...",
    "artifacts": [
        {
            "type": "line",
            "title": "AAPL vs SPY — 6M Relative Performance",
            "data": [{"date": "2025-09-22", "AAPL": 1.0, "SPY": 1.0}, ...],
            "axes": {"x": "date", "y": ["AAPL", "SPY"]},
            "pin_spec": {
                "fn": "relative_performance",
                "args": {"symbols": ["AAPL", "SPY"], "period": "6M"}
            }
        }
    ]
})
```

### Tasks

1. Create `code_executor.py` with `CodeExecutor` class
2. Implement prelude generation with whitelisted imports
3. Implement data context fetching (reuse `openbb.py` and `market_cache.py`)
4. Implement subprocess execution with timeout + memory limits
5. Implement result parsing and validation
6. Write tests with sample analytics scripts

---

## Phase 2: Artifact System (Backend)

**Goal:** Artifacts can be created, stored, pinned, and auto-refreshed.

### New Files

- `backend/app/models/artifact.py`
- `backend/app/routes/artifacts.py`
- `backend/app/services/artifact_service.py`
- `backend/app/lib/artifact_functions.py`

### Artifact Model

```python
class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True, default=uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)

    type = Column(String, nullable=False)        # line, candlestick, bar, table, metric_card, comparison
    title = Column(String, nullable=False)
    spec_json = Column(JSON, nullable=False)      # full ChartSpec
    pin_spec_json = Column(JSON, nullable=True)   # declarative refresh spec

    pinned = Column(Boolean, default=False)
    pinned_at = Column(DateTime, nullable=True)
    last_refreshed_at = Column(DateTime, nullable=True)
    refresh_interval = Column(String, nullable=True)  # "15m", "1h", "1d"
    position = Column(Integer, default=0)

    created_at = Column(DateTime, default=func.now())
```

### ChartSpec Schema

```json
{
    "id": "uuid",
    "type": "line | candlestick | bar | area | table | metric_card | comparison",
    "title": "string",
    "data": [],
    "axes": {"x": "field_name", "y": ["field1", "field2"]},
    "options": {},
    "pin_spec": {
        "fn": "registered_function_name",
        "args": {"symbol": "AAPL", "period": "6M"},
        "refresh_interval": "15m"
    }
}
```

### API Endpoints

```
GET    /api/artifacts/pinned              — all pinned artifacts for user
POST   /api/artifacts                     — create artifact (used internally by agent)
PUT    /api/artifacts/{id}/pin            — pin with refresh_interval + position
PUT    /api/artifacts/{id}/unpin          — unpin (artifact stays in conversation)
PUT    /api/artifacts/{id}/position       — reorder on dashboard
POST   /api/artifacts/{id}/refresh        — manual refresh now
DELETE /api/artifacts/{id}                — delete artifact
```

### Registered Refresh Functions

`artifact_functions.py` contains plain Python functions that the scheduler can call safely:

```python
REGISTRY = {}

def register(name):
    def decorator(fn):
        REGISTRY[name] = fn
        return fn
    return decorator

@register("price_history")
def price_history(symbol: str, period: str) -> dict:
    # Uses existing openbb.get_history()
    ...

@register("relative_performance")
def relative_performance(symbols: list[str], period: str) -> dict:
    # Fetches history for each symbol, normalizes to day 1
    ...

@register("watchlist_movers")
def watchlist_movers(watchlist_id: int) -> dict:
    # Fetches quotes for all items, sorts by change %
    ...
```

### Scheduled Refresh

Extend existing `scheduler.py`:

```python
@scheduler.scheduled_job('interval', minutes=5)
def refresh_stale_artifacts():
    artifacts = db.query(Artifact).filter(
        Artifact.pinned == True,
        Artifact.pin_spec_json != None
    ).all()

    for artifact in artifacts:
        if is_stale(artifact):  # compare last_refreshed_at vs refresh_interval
            fn = REGISTRY[artifact.pin_spec_json["fn"]]
            new_data = fn(**artifact.pin_spec_json["args"])
            artifact.spec_json["data"] = new_data
            artifact.last_refreshed_at = datetime.utcnow()

    db.commit()
```

### Tasks

1. Create `Artifact` model and run migration
2. Create `artifact_service.py` with CRUD + pin/unpin logic
3. Create `artifacts.py` routes
4. Create `artifact_functions.py` with initial registered functions (price_history, watchlist_movers)
5. Add artifact refresh job to `scheduler.py`
6. Register routes in `main.py`

---

## Phase 3: Agent Tools

**Goal:** Agent can create artifacts, run analysis, and pin results — all through its existing tool system.

### Modified Files

- `backend/app/lib/agent/tools.py`
- `backend/app/lib/agent/prompts.py`

### New Tools

**`run_analysis`** — Execute Python analytics code:

```python
{
    "name": "run_analysis",
    "description": "Run Python analytics code in a sandboxed environment with pre-loaded market data.",
    "parameters": {
        "code": {"type": "string", "description": "Python code to execute"},
        "data_context": {
            "type": "object",
            "properties": {
                "symbols": {"type": "array", "items": {"type": "string"}},
                "watchlist_id": {"type": "integer"},
                "include_history": {"type": "boolean"},
                "period": {"type": "string", "enum": ["1M", "3M", "6M", "1Y", "2Y"]}
            }
        }
    }
}
```

**`create_artifact`** — Produce a visualization from existing data (no code execution):

```python
{
    "name": "create_artifact",
    "description": "Create an interactive chart or table from data already gathered via other tools.",
    "parameters": {
        "type": {"type": "string", "enum": ["line", "candlestick", "bar", "area", "table", "metric_card", "comparison"]},
        "title": {"type": "string"},
        "data": {"type": "array"},
        "axes": {"type": "object"},
        "options": {"type": "object"},
        "pin_spec": {"type": "object"}
    }
}
```

**`pin_artifact`** — Pin an artifact to the dashboard:

```python
{
    "name": "pin_artifact",
    "description": "Pin an artifact to the user's dashboard for automatic refresh.",
    "parameters": {
        "artifact_id": {"type": "string"},
        "refresh_interval": {"type": "string", "enum": ["15m", "1h", "1d"]},
        "position": {"type": "integer"}
    }
}
```

### System Prompt Additions

Tool prose to guide the agent:

- Use `create_artifact` when data is already in hand from `get_quote`, `get_price_history`, etc. — no subprocess overhead
- Use `run_analysis` when custom computation is needed: correlations, regressions, screening, derived metrics, multi-symbol comparisons
- Always include `pin_spec` when the artifact would benefit from periodic refresh
- Use `pin_artifact` when the user says "keep this on my dashboard", "track this", or similar

### New SSE Event Types

```json
{"type": "artifact", "data": {"id": "uuid", "type": "line", "title": "...", "data": [...]}}
{"type": "execution_log", "data": {"status": "running", "output": "Loading data..."}}
{"type": "execution_log", "data": {"status": "done", "output": "Completed in 2.1s, 126 rows"}}
```

### Tasks

1. Add `run_analysis` tool definition and handler (calls CodeExecutor)
2. Add `create_artifact` tool definition and handler (calls ArtifactService)
3. Add `pin_artifact` tool definition and handler
4. Add tool prose to `prompts.py`
5. Add `artifact` and `execution_log` SSE event types to harness streaming
6. Test end-to-end: agent generates code → executor runs it → artifact streamed to frontend

---

## Phase 4: Workspace UI

**Goal:** Full-width workspace page where the agent can present research with interactive artifacts.

### New Files

```
frontend/src/pages/Workspace.jsx
frontend/src/components/WorkspaceChat.jsx
frontend/src/components/ArtifactPanel.jsx
frontend/src/components/ArtifactRenderer.jsx
frontend/src/components/DataTable.jsx
frontend/src/components/ExecutionLog.jsx
frontend/src/stores/artifactStore.js
```

### WorkspacePage

Split-pane layout at `/workspace`:

- Left pane (40%): `WorkspaceChat` — full-height chat with input, reuses message rendering from AISidebar
- Right pane (60%): `ArtifactPanel` — tabbed artifact display
- Bottom drawer (collapsible): `ExecutionLog` — code execution stdout/stderr
- Resizable panes via CSS resize or a lightweight splitter

### ArtifactRenderer

Maps `ChartSpec.type` to existing chart components:

```jsx
const RENDERERS = {
  line: PriceChart,
  candlestick: CandlestickChart,
  bar: BarChart,         // new, simple Recharts wrapper
  area: AreaChart,       // new, simple Recharts wrapper
  table: DataTable,      // new
  metric_card: MetricCard, // new, based on PerformanceTiles
  comparison: ComparisonView, // new, side-by-side metrics
};

function ArtifactRenderer({ spec }) {
  const Component = RENDERERS[spec.type];
  return <Component {...spec} />;
}
```

Existing `PriceChart` and `CandlestickChart` may need minor prop adjustments to accept the `ChartSpec` shape, but their rendering logic stays unchanged.

### ArtifactPanel

Tabbed container for multiple artifacts in a conversation:

- Each artifact from SSE creates a new tab
- Active tab shows the rendered artifact
- Each tab has a "Pin to Dashboard" button
- Pinning calls `PUT /api/artifacts/{id}/pin`

### WorkspaceChat

Extracts the chat rendering logic from `AISidebar.jsx` into a shared module, then both `AISidebar` and `WorkspaceChat` use it. Key difference: WorkspaceChat is full-height and routes artifact SSE events to `ArtifactPanel` instead of rendering inline.

### ArtifactStore (Zustand)

```javascript
{
  artifacts: [],              // current conversation artifacts
  pinnedArtifacts: [],        // dashboard artifacts
  executionLog: [],           // code execution output lines

  addArtifact(spec),          // from SSE artifact event
  addLogEntry(entry),         // from SSE execution_log event
  loadPinned(),               // GET /api/artifacts/pinned
  pinArtifact(id, interval),  // PUT /api/artifacts/{id}/pin
  unpinArtifact(id),          // PUT /api/artifacts/{id}/unpin
  reorderPinned(id, pos),     // PUT /api/artifacts/{id}/position
  refreshArtifact(id),        // POST /api/artifacts/{id}/refresh
}
```

### Modified Files

- `App.jsx` — add `/workspace` and `/dashboard` routes
- `AISidebar.jsx` — add "Open in Workspace" button when conversation has artifacts
- `chatStore.js` — handle `artifact` and `execution_log` SSE events, forward to artifactStore

### Tasks

1. Create `artifactStore.js`
2. Create `ArtifactRenderer.jsx` with type→component mapping
3. Create `DataTable.jsx` for tabular artifacts
4. Create `ArtifactPanel.jsx` with tabs
5. Create `ExecutionLog.jsx` collapsible drawer
6. Extract shared chat rendering from AISidebar into reusable module
7. Create `WorkspaceChat.jsx` using shared chat module
8. Create `Workspace.jsx` page with split-pane layout
9. Add routes to `App.jsx`
10. Add "Open in Workspace" to AISidebar
11. Handle new SSE events in chatStore

---

## Phase 5: Dashboard

**Goal:** Pinned artifacts rendered in a grid on a dashboard page with auto-refresh.

### New Files

```
frontend/src/pages/Dashboard.jsx
frontend/src/components/PinnedWidget.jsx
```

### Dashboard Page

CSS Grid layout at `/dashboard`:

- Responsive: 3 columns on wide screens, 2 on medium, 1 on narrow
- Each cell is a `PinnedWidget` wrapping an `ArtifactRenderer`
- Drag-to-reorder via simple sortable (or manual up/down initially)
- Polls `/api/artifacts/pinned` every 60 seconds for refresh updates

### PinnedWidget

Wrapper around each pinned artifact:

- Renders `<ArtifactRenderer spec={artifact.spec_json} />`
- Shows title and "last refreshed X ago" timestamp
- Three-dot menu: Unpin, Refresh Now, Open in Workspace
- Subtle border/shadow to distinguish from page background

### Navigation

- Dashboard becomes accessible via main nav alongside Watchlists
- Could become the default landing page in a future iteration, but starts as an opt-in route

### Tasks

1. Create `PinnedWidget.jsx`
2. Create `Dashboard.jsx` with grid layout
3. Add `/dashboard` route to `App.jsx`
4. Add Dashboard to main navigation
5. Implement polling for refresh updates
6. Test pin→dashboard→auto-refresh end-to-end flow

---

## Implementation Order

```
Phase 1: Code Executor           — backend only, testable in isolation
Phase 2: Artifact System          — backend only, new model + API
Phase 3: Agent Tools              — connects executor + artifacts to agent
Phase 4: Workspace UI             — frontend, the big visual payoff
Phase 5: Dashboard                — frontend, pinned artifact grid
```

Each phase is independently shippable and testable before moving to the next.
