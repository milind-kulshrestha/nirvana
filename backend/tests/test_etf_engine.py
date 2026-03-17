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
