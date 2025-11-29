# Requirements Document: AI-Powered Financial Analysis & Tracking Tool

## 1. Executive Summary

### 1.1 Project Overview
A web-based financial analysis and tracking platform for individual investors in stocks and cryptocurrencies. The system starts with core tracking capabilities and is architected for future enhancement with AI agents, advanced analytics, and automated insights.

### 1.2 Version 1.0 Scope
- Multi-watchlist stock tracking
- Essential technical indicators and metrics
- On-demand data refresh
- 6-month historical data storage
- Foundation for future AI agent integration

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Web App)                       │
│                  React/Vue/Svelte + TailwindCSS             │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API / WebSocket (future)
┌──────────────────────┴──────────────────────────────────────┐
│                   Backend API Layer (Python)                 │
│                     FastAPI / Flask                          │
├──────────────────────────────────────────────────────────────┤
│                   Service Layer                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Watchlist   │  │ Market Data  │  │ Analytics        │   │
│  │ Service     │  │ Service      │  │ Service          │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│                   Data Access Layer                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ User/       │  │ Market Data  │  │ Historical Data  │   │
│  │ Watchlist   │  │ Cache        │  │ Repository       │   │
│  │ Repository  │  │              │  │                  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│              External Data & Future Extensions               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ OpenBB      │  │ MCP Server   │  │ Claude Agent SDK │   │
│  │ Python Lib  │  │ (Future)     │  │ Agents (Future)  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                   Data Storage                               │
│  ┌─────────────────────────┐  ┌────────────────────────┐    │
│  │ PostgreSQL              │  │ Redis (Cache)          │    │
│  │ - User data             │  │ - Market data cache    │    │
│  │ - Watchlists            │  │ - Session data         │    │
│  │ - Historical prices     │  └────────────────────────┘    │
│  │ - Calculated metrics    │                                │
│  └─────────────────────────┘                                │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

**Frontend:**
- Framework: React/Vue.js/Next.js (TBD based on preference)
- UI Library: TailwindCSS + shadcn/ui or similar
- Charts: Recharts / Chart.js / Lightweight Charts
- State Management: React Context / Zustand / Redux (based on framework choice)

**Backend:**
- Language: Python 3.11+
- API Framework: FastAPI (recommended for async support and auto-documentation)
- Data Library: OpenBB Python SDK
- Task Queue: Celery (for future background jobs)

**Database:**
- Primary DB: PostgreSQL 15+
- Cache: Redis 7+
- ORM: SQLAlchemy 2.0

**Future AI/Agent Layer:**
- Agent Framework: Claude Agent SDK
- MCP Integration: Model Context Protocol servers
- LLM: Claude (Anthropic)

---

## 3. Functional Requirements

### 3.1 User Management (Future - V1 may use simple auth)

**FR-1.1**: User Registration and Authentication
- Users can create accounts with email/password
- Basic authentication (consider OAuth for future)
- Session management

**FR-1.2**: User Profile
- Basic profile information
- Preferences storage (future: for AI personalization)

### 3.2 Watchlist Management

**FR-2.1**: Create Watchlist
- Users can create multiple named watchlists
- Each watchlist has a name and optional description
- Default character limits: Name (50 chars), Description (200 chars)

**FR-2.2**: Add Securities to Watchlist
- Users can search for stocks by ticker symbol
- Users can add stocks and crypto to watchlists
- Support for major exchanges (NYSE, NASDAQ, crypto exchanges)
- Validation of ticker symbols via OpenBB

**FR-2.3**: Remove Securities from Watchlist
- Users can remove individual securities from watchlists
- Confirmation prompt before removal

**FR-2.4**: Edit Watchlist
- Rename watchlist
- Update description
- Reorder securities (drag-and-drop in UI)

**FR-2.5**: Delete Watchlist
- Users can delete entire watchlists
- Confirmation prompt with warning
- Historical data retention configurable

