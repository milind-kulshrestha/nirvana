"""OpenBB SDK integration for market data with DuckDB cache layer."""
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import httpx
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


def _format_date(date_obj) -> str:
    """Format date object to YYYY-MM-DD string."""
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%Y-%m-%d")
    return str(date_obj)


def _safe_float_attr(obj, attr_name: str) -> float | None:
    """Safely extract float attribute from OpenBB result object."""
    if hasattr(obj, attr_name):
        value = getattr(obj, attr_name)
        if value is not None:
            return float(value)
    return None


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


def get_ohlcv(symbol: str, days: int = 365) -> list[dict]:
    """
    Fetch OHLCV daily bars.

    Checks DuckDB daily_prices cache first. On miss, fetches from OpenBB
    and caches the result.

    Args:
        symbol: Stock ticker symbol
        days: Number of calendar days of history (default: 365)

    Returns:
        List of dicts with date, open, high, low, close, volume

    Raises:
        SymbolNotFoundError: If symbol not found
        OpenBBTimeoutError: If API request times out
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    # --- cache hit? ---
    try:
        from app.lib.market_cache import get_cached_history
        cached_rows = get_cached_history(symbol, start_str, end_str)
        if cached_rows and len(cached_rows) >= days * 0.6:
            return [
                {
                    "date": row["date"],
                    "open": float(row["open"]) if row.get("open") is not None else None,
                    "high": float(row["high"]) if row.get("high") is not None else None,
                    "low": float(row["low"]) if row.get("low") is not None else None,
                    "close": float(row["close"]),
                    "volume": int(row["volume"]) if row.get("volume") is not None else None,
                }
                for row in cached_rows
            ]
    except Exception:
        logger.debug("Cache read failed for OHLCV %s, falling back to API", symbol)

    # --- cache miss: fetch from OpenBB ---
    try:
        historical = obb.equity.price.historical(
            symbol=symbol,
            start_date=start_str,
            end_date=end_str,
            provider="fmp",
        )

        if not historical or not historical.results:
            raise SymbolNotFoundError(f"No OHLCV data for {symbol}")

        ohlcv_data = []
        cache_records = []
        for day in historical.results:
            date_str = day.date.strftime("%Y-%m-%d") if isinstance(day.date, datetime) else str(day.date)
            rec = {
                "date": date_str,
                "open": float(day.open) if day.open else None,
                "high": float(day.high) if day.high else None,
                "low": float(day.low) if day.low else None,
                "close": float(day.close),
                "volume": int(day.volume) if day.volume else None,
            }
            ohlcv_data.append(rec)
            cache_records.append(rec)

        # Write to cache
        try:
            from app.lib.market_cache import cache_history
            cache_history(symbol, cache_records)
        except Exception:
            logger.debug("Cache write failed for OHLCV %s", symbol)

        return ohlcv_data

    except SymbolNotFoundError:
        raise
    except Exception as e:
        if "timeout" in str(e).lower():
            raise OpenBBTimeoutError(f"Timeout fetching OHLCV data for {symbol}")
        raise SymbolNotFoundError(f"Error fetching OHLCV for {symbol}: {str(e)}")


def get_performance(symbol: str) -> dict:
    """
    Fetch multi-period return summary.

    Checks DuckDB quotes_cache first (key: {SYMBOL}:performance, TTL 15 min).
    On miss, fetches from OpenBB and caches.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dict with period returns (one_day, one_week, one_month, etc.)

    Raises:
        SymbolNotFoundError: If symbol not found
        OpenBBTimeoutError: If API request times out
    """
    cache_key = f"{symbol.upper()}:performance"

    # --- cache hit? ---
    try:
        from app.lib.market_cache import get_cached_quote
        cached = get_cached_quote(cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache read failed for performance %s", symbol)

    # --- cache miss: fetch from OpenBB ---
    try:
        data = obb.equity.price.performance(symbol=symbol, provider="fmp")

        if not data or not data.results:
            raise SymbolNotFoundError(f"No performance data for {symbol}")

        result = data.results[0]
        perf_data = {
            "one_day_return": float(result.one_day) if hasattr(result, "one_day") and result.one_day is not None else None,
            "one_week_return": float(result.one_week) if hasattr(result, "one_week") and result.one_week is not None else None,
            "one_month_return": float(result.one_month) if hasattr(result, "one_month") and result.one_month is not None else None,
            "three_month_return": float(result.three_month) if hasattr(result, "three_month") and result.three_month is not None else None,
            "six_month_return": float(result.six_month) if hasattr(result, "six_month") and result.six_month is not None else None,
            "ytd_return": float(result.ytd) if hasattr(result, "ytd") and result.ytd is not None else None,
            "one_year_return": float(result.one_year) if hasattr(result, "one_year") and result.one_year is not None else None,
        }

        # Cache with 15-min TTL (reuses quotes_cache)
        try:
            from app.lib.market_cache import cache_quote
            cache_quote(cache_key, perf_data)
        except Exception:
            logger.debug("Cache write failed for performance %s", symbol)

        return perf_data

    except SymbolNotFoundError:
        raise
    except Exception as e:
        if "timeout" in str(e).lower():
            raise OpenBBTimeoutError(f"Timeout fetching performance for {symbol}")
        raise SymbolNotFoundError(f"Error fetching performance for {symbol}: {str(e)}")


def get_estimates(symbol: str) -> dict:
    """
    Fetch analyst consensus estimates.

    Checks DuckDB fundamentals cache first (24h TTL).
    On miss, fetches from OpenBB and caches.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dict with consensus_type, consensus_rating, target_price

    Raises:
        SymbolNotFoundError: If symbol not found
        OpenBBTimeoutError: If API request times out
    """
    cache_key = f"{symbol.upper()}:estimates"

    # --- cache hit? ---
    try:
        from app.lib.market_cache import get_cached_fundamentals
        cached = get_cached_fundamentals(cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache read failed for estimates %s", symbol)

    # --- cache miss: fetch from OpenBB ---
    try:
        data = obb.equity.estimates.consensus(symbol=symbol, provider="fmp")

        if not data or not data.results:
            raise SymbolNotFoundError(f"No estimates data for {symbol}")

        result = data.results[0]
        estimates_data = {
            "consensus_type": str(result.type) if hasattr(result, "type") and result.type else None,
            "consensus_rating": float(result.rating) if hasattr(result, "rating") and result.rating is not None else None,
            "target_price": float(result.target_price) if hasattr(result, "target_price") and result.target_price is not None else None,
        }

        # Cache with 24h TTL
        try:
            from app.lib.market_cache import cache_fundamentals
            cache_fundamentals(cache_key, estimates_data)
        except Exception:
            logger.debug("Cache write failed for estimates %s", symbol)

        return estimates_data

    except SymbolNotFoundError:
        raise
    except Exception as e:
        if "timeout" in str(e).lower():
            raise OpenBBTimeoutError(f"Timeout fetching estimates for {symbol}")
        raise SymbolNotFoundError(f"Error fetching estimates for {symbol}: {str(e)}")


def get_market_movers(category: str = "active") -> list[dict]:
    """
    Fetch market discovery data (most active, gainers, losers).

    Checks DuckDB quotes_cache first (key: _discovery:{category}, TTL 15 min).

    Args:
        category: "active", "gainers", or "losers"

    Returns:
        List of dicts with symbol, name, price, change, change_percent, volume
    """
    cache_key = f"_discovery:{category}"

    # --- cache hit? ---
    try:
        from app.lib.market_cache import get_cached_quote
        cached = get_cached_quote(cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache read failed for discovery %s", category)

    # --- cache miss: fetch from OpenBB ---
    try:
        fetcher = {
            "active": lambda: obb.equity.discovery.active(provider="fmp"),
            "gainers": lambda: obb.equity.discovery.gainers(provider="fmp"),
            "losers": lambda: obb.equity.discovery.losers(provider="fmp"),
        }.get(category)

        if not fetcher:
            return []

        data = fetcher()

        if not data or not data.results:
            return []

        items = []
        for row in data.results:
            # OpenBB uses percent_change (not change_percent) for discovery endpoints
            pct = None
            for field in ("percent_change", "change_percent", "changes_percentage"):
                val = getattr(row, field, None)
                if val is not None:
                    pct = float(val)
                    break
            if pct is None:
                pct = 0.0

            items.append({
                "symbol": str(row.symbol) if hasattr(row, "symbol") else "",
                "name": str(row.name) if hasattr(row, "name") and row.name else None,
                "price": float(row.price) if hasattr(row, "price") and row.price is not None else 0.0,
                "change": float(row.change) if hasattr(row, "change") and row.change is not None else 0.0,
                "change_percent": pct,
                "volume": int(row.volume) if hasattr(row, "volume") and row.volume else None,
            })

        # Cache with 15-min TTL
        try:
            from app.lib.market_cache import cache_quote
            cache_quote(cache_key, items)
        except Exception:
            logger.debug("Cache write failed for discovery %s", category)

        return items

    except Exception as e:
        logger.warning("Failed to fetch market movers (%s): %s", category, e)
        return []


def get_calendar_events(event_type: str = "earnings", days_ahead: int = 30) -> list[dict]:
    """
    Fetch upcoming calendar events (earnings or dividends).

    Checks DuckDB quotes_cache first (key: _calendar:{type}, TTL 1 hour).

    Args:
        event_type: "earnings" or "dividends"
        days_ahead: lookahead window in days (default: 30)

    Returns:
        List of event dicts
    """
    cache_key = f"_calendar:{event_type}"

    # --- cache hit? (1-hour TTL handled by custom check) ---
    try:
        from app.lib.market_cache import get_cached_quote_with_ttl
        cached = get_cached_quote_with_ttl(cache_key, ttl_minutes=60)
        if cached is not None:
            return cached
    except (ImportError, AttributeError):
        # Fallback: use standard 15-min cache
        try:
            from app.lib.market_cache import get_cached_quote
            cached = get_cached_quote(cache_key)
            if cached is not None:
                return cached
        except Exception:
            pass
    except Exception:
        logger.debug("Cache read failed for calendar %s", event_type)

    # --- cache miss: fetch from OpenBB ---
    try:
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        if event_type == "earnings":
            data = obb.equity.calendar.earnings(
                start_date=start_date,
                end_date=end_date,
                provider="fmp",
            )
        elif event_type == "dividends":
            data = obb.equity.calendar.dividend(
                start_date=start_date,
                end_date=end_date,
                provider="fmp",
            )
        else:
            return []

        if not data or not data.results:
            return []

        events = []
        for row in data.results:
            if event_type == "earnings":
                # OpenBB FMP uses 'date' for earnings date and 'eps_estimate' (not 'eps_estimated')
                date_val = getattr(row, "date", None) or getattr(row, "reporting_date", None)
                eps_est = getattr(row, "eps_estimate", None) or getattr(row, "eps_estimated", None)
                events.append({
                    "symbol": str(row.symbol) if hasattr(row, "symbol") else "",
                    "name": str(row.name) if hasattr(row, "name") and row.name else None,
                    "date": str(date_val) if date_val is not None else None,
                    "eps_estimated": float(eps_est) if eps_est is not None else None,
                    "fiscal_date_ending": str(row.fiscal_date_ending) if hasattr(row, "fiscal_date_ending") and row.fiscal_date_ending else None,
                })
            else:
                date_val = getattr(row, "date", None)
                ex_div = getattr(row, "ex_dividend_date", None)
                events.append({
                    "symbol": str(row.symbol) if hasattr(row, "symbol") else "",
                    "date": str(date_val) if date_val is not None else None,
                    "ex_dividend_date": str(ex_div) if ex_div is not None else None,
                    "dividend": float(row.dividend) if hasattr(row, "dividend") and row.dividend is not None else None,
                    "payment_date": str(row.payment_date) if hasattr(row, "payment_date") and row.payment_date else None,
                    "declaration_date": str(row.declaration_date) if hasattr(row, "declaration_date") and row.declaration_date else None,
                })

        # Cache
        try:
            from app.lib.market_cache import cache_quote
            cache_quote(cache_key, events)
        except Exception:
            logger.debug("Cache write failed for calendar %s", event_type)

        return events

    except Exception as e:
        logger.warning("Failed to fetch calendar events (%s): %s", event_type, e)
        return []


def get_insider_trading(symbol: str) -> list[dict]:
    """
    Fetch insider trades for symbol from SEC EDGAR Form 4 filings.

    Checks DuckDB fundamentals cache first (24h TTL, key: {SYMBOL}:insider_trades).
    On miss, fetches from SEC EDGAR and caches the result.

    Args:
        symbol: Stock ticker symbol

    Returns:
        List of dicts with date, insider_name, insider_title,
        transaction_type ('buy'/'sell'), shares, value.
        Sorted newest-first, limited to 20 most recent.
    """
    cache_key = f"{symbol.upper()}:insider_trades"

    # --- cache hit? ---
    try:
        from app.lib.market_cache import get_cached_fundamentals
        cached = get_cached_fundamentals(cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache read failed for insider trades %s", symbol)

    # --- cache miss: fetch from SEC EDGAR ---
    try:
        trades = _fetch_insider_trades_from_edgar(symbol.upper())

        # Cache with 24h TTL
        try:
            from app.lib.market_cache import cache_fundamentals
            cache_fundamentals(cache_key, trades)
        except Exception:
            logger.debug("Cache write failed for insider trades %s", symbol)

        return trades

    except Exception as e:
        logger.warning("Failed to fetch insider trades for %s: %s", symbol, e)
        return []


# ---------------------------------------------------------------------------
# SEC EDGAR helpers
# ---------------------------------------------------------------------------

_SEC_HEADERS = {"User-Agent": "Nirvana/1.0 (contact@nirvana.app)"}
_CIK_CACHE: dict[str, str] = {}  # ticker -> zero-padded CIK


def _get_cik(symbol: str) -> str | None:
    """Look up 10-digit CIK for a ticker from SEC company_tickers.json."""
    if symbol in _CIK_CACHE:
        return _CIK_CACHE[symbol]

    try:
        resp = httpx.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=_SEC_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        for entry in resp.json().values():
            ticker = entry.get("ticker", "").upper()
            cik = str(entry.get("cik_str", ""))
            _CIK_CACHE[ticker] = cik.zfill(10)

        return _CIK_CACHE.get(symbol)
    except Exception as e:
        logger.warning("SEC CIK lookup failed: %s", e)
        return None


def _fetch_insider_trades_from_edgar(symbol: str) -> list[dict]:
    """Fetch and parse Form 4 filings from SEC EDGAR for a symbol."""
    cik = _get_cik(symbol)
    if not cik:
        return []

    # Get recent filings index
    try:
        resp = httpx.get(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers=_SEC_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("SEC EDGAR submissions fetch failed for %s: %s", symbol, e)
        return []

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])

    # Collect up to 15 most recent Form 4 filings
    form4s = []
    for i, form in enumerate(forms):
        if form == "4":
            form4s.append((filing_dates[i], accessions[i], primary_docs[i]))
        if len(form4s) >= 15:
            break

    if not form4s:
        return []

    # Parse each Form 4 XML
    trades: list[dict] = []
    for filing_date, accession, primary_doc in form4s:
        # Strip XSLT prefix if present (e.g., "xslF345X05/file.xml" -> "file.xml")
        xml_filename = primary_doc
        if "/" in xml_filename:
            xml_filename = xml_filename.split("/", 1)[1]

        accession_path = accession.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession_path}/{xml_filename}"

        try:
            xml_resp = httpx.get(url, headers=_SEC_HEADERS, timeout=10)
            xml_resp.raise_for_status()
            parsed = _parse_form4_xml(xml_resp.text, filing_date)
            trades.extend(parsed)
        except Exception as e:
            logger.debug("Failed to parse Form 4 %s: %s", accession, e)
            continue

    # Sort newest-first, limit to 20
    trades.sort(key=lambda t: t["date"] or "", reverse=True)
    return trades[:20]


# Transaction codes: P=Purchase, S=Sale, M=Exercise, F=Tax withholding,
# G=Gift, A=Grant/Award. We only surface P and S as buy/sell.
_BUY_CODES = {"P"}
_SELL_CODES = {"S"}


def _parse_form4_xml(xml_text: str, filing_date: str) -> list[dict]:
    """Parse a Form 4 XML document and extract non-derivative transactions."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    # Extract owner info
    owner_el = root.find(".//reportingOwner")
    owner_name = None
    owner_title = None
    if owner_el is not None:
        name_el = owner_el.find(".//rptOwnerName")
        if name_el is not None and name_el.text:
            owner_name = name_el.text.strip()
        title_el = owner_el.find(".//officerTitle")
        if title_el is not None and title_el.text:
            owner_title = title_el.text.strip()

    trades = []
    for txn in root.findall(".//nonDerivativeTransaction"):
        code_el = txn.find(".//transactionCode")
        if code_el is None or code_el.text is None:
            continue

        code = code_el.text.strip()
        if code not in _BUY_CODES and code not in _SELL_CODES:
            continue

        txn_type = "buy" if code in _BUY_CODES else "sell"

        date_el = txn.find(".//transactionDate/value")
        date_str = date_el.text.strip() if date_el is not None and date_el.text else filing_date

        shares_el = txn.find(".//transactionShares/value")
        shares = None
        if shares_el is not None and shares_el.text:
            try:
                shares = int(float(shares_el.text.strip()))
            except ValueError:
                pass

        price_el = txn.find(".//transactionPricePerShare/value")
        price = None
        if price_el is not None and price_el.text:
            try:
                price = float(price_el.text.strip())
            except ValueError:
                pass

        value = None
        if shares is not None and price is not None:
            value = round(shares * price, 2)

        trades.append({
            "date": date_str,
            "insider_name": owner_name,
            "insider_title": owner_title,
            "transaction_type": txn_type,
            "shares": shares,
            "value": value,
        })

    return trades


