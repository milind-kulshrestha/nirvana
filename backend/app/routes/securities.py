"""Securities/market data routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.lib.openbb import get_quote, get_ma_200, get_history, SymbolNotFoundError, OpenBBTimeoutError

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic schemas
class QuoteData(BaseModel):
    price: float
    change: float
    change_percent: float
    volume: int


class HistoryData(BaseModel):
    date: str
    close: float


class SecurityResponse(BaseModel):
    symbol: str
    name: Optional[str] = None
    quote: Optional[QuoteData] = None
    ma_200: Optional[float] = None
    history: Optional[list[HistoryData]] = None


@router.get("/{symbol}", response_model=SecurityResponse)
async def get_security(symbol: str, include: str = "quote,ma200,history"):
    """
    Get security data including quote, moving average, and history.

    Args:
        symbol: Stock ticker symbol
        include: Comma-separated list of data to include (quote, ma200, history)

    Returns:
        Security data based on include parameter
        Note: MA200 may be None if insufficient historical data (< 200 days)

    Raises:
        HTTPException: If symbol not found, timeout, or critical error
    """
    symbol = symbol.upper()
    include_parts = [part.strip().lower() for part in include.split(",")]

    response_data = {
        "symbol": symbol,
        "name": None,  # Could fetch from OpenBB if needed
    }

    # Track if we got any successful data
    has_data = False

    try:
        # Fetch quote
        if "quote" in include_parts:
            try:
                quote_data = get_quote(symbol)
                response_data["quote"] = QuoteData(**quote_data)
                has_data = True
            except (SymbolNotFoundError, OpenBBTimeoutError) as e:
                logger.warning(f"Quote fetch failed for {symbol}: {e}")
                # If quote fails, we should return 404 as symbol likely invalid
                if not has_data:
                    raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

        # Calculate 200-day MA (optional, returns None if insufficient data)
        if "ma200" in include_parts:
            try:
                ma_200_value = get_ma_200(symbol)
                response_data["ma_200"] = ma_200_value  # May be None
                if ma_200_value is not None:
                    has_data = True
            except OpenBBTimeoutError as e:
                logger.warning(f"MA200 fetch timed out for {symbol}: {e}")
                # Don't fail entire request for MA timeout
                response_data["ma_200"] = None

        # Fetch history
        if "history" in include_parts:
            try:
                history_data = get_history(symbol)
                response_data["history"] = [HistoryData(**item) for item in history_data]
                has_data = True
            except SymbolNotFoundError as e:
                logger.warning(f"History fetch failed for {symbol}: {e}")
                # Don't fail entire request if only history fails
            except OpenBBTimeoutError as e:
                logger.warning(f"History fetch timed out for {symbol}: {e}")
                # Don't fail entire request for timeout

        return SecurityResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
