"""
data_loader.py
--------------
Fetches and caches data from FRED and Yahoo Finance.
All heavy I/O lives here; other modules work with clean DataFrames.

Extension points
----------------
- Add ECB / BOJ / PBOC series by extending `get_fred_data()`.
- Add more tickers by updating TICKERS in config.py.
- Replace or augment caching by swapping the @st.cache_data decorator.
"""

from __future__ import annotations

import datetime
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False

from modules.config import (
    FRED_API_KEY, FRED_SERIES, TICKERS,
    HISTORY_YEARS, CACHE_TTL_SECONDS,
    LIQUIDITY_POSITIVE_COMPONENTS, LIQUIDITY_NEGATIVE_COMPONENTS,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _start_date() -> str:
    start = datetime.date.today() - datetime.timedelta(days=365 * HISTORY_YEARS)
    return start.strftime("%Y-%m-%d")


def _to_monthly(series: pd.Series) -> pd.Series:
    """Resample a series to month-end frequency, forward-filling gaps."""
    return (
        series
        .resample("ME")
        .last()
        .ffill()
    )


# ── FRED ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_fred_data() -> dict[str, pd.Series]:
    """
    Returns a dict of monthly FRED series keyed by their series ID.

    Extend here to add ECB (via ECB SDMX API), BOJ, or PBOC data.
    """
    if not FRED_AVAILABLE:
        raise ImportError("fredapi not installed. Run: pip install fredapi")
    if not FRED_API_KEY:
        raise ValueError(
            "FRED_API_KEY is not set. "
            "Add it to your .env file or Streamlit secrets."
        )

    fred = Fred(api_key=FRED_API_KEY)
    start = _start_date()
    result: dict[str, pd.Series] = {}

    for series_id in FRED_SERIES:
        raw = fred.get_series(series_id, observation_start=start)
        raw.index = pd.to_datetime(raw.index)
        result[series_id] = _to_monthly(raw)

    return result


# ── Yahoo Finance ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_price_data() -> pd.DataFrame:
    """
    Returns a DataFrame of monthly adjusted-close prices for all tickers.
    Columns are ticker symbols; index is month-end dates.
    """
    start = _start_date()
    raw = yf.download(
        list(TICKERS.keys()),
        start=start,
        auto_adjust=True,
        progress=False,
        threads=True,
    )

    # Handle both single and multi-ticker download shapes
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]].rename(columns={"Close": list(TICKERS.keys())[0]})

    prices.index = pd.to_datetime(prices.index)
    monthly = prices.resample("ME").last().ffill()
    return monthly


# ── Derived: Net Liquidity ────────────────────────────────────────────────────

def compute_net_liquidity(fred_data: dict[str, pd.Series]) -> pd.Series:
    """
    Net Liquidity = WALCL  -  RRPONTSYD  -  WTREGEN

    All components are forward-filled and aligned on a common monthly index
    before subtraction. Values are in billions of USD (as reported by FRED).
    """
    # Align all series to a common index
    df = pd.DataFrame(fred_data)
    df = df.ffill().dropna()

    liquidity = pd.Series(0.0, index=df.index, name="Net_Liquidity")
    for col in LIQUIDITY_POSITIVE_COMPONENTS:
        if col in df.columns:
            liquidity += df[col]
    for col in LIQUIDITY_NEGATIVE_COMPONENTS:
        if col in df.columns:
            liquidity -= df[col]

    return liquidity


# ── Derived: Monthly Returns ──────────────────────────────────────────────────

def compute_monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Percentage monthly returns for each ticker."""
    return prices.pct_change().dropna()


# ── Master Load ───────────────────────────────────────────────────────────────

def load_all() -> tuple[pd.Series, pd.DataFrame, pd.DataFrame, dict[str, pd.Series]]:
    """
    Convenience wrapper that loads everything in one call.

    Returns
    -------
    net_liquidity   : monthly Net Liquidity series
    prices          : monthly adjusted-close prices
    returns         : monthly pct-change returns
    fred_components : raw FRED series dict
    """
    fred_data   = get_fred_data()
    prices      = get_price_data()
    net_liq     = compute_net_liquidity(fred_data)
    returns     = compute_monthly_returns(prices)
    return net_liq, prices, returns, fred_data