**FR-2.6**: Watchlist Limits
- Maximum watchlists per user: 10 (configurable)
- Maximum securities per watchlist: 50 (configurable)

### 3.3 Market Data Display

**FR-3.1**: Real-time Metrics Display (On-Demand Refresh)
For each security in watchlist, display:
- **Current Price**: Latest trading price
- **Day Change**: $ and % change from previous close
- **Volume**: Current day trading volume
- **Market Cap**: Current market capitalization
- **P/E Ratio**: Price-to-earnings ratio
- **52-Week High/Low**: Range values

**FR-3.2**: Technical Indicators
- **Moving Averages**:
  - 20-day SMA (Simple Moving Average)
  - 50-day SMA
  - 200-day SMA
- Display whether current price is above/below each MA
- Optional: Color coding (green/red) for bullish/bearish signals

**FR-3.3**: Data Refresh
- On-demand refresh button per watchlist
- Refresh all watchlists option
- Last updated timestamp display
- Loading states during refresh

**FR-3.4**: Historical Data View
- 6-month price history storage
- Basic line chart showing price over time
- Ability to toggle between different time ranges (1D, 5D, 1M, 3M, 6M)
- Volume bars on chart (optional toggle)

### 3.4 Data Management

**FR-4.1**: Historical Data Storage
- Store daily OHLCV (Open, High, Low, Close, Volume) for 6 months
- Automatic data retention policy (delete data older than 6 months)
- Efficient querying for chart generation

**FR-4.2**: Data Synchronization
- On-demand fetch from OpenBB
- Error handling for failed data fetches
- Graceful degradation (show last known data with timestamp)

### 3.5 User Interface Requirements

**FR-5.1**: Dashboard View
- Overview of all watchlists
- Summary cards showing count of securities
- Quick stats (biggest gainers/losers in watchlists)

**FR-5.2**: Watchlist Detail View
- Tabular view of all securities in watchlist
- Sortable columns (by price, change %, volume, etc.)
- Expandable rows for detailed view/charts

**FR-5.3**: Search & Discovery
- Search bar for finding stocks/crypto by ticker or name
- Recent searches history
- Popular securities suggestions

**FR-5.4**: Responsive Design
- Mobile-friendly layout
- Tablet optimization
- Desktop full-featured view

---

## 4. Non-Functional Requirements

### 4.1 Performance

**NFR-1.1**: Response Time
- API response time: < 500ms for cached data
- API response time: < 3s for fresh data fetch from OpenBB
- UI rendering: < 100ms for interactions

**NFR-1.2**: Scalability
- Support 100 concurrent users (initial target)
- Design for horizontal scaling
- Database indexing for efficient queries

**NFR-1.3**: Data Freshness
- Market data accuracy within provider limits
- Clear indication of data staleness

### 4.2 Reliability

**NFR-2.1**: Availability
- Target uptime: 99% (excluding maintenance windows)
- Graceful handling of OpenBB API failures
- Fallback to cached data when external API unavailable

**NFR-2.2**: Data Integrity
- Transaction support for critical operations
- Data validation at API and database layers
- Audit logging for data modifications

### 4.3 Security

**NFR-3.1**: Authentication & Authorization
- Secure password storage (bcrypt/argon2)
- JWT or session-based authentication
- HTTPS only in production
- Rate limiting on API endpoints

**NFR-3.2**: Data Privacy
- User data isolation
- No sharing of watchlist data between users
- GDPR-compliant data handling (future consideration)

### 4.4 Maintainability

**NFR-4.1**: Code Quality
- Python type hints throughout
- Comprehensive docstrings
- Unit test coverage > 70%
- Integration tests for critical paths

**NFR-4.2**: Documentation
- API documentation (auto-generated via FastAPI)
- README with setup instructions
- Architecture decision records (ADRs)

### 4.5 Extensibility

**NFR-5.1**: Modular Architecture
- Service-oriented design
- Clear separation of concerns
- Plugin-ready architecture for future agents

