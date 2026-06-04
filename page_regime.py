"""
pages/page_regime.py
---------------------
Page 4 — Regime Analysis: High vs. Low Liquidity asset return comparison.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.charts        import (
    compute_regime_returns,
    chart_regime_avg_returns,
    chart_regime_timeline,
)
from modules.analytics     import regime_statistics
from modules.ui_components import (
    section_header, page_title, chart_container, info_box
)
from modules.config        import TICKERS, COLORS


def _pct(v):
    if pd.isna(v):
        return "N/A"
    color = "#00E676" if v >= 0 else "#FF1744"
    return f"<span style='color:{color};font-family:IBM Plex Mono,monospace'>{v:+.2%}</span>"


def render(net_liq: pd.Series, returns: pd.DataFrame) -> None:
    page_title(
        "Regime Analysis",
        "High vs. Low Liquidity — how assets perform in each environment"
    )

    high_df, low_df, regime = compute_regime_returns(net_liq, returns)

    # ── Regime timeline ────────────────────────────────────────────────────
    section_header("Net Liquidity — Regime Timeline")
    info_box(
        "Shaded areas mark High Liquidity regimes (Net Liquidity ≥ median). "
        "White/unshaded periods are Low Liquidity regimes."
    )
    common_idx = regime.index.intersection(net_liq.index)
    fig_timeline = chart_regime_timeline(regime.loc[common_idx], net_liq.loc[common_idx])
    chart_container(fig_timeline)

    # ── Regime counts ──────────────────────────────────────────────────────
    n_high = int(regime.sum())
    n_low  = int((~regime).sum())
    bg_card    = COLORS["bg_card"]
    border_clr = COLORS["border"]
    muted_clr  = COLORS["text_muted"]
    cyan_clr   = COLORS["accent_cyan"]
    red_clr    = COLORS["accent_red"]

    c1, c2, _ = st.columns([1, 1, 3])
    with c1:
        st.markdown(
            f"<div style='background:{bg_card};border:1px solid {border_clr};"
            f"border-radius:6px;padding:12px 16px;font-family:IBM Plex Mono,monospace'>"
            f"<div style='font-size:0.68rem;color:{muted_clr};letter-spacing:0.12em;"
            f"text-transform:uppercase;margin-bottom:4px'>High Liq Months</div>"
            f"<div style='font-size:1.4rem;color:{cyan_clr}'>{n_high}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div style='background:{bg_card};border:1px solid {border_clr};"
            f"border-radius:6px;padding:12px 16px;font-family:IBM Plex Mono,monospace'>"
            f"<div style='font-size:0.68rem;color:{muted_clr};letter-spacing:0.12em;"
            f"text-transform:uppercase;margin-bottom:4px'>Low Liq Months</div>"
            f"<div style='font-size:1.4rem;color:{red_clr}'>{n_low}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Bar chart ──────────────────────────────────────────────────────────
    section_header("Average Monthly Returns by Regime")
    fig_bar = chart_regime_avg_returns(high_df, low_df)
    chart_container(fig_bar)

    # ── Statistics table ───────────────────────────────────────────────────
    section_header("Regime Statistics Table")
    stats_df = regime_statistics(high_df, low_df)

    styled = stats_df.style.set_table_styles([
        {"selector": "thead th",
         "props": [("background", "#1A2340"), ("color", "#7986CB"),
                   ("font-family", "'IBM Plex Mono',monospace"),
                   ("font-size", "0.72rem"), ("text-transform", "uppercase"),
                   ("letter-spacing", "0.08em")]},
        {"selector": "tbody td",
         "props": [("font-family", "'IBM Plex Mono',monospace"),
                   ("font-size", "0.8rem"), ("background", "#141B2D"),
                   ("color", "#E8EAF6")]},
    ]).format({
        "High Liq Avg (Mo)": "{:+.3%}",
        "Low Liq Avg (Mo)":  "{:+.3%}",
        "Difference":        "{:+.3%}",
        "High Liq Hit Rate": "{:.1%}",
        "n (High)":          "{:.0f}",
        "n (Low)":           "{:.0f}",
    }).applymap(
        lambda v: "color:#00E676" if isinstance(v, float) and v >= 0
                  else "color:#FF1744" if isinstance(v, float) and v < 0 else "",
        subset=["High Liq Avg (Mo)", "Low Liq Avg (Mo)", "Difference"],
    )

    st.dataframe(styled, use_container_width=True)

    info_box(
        "Hit Rate = fraction of High Liquidity months where the asset posted a positive return. "
        "Difference = High Liq Avg − Low Liq Avg (positive = outperforms in high-liq environment)."
    )

    # ── Per-asset deep dive ────────────────────────────────────────────────
    section_header("Asset Deep Dive")
    ticker_opts = {v: k for k, v in TICKERS.items() if k in returns.columns}
    chosen_name   = st.selectbox("Select asset", list(ticker_opts.keys()), key="regime_ticker")
    chosen_ticker = ticker_opts[chosen_name]

    h_ret = high_df[chosen_ticker].dropna()
    l_ret = low_df[chosen_ticker].dropna()

    col_a, col_b, col_c, col_d = st.columns(4)
    def _kpi(col, label, val, is_pos: bool | None = None):
        _green  = COLORS["accent_green"]
        _red    = COLORS["accent_red"]
        _white  = COLORS["text_primary"]
        _bgc    = COLORS["bg_card"]
        _brd    = COLORS["border"]
        _mut    = COLORS["text_muted"]
        color   = (_green if is_pos is True else _red if is_pos is False else _white)
        col.markdown(
            f"<div style='background:{_bgc};border:1px solid {_brd};"
            f"border-radius:6px;padding:14px 16px;font-family:IBM Plex Mono,monospace'>"
            f"<div style='font-size:0.66rem;color:{_mut};letter-spacing:.12em;"
            f"text-transform:uppercase;margin-bottom:4px'>{label}</div>"
            f"<div style='font-size:1.2rem;color:{color}'>{val}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    _kpi(col_a, "Avg (High Liq)", f"{h_ret.mean():+.2%}", h_ret.mean() >= 0)
    _kpi(col_b, "Avg (Low Liq)",  f"{l_ret.mean():+.2%}", l_ret.mean() >= 0)
    _kpi(col_c, "Vol (High Liq)", f"{h_ret.std():.2%}")
    _kpi(col_d, "Vol (Low Liq)",  f"{l_ret.std():.2%}")
