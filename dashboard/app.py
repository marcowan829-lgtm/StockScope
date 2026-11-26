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
from plotly.subplots import make_subplots
from chart_help import chart_help_button, help_chart
from i18n import ZH, init_language, is_zh, lang_key, language_css, peek_lang, plotly_font, render_language_toggle, t
from learning_integration import render_learning_page, render_study_launcher
from watchlist_design import WATCHLIST_STYLE, quote_labels, watchlist_row_html


st.set_page_config(
    page_title=t("StockScope · Stock market for beginner") if peek_lang() == "zh-HK" else "StockScope · Stock market for beginner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TOP_NAV = ["Home", "Market Overview", "Screener", "Live Quotes", "Returns & Risk", "Stock Research"]
LEGACY_MARKET_NAV = {
    "Overview": "Market Overview", "Screener": "Screener", "Live quotes": "Live Quotes",
    "Returns & risk": "Returns & Risk", "Stock": "Stock Research",
}
LEARN_TABS = ["Start here", "Data & methods"]
UP_COLOR = "#089981"
DOWN_COLOR = "#f23645"
PREV_CLOSE_COLOR = "#787b86"
GRID_COLOR = "#f0f3fa"
SPIKE_COLOR = "#9598a1"

CHART_RANGES = {
    "1D": {"period": "1d", "interval": "5m"},
    "5D": {"period": "5d", "interval": "15m"},
    "1M": {"period": "1mo", "interval": "1d"},
    "6M": {"period": "6mo", "interval": "1d"},
    "1Y": {"period": "1y", "interval": "1d"},
    "All Time": {"period": "max", "interval": "1wk"},
}
CHART_TYPES = ["Line", "Candle", "Area", "Baseline"]
INTRADAY_RANGES = {"1D", "5D"}
ET_ZONE = "America/New_York"
SESSION_OPEN_HOUR = 9.5
SESSION_CLOSE_HOUR = 16.0
SESSION_OPEN_MIN = 9 * 60 + 30
SESSION_CLOSE_MIN = 16 * 60
AREA_FILL_UP = "rgba(8,153,129,0.28)"
AREA_FILL_DOWN = "rgba(242,54,69,0.22)"
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
        "proxy": "SPY",
        "members": "About 500 large US companies",
        "about": (
            "The S&P 500 is a single number that follows 500 large companies listed in the United States. "
            "When this number rises, that slice of the market is generally up; when it falls, that slice is generally down. "
            "You cannot buy the index itself. A fund such as SPY is a common way to follow it in a brokerage account."
        ),
        "related": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"],
    },
    "^NDX": {
        "display": "NDX",
        "name": "NASDAQ 100",
        "blurb": "Largest non-financial Nasdaq companies",
        "unit": "point",
        "badge": "100",
        "badge_bg": "#2962ff",
        "proxy": "QQQ",
        "members": "About 100 large non-financial Nasdaq names",
        "about": (
            "The Nasdaq 100 follows the largest non-financial companies listed on Nasdaq. "
            "Technology names have a heavy weight, so this index can move more than the S&P 500 on tech news. "
            "A fund such as QQQ is a common way to follow it."
        ),
        "related": ["NVDA", "AAPL", "MSFT", "AMZN", "META"],
    },
    "^DJI": {
        "display": "DJI",
        "name": "Dow Jones",
        "blurb": "30 major US industrial companies",
        "unit": "USD",
        "badge": "30",
        "badge_bg": "#131722",
        "proxy": "DIA",
        "members": "30 large US companies",
        "about": (
            "The Dow Jones Industrial Average follows 30 well-known US companies. "
            "It is a short list, so one member can move the number more than in the S&P 500. "
            "A fund such as DIA is a common way to follow it."
        ),
        "related": ["JPM", "UNH", "HD", "CAT", "MCD"],
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
    background: #f5f7fa;
    color: #131722;
    font-family: -apple-system, BlinkMacSystemFont, "PingFang HK", "PingFang TC", "Microsoft JhengHei", "Noto Sans TC", "Trebuchet MS", Roboto, Ubuntu, sans-serif;
    font-variant-numeric: tabular-nums;
  }
  .stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: #131722;
    z-index: 999;
    pointer-events: none;
  }
  [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
  header[data-testid="stHeader"] { display: none !important; }
  div[data-testid="stDecoration"], div[data-testid="stToolbar"] { display: none !important; }
  .stAppDeployButton, #MainMenu, footer { display: none !important; }
  .block-container { padding-top: 1.15rem; padding-bottom: 2.2rem; max-width: 1440px; }
  div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e0e3eb;
    padding: 0.85rem 1rem;
    border-radius: 12px;
    box-shadow: 0 1px 2px rgba(19, 23, 34, 0.04);
  }
  div[class*="st-key-idx_card_"] {
    background: #ffffff !important;
    box-shadow: 0 1px 2px rgba(19, 23, 34, 0.04);
  }
  [data-testid="stDataFrame"] {
    background: #ffffff;
    border: 1px solid #e0e3eb;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 2px rgba(19, 23, 34, 0.04);
  }
  [data-testid="stAlert"] {
    background: #ffffff;
    border: 1px solid #e0e3eb;
    border-radius: 10px;
  }
  [data-testid="stPlotlyChart"] {
    background: #ffffff;
    border: 1px solid #e0e3eb;
    border-radius: 12px;
    padding: 0.2rem 0.15rem 0.05rem;
    box-shadow: 0 1px 2px rgba(19, 23, 34, 0.04);
  }
  div.st-key-nav_pills button:hover {
    border-color: #b2b5be !important;
    background: #ffffff !important;
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
    background: #ffffff;
    min-height: 118px;
    box-shadow: 0 1px 2px rgba(19, 23, 34, 0.04);
  }
  .index-card-top { display: flex; align-items: flex-start; gap: 0.7rem; }
  .idx-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 0.5rem; }
  .idx-head-main { display: flex; align-items: flex-start; gap: 0.7rem; min-width: 0; }
  .range-track {
    position: relative; height: 8px; background: #eef0f5; border-radius: 99px; margin: 0.55rem 0 0.35rem 0;
  }
  .range-dot {
    position: absolute; top: 50%; width: 12px; height: 12px; margin-top: -6px; margin-left: -6px;
    background: #131722; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 0 1px #c8ccd6;
  }
  .stat-chip {
    border: 1px solid #e0e3eb; border-radius: 10px; padding: 0.65rem 0.75rem; background: #ffffff;
    box-shadow: 0 1px 2px rgba(19, 23, 34, 0.03);
  }
  .stat-chip .k { color: #6a6d78; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; }
  .stat-chip .v { font-weight: 700; font-size: 1.02rem; font-variant-numeric: tabular-nums; margin-top: 0.15rem; }
  .about-box {
    border: 1px solid #e0e3eb; border-radius: 12px; padding: 1rem 1.1rem; background: #ffffff;
    box-shadow: 0 1px 2px rgba(19, 23, 34, 0.04);
  }
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
    border: 1px solid #e0e3eb; border-radius: 12px; padding: 1rem 1.1rem; background: #ffffff;
    box-shadow: 0 1px 2px rgba(19, 23, 34, 0.04);
  }
  .learn-card h3 { margin: 0 0 0.4rem 0; font-size: 1.02rem; }
  .learn-card p, .learn-card li { color: #4c4f59; font-size: 0.92rem; }
  div.st-key-nav_pills [data-testid="stMarkdownContainer"] p { font-weight: 600; font-size: 0.84rem; }
  div.st-key-nav_pills button { white-space: nowrap; padding: 0.4rem 0.65rem; min-height: 2.5rem; }
  div.st-key-nav_search [data-testid="stTextInputRootElement"] {
    border-radius: 24px;
    background: #ffffff;
    border: 1px solid #e0e3eb;
    box-shadow: 0 1px 2px rgba(19, 23, 34, 0.04);
  }
  div.st-key-nav_search input { background: transparent; }
  .nav-rule { border: 0; border-top: 1px solid #d8dbe3; margin: 0.15rem 0 1rem 0; }
  .site-footer {
    margin-top: 0.35rem;
    padding: 0.85rem 0 0.15rem;
    border-top: 1px solid #d8dbe3;
    color: #787b86;
    font-size: 0.78rem;
    letter-spacing: 0.01em;
    line-height: 1.55;
  }
  .chart-help-title { font-size: 1rem; font-weight: 700; line-height: 1.45; margin: 0; color: #131722; }
  div[class*="st-key-chart_help_"] button {
    border-radius: 50% !important; width: 2.2rem !important; height: 2.2rem !important;
    min-height: 2.2rem !important; padding: 0 !important;
    color: #4c4f59 !important; background: #fff !important;
    border: 1px solid #b2b5be !important; font-weight: 700 !important;
  }
  div[class*="st-key-chart_help_"] button:hover { color: #131722 !important; border-color: #131722 !important; background: #f0f3fa !important; }
  div[class*="st-key-chart_help_"] button:focus-visible { outline: 2px solid #2962ff; outline-offset: 3px; }
  div[class*="st-key-idx_add_"] button,
  div[class*="st-key-idx_open_"] button {
    min-width: 2.15rem !important;
    min-height: 2.15rem !important;
    height: 2.15rem !important;
    padding: 0 !important;
    border-radius: 8px !important;
    border: 1px solid #d8dbe3 !important;
    background: #fff !important;
    font-size: 0.95rem !important;
    line-height: 1 !important;
  }
  div.st-key-idx_full_chart button,
  div.st-key-idx_exit_full button,
  div.st-key-idx_back button {
    min-height: 2.1rem !important;
    border-radius: 8px !important;
  }
  div.st-key-chart_add button {
    min-height: 2rem !important;
    padding: 0.15rem 0.5rem !important;
    border-radius: 8px !important;
  }
  div.st-key-chart_type button {
    font-size: 0.8rem !important;
    padding: 0.15rem 0.45rem !important;
    min-height: 2rem !important;
  }
  @media (max-width: 900px) {
    .index-grid { grid-template-columns: 1fr; }
    .hero-title { font-size: 1.4rem; }
    .block-container { padding-left: 0.8rem; padding-right: 0.8rem; }
  }
  [data-testid="stDialog"]:has(.study-path-marker) { background: transparent !important; }
  [data-testid="stDialog"]:has(.study-path-marker) [role="dialog"] { background: #fff; color: #131722; }
  [data-testid="stDialog"]:has(.study-path-marker) h2,
  [data-testid="stDialog"]:has(.study-path-marker) p,
  [data-testid="stDialog"]:has(.study-path-marker) [data-testid="stCaptionContainer"] { color: #131722; }
  [data-testid="stDialog"]:has(.study-path-marker) [data-testid="stButton"] button {
    width: 100%; min-height: 3rem; justify-content: flex-start; text-align: left;
    background: #fff; color: #131722; border: 1px solid #e0e3eb; border-radius: 13px;
  }
  [data-testid="stDialog"]:has(.study-path-marker) [data-testid="stButton"] button:hover {
    border-color: #131722; background: #fff;
  }
  [data-testid="stDialog"]:has(.study-path-marker) [data-testid="stButton"] button div { width: 100%; justify-content: flex-start; }
  [data-testid="stDialog"]:has(.study-path-marker) [data-testid="stButton"] button p { font-size: 1rem; line-height: 1.4; text-align: left; }
  [data-testid="stDialog"]:has(.study-path-marker) [data-testid="stProgressBarTrack"] { background: #e0e3eb; }
  .study-path-brand { display: flex; gap: 14px; align-items: center; margin: 0.25rem 0 1.2rem; }
  .study-path-logo {
    display: grid; place-items: center; width: 48px; height: 48px; border-radius: 15px;
    background: #fff; border: 1px solid #e0e3eb; color: #131722; font-size: 26px; font-weight: 800;
  }
  .study-path-brand b { color: #131722; font-size: 1.2rem; }
  .study-path-brand small { display: block; color: #6a6d78; margin-top: 5px; }
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
        return t(INDEX_META[ticker]["name"])
    return t(COMPANY_NAMES.get(ticker, ticker))


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
        return t("Weekend: the regular US session is usually closed")
    current_minutes = now_et.hour * 60 + now_et.minute
    if 4 * 60 <= current_minutes < 9 * 60 + 30:
        return t("Pre-market (clock estimate)")
    if 9 * 60 + 30 <= current_minutes < 16 * 60:
        return t("Regular session (clock estimate)")
    if 16 * 60 <= current_minutes < 20 * 60:
        return t("After hours (clock estimate)")
    return t("Outside the regular session")


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
    raw = raw.loc[~raw.index.duplicated(keep="last")]

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
        last_day = pd.Timestamp(data.index.max()).date()
        data = data[pd.Series(data.index.date, index=data.index) == last_day]
    data = data.copy()
    for column in ["Open", "High", "Low", "Close", "Volume"]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    if "Close" not in data.columns:
        return pd.DataFrame()
    data = data.dropna(subset=["Close"]).sort_index()
    return data.loc[~data.index.duplicated(keep="last")]


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
    monthly_returns = pivot.pct_change(axis=1, fill_method=None) * 100
    if monthly_returns.empty:
        return None
    monthly_returns = monthly_returns.iloc[:, 1:]
    monthly_returns["Group"] = [UNIVERSE.get(sym, "Other") for sym in monthly_returns.index]
    sect = monthly_returns.groupby("Group").mean(numeric_only=True)
    if sect.empty or sect.shape[1] == 0:
        return None
    labels = [pd.Timestamp(c).strftime("%Y-%m") for c in sect.columns]
    fig = go.Figure(data=go.Heatmap(
        z=sect.values,
        x=labels,
        y=[t(g) for g in sect.index.tolist()],
        colorscale="RdYlGn",
        zmid=0,
        colorbar={"title": t("Monthly %")},
        hovertemplate=t("Group: %{y}<br>Month: %{x}<br>Avg return: %{z:.2f}%<extra></extra>"),
    ))
    fig.update_layout(
        title=t("Group monthly returns (0% = unchanged · equal-weighted inside each group)"),
        xaxis_title=t("Month"),
        yaxis_title=t("Group"),
        height=420,
        margin=dict(l=10, r=10, t=60, b=10),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return fig


def volume_bar_colors(frame: pd.DataFrame) -> list[str]:
    closes = frame["Close"].astype(float)
    if "Open" in frame.columns:
        opens = frame["Open"].astype(float)
        return [UP_COLOR if c >= o else DOWN_COLOR for o, c in zip(opens, closes)]
    prev = closes.shift(1)
    return [UP_COLOR if pd.isna(p) or c >= p else DOWN_COLOR for c, p in zip(closes, prev)]


def to_et_naive(index: pd.Index) -> pd.DatetimeIndex:
    idx = pd.DatetimeIndex(index)
    if idx.tz is not None:
        return idx.tz_convert(ET_ZONE).tz_localize(None)
    return idx


def clip_regular_session(frame: pd.DataFrame, range_key: str, *, include_extended: bool = False) -> pd.DataFrame:
    """Keep the requested regular or extended US session, excluding weekends."""
    out = frame.copy()
    out.index = to_et_naive(out.index)
    weekday = out.index.day_of_week < 5
    if range_key in INTRADAY_RANGES:
        minutes = out.index.hour * 60 + out.index.minute
        open_min, close_min = (4 * 60, 20 * 60) if include_extended else (SESSION_OPEN_MIN, SESSION_CLOSE_MIN)
        session = (minutes >= open_min) & (minutes <= close_min)
        return out.loc[weekday & session]
    return out.loc[weekday]


def market_rangebreaks(index: pd.DatetimeIndex, range_key: str, *, include_extended: bool = False) -> list[dict]:
    """Collapse weekends, US overnight hours, and weekday holidays on the time axis."""
    breaks: list[dict] = [dict(bounds=["sat", "mon"])]
    if range_key in INTRADAY_RANGES:
        close_hour, open_hour = (20, 4) if include_extended else (SESSION_CLOSE_HOUR, SESSION_OPEN_HOUR)
        breaks.append(dict(bounds=[close_hour, open_hour], pattern="hour"))
    if len(index) >= 2:
        idx = pd.DatetimeIndex(index)
        start, end = idx.min().normalize(), idx.max().normalize()
        have = {pd.Timestamp(d).normalize() for d in idx}
        missing = [d for d in pd.bdate_range(start, end) if d not in have]
        if missing:
            breaks.append(dict(values=missing))
    return breaks


def _split_at_baseline(index, values, level: float):
    """Split a series at `level` so the line can be green above and red below."""
    xs = list(index)
    ys = [float(v) for v in values]
    x_hi: list = []
    y_hi: list = []
    x_lo: list = []
    y_lo: list = []
    for i, (x, y) in enumerate(zip(xs, ys)):
        if i > 0:
            y_prev = ys[i - 1]
            if (y_prev - level) * (y - level) < 0 and y != y_prev:
                x_prev = xs[i - 1]
                t = (level - y_prev) / (y - y_prev)
                x_cross = x_prev + (x - x_prev) * t
                x_hi.append(x_cross)
                y_hi.append(level)
                x_lo.append(x_cross)
                y_lo.append(level)
        x_hi.append(x if y >= level else None)
        y_hi.append(y if y >= level else None)
        x_lo.append(x if y <= level else None)
        y_lo.append(y if y <= level else None)
    return x_hi, y_hi, x_lo, y_lo


def apply_market_layout(
    fig: go.Figure,
    *,
    height: int,
    tickformat: str,
    rangebreaks: list[dict] | None = None,
) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=64, t=8, b=28),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        hovermode="x unified",
        showlegend=False,
        font=dict(color="#131722", size=12, family=plotly_font()),
        xaxis_rangeslider_visible=False,
        spikedistance=-1,
    )
    fig.update_yaxes(
        side="right",
        showgrid=True,
        gridcolor=GRID_COLOR,
        zeroline=False,
        linecolor="#ffffff",
        tickfont=dict(color="#6a6d78", size=11),
        separatethousands=True,
        showspikes=True,
        spikemode="across",
        spikecolor=SPIKE_COLOR,
        spikethickness=1,
        spikedash="dot",
        fixedrange=False,
    )
    xaxis_kwargs: dict = dict(
        showgrid=False,
        linecolor="#e0e3eb",
        tickfont=dict(color="#6a6d78", size=11),
        tickformat=tickformat,
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikecolor=SPIKE_COLOR,
        spikethickness=1,
        spikedash="dot",
        rangeslider_visible=False,
        title_text="",
    )
    if rangebreaks:
        xaxis_kwargs["rangebreaks"] = rangebreaks
    fig.update_xaxes(**xaxis_kwargs)
    return fig


def restyle_chart(fig: go.Figure, height: int = 420) -> go.Figure:
    return apply_market_layout(fig, height=height, tickformat="%b %d")


def build_price_chart(
    frame: pd.DataFrame,
    ticker: str,
    chart_type: str,
    *,
    previous_close: float | None = None,
    range_key: str = "1D",
    include_extended: bool = False,
) -> go.Figure:
    """Quote-site price pane, using regular US hours unless extended hours are requested."""
    empty_ticks = "%I:%M %p" if range_key == "1D" else "%b %d"
    if frame.empty:
        return apply_market_layout(go.Figure(), height=460, tickformat=empty_ticks)

    frame = clip_regular_session(frame, range_key, include_extended=include_extended)
    if frame.empty:
        return apply_market_layout(go.Figure(), height=460, tickformat=empty_ticks)

    kind = chart_type if chart_type in CHART_TYPES else "Line"
    close = frame["Close"].astype(float)
    last = float(close.iloc[-1])
    ref = previous_close if previous_close is not None and pd.notna(previous_close) else float(close.iloc[0])
    up = last >= ref
    line_color = UP_COLOR if up else DOWN_COLOR
    has_ohlc = {"Open", "High", "Low", "Close"}.issubset(frame.columns)
    has_volume = "Volume" in frame.columns and frame["Volume"].notna().any()
    if kind == "Candle" and not has_ohlc:
        kind = "Line"

    x = frame.index
    name = display_symbol(ticker)
    # Separate price and volume panes so candles never sit on the volume bars.
    if has_volume:
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.82, 0.18],
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    if kind == "Candle":
        fig.add_trace(go.Candlestick(
            x=x,
            open=frame["Open"], high=frame["High"], low=frame["Low"], close=frame["Close"],
            name=name,
            increasing=dict(line=dict(color=UP_COLOR, width=1), fillcolor=UP_COLOR),
            decreasing=dict(line=dict(color=DOWN_COLOR, width=1), fillcolor=DOWN_COLOR),
            whiskerwidth=0.8,
            hoverinfo="x+y",
        ), row=1, col=1)
    elif kind == "Area":
        fig.add_trace(go.Scatter(
            x=x,
            y=close,
            mode="lines",
            name=name,
            line=dict(color=line_color, width=1.6, shape="linear"),
            fill="tozeroy",
            fillcolor=AREA_FILL_UP if up else AREA_FILL_DOWN,
            hovertemplate=t("Close: %{y:,.2f}<extra></extra>"),
        ), row=1, col=1)
    elif kind == "Baseline":
        baseline = float(ref)
        base_arr = [baseline] * len(close)
        above = close.clip(lower=baseline)
        below = close.clip(upper=baseline)
        fig.add_trace(go.Scatter(
            x=x, y=base_arr, mode="lines",
            line=dict(width=0, color="rgba(0,0,0,0)"),
            hoverinfo="skip", showlegend=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=x, y=above, mode="lines",
            line=dict(width=0, color="rgba(0,0,0,0)"),
            fill="tonexty", fillcolor=AREA_FILL_UP,
            hoverinfo="skip", showlegend=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=x, y=base_arr, mode="lines",
            line=dict(width=0, color="rgba(0,0,0,0)"),
            hoverinfo="skip", showlegend=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=x, y=below, mode="lines",
            line=dict(width=0, color="rgba(0,0,0,0)"),
            fill="tonexty", fillcolor=AREA_FILL_DOWN,
            hoverinfo="skip", showlegend=False,
        ), row=1, col=1)
        x_hi, y_hi, x_lo, y_lo = _split_at_baseline(x, close, baseline)
        fig.add_trace(go.Scatter(
            x=x_hi, y=y_hi, mode="lines", name=name,
            line=dict(color=UP_COLOR, width=1.6, shape="linear"),
            connectgaps=False,
            hovertemplate=t("Close: %{y:,.2f}<extra></extra>"),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=x_lo, y=y_lo, mode="lines", name=name,
            line=dict(color=DOWN_COLOR, width=1.6, shape="linear"),
            connectgaps=False,
            hovertemplate=t("Close: %{y:,.2f}<extra></extra>"),
        ), row=1, col=1)
        fig.add_hline(y=baseline, line_color=PREV_CLOSE_COLOR, line_width=1, row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=x,
            y=close,
            mode="lines",
            name=name,
            line=dict(color=line_color, width=1.6, shape="linear"),
            hovertemplate=t("Close: %{y:,.2f}<extra></extra>"),
        ), row=1, col=1)

    if has_volume:
        fig.add_trace(go.Bar(
            x=x,
            y=frame["Volume"],
            name=t("Volume"),
            marker_color=volume_bar_colors(frame),
            marker_line_width=0,
            opacity=0.9,
            hovertemplate=t("Volume: %{y:,.0f}<extra></extra>"),
        ), row=2, col=1)

    ymin = float(close.min())
    ymax = float(close.max())
    if kind == "Candle":
        if frame["Low"].notna().any():
            ymin = min(ymin, float(frame["Low"].min()))
        if frame["High"].notna().any():
            ymax = max(ymax, float(frame["High"].max()))
    if kind == "Baseline":
        ymin = min(ymin, float(ref))
        ymax = max(ymax, float(ref))
    pad = (ymax - ymin) * 0.08 if ymax > ymin else max(abs(ymin) * 0.01, 0.5)

    if range_key == "1D":
        tickformat = "%I:%M %p"
    elif range_key == "5D":
        tickformat = "%b %d"
    else:
        tickformat = "%b %d"

    apply_market_layout(
        fig,
        height=500,
        tickformat=tickformat,
        rangebreaks=market_rangebreaks(pd.DatetimeIndex(x), range_key, include_extended=include_extended),
    )
    fig.update_yaxes(range=[ymin - pad, ymax + pad], tickformat=",.2f", title_text="", row=1, col=1)
    if has_volume:
        fig.update_xaxes(showticklabels=False, row=1, col=1)
        fig.update_yaxes(
            title_text="",
            showticklabels=False,
            showgrid=False,
            showspikes=False,
            zeroline=False,
            row=2,
            col=1,
        )
    if range_key == "1D":
        fig.update_xaxes(dtick=3_600_000)
    return fig


def period_label(period: str) -> str:
    return t(PERIOD_LABELS[period])


def signed_hbar(df: pd.DataFrame, x_col: str, y_col: str, title: str, x_title: str) -> go.Figure:
    ordered = df.sort_values(x_col)
    colors = [UP_COLOR if (pd.notna(v) and v >= 0) else DOWN_COLOR for v in ordered[x_col]]
    fig = go.Figure(go.Bar(
        x=ordered[x_col],
        y=ordered[y_col],
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        hovertemplate="%{y}: %{x:+.2f}%<extra></extra>",
    ))
    fig.add_vline(x=0, line_color="#b2b5be", line_width=1)
    fig.update_layout(
        title=title, height=400, showlegend=False,
        xaxis_title=x_title, yaxis_title="",
        margin=dict(l=8, r=12, t=48, b=8),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(color="#131722", size=12),
        bargap=0.28,
    )
    fig.update_xaxes(zeroline=True, zerolinecolor="#b2b5be", gridcolor=GRID_COLOR, ticksuffix="%")
    fig.update_yaxes(showgrid=False)
    return fig


def lookup_snapshot(snap: pd.DataFrame, ticker: str) -> dict:
    if snap is None or snap.empty:
        return {}
    hit = snap[snap["ticker"] == ticker]
    if hit.empty:
        return {}
    return hit.iloc[0].to_dict()


def _take_pending(pending_key: str):
    if pending_key not in st.session_state:
        return None
    return st.session_state.pop(pending_key)


def apply_pending_nav_pills() -> None:
    if "_pending_nav_pills" not in st.session_state:
        return
    value = st.session_state.pop("_pending_nav_pills")
    st.session_state.nav_pills = value
    st.session_state._last_nav_pill = value


def apply_pending_idx_switcher() -> None:
    value = _take_pending("_pending_idx_switcher")
    if value is not None:
        st.session_state.idx_switcher = value


def apply_pending_markets_tab() -> None:
    value = _take_pending("_pending_markets_tab")
    if value is not None:
        st.session_state.markets_tab = value


def apply_pending_learn_tab() -> None:
    value = _take_pending("_pending_learn_tab")
    if value is not None:
        st.session_state.learn_tab = value


def apply_pending_widgets() -> None:
    """Apply queued widget values. Call only before those widgets exist."""
    apply_pending_nav_pills()
    apply_pending_idx_switcher()
    apply_pending_markets_tab()
    apply_pending_learn_tab()


def go_to(nav: str, markets_tab: str | None = None, learn_tab: str | None = None) -> None:
    st.session_state.nav = nav
    if nav in TOP_NAV:
        st.session_state._pending_nav_pills = nav
        st.session_state.index_full_chart = False
    if markets_tab:
        st.session_state._pending_markets_tab = markets_tab
        st.session_state.markets_tab_persist = markets_tab
    if learn_tab:
        st.session_state._pending_learn_tab = learn_tab
        st.session_state.learn_tab_persist = learn_tab


def open_index_page(ticker: str) -> None:
    st.session_state.selected_symbol = ticker
    st.session_state.nav = "Index"
    st.session_state.index_full_chart = False
    st.session_state._pending_idx_switcher = ticker
    st.session_state._pending_nav_pills = None


def on_idx_switch() -> None:
    picked = st.session_state.get("idx_switcher")
    if picked in INDEX_META:
        st.session_state.selected_symbol = picked
        st.session_state.index_full_chart = False


def trailing_return(prices: pd.DataFrame, ticker: str, days: int) -> float:
    g = prices[prices["ticker"] == ticker].sort_values("date").dropna(subset=["close"])
    if len(g) < 2:
        return np.nan
    last = float(g.iloc[-1]["close"])
    cutoff = pd.Timestamp(g["date"].max()) - pd.Timedelta(days=days)
    past = g[pd.to_datetime(g["date"]) <= cutoff]
    if past.empty:
        base = float(g.iloc[0]["close"])
    else:
        base = float(past.iloc[-1]["close"])
    if not base:
        return np.nan
    return (last / base - 1) * 100


def session_bar_stats(frame: pd.DataFrame) -> dict:
    if frame.empty or not {"Open", "High", "Low", "Close"}.issubset(frame.columns):
        return {}
    return {
        "open": float(frame["Open"].iloc[0]),
        "high": float(frame["High"].max()),
        "low": float(frame["Low"].min()),
        "close": float(frame["Close"].iloc[-1]),
        "volume": float(pd.to_numeric(frame["Volume"], errors="coerce").sum()) if "Volume" in frame.columns else np.nan,
    }


def add_to_watchlist(ticker: str) -> str:
    if ticker in INDEX_META:
        return t("{ticker} already sits in Indices.", ticker=display_symbol(ticker))
    current = list(st.session_state.get("watchlist", []))
    if ticker in current:
        return t("{ticker} is already on your watchlist.", ticker=ticker)
    st.session_state.watchlist = current + [ticker]
    return t("Added {ticker} to Watchlist.", ticker=ticker)


def remove_from_watchlist(ticker: str) -> None:
    st.session_state.watchlist = [t for t in st.session_state.get("watchlist", []) if t != ticker]


def normalize_query(query: str) -> str:
    return re.sub(r"[^A-Za-z0-9&]+", "", query).upper()


def resolve_search(query: str) -> dict:
    q = query.strip()
    if not q:
        return {"error": t("Type a ticker or company name, for example AAPL or Apple.")}
    compact = normalize_query(q)
    if compact in INDEX_ALIASES:
        return {"ticker": INDEX_ALIASES[compact]}
    upper = q.upper()
    if upper in UNIVERSE:
        return {"ticker": upper}
    lower = q.casefold()
    exact_name = next(
        (symbol for symbol, name in COMPANY_NAMES.items()
         if name.casefold() == lower or ZH.get(name, "").casefold() == lower),
        None,
    )
    if exact_name:
        return {"ticker": exact_name}
    matches = [
        symbol for symbol in UNIVERSE
        if upper in symbol.upper()
        or lower in COMPANY_NAMES.get(symbol, symbol).casefold()
        or lower in ZH.get(COMPANY_NAMES.get(symbol, symbol), "").casefold()
    ]
    index_matches = [
        yahoo for yahoo, meta in INDEX_META.items()
        if lower in meta["name"].casefold()
        or lower in meta["display"].casefold()
        or lower in ZH.get(meta["name"], "").casefold()
    ]
    matches = list(dict.fromkeys(index_matches + matches))
    if len(matches) == 1:
        return {"ticker": matches[0]}
    if matches:
        return {"candidates": matches}
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9.-]{0,9}", q):
        return {"ticker": upper, "custom": True}
    return {"error": t("No match in the starter list. Try a US ticker such as AAPL, MSFT, or SPX.")}


def on_search_change() -> None:
    result = resolve_search(st.session_state.get("nav_search", ""))
    st.session_state.search_result = result
    ticker = result.get("ticker")
    if ticker:
        st.session_state.selected_symbol = ticker
        if ticker in INDEX_META:
            open_index_page(ticker)
        else:
            go_to("Home")


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


def remember_idx_chart_range() -> None:
    if st.session_state.get("idx_chart_range"):
        st.session_state.idx_chart_range_persist = st.session_state.idx_chart_range


def remember_idx_chart_type() -> None:
    if st.session_state.get("idx_chart_type"):
        st.session_state.idx_chart_type_persist = st.session_state.idx_chart_type


def init_state() -> None:
    init_language()
    st.session_state.setdefault("nav", "Home")
    # Migrate open sessions from the old nested Markets navigation.
    previous_nav = st.session_state.nav
    if previous_nav == "Markets":
        previous_tab = st.session_state.get("_pending_markets_tab") or st.session_state.get("markets_tab") or st.session_state.get("markets_tab_persist", "Overview")
        st.session_state.nav = LEGACY_MARKET_NAV.get(previous_tab, "Market Overview")
        st.session_state._pending_nav_pills = st.session_state.nav
    elif previous_nav not in [*TOP_NAV, "Index", "Lesson"]:
        st.session_state.nav = "Home"
        st.session_state._pending_nav_pills = "Home"
    st.session_state.setdefault("markets_tab_persist", "Overview")
    st.session_state.setdefault("learn_tab_persist", "Start here")
    st.session_state.setdefault("selected_symbol", "AAPL")
    st.session_state.setdefault("chart_range_persist", "1D")
    st.session_state.setdefault("chart_type_persist", "Line")
    if st.session_state.chart_type_persist not in CHART_TYPES:
        st.session_state.chart_type_persist = "Line"
    if "chart_range" not in st.session_state:
        st.session_state.chart_range = st.session_state.chart_range_persist
    if "chart_type" not in st.session_state:
        st.session_state.chart_type = st.session_state.chart_type_persist
    if st.session_state.get("chart_type") not in CHART_TYPES:
        st.session_state.chart_type = st.session_state.chart_type_persist
    st.session_state.setdefault("watchlist", ["AAPL", "MCD"])
    st.session_state.setdefault("search_result", {})
    st.session_state.setdefault("flash", "")
    st.session_state.setdefault("analysis_period", "1y")
    st.session_state.setdefault("index_full_chart", False)
    st.session_state.setdefault("idx_chart_range_persist", "1D")
    st.session_state.setdefault("idx_chart_type_persist", "Candle")
    if st.session_state.idx_chart_type_persist not in CHART_TYPES:
        st.session_state.idx_chart_type_persist = "Candle"


def render_top_nav() -> None:
    brand, navigation, tools = st.columns([0.95, 5.05, 2.4], gap="small", vertical_alignment="center")
    with brand:
        st.markdown('<div class="topnav"><div class="brand">StockScope</div></div>', unsafe_allow_html=True)
    with navigation:
        if "nav_pills" not in st.session_state:
            st.session_state.nav_pills = st.session_state.nav if st.session_state.nav in TOP_NAV else None
        picked = st.pills(
            "Section", TOP_NAV, key="nav_pills", label_visibility="collapsed",
            format_func=lambda page: t(page),
        )
        last_pill = st.session_state.get("_last_nav_pill")
        if picked and picked != last_pill:
            st.session_state.nav = picked
            st.session_state.index_full_chart = False
            st.session_state._last_nav_pill = picked
        elif picked and st.session_state.get("nav") in TOP_NAV:
            st.session_state._last_nav_pill = picked
    with tools:
        search, lang = st.columns([1.7, 0.7], vertical_alignment="center")
        with search:
            st.text_input(
                t("Search"),
                placeholder=t("Search stocks or indices"),
                label_visibility="collapsed",
                key="nav_search",
                on_change=on_search_change,
                help=t("Search a ticker or company in the starter list, or a main US index such as SPX."),
            )
        with lang:
            render_language_toggle()
    st.markdown('<hr class="nav-rule" />', unsafe_allow_html=True)

    result = st.session_state.get("search_result") or {}
    if result.get("error") and st.session_state.get("nav_search"):
        st.caption(result["error"])
    elif result.get("candidates"):
        pick_col, go_col = st.columns([4, 1])
        chosen = pick_col.selectbox(
            t("Matches"),
            options=result["candidates"],
            format_func=ticker_label,
            key=lang_key("search_candidate_choice"),
        )
        if go_col.button(t("Open"), width="stretch"):
            st.session_state.selected_symbol = chosen
            st.session_state.search_result = {"ticker": chosen}
            if chosen in INDEX_META:
                open_index_page(chosen)
            else:
                go_to("Home")
            st.rerun()
    if st.session_state.get("flash"):
        st.caption(st.session_state.flash)
        st.session_state.flash = ""


def index_card_title_html(ticker: str) -> str:
    meta = INDEX_META[ticker]
    return (
        '<div class="idx-head-main">'
        f'<div class="idx-badge" style="background:{meta["badge_bg"]}">{html.escape(meta["badge"])}</div>'
        "<div>"
        f'<div class="idx-name">{html.escape(t(meta["name"]))}<span class="idx-ticker">{html.escape(meta["display"])}</span></div>'
        f'<div class="idx-blurb">{html.escape(t(meta["blurb"]))}</div>'
        "</div></div>"
    )


def index_card_quote_html(ticker: str, snap_row: dict) -> str:
    last = snap_row.get("last", np.nan)
    chg_pct = snap_row.get("chg_pct", np.nan)
    last_text = "—" if pd.isna(last) else f"{last:,.2f}"
    unit = t(INDEX_META[ticker]["unit"]) if INDEX_META[ticker]["unit"] == "point" else INDEX_META[ticker]["unit"]
    return (
        '<div class="idx-quote">'
        f'<div class="last-px">{last_text}<span class="last-unit">{html.escape(unit)}</span></div>'
        f'<div class="{chg_class(chg_pct)}">{html.escape(format_chg(chg_pct, True))}</div>'
        "</div>"
    )


def render_index_cards(snap: pd.DataFrame) -> None:
    cols = st.columns(3, gap="small")
    for col, ticker in zip(cols, INDEX_ORDER):
        meta = INDEX_META[ticker]
        with col:
            with st.container(border=True, key=widget_key("idx_card", ticker)):
                info, plus_col, open_col = st.columns([4.15, 0.55, 0.55])
                with info:
                    st.markdown(index_card_title_html(ticker), unsafe_allow_html=True)
                with plus_col:
                    if st.button("＋", key=widget_key("idx_add", ticker), help=t("Add {proxy} (tracks this index) to Watchlist", proxy=meta["proxy"])):
                        st.session_state.flash = add_to_watchlist(meta["proxy"])
                        st.rerun()
                with open_col:
                    if st.button("↗", key=widget_key("idx_open", ticker), help=t("Open {name} page", name=t(meta["name"]))):
                        open_index_page(ticker)
                        st.rerun()
                st.markdown(index_card_quote_html(ticker, lookup_snapshot(snap, ticker)), unsafe_allow_html=True)


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


def on_watchlist_selection(key: str, tickers: list[str]) -> None:
    """Update before rendering, only when the table selection actually changes."""
    event = st.session_state.get(key, {})
    rows = event.get("selection", {}).get("rows", [])
    if not rows:
        return
    idx = rows[0]
    if 0 <= idx < len(tickers):
        st.session_state["selected_symbol"] = tickers[idx]


def select_watchlist_symbol(ticker: str) -> None:
    st.session_state.selected_symbol = ticker


def render_watchlist_rows(tickers: Iterable[str], snap: pd.DataFrame) -> None:
    for ticker in tickers:
        quote = lookup_snapshot(snap, ticker)
        meta = INDEX_META.get(ticker, {})
        selected = ticker == st.session_state.selected_symbol
        last, change, _ = quote_labels(quote.get("last"), quote.get("chg"), quote.get("chg_pct"), is_index=bool(meta))
        label = t(
            "Show {name} ({symbol}) on chart. Price {last}; daily change {change}.",
            name=company_name(ticker), symbol=display_symbol(ticker), last=last, change=change,
        )
        if selected:
            label += t(" Selected.")
        with st.container(key=widget_key("wlrow", ticker)):
            st.markdown(watchlist_row_html(
                ticker, company_name(ticker), display_symbol(ticker),
                quote.get("last"), quote.get("chg"), quote.get("chg_pct"),
                selected=selected, index_badge=meta.get("badge"), index_color=meta.get("badge_bg", "#2962ff"),
            ), unsafe_allow_html=True)
            st.button(label, key=widget_key("wl_pick", ticker), width="stretch",
                      on_click=select_watchlist_symbol, args=(ticker,),
                      help=t("Currently shown on the chart") if selected else t("Show {symbol} on the chart", symbol=display_symbol(ticker)))


def render_watchlist_panel(snap: pd.DataFrame, *, show_remove: bool = False) -> None:
    stocks = [ticker for ticker in st.session_state.get("watchlist", []) if ticker not in INDEX_META]
    st.markdown(WATCHLIST_STYLE, unsafe_allow_html=True)
    with st.container(key="watchlist_panel"):
        with st.container(key="watchlist_header"):
            head_l, head_r = st.columns([3, 1], vertical_alignment="center")
            with head_l:
                st.markdown(
                    f'<p class="watchlist-heading">{t("Watchlist")}</p>'
                    f'<p class="watchlist-summary">{t("{n_idx} indices · {n_stocks} stocks & funds", n_idx=len(INDEX_ORDER), n_stocks=len(stocks))}</p>',
                    unsafe_allow_html=True,
                )
            with head_r:
                with st.popover("＋", help=t("Add a company or fund to your watchlist")):
                    add_query = st.text_input(t("Add ticker"), placeholder=t("Name or ticker, e.g. NVDA"), key="wl_add_query")
                    if st.button(t("Add symbol"), key="wl_add_btn", width="stretch"):
                        resolved = resolve_search(add_query)
                        st.session_state.flash = add_to_watchlist(resolved["ticker"]) if resolved.get("ticker") else resolved.get("error", t("Could not add that symbol."))
                        st.rerun()

        st.markdown(f'<div class="watchlist-group-title">{t("Market indices")}<span class="watchlist-count">{len(INDEX_ORDER)}</span></div>', unsafe_allow_html=True)
        render_watchlist_rows(INDEX_ORDER, snap)
        st.markdown(f'<div class="watchlist-group-title">{t("Stocks & funds")}<span class="watchlist-count">{len(stocks)}</span></div>', unsafe_allow_html=True)
        if stocks:
            render_watchlist_rows(stocks, snap)
            if show_remove:
                with st.popover(t("Manage watchlist"), width="stretch"):
                    drop = st.selectbox(t("Remove"), options=["—"] + stocks, format_func=lambda ticker: ticker_label(ticker) if ticker != "—" else "—", key=lang_key("wl_remove_choice"))
                    if st.button(t("Remove from watchlist"), key="wl_remove_btn", width="stretch", disabled=drop == "—"):
                        remove_from_watchlist(drop)
                        st.rerun()
        else:
            st.caption(t("Your list starts here. Use ＋ to add a company or fund."))
        st.caption(t("Select a row to update the chart. Yahoo Finance quotes may be delayed."))


def _index_chart_figure(ticker: str, snap: pd.DataFrame, *, tall: bool = False) -> tuple[go.Figure | None, pd.DataFrame]:
    bind_widget("idx_chart_range", "idx_chart_range_persist", "1D")
    bind_widget("idx_chart_type", "idx_chart_type_persist", "Candle")
    st.segmented_control(
        t("Chart type"),
        options=CHART_TYPES,
        key="idx_chart_type",
        on_change=remember_idx_chart_type,
        format_func=lambda kind: t(kind),
    )
    st.pills(
        t("Range"),
        list(CHART_RANGES.keys()),
        key="idx_chart_range",
        on_change=remember_idx_chart_range,
        label_visibility="collapsed",
        format_func=lambda rng: t(rng),
    )
    range_key = st.session_state.get("idx_chart_range") or "1D"
    if range_key not in CHART_RANGES:
        range_key = "1D"
    chart_type = st.session_state.get("idx_chart_type") or "Candle"
    spec = CHART_RANGES[range_key]
    with st.spinner(t("Loading index chart…")):
        series = download_ohlc(ticker, spec["period"], spec["interval"])
    if series.empty:
        st.info(t("No bars for this range yet. Markets may be closed, or Yahoo did not return data."))
        return None, series
    quote = lookup_snapshot(snap, ticker)
    prev_close = None
    if pd.notna(quote.get("last")) and pd.notna(quote.get("chg")):
        prev_close = float(quote["last"]) - float(quote["chg"])
    fig = build_price_chart(series, ticker, chart_type, previous_close=prev_close, range_key=range_key)
    if tall:
        fig.update_layout(height=720)
    help_chart(fig, f"price_{chart_type.lower()}", "index_price", width="stretch", config={"displayModeBar": False, "scrollZoom": True})
    return fig, series


def render_index_page() -> None:
    apply_pending_idx_switcher()
    ticker = st.session_state.selected_symbol
    if ticker not in INDEX_META:
        ticker = INDEX_ORDER[0]
        st.session_state.selected_symbol = ticker
    meta = INDEX_META[ticker]
    proxy = meta["proxy"]

    needed = tuple(dict.fromkeys([*INDEX_ORDER, proxy, *meta["related"]]))
    with st.spinner(t("Loading index quotes…")):
        try:
            snap_prices = download_prices(needed, "5d")
            history = download_prices((ticker,), "5y")
            peers = download_prices(tuple(INDEX_ORDER), "1y")
        except Exception:
            snap_prices, history, peers = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    snap = snapshot_from_prices(snap_prices)
    quote = lookup_snapshot(snap, ticker)

    if st.session_state.get("index_full_chart"):
        top_l, top_r = st.columns([3.4, 1])
        with top_l:
            st.markdown(
                f'<p class="quote-name">{html.escape(t(meta["name"]))}'
                f'<span class="quote-ticker">{html.escape(meta["display"])}</span></p>',
                unsafe_allow_html=True,
            )
        with top_r:
            if st.button(t("Exit full chart"), key="idx_exit_full", width="stretch"):
                st.session_state.index_full_chart = False
                st.rerun()
        last = quote.get("last", np.nan)
        chg = quote.get("chg", np.nan)
        chg_pct = quote.get("chg_pct", np.nan)
        unit_text = t(meta["unit"]) if meta["unit"] in ("point", "USD") else meta["unit"].upper()
        st.markdown(
            f'<div class="quote-last">{html.escape(format_last(ticker, last))} '
            f'<span class="last-unit">{html.escape(unit_text)}</span> '
            f'<span class="{chg_class(chg_pct)}">{html.escape(format_chg(chg))} {html.escape(format_chg(chg_pct, True))}</span></div>',
            unsafe_allow_html=True,
        )
        _index_chart_figure(ticker, snap, tall=True)
        st.caption(t("Full chart uses the same data as the index page. Weekends and closed hours stay hidden. Yahoo Finance; may be delayed."))
        return

    nav_l, nav_mid, nav_r = st.columns([1.35, 2.5, 2.3])
    with nav_l:
        if st.button(t("Back to home"), key="idx_back"):
            go_to("Home")
            st.rerun()
    with nav_mid:
        if "idx_switcher" not in st.session_state:
            st.session_state.idx_switcher = ticker if ticker in INDEX_ORDER else INDEX_ORDER[0]
        st.pills(
            "Index",
            INDEX_ORDER,
            format_func=lambda t: INDEX_META[t]["display"],
            key="idx_switcher",
            on_change=on_idx_switch,
            label_visibility="collapsed",
        )
    with nav_r:
        add_c, full_c = st.columns(2)
        with add_c:
            if st.button(f"＋ {proxy}", key="idx_add_proxy", help=t("Add {proxy} to Watchlist", proxy=proxy), width="stretch"):
                st.session_state.flash = add_to_watchlist(proxy)
                st.rerun()
        with full_c:
            if st.button(t("Full chart"), key="idx_full_chart", type="primary", width="stretch"):
                st.session_state.index_full_chart = True
                st.rerun()

    st.markdown(
        f'<p class="quote-name">{html.escape(t(meta["name"]))}'
        f'<span class="quote-ticker">{html.escape(meta["display"])}</span></p>'
        f'<p class="hero-sub">{html.escape(t(meta["members"]))} · {html.escape(t(meta["blurb"]))}</p>',
        unsafe_allow_html=True,
    )
    last = quote.get("last", np.nan)
    chg = quote.get("chg", np.nan)
    chg_pct = quote.get("chg_pct", np.nan)
    unit_text = t(meta["unit"]) if meta["unit"] in ("point", "USD") else meta["unit"].upper()
    st.markdown(
        f'<div class="quote-last">{html.escape(format_last(ticker, last))} '
        f'<span class="last-unit">{html.escape(unit_text)}</span> '
        f'<span class="{chg_class(chg_pct)}">{html.escape(format_chg(chg))} {html.escape(format_chg(chg_pct, True))}</span></div>',
        unsafe_allow_html=True,
    )
    now_et = pd.Timestamp.now(tz="America/New_York")
    st.caption(t("{session} · quotes via Yahoo Finance, may be delayed.", session=estimated_us_session(now_et)))

    _, series = _index_chart_figure(ticker, snap, tall=False)
    st.caption(t("Same four chart types as Home. Closed-market hours are hidden so the line stays continuous."))

    stats = session_bar_stats(series) if series is not None else {}
    if stats:
        range_key = st.session_state.get("idx_chart_range") or "1D"
        window = t("Session open") if range_key == "1D" else t("Range open")
        chips = st.columns(4)
        labels = [
            (window if range_key == "1D" else t("Range open"), stats.get("open")),
            (t("Session high") if range_key == "1D" else t("Range high"), stats.get("high")),
            (t("Session low") if range_key == "1D" else t("Range low"), stats.get("low")),
            (t("Prev close"), float(quote["last"]) - float(quote["chg"]) if pd.notna(quote.get("last")) and pd.notna(quote.get("chg")) else np.nan),
        ]
        for col, (label, value) in zip(chips, labels):
            shown = "—" if value is None or pd.isna(value) else f"{value:,.2f}"
            col.markdown(f'<div class="stat-chip"><div class="k">{label}</div><div class="v">{shown}</div></div>', unsafe_allow_html=True)

    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown(f"##### {t('What this index is')}")
        st.markdown(f'<div class="about-box"><p>{html.escape(t(meta["about"]))}</p></div>', unsafe_allow_html=True)

        st.markdown(f"##### {t('How it has moved')}")
        horizons = [(t("1 month"), 30), (t("6 months"), 182), (t("1 year"), 365), (t("5 years"), 365 * 5)]
        mcols = st.columns(4)
        for col, (label, days) in zip(mcols, horizons):
            value = trailing_return(history, ticker, days) if not history.empty else np.nan
            col.metric(label, format_chg(value, True) if pd.notna(value) else "—")

        if not history.empty:
            g = history[history["ticker"] == ticker].sort_values("date")
            if not g.empty:
                hi = float(g["close"].max())
                lo = float(g["close"].min())
                last_px = float(g["close"].iloc[-1])
                span = hi - lo
                pct_pos = 0 if span <= 0 else max(0, min(100, (last_px - lo) / span * 100))
                st.markdown(f"##### {t('5-year range')}")
                st.markdown(
                    f'<div class="range-track"><div class="range-dot" style="left:{pct_pos:.1f}%"></div></div>'
                    f'<div style="display:flex;justify-content:space-between;color:#6a6d78;font-size:0.82rem">'
                    f"<span>{t('Low {lo}', lo=f'{lo:,.2f}')}</span>"
                    f"<span>{t('Last {last}', last=f'{last_px:,.2f}')}</span>"
                    f"<span>{t('High {hi}', hi=f'{hi:,.2f}')}</span></div>",
                    unsafe_allow_html=True,
                )

    with right:
        st.markdown(f"##### {t('The other US indices')}")
        peer_rows = []
        for peer in INDEX_ORDER:
            row = lookup_snapshot(snap, peer)
            peer_rows.append({
                t("Index"): INDEX_META[peer]["display"],
                t("Last"): format_last(peer, row.get("last", np.nan)),
                t("Chg%"): format_chg(row.get("chg_pct", np.nan), True),
            })
        st.dataframe(pd.DataFrame(peer_rows), width="stretch", hide_index=True, height=148)

        if not peers.empty:
            pivot = peers.pivot_table(index="date", columns="ticker", values="close").dropna(how="all")
            if not pivot.empty:
                norm = pivot / pivot.bfill().iloc[0] * 100
                fig_cmp = go.Figure()
                colors = {"^GSPC": "#f23645", "^NDX": "#2962ff", "^DJI": "#131722"}
                for col_name in INDEX_ORDER:
                    if col_name not in norm.columns:
                        continue
                    fig_cmp.add_trace(go.Scatter(
                        x=norm.index,
                        y=norm[col_name],
                        mode="lines",
                        name=INDEX_META[col_name]["display"],
                        line=dict(color=colors.get(col_name, "#131722"), width=1.8),
                    ))
                fig_cmp.update_layout(
                    height=260, margin=dict(l=8, r=12, t=8, b=8),
                    paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                    hovermode="x unified",
                    yaxis_title=t("Start = 100"),
                )
                fig_cmp.update_xaxes(showgrid=False)
                fig_cmp.update_yaxes(gridcolor=GRID_COLOR, zeroline=False)
                restyle_chart(fig_cmp, height=260)
                fig_cmp.update_layout(showlegend=True)
                fig_cmp.add_hline(y=100, line_dash="dot", line_color=PREV_CLOSE_COLOR, line_width=1)
                help_chart(fig_cmp, "comparison", "index_comparison", width="stretch", config={"displayModeBar": False})
                st.caption(t("Each line starts at 100 one year ago, so you can compare path, not the raw index level."))

        st.markdown(f"##### {t('Names inside this index')}")
        st.caption(t("{proxy} is a fund that tracks {display}. The names below are well-known members, not a complete list.", proxy=proxy, display=meta["display"]))
        rel = st.columns(len(meta["related"]))
        for col, symbol in zip(rel, meta["related"]):
            row = lookup_snapshot(snap, symbol)
            label = f"{symbol} {format_chg(row.get('chg_pct', np.nan), True)}" if not pd.isna(row.get("chg_pct", np.nan)) else symbol
            if col.button(label, key=f"idx_rel_{symbol}", width="stretch"):
                st.session_state.selected_symbol = symbol
                go_to("Home")
                st.rerun()

    st.markdown(f"##### {t('How to read this page')}")
    st.markdown(t(
        "- **Full chart** hides the notes and enlarges the same quote chart.\n"
        "- **＋ {proxy}** adds a fund that follows this index to your watchlist. You cannot buy the index itself.\n"
        "- Header change is versus the **previous close**, not versus the left edge of the chart.\n"
        "- This is a classroom summary, not a trading terminal.",
        proxy=proxy,
    ))


def render_home() -> None:
    st.markdown(
        f'<div class="hero-title">{t("Stock market for beginner.")}</div>'
        f'<p class="hero-sub">{t("US stock market main indices")}</p>',
        unsafe_allow_html=True,
    )

    selected = st.session_state.selected_symbol
    needed = tuple(dict.fromkeys([*INDEX_ORDER, *st.session_state.get("watchlist", []), selected]))
    with st.spinner(t("Updating quotes…")):
        try:
            prices = download_prices(needed, "5d")
        except Exception:
            prices = pd.DataFrame()
    snap = snapshot_from_prices(prices)
    render_index_cards(snap)

    chart_col, list_col = st.columns([2.2, 1.15], gap="large")
    with chart_col:
        render_selected_chart(selected, snap)
    with list_col:
        render_watchlist_panel(snap, show_remove=True)


def render_selected_chart(ticker: str, snap: pd.DataFrame) -> None:
    quote = lookup_snapshot(snap, ticker)
    title_l, type_col, help_col, add_col = st.columns([2.05, 3.05, 0.7, 0.75])
    with title_l:
        st.markdown(
            f'<p class="quote-name">{html.escape(company_name(ticker))}'
            f'<span class="quote-ticker">{html.escape(display_symbol(ticker))}</span></p>',
            unsafe_allow_html=True,
        )
    with type_col:
        st.segmented_control(
            t("Chart type"),
            options=CHART_TYPES,
            key="chart_type",
            on_change=remember_chart_type,
            format_func=lambda kind: t(kind),
        )
    with help_col:
        chart_type = st.session_state.get("chart_type") or "Line"
        chart_help_button(f"price_{chart_type.lower()}", "home")
    with add_col:
        if st.button(t("Add ＋"), key="chart_add", help=t("Add this symbol to Watchlist"), type="secondary"):
            st.session_state.flash = add_to_watchlist(ticker)
            st.rerun()

    last = quote.get("last", np.nan)
    chg = quote.get("chg", np.nan)
    chg_pct = quote.get("chg_pct", np.nan)
    if is_index(ticker):
        raw_unit = INDEX_META[ticker]["unit"]
        unit = t(raw_unit) if raw_unit in ("point", "USD") else raw_unit.upper()
    else:
        unit = t("USD") if is_zh() else "USD"
    last_html = "—" if pd.isna(last) else (
        f"{last:,.2f}" if is_index(ticker) else f"${last:,.2f}"
    )
    st.markdown(
        f'<div class="quote-last">{last_html} <span class="last-unit">{html.escape(unit)}</span> '
        f'<span class="{chg_class(chg_pct)}">{html.escape(format_chg(chg))} {html.escape(format_chg(chg_pct, True))}</span></div>',
        unsafe_allow_html=True,
    )

    st.pills(
        t("Range"),
        list(CHART_RANGES.keys()),
        key="chart_range",
        on_change=remember_chart_range,
        label_visibility="collapsed",
        format_func=lambda rng: t(rng),
    )

    range_key = st.session_state.get("chart_range") or st.session_state.get("chart_range_persist") or "1D"
    if range_key not in CHART_RANGES:
        range_key = "1D"
    spec = CHART_RANGES[range_key]
    with st.spinner(t("Loading chart…")):
        series = download_ohlc(ticker, spec["period"], spec["interval"])
    if series.empty:
        st.info(t("No bars for this range yet. Markets may be closed, or Yahoo did not return data."))
    else:
        prev_close = None
        if pd.notna(quote.get("last")) and pd.notna(quote.get("chg")):
            prev_close = float(quote["last"]) - float(quote["chg"])
        fig = build_price_chart(
            series,
            ticker,
            st.session_state.get("chart_type") or st.session_state.get("chart_type_persist") or "Line",
            previous_close=prev_close,
            range_key=range_key,
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        as_of = to_new_york_time(series.index[-1])
        st.caption(t(
            "Range {range} · last bar {as_of}. Regular US hours only — nights, weekends, and holidays are hidden so the line stays continuous. Yahoo Finance / yfinance; may be delayed.",
            range=t(range_key), as_of=as_of.strftime("%Y-%m-%d %H:%M %Z"),
        ))
    if st.button(t("Open stock details")):
        go_to("Stock Research")
        st.rerun()


def load_universe(period: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    with st.spinner(t("Loading the starter universe from Yahoo Finance…")):
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


def render_markets(section: str) -> None:
    """Render each market tool directly from the top navigation."""
    descriptions = {
        "Market Overview": t("The wider market at a glance: group heatmaps, leading stocks, daily movers and volume."),
        "Screener": t("Find stocks by return, volatility and trading activity, then export your shortlist."),
        "Live Quotes": t("Follow intraday price, candles and volume, with a short list of symbols to monitor."),
        "Returns & Risk": t("Compare historical performance, volatility and drawdowns across stocks and ETFs."),
        "Stock Research": t("Explore one stock or index through price history, return metrics and company fundamentals."),
    }
    st.markdown(f'<div class="hero-title">{html.escape(t(section))}</div><p class="hero-sub">{html.escape(descriptions[section])}</p>', unsafe_allow_html=True)

    if section == "Live Quotes":
        render_live_quotes()
        return
    if section == "Stock Research":
        render_stock_details()
        return

    period_col, group_col = st.columns(2, gap="medium")
    with period_col:
        period = st.selectbox(
            t("Look-back window"),
            options=list(PERIOD_LABELS.keys()),
            format_func=period_label,
            key=lang_key("analysis_period"),
        )
    selected_sector = "All groups"
    if section != "Returns & Risk":
        with group_col:
            sector_options = ["All groups"] + sorted(set(UNIVERSE.values()))
            selected_sector = st.selectbox(
                t("Group filter"), options=sector_options, index=0, key=lang_key("market_group_filter"),
                format_func=lambda g: t(g),
            )

    prices, metrics, load_error = load_universe(period)
    if prices.empty:
        st.error(t("Could not load daily history. Check the network or Yahoo Finance, then retry."))
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

    if section == "Market Overview":
        render_overview(prices, prices_active, metrics, metrics_view, period)
    elif section == "Screener":
        render_screener(metrics_view)
    elif section == "Returns & Risk":
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
    k1.metric(t("Symbols loaded"), f"{loaded_tickers}", help=t("Starter watch universe, not the whole US market."))
    k2.metric(t("Average return · {period}", period=period_label(period)), pct(mean_return))
    k3.metric(t("Share with a positive return"), pct(positive_share))
    k4.metric(t("Median annualized volatility"), pct(median_vol))
    st.caption(t("As of {date} · {period} · {n} starter symbols", date=latest_date, period=period_label(period), n=len(UNIVERSE)))

    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        fig_heat = make_monthly_sector_heatmap(prices_active)
        if fig_heat is not None:
            help_chart(fig_heat, "heatmap", "heatmap", width="stretch", config={"displayModeBar": False})
        else:
            st.info(t("Not enough history in this window to draw the monthly heatmap."))
    with right:
        ranked = metrics_view.sort_values("Period return (%)", ascending=False).head(15)
        fig_rank = signed_hbar(ranked, "Period return (%)", "Ticker", t("Top 15 in this window"), t("Period return"))
        help_chart(fig_rank, "ranking", "ranking", width="stretch", config={"displayModeBar": False})

    st.subheader(t("Today's movers in the starter list"))
    stocks_only = metrics[~metrics["Ticker"].isin(["SPY", "QQQ", "DIA"])].copy()
    valid_daily = stocks_only["Day chg (%)"].dropna() if "Day chg (%)" in stocks_only.columns else pd.Series(dtype=float)
    breadth = st.columns(4)
    breadth[0].metric(t("Stocks watched"), f"{len(stocks_only)}")
    breadth[1].metric(t("Up"), f"{int((valid_daily > 0).sum())}")
    breadth[2].metric(t("Down"), f"{int((valid_daily < 0).sum())}")
    breadth[3].metric(t("Flat"), f"{int((valid_daily == 0).sum())}")

    movers_left, movers_right = st.columns(2, gap="large")
    with movers_left:
        if "Day chg (%)" in stocks_only.columns:
            gainers = stocks_only.dropna(subset=["Day chg (%)"]).nlargest(10, "Day chg (%)")
        else:
            gainers = pd.DataFrame()
        if not gainers.empty:
            fig_gainers = signed_hbar(gainers, "Day chg (%)", "Ticker", t("Gainers · top 10"), t("Day change"))
            help_chart(fig_gainers, "gainers", "gainers", width="stretch", config={"displayModeBar": False})
        else:
            st.info(t("Not enough data for a gainer list."))
    with movers_right:
        if "Day chg (%)" in stocks_only.columns:
            losers = stocks_only.dropna(subset=["Day chg (%)"]).nsmallest(10, "Day chg (%)")
        else:
            losers = pd.DataFrame()
        if not losers.empty:
            fig_losers = signed_hbar(losers, "Day chg (%)", "Ticker", t("Losers · bottom 10"), t("Day change"))
            help_chart(fig_losers, "losers", "losers", width="stretch", config={"displayModeBar": False})
        else:
            st.info(t("Not enough data for a loser list."))

    st.markdown(f"#### {t('Volume leaders')}")
    volume_rank = stocks_only.dropna(subset=["Volume"]).nlargest(10, "Volume")
    if not volume_rank.empty:
        ordered = volume_rank.sort_values("Volume")
        day_chg = ordered["Day chg (%)"] if "Day chg (%)" in ordered.columns else pd.Series(0, index=ordered.index)
        colors = [UP_COLOR if pd.notna(v) and v >= 0 else DOWN_COLOR for v in day_chg]
        fig_volume_rank = go.Figure(go.Bar(
            x=ordered["Volume"], y=ordered["Ticker"], orientation="h",
            marker_color=colors, marker_line_width=0,
            hovertemplate=t("%{y}: %{x:,.0f} shares<extra></extra>"),
        ))
        fig_volume_rank.update_layout(
            title=t("Highest volume in the latest session"),
            height=410, xaxis_title=t("Shares"), yaxis_title="",
            margin=dict(l=8, r=12, t=48, b=8),
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            showlegend=False,
        )
        fig_volume_rank.update_xaxes(tickformat="~s", gridcolor=GRID_COLOR)
        fig_volume_rank.update_yaxes(showgrid=False)
        help_chart(fig_volume_rank, "volume", "volume", width="stretch", config={"displayModeBar": False})

    st.subheader(t("Starter universe"))
    table_cols = ["Ticker", "Company", "Group", "Last", "Period return (%)", "Ann. volatility (%)", "Max drawdown (%)", "Avg volume", "Volume", "As of"]
    display_metrics = metrics_view.sort_values("Period return (%)", ascending=False)
    display_metrics = display_metrics[[c for c in table_cols if c in display_metrics.columns]].copy()
    if "Group" in display_metrics.columns:
        display_metrics["Group"] = display_metrics["Group"].map(lambda g: t(g))
    st.dataframe(
        display_metrics,
        width="stretch",
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn(t("Ticker")),
            "Company": st.column_config.TextColumn(t("Company")),
            "Group": st.column_config.TextColumn(t("Group")),
            "Last": st.column_config.NumberColumn(t("Last"), format="$%.2f"),
            "Period return (%)": st.column_config.NumberColumn(t("Period return (%)"), format="%.2f%%"),
            "Ann. volatility (%)": st.column_config.NumberColumn(t("Ann. volatility (%)"), format="%.2f%%"),
            "Max drawdown (%)": st.column_config.NumberColumn(t("Max drawdown (%)"), format="%.2f%%"),
            "Avg volume": st.column_config.NumberColumn(t("Avg volume"), format="%.0f"),
            "Volume": st.column_config.NumberColumn(t("Volume"), format="%.0f"),
            "As of": st.column_config.DateColumn(t("As of")),
        },
    )
    st.download_button(
        t("Download this table as CSV"),
        data=display_metrics.to_csv(index=False).encode("utf-8-sig"),
        file_name="stockscope_universe.csv",
        mime="text/csv",
    )


def render_screener(metrics_view: pd.DataFrame) -> None:
    st.subheader(t("Narrow the starter list by return and risk"))
    fc1, fc2, fc3 = st.columns(3)
    min_return = fc1.slider(t("Minimum period return (%)"), min_value=-100, max_value=200, value=-100, step=5)
    max_vol = fc2.slider(t("Maximum annualized volatility (%)"), min_value=0, max_value=150, value=150, step=5)
    sort_keys = ["Period return (%)", "Ann. volatility (%)", "Max drawdown (%)", "Avg volume"]
    sort_by = fc3.selectbox(t("Sort by"), sort_keys, index=0, format_func=lambda col: t(col))
    filtered = metrics_view[
        (metrics_view["Period return (%)"].fillna(-999) >= min_return)
        & (metrics_view["Ann. volatility (%)"].fillna(999) <= max_vol)
    ].copy()
    ascending = sort_by in ["Ann. volatility (%)", "Max drawdown (%)"]
    filtered = filtered.sort_values(sort_by, ascending=ascending)
    if "Group" in filtered.columns:
        filtered = filtered.copy()
        filtered["Group"] = filtered["Group"].map(lambda g: t(g))
    st.write(t("Symbols that match: **{n}**", n=len(filtered)))
    st.dataframe(
        filtered,
        width="stretch",
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn(t("Ticker")),
            "Company": st.column_config.TextColumn(t("Company")),
            "Group": st.column_config.TextColumn(t("Group")),
            "Last": st.column_config.NumberColumn(t("Last"), format="$%.2f"),
            "Day chg (%)": st.column_config.NumberColumn(t("Day change"), format="%.2f%%"),
            "Period return (%)": st.column_config.NumberColumn(t("Period return (%)"), format="%.2f%%"),
            "Ann. volatility (%)": st.column_config.NumberColumn(t("Ann. volatility (%)"), format="%.2f%%"),
            "Max drawdown (%)": st.column_config.NumberColumn(t("Max drawdown (%)"), format="%.2f%%"),
            "Avg volume": st.column_config.NumberColumn(t("Avg volume"), format="%.0f"),
            "Volume": st.column_config.NumberColumn(t("Volume"), format="%.0f"),
        },
    )
    st.download_button(
        t("Download screener CSV"),
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="stockscope_filtered_stocks.csv",
        mime="text/csv",
    )
    st.markdown(t(
        "**What the numbers mean:** period return uses the first and last valid close in the window; "
        "annualized volatility is the daily-return standard deviation × √252; "
        "max drawdown is the worst drop from a peak close."
    ))


def render_risk(prices: pd.DataFrame, metrics: pd.DataFrame, period: str) -> None:
    st.subheader(t("Compare return and volatility"))
    default = [sym for sym in ["AAPL", "MSFT", "NVDA", "SPY"] if sym in UNIVERSE]
    compare_tickers = st.multiselect(
        t("Symbols to compare"),
        options=list(UNIVERSE.keys()),
        default=default,
        format_func=ticker_label,
        help=t("Up to about eight names keeps the chart readable."),
    )
    if not compare_tickers:
        st.info(t("Pick at least one symbol."))
        return
    compare_data = prices[prices["ticker"].isin(compare_tickers)].copy()
    if compare_data.empty:
        st.warning(t("No history for those symbols in this window."))
        return
    normalized = compare_data.sort_values("date").copy()
    normalized["Indexed (start = 100)"] = normalized.groupby("ticker")["close"].transform(
        lambda s: s / s.dropna().iloc[0] * 100 if not s.dropna().empty else s
    )
    fig_line = px.line(
        normalized, x="date", y="Indexed (start = 100)", color="ticker",
        title=t("Rebased performance · {period}", period=period_label(period)),
        labels={"date": t("Date"), "ticker": t("Ticker"), "Indexed (start = 100)": t("Rebased (start = 100)")},
    )
    fig_line.add_hline(y=100, line_dash="dot", line_color=PREV_CLOSE_COLOR, line_width=1)
    fig_line.update_layout(
        height=470, hovermode="x unified",
        yaxis_title=t("Rebased level (start of window = 100)"),
        xaxis_title=t("Date"),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        legend_title_text=t("Ticker"),
    )
    fig_line.update_xaxes(showgrid=False)
    fig_line.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, side="right")
    help_chart(fig_line, "comparison", "comparison", width="stretch", config={"displayModeBar": False})
    st.caption(t("This is not the share price. Each series is rebased to 100 at the start of the window so you can compare percentage paths."))
    scat = metrics[metrics["Ticker"].isin(compare_tickers)].copy()
    if not scat.empty:
        fig_scatter = px.scatter(
            scat, x="Ann. volatility (%)", y="Period return (%)", color="Group", text="Ticker",
            hover_data={"Last": ":.2f", "Max drawdown (%)": ":.2f", "Avg volume": ":,.0f"},
            title=t("Return vs risk"),
        )
        fig_scatter.update_traces(textposition="top center", marker={"size": 12, "opacity": 0.8})
        fig_scatter.add_hline(y=0, line_dash="dot", line_color=PREV_CLOSE_COLOR, line_width=1)
        fig_scatter.update_layout(
            height=450, xaxis_title=t("Ann. volatility (%)"), yaxis_title=t("Period return (%)"),
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        )
        fig_scatter.update_xaxes(gridcolor=GRID_COLOR)
        fig_scatter.update_yaxes(gridcolor=GRID_COLOR, zeroline=True, zerolinecolor="#b2b5be")
        help_chart(fig_scatter, "risk", "risk", width="stretch", config={"displayModeBar": False})
    st.caption(t("Past return and volatility describe history. They are not a forecast."))


def render_stock_details() -> None:
    options = list(dict.fromkeys([
        st.session_state.selected_symbol,
        *INDEX_ORDER,
        *UNIVERSE.keys(),
    ]))
    if st.session_state.selected_symbol not in options:
        options.insert(0, st.session_state.selected_symbol)
    focus = st.selectbox(
        t("Symbol"),
        options=options,
        format_func=ticker_label,
        index=options.index(st.session_state.selected_symbol) if st.session_state.selected_symbol in options else 0,
        key=lang_key("stock_focus"),
    )
    st.session_state.selected_symbol = focus
    st.subheader(f"{company_name(focus)} · {display_symbol(focus)}")
    blurb = UNIVERSE.get(focus, INDEX_META.get(focus, {}).get("blurb", "Custom symbol"))
    st.caption(t(blurb))

    period = st.selectbox(t("History window"), options=list(PERIOD_LABELS.keys()), index=3, format_func=period_label, key=lang_key("stock_period"))
    with st.spinner(t("Loading this symbol…")):
        try:
            one_prices = download_prices((focus,), period)
        except Exception:
            one_prices = pd.DataFrame()
            st.warning(t("Could not load daily history. Check the network or Yahoo Finance, then retry."))
        series = download_ohlc(focus, period, "1d")
    if one_prices.empty and series.empty:
        st.warning(t("Yahoo did not return history for this symbol."))
        return
    metrics = calculate_metrics(one_prices) if not one_prices.empty else pd.DataFrame()
    m = metrics.iloc[0] if not metrics.empty else pd.Series(dtype=object)
    a, b, c, dcol = st.columns(4)
    a.metric(t("Last close"), format_last(focus, m.get("Last", np.nan)))
    b.metric(t("Period return"), pct(m.get("Period return (%)", np.nan)))
    c.metric(t("Ann. volatility"), pct(m.get("Ann. volatility (%)", np.nan)))
    dcol.metric(t("Max drawdown"), pct(m.get("Max drawdown (%)", np.nan)))

    if not series.empty:
        prev_close = None
        if isinstance(m, pd.Series) and pd.notna(m.get("Last")) and "Day chg (%)" in m.index and pd.notna(m.get("Day chg (%)")):
            last_px = float(m["Last"])
            prev_close = last_px / (1 + float(m["Day chg (%)"]) / 100) if float(m["Day chg (%)"]) != -100 else None
        price_fig = build_price_chart(series, focus, "Candle", previous_close=prev_close, range_key="1Y")
        help_chart(price_fig, "stock", "stock", width="stretch", config={"displayModeBar": False})
        st.caption(t("Daily OHLC candles. Weekends and holidays are hidden. Green = close ≥ open. Scale is zoomed to this window."))

    add_col, live_col = st.columns(2)
    if add_col.button(t("Add to watchlist"), width="stretch"):
        st.session_state.flash = add_to_watchlist(focus)
        st.rerun()
    if live_col.button(t("Open live quotes"), width="stretch"):
        go_to("Live Quotes")
        st.rerun()

    with st.expander(t("Optional Yahoo fundamentals (often incomplete)"), expanded=False):
        with st.spinner(t("Reading fundamentals…")):
            info = get_ticker_info(focus)
        fundamental_fields = [
            ("marketCap", t("Market cap"), money),
            ("trailingPE", t("P/E (TTM)"), lambda x: f"{x:.2f}x" if pd.notna(x) else "—"),
            ("forwardPE", t("Forward P/E"), lambda x: f"{x:.2f}x" if pd.notna(x) else "—"),
            ("priceToBook", t("Price / book"), lambda x: f"{x:.2f}x" if pd.notna(x) else "—"),
            ("revenueGrowth", t("Revenue growth"), lambda x: pct(x * 100) if pd.notna(x) else "—"),
            ("profitMargins", t("Profit margin"), lambda x: pct(x * 100) if pd.notna(x) else "—"),
            ("returnOnEquity", t("Return on equity"), lambda x: pct(x * 100) if pd.notna(x) else "—"),
            ("totalRevenue", t("Revenue"), money),
            ("freeCashflow", t("Free cash flow"), money),
            ("fiftyTwoWeekHigh", t("52-week high"), lambda x: f"${x:,.2f}" if pd.notna(x) else "—"),
            ("fiftyTwoWeekLow", t("52-week low"), lambda x: f"${x:,.2f}" if pd.notna(x) else "—"),
        ]
        if not info:
            st.warning(t("Yahoo did not return fundamentals. Price and volume still work."))
        else:
            fundamental_rows = []
            for key, label, formatter in fundamental_fields:
                value = info.get(key)
                try:
                    val_num = float(value) if value is not None else np.nan
                    shown = formatter(val_num)
                except (ValueError, TypeError):
                    shown = "—"
                fundamental_rows.append({t("Field"): label, t("Value"): shown})
            st.dataframe(pd.DataFrame(fundamental_rows), width="stretch", hide_index=True)
            st.caption(t("Confirm anything important in company filings. Yahoo fields vary by name and update schedule."))


def render_live_quotes() -> None:
    st.caption(t("This is a classroom feed, not an execution quote."))

    universe_options = list(dict.fromkeys([st.session_state.selected_symbol, *UNIVERSE.keys()]))
    default_live = st.session_state.selected_symbol if st.session_state.selected_symbol in universe_options else "AAPL"
    live_controls = st.columns([1.5, 1, 1.2, 1.4, 1.1])
    live_ticker = live_controls[0].selectbox(
        t("Symbol"),
        options=universe_options,
        index=universe_options.index(default_live) if default_live in universe_options else 0,
        format_func=ticker_label,
        key=lang_key("live_ticker"),
    )
    st.session_state.selected_symbol = live_ticker
    live_interval = live_controls[1].selectbox(
        t("Bar size"),
        options=["1m", "5m", "15m", "30m", "60m"],
        index=0,
        format_func=lambda x: t({"1m": "1 min", "5m": "5 min", "15m": "15 min", "30m": "30 min", "60m": "60 min"}[x]),
        key=lang_key("live_interval"),
    )
    refresh_label = live_controls[2].selectbox(
        t("Auto refresh"),
        options=["Manual", "Every 15s", "Every 30s", "Every 60s"],
        index=2,
        key=lang_key("live_refresh_mode"),
        format_func=lambda mode: t(mode),
    )
    refresh_seconds = {"Manual": None, "Every 15s": 15, "Every 30s": 30, "Every 60s": 60}[refresh_label]
    include_extended = live_controls[3].checkbox(t("Include pre/post"), value=True, key="live_extended")
    if live_controls[4].button(t("↻ Refresh now"), width="stretch", key="live_force_refresh"):
        download_intraday_one.clear()
        st.rerun()

    default_watch = [t for t in st.session_state.get("watchlist", ["AAPL", "MCD"]) if t in UNIVERSE][:6]
    live_watchlist = st.multiselect(
        t("Also watch (keep to six names to limit requests)"),
        options=list(UNIVERSE.keys()),
        default=default_watch,
        format_func=ticker_label,
        key=lang_key("live_watchlist"),
        help=t("Each row is the latest returned minute bar, not a time-and-sales print."),
    )
    interval_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "60m": 60}
    st.info(t(
        "Refresh is how often this app asks again. It is not a promise of a live or 15-minute-delayed feed. "
        "Yahoo / yfinance can lag, skip bars, or throttle."
    ))

    @st.fragment(run_every=refresh_seconds)
    def render_live_monitor(selected_symbol: str, selected_interval: str, extended: bool, watchlist_symbols: list[str]):
        now_et = pd.Timestamp.now(tz="America/New_York")
        st.caption(t(
            "New York time: {now} · {session} · auto refresh: {refresh}. "
            "The session label does not check exchange holidays.",
            now=now_et.strftime("%Y-%m-%d %H:%M:%S %Z"),
            session=estimated_us_session(now_et),
            refresh=t(refresh_label),
        ))
        try:
            intraday = download_intraday_one(selected_symbol, selected_interval, extended)
        except Exception as exc:
            st.error(t("Could not load minute bars. Network, Yahoo, or rate limits are the usual causes."))
            with st.expander(t("Technical error")):
                st.code(str(exc))
            intraday = pd.DataFrame()

        if intraday.empty:
            st.warning(t(
                "{symbol} did not return {interval} bars. "
                "If the US session is closed, wait for the next trading day, or turn off pre/post and retry.",
                symbol=selected_symbol, interval=selected_interval,
            ))
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
                status_text = t("Latest bar timestamp is slightly ahead of this clock; check again on the next refresh")
            elif age_minutes <= stale_threshold:
                status_text = t("Latest bar timestamp is close to now (not a live-data guarantee)")
            else:
                status_text = t("Latest bar looks stale; the session may be closed or the feed may have paused")
            st.caption(t(
                "{status} · bar time {bar_time} · about {age:.1f} minutes from this clock.",
                status=status_text, bar_time=last_ts_et.strftime("%Y-%m-%d %H:%M:%S %Z"), age=age_minutes,
            ))
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t("Last returned price"), f"${last_close:,.2f}", help=t("Close of the minute bar, not a trade print."))
            m2.metric(t("Vs previous bar"), f"{bar_change:+.2f}%" if pd.notna(bar_change) else "—")
            m3.metric(t("Bar volume"), f"{last_volume:,.0f}" if pd.notna(last_volume) else "—")
            m4.metric(t("Bars returned"), f"{len(valid):,}")

            live_fig = build_price_chart(valid, selected_symbol, "Candle", range_key="1D", include_extended=extended)
            help_chart(live_fig, "intraday", "intraday", width="stretch", config={"displayModeBar": False})
            st.caption(
                (t("Intraday OHLC candles including pre/post-market hours. ") if extended else
                 t("Intraday OHLC candles on regular US hours only (nights hidden). ")) +
                t("Green = that bar closed ≥ open. This is a classroom feed, not an exchange plot.")
            )

            with st.expander(t("Latest minute rows"), expanded=False):
                detail = valid.tail(30).copy()
                detail.index.name = "Time"
                st.dataframe(detail.sort_index(ascending=False), width="stretch")
                st.download_button(
                    t("Download minute CSV"),
                    data=detail.reset_index().to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"{selected_symbol}_{selected_interval}_intraday.csv",
                    mime="text/csv",
                    key=f"download_live_{selected_symbol}_{selected_interval}",
                )

        st.markdown(f"### {t('Watchlist bars')}")
        if not watchlist_symbols:
            st.info(t("Pick at least one extra symbol above."))
        else:
            records = []
            symbols = list(dict.fromkeys(watchlist_symbols[:6]))
            for symbol in symbols:
                try:
                    bars = download_intraday_one(symbol, selected_interval, extended)
                    if bars.empty:
                        records.append({
                            "Ticker": symbol, "Company": company_name(symbol),
                            "Last": np.nan, "Bar chg (%)": np.nan, "Bar volume": np.nan,
                            "Bar time (ET)": t("No data"), "Age (min)": np.nan, "Status": t("No data"),
                        })
                        continue
                    bars = bars.dropna(subset=["Close"]).sort_index()
                    latest = bars.iloc[-1]
                    latest_time = to_new_york_time(bars.index[-1])
                    now = pd.Timestamp.now(tz="America/New_York")
                    age = (now - latest_time).total_seconds() / 60
                    previous = float(bars["Close"].iloc[-2]) if len(bars) >= 2 else np.nan
                    change = (float(latest["Close"]) / previous - 1) * 100 if pd.notna(previous) and previous else np.nan
                    status = t("Fresh timestamp") if 0 <= age <= max(3, interval_minutes[selected_interval] * 2) else t("Check update status")
                    records.append({
                        "Ticker": symbol,
                        "Company": company_name(symbol),
                        "Last": float(latest["Close"]),
                        "Bar chg (%)": change,
                        "Bar volume": float(latest["Volume"]) if pd.notna(latest["Volume"]) else np.nan,
                        "Bar time (ET)": latest_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                        "Age (min)": age,
                        "Status": status,
                    })
                except Exception as exc:
                    records.append({
                        "Ticker": symbol, "Company": company_name(symbol),
                        "Last": np.nan, "Bar chg (%)": np.nan, "Bar volume": np.nan,
                        "Bar time (ET)": t("Request failed"), "Age (min)": np.nan, "Status": str(exc)[:80],
                    })
            quote_table = pd.DataFrame(records)
            st.dataframe(
                quote_table,
                width="stretch",
                hide_index=True,
                column_config={
                    "Ticker": st.column_config.TextColumn(t("Ticker")),
                    "Company": st.column_config.TextColumn(t("Company")),
                    "Last": st.column_config.NumberColumn(t("Last"), format="$%.2f"),
                    "Bar chg (%)": st.column_config.NumberColumn(t("Bar chg (%)"), format="%.2f%%"),
                    "Bar volume": st.column_config.NumberColumn(t("Bar volume"), format="%.0f"),
                    "Bar time (ET)": st.column_config.TextColumn(t("Bar time (ET)")),
                    "Age (min)": st.column_config.NumberColumn(t("Age (min)"), format="%.1f"),
                    "Status": st.column_config.TextColumn(t("Status")),
                },
            )
        st.caption(t("Age is only the gap between the bar timestamp and this clock, not the true exchange-to-screen delay."))

    render_live_monitor(live_ticker, live_interval, include_extended, live_watchlist)


def remember_learn_tab() -> None:
    if st.session_state.get("learn_tab"):
        st.session_state.learn_tab_persist = st.session_state.learn_tab


def render_learn() -> None:
    apply_pending_learn_tab()
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
            go_to("Live Quotes")
            st.rerun()
    with right:
        render_selected_chart(st.session_state.selected_symbol, snap)


def main() -> None:
    init_state()
    apply_pending_widgets()
    st.markdown(APP_STYLE, unsafe_allow_html=True)
    st.markdown(language_css(), unsafe_allow_html=True)
    render_top_nav()

    nav = st.session_state.nav
    st.session_state.learn_embedded = nav == "Lesson"
    if nav == "Lesson":
        render_learning_page()
    elif nav == "Home":
        render_home()
    elif nav == "Index":
        render_index_page()
    elif nav in TOP_NAV[1:]:
        render_markets(nav)
    else:
        render_home()

    render_study_launcher()

    st.markdown(
        f"<div class='site-footer'>{t('StockScope · classroom prototype · verify definitions and data rights yourself. This tool is not investment advice.')}</div>",
        unsafe_allow_html=True,
    )


main()
