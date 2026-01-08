# Feature Request: Dedicated Agent Chat Window

**Created**: 2026-01-08
**Status**: Proposed
**Priority**: High
**Category**: AI/Agent Integration

---

## Executive Summary

Add a dedicated AI agent chat window to the stock watchlist tracker UI that enables users to interact with an intelligent assistant for stock analysis, watchlist management, and market insights through natural language conversations.

### Key Capabilities
- Natural language queries about stocks and watchlists
- AI-powered stock analysis and recommendations
- Conversational watchlist management (add/remove stocks via chat)
- Real-time market data interpretation
- Historical data analysis and trend identification
- Personalized investment insights based on user's watchlists

---

## Motivation

### Problem Statement
Currently, users must manually:
- Navigate through multiple pages to manage watchlists
- Interpret raw market data without context
- Perform their own technical analysis
- Search and add stocks using traditional UI forms

### Proposed Solution
A conversational AI agent that:
- Understands natural language queries like "What's happening with my tech stocks today?"
- Proactively suggests insights like "AAPL dropped 3% below its 200-day MA"
- Enables hands-free watchlist management via chat commands
- Provides context-aware analysis based on user's portfolio

### User Value
- **Faster insights**: Get answers through conversation vs manual research
- **Better decisions**: AI-powered analysis and recommendations
- **Easier management**: Natural language commands vs form inputs
- **Personalized experience**: Agent learns user preferences and watchlists

---

## Use Cases

### UC-1: Stock Analysis Query
**User**: "Tell me about Apple's performance this week"
**Agent**:
```
AAPL (Apple Inc.) - Current: $185.50 (+1.37%)

📊 Weekly Performance:
• Up 4.2% from $178.00 last Monday
• Trading above 200-day MA ($175.40)
• Volume up 15% vs avg

🔍 Key Events:
• Strong iPhone sales report on Wed
• Approaching resistance at $188

Would you like me to add AAPL to one of your watchlists?
```

### UC-2: Watchlist Management
**User**: "Add Tesla and Microsoft to my Tech Watchlist"
**Agent**: "Added TSLA and MSFT to 'Tech Watchlist'. Both stocks are currently trading above their 200-day moving averages. Would you like a quick analysis of these additions?"

### UC-3: Portfolio Overview
**User**: "How are my watchlists doing today?"
**Agent**:
```
📈 Your Portfolio Summary:

Tech Watchlist (5 stocks):
✅ 3 up, 1 down, 1 flat
🔥 Top performer: NVDA +5.2%
⚠️  Attention: TSLA -3.1% (below 200-day MA)

Value Stocks (3 stocks):
✅ All positive
📊 Avg gain: +1.8%

Want details on any specific watchlist?
```

### UC-4: Smart Alerts
**User**: "Alert me when any of my stocks drop below their 200-day MA"
**Agent**: "I'll monitor your 8 stocks and notify you here in the chat when any cross below their 200-day MA. Currently, all are trading above."

### UC-5: Research Assistance
**User**: "What semiconductor stocks should I watch?"
**Agent**: "Based on market cap and liquidity, consider: NVDA, AMD, INTC, TSM, QCOM. Which would you like analysis on, or shall I add all to a new 'Semiconductors' watchlist?"

---

## UI/UX Design

### Chat Window Location
**Option A: Floating Widget (Recommended)**
- Fixed position bottom-right corner
- Collapsible/expandable button
- Overlay on top of existing pages
- Accessible from any page in the app

**Option B: Side Panel**
- Slide-in panel from right side
- Takes 30-40% of screen width
- Pushes main content left

**Option C: Dedicated Page**
- New route `/chat` or `/agent`
- Full-page chat experience
- Link in navigation menu

**Recommendation**: Option A (Floating Widget) for best UX - always accessible without navigation.

### Visual Design

