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