**NFR-5.2**: Configuration Management
- Environment-based configuration
- Feature flags for gradual rollouts
- Configurable limits and thresholds

---

## 5. Data Models

### 5.1 Core Entities

```python
# User Model
User {
    id: UUID (PK)
    email: String (unique, indexed)
    password_hash: String
    created_at: Timestamp
    updated_at: Timestamp
    preferences: JSON (nullable, for future use)
}

# Watchlist Model
Watchlist {
    id: UUID (PK)
    user_id: UUID (FK -> User)
    name: String (max 50 chars)
    description: String (max 200 chars, nullable)
    created_at: Timestamp
    updated_at: Timestamp
    display_order: Integer
}

# WatchlistItem Model
WatchlistItem {
    id: UUID (PK)
    watchlist_id: UUID (FK -> Watchlist)
    symbol: String (ticker symbol, indexed)
    asset_type: Enum ['STOCK', 'CRYPTO']
    added_at: Timestamp
    display_order: Integer
    notes: Text (nullable, for future use)
}

# SecurityMetadata Model (Cache security info)
SecurityMetadata {
    symbol: String (PK)
    name: String
    exchange: String
    asset_type: Enum ['STOCK', 'CRYPTO']
    sector: String (nullable)
    industry: String (nullable)
    last_updated: Timestamp
}

# HistoricalPrice Model
HistoricalPrice {
    id: UUID (PK)
    symbol: String (indexed)
    date: Date (indexed)
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: BigInteger
    adjusted_close: Decimal (nullable)
    created_at: Timestamp
    
    UNIQUE(symbol, date)
}

# CurrentMetrics Model (Calculated/Cached)
CurrentMetrics {
    symbol: String (PK)
    current_price: Decimal
    day_change_dollar: Decimal
    day_change_percent: Decimal
    volume: BigInteger
    market_cap: BigInteger (nullable)
    pe_ratio: Decimal (nullable)
    week_52_high: Decimal
    week_52_low: Decimal
    ma_20: Decimal (nullable)
    ma_50: Decimal (nullable)
    ma_200: Decimal (nullable)
    last_updated: Timestamp
}
```

### 5.2 Index Strategy

```sql
-- User indices
CREATE INDEX idx_user_email ON users(email);

-- Watchlist indices
CREATE INDEX idx_watchlist_user_id ON watchlists(user_id);

-- WatchlistItem indices
CREATE INDEX idx_watchlist_item_watchlist_id ON watchlist_items(watchlist_id);
CREATE INDEX idx_watchlist_item_symbol ON watchlist_items(symbol);

-- HistoricalPrice indices
CREATE INDEX idx_historical_symbol_date ON historical_prices(symbol, date DESC);
CREATE INDEX idx_historical_date ON historical_prices(date);
```

---

## 6. API Design

### 6.1 API Endpoints (RESTful)

#### Authentication
```
POST   /api/v1/auth/register          # Register new user
POST   /api/v1/auth/login             # Login
POST   /api/v1/auth/logout            # Logout
GET    /api/v1/auth/me                # Get current user
```

#### Watchlists
```
GET    /api/v1/watchlists             # List all user watchlists
POST   /api/v1/watchlists             # Create watchlist
GET    /api/v1/watchlists/{id}        # Get watchlist details
PUT    /api/v1/watchlists/{id}        # Update watchlist
DELETE /api/v1/watchlists/{id}        # Delete watchlist
POST   /api/v1/watchlists/{id}/refresh # Refresh watchlist data
```

#### Watchlist Items
```
GET    /api/v1/watchlists/{id}/items            # List items in watchlist
POST   /api/v1/watchlists/{id}/items            # Add item to watchlist
DELETE /api/v1/watchlists/{id}/items/{item_id}  # Remove item
PUT    /api/v1/watchlists/{id}/items/reorder    # Reorder items
```

