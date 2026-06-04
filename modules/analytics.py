"""
analytics.py
------------
Pure-Python / NumPy / Pandas statistical utilities.
No Streamlit or Plotly imports here — keeps analytics logic portable.

Extension points
----------------
- Add Granger causality tests (statsmodels).
- Add VAR model fitting and impulse-response functions.
- Add rolling beta / alpha calculations.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from modules.config import TICKERS, LAG_HORIZONS


def liquidity_summary(net_liq: pd.Series) -> dict:
    """
    Compute key headline statistics for Net Liquidity.

    Returns a dict with keys:
        current, change_1m, change_3m, change_6m, change_1m_pct,
        change_3m_pct, change_6m_pct, yoy_pct, all_time_high, all_time_low
    """
    s = net_liq.dropna()
    if len(s) < 2:
        return {}

    current = s.iloc[-1]

    def _chg(n: int) -> tuple[float, float]:
        if len(s) > n:
            prev = s.iloc[-1 - n]
            return current - prev, (current - prev) / abs(prev) if prev != 0 else np.nan
        return np.nan, np.nan

    c1, p1   = _chg(1)
    c3, p3   = _chg(3)
    c6, p6   = _chg(6)
    c12, p12 = _chg(12)

    return {
        "current":        current,
        "change_1m":      c1,   "change_1m_pct":  p1,
        "change_3m":      c3,   "change_3m_pct":  p3,
        "change_6m":      c6,   "change_6m_pct":  p6,
        "change_yoy":     c12,  "change_yoy_pct": p12,
        "all_time_high":  s.max(),
        "all_time_low":   s.min(),
        "median":         s.median(),
        "pct_of_ath":     current / s.max(),
    }


def asset_performance_table(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a summary table with columns:
        MTD, 3M, 6M, 1Y, Max Drawdown, Sharpe (annualised), Vol (ann.)
    """
    cols = [t for t in TICKERS if t in returns.columns]
    rows = []
    for ticker in cols:
        r = returns[ticker].dropna()
        if r.empty:
            continue

        def _ret(n: int) -> float:
            if len(r) >= n:
                return (1 + r.iloc[-n:]).prod() - 1
            return np.nan

        ann_vol   = r.std() * np.sqrt(12)
        ann_ret   = r.mean() * 12
        sharpe    = ann_ret / ann_vol if ann_vol > 0 else np.nan

        # Max drawdown on cumulative returns
        cum = (1 + r).cumprod()
        drawdown = (cum / cum.cummax() - 1).min()

        rows.append({
            "Asset":      TICKERS[ticker],
            "1M":         _ret(1),
            "3M":         _ret(3),
            "6M":         _ret(6),
            "1Y":         _ret(12),
            "Ann. Vol":   ann_vol,
            "Sharpe":     sharpe,
            "Max DD":     drawdown,
        })

    df = pd.DataFrame(rows).set_index("Asset")
    return df


def rolling_correlation(
    net_liq: pd.Series,
    returns: pd.DataFrame,
    window: int = 12,
) -> pd.DataFrame:
    """
    Rolling N-month Pearson correlation between Net Liquidity change
    and each asset's return.
    """
    cols    = [t for t in TICKERS if t in returns.columns]
    liq_chg = net_liq.pct_change().dropna()

    result = {}
    for ticker in cols:
        common = pd.concat([liq_chg, returns[ticker]], axis=1).dropna()
        common.columns = ["liq", ticker]
        result[TICKERS[ticker]] = common["liq"].rolling(window).corr(common[ticker])

    return pd.DataFrame(result)


def regime_statistics(high_df: pd.DataFrame, low_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a formatted comparison table:
        Asset | High Liq Avg | Low Liq Avg | Difference | Hit Rate (High>Low)
    """
    cols = [t for t in TICKERS if t in high_df.columns]
    rows = []
    for ticker in cols:
        h_mean = high_df[ticker].mean()
        l_mean = low_df[ticker].mean()
        diff   = h_mean - l_mean
        # Hit-rate: fraction of High-Liq months with positive returns
        hit    = (high_df[ticker] > 0).mean()
        rows.append({
            "Asset":              TICKERS[ticker],
            "High Liq Avg (Mo)":  h_mean,
            "Low Liq Avg (Mo)":   l_mean,
            "Difference":         diff,
            "High Liq Hit Rate":  hit,
            "n (High)":           len(high_df[ticker].dropna()),
            "n (Low)":            len(low_df[ticker].dropna()),
        })

    return pd.DataFrame(rows).set_index("Asset")
