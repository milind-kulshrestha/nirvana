# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

## [2026-02-07] - AI Agent Integration

### Added
- **AI Agent System** - Complete conversational AI assistant for stock analysis
  - Database models: Conversation, Message, MemoryFact, PendingAction, Skill
  - Backend agent infrastructure using Anthropic SDK
  - Tool execution framework (stock quotes, watchlists, price history, symbol search)
  - Skill management system with filesystem and database integration
  - Memory fact extraction for personalized recommendations
  - Streaming chat harness with SSE support
- **Chat Service & API** - Backend service layer and REST/SSE endpoints
  - `/api/chat/*` - Conversation CRUD, streaming chat, action confirmation
  - `/api/skills/*` - Skill CRUD operations
  - SSE streaming for real-time AI responses
  - Action executor for watchlist operations requiring user approval
- **System Skills** - 5 pre-built investment analysis skills
  - `research-stock` - Comprehensive equity research methodology
  - `portfolio-review` - Watchlist health check and analysis
  - `compare-stocks` - Side-by-side stock comparison
  - `earnings-preview` - Pre-earnings analysis framework
  - `watchlist-scan` - Quick scan for opportunities and risks
- **Frontend AI Components**
  - `AISidebar` - Fixed right panel with chat interface, conversation history, tool indicators
  - `AIToggleButton` - Floating button to open/close AI sidebar
  - `SendToAIButton` - Context capture for AI-enabled components
  - `useAISerializable` - Hook for registering components as AI-sendable
- **Frontend State Management**
  - `aiChatStore` - Zustand store for chat state with SSE streaming
  - `aiComponentStore` - Component-to-AI context registry
- **Dependencies**
  - Backend: `anthropic` SDK for Claude API integration
  - Frontend: `html-to-image` for visual context capture
  - Environment: `ANTHROPIC_API_KEY` configuration

### Technical Details
- AI agent uses Claude via Anthropic SDK with streaming tool use
- Pending actions require explicit user approval via frontend
- Memory facts stored per user for personalized assistance
- Skills can be system-provided or user-defined (stored in database)
- Frontend components can register themselves for AI context capture
- SSE (Server-Sent Events) for real-time streaming responses
- Tool execution includes watchlist CRUD, quote fetching, symbol search, price history

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