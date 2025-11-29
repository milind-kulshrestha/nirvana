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

    Raises:
        HTTPException: If symbol not found, timeout, or other error
    """
    symbol = symbol.upper()
    include_parts = [part.strip().lower() for part in include.split(",")]

    response_data = {
        "symbol": symbol,
        "name": None,  # Could fetch from OpenBB if needed
    }

    try:
        # Fetch quote
        if "quote" in include_parts:
            quote_data = get_quote(symbol)
            response_data["quote"] = QuoteData(**quote_data)

        # Calculate 200-day MA
        if "ma200" in include_parts:
            ma_200_value = get_ma_200(symbol)
            response_data["ma_200"] = ma_200_value

        # Fetch history
        if "history" in include_parts:
            history_data = get_history(symbol)
            response_data["history"] = [HistoryData(**item) for item in history_data]

        return SecurityResponse(**response_data)

    except SymbolNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OpenBBTimeoutError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
