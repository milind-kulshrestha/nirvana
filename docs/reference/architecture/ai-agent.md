# AI Agent Architecture

**Last Updated:** 2026-02-07

The AI agent system provides conversational intelligence for stock analysis, portfolio management, and investment research using Claude via the Anthropic SDK.

## Overview

The AI agent is a full-stack feature that enables users to:
- Have natural language conversations about stocks and portfolios
- Execute tool calls for real-time market data and analysis
- Use pre-built or custom skills for specialized investment workflows
- Build personalized memory for better recommendations
- Approve pending actions before execution (watchlist modifications)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
├─────────────────────────────────────────────────────────────┤
│  AISidebar                                                   │
│  ├─ Chat Interface (messages, streaming)                    │
│  ├─ Conversation History                                    │
│  ├─ Tool Call Indicators                                    │
│  └─ Pending Action Approvals                                │
│                                                              │
│  AIToggleButton (floating open/close)                       │
│                                                              │
│  SendToAIButton + useAISerializable                         │
│  └─ Component Context Capture (StockRow, PriceChart)        │
│                                                              │
│  Zustand Stores:                                            │
│  ├─ aiChatStore (chat state, SSE streaming)                 │
│  └─ aiComponentStore (component registry)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ REST + SSE
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API Layer                       │
├─────────────────────────────────────────────────────────────┤
│  /api/chat/*                                                 │
│  ├─ POST /conversations - Create conversation               │
│  ├─ GET /conversations - List conversations                 │
│  ├─ GET /conversations/:id/messages - Get messages          │
│  ├─ POST /stream - SSE streaming chat endpoint              │
│  ├─ POST /actions/:id/confirm - Confirm pending action      │
│  └─ POST /actions/:id/reject - Reject pending action        │
│                                                              │
│  /api/skills/*                                               │
│  ├─ GET /skills - List all skills                           │
│  ├─ GET /skills/:id - Get skill detail                      │
│  ├─ POST /skills - Create user skill                        │
│  ├─ PUT /skills/:id - Update skill                          │
│  └─ DELETE /skills/:id - Delete skill                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
├─────────────────────────────────────────────────────────────┤
│  ChatService                                                 │
│  ├─ create_conversation()                                   │
│  ├─ add_message()                                           │
│  ├─ stream_chat() - Orchestrates agent + SSE               │
│  └─ get_conversation_history()                              │
│                                                              │
│  ActionExecutor                                              │
│  ├─ confirm_action() - Execute approved action              │
│  └─ reject_action() - Mark action as rejected               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Core                             │
├─────────────────────────────────────────────────────────────┤
│  InvestmentAgent (app/agent/harness.py)                     │
│  ├─ Streaming tool-use loop with Anthropic SDK              │
│  ├─ Tool execution orchestration                            │
│  ├─ Memory fact extraction                                  │
│  └─ Multi-turn conversation handling                        │
│                                                              │
│  ToolExecutor (app/agent/tools.py)                          │
│  ├─ get_stock_quote() - Fetch real-time quote               │
│  ├─ get_price_history() - Historical price data             │
│  ├─ search_symbol() - Symbol lookup                         │
│  ├─ get_watchlists() - User's watchlists                    │
│  ├─ get_watchlist_detail() - Watchlist with quotes          │
│  ├─ propose_action() - Create pending action                │
│  └─ get_user_memory() - Fetch memory facts                  │
│                                                              │
│  SkillManager (app/agent/skills.py)                         │
│  ├─ Load system skills from filesystem                      │
│  ├─ Load user skills from database                          │
│  └─ Inject skills into system prompt                        │
│                                                              │
│  System Prompt (app/agent/prompts.py)                       │
│  ├─ Role definition (investment analyst)                    │
│  ├─ Tool usage instructions                                 │
│  ├─ Memory context injection                                │
│  └─ Skill definitions                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Models                           │
├─────────────────────────────────────────────────────────────┤
│  Conversation                                                │
│  ├─ id, user_id, title, created_at, updated_at              │
│  └─ messages (relationship)                                 │
│                                                              │
│  Message                                                     │
│  ├─ id, conversation_id, role, content, metadata            │
│  └─ tool_calls, tool_results stored in metadata JSON        │
│                                                              │
│  MemoryFact                                                  │
│  ├─ id, user_id, fact_type, content, source_conversation    │
│  └─ Stores investment preferences, risk tolerance, goals    │
│                                                              │
│  PendingAction                                               │
│  ├─ id, user_id, conversation_id, action_type, params       │
│  └─ status (pending/confirmed/rejected), created_at         │
│                                                              │
│  Skill                                                       │
│  ├─ id, user_id, name, description, content                 │
│  └─ is_system (true for built-in skills)                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
├─────────────────────────────────────────────────────────────┤
│  Anthropic Claude API                                        │
│  └─ Streaming Messages API with tool use                    │
│                                                              │
│  OpenBB SDK                                                  │
│  └─ Market data (quotes, history) via FMP provider          │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Frontend Components

#### AISidebar (`frontend/src/components/ai/AISidebar.jsx`)
- Fixed right panel (400px width)
- Chat message display with role-based styling
- Conversation history dropdown
- Tool call indicators (loading spinners)
- Pending action approval UI
- SSE streaming support with real-time updates

#### AIToggleButton (`frontend/src/components/ai/AIToggleButton.jsx`)
- Floating button (bottom-right)
- Opens/closes AI sidebar
- Shows unread message indicator

#### SendToAIButton (`frontend/src/components/ai/SendToAIButton.jsx`)
- Inline button for AI-registered components
- Captures component context (props, state)
- Sends context to AI with user message

#### useAISerializable Hook (`frontend/src/hooks/useAISerializable.js`)
- Registers component for AI context capture
- Provides `serialize()` function for data extraction
- Returns `componentId` for tracking

### 2. Frontend State Management

#### aiChatStore (`frontend/src/stores/aiChatStore.js`)
- Manages chat state (messages, conversations, loading)
- SSE streaming with EventSource
- Handles tool calls and pending actions
- Exposes actions: `sendMessage()`, `loadConversations()`, `confirmAction()`, `rejectAction()`

#### aiComponentStore (`frontend/src/stores/aiComponentStore.js`)
- Registry of AI-sendable components
- Maps `componentId` to `serialize()` functions
- Used by `SendToAIButton` to capture context

### 3. Backend API Routes

#### Chat Routes (`backend/app/routes/chat.py`)
```python
POST   /api/chat/conversations           # Create new conversation
GET    /api/chat/conversations           # List user's conversations
GET    /api/chat/conversations/:id/messages  # Get conversation messages
POST   /api/chat/stream                  # SSE streaming chat endpoint
POST   /api/chat/actions/:id/confirm     # Confirm pending action
POST   /api/chat/actions/:id/reject      # Reject pending action
```

#### Skills Routes (`backend/app/routes/skills.py`)
```python
GET    /api/skills                       # List all skills (system + user)
GET    /api/skills/:id                   # Get skill detail
POST   /api/skills                       # Create user skill
PUT    /api/skills/:id                   # Update user skill
DELETE /api/skills/:id                   # Delete user skill
```

### 4. Service Layer

#### ChatService (`backend/app/services/chat_service.py`)
- Creates and manages conversations
- Persists messages to database
- Orchestrates `InvestmentAgent` for streaming chat
- Yields SSE events: `message`, `tool_call`, `tool_result`, `done`, `error`

#### ActionExecutor (`backend/app/services/action_executor.py`)
- Executes confirmed pending actions
- Supported actions: `add_to_watchlist`, `remove_from_watchlist`, `create_watchlist`, `delete_watchlist`
- Updates action status in database
- Returns execution results

### 5. AI Agent Core

#### InvestmentAgent (`backend/app/agent/harness.py`)
- Wraps Anthropic SDK Messages API
- Streaming tool-use loop:
  1. Send user message to Claude
  2. Stream response chunks
  3. Execute tool calls via `ToolExecutor`
  4. Continue conversation with tool results
  5. Extract memory facts from final response
- Manages conversation state and context

#### ToolExecutor (`backend/app/agent/tools.py`)
- Tool definitions for Claude:
  - `get_stock_quote` - Real-time quote from OpenBB
  - `get_price_history` - Historical OHLCV data
  - `search_symbol` - Symbol lookup by name/ticker
  - `get_watchlists` - User's watchlist summary
  - `get_watchlist_detail` - Watchlist with live quotes
  - `propose_action` - Create pending action (requires approval)
  - `get_user_memory` - Fetch memory facts
- Tool execution with error handling
- Database and OpenBB integration

#### SkillManager (`backend/app/agent/skills.py`)
- Loads system skills from `backend/app/agent/system_skills/`
- Loads user skills from `Skill` model
- Formats skills for system prompt injection
- Skills provide specialized investment workflows

#### System Prompt (`backend/app/agent/prompts.py`)
- Defines agent role (investment research analyst)
- Tool usage instructions
- Memory context injection (user preferences, goals)
- Skill definitions (system + user)
- Response formatting guidelines

### 6. Database Models

#### Conversation (`backend/app/models/conversation.py`)
- Tracks chat sessions per user
- Links to messages via relationship
- Auto-updates `updated_at` on new messages

#### Message (`backend/app/models/message.py`)
- Stores conversation messages
- Fields: `role` (user/assistant), `content`, `metadata` (JSON)
- Tool calls and results stored in `metadata`

#### MemoryFact (`backend/app/models/memory_fact.py`)
- Long-term user preferences and context
- Fields: `fact_type` (preference/goal/context), `content`, `source_conversation_id`
- Injected into system prompt for personalization

#### PendingAction (`backend/app/models/pending_action.py`)
- Actions awaiting user approval
- Fields: `action_type`, `params` (JSON), `status`
- Prevents unauthorized watchlist modifications

#### Skill (`backend/app/models/skill.py`)
- User-defined and system skills
- Fields: `name`, `description`, `content` (markdown)
- `is_system` flag for built-in skills

## System Skills

Five pre-built investment analysis skills shipped with the platform:

### 1. research-stock (`backend/app/agent/system_skills/research-stock.md`)
Comprehensive equity research methodology:
- Financial health analysis (revenue, margins, cash flow)
- Valuation assessment (P/E, P/B, DCF)
- Competitive positioning
- Risk factors identification
- Investment thesis synthesis

### 2. portfolio-review (`backend/app/agent/system_skills/portfolio-review.md`)
Watchlist health check and analysis:
- Diversification assessment
- Sector concentration analysis
- Risk/return profile
- Position sizing review
- Rebalancing recommendations

### 3. compare-stocks (`backend/app/agent/system_skills/compare-stocks.md`)
Side-by-side stock comparison:
- Financial metrics comparison tables
- Valuation multiples analysis
- Growth trajectory comparison
- Relative strengths/weaknesses
- Investment preference recommendation

### 4. earnings-preview (`backend/app/agent/system_skills/earnings-preview.md`)
Pre-earnings analysis framework:
- Consensus estimates review
- Historical beat/miss patterns
- Key metrics to watch
- Guidance expectations
- Risk factors for earnings

### 5. watchlist-scan (`backend/app/agent/system_skills/watchlist-scan.md`)
Quick scan for opportunities and risks:
- Price action alerts (breakouts, breakdowns)
- Momentum indicators
- Support/resistance levels
- Volume anomalies
- News-driven catalysts

## Tool Execution Flow

```mermaid
sequenceDiagram
    User->>Frontend: "What's the P/E ratio for AAPL?"
    Frontend->>API: POST /api/chat/stream (SSE)
    API->>ChatService: stream_chat()
    ChatService->>InvestmentAgent: chat_stream()
    InvestmentAgent->>Claude: messages.stream()
    Claude-->>InvestmentAgent: tool_use: get_stock_quote("AAPL")
    InvestmentAgent->>ToolExecutor: execute_tool()
    ToolExecutor->>OpenBB: get_quote("AAPL")
    OpenBB-->>ToolExecutor: {price: 180.50, pe_ratio: 28.5, ...}
    ToolExecutor-->>InvestmentAgent: tool_result
    InvestmentAgent->>Claude: continue with tool_result
    Claude-->>InvestmentAgent: text: "AAPL P/E is 28.5..."
    InvestmentAgent-->>ChatService: yield events
    ChatService-->>API: SSE: message chunks
    API-->>Frontend: EventSource events
    Frontend->>User: Display "AAPL P/E is 28.5..."
```

## Pending Action Flow

For actions requiring approval (watchlist modifications):

```mermaid
sequenceDiagram
    User->>Frontend: "Add TSLA to my Tech watchlist"
    Frontend->>API: POST /api/chat/stream
    API->>InvestmentAgent: chat_stream()
    InvestmentAgent->>Claude: messages.stream()
    Claude-->>InvestmentAgent: tool_use: propose_action()
    InvestmentAgent->>ToolExecutor: execute propose_action
    ToolExecutor->>Database: Create PendingAction
    Database-->>ToolExecutor: action_id
    ToolExecutor-->>InvestmentAgent: {action_id, status: "pending"}
    InvestmentAgent-->>Frontend: SSE: pending_action event
    Frontend->>User: Show approval UI
    User->>Frontend: Click "Approve"
    Frontend->>API: POST /api/chat/actions/:id/confirm
    API->>ActionExecutor: confirm_action()
    ActionExecutor->>Database: Add WatchlistItem
    ActionExecutor->>Database: Update PendingAction.status = "confirmed"
    ActionExecutor-->>API: {success: true}
    API-->>Frontend: Action confirmed
    Frontend->>User: "TSLA added to Tech watchlist"
```

## Memory System

The agent extracts memory facts from conversations to personalize future interactions:

**Fact Types:**
- `preference` - Investment style, sector preferences, risk tolerance
- `goal` - Financial goals, time horizon, target allocations
- `context` - Account details, tax situation, constraints

**Extraction:**
- Happens automatically after each conversation turn
- Claude identifies relevant user information
- Stored in `MemoryFact` model linked to user
- Injected into system prompt on subsequent conversations

**Example:**
```
User: "I'm a conservative investor focused on dividend stocks"
→ Creates MemoryFact:
  fact_type: "preference"
  content: "Conservative investor preferring dividend-paying stocks"
  source_conversation_id: 123
```

## Configuration

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (defaults shown)
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096
```

### Backend Config (`backend/app/config.py`)
```python
ANTHROPIC_API_KEY: str
CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
CLAUDE_MAX_TOKENS: int = 4096
```

## Security Considerations

1. **API Key Protection**
   - `ANTHROPIC_API_KEY` stored in environment, never in code
   - Not exposed to frontend

2. **User Isolation**
   - All queries filtered by `current_user`
   - Cannot access other users' conversations or watchlists

3. **Action Approval**
   - Watchlist modifications require explicit user confirmation
   - Prevents unintended portfolio changes

4. **Input Validation**
   - All tool parameters validated (symbol format, IDs)
   - Rate limiting on API endpoints (TODO)

## Performance Considerations

1. **SSE Streaming**
   - Reduces perceived latency
   - User sees responses as they're generated
   - Tool calls shown with loading indicators

2. **Database Indexes**
   - `pending_actions.user_id` indexed for fast lookups
   - `message.conversation_id` ordered for chronological retrieval

3. **Caching** (TODO)
   - Cache frequent stock quotes
   - Cache skill definitions

## Testing

### Unit Tests (TODO)
- Tool execution with mocked OpenBB
- Memory fact extraction
- Action executor logic

### Integration Tests (TODO)
- End-to-end chat flow
- SSE streaming
- Pending action workflow

### Manual Testing
```bash
# Start backend with AI agent
docker-compose up -d
docker-compose logs -f backend

# Frontend (separate terminal)
cd frontend && npm run dev

# Test workflow:
1. Login at http://localhost:5173
2. Click AI toggle button
3. Ask: "What's the current price of AAPL?"
4. Verify tool call indicator shows
5. Verify response with quote data
6. Ask: "Add AAPL to my watchlist"
7. Verify pending action approval UI
8. Approve action
9. Verify AAPL added to watchlist
```

## Future Enhancements

1. **Additional Tools**
   - News sentiment analysis
   - Earnings transcript analysis
   - Insider trading data
   - Analyst recommendations

2. **Enhanced Skills**
   - Chart pattern recognition
   - Options strategy analyzer
   - Portfolio optimizer
   - Risk scenario analysis

3. **Multi-modal Capabilities**
   - Image analysis (chart screenshots)
   - Document parsing (10-K, 10-Q)

4. **Collaboration**
   - Share conversations with other users
   - Collaborative watchlist analysis

5. **Automation**
   - Scheduled portfolio reviews
   - Automated alerts based on AI analysis

## Troubleshooting

### "AI agent not responding"
- Check `ANTHROPIC_API_KEY` in docker-compose.yml
- Verify backend logs: `docker-compose logs backend`
- Check API quota limits

### "Tool calls failing"
- Check OpenBB API key (`OPENBB_API_KEY`)
- Verify symbol format (uppercase, valid ticker)
- Check backend logs for error details

### "Pending actions not executing"
- Verify action status in database: `SELECT * FROM pending_actions;`
- Check user permissions (must own the watchlist)
- Review backend logs for action executor errors

### "Memory facts not persisting"
- Check database connection
- Verify `ai_memory_enabled` flag on User model
- Review Claude's responses for memory extraction

## Related Documentation

- [Backend Architecture](backend.md) - Overall backend structure
- [Database Schema](database.md) - Database models and relationships
- [Frontend Architecture](frontend.md) - React components and state
- [Authentication Guide](../../guides/authentication.md) - Session management