#### Market Data
```
GET    /api/v1/securities/search?q={query}      # Search securities
GET    /api/v1/securities/{symbol}              # Get security details
GET    /api/v1/securities/{symbol}/metrics      # Get current metrics
GET    /api/v1/securities/{symbol}/history?range={range} # Get historical data
POST   /api/v1/securities/batch-metrics         # Bulk metrics fetch
```

### 6.2 Sample Request/Response

**Create Watchlist**
```json
POST /api/v1/watchlists
{
  "name": "Tech Stocks",
  "description": "My favorite technology companies"
}

Response: 201 Created
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Tech Stocks",
  "description": "My favorite technology companies",
  "created_at": "2024-11-28T10:00:00Z",
  "updated_at": "2024-11-28T10:00:00Z",
  "items_count": 0
}
```

**Add Item to Watchlist**
```json
POST /api/v1/watchlists/{id}/items
{
  "symbol": "AAPL",
  "asset_type": "STOCK"
}

Response: 201 Created
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "watchlist_id": "550e8400-e29b-41d4-a716-446655440000",
  "symbol": "AAPL",
  "asset_type": "STOCK",
  "added_at": "2024-11-28T10:05:00Z",
  "security": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "exchange": "NASDAQ"
  }
}
```

**Get Current Metrics**
```json
GET /api/v1/securities/AAPL/metrics

Response: 200 OK
{
  "symbol": "AAPL",
  "current_price": 185.50,
  "day_change_dollar": 2.50,
  "day_change_percent": 1.37,
  "volume": 52430000,
  "market_cap": 2876000000000,
  "pe_ratio": 29.5,
  "week_52_high": 199.62,
  "week_52_low": 164.08,
  "moving_averages": {
    "ma_20": 182.30,
    "ma_50": 178.90,
    "ma_200": 175.40
  },
  "last_updated": "2024-11-28T15:59:00Z"
}
```

---

## 7. OpenBB Integration

### 7.1 OpenBB Usage Patterns

**Data Fetching Strategy:**
```python
from openbb import obb

# Stock quote data
quote_data = obb.equity.price.quote(symbol="AAPL")

# Historical prices
historical_data = obb.equity.price.historical(
    symbol="AAPL",
    start_date="2024-05-28",
    end_date="2024-11-28",
    provider="yfinance"  # or other providers
)

# Technical indicators
ma_data = obb.technical.ma(
    data=historical_data,
    length=20,
    ma_type="SMA"
)
```

### 7.2 Data Provider Configuration

- Primary provider: yfinance (free tier)
- Fallback providers: Configuration for future paid providers
- Rate limiting: Respect OpenBB/provider limits
- Caching strategy: Cache data with TTL based on market hours

### 7.3 Error Handling

```python
# Graceful degradation strategy
try:
    data = fetch_from_openbb(symbol)
except RateLimitError:
    # Return cached data with staleness warning
    return get_cached_data(symbol, stale_ok=True)
except SymbolNotFoundError:
    # Return 404 with helpful message
    raise HTTPException(404, "Symbol not found")
except OpenBBAPIError as e:
    # Log error, return cached or partial data
    log_error(e)
    return get_best_available_data(symbol)
```

---

## 8. Future Agent Architecture (Design Hooks)

### 8.1 Agent System Overview

**Planned Agent Types:**
1. **Market Analysis Agent**: Fundamental & technical analysis
2. **Sentiment Analysis Agent**: News and social media analysis
3. **Alert Agent**: Pattern detection and notifications
4. **Portfolio Optimization Agent**: Rebalancing suggestions
5. **Research Agent**: Deep dive on specific securities

### 8.2 MCP Integration Points

**Designed Integration Hooks:**
```python
# Service layer abstraction for future MCP
class MarketDataService:
    def __init__(self, data_source="openbb"):
        if data_source == "openbb":
            self.provider = OpenBBProvider()
        elif data_source == "mcp":
            self.provider = MCPServerProvider()
    
    async def get_quote(self, symbol: str):
        return await self.provider.fetch_quote(symbol)
```