# ---------------------------------------------------------------------------
# Direct FMP API helpers
# ---------------------------------------------------------------------------

def _fmp_get(path: str, params: dict | None = None) -> list | dict:
    """GET from FMP stable API with API key from config.

    Args:
        path: URL path after /stable/ (e.g. "profile")
        params: Query params (symbol, limit, period, etc.)

    Returns:
        Parsed JSON response (list or dict).

    Raises:
        SymbolNotFoundError: on 404 or empty response.
        OpenBBTimeoutError: on timeout.
    """
    from app.lib.config_manager import config_manager
    api_key = config_manager.get("fmp_api_key", "")
    if not api_key:
        raise SymbolNotFoundError("FMP API key not configured")

    url = f"https://financialmodelingprep.com/stable/{path}"
    all_params = {**(params or {}), "apikey": api_key}

    try:
        resp = httpx.get(url, params=all_params, timeout=10)
        if resp.status_code == 402:
            raise SymbolNotFoundError(f"FMP endpoint restricted: {path}")
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and len(data) == 0:
            raise SymbolNotFoundError(f"No data from FMP for {path}")
        return data
    except httpx.TimeoutException:
        raise OpenBBTimeoutError(f"FMP timeout: {path}")
    except (SymbolNotFoundError, OpenBBTimeoutError):
        raise
    except Exception as e:
        raise SymbolNotFoundError(f"FMP error for {path}: {e}")


