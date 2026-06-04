"""
ui_components.py
----------------
Reusable Streamlit UI components: KPI cards, section headers, data tables.
Centralise all HTML-injection and CSS customisation here.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.config import COLORS


# ── Global CSS ────────────────────────────────────────────────────────────────

GLOBAL_CSS = f"""
<style>
  /* ── Google Font import ── */
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] {{
      font-family: 'IBM Plex Sans', sans-serif;
      background-color: {COLORS["bg_primary"]};
      color: {COLORS["text_primary"]};
  }}

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {{
      background-color: {COLORS["bg_secondary"]};
      border-right: 1px solid {COLORS["border"]};
  }}
  section[data-testid="stSidebar"] .stRadio label {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.82rem;
      letter-spacing: 0.06em;
      color: {COLORS["text_muted"]};
  }}

  /* ── Main area ── */
  .main .block-container {{
      padding-top: 1.5rem;
      padding-bottom: 3rem;
      max-width: 1280px;
  }}

  /* ── KPI Card ── */
  .kpi-card {{
      background: {COLORS["bg_card"]};
      border: 1px solid {COLORS["border"]};
      border-radius: 6px;
      padding: 18px 22px;
      min-height: 96px;
      position: relative;
      overflow: hidden;
  }}
  .kpi-card::before {{
      content: '';
      position: absolute;
      top: 0; left: 0;
      width: 3px; height: 100%;
      background: {COLORS["accent_cyan"]};
  }}
  .kpi-label {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.68rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: {COLORS["text_muted"]};
      margin-bottom: 6px;
  }}
  .kpi-value {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 1.55rem;
      font-weight: 600;
      color: {COLORS["text_primary"]};
      letter-spacing: -0.01em;
  }}
  .kpi-sub {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.75rem;
      margin-top: 4px;
  }}
  .kpi-pos {{ color: {COLORS["accent_green"]}; }}
  .kpi-neg {{ color: {COLORS["accent_red"]}; }}
  .kpi-neu {{ color: {COLORS["text_muted"]}; }}

  /* ── Section Header ── */
  .section-header {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.7rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: {COLORS["accent_cyan"]};
      border-bottom: 1px solid {COLORS["border"]};
      padding-bottom: 6px;
      margin-bottom: 18px;
      margin-top: 28px;
  }}

  /* ── Page Title ── */
  .page-title {{
      font-family: 'IBM Plex Sans', sans-serif;
      font-size: 1.4rem;
      font-weight: 600;
      color: {COLORS["text_primary"]};
      letter-spacing: -0.02em;
  }}
  .page-sub {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.75rem;
      color: {COLORS["text_muted"]};
      margin-top: 2px;
  }}

  /* ── Data Tables ── */
  .stDataFrame, .stTable {{
      font-family: 'IBM Plex Mono', monospace !important;
      font-size: 0.82rem !important;
  }}

  /* ── Chart container ── */
  .chart-container {{
      background: {COLORS["bg_card"]};
      border: 1px solid {COLORS["border"]};
      border-radius: 6px;
      padding: 4px;
      margin-bottom: 12px;
  }}

  /* ── Plotly toolbar tweak ── */
  .modebar {{ background: transparent !important; }}

  /* ── Streamlit metric overrides ── */
  [data-testid="metric-container"] {{
      background: {COLORS["bg_card"]};
      border: 1px solid {COLORS["border"]};
      border-radius: 6px;
      padding: 12px 16px;
  }}

  /* ── Divider ── */
  hr {{
      border-color: {COLORS["border"]};
      margin: 20px 0;
  }}

  /* ── Info box ── */
  .info-box {{
      background: {COLORS["bg_elevated"]};
      border-left: 3px solid {COLORS["accent_blue"]};
      border-radius: 0 4px 4px 0;
      padding: 10px 14px;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.78rem;
      color: {COLORS["text_muted"]};
      margin: 8px 0;
  }}
</style>
"""


def inject_css() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ── KPI Card ─────────────────────────────────────────────────────────────────

def kpi_card(label: str, value: str, sub: str = "", sub_positive: bool | None = None) -> None:
    sub_class = "kpi-neu"
    if sub_positive is True:
        sub_class = "kpi-pos"
    elif sub_positive is False:
        sub_class = "kpi-neg"

    html = f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      {"" if not sub else f'<div class="kpi-sub {sub_class}">{sub}</div>'}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ── Section Header ────────────────────────────────────────────────────────────

def section_header(title: str) -> None:
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


# ── Page Title ────────────────────────────────────────────────────────────────

def page_title(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="page-title">{title}</div>'
        + (f'<div class="page-sub">{subtitle}</div>' if subtitle else ""),
        unsafe_allow_html=True,
    )
    st.markdown("<hr/>", unsafe_allow_html=True)


# ── Chart Wrapper ─────────────────────────────────────────────────────────────

def chart_container(fig, use_container_width: bool = True) -> None:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=use_container_width, config={
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["select2d", "lasso2d"],
        "toImageButtonOptions": {"format": "png", "width": 1400, "height": 700},
    })
    st.markdown("</div>", unsafe_allow_html=True)


# ── Data Table ────────────────────────────────────────────────────────────────

def styled_table(df: pd.DataFrame, pct_cols: list[str] | None = None) -> None:
    """
    Render a DataFrame with conditional red/green colour on percentage columns.
    """
    pct_cols = pct_cols or []

    def _color(val):
        if isinstance(val, float):
            color = COLORS["accent_green"] if val >= 0 else COLORS["accent_red"]
            return f"color: {color}"
        return ""

    styled = df.style.set_table_styles([
        {"selector": "thead th",
         "props": [
             ("background-color", COLORS["bg_elevated"]),
             ("color", COLORS["text_muted"]),
             ("font-family", "'IBM Plex Mono', monospace"),
             ("font-size", "0.72rem"),
             ("letter-spacing", "0.08em"),
             ("text-transform", "uppercase"),
             ("border-bottom", f"1px solid {COLORS['border']}"),
         ]},
        {"selector": "tbody td",
         "props": [
             ("font-family", "'IBM Plex Mono', monospace"),
             ("font-size", "0.8rem"),
             ("background-color", COLORS["bg_card"]),
             ("color", COLORS["text_primary"]),
             ("border-bottom", f"1px solid {COLORS['border']}"),
         ]},
        {"selector": "tbody tr:hover td",
         "props": [("background-color", COLORS["bg_elevated"])]},
    ])

    for col in pct_cols:
        if col in df.columns:
            styled = styled.applymap(_color, subset=[col])
            styled = styled.format({col: "{:+.2%}"})

    # Format remaining float columns
    float_cols = {
        c: "{:.3f}" for c in df.columns
        if c not in pct_cols and pd.api.types.is_float_dtype(df[c])
    }
    styled = styled.format(float_cols)

    st.dataframe(styled, use_container_width=True)


# ── Info Box ─────────────────────────────────────────────────────────────────

def info_box(text: str) -> None:
    st.markdown(f'<div class="info-box">ℹ️ &nbsp;{text}</div>', unsafe_allow_html=True)
