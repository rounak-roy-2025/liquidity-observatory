# 📡 Liquidity & Capital Flow Observatory

A professional macro-finance dashboard tracking **Federal Reserve Net Liquidity** and its relationship with global asset markets.

Built with **Streamlit**, **Plotly**, **FRED API**, and **Yahoo Finance**.

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| **Overview** | Net Liquidity KPIs (current, 1M, 3M, YoY change) + interactive time-series with FRED components |
| **Asset Performance** | Monthly returns, cumulative fan chart, correlation matrix for SPY/QQQ/GLD/TLT/BTC/EEM |
| **Lead-Lag Analysis** | Correlation between Net Liquidity changes and future asset returns at 1M, 3M, 6M horizons |
| **Regime Analysis** | High vs. Low Liquidity regime split (median threshold) — average returns, hit rates, deep-dive |

---

## Liquidity Formula

```
Net Liquidity = WALCL − RRPONTSYD − WTREGEN
```

| Series | Description |
|--------|-------------|
| `WALCL` | Federal Reserve Total Assets |
| `RRPONTSYD` | Overnight Reverse Repo Facility |
| `WTREGEN` | Treasury General Account (TGA) |

All series are resampled to **month-end** frequency.

---

## Project Structure

```
liquidity_observatory/
│
├── app.py                          # Streamlit entry point
│
├── modules/
│   ├── __init__.py
│   ├── config.py                   # Constants, tickers, colours, FRED series
│   ├── data_loader.py              # FRED + yfinance fetching & caching
│   ├── analytics.py                # Statistical utilities (no Streamlit)
│   ├── charts.py                   # Plotly figure builders (no Streamlit)
│   ├── ui_components.py            # Reusable Streamlit widgets & CSS
│   │
│   └── pages/
│       ├── __init__.py
│       ├── page_overview.py        # Page 1
│       ├── page_assets.py          # Page 2
│       ├── page_leadlag.py         # Page 3
│       └── page_regime.py          # Page 4
│
├── .streamlit/
│   ├── config.toml                 # Dark theme & server settings
│   └── secrets.toml                # API keys (DO NOT commit)
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Local Setup

### 1. Clone / download

```bash
git clone https://github.com/your-org/liquidity-observatory.git
cd liquidity-observatory
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your FRED API key

Copy the example env file and add your key:

```bash
cp .env.example .env
```

Edit `.env`:

```
FRED_API_KEY=2f8fd1c43b0524fe40d61a54ba7c117e
```

You can get a free FRED API key at: https://fred.stlouisfed.org/docs/api/api_key.html

### 5. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Streamlit Cloud Deployment

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-org/liquidity-observatory.git
git push -u origin main
```

> ⚠️ Make sure `.streamlit/secrets.toml` is in `.gitignore`. Never commit API keys.

### 2. Connect on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app**
3. Select your repository, branch (`main`), and main file (`app.py`)
4. Click **Advanced settings → Secrets** and paste:

```toml
FRED_API_KEY = "2f8fd1c43b0524fe40d61a54ba7c117e"
```

5. Click **Deploy**

---

## Extending the Dashboard

The codebase is designed for easy extension:

### Add new FRED series

In `modules/config.py`:

```python
FRED_SERIES = {
    "WALCL":     "Fed Total Assets",
    "RRPONTSYD": "Reverse Repo",
    "WTREGEN":   "Treasury General Account",
    # ── Add ECB, BOJ, PBOC here ──
    "ECBASSETSW": "ECB Balance Sheet",
}
```

### Add new tickers

```python
TICKERS = {
    "SPY": "S&P 500",
    # ... existing ...
    "GDX": "Gold Miners",   # just add here
}
TICKER_COLORS["GDX"] = "#A5D6A7"
```

### Add Granger causality

In `modules/analytics.py`, add:

```python
from statsmodels.tsa.stattools import grangercausalitytests

def granger_causality(net_liq, returns, max_lag=6):
    ...
```

### Add VAR model

```python
from statsmodels.tsa.vector_ar.var_model import VAR

def fit_var(net_liq, returns, lags=3):
    ...
```

---

## Data Notes

- FRED data is updated on different frequencies (weekly for WALCL/RRPONTSYD, weekly for WTREGEN). The dashboard forward-fills and resamples to month-end.
- Yahoo Finance data uses adjusted close prices.
- Cache TTL is 1 hour by default (configurable in `config.py` via `CACHE_TTL_SECONDS`).
- The app fetches the last `HISTORY_YEARS` (default: 10) years of data.

---

## License

MIT — free to use, modify, and extend.