```
┌─────────────────────────────────────┐
│ 💬 AI Assistant              □ ✕   │ ← Header
├─────────────────────────────────────┤
│                                     │
│  👤 How are my watchlists today?   │
│                                     │
│  🤖 Your portfolio is up 2.3%...   │
│     [Tech Watchlist: +3.1%]        │ ← Clickable card
│     [Value Stocks: +1.2%]          │
│                                     │
│  👤 Tell me more about Tech        │
│                                     │
│  🤖 Tech Watchlist (5 stocks)...   │
│     • AAPL $185.50 (+1.4%)         │
│     • MSFT $420.00 (+2.1%)         │
│     ...                            │
│                                     │ ← Scrollable
│  💭 Suggested questions:           │
│     • Add a stock to watchlist     │
│     • Market news today            │
│     • Best performers this week    │
│                                     │
├─────────────────────────────────────┤
│ Type your message...          [📤] │ ← Input
└─────────────────────────────────────┘
```

### Component Breakdown
- **ChatWindow**: Main container (collapsible)
- **ChatHeader**: Title, minimize/close buttons
- **MessageList**: Scrollable message history
- **Message**: Individual message bubble (user/agent)
- **StockCard**: Embedded stock data cards
- **SuggestedActions**: Quick action chips
- **ChatInput**: Text input with send button
- **TypingIndicator**: Agent typing animation

---

## Technical Architecture

### Frontend Components

```
frontend/src/
├── components/
│   ├── chat/
│   │   ├── ChatWindow.jsx          # Main chat container
│   │   ├── ChatHeader.jsx          # Header with controls
│   │   ├── MessageList.jsx         # Scrollable messages
│   │   ├── Message.jsx             # Single message bubble
│   │   ├── UserMessage.jsx         # User message variant
│   │   ├── AgentMessage.jsx        # Agent message variant
│   │   ├── StockCard.jsx           # Embedded stock data
│   │   ├── WatchlistSummaryCard.jsx # Watchlist overview
│   │   ├── SuggestedActions.jsx    # Quick action chips
│   │   ├── ChatInput.jsx           # Message input
│   │   └── TypingIndicator.jsx     # Loading animation
│   └── ...
├── stores/
│   ├── chatStore.js                # Chat state management
│   └── ...
└── ...
```

### State Management (Zustand)

```javascript
// stores/chatStore.js
const useChatStore = create((set) => ({
  // State
  messages: [],
  isOpen: false,
  isTyping: false,
  sessionId: null,

  // Actions
  sendMessage: async (text) => { /* ... */ },
  receiveMessage: (message) => { /* ... */ },
  toggleChat: () => set((state) => ({ isOpen: !state.isOpen })),
  clearChat: () => set({ messages: [] }),
  setTyping: (typing) => set({ isTyping: typing }),
  initSession: async () => { /* ... */ },
}));
```

### Message Schema

```typescript
interface Message {
  id: string;
  type: 'user' | 'agent';
  content: string;
  timestamp: Date;
  metadata?: {
    stocks?: StockData[];
    watchlists?: WatchlistSummary[];
    actions?: Action[];
  };
}

interface StockData {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
}

interface Action {
  type: 'add_stock' | 'create_watchlist' | 'view_details';
  label: string;
  payload: any;
}
```

---

## Backend Requirements

### New API Endpoints

```python
# backend/app/routes/agent.py

# Chat endpoints
POST   /api/agent/chat
  Request: { message: string, session_id?: string }
  Response: {
    reply: string,
    session_id: string,
    metadata?: {
      stocks?: [...],
      suggested_actions?: [...]
    }
  }

GET    /api/agent/sessions/{session_id}
  Response: { messages: [...], created_at: datetime }

DELETE /api/agent/sessions/{session_id}
  Response: 204 No Content

# Streaming support (optional)
GET    /api/agent/chat/stream
  Response: text/event-stream
```

### Agent Architecture

```python
# backend/app/lib/agent.py

class StockAnalystAgent:
    """AI agent for stock analysis and watchlist management."""

    def __init__(self, user_id: int, llm_provider: str = "anthropic"):
        self.user_id = user_id
        self.llm = self._init_llm(llm_provider)
        self.tools = self._init_tools()

    def _init_tools(self):
        """Initialize agent tools."""
        return [
            get_user_watchlists,
            get_stock_quote,
            get_stock_analysis,
            add_to_watchlist,
            create_watchlist,
            search_stocks,
            get_market_news,
        ]

    async def process_message(self, message: str, context: dict) -> dict:
        """Process user message and generate response."""
        # 1. Understand intent
        # 2. Fetch relevant data
        # 3. Generate response with LLM
        # 4. Format response with metadata
        pass
```

