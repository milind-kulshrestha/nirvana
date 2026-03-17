"""Tests for ETF DuckDB cache functions."""
import json
import pytest
from datetime import datetime, timezone
import duckdb


@pytest.fixture
def mock_conn(monkeypatch):
    conn = duckdb.connect(":memory:")
    monkeypatch.setattr("app.lib.market_cache._connection", conn)
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
