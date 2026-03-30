"""Securities/market data routes."""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.lib.openbb import (
    get_quote, get_ma_200, get_history, get_ohlcv, get_performance, get_estimates,
    get_insider_trading, get_fundamentals, get_earnings, get_analyst_coverage,
    get_valuation_history,
    SymbolNotFoundError, OpenBBTimeoutError,
)

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


class OHLCVData(BaseModel):
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: float
    volume: Optional[int] = None


class PerformanceData(BaseModel):
    one_day_return: Optional[float] = None
    one_week_return: Optional[float] = None
    one_month_return: Optional[float] = None
    three_month_return: Optional[float] = None
    six_month_return: Optional[float] = None
    ytd_return: Optional[float] = None
    one_year_return: Optional[float] = None


class EstimatesData(BaseModel):
    consensus_type: Optional[str] = None
    consensus_rating: Optional[float] = None
    target_price: Optional[float] = None


class SecurityResponse(BaseModel):
    symbol: str
    name: Optional[str] = None
    quote: Optional[QuoteData] = None
    ma_200: Optional[float] = None
    history: Optional[list[HistoryData]] = None
    ohlcv: Optional[list[OHLCVData]] = None
    performance: Optional[PerformanceData] = None
    estimates: Optional[EstimatesData] = None


@router.get("/{symbol}", response_model=SecurityResponse)
async def get_security(symbol: str, include: str = "quote,ma200,history"):
    """
    Get security data including quote, moving average, and history.

    Args:
        symbol: Stock ticker symbol
        include: Comma-separated list of data to include
                 (quote, ma200, history, ohlcv, performance, estimates)

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
            except SymbolNotFoundError as e:
                logger.warning(f"Quote fetch failed for {symbol}: {e}")
                if not has_data:
                    raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
            except OpenBBTimeoutError as e:
                logger.warning(f"Quote fetch timed out for {symbol}: {e}")
                # Don't 404 on timeout — symbol may be valid but API is slow

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

        # Fetch OHLCV data
        if "ohlcv" in include_parts:
            try:
                ohlcv_data = get_ohlcv(symbol)
                response_data["ohlcv"] = [OHLCVData(**item) for item in ohlcv_data]
                has_data = True
            except SymbolNotFoundError as e:
                logger.warning(f"OHLCV fetch failed for {symbol}: {e}")
            except OpenBBTimeoutError as e:
                logger.warning(f"OHLCV fetch timed out for {symbol}: {e}")

        # Fetch performance data
        if "performance" in include_parts:
            try:
                perf_data = get_performance(symbol)
                response_data["performance"] = PerformanceData(**perf_data)
                has_data = True
            except SymbolNotFoundError as e:
                logger.warning(f"Performance fetch failed for {symbol}: {e}")
            except OpenBBTimeoutError as e:
                logger.warning(f"Performance fetch timed out for {symbol}: {e}")

        # Fetch estimates data
        if "estimates" in include_parts:
            try:
                est_data = get_estimates(symbol)
                response_data["estimates"] = EstimatesData(**est_data)
                has_data = True
            except SymbolNotFoundError as e:
                logger.warning(f"Estimates fetch failed for {symbol}: {e}")
            except OpenBBTimeoutError as e:
                logger.warning(f"Estimates fetch timed out for {symbol}: {e}")

        return SecurityResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{symbol}/insider-trades")
async def get_insider_trades(symbol: str):
    """
    Get insider trading data for a symbol.

    Returns:
        summary: Aggregated buy/sell stats for last 3 months
        trades: Up to 20 most recent insider trades
    """
    symbol = symbol.upper()
    trades = get_insider_trading(symbol)

    # Compute summary for last 3 months
    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    recent = [t for t in trades if t.get("date") and t["date"] >= cutoff]

    buys = [t for t in recent if t["transaction_type"] == "buy"]
    sells = [t for t in recent if t["transaction_type"] == "sell"]

    buy_value = sum(t["value"] for t in buys if t["value"] is not None)
    sell_value = sum(t["value"] for t in sells if t["value"] is not None)

    return {
        "summary": {
            "total_buys": len(buys),
            "total_sells": len(sells),
            "buy_value": buy_value,
            "sell_value": sell_value,
            "net_value": buy_value - sell_value,
            "period": "3m",
        },
        "trades": trades,
    }


@router.get("/{symbol}/fundamentals")
async def get_fundamentals_route(symbol: str):
    """
    Get company fundamentals (profile + key metrics) for a symbol.

    Returns:
        Dict with company info, valuation, profitability, and financial health metrics.
    """
    symbol = symbol.upper()
    try:
        data = get_fundamentals(symbol)
        return data
    except (SymbolNotFoundError, OpenBBTimeoutError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{symbol}/earnings")
async def get_earnings_route(symbol: str):
    """
    Get earnings data (quarterly actuals + forward estimates) for a symbol.

    Returns:
        Dict with 'quarterly' (income statement actuals) and 'forward' (analyst estimates).
    """
    symbol = symbol.upper()
    try:
        data = get_earnings(symbol)
        return data
    except (SymbolNotFoundError, OpenBBTimeoutError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{symbol}/analyst")
async def get_analyst_route(symbol: str):
    """
    Get analyst coverage data (consensus, price targets, forward estimates) for a symbol.

    Returns:
        Dict with 'consensus', 'price_targets', and 'forward_estimates'.
    """
    symbol = symbol.upper()
    try:
        data = get_analyst_coverage(symbol)
        return data
    except (SymbolNotFoundError, OpenBBTimeoutError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{symbol}/valuation")
async def get_valuation_route(symbol: str):
    """
    Get historical valuation multiples (annual P/E, P/S, P/B, EV/EBITDA) for a symbol.

    Returns:
        List of annual valuation entries sorted oldest-first.
    """
    symbol = symbol.upper()
    try:
        data = get_valuation_history(symbol)
        return data
    except (SymbolNotFoundError, OpenBBTimeoutError) as e:
        raise HTTPException(status_code=404, detail=str(e))