### LLM Integration

**Option 1: Anthropic Claude (Recommended)**
- Claude 3.5 Sonnet for balanced cost/quality
- Function calling for tool use
- Strong financial reasoning capabilities

**Option 2: OpenAI GPT-4**
- GPT-4 Turbo for speed
- Function calling support
- Extensive community knowledge

**Option 3: Open Source (Llama, Mixtral)**
- Self-hosted for privacy
- Lower cost at scale
- Requires more infrastructure

### Database Schema

```python
# New tables for chat persistence

class AgentSession(Base):
    """Chat session persistence."""
    __tablename__ = "agent_sessions"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("AgentMessage", back_populates="session")

class AgentMessage(Base):
    """Individual chat messages."""
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), ForeignKey("agent_sessions.id"), nullable=False)
    role = Column(Enum("user", "agent"), nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("AgentSession", back_populates="messages")
```

---

## Implementation Plan

### Phase 1: Basic Chat UI (Week 1)
**Goal**: Working chat interface with mock responses

- [ ] Create ChatWindow component (floating widget)
- [ ] Implement ChatHeader with minimize/close
- [ ] Build MessageList with scrolling
- [ ] Create Message components (user/agent variants)
- [ ] Add ChatInput with send functionality
- [ ] Implement chatStore with Zustand
- [ ] Add typing indicator animation
- [ ] Style with Tailwind + shadcn/ui
- [ ] Make responsive (mobile/desktop)

**Deliverable**: UI-only chat that echoes messages back

### Phase 2: Backend Agent Foundation (Week 1-2)
**Goal**: Agent API with basic intelligence

- [ ] Set up `/api/agent/chat` endpoint
- [ ] Integrate LLM provider (Anthropic Claude)
- [ ] Create AgentSession and AgentMessage models
- [ ] Implement session management
- [ ] Build basic prompt engineering
- [ ] Add conversation history context
- [ ] Create agent tools for data fetching
- [ ] Implement function calling
- [ ] Add error handling and fallbacks

**Deliverable**: Agent that responds to greetings and basic questions

### Phase 3: Stock Analysis Tools (Week 2-3)
**Goal**: Agent can analyze stocks and watchlists

- [ ] Implement `get_stock_quote` tool
- [ ] Implement `get_user_watchlists` tool
- [ ] Implement `analyze_stock` tool (technical indicators)
- [ ] Implement `search_stocks` tool
- [ ] Create formatted response templates
- [ ] Add StockCard component for rich stock display
- [ ] Add WatchlistSummaryCard component
- [ ] Integrate real market data
- [ ] Add market context (news, events)

**Deliverable**: Agent provides stock analysis and watchlist summaries

### Phase 4: Watchlist Management (Week 3)
**Goal**: Agent can modify watchlists via chat

- [ ] Implement `add_to_watchlist` tool
- [ ] Implement `remove_from_watchlist` tool
- [ ] Implement `create_watchlist` tool
- [ ] Add confirmation prompts for actions
- [ ] Update UI to reflect changes immediately
- [ ] Add undo functionality
- [ ] Implement SuggestedActions component
- [ ] Add success/error notifications

**Deliverable**: Full CRUD operations via natural language

### Phase 5: Polish & Advanced Features (Week 4)
**Goal**: Production-ready experience

- [ ] Add streaming responses (SSE)
- [ ] Implement chat history persistence
- [ ] Add "suggested questions" feature
- [ ] Improve prompt engineering for better responses
- [ ] Add rate limiting and abuse prevention
- [ ] Implement conversation context pruning
- [ ] Add keyboard shortcuts (Cmd+K to open)
- [ ] Optimize for mobile experience
- [ ] Add analytics and usage tracking
- [ ] Write tests for agent logic

**Deliverable**: Polished, production-ready agent chat

---

## Technical Decisions

### LLM Provider
**Choice**: Anthropic Claude 3.5 Sonnet

**Reasoning**:
- Strong function calling capabilities
- Excellent financial reasoning
- Lower cost than GPT-4
- Fast response times
- Robust API with good docs

