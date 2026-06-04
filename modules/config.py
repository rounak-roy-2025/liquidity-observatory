"""
config.py
---------
Central configuration for the Liquidity & Capital Flow Observatory.
Edit this file to add new FRED series, tickers, or adjust display settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ────────────────────────────────────────────────────────────────
# Priority: Streamlit secrets → environment variable → .env file
def _get_fred_key() -> str:
    try:
        import streamlit as st
        return st.secrets.get("FRED_API_KEY", os.getenv("FRED_API_KEY", ""))
    except Exception:
        return os.getenv("FRED_API_KEY", "")

FRED_API_KEY: str = _get_fred_key()

# ── FRED Series ─────────────────────────────────────────────────────────────
FRED_SERIES: dict[str, str] = {
    "WALCL":     "Fed Total Assets (WALCL)",
    "RRPONTSYD": "Reverse Repo (RRPONTSYD)",
    "WTREGEN":   "Treasury General Account (WTREGEN)",
}

# ── Yahoo Finance Tickers ────────────────────────────────────────────────────
TICKERS: dict[str, str] = {
    "SPY":     "S&P 500",
    "QQQ":     "Nasdaq 100",
    "GLD":     "Gold",
    "TLT":     "20Y Treasuries",
    "BTC-USD": "Bitcoin",
    "EEM":     "Emerging Markets",
}

TICKER_COLORS: dict[str, str] = {
    "SPY":     "#4FC3F7",
    "QQQ":     "#81D4FA",
    "GLD":     "#FFD54F",
    "TLT":     "#A5D6A7",
    "BTC-USD": "#FFB74D",
    "EEM":     "#CE93D8",
}

# ── Data Window ──────────────────────────────────────────────────────────────
HISTORY_YEARS: int = 10          # how many years of history to fetch
CACHE_TTL_SECONDS: int = 3600    # 1 hour Streamlit cache TTL

# ── Liquidity Formula ────────────────────────────────────────────────────────
# Net Liquidity = WALCL - RRPONTSYD - WTREGEN
LIQUIDITY_POSITIVE_COMPONENTS: list[str] = ["WALCL"]
LIQUIDITY_NEGATIVE_COMPONENTS: list[str] = ["RRPONTSYD", "WTREGEN"]

# ── Lead-Lag Horizons (months) ────────────────────────────────────────────────
LAG_HORIZONS: list[int] = [1, 3, 6]

# ── Theme / Palette ──────────────────────────────────────────────────────────
COLORS = {
    "bg_primary":   "#0A0E1A",
    "bg_secondary": "#0F1629",
    "bg_card":      "#141B2D",
    "bg_elevated":  "#1A2340",
    "accent_blue":  "#1E88E5",
    "accent_cyan":  "#00B8D9",
    "accent_green": "#00E676",
    "accent_amber": "#FFD600",
    "accent_red":   "#FF1744",
    "text_primary": "#E8EAF6",
    "text_muted":   "#7986CB",
    "border":       "#1E2D4A",
    "grid":         "#1A2340",
}

PLOTLY_TEMPLATE = "plotly_dark"

CHART_LAYOUT_DEFAULTS = dict(
    plot_bgcolor  = COLORS["bg_card"],
    paper_bgcolor = COLORS["bg_card"],
    font          = dict(family="'IBM Plex Mono', 'Courier New', monospace",
                         color=COLORS["text_primary"], size=11),
    xaxis         = dict(gridcolor=COLORS["grid"], zeroline=False,
                         linecolor=COLORS["border"]),
    yaxis         = dict(gridcolor=COLORS["grid"], zeroline=False,
                         linecolor=COLORS["border"]),
    margin        = dict(l=50, r=30, t=50, b=40),
    legend        = dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"]),
    hoverlabel    = dict(bgcolor=COLORS["bg_elevated"],
                         font_color=COLORS["text_primary"],
                         bordercolor=COLORS["border"]),
)
