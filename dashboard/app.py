from __future__ import annotations

import html
import re
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf


st.set_page_config(
    page_title="StockScope · Stock market for beginner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TOP_NAV = ["Home", "Learn", "Markets", "Watchlist"]
MARKET_TABS = ["Overview", "Screener", "Live quotes", "Returns & risk", "Stock"]
LEARN_TABS = ["Start here", "Data & methods"]
CHART_RANGES = {
    "1D": {"period": "1d", "interval": "5m"},
    "5D": {"period": "5d", "interval": "15m"},
    "1M": {"period": "1mo", "interval": "1d"},
    "6M": {"period": "6mo", "interval": "1d"},
    "1Y": {"period": "1y", "interval": "1d"},
    "All Time": {"period": "max", "interval": "1wk"},
}
PERIOD_LABELS = {
    "1mo": "1 month",
    "3mo": "3 months",
    "6mo": "6 months",
    "1y": "1 year",
    "2y": "2 years",
    "5y": "5 years",
}
INDEX_META = {
    "^GSPC": {
        "display": "SPX",
        "name": "S&P 500",
        "blurb": "Broad view of large US companies",
        "unit": "point",
        "badge": "500",
        "badge_bg": "#f23645",
    },
    "^NDX": {
        "display": "NDX",
        "name": "NASDAQ 100",
        "blurb": "Largest non-financial Nasdaq companies",
        "unit": "point",
        "badge": "100",
        "badge_bg": "#2962ff",
    },
    "^DJI": {
        "display": "DJI",
        "name": "Dow Jones",
        "blurb": "30 major US industrial companies",
        "unit": "USD",
        "badge": "30",
        "badge_bg": "#131722",
    },
}
INDEX_ORDER = ["^GSPC", "^NDX", "^DJI"]
INDEX_ALIASES = {
    "SPX": "^GSPC", "S&P": "^GSPC", "S&P500": "^GSPC", "SP500": "^GSPC",
    "GSPC": "^GSPC", "^GSPC": "^GSPC", "SNP": "^GSPC",
    "NDX": "^NDX", "NASDAQ": "^NDX", "NASDAQ100": "^NDX", "IXIC": "^NDX",
    "^NDX": "^NDX",
    "DJI": "^DJI", "DJIA": "^DJI", "DOW": "^DJI", "^DJI": "^DJI",
}

UNIVERSE = {
    "AAPL": "Technology", "MSFT": "Technology", "NVDA": "Technology", "GOOGL": "Technology",
    "AMZN": "Tech / consumer", "META": "Technology", "AVGO": "Technology", "ORCL": "Technology",
    "CRM": "Technology", "AMD": "Technology", "QCOM": "Technology", "INTC": "Technology",
    "CSCO": "Technology", "ADBE": "Technology", "IBM": "Technology",
    "JPM": "Financials", "BAC": "Financials", "GS": "Financials", "MS": "Financials",
    "V": "Financials", "MA": "Financials", "PYPL": "Financials", "BRK-B": "Financials",
    "LLY": "Health care", "JNJ": "Health care", "UNH": "Health care",
    "ABBV": "Health care", "MRK": "Health care", "PFE": "Health care", "ISRG": "Health care",
    "WMT": "Consumer", "COST": "Consumer", "HD": "Consumer", "NKE": "Consumer",
    "MCD": "Consumer", "KO": "Consumer", "PG": "Consumer", "DIS": "Consumer", "NFLX": "Consumer / media",
    "CAT": "Industrials", "GE": "Industrials", "RTX": "Industrials", "HON": "Industrials",
    "UPS": "Industrials", "DE": "Industrials",
    "XOM": "Energy", "CVX": "Energy", "SLB": "Energy",
    "SPY": "Market benchmark", "QQQ": "Market benchmark", "DIA": "Market benchmark",
}

COMPANY_NAMES = {
    "AAPL": "Apple Inc", "MSFT": "Microsoft", "NVDA": "NVIDIA", "GOOGL": "Alphabet A",
    "AMZN": "Amazon", "META": "Meta Platforms", "AVGO": "Broadcom", "ORCL": "Oracle",
    "CRM": "Salesforce", "AMD": "AMD", "QCOM": "Qualcomm", "INTC": "Intel",
    "CSCO": "Cisco", "ADBE": "Adobe", "IBM": "IBM",
    "JPM": "JPMorgan Chase", "BAC": "Bank of America", "GS": "Goldman Sachs", "MS": "Morgan Stanley",
    "V": "Visa", "MA": "Mastercard", "PYPL": "PayPal", "BRK-B": "Berkshire Hathaway B",
    "LLY": "Eli Lilly", "JNJ": "Johnson & Johnson", "UNH": "UnitedHealth Group",
    "ABBV": "AbbVie", "MRK": "Merck", "PFE": "Pfizer", "ISRG": "Intuitive Surgical",
    "WMT": "Walmart", "COST": "Costco", "HD": "Home Depot", "NKE": "Nike",
    "MCD": "McDonald's", "KO": "Coca-Cola", "PG": "Procter & Gamble", "DIS": "Walt Disney",
    "NFLX": "Netflix", "CAT": "Caterpillar", "GE": "GE Aerospace", "RTX": "RTX",
    "HON": "Honeywell", "UPS": "UPS", "DE": "Deere & Company",
    "XOM": "Exxon Mobil", "CVX": "Chevron", "SLB": "SLB",
    "SPY": "SPDR S&P 500 ETF", "QQQ": "Invesco Nasdaq-100 ETF", "DIA": "SPDR Dow Jones ETF",
}

APP_STYLE = """
<style>
  html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #ffffff;
    color: #131722;
    font-family: -apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, Ubuntu, sans-serif;
  }
  [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
  header[data-testid="stHeader"] { display: none !important; }
  div[data-testid="stDecoration"], div[data-testid="stToolbar"] { display: none !important; }
  .stAppDeployButton, #MainMenu, footer { display: none !important; }
  .block-container { padding-top: 1rem; padding-bottom: 2.2rem; max-width: 1440px; }
  div[data-testid="stMetric"] {
    background: #fff;
    border: 1px solid #e0e3eb;
    padding: 0.85rem 1rem;
    border-radius: 12px;
  }
  .topnav {
    display: flex;
    align-items: center;
    gap: 0.35rem 1.15rem;
    flex-wrap: wrap;
    min-height: 2.6rem;
    padding: 0.15rem 0 0.55rem 0;
  }
  .brand {
    font-size: 1.22rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    color: #131722;
    margin-right: 0.45rem;
  }
  .hero-title {
    font-size: 1.72rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin: 0.15rem 0 0.2rem 0;
    line-height: 1.2;
  }
  .hero-sub { color: #6a6d78; font-size: 0.98rem; margin: 0 0 0.85rem 0; }
  .index-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 0 0 1rem 0;
  }
  .index-card {
    border: 1px solid #e0e3eb;
    border-radius: 12px;
    padding: 0.9rem 1rem 0.85rem 1rem;
    background: #fff;
    min-height: 118px;
  }
  .index-card-top { display: flex; align-items: flex-start; gap: 0.7rem; }
  .idx-badge {
    width: 36px; height: 36px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    color: #fff; font-weight: 800; font-size: 0.7rem; flex: 0 0 36px;
    letter-spacing: -0.02em;
  }
  .idx-name { font-weight: 700; font-size: 0.98rem; line-height: 1.2; }
  .idx-ticker {
    display: inline-block; margin-left: 0.35rem; font-size: 0.75rem; font-weight: 700;
    color: #6a6d78; background: #f0f3fa; border-radius: 4px; padding: 0.05rem 0.35rem;
  }
  .idx-blurb { color: #6a6d78; font-size: 0.8rem; margin-top: 0.15rem; }
  .idx-quote { display: flex; justify-content: space-between; align-items: baseline; margin-top: 0.7rem; gap: 0.5rem; }
  .last-px { font-size: 1.28rem; font-weight: 700; font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
  .last-unit { color: #6a6d78; font-size: 0.78rem; font-weight: 600; margin-left: 0.25rem; }
  .chg-up { color: #089981; font-weight: 700; font-variant-numeric: tabular-nums; }
  .chg-down { color: #f23645; font-weight: 700; font-variant-numeric: tabular-nums; }
  .chg-flat { color: #6a6d78; font-weight: 600; }
  .quote-name { font-size: 1.28rem; font-weight: 700; letter-spacing: -0.02em; margin: 0; }
  .quote-ticker { color: #6a6d78; font-size: 0.95rem; font-weight: 700; margin-left: 0.4rem; }
  .quote-last { font-size: 1.55rem; font-weight: 700; font-variant-numeric: tabular-nums; letter-spacing: -0.03em; }
  .muted { color: #6a6d78; font-size: 0.88rem; }
  .small-note { font-size: 0.86rem; color: #6a6d78; }
  .wl-title { font-size: 1.05rem; font-weight: 700; margin: 0; }
  .section-label {
    font-size: 0.75rem; font-weight: 700; color: #6a6d78; letter-spacing: 0.04em;
    text-transform: uppercase; margin: 0.35rem 0 0.2rem 0;
  }
  .learn-card {
    border: 1px solid #e0e3eb; border-radius: 12px; padding: 1rem 1.1rem; background: #f7f8fa;
  }
  .learn-card h3 { margin: 0 0 0.4rem 0; font-size: 1.02rem; }
  .learn-card p, .learn-card li { color: #4c4f59; font-size: 0.92rem; }
  div.st-key-nav_pills [data-testid="stMarkdownContainer"] p { font-weight: 600; }
  div.st-key-nav_search [data-testid="stTextInputRootElement"] {
    border-radius: 24px;
    background: #f0f3fa;
    border: 1px solid #e0e3eb;
  }
  div.st-key-nav_search input { background: transparent; }
  .nav-rule { border: 0; border-top: 1px solid #e0e3eb; margin: 0.1rem 0 0.85rem 0; }
  div[class*="st-key-idx_"] button {
    min-height: 2rem !important;
    font-size: 0.8rem !important;
    padding: 0.15rem 0.45rem !important;
    border-radius: 8px !important;
  }
  div.st-key-chart_add button {
    min-height: 2rem !important;
    padding: 0.15rem 0.5rem !important;
    border-radius: 8px !important;
  }
  @media (max-width: 900px) {
    .index-grid { grid-template-columns: 1fr; }
    .hero-title { font-size: 1.4rem; }
    .block-container { padding-left: 0.8rem; padding-right: 0.8rem; }
  }
</style>
"""


def widget_key(prefix: str, ticker: str) -> str:
    return f"{prefix}_{ticker.replace('^', 'I').replace('-', '_')}"


def display_symbol(ticker: str) -> str:
    if ticker in INDEX_META:
        return INDEX_META[ticker]["display"]
    return ticker


def company_name(ticker: str) -> str:
    if ticker in INDEX_META:
        return INDEX_META[ticker]["name"]
    return COMPANY_NAMES.get(ticker, ticker)


def is_index(ticker: str) -> bool:
    return ticker in INDEX_META


def ticker_label(ticker: str) -> str:
    return f"{display_symbol(ticker)} · {company_name(ticker)}"


def format_last(ticker: str, value: float) -> str:
    if pd.isna(value):
        return "—"
    if is_index(ticker):
        return f"{value:,.2f}"
    return f"${value:,.2f}"


def format_chg(value: float, percent: bool = False) -> str:
    if pd.isna(value):
        return "—"
    if percent:
        return f"{value:+.2f}%"
    return f"{value:+.2f}"


def chg_class(value: float) -> str:
    if pd.isna(value) or value == 0:
        return "chg-flat"
    return "chg-up" if value > 0 else "chg-down"


def chg_arrow(value: float) -> str:
    if pd.isna(value) or value == 0:
        return ""
    return "↑" if value > 0 else "↓"


def money(value: float) -> str:
    if pd.isna(value):
        return "—"
    if abs(value) >= 1e12:
        return f"${value / 1e12:.2f}T"
    if abs(value) >= 1e9:
        return f"${value / 1e9:.2f}B"
    if abs(value) >= 1e6:
        return f"${value / 1e6:.2f}M"
    return f"${value:,.2f}"


def pct(value: float, digits: int = 2) -> str:
    return "—" if pd.isna(value) else f"{value:.{digits}f}%"


def to_new_york_time(value) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        return stamp.tz_localize("America/New_York")
    return stamp.tz_convert("America/New_York")


def estimated_us_session(now_et: pd.Timestamp) -> str:
    if now_et.weekday() >= 5:
        return "Weekend: the regular US session is usually closed"
    current_minutes = now_et.hour * 60 + now_et.minute
    if 4 * 60 <= current_minutes < 9 * 60 + 30:
        return "Pre-market (clock estimate)"
    if 9 * 60 + 30 <= current_minutes < 16 * 60:
        return "Regular session (clock estimate)"
    if 16 * 60 <= current_minutes < 20 * 60:
        return "After hours (clock estimate)"
    return "Outside the regular session"


@st.cache_data(ttl=900, show_spinner=False)
def download_prices(tickers: tuple[str, ...], period: str) -> pd.DataFrame:
    """Download daily adjusted OHLC data from Yahoo Finance via yfinance."""
    if not tickers:
        return pd.DataFrame(columns=["date", "ticker", "close", "volume"])

    raw = yf.download(
        tickers=list(tickers),
        period=period,
        interval="1d",
        auto_adjust=True,
        group_by="column",
        progress=False,
        threads=True,
        timeout=20,
    )
    if raw is None or raw.empty:
        return pd.DataFrame(columns=["date", "ticker", "close", "volume"])

    def extract_field(frame: pd.DataFrame, field: str) -> pd.DataFrame:
        if isinstance(frame.columns, pd.MultiIndex):
            if field in frame.columns.get_level_values(0):
                out = frame[field].copy()
            elif field in frame.columns.get_level_values(1):
                out = frame.xs(field, axis=1, level=1).copy()
            else:
                return pd.DataFrame(index=frame.index)
        else:
            if field not in frame.columns:
                return pd.DataFrame(index=frame.index)
            out = frame[[field]].copy()
            if len(tickers) == 1:
                out.columns = [tickers[0]]
        if isinstance(out, pd.Series):
            out = out.to_frame(name=tickers[0] if len(tickers) else field)
        return out

    close = extract_field(raw, "Close")
    volume = extract_field(raw, "Volume")
    if close.empty:
        return pd.DataFrame(columns=["date", "ticker", "close", "volume"])

    close_long = close.rename_axis(index="date", columns="ticker").stack(future_stack=True).rename("close").reset_index()
    if volume.empty:
        volume_long = pd.DataFrame(columns=["date", "ticker", "volume"])
    else:
        volume_long = volume.rename_axis(index="date", columns="ticker").stack(future_stack=True).rename("volume").reset_index()
    df = close_long.merge(volume_long, on=["date", "ticker"], how="left")
    df["ticker"] = df["ticker"].astype(str)
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert(None)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    df = df.dropna(subset=["close"]).sort_values(["ticker", "date"])
    return df.reset_index(drop=True)


@st.cache_data(ttl=15, show_spinner=False)
def download_intraday_one(ticker: str, interval: str, include_extended: bool) -> pd.DataFrame:
    data = yf.Ticker(ticker).history(
        period="1d",
        interval=interval,
        prepost=include_extended,
        auto_adjust=False,
        actions=False,
    )
    if data is None or data.empty:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    data = data.copy()
    required = ["Open", "High", "Low", "Close", "Volume"]
    for column in required:
        if column not in data.columns:
            data[column] = np.nan
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data[required].dropna(subset=["Close"]).sort_index()
    data = data.loc[~data.index.duplicated(keep="last")]
    return data


@st.cache_data(ttl=180, show_spinner=False)
def download_ohlc(ticker: str, period: str, interval: str) -> pd.DataFrame:
    try:
        data = yf.Ticker(ticker).history(
            period=period,
            interval=interval,
            auto_adjust=True,
            actions=False,
            prepost=False,
        )
    except Exception:
        return pd.DataFrame()
    if data is None or data.empty:
        if period == "1d":
            try:
                data = yf.Ticker(ticker).history(
                    period="5d",
                    interval=interval,
                    auto_adjust=True,
                    actions=False,
                    prepost=False,
                )
            except Exception:
                return pd.DataFrame()
        if data is None or data.empty:
            return pd.DataFrame()
        last_day = pd.Timestamp(data.index[-1]).date()
        data = data[pd.Series(data.index.date, index=data.index) == last_day]
    data = data.copy()
    for column in ["Open", "High", "Low", "Close", "Volume"]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    if "Close" not in data.columns:
        return pd.DataFrame()
    return data.dropna(subset=["Close"]).sort_index()


@st.cache_data(ttl=3600, show_spinner=False)
def get_ticker_info(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).get_info()
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


def snapshot_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if prices.empty:
        return pd.DataFrame(columns=["ticker", "last", "chg", "chg_pct", "as_of"])
    for ticker, group in prices.groupby("ticker"):
        g = group.sort_values("date").dropna(subset=["close"])
        if g.empty:
            continue
        last_close = float(g.iloc[-1]["close"])
        previous_close = float(g.iloc[-2]["close"]) if len(g) >= 2 else np.nan
        chg = last_close - previous_close if pd.notna(previous_close) else np.nan
        chg_pct = (chg / previous_close) * 100 if pd.notna(previous_close) and previous_close else np.nan
        rows.append({
            "ticker": str(ticker),
            "last": last_close,
            "chg": chg,
            "chg_pct": chg_pct,
            "as_of": g["date"].max().date(),
        })
    return pd.DataFrame(rows)


def calculate_metrics(prices: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ticker, group in prices.groupby("ticker"):
        g = group.sort_values("date").dropna(subset=["close"])
        if g.empty:
            continue
        close = g["close"].astype(float)
        returns = close.pct_change().dropna()
        first_price = float(close.iloc[0])
        last_price = float(close.iloc[-1])
        total_return = (last_price / first_price - 1) * 100 if first_price else np.nan
        volatility = returns.std(ddof=1) * np.sqrt(252) * 100 if len(returns) > 1 else np.nan
        drawdown = (close / close.cummax() - 1).min() * 100
        rows.append({
            "Ticker": ticker,
            "Group": UNIVERSE.get(ticker, "Other"),
            "Company": company_name(str(ticker)),
            "Last": last_price,
            "Period return (%)": total_return,
            "Ann. volatility (%)": volatility,
            "Max drawdown (%)": float(drawdown),
            "Avg volume": float(g["volume"].mean()) if g["volume"].notna().any() else np.nan,
            "Volume": float(g["volume"].iloc[-1]) if pd.notna(g["volume"].iloc[-1]) else np.nan,
            "From": g["date"].min().date(),
            "As of": g["date"].max().date(),
        })
    return pd.DataFrame(rows)


def make_monthly_sector_heatmap(prices: pd.DataFrame) -> go.Figure | None:
    temp = prices.copy()
    if temp.empty:
        return None
    temp["month"] = pd.to_datetime(temp["date"]).dt.to_period("M").dt.to_timestamp()
    month_ends = temp.sort_values("date").groupby(["ticker", "month"], as_index=False).tail(1)
    pivot = month_ends.pivot(index="ticker", columns="month", values="close").sort_index(axis=1)
    monthly_returns = pivot.pct_change(axis=1) * 100
    if monthly_returns.empty:
        return None
    monthly_returns = monthly_returns.iloc[:, 1:]
    monthly_returns["Group"] = [UNIVERSE.get(t, "Other") for t in monthly_returns.index]
    sect = monthly_returns.groupby("Group").mean(numeric_only=True)
    if sect.empty or sect.shape[1] == 0:
        return None
    labels = [pd.Timestamp(c).strftime("%Y-%m") for c in sect.columns]
    fig = go.Figure(data=go.Heatmap(
        z=sect.values,
        x=labels,
        y=sect.index.tolist(),
        colorscale="RdYlGn",
        zmid=0,
        colorbar={"title": "Monthly %"},
        hovertemplate="Group: %{y}<br>Month: %{x}<br>Avg return: %{z:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        title="Group monthly returns (equal-weighted inside each group)",
        xaxis_title="Month",
        yaxis_title="Group",
        height=420,
        margin=dict(l=10, r=10, t=60, b=10),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return fig


def restyle_chart(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=56, t=12, b=32),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        hovermode="x unified",
        showlegend=False,
        legend_title_text="",
        font=dict(color="#131722", size=12),
    )
    fig.update_xaxes(showgrid=False, linecolor="#e0e3eb", tickfont=dict(color="#6a6d78"))
    fig.update_yaxes(
        side="right",
        showgrid=True,
        gridcolor="#f0f3fa",
        linecolor="#ffffff",
        tickfont=dict(color="#6a6d78"),
        zeroline=False,
    )
    return fig


def build_price_chart(frame: pd.DataFrame, ticker: str, chart_type: str) -> go.Figure:
    fig = go.Figure()
    if frame.empty:
        return restyle_chart(fig, 430)
    y = frame["Close"].astype(float)
    up = bool(y.iloc[-1] >= y.iloc[0]) if len(y) else True
    line_color = "#089981" if up else "#f23645"
    fill_color = "rgba(8,153,129,0.14)" if up else "rgba(242,54,69,0.12)"
    if chart_type == "Candle" and {"Open", "High", "Low", "Close"}.issubset(frame.columns):
        fig.add_trace(go.Candlestick(
            x=frame.index,
            open=frame["Open"],
            high=frame["High"],
            low=frame["Low"],
            close=frame["Close"],
            name=display_symbol(ticker),
            increasing_line_color="#089981",
            decreasing_line_color="#f23645",
        ))
        fig.update_layout(xaxis_rangeslider_visible=False)
    else:
        ymin = float(y.min())
        ymax = float(y.max())
        pad = (ymax - ymin) * 0.08 if ymax > ymin else abs(ymin) * 0.01 or 1
        fig.add_trace(go.Scatter(
            x=frame.index, y=[ymin - pad] * len(frame),
            mode="lines",
            line=dict(width=0, color=fill_color),
            hoverinfo="skip", showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=frame.index,
            y=y,
            mode="lines",
            name=display_symbol(ticker),
            line=dict(color=line_color, width=2.2),
            fill="tonexty",
            fillcolor=fill_color,
        ))
        fig.update_yaxes(range=[ymin - pad, ymax + pad])
    unit = INDEX_META[ticker]["unit"].upper() if is_index(ticker) else "USD"
    fig.update_yaxes(title=unit)
    return restyle_chart(fig, 430)


def lookup_snapshot(snap: pd.DataFrame, ticker: str) -> dict:
    if snap is None or snap.empty:
        return {}
    hit = snap[snap["ticker"] == ticker]
    if hit.empty:
        return {}
    return hit.iloc[0].to_dict()


def go_to(nav: str, markets_tab: str | None = None, learn_tab: str | None = None) -> None:
    st.session_state.nav = nav
    if nav in TOP_NAV:
        st.session_state.nav_pills = nav
    if markets_tab:
        st.session_state.markets_tab = markets_tab
        st.session_state.markets_tab_persist = markets_tab
    if learn_tab:
        st.session_state.learn_tab = learn_tab
        st.session_state.learn_tab_persist = learn_tab


def add_to_watchlist(ticker: str) -> str:
    if ticker in INDEX_META:
        return f"{display_symbol(ticker)} already sits in Indices."
    current = list(st.session_state.get("watchlist", []))
    if ticker in current:
        return f"{ticker} is already on your watchlist."
    st.session_state.watchlist = current + [ticker]
    return f"Added {ticker} to Watchlist."


def remove_from_watchlist(ticker: str) -> None:
    st.session_state.watchlist = [t for t in st.session_state.get("watchlist", []) if t != ticker]


def normalize_query(query: str) -> str:
    return re.sub(r"[^A-Za-z0-9&]+", "", query).upper()


def resolve_search(query: str) -> dict:
    q = query.strip()
    if not q:
        return {"error": "Type a ticker or company name, for example AAPL or Apple."}
    compact = normalize_query(q)
    if compact in INDEX_ALIASES:
        return {"ticker": INDEX_ALIASES[compact]}
    upper = q.upper()
    if upper in UNIVERSE:
        return {"ticker": upper}
    lower = q.casefold()
    exact_name = next((t for t, name in COMPANY_NAMES.items() if name.casefold() == lower), None)
    if exact_name:
        return {"ticker": exact_name}
    matches = [
        t for t in UNIVERSE
        if upper in t.upper() or lower in COMPANY_NAMES.get(t, t).casefold()
    ]
    index_matches = [
        yahoo for yahoo, meta in INDEX_META.items()
        if lower in meta["name"].casefold() or lower in meta["display"].casefold()
    ]
    matches = list(dict.fromkeys(index_matches + matches))
    if len(matches) == 1:
        return {"ticker": matches[0]}
    if matches:
        return {"candidates": matches}
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9.-]{0,9}", q):
        return {"ticker": upper, "custom": True}
    return {"error": "No match in the starter list. Try a US ticker such as AAPL, MSFT, or SPX."}


def on_search_change() -> None:
    result = resolve_search(st.session_state.get("nav_search", ""))
    st.session_state.search_result = result
    if result.get("ticker"):
        st.session_state.selected_symbol = result["ticker"]


def bind_widget(key: str, persist_key: str, default) -> None:
    """Keep widget values after the widget unmounts on another page."""
    if persist_key not in st.session_state:
        st.session_state[persist_key] = default
    if key not in st.session_state:
        st.session_state[key] = st.session_state[persist_key]


def remember_chart_range() -> None:
    if st.session_state.get("chart_range"):
        st.session_state.chart_range_persist = st.session_state.chart_range


def remember_chart_type() -> None:
    if st.session_state.get("chart_type"):
        st.session_state.chart_type_persist = st.session_state.chart_type


def init_state() -> None:
    st.session_state.setdefault("nav", "Home")
    st.session_state.setdefault("markets_tab_persist", "Overview")
    st.session_state.setdefault("learn_tab_persist", "Start here")
    st.session_state.setdefault("selected_symbol", "AAPL")
    st.session_state.setdefault("chart_range_persist", "1D")
    st.session_state.setdefault("chart_type_persist", "Line")
    st.session_state.setdefault("watchlist", ["AAPL", "MCD"])
    st.session_state.setdefault("search_result", {})
    st.session_state.setdefault("flash", "")
    st.session_state.setdefault("analysis_period", "1y")


def render_top_nav() -> None:
    left, right = st.columns([3.6, 1.55], gap="large")
    with left:
        brand, pills = st.columns([1.15, 3.4])
        with brand:
            st.markdown('<div class="topnav"><div class="brand">StockScope</div></div>', unsafe_allow_html=True)
        with pills:
            if "nav_pills" not in st.session_state:
                st.session_state.nav_pills = st.session_state.nav if st.session_state.nav in TOP_NAV else "Home"
            picked = st.pills("Section", TOP_NAV, key="nav_pills", label_visibility="collapsed")
            if picked:
                st.session_state.nav = picked
    with right:
        st.text_input(
            "Search",
            placeholder="Search",
            label_visibility="collapsed",
            key="nav_search",
            on_change=on_search_change,
            help="Search a ticker or company in the starter list, or a main US index such as SPX.",
        )
    st.markdown('<hr class="nav-rule" />', unsafe_allow_html=True)

    result = st.session_state.get("search_result") or {}
    if result.get("error") and st.session_state.get("nav_search"):
        st.caption(result["error"])
    elif result.get("candidates"):
        pick_col, go_col = st.columns([4, 1])
        chosen = pick_col.selectbox(
            "Matches",
            options=result["candidates"],
            format_func=ticker_label,
            key="search_candidate_choice",
        )
        if go_col.button("Open", width="stretch"):
            st.session_state.selected_symbol = chosen
            st.session_state.search_result = {"ticker": chosen}
            st.rerun()
    if st.session_state.get("flash"):
        st.caption(st.session_state.flash)


def index_card_html(ticker: str, snap_row: dict) -> str:
    meta = INDEX_META[ticker]
    last = snap_row.get("last", np.nan)
    chg_pct = snap_row.get("chg_pct", np.nan)
    klass = chg_class(chg_pct)
    arrow = chg_arrow(chg_pct)
    last_text = "—" if pd.isna(last) else f"{last:,.2f}"
    chg_text = "—" if pd.isna(chg_pct) else f"{arrow} {abs(chg_pct):.2f}%"
    return (
        '<div class="index-card">'
        '<div class="index-card-top">'
        f'<div class="idx-badge" style="background:{meta["badge_bg"]}">{html.escape(meta["badge"])}</div>'
        "<div>"
        f'<div class="idx-name">{html.escape(meta["name"])}<span class="idx-ticker">{html.escape(meta["display"])}</span></div>'
        f'<div class="idx-blurb">{html.escape(meta["blurb"])}</div>'
        "</div></div>"
        '<div class="idx-quote">'
        f'<div class="last-px">{last_text}<span class="last-unit">{html.escape(meta["unit"])}</span></div>'
        f'<div class="{klass}">{chg_text}</div>'
        "</div></div>"
    )


def render_index_cards(snap: pd.DataFrame) -> None:
    cards = "".join(index_card_html(ticker, lookup_snapshot(snap, ticker)) for ticker in INDEX_ORDER)
    st.markdown(f'<div class="index-grid">{cards}</div>', unsafe_allow_html=True)
    actions = st.columns(3)
    labels = {
        "^GSPC": "Chart S&P 500",
        "^NDX": "Chart NASDAQ 100",
        "^DJI": "Chart Dow Jones",
    }
    for col, ticker in zip(actions, INDEX_ORDER):
        if col.button(labels[ticker], key=widget_key("idx_focus", ticker), type="secondary", width="stretch"):
            st.session_state.selected_symbol = ticker
            st.rerun()


def watchlist_frame(tickers: Iterable[str], snap: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ticker in tickers:
        row = lookup_snapshot(snap, ticker)
        rows.append({
            "Symbol": display_symbol(ticker),
            "Last": row.get("last", np.nan),
            "Chg": row.get("chg", np.nan),
            "Chg%": row.get("chg_pct", np.nan),
            "ticker": ticker,
        })
    return pd.DataFrame(rows)


def style_watchlist(df: pd.DataFrame) -> pd.DataFrame:
    def fmt_last(value) -> str:
        return "—" if pd.isna(value) else f"{value:,.2f}"

    def fmt_chg(value) -> str:
        return "—" if pd.isna(value) else f"{value:+.2f}"

    def fmt_pct(value) -> str:
        return "—" if pd.isna(value) else f"{value:+.2f}%"

    return pd.DataFrame({
        "Symbol": df["Symbol"],
        "Last": df["Last"].map(fmt_last),
        "Chg": df["Chg"].map(fmt_chg),
        "Chg%": df["Chg%"].map(fmt_pct),
    })


def handle_watchlist_selection(event, table: pd.DataFrame) -> None:
    rows = event.selection.rows if event and getattr(event, "selection", None) else []
    if not rows or table.empty:
        return
    idx = rows[0]
    if 0 <= idx < len(table):
        st.session_state.selected_symbol = str(table.iloc[idx]["ticker"])


def render_watchlist_panel(snap: pd.DataFrame, *, show_remove: bool = False) -> None:
    head_l, head_r = st.columns([3, 1])
    with head_l:
        st.markdown('<p class="wl-title">Watchlist</p>', unsafe_allow_html=True)
    with head_r:
        with st.popover("＋"):
            add_query = st.text_input("Add ticker", placeholder="MCD", key="wl_add_query")
            if st.button("Add symbol", key="wl_add_btn", width="stretch"):
                resolved = resolve_search(add_query)
                if resolved.get("ticker"):
                    st.session_state.flash = add_to_watchlist(resolved["ticker"])
                    st.rerun()
                else:
                    st.session_state.flash = resolved.get("error", "Could not add that symbol.")
                    st.rerun()

    st.markdown('<div class="section-label">Indices</div>', unsafe_allow_html=True)
    idx_table = watchlist_frame(INDEX_ORDER, snap)
    idx_event = st.dataframe(
        style_watchlist(idx_table),
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="wl_indices",
        height=52 + 36 * len(INDEX_ORDER),
    )
    handle_watchlist_selection(idx_event, idx_table)

    st.markdown('<div class="section-label">Stocks</div>', unsafe_allow_html=True)
    stocks = [t for t in st.session_state.get("watchlist", []) if t not in INDEX_META]
    if not stocks:
        st.caption("No stocks yet. Use ＋ to add a beginner-friendly name such as AAPL.")
    else:
        stock_table = watchlist_frame(stocks, snap)
        stock_event = st.dataframe(
            style_watchlist(stock_table),
            width="stretch",
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="wl_stocks",
            height=52 + 36 * max(len(stocks), 1),
        )
        handle_watchlist_selection(stock_event, stock_table)
        if show_remove:
            drop = st.selectbox("Remove", options=["—"] + stocks, format_func=lambda t: ticker_label(t) if t != "—" else "—")
            if drop != "—" and st.button("Remove from watchlist"):
                remove_from_watchlist(drop)
                st.rerun()
    st.caption("Click a row to show it on the chart. Quotes via Yahoo Finance; they may be delayed.")


def render_home() -> None:
    st.markdown(
        '<div class="hero-title">Stock market for beginner.</div>'
        '<p class="hero-sub">US stock market main indices</p>',
        unsafe_allow_html=True,
    )

    selected = st.session_state.selected_symbol
    needed = tuple(dict.fromkeys([*INDEX_ORDER, *st.session_state.get("watchlist", []), selected]))
    with st.spinner("Updating quotes…"):
        try:
            prices = download_prices(needed, "5d")
        except Exception:
            prices = pd.DataFrame()
    snap = snapshot_from_prices(prices)
    render_index_cards(snap)

    chart_col, list_col = st.columns([2.35, 1], gap="large")
    with chart_col:
        render_selected_chart(selected, snap)
    with list_col:
        render_watchlist_panel(snap, show_remove=False)


def render_selected_chart(ticker: str, snap: pd.DataFrame) -> None:
    quote = lookup_snapshot(snap, ticker)
    title_l, type_col, help_col, add_col = st.columns([3.2, 1.45, 0.8, 0.9])
    with title_l:
        st.markdown(
            f'<p class="quote-name">{html.escape(company_name(ticker))}'
            f'<span class="quote-ticker">{html.escape(display_symbol(ticker))}</span></p>',
            unsafe_allow_html=True,
        )
    with type_col:
        bind_widget("chart_type", "chart_type_persist", "Line")
        st.segmented_control(
            "Chart type",
            options=["Line", "Candle"],
            key="chart_type",
            on_change=remember_chart_type,
        )
    with help_col:
        with st.popover("Help"):
            st.markdown(
                """
                **How to read this chart**
                - **1D / 5D** use intraday bars; longer ranges use daily or weekly closes.
                - The big number is the latest close Yahoo returned, not a guaranteed live print.
                - Green means up versus the previous close; red means down.
                - This dashboard is a class prototype, not trading software.
                """
            )
    with add_col:
        if st.button("Add ＋", key="chart_add", help="Add this symbol to Watchlist", type="secondary"):
            st.session_state.flash = add_to_watchlist(ticker)
            st.rerun()

    last = quote.get("last", np.nan)
    chg = quote.get("chg", np.nan)
    chg_pct = quote.get("chg_pct", np.nan)
    unit = INDEX_META[ticker]["unit"].upper() if is_index(ticker) else "USD"
    last_html = "—" if pd.isna(last) else (
        f"{last:,.2f}" if is_index(ticker) else f"${last:,.2f}"
    )
    st.markdown(
        f'<div class="quote-last">{last_html} <span class="last-unit">{html.escape(unit)}</span> '
        f'<span class="{chg_class(chg_pct)}">{html.escape(format_chg(chg))} {html.escape(format_chg(chg_pct, True))}</span></div>',
        unsafe_allow_html=True,
    )

    bind_widget("chart_range", "chart_range_persist", "1D")
    st.pills(
        "Range",
        list(CHART_RANGES.keys()),
        key="chart_range",
        on_change=remember_chart_range,
        label_visibility="collapsed",
    )

    range_key = st.session_state.get("chart_range") or st.session_state.get("chart_range_persist") or "1D"
    if range_key not in CHART_RANGES:
        range_key = "1D"
    spec = CHART_RANGES[range_key]
    with st.spinner("Loading chart…"):
        series = download_ohlc(ticker, spec["period"], spec["interval"])
    if series.empty:
        st.info("No bars for this range yet. Markets may be closed, or Yahoo did not return data.")
    else:
        fig = build_price_chart(
            series,
            ticker,
            st.session_state.get("chart_type") or st.session_state.get("chart_type_persist") or "Line",
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        as_of = pd.Timestamp(series.index[-1])
        st.caption(f"Range {range_key} · last bar {as_of} · data via Yahoo Finance / yfinance.")
    if st.button("Open stock details"):
        go_to("Markets", markets_tab="Stock")
        st.rerun()


def load_universe(period: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    with st.spinner("Loading the starter universe from Yahoo Finance…"):
        try:
            prices = download_prices(tuple(UNIVERSE.keys()), period)
            error = ""
        except Exception as exc:
            prices = pd.DataFrame()
            error = str(exc)
    metrics = calculate_metrics(prices) if not prices.empty else pd.DataFrame()
    if not prices.empty:
        daily = snapshot_from_prices(prices).rename(columns={
            "ticker": "Ticker", "chg_pct": "Day chg (%)", "last": "Last close",
        })
        if not metrics.empty:
            metrics = metrics.drop(columns=["Last"], errors="ignore").merge(
                daily[["Ticker", "Last close", "Day chg (%)"]],
                on="Ticker",
                how="left",
            )
            metrics = metrics.rename(columns={"Last close": "Last"})
    return prices, metrics, error


def remember_markets_tab() -> None:
    if st.session_state.get("markets_tab"):
        st.session_state.markets_tab_persist = st.session_state.markets_tab


def render_markets() -> None:
    bind_widget("markets_tab", "markets_tab_persist", "Overview")
    st.segmented_control("Markets", options=MARKET_TABS, key="markets_tab", on_change=remember_markets_tab)
    tab = st.session_state.markets_tab

    if tab == "Live quotes":
        render_live_quotes()
        return
    if tab == "Stock":
        render_stock_details()
        return

    period = st.selectbox(
        "Look-back window",
        options=list(PERIOD_LABELS.keys()),
        format_func=lambda x: PERIOD_LABELS[x],
        key="analysis_period",
    )
    sector_options = ["All groups"] + sorted(set(UNIVERSE.values()))
    selected_sector = st.selectbox("Group filter", options=sector_options, index=0)

    prices, metrics, load_error = load_universe(period)
    if prices.empty:
        st.error("Could not load daily history. Check the network or Yahoo Finance, then retry.")
        if load_error:
            st.code(load_error)
        return

    if selected_sector != "All groups":
        metrics_view = metrics[metrics["Group"] == selected_sector].copy()
        active_tickers = [t for t, s in UNIVERSE.items() if s == selected_sector]
    else:
        metrics_view = metrics.copy()
        active_tickers = list(UNIVERSE.keys())
    prices_active = prices[prices["ticker"].isin(active_tickers)].copy()

    if tab == "Overview":
        render_overview(prices, prices_active, metrics, metrics_view, period)
    elif tab == "Screener":
        render_screener(metrics_view)
    elif tab == "Returns & risk":
        render_risk(prices, metrics, period)


def render_overview(
    prices: pd.DataFrame,
    prices_active: pd.DataFrame,
    metrics: pd.DataFrame,
    metrics_view: pd.DataFrame,
    period: str,
) -> None:
    latest_date = prices["date"].max().date()
    loaded_tickers = prices["ticker"].nunique()
    positive_share = (metrics["Period return (%)"] > 0).mean() * 100 if not metrics.empty else np.nan
    median_vol = metrics["Ann. volatility (%)"].median() if not metrics.empty else np.nan
    mean_return = metrics["Period return (%)"].mean() if not metrics.empty else np.nan

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Symbols loaded", f"{loaded_tickers}", help="Starter watch universe, not the whole US market.")
    k2.metric(f"Average return · {PERIOD_LABELS[period]}", pct(mean_return))
    k3.metric("Share with a positive return", pct(positive_share))
    k4.metric("Median annualized volatility", pct(median_vol))
    st.caption(f"As of {latest_date} · {PERIOD_LABELS[period]} · {len(UNIVERSE)} starter symbols")

    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        fig_heat = make_monthly_sector_heatmap(prices_active)
        if fig_heat is not None:
            st.plotly_chart(fig_heat, width="stretch", config={"displayModeBar": False})
        else:
            st.info("Not enough history in this window to draw the monthly heatmap.")
    with right:
        ranked = metrics_view.sort_values("Period return (%)", ascending=False).head(15)
        fig_rank = px.bar(
            ranked.sort_values("Period return (%)"),
            x="Period return (%)", y="Ticker", color="Period return (%)",
            color_continuous_scale="RdYlGn", orientation="h",
            hover_data={"Group": True, "Ann. volatility (%)": ":.2f", "Max drawdown (%)": ":.2f"},
            title="Top 15 in this window",
        )
        fig_rank.update_layout(
            height=420, coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=60, b=10),
            yaxis_title="", xaxis_title="Period return (%)",
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        )
        st.plotly_chart(fig_rank, width="stretch", config={"displayModeBar": False})

    st.subheader("Today's movers in the starter list")
    stocks_only = metrics[~metrics["Ticker"].isin(["SPY", "QQQ", "DIA"])].copy()
    valid_daily = stocks_only["Day chg (%)"].dropna() if "Day chg (%)" in stocks_only.columns else pd.Series(dtype=float)
    breadth = st.columns(4)
    breadth[0].metric("Stocks watched", f"{len(stocks_only)}")
    breadth[1].metric("Up", f"{int((valid_daily > 0).sum())}")
    breadth[2].metric("Down", f"{int((valid_daily < 0).sum())}")
    breadth[3].metric("Flat", f"{int((valid_daily == 0).sum())}")

    movers_left, movers_right = st.columns(2, gap="large")
    with movers_left:
        if "Day chg (%)" in stocks_only.columns:
            gainers = stocks_only.dropna(subset=["Day chg (%)"]).nlargest(10, "Day chg (%)")
        else:
            gainers = pd.DataFrame()
        if not gainers.empty:
            fig_gainers = px.bar(
                gainers.sort_values("Day chg (%)"),
                x="Day chg (%)", y="Ticker", orientation="h",
                color="Day chg (%)", color_continuous_scale="RdYlGn",
                hover_data={"Company": True, "Last": ":.2f"},
                title="Gainers · top 10",
            )
            fig_gainers.update_layout(
                height=390, showlegend=False, coloraxis_showscale=False,
                xaxis_title="Day change (%)", yaxis_title="",
                margin=dict(l=5, r=5, t=55, b=5),
                paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            )
            st.plotly_chart(fig_gainers, width="stretch", config={"displayModeBar": False})
        else:
            st.info("Not enough data for a gainer list.")
    with movers_right:
        if "Day chg (%)" in stocks_only.columns:
            losers = stocks_only.dropna(subset=["Day chg (%)"]).nsmallest(10, "Day chg (%)")
        else:
            losers = pd.DataFrame()
        if not losers.empty:
            fig_losers = px.bar(
                losers.sort_values("Day chg (%)", ascending=False),
                x="Day chg (%)", y="Ticker", orientation="h",
                color="Day chg (%)", color_continuous_scale="RdYlGn",
                hover_data={"Company": True, "Last": ":.2f"},
                title="Losers · bottom 10",
            )
            fig_losers.update_layout(
                height=390, showlegend=False, coloraxis_showscale=False,
                xaxis_title="Day change (%)", yaxis_title="",
                margin=dict(l=5, r=5, t=55, b=5),
                paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            )
            st.plotly_chart(fig_losers, width="stretch", config={"displayModeBar": False})
        else:
            st.info("Not enough data for a loser list.")

    st.markdown("#### Volume leaders")
    volume_rank = stocks_only.dropna(subset=["Volume"]).nlargest(10, "Volume")
    if not volume_rank.empty:
        fig_volume_rank = px.bar(
            volume_rank.sort_values("Volume"),
            x="Volume", y="Ticker", orientation="h",
            color="Day chg (%)" if "Day chg (%)" in volume_rank.columns else None,
            color_continuous_scale="RdYlGn",
            hover_data={"Company": True, "Last": ":.2f"},
            title="Highest volume in the latest session",
        )
        fig_volume_rank.update_layout(
            height=410, xaxis_title="Shares", yaxis_title="",
            margin=dict(l=5, r=5, t=55, b=5), coloraxis_showscale=False,
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        )
        st.plotly_chart(fig_volume_rank, width="stretch", config={"displayModeBar": False})

    st.subheader("Starter universe")
    table_cols = ["Ticker", "Company", "Group", "Last", "Period return (%)", "Ann. volatility (%)", "Max drawdown (%)", "Avg volume", "Volume", "As of"]
    display_metrics = metrics_view.sort_values("Period return (%)", ascending=False)
    display_metrics = display_metrics[[c for c in table_cols if c in display_metrics.columns]]
    st.dataframe(
        display_metrics,
        width="stretch",
        hide_index=True,
        column_config={
            "Last": st.column_config.NumberColumn(format="$%.2f"),
            "Period return (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Ann. volatility (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Max drawdown (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Avg volume": st.column_config.NumberColumn(format="%.0f"),
            "Volume": st.column_config.NumberColumn(format="%.0f"),
        },
    )
    st.download_button(
        "Download this table as CSV",
        data=display_metrics.to_csv(index=False).encode("utf-8-sig"),
        file_name="stockscope_universe.csv",
        mime="text/csv",
    )


def render_screener(metrics_view: pd.DataFrame) -> None:
    st.subheader("Narrow the starter list by return and risk")
    fc1, fc2, fc3 = st.columns(3)
    min_return = fc1.slider("Minimum period return (%)", min_value=-100, max_value=200, value=-100, step=5)
    max_vol = fc2.slider("Maximum annualized volatility (%)", min_value=0, max_value=150, value=150, step=5)
    sort_by = fc3.selectbox(
        "Sort by",
        ["Period return (%)", "Ann. volatility (%)", "Max drawdown (%)", "Avg volume"],
        index=0,
    )
    filtered = metrics_view[
        (metrics_view["Period return (%)"].fillna(-999) >= min_return)
        & (metrics_view["Ann. volatility (%)"].fillna(999) <= max_vol)
    ].copy()
    ascending = sort_by in ["Ann. volatility (%)", "Max drawdown (%)"]
    filtered = filtered.sort_values(sort_by, ascending=ascending)
    st.write(f"Symbols that match: **{len(filtered)}**")
    st.dataframe(
        filtered,
        width="stretch",
        hide_index=True,
        column_config={
            "Last": st.column_config.NumberColumn(format="$%.2f"),
            "Day chg (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Period return (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Ann. volatility (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Max drawdown (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Avg volume": st.column_config.NumberColumn(format="%.0f"),
            "Volume": st.column_config.NumberColumn(format="%.0f"),
        },
    )
    st.download_button(
        "Download screener CSV",
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="stockscope_filtered_stocks.csv",
        mime="text/csv",
    )
    st.markdown(
        "**What the numbers mean:** period return uses the first and last valid close in the window; "
        "annualized volatility is the daily-return standard deviation × √252; "
        "max drawdown is the worst drop from a peak close."
    )


def render_risk(prices: pd.DataFrame, metrics: pd.DataFrame, period: str) -> None:
    st.subheader("Compare return and volatility")
    default = [t for t in ["AAPL", "MSFT", "NVDA", "SPY"] if t in UNIVERSE]
    compare_tickers = st.multiselect(
        "Symbols to compare",
        options=list(UNIVERSE.keys()),
        default=default,
        format_func=ticker_label,
        help="Up to about eight names keeps the chart readable.",
    )
    if not compare_tickers:
        st.info("Pick at least one symbol.")
        return
    compare_data = prices[prices["ticker"].isin(compare_tickers)].copy()
    if compare_data.empty:
        st.warning("No history for those symbols in this window.")
        return
    normalized = compare_data.sort_values("date").copy()
    normalized["Indexed (start = 100)"] = normalized.groupby("ticker")["close"].transform(
        lambda s: s / s.dropna().iloc[0] * 100 if not s.dropna().empty else s
    )
    fig_line = px.line(
        normalized, x="date", y="Indexed (start = 100)", color="ticker",
        title=f"Indexed price · {PERIOD_LABELS[period]}",
        labels={"date": "Date", "ticker": "Ticker"},
    )
    fig_line.update_layout(height=470, hovermode="x unified", yaxis_title="Indexed price", xaxis_title="Date")
    fig_line.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
    st.plotly_chart(fig_line, width="stretch", config={"displayModeBar": False})
    scat = metrics[metrics["Ticker"].isin(compare_tickers)].copy()
    if not scat.empty:
        fig_scatter = px.scatter(
            scat, x="Ann. volatility (%)", y="Period return (%)", color="Group", text="Ticker",
            hover_data={"Last": ":.2f", "Max drawdown (%)": ":.2f", "Avg volume": ":,.0f"},
            title="Return vs risk",
        )
        fig_scatter.update_traces(textposition="top center", marker={"size": 12, "opacity": 0.8})
        fig_scatter.update_layout(
            height=450, xaxis_title="Ann. volatility (%)", yaxis_title="Period return (%)",
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        )
        st.plotly_chart(fig_scatter, width="stretch", config={"displayModeBar": False})
    st.caption("Past return and volatility describe history. They are not a forecast.")


def render_stock_details() -> None:
    options = list(dict.fromkeys([
        st.session_state.selected_symbol,
        *INDEX_ORDER,
        *UNIVERSE.keys(),
    ]))
    if st.session_state.selected_symbol not in options:
        options.insert(0, st.session_state.selected_symbol)
    focus = st.selectbox(
        "Symbol",
        options=options,
        format_func=ticker_label,
        index=options.index(st.session_state.selected_symbol) if st.session_state.selected_symbol in options else 0,
        key="stock_focus",
    )
    st.session_state.selected_symbol = focus
    st.subheader(f"{company_name(focus)} · {display_symbol(focus)}")
    st.caption(UNIVERSE.get(focus, INDEX_META.get(focus, {}).get("blurb", "Custom symbol")))

    period = st.selectbox("History window", options=list(PERIOD_LABELS.keys()), index=3, format_func=lambda x: PERIOD_LABELS[x], key="stock_period")
    with st.spinner("Loading this symbol…"):
        one_prices = download_prices((focus,), period)
        series = download_ohlc(focus, period, "1d")
    if one_prices.empty and series.empty:
        st.warning("Yahoo did not return history for this symbol.")
        return
    metrics = calculate_metrics(one_prices) if not one_prices.empty else pd.DataFrame()
    m = metrics.iloc[0] if not metrics.empty else pd.Series(dtype=object)
    a, b, c, dcol = st.columns(4)
    a.metric("Last close", format_last(focus, m.get("Last", np.nan)))
    b.metric("Period return", pct(m.get("Period return (%)", np.nan)))
    c.metric("Ann. volatility", pct(m.get("Ann. volatility (%)", np.nan)))
    dcol.metric("Max drawdown", pct(m.get("Max drawdown (%)", np.nan)))

    if not series.empty:
        price_fig = build_price_chart(series, focus, "Line")
        price_fig.update_layout(title=f"{display_symbol(focus)} close")
        st.plotly_chart(price_fig, width="stretch", config={"displayModeBar": False})
        if "Volume" in series.columns:
            vol_fig = px.bar(series.reset_index(), x=series.reset_index().columns[0], y="Volume", title=f"{display_symbol(focus)} volume")
            vol_fig.update_layout(height=300, paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", xaxis_title="Date", yaxis_title="Shares")
            st.plotly_chart(vol_fig, width="stretch", config={"displayModeBar": False})

    add_col, live_col = st.columns(2)
    if add_col.button("Add to watchlist", width="stretch"):
        st.session_state.flash = add_to_watchlist(focus)
        st.rerun()
    if live_col.button("Open live quotes", width="stretch"):
        go_to("Markets", markets_tab="Live quotes")
        st.rerun()

    with st.expander("Optional Yahoo fundamentals (often incomplete)", expanded=False):
        with st.spinner("Reading fundamentals…"):
            info = get_ticker_info(focus)
        fundamental_fields = [
            ("marketCap", "Market cap", money),
            ("trailingPE", "P/E (TTM)", lambda x: f"{x:.2f}x" if pd.notna(x) else "—"),
            ("forwardPE", "Forward P/E", lambda x: f"{x:.2f}x" if pd.notna(x) else "—"),
            ("priceToBook", "Price / book", lambda x: f"{x:.2f}x" if pd.notna(x) else "—"),
            ("revenueGrowth", "Revenue growth", lambda x: pct(x * 100) if pd.notna(x) else "—"),
            ("profitMargins", "Profit margin", lambda x: pct(x * 100) if pd.notna(x) else "—"),
            ("returnOnEquity", "Return on equity", lambda x: pct(x * 100) if pd.notna(x) else "—"),
            ("totalRevenue", "Revenue", money),
            ("freeCashflow", "Free cash flow", money),
            ("fiftyTwoWeekHigh", "52-week high", lambda x: f"${x:,.2f}" if pd.notna(x) else "—"),
            ("fiftyTwoWeekLow", "52-week low", lambda x: f"${x:,.2f}" if pd.notna(x) else "—"),
        ]
        if not info:
            st.warning("Yahoo did not return fundamentals. Price and volume still work.")
        else:
            fundamental_rows = []
            for key, label, formatter in fundamental_fields:
                value = info.get(key)
                try:
                    val_num = float(value) if value is not None else np.nan
                    shown = formatter(val_num)
                except (ValueError, TypeError):
                    shown = "—"
                fundamental_rows.append({"Field": label, "Value": shown})
            st.dataframe(pd.DataFrame(fundamental_rows), width="stretch", hide_index=True)
            st.caption("Confirm anything important in company filings. Yahoo fields vary by name and update schedule.")


def render_live_quotes() -> None:
    st.subheader("Live quotes")
    st.markdown("Intraday bars for one symbol, plus a short watchlist. This is a classroom feed, not an execution quote.")

    universe_options = list(dict.fromkeys([st.session_state.selected_symbol, *UNIVERSE.keys()]))
    default_live = st.session_state.selected_symbol if st.session_state.selected_symbol in universe_options else "AAPL"
    live_controls = st.columns([1.5, 1, 1.2, 1.4, 1.1])
    live_ticker = live_controls[0].selectbox(
        "Symbol",
        options=universe_options,
        index=universe_options.index(default_live) if default_live in universe_options else 0,
        format_func=ticker_label,
        key="live_ticker",
    )
    st.session_state.selected_symbol = live_ticker
    live_interval = live_controls[1].selectbox(
        "Bar size",
        options=["1m", "5m", "15m", "30m", "60m"],
        index=0,
        format_func=lambda x: {"1m": "1 min", "5m": "5 min", "15m": "15 min", "30m": "30 min", "60m": "60 min"}[x],
        key="live_interval",
    )
    refresh_label = live_controls[2].selectbox(
        "Auto refresh",
        options=["Manual", "Every 15s", "Every 30s", "Every 60s"],
        index=2,
        key="live_refresh_mode",
    )
    refresh_seconds = {"Manual": None, "Every 15s": 15, "Every 30s": 30, "Every 60s": 60}[refresh_label]
    include_extended = live_controls[3].checkbox("Include pre/post", value=True, key="live_extended")
    if live_controls[4].button("↻ Refresh now", width="stretch", key="live_force_refresh"):
        download_intraday_one.clear()
        st.rerun()

    default_watch = [t for t in st.session_state.get("watchlist", ["AAPL", "MCD"]) if t in UNIVERSE][:6]
    live_watchlist = st.multiselect(
        "Also watch (keep to six names to limit requests)",
        options=list(UNIVERSE.keys()),
        default=default_watch,
        format_func=ticker_label,
        key="live_watchlist",
        help="Each row is the latest returned minute bar, not a time-and-sales print.",
    )
    interval_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "60m": 60}
    st.info(
        "Refresh is how often this app asks again. It is not a promise of a live or 15-minute-delayed feed. "
        "Yahoo / yfinance can lag, skip bars, or throttle."
    )

    @st.fragment(run_every=refresh_seconds)
    def render_live_monitor(selected_symbol: str, selected_interval: str, extended: bool, watchlist_symbols: list[str]):
        now_et = pd.Timestamp.now(tz="America/New_York")
        st.caption(
            f"New York time: {now_et.strftime('%Y-%m-%d %H:%M:%S %Z')} · "
            f"{estimated_us_session(now_et)} · auto refresh: {refresh_label}. "
            "The session label does not check exchange holidays."
        )
        try:
            intraday = download_intraday_one(selected_symbol, selected_interval, extended)
        except Exception as exc:
            st.error("Could not load minute bars. Network, Yahoo, or rate limits are the usual causes.")
            with st.expander("Technical error"):
                st.code(str(exc))
            intraday = pd.DataFrame()

        if intraday.empty:
            st.warning(
                f"{selected_symbol} did not return {selected_interval} bars. "
                "If the US session is closed, wait for the next trading day, or turn off pre/post and retry."
            )
        else:
            valid = intraday.dropna(subset=["Close"]).copy()
            last = valid.iloc[-1]
            last_ts_et = to_new_york_time(valid.index[-1])
            age_minutes = (now_et - last_ts_et).total_seconds() / 60
            prev_close = float(valid["Close"].iloc[-2]) if len(valid) >= 2 and pd.notna(valid["Close"].iloc[-2]) else np.nan
            last_close = float(last["Close"])
            bar_change = ((last_close / prev_close) - 1) * 100 if pd.notna(prev_close) and prev_close else np.nan
            last_volume = float(last["Volume"]) if pd.notna(last["Volume"]) else np.nan
            stale_threshold = max(3.0, interval_minutes[selected_interval] * 2.0)
            if age_minutes < 0:
                status_text = "Latest bar timestamp is slightly ahead of this clock; check again on the next refresh"
            elif age_minutes <= stale_threshold:
                status_text = "Latest bar timestamp is close to now (not a live-data guarantee)"
            else:
                status_text = "Latest bar looks stale; the session may be closed or the feed may have paused"
            st.caption(
                f"{status_text} · bar time {last_ts_et.strftime('%Y-%m-%d %H:%M:%S %Z')} · "
                f"about {age_minutes:.1f} minutes from this clock."
            )
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Last returned price", f"${last_close:,.2f}", help="Close of the minute bar, not a trade print.")
            m2.metric("Vs previous bar", f"{bar_change:+.2f}%" if pd.notna(bar_change) else "—")
            m3.metric("Bar volume", f"{last_volume:,.0f}" if pd.notna(last_volume) else "—")
            m4.metric("Bars returned", f"{len(valid):,}")

            chart_left, chart_right = st.columns([1.6, 1], gap="large")
            with chart_left:
                candle = go.Figure(data=[go.Candlestick(
                    x=valid.index,
                    open=valid["Open"], high=valid["High"], low=valid["Low"], close=valid["Close"],
                    name=selected_symbol,
                    increasing_line_color="#089981",
                    decreasing_line_color="#f23645",
                )])
                candle.update_layout(
                    title=f"{selected_symbol} · {selected_interval} bars",
                    xaxis_title="Time (as returned by Yahoo)",
                    yaxis_title="USD",
                    xaxis_rangeslider_visible=False,
                )
                st.plotly_chart(restyle_chart(candle, 480), width="stretch", config={"displayModeBar": False})
            with chart_right:
                volume_figure = go.Figure(data=[go.Bar(x=valid.index, y=valid["Volume"], name="Volume", marker_color="#2962ff")])
                volume_figure.update_layout(title="Volume per bar", xaxis_title="Time", yaxis_title="Shares")
                st.plotly_chart(restyle_chart(volume_figure, 480), width="stretch", config={"displayModeBar": False})

            with st.expander("Latest minute rows", expanded=False):
                detail = valid.tail(30).copy()
                detail.index.name = "Time"
                st.dataframe(detail.sort_index(ascending=False), width="stretch")
                st.download_button(
                    "Download minute CSV",
                    data=detail.reset_index().to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"{selected_symbol}_{selected_interval}_intraday.csv",
                    mime="text/csv",
                    key=f"download_live_{selected_symbol}_{selected_interval}",
                )

        st.markdown("### Watchlist bars")
        if not watchlist_symbols:
            st.info("Pick at least one extra symbol above.")
        else:
            records = []
            symbols = list(dict.fromkeys(watchlist_symbols[:6]))
            for symbol in symbols:
                try:
                    bars = download_intraday_one(symbol, selected_interval, extended)
                    if bars.empty:
                        records.append({
                            "Ticker": symbol, "Company": COMPANY_NAMES.get(symbol, symbol),
                            "Last": np.nan, "Bar chg (%)": np.nan, "Bar volume": np.nan,
                            "Bar time (ET)": "No data", "Age (min)": np.nan, "Status": "No data",
                        })
                        continue
                    bars = bars.dropna(subset=["Close"]).sort_index()
                    latest = bars.iloc[-1]
                    latest_time = to_new_york_time(bars.index[-1])
                    now = pd.Timestamp.now(tz="America/New_York")
                    age = (now - latest_time).total_seconds() / 60
                    previous = float(bars["Close"].iloc[-2]) if len(bars) >= 2 else np.nan
                    change = (float(latest["Close"]) / previous - 1) * 100 if pd.notna(previous) and previous else np.nan
                    status = "Fresh timestamp" if 0 <= age <= max(3, interval_minutes[selected_interval] * 2) else "Check update status"
                    records.append({
                        "Ticker": symbol,
                        "Company": COMPANY_NAMES.get(symbol, symbol),
                        "Last": float(latest["Close"]),
                        "Bar chg (%)": change,
                        "Bar volume": float(latest["Volume"]) if pd.notna(latest["Volume"]) else np.nan,
                        "Bar time (ET)": latest_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                        "Age (min)": age,
                        "Status": status,
                    })
                except Exception as exc:
                    records.append({
                        "Ticker": symbol, "Company": COMPANY_NAMES.get(symbol, symbol),
                        "Last": np.nan, "Bar chg (%)": np.nan, "Bar volume": np.nan,
                        "Bar time (ET)": "Request failed", "Age (min)": np.nan, "Status": str(exc)[:80],
                    })
            quote_table = pd.DataFrame(records)
            st.dataframe(
                quote_table,
                width="stretch",
                hide_index=True,
                column_config={
                    "Last": st.column_config.NumberColumn(format="$%.2f"),
                    "Bar chg (%)": st.column_config.NumberColumn(format="%.2f%%"),
                    "Bar volume": st.column_config.NumberColumn(format="%.0f"),
                    "Age (min)": st.column_config.NumberColumn(format="%.1f"),
                },
            )
        st.caption("Age is only the gap between the bar timestamp and this clock, not the true exchange-to-screen delay.")

    render_live_monitor(live_ticker, live_interval, include_extended, live_watchlist)


def remember_learn_tab() -> None:
    if st.session_state.get("learn_tab"):
        st.session_state.learn_tab_persist = st.session_state.learn_tab


def render_learn() -> None:
    bind_widget("learn_tab", "learn_tab_persist", "Start here")
    st.segmented_control("Learn", options=LEARN_TABS, key="learn_tab", on_change=remember_learn_tab)
    if st.session_state.learn_tab == "Start here":
        st.markdown("## Learn the market, then look it up here")
        st.markdown(
            "StockScope Learn is a **separate beginner course**. This dashboard does not embed those lessons, "
            "so each app stays focused. Use Learn to build vocabulary; use Home and Markets to look at real quotes."
        )
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown("### Open the Learn app")
            st.caption("From the repository root. Keep this dashboard on port 8501 so both can run.")
            st.code("cd learn\npython3 -m streamlit run app.py --server.port 8502", language="bash")
            st.markdown("Then open **http://localhost:8502**.")
        with col2:
            st.markdown(
                """
                <div class="learn-card">
                  <h3>Course map</h3>
                  <ol>
                    <li>Stock market basics</li>
                    <li>Reading a quote · candlesticks · indicators</li>
                    <li>How a trade is executed</li>
                    <li>Researching a company</li>
                    <li>Why prices move</li>
                    <li>Risk and investor protection</li>
                  </ol>
                  <p>Plus a practice quiz and a data-and-methods page inside Learn.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.info("Tip: after a lesson on indices, come back to Home and compare SPX, NDX, and DJI on the same day.")
        return

    render_methods()


def render_methods() -> None:
    st.subheader("Data sources and definitions")
    st.markdown(
        """
        **Where the numbers come from**
        - Home quotes and charts: Yahoo Finance through the Python package `yfinance`.
        - Main indices use Yahoo symbols `^GSPC` (shown as SPX), `^NDX` (NDX), and `^DJI` (DJI).
        - Live quotes: 1m / 5m / 15m / 30m / 60m bars with a candle chart, volume, and a short watch table.
        - Markets overview: daily history for a starter list of about 50 US stocks and benchmark ETFs.
        - Prices on historical pages use `auto_adjust=True`, so `Close` is the adjusted close.

        **How we compute**
        - Period return = (last close ÷ first valid close − 1) × 100.
        - Annualized volatility = daily-return standard deviation × √252 × 100.
        - Max drawdown = worst drop from a running peak close.
        - Group heatmap = simple average of monthly stock returns inside each classroom group, not a cap-weighted sector index.

        **Limits**
        - The watchlist lives in this browser session and resets when the app restarts.
        - This is a learning prototype, not a trading system, and not investment advice.
        - Yahoo data can be delayed, missing, revised, or rate-limited. A close timestamp is not a latency SLA.
        - Using `yfinance` is not a redistribution license. Check Yahoo's terms before any public deployment.
        """
    )
    if st.button("Load a 1-year snapshot of the starter list"):
        prices, metrics, error = load_universe("1y")
        if prices.empty:
            st.error("Could not load that snapshot.")
            if error:
                st.code(error)
            return
        st.subheader("Current load")
        data_summary = pd.DataFrame([
            {"Item": "Rows", "Value": f"{len(prices):,}"},
            {"Item": "Symbols", "Value": str(prices["ticker"].nunique())},
            {"Item": "First date", "Value": str(prices["date"].min().date())},
            {"Item": "Last date", "Value": str(prices["date"].max().date())},
            {"Item": "Missing volume share", "Value": f"{prices['volume'].isna().mean() * 100:.2f}%"},
        ])
        st.dataframe(data_summary, width="stretch", hide_index=True)
        st.download_button(
            "Download cleaned daily CSV",
            data=prices.to_csv(index=False).encode("utf-8-sig"),
            file_name="stockscope_daily_prices.csv",
            mime="text/csv",
        )
        if not metrics.empty:
            st.caption(f"{len(metrics)} symbols in the metrics table.")


def render_watchlist_page() -> None:
    st.subheader("Your watchlist")
    st.caption("Indices stay pinned so beginners always see the three main US benchmarks. Stocks you add sit underneath.")
    needed = tuple(dict.fromkeys([*INDEX_ORDER, *st.session_state.get("watchlist", [])]))
    with st.spinner("Updating watchlist quotes…"):
        try:
            prices = download_prices(needed, "5d")
        except Exception:
            prices = pd.DataFrame()
    snap = snapshot_from_prices(prices)
    left, right = st.columns([1.15, 1.55], gap="large")
    with left:
        render_watchlist_panel(snap, show_remove=True)
        if st.button("Open live quotes for this list"):
            go_to("Markets", markets_tab="Live quotes")
            st.rerun()
    with right:
        render_selected_chart(st.session_state.selected_symbol, snap)


def main() -> None:
    init_state()
    st.markdown(APP_STYLE, unsafe_allow_html=True)
    render_top_nav()

    nav = st.session_state.nav
    if nav == "Home":
        render_home()
    elif nav == "Learn":
        render_learn()
    elif nav == "Markets":
        render_markets()
    elif nav == "Watchlist":
        render_watchlist_page()
    else:
        render_home()

    st.markdown("---")
    st.markdown(
        "<div class='small-note'>StockScope · classroom prototype · verify definitions and data rights yourself. "
        "This tool is not investment advice.</div>",
        unsafe_allow_html=True,
    )


main()