**Alternative**: OpenAI GPT-4 Turbo if Claude unavailable

### Chat Persistence
**Choice**: PostgreSQL for session/message storage

**Reasoning**:
- Already using PostgreSQL
- Simpler than adding Redis/MongoDB
- Chat volume low initially
- Can optimize later if needed

**Alternative**: Redis for ephemeral sessions, PostgreSQL for archive

### Frontend State
**Choice**: Zustand for chat state

**Reasoning**:
- Already using Zustand for auth
- Simple API, minimal boilerplate
- Sufficient for chat state needs
- Easy to integrate with React

### Response Format
**Choice**: JSON with structured metadata

**Reasoning**:
- Enables rich UI elements (cards, buttons)
- Agent can return actionable items
- Frontend can render differently based on metadata
- Backwards compatible with plain text

---

## API Examples

### Send Message
```bash
POST /api/agent/chat
Content-Type: application/json

{
  "message": "How is my Tech Watchlist performing?",
  "session_id": "abc-123-def"
}

# Response
{
  "reply": "Your Tech Watchlist is up 2.3% today with 4/5 stocks positive...",
  "session_id": "abc-123-def",
  "metadata": {
    "watchlist": {
      "id": 1,
      "name": "Tech Watchlist",
      "total_change": 2.3,
      "stocks": [
        { "symbol": "AAPL", "price": 185.50, "change_percent": 1.4 },
        { "symbol": "MSFT", "price": 420.00, "change_percent": 2.1 }
      ]
    },
    "suggested_actions": [
      { "type": "view_details", "label": "View full watchlist", "payload": { "watchlist_id": 1 } }
    ]
  }
}
```

### Stream Response (Optional)
```bash
GET /api/agent/chat/stream?message=Tell me about AAPL&session_id=abc-123

# Response (SSE)
data: {"type": "token", "content": "AAPL"}

data: {"type": "token", "content": " is currently"}

data: {"type": "token", "content": " trading at"}

data: {"type": "metadata", "data": {"symbol": "AAPL", "price": 185.50}}

data: {"type": "done"}
```

---

## Integration Points

### Existing Features
1. **Authentication**: Use existing authStore for user context
2. **Watchlists**: Agent calls existing `/api/watchlists/*` endpoints
3. **Market Data**: Agent calls existing `/api/securities/*` endpoints
4. **UI Components**: Reuse shadcn/ui buttons, cards, inputs

### External Services
1. **LLM API**: Anthropic Claude API
2. **OpenBB**: Existing market data integration
3. **News API** (future): For market context

### User Permissions
- Agent operates with same permissions as logged-in user
- Cannot access other users' watchlists
- All actions validated server-side

---

## Security Considerations

### Input Validation
- Sanitize user messages for XSS
- Validate session IDs
- Rate limit requests (10 msg/min per user)

### LLM Safety
- System prompt constraints to prevent harmful outputs
- Content filtering for inappropriate requests
- No PII in prompts (use IDs, not names)

### API Security
- Session-based auth (existing system)
- CORS properly configured
- SQL injection prevention (SQLAlchemy)

### Data Privacy
- Chat history private per user
- No sharing between users
- Optional: Allow users to delete history

---

## Performance Considerations

### Response Time
- **Target**: < 2 seconds for agent responses
- LLM latency: ~1-1.5s (Claude API)
- Database queries: < 100ms
- Total: ~1.5-2s acceptable

**Optimization**:
- Cache common queries (200-day MA)
- Parallel tool calls where possible
- Streaming responses for better UX

### Scalability
- **Initial**: 100 concurrent users
- LLM API handles concurrency
- PostgreSQL can handle chat load
- Add caching if needed later

### Cost Estimation
- Claude API: ~$0.01 per conversation
- Storage: negligible (text only)
- Target: < $50/month for 1000 users

---

## Success Metrics

### Usage Metrics
- Daily active chat users
- Messages per session (target: 5+)
- Session length (target: 3+ min)
- Feature adoption rate (% of users who try chat)

### Quality Metrics
- Agent response accuracy (manual review)
- User satisfaction (thumbs up/down)
- Error rate (< 5%)
- Response time (< 2s p95)

### Business Metrics
- User retention improvement
- Time spent in app increase
- Feature engagement (watchlist actions via chat)