**MCP Server Skills (Future):**
- Financial data retrieval
- News aggregation
- Sentiment scoring
- Technical analysis calculations
- Report generation

### 8.3 Agent Communication Protocol

**Event-Driven Architecture:**
```python
# Event bus for agent communication (future)
class EventBus:
    async def publish(self, event_type: str, data: dict):
        # Notify subscribed agents
        pass
    
    async def subscribe(self, event_type: str, handler):
        # Register agent handlers
        pass

# Example events
events = [
    "watchlist.item.added",
    "price.threshold.crossed",
    "analysis.requested",
    "alert.triggered"
]
```

### 8.4 Claude Agent SDK Integration

**Agent Execution Framework:**
```python
# Placeholder for agent initialization
class FinancialAgent:
    def __init__(self, agent_type: str, skills: list):
        # Initialize with Claude Agent SDK
        self.agent_type = agent_type
        self.skills = skills
        # self.claude_agent = ClaudeAgent(config)
    
    async def execute_task(self, task: dict):
        # Use Claude Agent SDK to process task
        pass
```

**Skill Registry (Extensible):**
```python
# Agent skills registration system
class SkillRegistry:
    skills = {}
    
    @classmethod
    def register_skill(cls, name: str, skill_func):
        cls.skills[name] = skill_func
    
    @classmethod
    def get_skill(cls, name: str):
        return cls.skills.get(name)

# Example skill registration
@SkillRegistry.register_skill("calculate_rsi")
def calculate_rsi(prices: list, period: int = 14):
    # RSI calculation logic
    pass
```

### 8.5 Alert System Hooks

**Alert Configuration Schema (Future):**
```python
AlertRule {
    id: UUID
    user_id: UUID
    watchlist_id: UUID (nullable)
    symbol: String (nullable)
    rule_type: Enum ['PRICE_THRESHOLD', 'VOLUME_SPIKE', 
                     'MA_CROSSOVER', 'PATTERN_DETECTED']
    conditions: JSON
    actions: JSON
    enabled: Boolean
    created_at: Timestamp
}
```

**Agent-Triggered Alerts:**
- Agents can create/trigger alerts based on analysis
- User-defined rules processed by Alert Agent
- Multi-channel notifications (email, push, in-app)

---

## 9. Implementation Phases

### Phase 1: Foundation (Weeks 1-3)
**Deliverables:**
- Database schema implementation
- Basic user authentication
- Watchlist CRUD operations
- OpenBB integration for basic data fetch
- Simple REST API

**Success Criteria:**
- Users can create watchlists
- Add stocks to watchlists
- View current prices

### Phase 2: Core Features (Weeks 4-6)
**Deliverables:**
- Historical data storage and retrieval
- Moving average calculations
- Frontend dashboard
- Watchlist detail views
- Basic charting

**Success Criteria:**
- Display all specified metrics
- 6-month historical data accessible
- Responsive UI working

### Phase 3: Polish & Optimization (Weeks 7-8)
**Deliverables:**
- Caching layer (Redis)
- Performance optimization
- Error handling and logging
- UI/UX refinements
- Testing suite

**Success Criteria:**
- API response times meet NFR targets
- Graceful error handling
- 70%+ test coverage

### Phase 4: Agent Foundation (Weeks 9-12)
**Deliverables:**
- MCP server integration
- Basic agent framework
- Simple analysis agent (e.g., MA crossover detection)
- Event bus implementation
- Alert rule schema

**Success Criteria:**
- One working agent demonstrating capability
- MCP integration functional
- Architecture validated for expansion

### Future Phases
- Advanced agents (sentiment, research, portfolio optimization)
- Real-time data streaming
- Mobile apps
- Social features (shared watchlists)
- Backtesting engine

---

## 10. Technical Specifications

### 10.1 Project Structure

