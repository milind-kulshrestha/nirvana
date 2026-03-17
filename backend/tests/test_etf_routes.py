"""Tests for ETF API routes."""
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.routes.auth import get_current_user
from app.routes import etf as etf_routes


def _make_app(db_session_factory):
    """Build a minimal FastAPI app with just the ETF router."""
    test_app = FastAPI()

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    from app.models.user import User
    fake_user = User(id=1, email="test@test.com", password_hash="x")

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_user] = lambda: fake_user
    test_app.include_router(etf_routes.router, prefix="/api/etf")
    return test_app


@pytest.fixture(scope="module")
def client():
    # Import all models so SQLAlchemy registers them with Base.metadata before create_all
    import app.models  # noqa: F401 — registers all ORM models on Base.metadata
    # StaticPool forces all connections to share the same in-memory DB instance
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    test_app = _make_app(Session)
    return TestClient(test_app)


def test_snapshot_empty(client):
    with patch("app.routes.etf.get_etf_snapshot", return_value=None):
        resp = client.get("/api/etf/snapshot")
    assert resp.status_code == 200
    assert resp.json() is None


def test_snapshot_returns_data(client):
    fake = {
        "built_at": "2026-03-16T20:00:00Z",
        "groups": {"Indices": [{"ticker": "SPY", "abc": "A"}]},
        "column_ranges": {},
    }
    with patch("app.routes.etf.get_etf_snapshot", return_value=fake):
        resp = client.get("/api/etf/snapshot")
    assert resp.status_code == 200
    assert resp.json()["groups"]["Indices"][0]["ticker"] == "SPY"


def test_get_custom_symbols_empty(client):
    resp = client.get("/api/etf/custom")
    assert resp.status_code == 200
    assert resp.json() == []


def test_add_and_remove_custom_symbol(client):
    resp = client.post("/api/etf/custom/TQQQ")
    assert resp.status_code == 201
    assert resp.json()["symbol"] == "TQQQ"

    resp = client.get("/api/etf/custom")
    assert "TQQQ" in resp.json()

    resp = client.delete("/api/etf/custom/TQQQ")
    assert resp.status_code == 200

    resp = client.get("/api/etf/custom")
    assert "TQQQ" not in resp.json()


def test_holdings_cached(client):
    holdings = [{"symbol": "AAPL", "weight": 0.07}]
    with patch("app.routes.etf.get_etf_holdings", return_value=holdings):
        resp = client.get("/api/etf/holdings/SPY")
    assert resp.status_code == 200
    assert resp.json()[0]["symbol"] == "AAPL"


def test_holdings_fetches_live_on_miss(client):
    with patch("app.routes.etf.get_etf_holdings", return_value=None), \
         patch("app.routes.etf.fetch_etf_holdings_sync", return_value=[]):
        resp = client.get("/api/etf/holdings/UNKNOWN")
    assert resp.status_code == 200
    assert resp.json() == []
