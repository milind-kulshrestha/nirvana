"""Action executor for confirmed AI agent actions."""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.pending_action import PendingAction
from app.models.watchlist import Watchlist
from app.models.watchlist_item import WatchlistItem

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes confirmed pending actions."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def execute(self, action_id: int) -> dict:
        """Execute a pending action after user confirmation."""
        action = self.db.query(PendingAction).filter(
            PendingAction.id == action_id,
            PendingAction.user_id == self.user_id,
            PendingAction.status == "pending",
        ).first()

        if not action:
            return {"error": "Action not found or already processed"}

        handler = getattr(self, f"_execute_{action.action_type}", None)
        if not handler:
            action.status = "rejected"
            self.db.commit()
            return {"error": f"Unknown action type: {action.action_type}"}

        try:
            result = handler(action.action_payload)
            action.status = "executed"
            action.resolved_at = datetime.utcnow()
            self.db.commit()
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            action.status = "rejected"
            action.resolved_at = datetime.utcnow()
            self.db.commit()
            return {"error": str(e)}

    def reject(self, action_id: int) -> dict:
        """Reject a pending action."""
        action = self.db.query(PendingAction).filter(
            PendingAction.id == action_id,
            PendingAction.user_id == self.user_id,
            PendingAction.status == "pending",
        ).first()

        if not action:
            return {"error": "Action not found or already processed"}

        action.status = "rejected"
        action.resolved_at = datetime.utcnow()
        self.db.commit()
        return {"success": True}

    def _execute_add_to_watchlist(self, payload: dict) -> dict:
        """Add a stock to a watchlist."""
        watchlist_id = payload.get("watchlist_id")
        symbol = payload.get("symbol", "").upper()

        if not watchlist_id or not symbol:
            raise ValueError("Missing watchlist_id or symbol")

        watchlist = self.db.query(Watchlist).filter(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == self.user_id,
        ).first()
        if not watchlist:
            raise ValueError("Watchlist not found")

        # Check for duplicate
        existing = self.db.query(WatchlistItem).filter(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.symbol == symbol,
        ).first()
        if existing:
            return {"message": f"{symbol} is already in {watchlist.name}"}

        item = WatchlistItem(watchlist_id=watchlist_id, symbol=symbol)
        self.db.add(item)
        self.db.commit()
        return {"message": f"Added {symbol} to {watchlist.name}"}

    def _execute_remove_stock(self, payload: dict) -> dict:
        """Remove a stock from a watchlist."""
        watchlist_id = payload.get("watchlist_id")
        symbol = payload.get("symbol", "").upper()

        if not watchlist_id or not symbol:
            raise ValueError("Missing watchlist_id or symbol")

        item = self.db.query(WatchlistItem).filter(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.symbol == symbol,
        ).join(Watchlist).filter(Watchlist.user_id == self.user_id).first()

        if not item:
            return {"message": f"{symbol} not found in watchlist"}

        self.db.delete(item)
        self.db.commit()
        return {"message": f"Removed {symbol} from watchlist"}

    def _execute_create_alert(self, payload: dict) -> dict:
        """Create an alert -- placeholder for Phase 4."""
        return {"message": "Alert creation will be available in a future update"}

    def get_pending_actions(self) -> list[dict]:
        """Get all pending actions for the user."""
        actions = self.db.query(PendingAction).filter(
            PendingAction.user_id == self.user_id,
            PendingAction.status == "pending",
        ).order_by(PendingAction.created_at.desc()).all()

        return [
            {
                "id": a.id,
                "action_type": a.action_type,
                "description": a.action_payload.get("description", "") if a.action_payload else "",
                "payload": a.action_payload,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in actions
        ]