```
financial-tracker/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Configuration
│   │   ├── database.py             # DB connection
│   │   ├── dependencies.py         # FastAPI dependencies
│   │   │
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── watchlist.py
│   │   │   ├── security.py
│   │   │   └── metrics.py
│   │   │
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── watchlist.py
│   │   │   └── security.py
│   │   │
│   │   ├── api/                    # API routes
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── watchlists.py
│   │   │   │   └── securities.py
│   │   │
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── watchlist_service.py
│   │   │   ├── market_data_service.py
│   │   │   ├── analytics_service.py
│   │   │   └── cache_service.py
│   │   │
│   │   ├── repositories/           # Data access
│   │   │   ├── __init__.py
│   │   │   ├── watchlist_repo.py
│   │   │   ├── security_repo.py
│   │   │   └── metrics_repo.py
│   │   │
│   │   ├── integrations/           # External services
│   │   │   ├── __init__.py
│   │   │   ├── openbb_client.py
│   │   │   └── mcp_client.py       # Future
│   │   │
│   │   ├── agents/                 # Agent system (future)
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py
│   │   │   ├── skills/
│   │   │   └── registry.py
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── calculations.py
│   │       ├── validators.py
│   │       └── helpers.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   │
│   ├── alembic/                    # DB migrations
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── watchlist/
│   │   │   ├── securities/
│   │   │   ├── charts/
│   │   │   └── common/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── public/
│   ├── package.json
│   └── README.md
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── docs/
│   ├── api/
│   ├── architecture/
│   └── user-guide/
│
└── README.md
```

### 10.2 Key Dependencies

**Backend (requirements.txt):**
```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
alembic==1.13.0
psycopg2-binary==2.9.9
redis==5.0.1

# OpenBB
openbb==4.1.0

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Utilities
python-dotenv==1.0.0
httpx==0.25.2
pandas==2.1.4
numpy==1.26.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Development
black==23.12.1
ruff==0.1.9
mypy==1.7.1
```

### 10.3 Environment Configuration

**.env.example:**
```bash
# Application
APP_ENV=development
APP_NAME=Financial Tracker
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/fintrack
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=300

# OpenBB
OPENBB_API_KEY=  # Optional for premium features
OPENBB_DEFAULT_PROVIDER=yfinance

# API Settings
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Data Retention
HISTORICAL_DATA_DAYS=180
DATA_CLEANUP_SCHEDULE=0 2 * * *  # 2 AM daily

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Future: Agent Configuration
# CLAUDE_API_KEY=
# MCP_SERVER_URL=
```

### 10.4 Database Migrations

**Initial Migration Example:**
```python
# alembic/versions/001_initial_schema.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

def upgrade():
    # Users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Watchlists table
    op.create_table(
        'watchlists',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(200)),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('display_order', sa.Integer, default=0),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # ... additional tables
```

---

## 11. Testing Strategy

### 11.1 Test Coverage Requirements

**Unit Tests (70% minimum):**
- All service layer methods
- Repository methods
- Utility functions
- Calculation logic (moving averages, etc.)

**Integration Tests:**
- API endpoints
- Database operations
- OpenBB integration
- Cache operations

**E2E Tests (Future):**
- Critical user flows
- Watchlist management flow
- Data refresh flow

### 11.2 Test Examples

