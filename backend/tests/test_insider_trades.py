"""Tests for insider trading data functions."""
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import duckdb


@pytest.fixture
def mock_cache(monkeypatch):
    """In-memory DuckDB for cache isolation."""
    conn = duckdb.connect(":memory:")
    monkeypatch.setattr("app.lib.market_cache._connection", conn)
    from app.lib import market_cache
    market_cache._init_tables(conn)
    return conn


def _make_openbb_result(trades_data):
    """Create a mock OpenBB response with insider trading results."""
    mock_results = []
    for t in trades_data:
        r = MagicMock()
        r.filing_date = t.get("filing_date")
        r.transaction_date = t.get("transaction_date")
        r.owner_name = t.get("owner_name")
        r.owner_title = t.get("owner_title")
        r.transaction_type = t.get("transaction_type")
        r.acquisition_or_disposition = t.get("acquisition_or_disposition")
        r.securities_transacted = t.get("securities_transacted")
        r.price = t.get("price")
        r.value = t.get("value")
        mock_results.append(r)
    mock_resp = MagicMock()
    mock_resp.results = mock_results
    return mock_resp


class TestGetInsiderTrading:
    def test_returns_normalized_trades(self, mock_cache):
        from app.lib.openbb import get_insider_trading

        mock_data = _make_openbb_result([
            {
                "filing_date": "2026-03-15",
                "transaction_date": "2026-03-14",
                "owner_name": "Jane Doe",
                "owner_title": "CEO",
                "transaction_type": "P-Purchase",
                "acquisition_or_disposition": "A",
                "securities_transacted": 5000.0,
                "price": 150.0,
                "value": 750000.0,
            },
            {
                "filing_date": "2026-03-10",
                "transaction_date": "2026-03-09",
                "owner_name": "John Smith",
                "owner_title": "CFO",
                "transaction_type": "S-Sale",
                "acquisition_or_disposition": "D",
                "securities_transacted": 10000.0,
                "price": 148.0,
                "value": 1480000.0,
            },
        ])

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.return_value = mock_data
            result = get_insider_trading("AAPL")

        assert len(result) == 2
        assert result[0]["insider_name"] == "Jane Doe"
        assert result[0]["insider_title"] == "CEO"
        assert result[0]["transaction_type"] == "buy"
        assert result[0]["shares"] == 5000
        assert result[0]["value"] == 750000.0
        assert result[1]["transaction_type"] == "sell"

    def test_caches_result(self, mock_cache):
        from app.lib.openbb import get_insider_trading

        mock_data = _make_openbb_result([{
            "filing_date": "2026-03-15",
            "transaction_date": "2026-03-14",
            "owner_name": "Jane Doe",
            "owner_title": "CEO",
            "transaction_type": "P-Purchase",
            "acquisition_or_disposition": "A",
            "securities_transacted": 5000.0,
            "price": 150.0,
            "value": 750000.0,
        }])

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.return_value = mock_data
            get_insider_trading("AAPL")
            result = get_insider_trading("AAPL")

        assert mock_obb.equity.ownership.insider_trading.call_count == 1
        assert len(result) == 1

    def test_empty_results(self, mock_cache):
        from app.lib.openbb import get_insider_trading

        mock_resp = MagicMock()
        mock_resp.results = []

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.return_value = mock_resp
            result = get_insider_trading("AAPL")

        assert result == []

    def test_computes_value_when_missing(self, mock_cache):
        from app.lib.openbb import get_insider_trading

        mock_data = _make_openbb_result([{
            "filing_date": "2026-03-15",
            "transaction_date": "2026-03-14",
            "owner_name": "Alice",
            "owner_title": "VP",
            "transaction_type": "P-Purchase",
            "acquisition_or_disposition": "A",
            "securities_transacted": 100.0,
            "price": 50.0,
            "value": None,
        }])

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.return_value = mock_data
            result = get_insider_trading("TSLA")

        assert result[0]["value"] == 5000.0

    def test_api_failure_returns_empty(self, mock_cache):
        from app.lib.openbb import get_insider_trading

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.side_effect = Exception("API down")
            result = get_insider_trading("AAPL")

        assert result == []

    def test_limits_to_20_trades(self, mock_cache):
        from app.lib.openbb import get_insider_trading

        trades = []
        for i in range(30):
            trades.append({
                "filing_date": f"2026-01-{i+1:02d}",
                "transaction_date": f"2026-01-{i+1:02d}",
                "owner_name": f"Person {i}",
                "owner_title": "VP",
                "transaction_type": "P-Purchase",
                "acquisition_or_disposition": "A",
                "securities_transacted": 100.0,
                "price": 10.0,
                "value": 1000.0,
            })
        mock_data = _make_openbb_result(trades)

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.return_value = mock_data
            result = get_insider_trading("AAPL")

        assert len(result) == 20


from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client(mock_cache):
    """Test client with minimal FastAPI app containing only securities router."""
    from app.routes.securities import router
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/securities")
    return TestClient(test_app)


class TestInsiderTradesEndpoint:
    def test_returns_trades_with_summary(self, client):
        mock_trades = [
            {
                "filing_date": "2026-03-15",
                "transaction_date": "2026-03-14",
                "owner_name": "Jane Doe",
                "owner_title": "CEO",
                "transaction_type": "P-Purchase",
                "acquisition_or_disposition": "A",
                "securities_transacted": 5000.0,
                "price": 150.0,
                "value": 750000.0,
            },
            {
                "filing_date": "2026-02-10",
                "transaction_date": "2026-02-09",
                "owner_name": "John Smith",
                "owner_title": "CFO",
                "transaction_type": "S-Sale",
                "acquisition_or_disposition": "D",
                "securities_transacted": 10000.0,
                "price": 148.0,
                "value": 1480000.0,
            },
        ]
        mock_data = _make_openbb_result(mock_trades)

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.return_value = mock_data
            response = client.get("/api/securities/AAPL/insider-trades")

        assert response.status_code == 200
        body = response.json()
        assert "summary" in body
        assert "trades" in body
        assert body["summary"]["total_buys"] == 1
        assert body["summary"]["total_sells"] == 1
        assert body["summary"]["buy_value"] == 750000.0
        assert body["summary"]["sell_value"] == 1480000.0
        assert body["summary"]["net_value"] == 750000.0 - 1480000.0
        assert len(body["trades"]) == 2

    def test_empty_insider_trades(self, client):
        mock_resp = MagicMock()
        mock_resp.results = []

        with patch("app.lib.openbb.obb") as mock_obb:
            mock_obb.equity.ownership.insider_trading.return_value = mock_resp
            response = client.get("/api/securities/AAPL/insider-trades")

        assert response.status_code == 200
        body = response.json()
        assert body["summary"]["total_buys"] == 0
        assert body["summary"]["total_sells"] == 0
        assert body["trades"] == []
