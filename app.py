"""
app.py
------
Liquidity & Capital Flow Observatory
Entry point for the Streamlit application.

Run locally:
    streamlit run app.py

Deploy on Streamlit Cloud:
    Push to GitHub, connect the repo in share.streamlit.io,
    add FRED_API_KEY to Streamlit Secrets.
"""

from __future__ import annotations

import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Liquidity Observatory",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**Liquidity & Capital Flow Observatory**\n\n"
            "Tracks Federal Reserve Net Liquidity and its relationship "
            "with global asset markets.\n\n"
            "Data: FRED + Yahoo Finance"
        )
    },
)

# ── Module imports ────────────────────────────────────────────────────────────
from modules.ui_components import inject_css
from modules.data_loader   import load_all
from modules.config        import COLORS

from modules.pages import (
    page_overview,
    page_assets,
    page_leadlag,
    page_regime,
)

# ── Inject global CSS ─────────────────────────────────────────────────────────
inject_css()


# ── Sidebar ───────────────────────────────────────────────────────────────────
def _sidebar() -> str:
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding: 16px 0 24px 0;">
              <div style="font-family: 'IBM Plex Mono', monospace;
                          font-size: 0.65rem; letter-spacing: 0.18em;
                          text-transform: uppercase; color: {COLORS['accent_cyan']};
                          margin-bottom: 4px;">
                Liquidity Observatory
              </div>
              <div style="font-family: 'IBM Plex Sans', sans-serif;
                          font-size: 1.05rem; font-weight: 600;
                          color: {COLORS['text_primary']};">
                Capital Flow Monitor
              </div>
              <div style="font-family: 'IBM Plex Mono', monospace;
                          font-size: 0.7rem; color: {COLORS['text_muted']};
                          margin-top: 4px;">
                FRED · Yahoo Finance
              </div>
            </div>
            <hr style="border-color:{COLORS['border']}; margin: 0 0 16px 0;"/>
            """,
            unsafe_allow_html=True,
        )

        pages = {
            "📡  Overview":          "Overview",
            "📊  Asset Performance": "Asset Performance",
            "🔗  Lead-Lag Analysis": "Lead-Lag Analysis",
            "🎛  Regime Analysis":   "Regime Analysis",
        }

        selected = st.radio(
            "Navigation",
            options=list(pages.keys()),
            label_visibility="collapsed",
        )

        st.markdown(
            f"""
            <hr style="border-color:{COLORS['border']}; margin: 20px 0 12px 0;"/>
            <div style="font-family:'IBM Plex Mono',monospace;
                        font-size:0.65rem;color:{COLORS['text_muted']};
                        line-height:1.7;">
              <b style="color:{COLORS['text_muted']}">SOURCES</b><br/>
              WALCL · RRPONTSYD · WTREGEN<br/>
              SPY · QQQ · GLD · TLT<br/>
              BTC-USD · EEM<br/><br/>
              Data refreshes on each page load.<br/>
              Cache TTL: 60 minutes.
            </div>
            """,
            unsafe_allow_html=True,
        )

    return pages[selected]


# ── Data loading with spinner ─────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _cached_load():
    """
    Thin wrapper so we can show a custom spinner while load_all() runs.
    Note: load_all() itself uses @st.cache_data internally with a TTL.
    """
    return load_all()


def main() -> None:
    active_page = _sidebar()

    # ── Load data ──────────────────────────────────────────────────────────
    with st.spinner("📡  Connecting to FRED & Yahoo Finance…"):
        try:
            net_liq, prices, returns, fred_components = load_all()
        except ValueError as exc:
            st.error(
                f"**Configuration error:** {exc}\n\n"
                "Please set `FRED_API_KEY` in your `.env` file or "
                "Streamlit Secrets (`[secrets]` section in cloud settings)."
            )
            st.stop()
        except Exception as exc:
            st.error(
                f"**Data loading error:** {exc}\n\n"
                "Check your internet connection and API key, then refresh."
            )
            st.stop()

    # ── Route to page ──────────────────────────────────────────────────────
    if active_page == "Overview":
        page_overview.render(net_liq, fred_components)

    elif active_page == "Asset Performance":
        page_assets.render(prices, returns)

    elif active_page == "Lead-Lag Analysis":
        page_leadlag.render(net_liq, returns)

    elif active_page == "Regime Analysis":
        page_regime.render(net_liq, returns)


if __name__ == "__main__":
    main()