```python
# tests/unit/services/test_watchlist_service.py
import pytest
from app.services.watchlist_service import WatchlistService

@pytest.mark.asyncio
async def test_create_watchlist(db_session, test_user):
    service = WatchlistService(db_session)
    watchlist = await service.create_watchlist(
        user_id=test_user.id,
        name="Tech Stocks",
        description="My tech picks"
    )
    
    assert watchlist.name == "Tech Stocks"
    assert watchlist.user_id == test_user.id
    assert watchlist.items_count == 0

# tests/integration/api/test_watchlists.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_watchlists(client: AsyncClient, auth_headers):
    response = await client.get(
        "/api/v1/watchlists",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

---

## 12. Deployment Considerations

### 12.1 Infrastructure

**Development:**
- Local Docker Compose setup
- PostgreSQL + Redis containers
- Hot reload for development

**Production (Future):**
- Cloud provider: AWS/GCP/Azure (TBD)
- Container orchestration: Docker Compose / Kubernetes
- Database: Managed PostgreSQL (RDS/Cloud SQL)
- Cache: Managed Redis (ElastiCache/MemoryStore)
- CDN for frontend assets

### 12.2 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml (example)
name: CI/CD

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest --cov=app tests/
      - name: Lint
        run: |
          ruff check .
          black --check .
```

### 12.3 Monitoring & Logging

**Logging Strategy:**
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for request tracing

**Metrics to Track:**
- API response times
- Database query performance
- Cache hit rates
- OpenBB API call counts
- Error rates by endpoint

**Tools (Future):**
- Application monitoring: Sentry/DataDog
- Log aggregation: ELK stack / CloudWatch
- Uptime monitoring: Pingdom/UptimeRobot

---

## 13. Security Considerations

### 13.1 Authentication & Authorization

- JWT-based authentication with refresh tokens
- Token expiration: 15 minutes (access), 7 days (refresh)
- Password requirements: Min 8 chars, complexity rules
- Rate limiting on auth endpoints

### 13.2 Data Protection

- HTTPS only in production
- SQL injection prevention (parameterized queries via SQLAlchemy)
- XSS protection (Content Security Policy headers)
- CSRF protection for state-changing operations

### 13.3 API Security

- Rate limiting per user/IP
- Input validation on all endpoints
- CORS configuration (whitelist origins)
- API versioning for backward compatibility

---

## 14. Open Questions & Decisions Needed

1. **Frontend Framework**: React vs. Vue.js vs. Next.js?
2. **Authentication**: Session-based vs. JWT? OAuth providers needed initially?
3. **Charting Library**: Recharts vs. Chart.js vs. Lightweight Charts?
4. **Deployment**: Cloud provider preference?
5. **Real-time Updates**: Should we plan for WebSocket support in Phase 2?
6. **Crypto Exchanges**: Which crypto exchanges to support initially?

---

## 15. Success Metrics

### V1.0 Launch Criteria
- [ ] Users can create and manage watchlists
- [ ] All specified metrics displayed accurately
- [ ] 6-month historical data accessible
- [ ] API response times < 3s
- [ ] Mobile-responsive UI
- [ ] 70%+ test coverage
- [ ] Documentation complete

### KPIs (Post-Launch)
- Daily Active Users (DAU)
- Average watchlists per user
- API uptime %
- Average session duration
- Feature adoption rates

---

## 16. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| OpenBB API rate limits | High | Medium | Implement aggressive caching, fallback providers |
| Data accuracy issues | High | Low | Validate against multiple sources, user reporting |
| Scalability bottlenecks | Medium | Medium | Performance testing, horizontal scaling design |
| Agent complexity overrun | Medium | High | Phased approach, clear scope boundaries |
| Security vulnerabilities | High | Low | Security audit, penetration testing |

---

## 17. Glossary

- **MA**: Moving Average
- **OHLCV**: Open, High, Low, Close, Volume
- **SMA**: Simple Moving Average
- **P/E**: Price-to-Earnings ratio
- **MCP**: Model Context Protocol
- **OpenBB**: Open-source investment research platform
- **TTL**: Time To Live (cache duration)

---

**Document Version**: 1.0  
**Last Updated**: November 28, 2024  
**Next Review**: After Phase 1 completion

---

## Next Steps

This requirements document provides a comprehensive blueprint for your financial tracking tool. Consider the following next actions:

1. Review and approve requirements
2. Make decisions on open questions (Section 14)
3. Set up development environment
4. Initialize project structure
5. Begin Phase 1 implementation
6. Schedule regular requirement review meetings
