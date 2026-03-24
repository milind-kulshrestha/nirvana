"""Tests for insider trading data functions (SEC EDGAR source)."""
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


# Sample Form 4 XML for testing
SAMPLE_FORM4_XML = """<?xml version="1.0"?>
<ownershipDocument>
  <issuer>
    <issuerCik>0000320193</issuerCik>
    <issuerName>Apple Inc.</issuerName>
    <issuerTradingSymbol>AAPL</issuerTradingSymbol>
  </issuer>
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerName>Jane Doe</rptOwnerName>
    </reportingOwnerId>
    <reportingOwnerRelationship>
      <isOfficer>1</isOfficer>
      <officerTitle>CEO</officerTitle>
    </reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionDate><value>2026-03-14</value></transactionDate>
      <transactionCoding><transactionCode>P</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>5000</value></transactionShares>
        <transactionPricePerShare><value>150.00</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""

SAMPLE_FORM4_SELL_XML = """<?xml version="1.0"?>
<ownershipDocument>
  <issuer>
    <issuerCik>0000320193</issuerCik>
    <issuerName>Apple Inc.</issuerName>
    <issuerTradingSymbol>AAPL</issuerTradingSymbol>
  </issuer>
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerName>John Smith</rptOwnerName>
    </reportingOwnerId>
    <reportingOwnerRelationship>
      <isOfficer>1</isOfficer>
      <officerTitle>CFO</officerTitle>
    </reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionDate><value>2026-03-09</value></transactionDate>
      <transactionCoding><transactionCode>S</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>10000</value></transactionShares>
        <transactionPricePerShare><value>148.00</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""

# RSU vesting (M code) — should be filtered out
SAMPLE_FORM4_RSU_XML = """<?xml version="1.0"?>
<ownershipDocument>
  <reportingOwner>
    <reportingOwnerId><rptOwnerName>RSU Person</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship><officerTitle>VP</officerTitle></reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionDate><value>2026-03-15</value></transactionDate>
      <transactionCoding><transactionCode>M</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>1000</value></transactionShares>
        <transactionPricePerShare><value>0</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""

# Mock SEC EDGAR submissions response
MOCK_SUBMISSIONS = {
    "filings": {
        "recent": {
            "form": ["4", "4", "4", "10-K"],
            "filingDate": ["2026-03-15", "2026-03-10", "2026-03-05", "2026-02-01"],
            "accessionNumber": [
                "0001-26-000001", "0002-26-000002", "0003-26-000003", "0004-26-000004"
            ],
            "primaryDocument": [
                "xslF345X05/form4.xml", "form4_sell.xml", "xslF345X05/form4_rsu.xml", "10k.htm"
            ],
        }
    }
}

MOCK_TICKERS = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
}


def _mock_httpx_get(url, **kwargs):
    """Mock httpx.get responses for SEC EDGAR URLs."""
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()

    if "company_tickers.json" in url:
        resp.json.return_value = MOCK_TICKERS
    elif "submissions/CIK" in url:
        resp.json.return_value = MOCK_SUBMISSIONS
    elif "000126000001/form4.xml" in url:
        resp.text = SAMPLE_FORM4_XML
    elif "000226000002/form4_sell.xml" in url:
        resp.text = SAMPLE_FORM4_SELL_XML
    elif "000326000003/form4_rsu.xml" in url:
        resp.text = SAMPLE_FORM4_RSU_XML
    else:
        resp.raise_for_status.side_effect = Exception(f"Unexpected URL: {url}")

    return resp


class TestParseForm4Xml:
    def test_parses_purchase(self):
        from app.lib.openbb import _parse_form4_xml
        trades = _parse_form4_xml(SAMPLE_FORM4_XML, "2026-03-15")
        assert len(trades) == 1
        t = trades[0]
        assert t["insider_name"] == "Jane Doe"
        assert t["insider_title"] == "CEO"
        assert t["transaction_type"] == "buy"
        assert t["shares"] == 5000
        assert t["value"] == 750000.0
        assert t["date"] == "2026-03-14"

    def test_parses_sale(self):
        from app.lib.openbb import _parse_form4_xml
        trades = _parse_form4_xml(SAMPLE_FORM4_SELL_XML, "2026-03-10")
        assert len(trades) == 1
        t = trades[0]
        assert t["insider_name"] == "John Smith"
        assert t["transaction_type"] == "sell"
        assert t["shares"] == 10000
        assert t["value"] == 1480000.0

    def test_filters_non_buy_sell(self):
        from app.lib.openbb import _parse_form4_xml
        trades = _parse_form4_xml(SAMPLE_FORM4_RSU_XML, "2026-03-05")
        assert len(trades) == 0  # M (exercise) transactions are filtered out


class TestGetInsiderTrading:
    def test_returns_normalized_trades(self, mock_cache):
        from app.lib.openbb import get_insider_trading, _CIK_CACHE
        _CIK_CACHE.clear()

        with patch("app.lib.openbb.httpx.get", side_effect=_mock_httpx_get):
            result = get_insider_trading("AAPL")

        # Should have 2 trades (buy + sell), RSU filtered out
        assert len(result) == 2
        assert result[0]["insider_name"] == "Jane Doe"
        assert result[0]["transaction_type"] == "buy"
        assert result[0]["shares"] == 5000
        assert result[0]["value"] == 750000.0
        assert result[1]["insider_name"] == "John Smith"
        assert result[1]["transaction_type"] == "sell"

    def test_caches_result(self, mock_cache):
        from app.lib.openbb import get_insider_trading, _CIK_CACHE
        _CIK_CACHE.clear()

        with patch("app.lib.openbb.httpx.get", side_effect=_mock_httpx_get) as mock_get:
            get_insider_trading("AAPL")
            call_count_first = mock_get.call_count
            result = get_insider_trading("AAPL")

        # Second call should not make any HTTP requests (cache hit)
        assert mock_get.call_count == call_count_first
        assert len(result) == 2

    def test_unknown_symbol_returns_empty(self, mock_cache):
        from app.lib.openbb import get_insider_trading, _CIK_CACHE
        _CIK_CACHE.clear()

        with patch("app.lib.openbb.httpx.get", side_effect=_mock_httpx_get):
            result = get_insider_trading("ZZZZZ")

        assert result == []

    def test_api_failure_returns_empty(self, mock_cache):
        from app.lib.openbb import get_insider_trading, _CIK_CACHE
        _CIK_CACHE.clear()

        with patch("app.lib.openbb.httpx.get", side_effect=Exception("network error")):
            result = get_insider_trading("AAPL")

        assert result == []


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
        from app.lib.openbb import _CIK_CACHE
        _CIK_CACHE.clear()

        with patch("app.lib.openbb.httpx.get", side_effect=_mock_httpx_get):
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
        from app.lib.openbb import _CIK_CACHE
        _CIK_CACHE.clear()

        with patch("app.lib.openbb.httpx.get", side_effect=_mock_httpx_get):
            response = client.get("/api/securities/ZZZZZ/insider-trades")

        assert response.status_code == 200
        body = response.json()
        assert body["summary"]["total_buys"] == 0
        assert body["summary"]["total_sells"] == 0
        assert body["trades"] == []