### V1 Success Criteria
- ✅ 50%+ of active users try chat
- ✅ 80%+ correct responses on test queries
- ✅ < 2s response time p95
- ✅ < 5% error rate
- ✅ Positive user feedback

---

## Future Enhancements (V2+)

### Advanced Analysis
- Multi-stock comparisons
- Sector analysis
- Correlation analysis
- Portfolio optimization suggestions

### Proactive Notifications
- Agent-initiated messages for alerts
- Daily/weekly summaries
- Breaking news notifications
- Custom alert conditions

### Voice Interface
- Voice input (speech-to-text)
- Voice output (text-to-speech)
- Hands-free experience

### Personalization
- Learn user preferences
- Customized analysis style
- Investment strategy alignment
- Risk profile adaptation

### Integrations
- Connect to brokerage accounts
- Execute trades (with confirmation)
- Tax optimization suggestions
- Portfolio rebalancing

### Multi-modal
- Chart screenshots in responses
- PDF report generation
- Image-based queries
- Video explanations

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM generates incorrect analysis | High | Add disclaimer, manual verification, confidence scores |
| High API costs | Medium | Implement caching, rate limiting, usage caps |
| Slow response times | Medium | Use streaming, optimize prompts, cache common queries |
| Privacy concerns | High | Clear privacy policy, data encryption, opt-in |
| Hallucinations | High | Function calling for facts, cite sources, validation |
| User over-reliance | Medium | Disclaimers, encourage independent research |

---

## Dependencies

### External Services
- Anthropic Claude API (or alternative LLM)
- OpenBB (already integrated)

### New Libraries
- `anthropic` - Claude Python SDK
- `tiktoken` - Token counting (optional)
- `langchain` - Agent framework (optional, or custom)

### Infrastructure
- No new infrastructure needed
- Existing PostgreSQL + FastAPI
- May need to increase backend resources for LLM calls

---

## Open Questions

1. **LLM Provider**: Anthropic Claude vs OpenAI GPT-4?
2. **Persistence**: How long to keep chat history? (30 days? Forever?)
3. **Streaming**: Implement SSE streaming or simple request/response?
4. **Mobile**: Floating widget or full-page on mobile?
5. **Rate Limiting**: What's appropriate? (10 msg/min, 100 msg/day?)
6. **Monetization**: Premium feature or free for all?
7. **Agent Persona**: Professional analyst vs friendly assistant?
8. **Multi-language**: English only or i18n support?

---

## Getting Started

### Development Setup
```bash
# Backend
pip install anthropic langchain  # Or chosen LLM SDK
docker-compose restart backend

# Frontend
cd frontend
npm install  # No new dependencies for basic chat
npm run dev

# Environment variables
ANTHROPIC_API_KEY=sk-ant-...
AGENT_MODEL=claude-3-5-sonnet-20241022
AGENT_MAX_TOKENS=2000
```

### Testing
```bash
# Backend tests
pytest backend/tests/test_agent.py

# Manual testing
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test-123"}'
```

---

## Timeline

- **Phase 1**: 1 week (Chat UI)
- **Phase 2**: 1-2 weeks (Backend agent)
- **Phase 3**: 1 week (Stock tools)
- **Phase 4**: 1 week (Watchlist management)
- **Phase 5**: 1 week (Polish)

**Total**: 5-6 weeks for full V1 release

---

## References

- [Anthropic Claude API Docs](https://docs.anthropic.com/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [shadcn/ui Chat Components](https://ui.shadcn.com/examples/tasks)
- [Zustand Docs](https://github.com/pmndrs/zustand)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)

---

## Approval Checklist

Before implementation, confirm:

- [ ] LLM provider choice (Anthropic vs OpenAI)
- [ ] UI pattern (floating widget vs side panel vs page)
- [ ] Feature scope for V1 (basic chat or full analysis?)
- [ ] Budget for LLM API costs
- [ ] Timeline acceptable (5-6 weeks)
- [ ] Privacy/security requirements clear
- [ ] Success metrics agreed upon

---

**Next Steps**: Review this feature request, answer open questions, and approve for implementation. Once approved, development can begin with Phase 1 (Chat UI).
