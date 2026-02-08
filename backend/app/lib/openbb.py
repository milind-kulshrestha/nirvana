"""OpenBB SDK integration for market data with DuckDB cache layer."""
import logging
from datetime import datetime, timedelta
from openbb import obb

logger = logging.getLogger(__name__)


class SymbolNotFoundError(Exception):
    """Raised when a symbol is not found."""

    pass


class OpenBBTimeoutError(Exception):
    """Raised when OpenBB API times out."""

    pass


def _try_cached_quote(symbol: str) -> dict | None:
    """Attempt to read a cached quote; return None on any failure."""
    try:
        from app.lib.market_cache import get_cached_quote
        return get_cached_quote(symbol)
    except Exception:
        logger.debug("Cache read failed for quote %s, falling back to API", symbol)
        return None


def _try_cache_quote(symbol: str, data: dict) -> None:
    """Attempt to write a quote to cache; silently ignore failures."""
    try:
        from app.lib.market_cache import cache_quote
        cache_quote(symbol, data)
    except Exception:
        logger.debug("Cache write failed for quote %s", symbol)


def get_quote(symbol: str) -> dict:
    """
    Fetch current quote for symbol.

    Checks the DuckDB cache first (TTL 15 min). On a miss, fetches from
    OpenBB and stores the result in cache before returning.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dictionary with price, change, change_percent, volume

    Raises:
        SymbolNotFoundError: If symbol not found
        OpenBBTimeoutError: If API request times out
    """
    # --- cache hit? ---
    cached = _try_cached_quote(symbol)
    if cached is not None:
        return cached

    # --- cache miss: fetch from OpenBB ---
    try:
        data = obb.equity.price.quote(symbol=symbol, provider="fmp")

        if not data or not data.results:
            raise SymbolNotFoundError(f"Symbol {symbol} not found")

        result = data.results[0]

        quote_data = {
            "price": float(result.last_price) if hasattr(result, "last_price") else float(result.price),
            "change": float(result.change) if hasattr(result, "change") else 0.0,
            "change_percent": float(result.change_percent) if hasattr(result, "change_percent") else 0.0,
            "volume": int(result.volume) if result.volume else 0,
        }

        _try_cache_quote(symbol, quote_data)
        return quote_data

    except AttributeError:
        raise SymbolNotFoundError(f"Symbol {symbol} not found or invalid data")
    except (SymbolNotFoundError, OpenBBTimeoutError):
        raise
    except Exception as e:
        if "timeout" in str(e).lower():
            raise OpenBBTimeoutError(f"Timeout fetching data for {symbol}")
        raise SymbolNotFoundError(f"Error fetching {symbol}: {str(e)}")


def get_ma_200(symbol: str) -> float | None:
    """
    Calculate 200-day moving average.

    Tries to compute from cached daily_prices first (needs >= 200 rows).
    Falls back to fetching from OpenBB if not enough cached data.

    Args:
        symbol: Stock ticker symbol

    Returns:
        200-day simple moving average, or None if insufficient data

    Raises:
        SymbolNotFoundError: If symbol not found
        OpenBBTimeoutError: If API request times out
    """
    # --- try computing from cache ---
    try:
        from app.lib.market_cache import get_cached_history

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        cached_rows = get_cached_history(symbol, start_date, end_date)

        if cached_rows and len(cached_rows) >= 200:
            prices = [float(row["close"]) for row in cached_rows[-200:]]
            ma_200 = sum(prices) / len(prices)
            return round(ma_200, 2)
    except Exception:
        logger.debug("Cache read failed for MA-200 %s, falling back to API", symbol)

    # --- not enough cached data: fetch from OpenBB ---
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
            return None

        results = historical.results
        if len(results) < 200:
            return None

        # Cache the fetched history for future use
        try:
            from app.lib.market_cache import cache_history

            records = [
                {
                    "date": day.date.strftime("%Y-%m-%d") if isinstance(day.date, datetime) else str(day.date),
                    "open": float(day.open) if day.open else None,
                    "high": float(day.high) if day.high else None,
                    "low": float(day.low) if day.low else None,
                    "close": float(day.close),
                    "volume": int(day.volume) if day.volume else None,
                }
                for day in results
            ]
            cache_history(symbol, records)
        except Exception:
            logger.debug("Cache write failed for history %s", symbol)

        prices = [float(day.close) for day in results[-200:]]
        ma_200 = sum(prices) / len(prices)
        return round(ma_200, 2)

    except Exception as e:
        if "timeout" in str(e).lower():
            raise OpenBBTimeoutError(f"Timeout fetching historical data for {symbol}")
        return None


def get_history(symbol: str, months: int = 6) -> list[dict]:
    """
    Fetch historical prices for charting.

    Checks DuckDB cache first; if cached rows cover the date range,
    returns them directly. Otherwise fetches from OpenBB and caches
    the result.

    Args:
        symbol: Stock ticker symbol
        months: Number of months of history (default: 6)

    Returns:
        List of dictionaries with date and close price

    Raises:
        SymbolNotFoundError: If symbol not found
        OpenBBTimeoutError: If API request times out
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    # --- cache hit? ---
    try:
        from app.lib.market_cache import get_cached_history

        cached_rows = get_cached_history(symbol, start_str, end_str)
        if cached_rows:
            # Rough check: cached data should cover most of the range.
            # A trading month has ~21 days, so expect at least months*15 rows.
            expected_min = months * 15
            if len(cached_rows) >= expected_min:
                return [
                    {"date": row["date"], "close": float(row["close"])}
                    for row in cached_rows
                ]
    except Exception:
        logger.debug("Cache read failed for history %s, falling back to API", symbol)

    # --- cache miss: fetch from OpenBB ---
    try:
        historical = obb.equity.price.historical(
            symbol=symbol,
            start_date=start_str,
            end_date=end_str,
            provider="fmp",
        )

        if not historical or not historical.results:
            raise SymbolNotFoundError(f"No historical data for {symbol}")

        history_data = []
        cache_records = []
        for day in historical.results:
            date_str = day.date.strftime("%Y-%m-%d") if isinstance(day.date, datetime) else str(day.date)
            history_data.append({"date": date_str, "close": float(day.close)})
            cache_records.append({
                "date": date_str,
                "open": float(day.open) if day.open else None,
                "high": float(day.high) if day.high else None,
                "low": float(day.low) if day.low else None,
                "close": float(day.close),
                "volume": int(day.volume) if day.volume else None,
            })

        # Write to cache
        try:
            from app.lib.market_cache import cache_history
            cache_history(symbol, cache_records)
        except Exception:
            logger.debug("Cache write failed for history %s", symbol)

        return history_data

    except SymbolNotFoundError:
        raise
    except Exception as e:
        if "timeout" in str(e).lower():
            raise OpenBBTimeoutError(f"Timeout fetching historical data for {symbol}")
        raise SymbolNotFoundError(f"Error fetching history for {symbol}: {str(e)}")
