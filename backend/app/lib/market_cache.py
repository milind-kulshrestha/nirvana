"""
DuckDB-based market data cache layer.

Stores time-series price data, quote snapshots, and fundamentals
separately from the main SQLite app-state database. DuckDB is
optimized for analytical / columnar workloads on market data.

Database location: ~/.nirvana/market_data.duckdb
"""

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import duckdb

# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

_NIRVANA_DIR = Path.home() / ".nirvana"
_DB_PATH = _NIRVANA_DIR / "market_data.duckdb"

_lock = threading.Lock()
_connection: duckdb.DuckDBPyConnection | None = None


def _get_connection() -> duckdb.DuckDBPyConnection:
    """Return a lazily-initialised DuckDB connection (singleton)."""
    global _connection
    if _connection is not None:
        return _connection

    with _lock:
        # Double-check after acquiring the lock
        if _connection is not None:
            return _connection

        _NIRVANA_DIR.mkdir(parents=True, exist_ok=True)
        _connection = duckdb.connect(str(_DB_PATH))
        _init_tables(_connection)
        return _connection


def _init_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create cache tables if they don't already exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_prices (
            symbol  VARCHAR NOT NULL,
            date    DATE    NOT NULL,
            open    DOUBLE,
            high    DOUBLE,
            low     DOUBLE,
            close   DOUBLE,
            volume  BIGINT,
            PRIMARY KEY (symbol, date)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS quotes_cache (
            symbol      VARCHAR PRIMARY KEY,
            data        JSON NOT NULL,
            fetched_at  TIMESTAMP NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals (
            symbol      VARCHAR PRIMARY KEY,
            data        JSON NOT NULL,
            fetched_at  TIMESTAMP NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS etf_snapshot (
            symbol          VARCHAR NOT NULL,
            name            VARCHAR,
            group_name      VARCHAR NOT NULL,
            built_at        TIMESTAMP NOT NULL,
            daily           DOUBLE,
            intra           DOUBLE,
            d5              DOUBLE,
            d20             DOUBLE,
            atr_pct         DOUBLE,
            dist_sma50_atr  DOUBLE,
            rs              DOUBLE,
            abc             VARCHAR,
            long_etfs       VARCHAR,
            short_etfs      VARCHAR,
            rrs_chart       VARCHAR
        )
    """)

    # Add name column if it doesn't exist (for existing tables)
    try:
        conn.execute("ALTER TABLE etf_snapshot ADD COLUMN name VARCHAR")
    except Exception:
        pass  # Column already exists

    conn.execute("""
        CREATE TABLE IF NOT EXISTS etf_holdings (
            symbol      VARCHAR PRIMARY KEY,
            data        VARCHAR NOT NULL,
            fetched_at  TIMESTAMP NOT NULL
        )
    """)


# ---------------------------------------------------------------------------
# Quotes cache  (fresh if < 15 minutes old)
# ---------------------------------------------------------------------------

_QUOTE_TTL = timedelta(minutes=15)


def get_cached_quote(symbol: str) -> dict[str, Any] | None:
    """Return cached quote data if it was fetched less than 15 min ago."""
    conn = _get_connection()
    result = conn.execute(
        "SELECT data, fetched_at FROM quotes_cache WHERE symbol = ?",
        [symbol.upper()],
    ).fetchone()

    if result is None:
        return None

    data_json, fetched_at = result
    if datetime.now(timezone.utc) - fetched_at.replace(tzinfo=timezone.utc) > _QUOTE_TTL:
        return None

    return json.loads(data_json) if isinstance(data_json, str) else data_json


def get_cached_quote_with_ttl(symbol: str, ttl_minutes: int = 15) -> dict[str, Any] | None:
    """Return cached quote data if it was fetched less than ttl_minutes ago."""
    conn = _get_connection()
    result = conn.execute(
        "SELECT data, fetched_at FROM quotes_cache WHERE symbol = ?",
        [symbol.upper()],
    ).fetchone()

    if result is None:
        return None

    data_json, fetched_at = result
    if datetime.now(timezone.utc) - fetched_at.replace(tzinfo=timezone.utc) > timedelta(minutes=ttl_minutes):
        return None

    return json.loads(data_json) if isinstance(data_json, str) else data_json


def cache_quote(symbol: str, data: dict[str, Any]) -> None:
    """Upsert a quote into the cache."""
    conn = _get_connection()
    now = datetime.now(timezone.utc)
    conn.execute(
        """
        INSERT OR REPLACE INTO quotes_cache (symbol, data, fetched_at)
        VALUES (?, ?::JSON, ?)
        """,
        [symbol.upper(), json.dumps(data), now],
    )


# ---------------------------------------------------------------------------
# Daily price history cache
# ---------------------------------------------------------------------------

def get_cached_history(
    symbol: str,
    start_date: str,
    end_date: str,
) -> list[dict[str, Any]] | None:
    """
    Return cached daily prices for *symbol* between *start_date* and
    *end_date* (inclusive, ISO-8601 date strings).

    Returns a list of dicts or ``None`` if there are no cached rows for
    the requested range.
    """
    conn = _get_connection()
    rows = conn.execute(
        """
        SELECT symbol, date, open, high, low, close, volume
        FROM daily_prices
        WHERE symbol = ? AND date BETWEEN ?::DATE AND ?::DATE
        ORDER BY date
        """,
        [symbol.upper(), start_date, end_date],
    ).fetchall()

    if not rows:
        return None

    columns = ["symbol", "date", "open", "high", "low", "close", "volume"]
    return [
        {col: (val.isoformat() if col == "date" else val) for col, val in zip(columns, row)}
        for row in rows
    ]


def cache_history(symbol: str, records: list[dict[str, Any]]) -> None:
    """
    Upsert daily price records for *symbol*.

    Each dict in *records* must contain at least: date, open, high, low,
    close, volume.
    """
    conn = _get_connection()
    sym = symbol.upper()
    for rec in records:
        conn.execute(
            """
            INSERT OR REPLACE INTO daily_prices
                (symbol, date, open, high, low, close, volume)
            VALUES (?, ?::DATE, ?, ?, ?, ?, ?)
            """,
            [
                sym,
                rec["date"],
                rec.get("open"),
                rec.get("high"),
                rec.get("low"),
                rec.get("close"),
                rec.get("volume"),
            ],
        )


# ---------------------------------------------------------------------------
# Fundamentals cache  (fresh if < 24 hours old)
# ---------------------------------------------------------------------------

_FUNDAMENTALS_TTL = timedelta(hours=24)


def get_cached_fundamentals(symbol: str) -> dict[str, Any] | None:
    """Return cached fundamentals if fetched less than 24 hours ago."""
    conn = _get_connection()
    result = conn.execute(
        "SELECT data, fetched_at FROM fundamentals WHERE symbol = ?",
        [symbol.upper()],
    ).fetchone()

    if result is None:
        return None

    data_json, fetched_at = result
    if datetime.now(timezone.utc) - fetched_at.replace(tzinfo=timezone.utc) > _FUNDAMENTALS_TTL:
        return None

    return json.loads(data_json) if isinstance(data_json, str) else data_json


def cache_fundamentals(symbol: str, data: dict[str, Any]) -> None:
    """Upsert fundamentals data into the cache."""
    conn = _get_connection()
    now = datetime.now(timezone.utc)
    conn.execute(
        """
        INSERT OR REPLACE INTO fundamentals (symbol, data, fetched_at)
        VALUES (?, ?::JSON, ?)
        """,
        [symbol.upper(), json.dumps(data), now],
    )


# ---------------------------------------------------------------------------
# ETF snapshot cache
# ---------------------------------------------------------------------------

def save_etf_snapshot(rows: list[dict], built_at) -> None:
    """Replace all ETF snapshot rows with fresh data (atomic via transaction)."""
    conn = _get_connection()
    with _lock:
        conn.execute("BEGIN")
        try:
            conn.execute("DELETE FROM etf_snapshot")
            for row in rows:
                conn.execute(
                    """
                    INSERT INTO etf_snapshot
                        (symbol, name, group_name, built_at, daily, intra, d5, d20,
                         atr_pct, dist_sma50_atr, rs, abc, long_etfs, short_etfs, rrs_chart)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        row["symbol"].upper(),
                        row.get("name"),
                        row["group_name"],
                        built_at,
                        row.get("daily"),
                        row.get("intra"),
                        row.get("d5"),
                        row.get("d20"),
                        row.get("atr_pct"),
                        row.get("dist_sma50_atr"),
                        row.get("rs"),
                        row.get("abc"),
                        json.dumps(row.get("long_etfs", [])),
                        json.dumps(row.get("short_etfs", [])),
                        json.dumps(row.get("rrs_chart", [])),
                    ],
                )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise


def get_etf_snapshot() -> dict | None:
    """Return full ETF snapshot grouped by category, or None if empty."""
    conn = _get_connection()
    rows = conn.execute(
        """
        SELECT symbol, name, group_name, built_at, daily, intra, d5, d20,
               atr_pct, dist_sma50_atr, rs, abc, long_etfs, short_etfs, rrs_chart
        FROM etf_snapshot
        ORDER BY group_name, symbol
        """
    ).fetchall()

    if not rows:
        return None

    built_at = rows[0][3]
    groups: dict[str, list] = {}
    col_ranges: dict[str, dict] = {}

    for row in rows:
        sym, name, grp, _, daily, intra, d5, d20, atr_pct, dist, rs, abc, longs, shorts, chart = row
        item = {
            "ticker": sym,
            "name": name,
            "daily": daily, "intra": intra, "5d": d5, "20d": d20,
            "atr_pct": atr_pct, "dist_sma50_atr": dist,
            "rs": rs, "abc": abc,
            "long": json.loads(longs) if longs else [],
            "short": json.loads(shorts) if shorts else [],
            "rrs_chart": json.loads(chart) if chart else [],
        }
        groups.setdefault(grp, []).append(item)

    for grp, items in groups.items():
        def _range(key):
            vals = [i[key] for i in items if i.get(key) is not None]
            return [min(vals), max(vals)] if vals else [-10, 10]
        col_ranges[grp] = {
            "daily": _range("daily"), "intra": _range("intra"),
            "5d": _range("5d"), "20d": _range("20d"),
        }

    return {
        "built_at": built_at.isoformat() if hasattr(built_at, "isoformat") else str(built_at),
        "groups": groups,
        "column_ranges": col_ranges,
    }


# ---------------------------------------------------------------------------
# ETF holdings cache  (24h TTL)
# ---------------------------------------------------------------------------

_HOLDINGS_TTL = timedelta(hours=24)


def get_etf_holdings(symbol: str) -> list[dict] | None:
    """Return cached ETF holdings if < 24 hours old."""
    conn = _get_connection()
    result = conn.execute(
        "SELECT data, fetched_at FROM etf_holdings WHERE symbol = ?",
        [symbol.upper()],
    ).fetchone()

    if result is None:
        return None

    data_json, fetched_at = result
    if datetime.now(timezone.utc) - fetched_at.replace(tzinfo=timezone.utc) > _HOLDINGS_TTL:
        return None

    return json.loads(data_json) if isinstance(data_json, str) else data_json


def save_etf_holdings(symbol: str, data: list[dict]) -> None:
    """Upsert ETF holdings into cache."""
    conn = _get_connection()
    now = datetime.now(timezone.utc)
    conn.execute(
        """
        INSERT OR REPLACE INTO etf_holdings (symbol, data, fetched_at)
        VALUES (?, ?, ?)
        """,
        [symbol.upper(), json.dumps(data), now],
    )
