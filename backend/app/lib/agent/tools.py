"""Custom tools for the AI investment agent."""
import logging
from sqlalchemy.orm import Session

from app.models.watchlist import Watchlist
from app.models.watchlist_item import WatchlistItem
from app.models.pending_action import PendingAction
from app.models.memory_fact import MemoryFact
from app.lib.openbb import (
    get_quote,
    get_history,
    get_ma_200,
    SymbolNotFoundError,
    OpenBBTimeoutError,
)

logger = logging.getLogger(__name__)

# Tool definitions for the Anthropic API
TOOL_DEFINITIONS = [
    {
        "name": "get_quote",
        "description": "Get real-time quote for a stock symbol including price, change, volume",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., AAPL, MSFT)",
                }
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_watchlists",
        "description": "List the user's watchlists with item counts",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_watchlist_items",
        "description": "Get all stocks in a specific watchlist with their current quotes",
        "input_schema": {
            "type": "object",
            "properties": {
                "watchlist_id": {
                    "type": "integer",
                    "description": "The watchlist ID",
                }
            },
            "required": ["watchlist_id"],
        },
    },
    {
        "name": "get_price_history",
        "description": "Get 6-month price history for a symbol (daily close prices)",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol",
                }
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_financial_ratios",
        "description": "Get P/E, P/B, P/S valuation ratios for a symbol",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol",
                }
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "search_symbol",
        "description": "Search for a stock or ETF by name or partial ticker",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (company name or ticker)",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "propose_action",
        "description": (
            "Propose an action for the user to confirm. Use this when you want to "
            "modify the user's data (add stock, remove stock, create alert). "
            "The user must approve before it executes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": ["create_alert", "add_to_watchlist", "remove_stock"],
                    "description": "Type of action to propose",
                },
                "description": {
                    "type": "string",
                    "description": "Human-readable description of what this action will do",
                },
                "payload": {
                    "type": "object",
                    "description": "Action parameters (e.g., {symbol, watchlist_id, threshold})",
                },
            },
            "required": ["action_type", "description", "payload"],
        },
    },
    {
        "name": "get_user_memory",
        "description": "Get remembered facts about the current user (preferences, strategies, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


class ToolExecutor:
    """Executes tool calls from the AI agent."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    async def execute(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return the result as a string."""
        handler = getattr(self, f"_handle_{tool_name}", None)
        if not handler:
            return f"Unknown tool: {tool_name}"
        try:
            result = await handler(tool_input)
            return str(result)
        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            return f"Error executing {tool_name}: {str(e)}"

    async def _handle_get_quote(self, input: dict) -> dict:
        """Get real-time quote with 200-day moving average."""
        symbol = input["symbol"].upper()
        try:
            quote = get_quote(symbol)
            ma200 = get_ma_200(symbol)
            return {**quote, "symbol": symbol, "ma_200": ma200}
        except (SymbolNotFoundError, OpenBBTimeoutError) as e:
            return {"error": str(e)}

    async def _handle_get_watchlists(self, input: dict) -> list:
        """List user's watchlists with item counts."""
        watchlists = (
            self.db.query(Watchlist)
            .filter(Watchlist.user_id == self.user_id)
            .all()
        )
        return [
            {
                "id": w.id,
                "name": w.name,
                "item_count": len(w.items),
                "created_at": w.created_at.isoformat(),
            }
            for w in watchlists
        ]

    async def _handle_get_watchlist_items(self, input: dict) -> list | dict:
        """Get all stocks in a watchlist with current quotes."""
        watchlist_id = input["watchlist_id"]
        watchlist = (
            self.db.query(Watchlist)
            .filter(
                Watchlist.id == watchlist_id,
                Watchlist.user_id == self.user_id,
            )
            .first()
        )
        if not watchlist:
            return {"error": "Watchlist not found"}

        items = []
        for item in watchlist.items:
            try:
                quote = get_quote(item.symbol)
                items.append({"symbol": item.symbol, **quote})
            except Exception:
                items.append({"symbol": item.symbol, "error": "Failed to fetch quote"})
        return items

    async def _handle_get_price_history(self, input: dict) -> dict:
        """Get 6-month price history for charting."""
        symbol = input["symbol"].upper()
        try:
            history = get_history(symbol)
            return {"symbol": symbol, "data": history, "count": len(history)}
        except (SymbolNotFoundError, OpenBBTimeoutError) as e:
            return {"error": str(e)}

    async def _handle_get_financial_ratios(self, input: dict) -> dict:
        """Placeholder -- will be implemented with openbb_fundamentals.py in Phase 2."""
        symbol = input["symbol"].upper()
        return {
            "symbol": symbol,
            "message": "Financial ratios not yet available. Coming in Phase 2.",
        }

    async def _handle_search_symbol(self, input: dict) -> list | dict:
        """Search for symbols using OpenBB."""
        query = input["query"]
        try:
            from openbb import obb

            results = obb.equity.search(query=query, provider="fmp")
            if results and results.results:
                return [
                    {"symbol": r.symbol, "name": getattr(r, "name", "")}
                    for r in results.results[:10]
                ]
            return {"results": [], "message": "No results found"}
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}

    async def _handle_propose_action(self, input: dict) -> dict:
        """Create a pending action that requires user confirmation."""
        action = PendingAction(
            user_id=self.user_id,
            conversation_id=input.get("_conversation_id"),
            action_type=input["action_type"],
            action_payload=input["payload"],
            status="pending",
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return {
            "pending_action_id": action.id,
            "requires_confirmation": True,
            "description": input["description"],
            "action_type": input["action_type"],
        }

    async def _handle_get_user_memory(self, input: dict) -> list:
        """Get remembered facts about the user."""
        facts = (
            self.db.query(MemoryFact)
            .filter(MemoryFact.user_id == self.user_id)
            .all()
        )
        return [
            {"type": f.fact_type, "content": f.content, "confidence": f.confidence}
            for f in facts
        ]
