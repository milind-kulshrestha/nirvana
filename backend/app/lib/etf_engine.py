"""
ETF data engine — fetches metrics from Yahoo Finance and computes
technical indicators (ABC Rating, ATR, ATRx, VARS/RRS).
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
        # Normalize DatetimeIndex to date precision so microsecond differences don't prevent merging
        stock_cols = stock_data[["High", "Low", "Close"]].copy()
        spy_cols   = spy_data[["High", "Low", "Close"]].copy()
        if hasattr(stock_cols.index, "normalize"):
            stock_cols.index = stock_cols.index.normalize()
        if hasattr(spy_cols.index, "normalize"):
            spy_cols.index = spy_cols.index.normalize()
        merged = pd.merge(
            stock_cols,
            spy_cols,
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
