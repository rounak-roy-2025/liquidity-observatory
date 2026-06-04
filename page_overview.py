"""
pages/page_overview.py
-----------------------
Page 1 — Overview: Net Liquidity headline KPIs + interactive time-series.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.analytics     import liquidity_summary
from modules.charts        import chart_net_liquidity
from modules.ui_components import (
    kpi_card, section_header, page_title, chart_container, info_box
)
from modules.config import COLORS


def _fmt_billions(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    if abs(v) >= 1_000:
        return f"${v/1_000:.2f}T"
    return f"${v:.1f}B"


def _fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "N/A"
    return f"{v:+.2%}"


def render(
    net_liq: pd.Series,
    fred_components: dict[str, pd.Series],
) -> None:
    page_title(
        "Liquidity Observatory",
        "Net Federal Reserve Liquidity · WALCL − RRPONTSYD − WTREGEN"
    )

    # ── Summary stats ──────────────────────────────────────────────────────
    stats = liquidity_summary(net_liq)
    if not stats:
        st.error("Insufficient data to compute liquidity statistics.")
        return

    section_header("Headline Metrics")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card(
            "Net Liquidity",
            _fmt_billions(stats.get("current")),
            f"Median: {_fmt_billions(stats.get('median'))}",
        )
    with c2:
        chg1 = stats.get("change_1m", 0) or 0
        kpi_card(
            "1-Month Change",
            _fmt_billions(chg1),
            f"{_fmt_pct(stats.get('change_1m_pct'))}",
            sub_positive=(chg1 >= 0),
        )
    with c3:
        chg3 = stats.get("change_3m", 0) or 0
        kpi_card(
            "3-Month Change",
            _fmt_billions(chg3),
            f"{_fmt_pct(stats.get('change_3m_pct'))}",
            sub_positive=(chg3 >= 0),
        )
    with c4:
        chgy = stats.get("change_yoy", 0) or 0
        kpi_card(
            "Year-over-Year",
            _fmt_billions(chgy),
            f"{_fmt_pct(stats.get('change_yoy_pct'))}",
            sub_positive=(chgy >= 0),
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Secondary stats row ────────────────────────────────────────────────
    s1, s2, s3 = st.columns(3)
    with s1:
        kpi_card("All-Time High",  _fmt_billions(stats.get("all_time_high")))
    with s2:
        kpi_card("All-Time Low",   _fmt_billions(stats.get("all_time_low")))
    with s3:
        pct_ath = stats.get("pct_of_ath")
        kpi_card(
            "% of ATH",
            f"{pct_ath:.1%}" if pct_ath else "N/A",
            sub_positive=(pct_ath >= 0.8 if pct_ath else None),
        )

    # ── Chart ─────────────────────────────────────────────────────────────
    section_header("Net Liquidity Time Series")
    fig = chart_net_liquidity(net_liq, fred_components)
    chart_container(fig)

    info_box(
        "Net Liquidity = Fed Balance Sheet (WALCL) "
        "minus Reverse Repo Facility (RRPONTSYD) "
        "minus Treasury General Account (WTREGEN). "
        "Data sourced from FRED; resampled to month-end frequency."
    )

    # ── Raw data expander ──────────────────────────────────────────────────
    with st.expander("▸  Show raw monthly data", expanded=False):
        df = pd.DataFrame(fred_components)
        df.index.name = "Date"
        df.index = df.index.strftime("%Y-%m")
        df["Net_Liquidity"] = net_liq.values[-len(df):]
        st.dataframe(
            df.tail(36).style.format("${:,.1f}"),
            use_container_width=True,
        )
