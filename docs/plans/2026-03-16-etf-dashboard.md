# ETF Dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a dedicated `/etf` page to Nirvana that displays ~180 preset ETFs (plus user-added custom ones) with ABC Rating, ATR%, ATRx, VARS, and RS sparkline indicators powered by yfinance.

**Architecture:** New `etf_engine.py` library ports the computation logic from `market_dashboard/scripts/build_data.py`. Data is cached in two new DuckDB tables (`etf_snapshot`, `etf_holdings`). User's custom ETF symbols live in a new SQLite model `EtfCustomSymbol`. A new FastAPI router (`etf.py`) serves snapshot data and streams refresh progress via SSE. The frontend has a new `ETFDashboard.jsx` page with category tabs, a sortable data table, inline SVG sparklines, and holdings popovers.

**Tech Stack:** Python (yfinance, scipy, pandas, numpy, asyncio), FastAPI SSE (StreamingResponse), DuckDB, SQLAlchemy SQLite, React + Zustand + shadcn/ui

---

## Task 1: Add yfinance and scipy to requirements

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Add dependencies**

In `backend/requirements.txt`, add after the `# AI Agent` section:

```
# ETF data (yfinance)
yfinance>=0.2.40
scipy>=1.11.0
```

**Step 2: Install**

```bash
cd backend && pip install yfinance scipy
```

Expected: installs without error. pandas and numpy come in transitively.

**Step 3: Verify**

```bash
python -c "import yfinance; import scipy; print('ok')"
```

Expected: `ok`

**Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add yfinance and scipy for ETF engine"
```

---

## Task 2: DuckDB tables for ETF data

**Files:**
- Modify: `backend/app/lib/market_cache.py`

**Step 1: Write the failing test**

Create `backend/tests/test_etf_cache.py`:

```python
"""Tests for ETF DuckDB cache functions."""
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch
import duckdb

# Use an in-memory DuckDB for tests
@pytest.fixture
def mock_conn(monkeypatch):
    conn = duckdb.connect(":memory:")
    monkeypatch.setattr("app.lib.market_cache._connection", conn)
    # Re-run init to create all tables including ETF ones
    from app.lib import market_cache
    market_cache._init_tables(conn)
    return conn


def test_save_etf_snapshot_and_retrieve(mock_conn):
    from app.lib.market_cache import save_etf_snapshot, get_etf_snapshot

    rows = [
        {
            "symbol": "SPY", "group_name": "Indices",
            "daily": 0.4, "intra": 0.1, "d5": 1.2, "d20": 3.1,
            "atr_pct": 0.9, "dist_sma50_atr": 1.3, "rs": 72.0, "abc": "A",
            "long_etfs": ["SPXL"], "short_etfs": ["SPXS"],
            "rrs_chart": [0.1, 0.2, 0.3],
        }
    ]
    built_at = datetime.now(timezone.utc)
    save_etf_snapshot(rows, built_at)

    result = get_etf_snapshot()
    assert result is not None
    assert result["built_at"] is not None
    groups = result["groups"]
    assert "Indices" in groups
    spys = [r for r in groups["Indices"] if r["ticker"] == "SPY"]
    assert len(spys) == 1
    assert spys[0]["abc"] == "A"
    assert spys[0]["long"] == ["SPXL"]
    assert spys[0]["rrs_chart"] == [0.1, 0.2, 0.3]


def test_get_etf_snapshot_empty(mock_conn):
    from app.lib.market_cache import get_etf_snapshot
    result = get_etf_snapshot()
    assert result is None


def test_save_etf_holdings_and_retrieve(mock_conn):
    from app.lib.market_cache import save_etf_holdings, get_etf_holdings

    data = [{"symbol": "AAPL", "weight": 0.072}, {"symbol": "MSFT", "weight": 0.065}]
    save_etf_holdings("SPY", data)

    result = get_etf_holdings("SPY")
    assert result is not None
    assert len(result) == 2
    assert result[0]["symbol"] == "AAPL"


def test_get_etf_holdings_missing(mock_conn):
    from app.lib.market_cache import get_etf_holdings
    result = get_etf_holdings("DOESNOTEXIST")
    assert result is None
```

**Step 2: Run to verify failure**

```bash
cd backend && python -m pytest tests/test_etf_cache.py -v
```

Expected: ImportError or AttributeError (functions don't exist yet)

**Step 3: Add ETF tables and functions to `market_cache.py`**

In `_init_tables()`, add after the `fundamentals` table:

```python
    conn.execute("""
        CREATE TABLE IF NOT EXISTS etf_snapshot (
            symbol          VARCHAR NOT NULL,
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS etf_holdings (
            symbol      VARCHAR PRIMARY KEY,
            data        VARCHAR NOT NULL,
            fetched_at  TIMESTAMP NOT NULL
        )
    """)
```

Then add these functions at the bottom of `market_cache.py`:

```python
# ---------------------------------------------------------------------------
# ETF snapshot cache
# ---------------------------------------------------------------------------

