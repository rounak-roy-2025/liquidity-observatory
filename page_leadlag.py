"""
pages/page_leadlag.py
----------------------
Page 3 — Lead-Lag Analysis: correlation between Net Liquidity change
         and forward asset returns at 1M, 3M, 6M horizons.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.charts        import (
    compute_lead_lag_correlations,
    chart_lead_lag_heatmap,
    chart_lead_lag_scatter,
)
from modules.ui_components import (
    section_header, page_title, chart_container, info_box
)
from modules.config        import TICKERS, LAG_HORIZONS, COLORS


def render(net_liq: pd.Series, returns: pd.DataFrame) -> None:
    page_title(
        "Lead-Lag Analysis",
        "Does Net Liquidity predict future asset returns?"
    )

    # ── Compute correlations ───────────────────────────────────────────────
    corr_df = compute_lead_lag_correlations(net_liq, returns)

    # ── Heatmap ───────────────────────────────────────────────────────────
    section_header("Correlation Heatmap · Liquidity Change vs. Forward Returns")
    info_box(
        "Each cell shows the Pearson correlation between the monthly percentage "
        "change in Net Liquidity and the asset's return N months later. "
        "Green = positive lead correlation; red = negative."
    )
    fig_heatmap = chart_lead_lag_heatmap(corr_df)
    chart_container(fig_heatmap)

    # ── Correlation table ─────────────────────────────────────────────────
    section_header("Correlation Table")
    styled = corr_df.style.set_table_styles([
        {"selector": "thead th",
         "props": [("background", "#1A2340"), ("color", "#7986CB"),
                   ("font-family", "'IBM Plex Mono',monospace"),
                   ("font-size", "0.72rem"), ("text-transform", "uppercase")]},
        {"selector": "tbody td",
         "props": [("font-family", "'IBM Plex Mono',monospace"),
                   ("font-size", "0.82rem"), ("background", "#141B2D"),
                   ("color", "#E8EAF6")]},
    ]).format("{:.3f}").background_gradient(
        cmap="RdYlGn", vmin=-1, vmax=1, axis=None
    )
    st.dataframe(styled, use_container_width=True)

    # ── Scatter plot drill-down ────────────────────────────────────────────
    section_header("Scatter — Drill Down")
    col1, col2 = st.columns(2)
    with col1:
        ticker_opts = {v: k for k, v in TICKERS.items() if k in returns.columns}
        chosen_name = st.selectbox(
            "Asset", options=list(ticker_opts.keys()), key="ll_ticker"
        )
        chosen_ticker = ticker_opts[chosen_name]
    with col2:
        chosen_horizon = st.selectbox(
            "Forward Horizon",
            options=LAG_HORIZONS,
            format_func=lambda x: f"{x} Month{'s' if x > 1 else ''}",
            key="ll_horizon",
        )

    fig_scatter = chart_lead_lag_scatter(net_liq, returns, chosen_ticker, chosen_horizon)
    chart_container(fig_scatter)

    corr_val = corr_df.loc[f"{chosen_horizon}M Forward", TICKERS[chosen_ticker]]
    sign_str = "positive" if corr_val >= 0 else "negative"
    strength = "strong" if abs(corr_val) > 0.4 else "moderate" if abs(corr_val) > 0.2 else "weak"

    st.markdown(
        f"<div style='font-family: IBM Plex Mono, monospace; font-size:0.8rem; "
        f"color: {COLORS['text_muted']}; margin-top:6px;'>"
        f"Correlation: <span style='color:{COLORS['text_primary']}'>{corr_val:.3f}</span> "
        f"— {strength} {sign_str} lead relationship over {chosen_horizon}-month horizon."
        f"</div>",
        unsafe_allow_html=True,
    )
