"""
pages/page_assets.py
---------------------
Page 2 — Asset Performance: monthly returns, cumulative fan, correlation matrix.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.analytics     import asset_performance_table
from modules.charts        import (
    chart_asset_performance,
    chart_monthly_returns_bar,
    chart_correlation_matrix,
)
from modules.ui_components import (
    section_header, page_title, chart_container, styled_table, info_box
)
from modules.config import TICKERS


_PCT_COLS = ["1M", "3M", "6M", "1Y", "Ann. Vol", "Max DD"]
_FLT_COLS = ["Sharpe"]


def render(prices: pd.DataFrame, returns: pd.DataFrame) -> None:
    page_title(
        "Asset Performance",
        "Monthly & cumulative returns · Correlations"
    )

    # ── Lookback selector ─────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    col_ctrl, _ = st.columns([2, 5])
    with col_ctrl:
        lookback = st.selectbox(
            "Lookback window",
            options=[12, 24, 36, 60],
            format_func=lambda x: f"{x} months",
            index=1,
            key="asset_lookback",
        )

    # ── Performance summary table ──────────────────────────────────────────
    section_header("Performance Summary")
    perf_df = asset_performance_table(returns)

    styled = perf_df.style.set_table_styles([
        {"selector": "thead th",
         "props": [("background", "#1A2340"), ("color", "#7986CB"),
                   ("font-family", "'IBM Plex Mono',monospace"), ("font-size", "0.72rem"),
                   ("text-transform", "uppercase"), ("letter-spacing", "0.08em")]},
        {"selector": "tbody td",
         "props": [("font-family", "'IBM Plex Mono',monospace"), ("font-size", "0.8rem"),
                   ("background", "#141B2D"), ("color", "#E8EAF6")]},
    ]).format({
        "1M":      "{:+.2%}",
        "3M":      "{:+.2%}",
        "6M":      "{:+.2%}",
        "1Y":      "{:+.2%}",
        "Ann. Vol": "{:.2%}",
        "Sharpe":  "{:.2f}",
        "Max DD":  "{:+.2%}",
    }).applymap(
        lambda v: "color: #00E676" if isinstance(v, float) and v >= 0
                  else "color: #FF1744" if isinstance(v, float) and v < 0 else "",
        subset=["1M", "3M", "6M", "1Y", "Max DD"],
    )
    st.dataframe(styled, use_container_width=True)

    # ── Cumulative return chart ────────────────────────────────────────────
    section_header("Cumulative Returns")
    fig_cum = chart_asset_performance(returns, lookback_months=lookback)
    chart_container(fig_cum)

    # ── Monthly returns bar ────────────────────────────────────────────────
    section_header("Monthly Returns — Last 12 Months")
    fig_bar = chart_monthly_returns_bar(returns, lookback_months=12)
    chart_container(fig_bar)

    # ── Correlation matrix ─────────────────────────────────────────────────
    section_header("Return Correlation Matrix")
    info_box(
        f"Pearson pairwise correlations computed over the full available history "
        f"({len(returns)} months). Green = positive, red = negative."
    )
    fig_corr = chart_correlation_matrix(returns)
    chart_container(fig_corr)

    # ── Price data expander ────────────────────────────────────────────────
    with st.expander("▸  Show monthly closing prices", expanded=False):
        disp = prices.copy()
        disp.index = disp.index.strftime("%Y-%m")
        disp.columns = [TICKERS.get(c, c) for c in disp.columns]
        st.dataframe(
            disp.tail(36).style.format("${:,.2f}"),
            use_container_width=True,
        )
