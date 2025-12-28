"""OpenBB SDK integration for market data."""
from datetime import datetime, timedelta
from openbb import obb


class SymbolNotFoundError(Exception):
    """Raised when a symbol is not found."""

    pass


class OpenBBTimeoutError(Exception):
    """Raised when OpenBB API times out."""

    pass


def get_quote(symbol: str) -> dict:
    """
    Fetch current quote for symbol.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dictionary with price, change, change_percent, volume

    Raises:
        SymbolNotFoundError: If symbol not found
        OpenBBTimeoutError: If API request times out
    """
    try:
        data = obb.equity.price.quote(symbol=symbol, provider="fmp")

        if not data or not data.results:
            raise SymbolNotFoundError(f"Symbol {symbol} not found")

        result = data.results[0]

        return {
            "price": float(result.last_price) if hasattr(result, "last_price") else float(result.price),
            "change": float(result.change) if hasattr(result, "change") else 0.0,
            "change_percent": float(result.change_percent) if hasattr(result, "change_percent") else 0.0,
            "volume": int(result.volume) if result.volume else 0,
        }
    except AttributeError as e:
        raise SymbolNotFoundError(f"Symbol {symbol} not found or invalid data")
    except Exception as e:
        if "timeout" in str(e).lower():
            raise OpenBBTimeoutError(f"Timeout fetching data for {symbol}")
        raise SymbolNotFoundError(f"Error fetching {symbol}: {str(e)}")


def get_ma_200(symbol: str) -> float | None:
    """
    Calculate 200-day moving average.

    Args:
        symbol: Stock ticker symbol

    Returns:
        200-day simple moving average, or None if insufficient data

    Raises:
        SymbolNotFoundError: If symbol not found
        OpenBBTimeoutError: If API request times out
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=250)  # Extra buffer for weekends/holidays

        historical = obb.equity.price.historical(
            symbol=symbol,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            provider="fmp",
        )

        if not historical or not historical.results:
            # Return None instead of raising error - symbol may be valid but lack data
            return None

        # Get last 200 days of closing prices
        results = historical.results
        if len(results) < 200:
            # Return None for insufficient data - this is not an error condition
            return None

        # Calculate simple moving average
        prices = [float(day.close) for day in results[-200:]]
        ma_200 = sum(prices) / len(prices)

        return round(ma_200, 2)

    except Exception as e:
        if "timeout" in str(e).lower():
            raise OpenBBTimeoutError(f"Timeout fetching historical data for {symbol}")
        # Return None for other errors rather than failing entire request
        return None


def get_history(symbol: str, months: int = 6) -> list[dict]:
    """
    Fetch historical prices for charting.

    Args:
        symbol: Stock ticker symbol
        months: Number of months of history (default: 6)

    Returns:
        List of dictionaries with date and close price

    Raises:
        SymbolNotFoundError: If symbol not found
        OpenBBTimeoutError: If API request times out
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)

        historical = obb.equity.price.historical(
            symbol=symbol,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            provider="fmp",
        )

        if not historical or not historical.results:
            raise SymbolNotFoundError(f"No historical data for {symbol}")

        # Format for frontend charting
        history_data = [
            {
                "date": day.date.strftime("%Y-%m-%d") if isinstance(day.date, datetime) else str(day.date),
                "close": float(day.close),
            }
            for day in historical.results
        ]

        return history_data

    except SymbolNotFoundError:
        raise
    except Exception as e:
        if "timeout" in str(e).lower():
            raise OpenBBTimeoutError(f"Timeout fetching historical data for {symbol}")
        raise SymbolNotFoundError(f"Error fetching history for {symbol}: {str(e)}")
