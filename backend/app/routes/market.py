"""Market discovery and calendar routes."""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import logging

from app.lib.openbb import get_market_movers, get_calendar_events

router = APIRouter()
logger = logging.getLogger(__name__)


# --- Discovery schemas ---

class MarketMover(BaseModel):
    symbol: str
    name: Optional[str] = None
    price: float
    change: float
    change_percent: float
    volume: int


class MarketMoversResponse(BaseModel):
    category: str
    items: list[MarketMover]
    fetched_at: str


@router.get("/movers", response_model=MarketMoversResponse)
async def movers(category: str = Query("active", pattern="^(active|gainers|losers)$")):
    """
    Get market movers: most active, top gainers, or top losers.

    Args:
        category: "active", "gainers", or "losers"
    """
    try:
        items = get_market_movers(category)
        return MarketMoversResponse(
            category=category,
            items=[MarketMover(**item) for item in items],
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        logger.error(f"Error fetching market movers ({category}): {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market movers")


# --- Calendar schemas ---

class EarningsEvent(BaseModel):
    symbol: str
    name: Optional[str] = None
    date: Optional[str] = None
    eps_estimated: Optional[float] = None
    fiscal_date_ending: Optional[str] = None


class DividendEvent(BaseModel):
    symbol: str
    date: Optional[str] = None
    ex_dividend_date: Optional[str] = None
    dividend: Optional[float] = None
    payment_date: Optional[str] = None
    declaration_date: Optional[str] = None


class CalendarResponse(BaseModel):
    event_type: str
    events: list[dict]
    fetched_at: str


@router.get("/calendar", response_model=CalendarResponse)
async def calendar(
    type: str = Query("earnings", pattern="^(earnings|dividends)$"),
    days: int = Query(30, ge=1, le=90),
):
    """
    Get upcoming market calendar events.

    Args:
        type: "earnings" or "dividends"
        days: lookahead window (1-90 days, default 30)
    """
    try:
        events = get_calendar_events(event_type=type, days_ahead=days)
        return CalendarResponse(
            event_type=type,
            events=events,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        logger.error(f"Error fetching calendar ({type}): {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch calendar events")