# ---------------------------------------------------------------------------
# Fundamentals (company profile + key metrics)
# ---------------------------------------------------------------------------

def _safe_pe(profile: dict, metrics: dict) -> float | None:
    """Extract P/E ratio from profile or compute from earnings yield."""
    pe = profile.get("peRatio") or metrics.get("peRatio")
    if pe:
        return pe
    ey = metrics.get("earningsYield")
    if ey and ey != 0:
        return round(1.0 / ey, 2)
    return None


def get_fundamentals(symbol: str) -> dict:
    """
    Fetch company fundamentals for symbol from FMP API.

    Checks DuckDB fundamentals cache first (24h TTL, key: {SYMBOL}:fundamentals).
    On miss, fetches from FMP profile + key-metrics endpoints and caches the result.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dict with company info and financial metrics.
    """
    cache_key = f"{symbol.upper()}:fundamentals"

    # --- cache hit? ---
    try:
        from app.lib.market_cache import get_cached_fundamentals
        cached = get_cached_fundamentals(cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache read failed for fundamentals %s", symbol)

    # --- cache miss: fetch from FMP ---
    profile_data = _fmp_get("profile", {"symbol": symbol.upper()})
    metrics_data = _fmp_get("key-metrics", {"symbol": symbol.upper(), "limit": 1})

    # profile returns a list with one element
    profile = profile_data[0] if isinstance(profile_data, list) else profile_data
    metrics = metrics_data[0] if isinstance(metrics_data, list) else metrics_data

    result = {
        # Company info (from profile)
        "company_name": profile.get("companyName"),
        "sector": profile.get("sector"),
        "industry": profile.get("industry"),
        "description": profile.get("description"),
        "ceo": profile.get("ceo"),
        "employees": profile.get("fullTimeEmployees"),
        "website": profile.get("website"),
        # Valuation metrics
        "market_cap": metrics.get("marketCap"),
        "enterprise_value": metrics.get("enterpriseValue"),
        "pe_ratio": _safe_pe(profile, metrics),
        "ev_to_ebitda": metrics.get("evToEBITDA"),
        "ev_to_sales": metrics.get("evToSales"),
        # Profitability
        "roe": metrics.get("returnOnEquity"),
        "roa": metrics.get("returnOnAssets"),
        "roic": metrics.get("returnOnInvestedCapital"),
        # Financial health
        "current_ratio": metrics.get("currentRatio"),
        "free_cash_flow_yield": metrics.get("freeCashFlowYield"),
        # Other
        "dividend_yield": profile.get("lastDividend"),
        "beta": profile.get("beta"),
        "52w_range": profile.get("range"),
    }

    # Cache with 24h TTL
    try:
        from app.lib.market_cache import cache_fundamentals
        cache_fundamentals(cache_key, result)
    except Exception:
        logger.debug("Cache write failed for fundamentals %s", symbol)

    return result


# ---------------------------------------------------------------------------
# Earnings (quarterly actuals + forward estimates)
# ---------------------------------------------------------------------------

def get_earnings(symbol: str) -> dict:
    """
    Fetch quarterly earnings actuals and forward analyst estimates for symbol.

    Checks DuckDB fundamentals cache first (24h TTL, key: {SYMBOL}:earnings).
    On miss, fetches from FMP income-statement + analyst-estimates endpoints.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dict with 'quarterly' (list of actual results) and 'forward' (list of estimates).
    """
    cache_key = f"{symbol.upper()}:earnings"

    # --- cache hit? ---
    try:
        from app.lib.market_cache import get_cached_fundamentals
        cached = get_cached_fundamentals(cache_key)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache read failed for earnings %s", symbol)

    quarterly = []
    forward = []

    # --- Quarterly actuals from income-statement ---
    try:
        income_data = _fmp_get(
            "income-statement",
            {"symbol": symbol.upper(), "period": "quarter", "limit": 5},
        )
        if isinstance(income_data, list):
            for item in income_data:
                quarterly.append({
                    "date": item.get("date", ""),
                    "period": item.get("period", ""),
                    "fiscal_year": str(item.get("fiscalYear") or item.get("calendarYear", "")),
                    "revenue": item.get("revenue"),
                    "net_income": item.get("netIncome"),
                    "eps": item.get("eps"),
                    "eps_diluted": item.get("epsDiluted") or item.get("epsdiluted"),
                })
    except (SymbolNotFoundError, OpenBBTimeoutError) as e:
        logger.warning("Earnings quarterly fetch failed for %s: %s", symbol, e)

    # --- Forward estimates from analyst-estimates ---
    try:
        estimates_data = _fmp_get(
            "analyst-estimates",
            {"symbol": symbol.upper(), "period": "annual", "limit": 3},
        )
        if isinstance(estimates_data, list):
            for item in estimates_data:
                forward.append({
                    "date": item.get("date", ""),
                    "revenue_avg": item.get("revenueAvg"),
                    "revenue_low": item.get("revenueLow"),
                    "revenue_high": item.get("revenueHigh"),
                    "eps_avg": item.get("epsAvg"),
                    "eps_low": item.get("epsLow"),
                    "eps_high": item.get("epsHigh"),
                    "ebitda_avg": item.get("ebitdaAvg"),
                    "net_income_avg": item.get("netIncomeAvg"),
                })
    except (SymbolNotFoundError, OpenBBTimeoutError) as e:
        logger.warning("Earnings forward estimates fetch failed for %s: %s", symbol, e)

    result = {"quarterly": quarterly, "forward": forward}

    # Cache with 24h TTL (reuses fundamentals table)
    try:
        from app.lib.market_cache import cache_fundamentals
        cache_fundamentals(cache_key, result)
    except Exception:
        logger.debug("Cache write failed for earnings %s", symbol)

    return result
