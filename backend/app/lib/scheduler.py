"""
Background scheduler for market data refresh.

Uses APScheduler's BackgroundScheduler to periodically fetch and cache market
data so that user-facing requests can be served from DuckDB instead of hitting
the API every time.

The BackgroundScheduler runs jobs in a thread pool, keeping uvicorn's async
event loop free to handle HTTP requests.

Jobs:
  1. refresh_quotes  - every 15 min during market hours (9:30-16:00 ET, weekdays)
  2. daily_snapshot  - 6:00 PM ET on weekdays (end-of-day prices)
"""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_all_watchlist_symbols() -> list[str]:
    """Query the app database for every unique symbol across all watchlists."""
    from app.database import SessionLocal
    from app.models.watchlist_item import WatchlistItem

    db = SessionLocal()
    try:
        rows = db.query(WatchlistItem.symbol).distinct().all()
        return [row[0].upper() for row in rows]
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Job 1: Refresh quotes (every 15 min during market hours)
# ---------------------------------------------------------------------------


def refresh_quotes() -> None:
    """Fetch fresh quotes for every watchlist symbol and cache them."""
    try:
        symbols = _get_all_watchlist_symbols()
        if not symbols:
            return

        logger.info("Scheduler: refreshing quotes for %d symbols", len(symbols))

        from app.lib.openbb import get_quote

        for symbol in symbols:
            try:
                get_quote(symbol)
            except Exception:
                logger.warning("Scheduler: failed to refresh quote for %s", symbol)
    except Exception:
        logger.exception("Scheduler: refresh_quotes job failed")


# ---------------------------------------------------------------------------
# Job 2: Daily snapshot (6 PM ET on weekdays)
# ---------------------------------------------------------------------------


def daily_snapshot() -> None:
    """Fetch end-of-day prices for all watchlist symbols and cache them."""
    try:
        symbols = _get_all_watchlist_symbols()
        if not symbols:
            return

        logger.info("Scheduler: daily snapshot for %d symbols", len(symbols))

        from app.lib.openbb import get_history

        for symbol in symbols:
            try:
                get_history(symbol, 12)
            except Exception:
                logger.warning("Scheduler: failed daily snapshot for %s", symbol)
    except Exception:
        logger.exception("Scheduler: daily_snapshot job failed")


# ---------------------------------------------------------------------------
# Scheduler instance
# ---------------------------------------------------------------------------

scheduler = BackgroundScheduler(timezone=ET)

# Job 1: every 15 minutes, Mon-Fri, 9:30 AM - 3:45 PM ET
# (last run at 3:45 so data is fresh through close at 4:00)
scheduler.add_job(
    refresh_quotes,
    CronTrigger(
        day_of_week="mon-fri",
        hour="9-15",
        minute="0,15,30,45",
        timezone=ET,
    ),
    id="refresh_quotes",
    name="Refresh watchlist quotes",
    replace_existing=True,
)

# Job 2: 6:00 PM ET, Mon-Fri
scheduler.add_job(
    daily_snapshot,
    CronTrigger(
        day_of_week="mon-fri",
        hour=18,
        minute=0,
        timezone=ET,
    ),
    id="daily_snapshot",
    name="End-of-day price snapshot",
    replace_existing=True,
)
