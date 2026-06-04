"""
charts.py
---------
Pure chart-building functions.  Each function accepts DataFrames / Series
and returns a Plotly Figure.  No Streamlit calls here — keeps rendering
logic decoupled from data and layout.

Extension points
----------------
- Add VAR / Granger causality overlays as new traces on existing figures.
- Wrap any figure with `add_recession_bands()` once NBER data is wired up.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from modules.config import (
    COLORS, CHART_LAYOUT_DEFAULTS, TICKERS, TICKER_COLORS, LAG_HORIZONS
)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _base_layout(**overrides) -> dict:
    layout = dict(CHART_LAYOUT_DEFAULTS)
    layout.update(overrides)
    return layout


def _format_billions(val: float) -> str:
    if abs(val) >= 1_000:
        return f"${val/1_000:.2f}T"
    return f"${val:.1f}B"


# ── Page 1: Overview ──────────────────────────────────────────────────────────

def chart_net_liquidity(
    net_liq: pd.Series,
    fred_components: dict[str, pd.Series],
) -> go.Figure:
    """
    Dual-panel chart:
      Top   : Net Liquidity area fill with gradient
      Bottom: Stacked FRED components (WALCL, RRP, TGA)
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.6, 0.4],
        subplot_titles=["Net Liquidity (WALCL − RRP − TGA)", "FRED Components"],
    )

    # ── Net Liquidity ──
    fig.add_trace(
        go.Scatter(
            x=net_liq.index, y=net_liq.values,
            name="Net Liquidity",
            mode="lines",
            line=dict(color=COLORS["accent_cyan"], width=2),
            fill="tozeroy",
            fillcolor="rgba(0,184,217,0.12)",
        ),
        row=1, col=1,
    )

    # ── FRED Components ──
    component_colors = {
        "WALCL":     COLORS["accent_blue"],
        "RRPONTSYD": COLORS["accent_red"],
        "WTREGEN":   COLORS["accent_amber"],
    }
    component_labels = {
        "WALCL":     "Fed Assets (WALCL)",
        "RRPONTSYD": "Reverse Repo (RRP)",
        "WTREGEN":   "Treasury Gen. Acct (TGA)",
    }

    for series_id, series in fred_components.items():
        fig.add_trace(
            go.Scatter(
                x=series.index, y=series.values,
                name=component_labels.get(series_id, series_id),
                mode="lines",
                line=dict(color=component_colors.get(series_id, "#999"), width=1.5),
            ),
            row=2, col=1,
        )

    layout = _base_layout(
        height=560,
        title=None,
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01,
            xanchor="left", x=0,
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    layout["xaxis2"] = dict(gridcolor=COLORS["grid"], zeroline=False,
                             linecolor=COLORS["border"])
    layout["yaxis"]  = dict(gridcolor=COLORS["grid"], zeroline=False,
                             linecolor=COLORS["border"],
                             tickformat="$,.0f", title="Billions USD")
    layout["yaxis2"] = dict(gridcolor=COLORS["grid"], zeroline=False,
                             linecolor=COLORS["border"],
                             tickformat="$,.0f", title="Billions USD")

    fig.update_layout(**layout)
    fig.update_annotations(font_color=COLORS["text_muted"], font_size=11)
    return fig


# ── Page 2: Asset Performance ─────────────────────────────────────────────────

def chart_asset_performance(returns: pd.DataFrame, lookback_months: int = 24) -> go.Figure:
    """
    Cumulative-return fan chart for all tickers over the selected window.
    """
    df = returns.tail(lookback_months).copy()
    cumret = (1 + df).cumprod() - 1

    fig = go.Figure()
    for ticker in cumret.columns:
        if ticker not in TICKERS:
            continue
        color = TICKER_COLORS.get(ticker, "#AAAAAA")
        last_val = cumret[ticker].dropna().iloc[-1] if not cumret[ticker].dropna().empty else 0
        fig.add_trace(go.Scatter(
            x=cumret.index,
            y=cumret[ticker],
            name=f"{TICKERS[ticker]} ({last_val:+.1%})",
            mode="lines",
            line=dict(color=color, width=2),
        ))

    fig.add_hline(y=0, line_color=COLORS["border"], line_width=1)

    fig.update_layout(**_base_layout(
        height=440,
        yaxis=dict(
            gridcolor=COLORS["grid"], zeroline=False,
            tickformat=".0%", title="Cumulative Return",
        ),
        xaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
    ))
    return fig


def chart_monthly_returns_bar(returns: pd.DataFrame, lookback_months: int = 12) -> go.Figure:
    """
    Grouped bar chart of the last N months of monthly returns per asset.
    """
    df = returns.tail(lookback_months).copy()
    df.index = df.index.strftime("%b %y")

    fig = go.Figure()
    for ticker in df.columns:
        if ticker not in TICKERS:
            continue
        color = TICKER_COLORS.get(ticker, "#AAAAAA")
        fig.add_trace(go.Bar(
            x=df.index,
            y=df[ticker],
            name=TICKERS[ticker],
            marker_color=color,
            opacity=0.85,
        ))

    fig.add_hline(y=0, line_color=COLORS["border"], line_width=1)
    fig.update_layout(**_base_layout(
        height=380,
        barmode="group",
        yaxis=dict(
            gridcolor=COLORS["grid"], zeroline=False,
            tickformat=".1%", title="Monthly Return",
        ),
        xaxis=dict(gridcolor=COLORS["grid"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
    ))
    return fig


def chart_correlation_matrix(returns: pd.DataFrame) -> go.Figure:
    """
    Annotated heatmap of pairwise return correlations.
    """
    cols  = [t for t in TICKERS if t in returns.columns]
    corr  = returns[cols].corr()
    labels = [TICKERS[t] for t in cols]

    # Custom diverging colorscale
    colorscale = [
        [0.0, "#FF1744"],
        [0.5, COLORS["bg_card"]],
        [1.0, COLORS["accent_cyan"]],
    ]

    z_text = [[f"{corr.iloc[i, j]:.2f}" for j in range(len(cols))]
              for i in range(len(cols))]

    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=labels, y=labels,
        text=z_text,
        texttemplate="%{text}",
        textfont=dict(size=11, color=COLORS["text_primary"]),
        colorscale=colorscale,
        zmid=0,
        zmin=-1, zmax=1,
        showscale=True,
        colorbar=dict(
            tickfont=dict(color=COLORS["text_muted"]),
            thickness=12,
        ),
    ))

    fig.update_layout(**_base_layout(
        height=420,
        xaxis=dict(tickangle=-35, gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
    ))
    return fig


# ── Page 3: Lead-Lag Analysis ─────────────────────────────────────────────────

def compute_lead_lag_correlations(
    net_liq: pd.Series,
    returns: pd.DataFrame,
    horizons: list[int] = LAG_HORIZONS,
) -> pd.DataFrame:
    """
    Pearson correlation between Net Liquidity change and forward asset returns
    at each horizon.

    Returns a DataFrame indexed by horizon, columns = tickers.
    """
    cols = [t for t in TICKERS if t in returns.columns]
    liq_chg = net_liq.pct_change().dropna()

    records = []
    for h in horizons:
        row = {"Horizon": f"{h}M Forward"}
        for ticker in cols:
            fwd_ret = returns[ticker].shift(-h)
            combined = pd.concat([liq_chg, fwd_ret], axis=1).dropna()
            if len(combined) > 10:
                corr = combined.iloc[:, 0].corr(combined.iloc[:, 1])
            else:
                corr = np.nan
            row[TICKERS[ticker]] = round(corr, 3)
        records.append(row)

    return pd.DataFrame(records).set_index("Horizon")


def chart_lead_lag_heatmap(corr_df: pd.DataFrame) -> go.Figure:
    """
    Heatmap of lead-lag correlations: rows = horizons, cols = assets.
    """
    colorscale = [
        [0.0, "#FF1744"],
        [0.5, COLORS["bg_card"]],
        [1.0, COLORS["accent_green"]],
    ]

    z_text = [[f"{corr_df.iloc[i, j]:.2f}" for j in range(corr_df.shape[1])]
              for i in range(corr_df.shape[0])]

    fig = go.Figure(go.Heatmap(
        z=corr_df.values,
        x=corr_df.columns.tolist(),
        y=corr_df.index.tolist(),
        text=z_text,
        texttemplate="%{text}",
        textfont=dict(size=13, color=COLORS["text_primary"]),
        colorscale=colorscale,
        zmid=0,
        zmin=-1, zmax=1,
        showscale=True,
        colorbar=dict(
            title=dict(text="Corr", font=dict(color=COLORS["text_muted"])),
            tickfont=dict(color=COLORS["text_muted"]),
            thickness=12,
        ),
    ))

    fig.update_layout(**_base_layout(
        height=300,
        xaxis=dict(tickangle=-20, gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
    ))
    return fig


def chart_lead_lag_scatter(
    net_liq: pd.Series,
    returns: pd.DataFrame,
    ticker: str,
    horizon: int,
) -> go.Figure:
    """
    Scatter of Net Liquidity YoY change vs. forward returns for a single ticker.
    """
    liq_chg = net_liq.pct_change(12).dropna()
    fwd_ret = returns[ticker].shift(-horizon) if ticker in returns.columns else pd.Series()
    combined = pd.concat([liq_chg.rename("liq_chg"), fwd_ret.rename("fwd_ret")],
                          axis=1).dropna()

    color   = TICKER_COLORS.get(ticker, COLORS["accent_cyan"])
    x_label = "Net Liquidity YoY Change"
    y_label = f"{TICKERS.get(ticker, ticker)} {horizon}M Fwd Return"

    # OLS trendline
    if len(combined) > 3:
        m, b = np.polyfit(combined["liq_chg"], combined["fwd_ret"], 1)
        x_line = np.linspace(combined["liq_chg"].min(), combined["liq_chg"].max(), 50)
        y_line = m * x_line + b
    else:
        x_line = y_line = []

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=combined["liq_chg"], y=combined["fwd_ret"],
        mode="markers",
        marker=dict(color=color, size=7, opacity=0.7,
                    line=dict(color="rgba(255,255,255,0.15)", width=1)),
        text=combined.index.strftime("%b %Y"),
        hovertemplate="%{text}<br>Liq Chg: %{x:.1%}<br>Fwd Ret: %{y:.1%}<extra></extra>",
        name="Observations",
    ))
    if len(x_line):
        fig.add_trace(go.Scatter(
            x=x_line, y=y_line,
            mode="lines",
            line=dict(color=COLORS["accent_amber"], width=1.5, dash="dash"),
            name="OLS Trend",
        ))

    fig.update_layout(**_base_layout(
        height=380,
        xaxis=dict(title=x_label, gridcolor=COLORS["grid"],
                   zeroline=True, zerolinecolor=COLORS["border"],
                   tickformat=".0%"),
        yaxis=dict(title=y_label, gridcolor=COLORS["grid"],
                   zeroline=True, zerolinecolor=COLORS["border"],
                   tickformat=".0%"),
    ))
    return fig


# ── Page 4: Regime Analysis ───────────────────────────────────────────────────

def compute_regime_returns(
    net_liq: pd.Series,
    returns: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Splits the sample into High / Low liquidity regimes using the median.

    Returns
    -------
    high_df  : returns during High Liquidity periods
    low_df   : returns during Low Liquidity periods
    regime   : boolean series (True = High Liquidity)
    """
    cols   = [t for t in TICKERS if t in returns.columns]
    common = net_liq.index.intersection(returns.index)
    liq    = net_liq.loc[common]
    ret    = returns.loc[common, cols]

    median  = liq.median()
    regime  = liq >= median

    high_df = ret.loc[regime]
    low_df  = ret.loc[~regime]
    return high_df, low_df, regime


def chart_regime_avg_returns(high_df: pd.DataFrame, low_df: pd.DataFrame) -> go.Figure:
    """
    Grouped bar chart comparing average monthly returns across regimes.
    """
    cols   = [t for t in TICKERS if t in high_df.columns]
    labels = [TICKERS[t] for t in cols]

    high_avg = [high_df[t].mean() for t in cols]
    low_avg  = [low_df[t].mean()  for t in cols]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=high_avg,
        name="High Liquidity",
        marker_color=COLORS["accent_cyan"],
        opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        x=labels, y=low_avg,
        name="Low Liquidity",
        marker_color=COLORS["accent_red"],
        opacity=0.85,
    ))

    fig.add_hline(y=0, line_color=COLORS["border"], line_width=1)
    fig.update_layout(**_base_layout(
        height=400,
        barmode="group",
        yaxis=dict(
            gridcolor=COLORS["grid"], zeroline=False,
            tickformat=".1%", title="Avg Monthly Return",
        ),
        xaxis=dict(gridcolor=COLORS["grid"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
    ))
    return fig


def chart_regime_timeline(regime: pd.Series, net_liq: pd.Series) -> go.Figure:
    """
    Net Liquidity line with shaded High / Low regime bands.
    """
    fig = go.Figure()

    # Shade High Liquidity bands
    in_band = False
    band_start = None
    for dt, is_high in regime.items():
        if is_high and not in_band:
            band_start = dt
            in_band = True
        elif not is_high and in_band:
            fig.add_vrect(
                x0=band_start, x1=dt,
                fillcolor=COLORS["accent_cyan"],
                opacity=0.08,
                layer="below",
                line_width=0,
            )
            in_band = False
    if in_band:
        fig.add_vrect(
            x0=band_start, x1=regime.index[-1],
            fillcolor=COLORS["accent_cyan"],
            opacity=0.08,
            layer="below",
            line_width=0,
        )

    fig.add_trace(go.Scatter(
        x=net_liq.index, y=net_liq.values,
        name="Net Liquidity",
        mode="lines",
        line=dict(color=COLORS["accent_cyan"], width=2),
    ))

    fig.add_hline(
        y=net_liq.median(),
        line=dict(color=COLORS["accent_amber"], width=1.5, dash="dot"),
        annotation_text="Median",
        annotation_font_color=COLORS["accent_amber"],
    )

    fig.update_layout(**_base_layout(
        height=360,
        yaxis=dict(
            gridcolor=COLORS["grid"], zeroline=False,
            tickformat="$,.0f", title="Net Liquidity (Billions USD)",
        ),
        xaxis=dict(gridcolor=COLORS["grid"]),
        hovermode="x unified",
    ))
    return fig