def save_etf_snapshot(rows: list[dict], built_at) -> None:
    """Replace all ETF snapshot rows with fresh data."""
    conn = _get_connection()
    with _lock:
        conn.execute("DELETE FROM etf_snapshot")
        for row in rows:
            conn.execute(
                """
                INSERT INTO etf_snapshot
                    (symbol, group_name, built_at, daily, intra, d5, d20,
                     atr_pct, dist_sma50_atr, rs, abc, long_etfs, short_etfs, rrs_chart)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    row["symbol"].upper(),
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


def get_etf_snapshot() -> dict | None:
    """Return full ETF snapshot grouped by category, or None if empty."""
    conn = _get_connection()
    rows = conn.execute(
        """
        SELECT symbol, group_name, built_at, daily, intra, d5, d20,
               atr_pct, dist_sma50_atr, rs, abc, long_etfs, short_etfs, rrs_chart
        FROM etf_snapshot
        ORDER BY group_name, symbol
        """
    ).fetchall()

    if not rows:
        return None

    built_at = rows[0][2]
    groups: dict[str, list] = {}
    col_ranges: dict[str, dict] = {}

    for row in rows:
        sym, grp, _, daily, intra, d5, d20, atr_pct, dist, rs, abc, longs, shorts, chart = row
        item = {
            "ticker": sym,
            "daily": daily, "intra": intra, "5d": d5, "20d": d20,
            "atr_pct": atr_pct, "dist_sma50_atr": dist,
            "rs": rs, "abc": abc,
            "long": json.loads(longs) if longs else [],
            "short": json.loads(shorts) if shorts else [],
            "rrs_chart": json.loads(chart) if chart else [],
        }
        groups.setdefault(grp, []).append(item)

    # Compute column ranges per group
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
```

**Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_etf_cache.py -v
```

Expected: 4 tests PASS

**Step 5: Commit**

```bash
git add backend/app/lib/market_cache.py backend/tests/test_etf_cache.py
git commit -m "feat: add ETF DuckDB cache tables and functions"
```

---

## Task 3: EtfCustomSymbol SQLAlchemy model

**Files:**
- Create: `backend/app/models/etf_custom_symbol.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/database.py`

**Step 1: Write the failing test**

Create `backend/tests/test_etf_model.py`:

```python
"""Tests for EtfCustomSymbol model."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_and_retrieve_custom_symbol(db):
    from app.models.etf_custom_symbol import EtfCustomSymbol
    sym = EtfCustomSymbol(symbol="TQQQ")
    db.add(sym)
    db.commit()

    result = db.query(EtfCustomSymbol).filter_by(symbol="TQQQ").first()
    assert result is not None
    assert result.symbol == "TQQQ"
    assert result.added_at is not None


def test_symbol_is_primary_key(db):
    from app.models.etf_custom_symbol import EtfCustomSymbol
    from sqlalchemy.exc import IntegrityError
    db.add(EtfCustomSymbol(symbol="TQQQ"))
    db.commit()
    db.add(EtfCustomSymbol(symbol="TQQQ"))
    with pytest.raises(IntegrityError):
        db.commit()
```

**Step 2: Run to verify failure**

```bash
cd backend && python -m pytest tests/test_etf_model.py -v
```

Expected: ImportError

**Step 3: Create the model**

Create `backend/app/models/etf_custom_symbol.py`:

```python
"""Custom ETF symbols added by the user."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.database import Base


class EtfCustomSymbol(Base):
    __tablename__ = "etf_custom_symbols"

    symbol    = Column(String(20), primary_key=True)
    added_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
```

**Step 4: Register the model**

In `backend/app/models/__init__.py`, add:

```python
from app.models.etf_custom_symbol import EtfCustomSymbol

__all__ = [
    ...,
    "EtfCustomSymbol",
]
```

In `backend/app/database.py`, add `EtfCustomSymbol` to the `init_db()` import list:

```python
    from app.models import (
        User, Watchlist, WatchlistItem, Conversation,
        Message, MemoryFact, PendingAction, Skill, EtfCustomSymbol,
    )
```

**Step 5: Run tests**

```bash
cd backend && python -m pytest tests/test_etf_model.py -v
```

Expected: 2 tests PASS

**Step 6: Commit**

```bash
git add backend/app/models/etf_custom_symbol.py backend/app/models/__init__.py backend/app/database.py backend/tests/test_etf_model.py
git commit -m "feat: add EtfCustomSymbol SQLAlchemy model"
```

---

## Task 4: ETF engine — computation functions

**Files:**
- Create: `backend/app/lib/etf_engine.py`

**Step 1: Write the failing tests**

Create `backend/tests/test_etf_engine.py`:

```python
"""Tests for ETF computation functions in etf_engine.py."""
import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timedelta


def _make_hist(n=60, trend="up"):
    """Create synthetic OHLCV history."""
    dates = pd.date_range(end=datetime.today(), periods=n, freq="B")
    if trend == "up":
        close = pd.Series(np.linspace(100, 130, n), index=dates)
    else:
        close = pd.Series(np.linspace(130, 100, n), index=dates)
    high  = close * 1.01
    low   = close * 0.99
    open_ = close * 0.995
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": 1_000_000})


def test_calculate_sma():
    from app.lib.etf_engine import calculate_sma
    hist = _make_hist(60)
    sma = calculate_sma(hist, 50)
    assert sma is not None
    assert isinstance(sma, float)


def test_calculate_ema():
    from app.lib.etf_engine import calculate_ema
    hist = _make_hist(60)
    ema = calculate_ema(hist, 10)
    assert ema is not None
    assert isinstance(ema, float)


def test_calculate_atr():
    from app.lib.etf_engine import calculate_atr
    hist = _make_hist(60)
    atr = calculate_atr(hist, 14)
    assert atr is not None
    assert atr > 0


def test_abc_rating_uptrend_is_A():
    from app.lib.etf_engine import calculate_abc_rating
    # Strong uptrend: EMA10 > EMA20 > SMA50
    hist = _make_hist(60, trend="up")
    rating = calculate_abc_rating(hist)
    assert rating == "A"


def test_abc_rating_downtrend_is_C():
    from app.lib.etf_engine import calculate_abc_rating
    hist = _make_hist(60, trend="down")
    rating = calculate_abc_rating(hist)
    assert rating == "C"


def test_get_rrs_chart_data_returns_list():
    from app.lib.etf_engine import calculate_rrs, get_rrs_chart_data
    stock = _make_hist(120, trend="up")
    spy   = _make_hist(120, trend="up")
    rrs_df = calculate_rrs(stock, spy)
    assert rrs_df is not None
    chart = get_rrs_chart_data(rrs_df)
    assert isinstance(chart, list)
    assert len(chart) <= 20
    assert all(isinstance(v, float) for v in chart)


def test_get_rrs_chart_data_none_returns_empty():
    from app.lib.etf_engine import get_rrs_chart_data
    result = get_rrs_chart_data(None)
    assert result == []
```

**Step 2: Run to verify failure**

```bash
cd backend && python -m pytest tests/test_etf_engine.py -v
```

Expected: ImportError

**Step 3: Create `etf_engine.py` with computation functions**

Create `backend/app/lib/etf_engine.py`:

```python
"""
ETF data engine — fetches metrics from Yahoo Finance and computes
technical indicators (ABC Rating, ATR, ATRx, VARS/RRS).

Ported from market_dashboard/scripts/build_data.py.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import rankdata

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static data: ETF groups and leveraged ETF map
# ---------------------------------------------------------------------------

STOCK_GROUPS: dict[str, list[str]] = {
    "Indices": ["QQQE", "MGK", "QQQ", "IBIT", "RSP", "MDY", "IWM", "TLT", "SPY", "ETHA", "DIA"],
    "S&P Style": ["IJS", "IJR", "IJT", "IJJ", "IJH", "IJK", "IVE", "IVV", "IVW"],
    "Sel Sectors": ["XLK", "XLI", "XLC", "XLF", "XLU", "XLY", "XLRE", "XLP", "XLB", "XLE", "XLV"],
    "EW Sectors": ["RSPT", "RSPC", "RSPN", "RSPF", "RSP", "RSPD", "RSPU", "RSPR", "RSPH", "RSPM", "RSPS", "RSPG"],
    "Industries": [
        "TAN", "KCE", "IBUY", "QQQE", "JETS", "IBB", "SMH", "CIBR", "UTES", "ROBO", "IGV", "WCLD", "ITA", "PAVE",
        "BLOK", "AIQ", "IYZ", "PEJ", "FDN", "KBE", "UNG", "BOAT", "KWEB", "KRE", "IBIT", "XRT", "IHI", "DRIV",
        "MSOS", "SOCL", "XLU", "ARKF", "SLX", "ARKK", "XTN", "XME", "KIE", "GLD", "GXC", "SCHH", "GDX", "IPAY",
        "IWM", "XOP", "VNQ", "EATZ", "FXI", "DBA", "ICLN", "SILJ", "REZ", "LIT", "SLV", "XHB", "XHE", "PBJ",
        "USO", "DBC", "FCG", "XBI", "ARKG", "CPER", "XES", "OIH", "PPH", "FNGS", "URA", "WGMI", "REMX",
    ],
    "Countries": [
        "EZA", "ARGT", "EWA", "THD", "EIDO", "EWC", "GREK", "EWP", "EWG", "EWL", "EUFN", "EWY", "IEUR", "EFA",
        "ACWI", "IEV", "EWQ", "EWI", "EWJ", "EWW", "ECH", "EWD", "ASHR", "EWS", "KSA", "INDA", "EEM", "EWZ",
        "TUR", "EWH", "EWT", "MCHI",
    ],
}

LEVERAGED_ETFS: dict[str, dict[str, list[str]]] = {
    "QQQ":  {"long": ["TQQQ"],        "short": ["SQQQ"]},
    "MDY":  {"long": ["MIDU"],        "short": []},
    "IWM":  {"long": ["TNA"],         "short": ["TZA"]},
    "TLT":  {"long": ["TMF"],         "short": ["TMV"]},
    "SPY":  {"long": ["SPXL", "UPRO"],"short": ["SPXS", "SH"]},
    "ETHA": {"long": ["ETHU"],        "short": []},
    "XLK":  {"long": ["TECL"],        "short": ["TECS"]},
    "XLI":  {"long": ["DUSL"],        "short": []},
    "XLC":  {"long": ["LTL"],         "short": []},
    "XLF":  {"long": ["FAS"],         "short": ["FAZ"]},
    "XLU":  {"long": ["UTSL"],        "short": []},
    "XLY":  {"long": ["WANT"],        "short": ["SCC"]},
    "XLRE": {"long": ["DRN"],         "short": ["DRV"]},
    "XLP":  {"long": ["UGE"],         "short": ["SZK"]},
    "XLB":  {"long": ["UYM"],         "short": ["SMN"]},
    "XLE":  {"long": ["ERX"],         "short": ["ERY"]},
    "XLV":  {"long": ["CURE"],        "short": []},
    "SMH":  {"long": ["SOXL"],        "short": ["SOXS"]},
    "ARKK": {"long": ["TARK"],        "short": ["SARK"]},
    "XTN":  {"long": ["TPOR"],        "short": []},
    "KWEB": {"long": ["CWEB"],        "short": []},
    "XRT":  {"long": ["RETL"],        "short": []},
    "KRE":  {"long": ["DPST"],        "short": []},
    "DRIV": {"long": ["EVAV"],        "short": []},
    "XBI":  {"long": ["LABU"],        "short": ["LABD"]},
    "ROBO": {"long": ["UBOT"],        "short": []},
    "XHB":  {"long": ["NAIL"],        "short": []},
    "FNGS": {"long": ["FNGB"],        "short": ["FNGD"]},
    "WCLD": {"long": ["CLDL"],        "short": []},
    "XOP":  {"long": ["GUSH"],        "short": ["DRIP"]},
    "FDN":  {"long": ["WEBL"],        "short": ["WEBS"]},
    "FXI":  {"long": ["YINN"],        "short": ["YANG"]},
    "PEJ":  {"long": ["OOTO"],        "short": []},
    "USO":  {"long": ["UCO"],         "short": ["SCO"]},
    "PPH":  {"long": ["PILL"],        "short": []},
    "ITA":  {"long": ["DFEN"],        "short": []},
    "SLV":  {"long": ["AGQ"],         "short": ["ZSL"]},
    "GLD":  {"long": ["UGL"],         "short": ["GLL"]},
    "UNG":  {"long": ["BOIL"],        "short": ["KOLD"]},
    "GDX":  {"long": ["NUGT", "GDXU"],"short": ["JDST", "GDXD"]},
    "IBIT": {"long": ["BITX", "BITU"],"short": ["SBIT", "BITI"]},
    "MSOS": {"long": ["MSOX"],        "short": []},
    "EWY":  {"long": ["KORU"],        "short": []},
    "IEV":  {"long": ["EURL"],        "short": []},
    "EWJ":  {"long": ["EZJ"],         "short": []},
    "EWW":  {"long": ["MEXX"],        "short": []},
    "ASHR": {"long": ["CHAU"],        "short": []},
    "INDA": {"long": ["INDL"],        "short": []},
    "EEM":  {"long": ["EDC"],         "short": ["EDZ"]},
    "EWZ":  {"long": ["BRZU"],        "short": []},
}


# ---------------------------------------------------------------------------
# Computation functions (pure, testable)
# ---------------------------------------------------------------------------

def calculate_sma(hist_data: pd.DataFrame, period: int = 50) -> float | None:
    try:
        return float(hist_data["Close"].rolling(window=period).mean().iloc[-1])
    except Exception:
        return None


def calculate_ema(hist_data: pd.DataFrame, period: int = 10) -> float | None:
    try:
        return float(hist_data["Close"].ewm(span=period, adjust=False).mean().iloc[-1])
    except Exception:
        return None


def calculate_atr(hist_data: pd.DataFrame, period: int = 14) -> float | None:
    try:
        hl = hist_data["High"] - hist_data["Low"]
        hc = (hist_data["High"] - hist_data["Close"].shift()).abs()
        lc = (hist_data["Low"] - hist_data["Close"].shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        return float(tr.ewm(alpha=1 / period, adjust=False).mean().iloc[-1])
    except Exception:
        return None


def calculate_abc_rating(hist_data: pd.DataFrame) -> str | None:
    try:
        ema10 = calculate_ema(hist_data, 10)
        ema20 = calculate_ema(hist_data, 20)
        sma50 = calculate_sma(hist_data, 50)
        if ema10 is None or ema20 is None or sma50 is None:
            return None
        if ema10 > ema20 and ema20 > sma50:
            return "A"
        if ema10 < ema20 and ema20 < sma50:
            return "C"
        return "B"
    except Exception:
        return None


def calculate_rrs(
    stock_data: pd.DataFrame,
    spy_data: pd.DataFrame,
    atr_length: int = 14,
    length_rolling: int = 50,
    length_sma: int = 20,
    atr_multiplier: float = 1.0,
) -> pd.DataFrame | None:
    try:
        merged = pd.merge(
            stock_data[["High", "Low", "Close"]],
            spy_data[["High", "Low", "Close"]],
            left_index=True, right_index=True,
            suffixes=("_stock", "_spy"), how="inner",
        )
        if len(merged) < atr_length + 1:
            return None
        for prefix in ["stock", "spy"]:
            h, l, c = merged[f"High_{prefix}"], merged[f"Low_{prefix}"], merged[f"Close_{prefix}"]
            tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
            merged[f"atr_{prefix}"] = tr.ewm(alpha=1 / atr_length, adjust=False).mean()
        sc    = merged["Close_stock"] - merged["Close_stock"].shift(1)
        spy_c = merged["Close_spy"] - merged["Close_spy"].shift(1)
        spy_pi   = spy_c / merged["atr_spy"]
        expected = spy_pi * merged["atr_stock"] * atr_multiplier
        rrs = (sc - expected) / merged["atr_stock"]
        rolling_rrs = rrs.rolling(window=length_rolling, min_periods=1).mean()
        rrs_sma     = rolling_rrs.rolling(window=length_sma, min_periods=1).mean()
        return pd.DataFrame({"RRS": rrs, "rollingRRS": rolling_rrs, "RRS_SMA": rrs_sma}, index=merged.index)
    except Exception:
        return None


def get_rrs_chart_data(rrs_df: pd.DataFrame | None, n: int = 20) -> list[float]:
    """Return the last n rollingRRS values as a plain float list for the sparkline."""
    if rrs_df is None or len(rrs_df) == 0:
        return []
    vals = rrs_df["rollingRRS"].tail(n).tolist()
    return [round(float(v), 4) if v == v else 0.0 for v in vals]  # NaN → 0.0
```

**Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_etf_engine.py -v
```

Expected: 7 tests PASS

**Step 5: Commit**

```bash
git add backend/app/lib/etf_engine.py backend/tests/test_etf_engine.py
git commit -m "feat: add ETF engine computation functions (ABC, ATR, RRS)"
```

---

## Task 5: ETF engine — fetch orchestration

**Files:**
- Modify: `backend/app/lib/etf_engine.py`

**Step 1: Write the failing test**

In `backend/tests/test_etf_engine.py`, add:

```python
def test_fetch_etf_row_returns_dict(monkeypatch):
    """fetch_etf_row returns a dict with expected keys when yfinance works."""
    from app.lib.etf_engine import fetch_etf_row

    hist_60 = _make_hist(60)
    hist_21 = _make_hist(21)
    hist_120 = _make_hist(120)

    class FakeTicker:
        def history(self, period=None, start=None, end=None):
            if period == "21d":
                return hist_21
            if period == "60d":
                return hist_60
            return hist_120

    monkeypatch.setattr("yfinance.Ticker", lambda sym: FakeTicker())
    result = fetch_etf_row("SPY", "Indices")
    assert result is not None
    assert result["symbol"] == "SPY"
    assert result["group_name"] == "Indices"
    assert "abc" in result
    assert "atr_pct" in result
    assert isinstance(result["rrs_chart"], list)


def test_fetch_etf_row_returns_none_on_insufficient_data(monkeypatch):
    from app.lib.etf_engine import fetch_etf_row

    class EmptyTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr("yfinance.Ticker", lambda sym: EmptyTicker())
    result = fetch_etf_row("BAD", "Indices")
    assert result is None
```

**Step 2: Run to verify failure**

```bash
cd backend && python -m pytest tests/test_etf_engine.py::test_fetch_etf_row_returns_dict -v
```

Expected: ImportError or AttributeError

**Step 3: Add fetch functions to `etf_engine.py`**

Append to `backend/app/lib/etf_engine.py`:

```python
# ---------------------------------------------------------------------------
# yfinance fetch functions (synchronous — call via asyncio.to_thread)
# ---------------------------------------------------------------------------

def _get_leveraged(ticker: str) -> tuple[list[str], list[str]]:
    entry = LEVERAGED_ETFS.get(ticker.upper(), {})
    return entry.get("long", []), entry.get("short", [])


def fetch_etf_row(symbol: str, group_name: str) -> dict | None:
    """
    Fetch all metrics for one ETF symbol via yfinance.
    Returns a flat dict ready for save_etf_snapshot(), or None on failure.
    This is synchronous — call via asyncio.to_thread() from async contexts.
    """
    try:
        stock = yf.Ticker(symbol)
        hist_21  = stock.history(period="21d")
        hist_60  = stock.history(period="60d")
        if len(hist_21) < 2 or len(hist_60) < 50:
            return None

        daily = float((hist_21["Close"].iloc[-1] / hist_21["Close"].iloc[-2] - 1) * 100)
        intra = float((hist_21["Close"].iloc[-1] / hist_21["Open"].iloc[-1] - 1) * 100)
        d5    = float((hist_21["Close"].iloc[-1] / hist_21["Close"].iloc[-6] - 1) * 100) if len(hist_21) >= 6 else None
        d20   = float((hist_21["Close"].iloc[-1] / hist_21["Close"].iloc[-21] - 1) * 100) if len(hist_21) >= 21 else None

        sma50   = calculate_sma(hist_60)
        atr     = calculate_atr(hist_60)
        current = float(hist_60["Close"].iloc[-1])
        atr_pct = round((atr / current) * 100, 1) if (atr and current) else None
        dist    = round(100 * (current / sma50 - 1) / atr_pct, 2) if (sma50 and atr_pct and atr_pct != 0) else None
        abc     = calculate_abc_rating(hist_60)

        # Relative strength vs SPY (120 days)
        rrs_df  = None
        rs_sts  = None
        try:
            end   = datetime.now()
            start = end - timedelta(days=120)
            hist_120 = stock.history(start=start, end=end)
            spy_120  = yf.Ticker("SPY").history(start=start, end=end)
            if len(hist_120) >= 21 and len(spy_120) >= 21:
                rrs_df = calculate_rrs(hist_120, spy_120)
                if rrs_df is not None and len(rrs_df) >= 21:
                    recent = rrs_df["rollingRRS"].iloc[-21:]
                    ranks  = rankdata(recent, method="average")
                    rs_sts = round(float((ranks[-1] - 1) / (len(recent) - 1) * 100), 0)
        except Exception as e:
            logger.debug("RRS error %s: %s", symbol, e)

        long_etfs, short_etfs = _get_leveraged(symbol)

        return {
            "symbol":        symbol.upper(),
            "group_name":    group_name,
            "daily":         round(daily, 2),
            "intra":         round(intra, 2),
            "d5":            round(d5, 2) if d5 is not None else None,
            "d20":           round(d20, 2) if d20 is not None else None,
            "atr_pct":       atr_pct,
            "dist_sma50_atr": dist,
            "rs":            rs_sts,
            "abc":           abc,
            "long_etfs":     long_etfs,
            "short_etfs":    short_etfs,
            "rrs_chart":     get_rrs_chart_data(rrs_df),
        }
    except Exception as e:
        logger.warning("Error fetching %s: %s", symbol, e)
        return None


def fetch_etf_holdings_sync(symbol: str) -> list[dict]:
    """Fetch top 10 holdings for an ETF via yfinance. Returns [] on failure."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.funds_data.top_holdings
        if df is not None and len(df) > 0:
            holdings = []
            for idx, row in df.head(10).iterrows():
                holding_symbol = str(idx) if str(idx) != "nan" else str(row.get("Symbol", ""))
                weight = row.get("Holding Percent", row.get("weight"))
                try:
                    weight = float(weight) if weight is not None else None
                except (ValueError, TypeError):
                    weight = None
                holdings.append({"symbol": holding_symbol, "weight": weight})
            return holdings
    except Exception as e:
        logger.debug("Holdings error %s: %s", symbol, e)
    return []


# ---------------------------------------------------------------------------
# Async orchestration (used by the SSE refresh endpoint)
# ---------------------------------------------------------------------------

async def stream_etf_refresh(
    custom_symbols: list[str],
) -> AsyncIterator[dict]:
    """
    Async generator that fetches all preset + custom ETFs and yields progress events.

    Yields dicts:
      { "type": "progress", "symbol": "SPY", "done": 12, "total": 180 }
      { "type": "error",    "symbol": "XYZ", "msg": "no data" }
      { "type": "complete", "built_at": "..." }
    """
    from app.lib.market_cache import save_etf_snapshot

    # Build ordered work list: preset groups + Custom group
    work: list[tuple[str, str]] = []
    for group_name, symbols in STOCK_GROUPS.items():
        for sym in symbols:
            work.append((sym, group_name))
    for sym in custom_symbols:
        if sym.upper() not in {s for s, _ in work}:
            work.append((sym.upper(), "Custom"))

    total = len(work)
    rows: list[dict] = []

    for done, (symbol, group_name) in enumerate(work, start=1):
        row = await asyncio.to_thread(fetch_etf_row, symbol, group_name)
        if row:
            rows.append(row)
            yield {"type": "progress", "symbol": symbol, "done": done, "total": total}
        else:
            yield {"type": "error", "symbol": symbol, "msg": "no data", "done": done, "total": total}

    built_at = datetime.now(timezone.utc)
    save_etf_snapshot(rows, built_at)
    yield {"type": "complete", "built_at": built_at.isoformat()}
```

**Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_etf_engine.py -v
```

Expected: all 9 tests PASS

**Step 5: Commit**

```bash
git add backend/app/lib/etf_engine.py backend/tests/test_etf_engine.py
git commit -m "feat: add ETF fetch orchestration and async refresh stream"
```

---

## Task 6: ETF API routes

**Files:**
- Create: `backend/app/routes/etf.py`
- Modify: `backend/app/main.py`

**Step 1: Write the failing tests**

Create `backend/tests/test_etf_routes.py`:

```python
"""Tests for ETF API routes."""
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app, cookies={"session": "test"})


@pytest.fixture(autouse=True)
def mock_auth(monkeypatch):
    """Bypass auth — inject a fake user."""
    from app.models.user import User
    fake_user = User(id=1, email="test@test.com")
    monkeypatch.setattr(
        "app.routes.etf.get_current_user",
        lambda session=None, db=None: fake_user,
    )


def test_snapshot_empty():
    with patch("app.routes.etf.get_etf_snapshot", return_value=None):
        resp = client.get("/api/etf/snapshot")
    assert resp.status_code == 200
    assert resp.json() is None


def test_snapshot_returns_data():
    fake = {
        "built_at": "2026-03-16T20:00:00Z",
        "groups": {"Indices": [{"ticker": "SPY", "abc": "A"}]},
        "column_ranges": {},
    }
    with patch("app.routes.etf.get_etf_snapshot", return_value=fake):
        resp = client.get("/api/etf/snapshot")
    assert resp.status_code == 200
    assert resp.json()["groups"]["Indices"][0]["ticker"] == "SPY"


def test_get_custom_symbols_empty(tmp_path, monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Base

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides["app.database.get_db"] = override_db
    resp = client.get("/api/etf/custom")
    assert resp.status_code == 200
    assert resp.json() == []
    app.dependency_overrides.clear()


def test_holdings_cached():
    holdings = [{"symbol": "AAPL", "weight": 0.07}]
    with patch("app.routes.etf.get_etf_holdings", return_value=holdings):
        resp = client.get("/api/etf/holdings/SPY")
    assert resp.status_code == 200
    assert resp.json()[0]["symbol"] == "AAPL"


def test_holdings_not_found_fetches_live():
    with patch("app.routes.etf.get_etf_holdings", return_value=None), \
         patch("app.routes.etf.fetch_etf_holdings_sync", return_value=[]):
        resp = client.get("/api/etf/holdings/UNKNOWN")
    assert resp.status_code == 200
    assert resp.json() == []
```

**Step 2: Run to verify failure**

```bash
cd backend && python -m pytest tests/test_etf_routes.py -v
```

Expected: ImportError (no etf routes yet)

**Step 3: Create `backend/app/routes/etf.py`**

```python
"""ETF dashboard routes."""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.auth import get_current_user
from app.models.user import User
from app.models.etf_custom_symbol import EtfCustomSymbol
from app.lib.market_cache import get_etf_snapshot, get_etf_holdings, save_etf_holdings
from app.lib.etf_engine import stream_etf_refresh, fetch_etf_holdings_sync

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/snapshot")
async def snapshot(current_user: User = Depends(get_current_user)):
    """Return cached ETF snapshot or null if not yet built."""
    return get_etf_snapshot()


@router.post("/refresh")
async def refresh(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SSE stream — fetches all ETFs and streams progress events."""
    custom_symbols = [row.symbol for row in db.query(EtfCustomSymbol).all()]

    async def event_stream():
        async for event in stream_etf_refresh(custom_symbols):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/holdings/{symbol}")
async def holdings(
    symbol: str,
    current_user: User = Depends(get_current_user),
):
    """Return ETF top-10 holdings (cached 24h, lazy-fetched on miss)."""
    cached = get_etf_holdings(symbol.upper())
    if cached is not None:
        return cached

    data = await __import__("asyncio").to_thread(fetch_etf_holdings_sync, symbol.upper())
    if data:
        save_etf_holdings(symbol.upper(), data)
    return data


@router.get("/custom")
async def get_custom(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return user's custom ETF symbols."""
    rows = db.query(EtfCustomSymbol).order_by(EtfCustomSymbol.added_at).all()
    return [row.symbol for row in rows]


@router.post("/custom/{symbol}", status_code=201)
async def add_custom(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a custom ETF symbol."""
    sym = symbol.upper()
    existing = db.query(EtfCustomSymbol).filter_by(symbol=sym).first()
    if existing:
        return {"symbol": sym, "status": "already exists"}
    db.add(EtfCustomSymbol(symbol=sym))
    db.commit()
    return {"symbol": sym, "status": "added"}


@router.delete("/custom/{symbol}")
async def remove_custom(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a custom ETF symbol."""
    sym = symbol.upper()
    row = db.query(EtfCustomSymbol).filter_by(symbol=sym).first()
    if not row:
        raise HTTPException(status_code=404, detail="Symbol not found")
    db.delete(row)
    db.commit()
    return {"symbol": sym, "status": "removed"}
```

**Step 4: Register router in `backend/app/main.py`**

Add to the imports:
```python
from app.routes import etf as etf_routes
```

Add after the existing `include_router` calls:
```python
app.include_router(etf_routes.router, prefix="/api/etf", tags=["ETF"])
```

**Step 5: Run tests**

```bash
cd backend && python -m pytest tests/test_etf_routes.py -v
```

Expected: all 5 tests PASS

**Step 6: Commit**

```bash
git add backend/app/routes/etf.py backend/app/main.py backend/tests/test_etf_routes.py
git commit -m "feat: add ETF API routes (snapshot, refresh SSE, holdings, custom)"
```

---

## Task 7: etfStore.js — Zustand store

**Files:**
- Create: `frontend/src/stores/etfStore.js`

**Step 1: Write the failing test**

Create `frontend/src/stores/etfStore.test.js`:

```js
import { describe, it, expect, beforeEach } from 'vitest';
import { act } from 'react';

// Reset store between tests
beforeEach(() => {
  const { default: useEtfStore } = require('./etfStore');
  useEtfStore.setState({
    snapshot: null,
    status: 'idle',
    progress: { done: 0, total: 0, current: '' },
    customSymbols: [],
  });
});

describe('etfStore', () => {
  it('initial state is idle with no snapshot', () => {
    const { default: useEtfStore } = require('./etfStore');
    const state = useEtfStore.getState();
    expect(state.snapshot).toBeNull();
    expect(state.status).toBe('idle');
    expect(state.customSymbols).toEqual([]);
  });

  it('setSnapshot updates snapshot and status', () => {
    const { default: useEtfStore } = require('./etfStore');
    const fake = { built_at: '2026-03-16T20:00:00Z', groups: {}, column_ranges: {} };
    act(() => useEtfStore.getState().setSnapshot(fake));
    expect(useEtfStore.getState().snapshot).toEqual(fake);
    expect(useEtfStore.getState().status).toBe('idle');
  });

  it('setProgress updates progress fields', () => {
    const { default: useEtfStore } = require('./etfStore');
    act(() => useEtfStore.getState().setProgress({ done: 5, total: 180, current: 'SPY' }));
    const { progress } = useEtfStore.getState();
    expect(progress.done).toBe(5);
    expect(progress.current).toBe('SPY');
  });
});
```

**Step 2: Run to verify failure**

```bash
cd frontend && npx vitest run src/stores/etfStore.test.js
```

Expected: module not found

**Step 3: Create `frontend/src/stores/etfStore.js`**

```js
import { create } from 'zustand';
import { API_BASE } from '../config';

const useEtfStore = create((set, get) => ({
  snapshot: null,
  status: 'idle',        // 'idle' | 'loading' | 'refreshing' | 'error'
  progress: { done: 0, total: 0, current: '' },
  customSymbols: [],

  setSnapshot: (snapshot) => set({ snapshot, status: 'idle' }),
  setProgress: (progress) => set({ progress }),
  setStatus: (status) => set({ status }),
  setCustomSymbols: (customSymbols) => set({ customSymbols }),

  fetchSnapshot: async () => {
    set({ status: 'loading' });
    try {
      const res = await fetch(`${API_BASE}/api/etf/snapshot`, { credentials: 'include' });
      if (!res.ok) throw new Error('Failed to fetch snapshot');
      const data = await res.json();
      set({ snapshot: data, status: 'idle' });
    } catch (err) {
      console.error('ETF snapshot error:', err);
      set({ status: 'error' });
    }
  },

  fetchCustomSymbols: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/etf/custom`, { credentials: 'include' });
      if (!res.ok) return;
      const data = await res.json();
      set({ customSymbols: data });
    } catch (err) {
      console.error('ETF custom symbols error:', err);
    }
  },

  addCustomSymbol: async (symbol) => {
    const res = await fetch(`${API_BASE}/api/etf/custom/${symbol.toUpperCase()}`, {
      method: 'POST',
      credentials: 'include',
    });
    if (res.ok) {
      await get().fetchCustomSymbols();
    }
    return res.ok;
  },

  removeCustomSymbol: async (symbol) => {
    const res = await fetch(`${API_BASE}/api/etf/custom/${symbol.toUpperCase()}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (res.ok) {
      await get().fetchCustomSymbols();
    }
    return res.ok;
  },

  startRefresh: async () => {
    set({ status: 'refreshing', progress: { done: 0, total: 0, current: '' } });
    try {
      const res = await fetch(`${API_BASE}/api/etf/refresh`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Refresh failed');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n').filter((l) => l.startsWith('data: '));
        for (const line of lines) {
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === 'progress' || event.type === 'error') {
              set({ progress: { done: event.done, total: event.total, current: event.symbol } });
            } else if (event.type === 'complete') {
              await get().fetchSnapshot();
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (err) {
      console.error('ETF refresh error:', err);
      set({ status: 'error' });
    }
  },
}));

export default useEtfStore;
```

**Step 4: Run tests**

```bash
cd frontend && npx vitest run src/stores/etfStore.test.js
```

Expected: 3 tests PASS

**Step 5: Commit**

```bash
git add frontend/src/stores/etfStore.js frontend/src/stores/etfStore.test.js
git commit -m "feat: add etfStore Zustand store with refresh SSE handling"
```

---

## Task 8: ETFDashboard page

**Files:**
- Create: `frontend/src/pages/ETFDashboard.jsx`
- Modify: `frontend/src/App.jsx`

**Step 1: Create `frontend/src/pages/ETFDashboard.jsx`**

```jsx
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../stores/authStore';
import useEtfStore from '../stores/etfStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { RefreshCw, Plus, X, TrendingUp, Settings, Compass, BarChart2 } from 'lucide-react';
import { API_BASE } from '../config';

// --- ABC Rating badge ---
function AbcBadge({ rating }) {
  if (!rating) return <span className="text-muted-foreground">—</span>;
  const colors = { A: 'bg-blue-500', B: 'bg-green-500', C: 'bg-amber-500' };
  return (
    <span className={`inline-flex items-center justify-center w-5 h-5 rounded-full text-white text-xs font-bold ${colors[rating] ?? 'bg-gray-500'}`}>
      {rating}
    </span>
  );
}

// --- Color-coded cell with background bar ---
function BarCell({ value, range, decimals = 2 }) {
  if (value == null) return <span className="text-muted-foreground text-xs">—</span>;
  const [min, max] = range ?? [-10, 10];
  const positive = value >= 0;
  const pct = Math.min(100, Math.abs(value) / Math.max(Math.abs(min), Math.abs(max)) * 100);
  return (
    <span className="relative inline-block min-w-[48px] text-right px-1">
      <span
        className={`absolute top-0 h-full rounded opacity-20 z-0 ${positive ? 'bg-green-500 left-0' : 'bg-red-500 right-0'}`}
        style={{ width: `${pct}%` }}
      />
      <span className={`relative z-10 font-medium ${positive ? 'text-green-500' : 'text-red-500'}`}>
        {value.toFixed(decimals)}%
      </span>
    </span>
  );
}

// --- RS sparkline SVG ---
function RsSparkline({ data }) {
  if (!data || data.length === 0) return <span className="text-muted-foreground text-xs">—</span>;
  const w = 80, h = 28;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  });
  const maxIdx = data.indexOf(Math.max(...data));
  return (
    <svg width={w} height={h} className="block">
      {data.map((v, i) => {
        const x = (i / (data.length - 1)) * w;
        const barH = Math.abs(((v - min) / range) * h);
        return (
          <rect
            key={i}
            x={x - 1.5}
            y={v >= 0 ? h / 2 - barH : h / 2}
            width={3}
            height={barH}
            fill={i === maxIdx ? '#4ade80' : '#9ca3af'}
            opacity={0.8}
          />
        );
      })}
    </svg>
  );
}

// --- Holdings popover ---
function HoldingsPopover({ symbol }) {
  const [open, setOpen] = useState(false);
  const [holdings, setHoldings] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    if (holdings !== null) { setOpen(true); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/etf/holdings/${symbol}`, { credentials: 'include' });
      const data = await res.json();
      setHoldings(data ?? []);
    } catch { setHoldings([]); }
    finally { setLoading(false); setOpen(true); }
  };

  return (
    <div className="relative inline-block">
      <button
        onClick={load}
        className="text-xs px-1.5 py-0.5 rounded bg-muted hover:bg-muted/80 text-muted-foreground font-mono"
      >
        H
      </button>
      {open && (
        <div
          className="absolute left-0 top-6 z-50 w-52 bg-popover border rounded shadow-lg p-2 text-xs"
          onMouseLeave={() => setOpen(false)}
        >
          <div className="font-semibold mb-1">{symbol} Top Holdings</div>
          {loading && <div className="text-muted-foreground">Loading…</div>}
          {holdings && holdings.length === 0 && <div className="text-muted-foreground">No data</div>}
          {holdings && holdings.map((h, i) => (
            <div key={i} className="flex justify-between py-0.5">
              <span>{h.symbol}</span>
              <span className="text-muted-foreground">{h.weight != null ? `${(h.weight * 100).toFixed(1)}%` : '—'}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// --- ETF table ---
const COLUMNS = [
  { key: 'ticker',        label: 'Ticker',    sortable: false },
  { key: 'abc',           label: 'Grade',     sortable: true  },
  { key: 'daily',         label: 'Daily',     sortable: true  },
  { key: 'intra',         label: 'Intra',     sortable: true  },
  { key: '5d',            label: '5D',        sortable: true  },
  { key: '20d',           label: '20D',       sortable: true  },
  { key: 'atr_pct',       label: 'ATR%',      sortable: true  },
  { key: 'dist_sma50_atr',label: 'ATRx',      sortable: true  },
  { key: 'rs',            label: 'VARS',      sortable: true  },
  { key: 'rrs_chart',     label: 'Chart',     sortable: false },
];

function ETFTable({ rows, ranges }) {
  const [sortKey, setSortKey] = useState('rs');
  const [sortDir, setSortDir] = useState('desc');

  const sorted = [...rows].sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    const abcOrder = { A: 0, B: 1, C: 2 };
    if (sortKey === 'abc') {
      return sortDir === 'asc'
        ? (abcOrder[av] ?? 3) - (abcOrder[bv] ?? 3)
        : (abcOrder[bv] ?? 3) - (abcOrder[av] ?? 3);
    }
    return sortDir === 'asc' ? av - bv : bv - av;
  });

  const toggleSort = (key) => {
    if (!COLUMNS.find(c => c.key === key)?.sortable) return;
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="bg-muted/50 text-muted-foreground">
            {COLUMNS.map(col => (
              <th
                key={col.key}
                onClick={() => toggleSort(col.key)}
                className={`px-2 py-1.5 text-left font-medium border-b border-border ${col.sortable ? 'cursor-pointer hover:text-foreground' : ''} ${sortKey === col.key ? 'text-foreground' : ''}`}
              >
                {col.label}
                {col.sortable && sortKey === col.key && (sortDir === 'asc' ? ' ↑' : ' ↓')}
              </th>
            ))}
            <th className="px-2 py-1.5 text-left font-medium border-b border-border">Lev</th>
            <th className="px-2 py-1.5 text-left font-medium border-b border-border">Hold</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr key={row.ticker} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
              <td className="px-2 py-1.5 font-mono font-semibold">{row.ticker}</td>
              <td className="px-2 py-1.5"><AbcBadge rating={row.abc} /></td>
              <td className="px-2 py-1.5"><BarCell value={row.daily} range={ranges?.daily} /></td>
              <td className="px-2 py-1.5"><BarCell value={row.intra} range={ranges?.intra} /></td>
              <td className="px-2 py-1.5"><BarCell value={row['5d']} range={ranges?.['5d']} /></td>
              <td className="px-2 py-1.5"><BarCell value={row['20d']} range={ranges?.['20d']} /></td>
              <td className="px-2 py-1.5 text-muted-foreground">{row.atr_pct != null ? `${row.atr_pct}%` : '—'}</td>
              <td className="px-2 py-1.5 text-muted-foreground">{row.dist_sma50_atr != null ? row.dist_sma50_atr.toFixed(1) : '—'}</td>
              <td className="px-2 py-1.5 text-muted-foreground">{row.rs != null ? Math.round(row.rs) : '—'}</td>
              <td className="px-2 py-1.5"><RsSparkline data={row.rrs_chart} /></td>
              <td className="px-2 py-1.5">
                <span className="text-green-500 text-xs">{(row.long ?? []).join(' ')}</span>
                {row.short?.length > 0 && <span className="text-red-400 text-xs ml-1">{row.short.join(' ')}</span>}
              </td>
              <td className="px-2 py-1.5"><HoldingsPopover symbol={row.ticker} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --- Main page ---
const GROUP_ORDER = ['Indices', 'S&P Style', 'Sel Sectors', 'EW Sectors', 'Industries', 'Countries', 'Custom'];

export default function ETFDashboard() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const { snapshot, status, progress, customSymbols, fetchSnapshot, fetchCustomSymbols, startRefresh, addCustomSymbol, removeCustomSymbol } = useEtfStore();

  const [activeGroup, setActiveGroup] = useState('Indices');
  const [newSymbol, setNewSymbol] = useState('');

  useEffect(() => {
    fetchSnapshot();
    fetchCustomSymbols();
  }, []);

  const groups = snapshot?.groups ?? {};
  const availableGroups = GROUP_ORDER.filter(g => groups[g]?.length > 0 || g === 'Custom');

  const handleAddSymbol = async () => {
    const sym = newSymbol.trim().toUpperCase();
    if (!sym) return;
    await addCustomSymbol(sym);
    setNewSymbol('');
  };

  const handleLogout = async () => { await logout(); navigate('/'); };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Nav */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
        <div className="flex items-center gap-4">
          <Link to="/watchlists" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"><TrendingUp className="h-4 w-4" /> Watchlists</Link>
          <Link to="/discover" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"><Compass className="h-4 w-4" /> Discover</Link>
          <span className="flex items-center gap-1.5 text-sm font-medium"><BarChart2 className="h-4 w-4" /> ETF Dashboard</span>
        </div>
        <div className="flex items-center gap-3">
          {snapshot?.built_at && (
            <span className="text-xs text-muted-foreground">
              Updated {new Date(snapshot.built_at).toLocaleTimeString()}
            </span>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={startRefresh}
            disabled={status === 'refreshing'}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${status === 'refreshing' ? 'animate-spin' : ''}`} />
            {status === 'refreshing' ? `${progress.done}/${progress.total}` : 'Refresh'}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 rounded-full p-0">
                <Avatar className="h-7 w-7"><AvatarFallback className="text-xs">{user?.email?.[0]?.toUpperCase()}</AvatarFallback></Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel className="text-xs">{user?.email}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/settings')}><Settings className="h-3.5 w-3.5 mr-2" /> Settings</DropdownMenuItem>
              <DropdownMenuItem onClick={handleLogout}>Sign Out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Progress bar */}
      {status === 'refreshing' && (
        <div className="h-1 bg-muted shrink-0">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: progress.total > 0 ? `${(progress.done / progress.total) * 100}%` : '0%' }}
          />
        </div>
      )}

      {/* Group tabs */}
      <div className="flex gap-1 px-4 pt-3 pb-0 border-b border-border shrink-0 overflow-x-auto">
        {availableGroups.map(g => (
          <button
            key={g}
            onClick={() => setActiveGroup(g)}
            className={`px-3 py-1.5 text-sm rounded-t font-medium whitespace-nowrap transition-colors ${activeGroup === g ? 'bg-background border border-b-background border-border text-foreground -mb-px' : 'text-muted-foreground hover:text-foreground'}`}
          >
            {g}
            {groups[g] && <span className="ml-1.5 text-xs text-muted-foreground">({groups[g].length})</span>}
          </button>
        ))}
      </div>

      {/* Table area */}
      <div className="flex-1 overflow-auto">
        {status === 'loading' && (
          <div className="p-4 space-y-2">
            {[...Array(8)].map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
          </div>
        )}

        {status !== 'loading' && !snapshot && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
            <BarChart2 className="h-12 w-12 opacity-30" />
            <p className="text-sm">No ETF data yet. Click <strong>Refresh</strong> to fetch ~180 ETFs.</p>
          </div>
        )}

        {snapshot && activeGroup !== 'Custom' && groups[activeGroup] && (
          <ETFTable
            rows={groups[activeGroup]}
            ranges={snapshot.column_ranges?.[activeGroup]}
          />
        )}

        {activeGroup === 'Custom' && (
          <div>
            {groups['Custom']?.length > 0 && (
              <ETFTable
                rows={groups['Custom']}
                ranges={snapshot?.column_ranges?.['Custom']}
              />
            )}
            <div className="p-4 border-t border-border">
              <p className="text-xs text-muted-foreground mb-2">Custom symbols are included in the next Refresh.</p>
              <div className="flex gap-2 mb-3">
                <Input
                  value={newSymbol}
                  onChange={e => setNewSymbol(e.target.value.toUpperCase())}
                  onKeyDown={e => e.key === 'Enter' && handleAddSymbol()}
                  placeholder="e.g. TQQQ"
                  className="h-8 w-32 font-mono text-sm"
                />
                <Button size="sm" onClick={handleAddSymbol} className="h-8">
                  <Plus className="h-3.5 w-3.5 mr-1" /> Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {customSymbols.map(sym => (
                  <Badge key={sym} variant="secondary" className="flex items-center gap-1 font-mono">
                    {sym}
                    <button onClick={() => removeCustomSymbol(sym)} className="ml-0.5 hover:text-destructive">
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Wire route into `frontend/src/App.jsx`**

Add import at top:
```js
import ETFDashboard from './pages/ETFDashboard';
```

Add route after `/discover`:
```jsx
<Route
  path="/etf"
  element={
    <ProtectedRoute>
      <ETFDashboard />
    </ProtectedRoute>
  }
/>
```

**Step 3: Add ETF nav link to WatchlistsNew and Discover pages**

In `frontend/src/pages/WatchlistsNew.jsx` and `frontend/src/pages/Discover.jsx`, add to the nav links:
```jsx
import { BarChart2 } from 'lucide-react';
// ...
<Link to="/etf" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
  <BarChart2 className="h-4 w-4" /> ETF
</Link>
```

**Step 4: Manual smoke test**

```bash
# Terminal 1
cd backend && SINGLE_USER_MODE=true uvicorn app.main:app --port 6900

# Terminal 2
cd frontend && npm run dev
```

Open http://localhost:5173, log in, navigate to `/etf`, verify:
- Page loads with empty state and Refresh button
- Click Refresh — progress bar fills as ETFs stream in
- After complete, tabs show and table renders
- Click "H" on a row — holdings popover appears
- Custom tab — add a symbol, verify it appears

**Step 5: Commit**

```bash
git add frontend/src/pages/ETFDashboard.jsx frontend/src/App.jsx frontend/src/pages/WatchlistsNew.jsx frontend/src/pages/Discover.jsx
git commit -m "feat: add ETFDashboard page with tabs, table, sparklines, holdings"
```

---

## Task 9: Final integration check and cleanup

**Step 1: Run all backend tests**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: all tests PASS (including existing tests + new ETF tests)

**Step 2: Check requirements are accurate**

```bash
cd backend && pip install -r requirements.txt
```

Expected: no errors

**Step 3: Verify yfinance not already in requirements via openbb**

yfinance is a separate package — it was explicitly added in Task 1.

**Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: ETF dashboard integration cleanup"
```

**Step 5: Update status doc**

In `docs/project/status.md`, add to "Latest Accomplishments":
```
- ✅ **ETF Dashboard** — New `/etf` page with ~180 preset ETFs across 6 categories
  - ABC Rating (EMA10/EMA20/SMA50 trend grade), ATR%, ATRx, 1M-VARS relative strength
  - RS sparkline charts (20-bar rolling relative strength vs SPY)
  - Leveraged ETF lookup per symbol, ETF holdings popover (lazy, 24h cache)
  - Manual refresh with SSE progress stream, yfinance data source
  - User-extensible custom ETF group (SQLite-persisted)
```

```bash
git add docs/project/status.md
git commit -m "docs: update status for ETF dashboard milestone"
```
