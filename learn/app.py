from __future__ import annotations

from typing import Iterable
from pathlib import Path
from html import escape
import json
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf


def _bootstrap_i18n() -> None:
    dashboard_dir = str(Path(__file__).resolve().parents[1] / "dashboard")
    if dashboard_dir not in sys.path:
        sys.path.insert(0, dashboard_dir)


_bootstrap_i18n()
from i18n import init_language, lang_key, peek_lang, plotly_font, render_language_toggle, t


# ============================================================
# Page setup and visual system
# ============================================================
_EMBEDDED = bool(st.session_state.get("learn_embedded", False))
if not _EMBEDDED:
    init_language()
    st.set_page_config(
        page_title=t("StockScope Learn | Beginner Stock Academy") if peek_lang() == "zh-HK" else "StockScope Learn | Beginner Stock Academy",
        page_icon="📚", layout="wide", initial_sidebar_state="expanded",
    )
_style_scope = ".st-key-learning_content" if _EMBEDDED else ".stApp"
st.markdown('<span class="learning-style-marker"></span>' +
            Path(__file__).with_name("styles.css").read_text().replace("@SCOPE@", _style_scope),
            unsafe_allow_html=True)
if not _EMBEDDED:
    st.markdown('<style>.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"],[data-testid="stSidebar"]{background:#fff;color:#131722;}</style>', unsafe_allow_html=True)


# ============================================================
# Data and learning content
# ============================================================
TICKERS: dict[str, str] = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "META": "Meta Platforms",
    "AMD": "AMD",
    "TSLA": "Tesla",
    "JPM": "JPMorgan Chase",
    "WMT": "Walmart",
    "COST": "Costco",
    "KO": "Coca-Cola",
    "XOM": "Exxon Mobil",
    "LLY": "Eli Lilly",
    "SPY": 'S&P 500 ETF proxy',
    "QQQ": 'Nasdaq-100 ETF proxy',
    "EFA": 'Developed markets ETF proxy',
    "EEM": 'Emerging markets ETF proxy',
    "EWJ": 'Japan equity ETF proxy',
    "FXI": 'China large-cap ETF proxy',
    "BND": 'Vanguard Total Bond Market ETF (US aggregate bonds)',
    "SGOV": 'iShares 0-3 Month Treasury Bond ETF (short-term US Treasuries)',
}

PERIODS = {
    "5d": 'Last 5 days',
    "1mo": 'Last month',
    "3mo": 'Last 3 months',
    "6mo": 'Last 6 months',
    "1y": 'Last year',
    "5y": 'Last 5 years',
    "10y": 'Last 10 years',
    "max": 'All available history',
}

# Original StockScope lesson plan inspired by the public instructional structure of
# IBKR Traders' Academy (sequenced beginner courses, short lesson units, examples,
# practice checks, and progress tracking). Lesson text and exercises below are
# independently written for this student project.
LESSON_GUIDE = {
    'Stock Market Basics': {
        "time": 'About 10–12 minutes',
        "objective": 'Explain share ownership, primary and secondary markets, market participants, how prices form, returns and key risks.',
        "learn": 'Start with why companies issue shares, then learn who participates and how stocks differ from other investments.',
        "explore": 'Build number skills by calculating market capitalization, ownership percentage and a simple total return.',
        "practice": 'Complete the knowledge check and explain your reasoning using price, share count and risk.',
        "reflect": 'If someone says a company is more expensive just because its share price is higher, what other information would you check?',
    },
    'Reading Stock Charts': {
        "time": 'About 8–10 minutes',
        "objective": 'Identify open, high, low and close (OHLC), explain volume, and understand why a chart cannot prove what happens next.',
        "learn": 'Learn the meaning of open, high, low, close and trading volume.',
        "explore": 'Choose a security and hover over candles and volume bars to compare dates.',
        "practice": 'Explain what a sudden increase in volume can mean; try again if needed.',
        "reflect": 'Besides colour, what information should you check when reading a candlestick chart?',
    },
    'Candlestick Patterns': {
        "time": 'About 15–25 minutes',
        "objective": 'Recognise common single-candle, two-candle, three-candle and continuation patterns. Explain why trend, location and confirmation matter.',
        "learn": 'Learn bodies, upper and lower wicks, and proportions; then explore single and multiple-candle patterns.',
        "explore": 'Compare synthetic candle examples, then look for similar structures in real historical prices.',
        "practice": 'Answer pattern and context questions, review explanations and try again.',
        "reflect": 'When you recognise a pattern, which three types of context would you check?',
    },
    'Technical Indicators': {
        "time": 'About 25–35 minutes',
        "objective": 'Understand SMA, EMA, RSI, MACD, Stochastic, Bollinger Bands, ADX and OBV, plus support and resistance, Fibonacci retracement, VWAP and Ichimoku Cloud.',
        "learn": 'Start with the question each indicator answers, then learn its calculation, settings, interpretation and limitations.',
        "explore": 'Switch overlays and indicator panes on historical candlesticks. Compare signals with the trend and possible failure cases.',
        "practice": 'Use chart evidence to distinguish direction, momentum, volatility and price/volume relationships.',
        "reflect": 'Which signals use the same price data, and which observations still need independent evidence?',
    },
    'How Orders Work': {
        "time": 'About 8–10 minutes',
        "objective": "Describe a trade's main steps and the trade-offs between market, limit and stop orders.",
        "learn": 'Work through securities, brokers, order types, costs and execution records.',
        "explore": 'Use fictional bid and ask quotes to calculate the spread and compare price control with execution priority.',
        "practice": 'Choose an order approach for a scenario and review why execution is uncertain.',
        "reflect": 'Why can a limit order control the acceptable price without guaranteeing a fill?',
    },
    'Researching a Company': {
        "time": 'About 15–20 minutes',
        "objective": 'Build a picture of a business from its model, three financial statements, key ratios and reliable sources.',
        "learn": 'Use a familiar business to understand revenue, costs and profit, then read the income statement, balance sheet and cash flow statement.',
        "explore": 'Explore consistent fictional company accounts and change ratio inputs to see the effect.',
        "practice": 'Investigate a case where revenue rises but cash flow falls, then choose the next evidence to check.',
        "reflect": 'Which evidence most changed your view of the company, and what is still missing?',
    },
    'Why Stock Prices Move': {
        "time": 'About 6–8 minutes',
        "objective": 'Distinguish company, industry, economic and market influences. Avoid confusing events happening together with proof of cause.',
        "learn": 'Learn how earnings, interest rates, expectations, competition, liquidity and unexpected events can matter.',
        "explore": 'Compare actual results, earlier expectations and forward guidance in a case study.',
        "practice": 'Explain why a stock can fall even when profit grows.',
        "reflect": 'If a stock rises after a news story, what else would you check before explaining the cause?',
    },
    'Risk & Investor Protection': {
        "time": 'About 6–8 minutes',
        "objective": 'Recognise market risks, behavioural biases and investment scam warning signs, and know where to check information.',
        "learn": 'Explore the risk map, account security and common scam signals.',
        "explore": 'Work through a pre-investment checklist for a hypothetical situation.',
        "practice": 'Assess a social-media investment group promising high returns and demanding an urgent transfer.',
        "reflect": 'What three things would you verify before making an investment?',
    },
}



def ticker_label(symbol: str) -> str:
    return f"{symbol} · {t(TICKERS.get(symbol, symbol))}"


@st.cache_data(ttl=1800, show_spinner=False)
def load_prices(tickers: tuple[str, ...], period: str) -> pd.DataFrame:
    """Download daily adjusted OHLCV history via yfinance for learning/analysis prototype."""
    cols = ["date", "ticker", "open", "high", "low", "close", "volume"]
    if not tickers:
        return pd.DataFrame(columns=cols)

    raw = yf.download(
        tickers=list(tickers),
        period=period,
        interval="1d",
        auto_adjust=True,
        group_by="ticker",
        progress=False,
        threads=True,
        timeout=20,
    )
    if raw is None or raw.empty:
        return pd.DataFrame(columns=cols)

    frames: list[pd.DataFrame] = []
    fields = {"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
    for symbol in tickers:
        if isinstance(raw.columns, pd.MultiIndex):
            level0 = raw.columns.get_level_values(0)
            level1 = raw.columns.get_level_values(1)
            if symbol in level0:
                one = raw[symbol].copy()
            elif symbol in level1:
                one = raw.xs(symbol, axis=1, level=1).copy()
            else:
                continue
        elif len(tickers) == 1:
            one = raw.copy()
        else:
            continue

        rename: dict[str, str] = {}
        for original, target in fields.items():
            found = next((c for c in one.columns if str(c).lower() == original.lower()), None)
            if found is not None:
                rename[found] = target
        one = one.rename(columns=rename)
        if "close" not in one.columns:
            continue
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in one.columns:
                one[col] = np.nan
        idx = pd.DatetimeIndex(one.index)
        if idx.tz is not None:
            idx = idx.tz_localize(None)
        one = one[["open", "high", "low", "close", "volume"]].copy()
        one["date"] = idx
        one["ticker"] = symbol
        frames.append(one.reset_index(drop=True))

    if not frames:
        return pd.DataFrame(columns=cols)
    result = pd.concat(frames, ignore_index=True)
    for c in ["open", "high", "low", "close", "volume"]:
        result[c] = pd.to_numeric(result[c], errors="coerce")
    result = result.dropna(subset=["date", "close"]).drop_duplicates(["ticker", "date"], keep="last").sort_values(["ticker", "date"]).reset_index(drop=True)
    return result[cols]


def safe_prices(tickers: Iterable[str], period: str) -> tuple[pd.DataFrame, str | None]:
    try:
        data = load_prices(tuple(dict.fromkeys(tickers)), period)
        if data.empty:
            return data, t('No market data was returned. Check your connection or try again later.')
        return data, None
    except Exception as exc:
        return pd.DataFrame(columns=["date", "ticker", "open", "high", "low", "close", "volume"]), str(exc)







def find_dual_golden_cross_case(data: pd.DataFrame, future_bars: int = 20, max_gap: int = 3) -> dict | None:
    """Find a real daily-price window where MA5 crosses above MA20 and MACD crosses above its signal line nearby.

    The source dataframe must contain Yahoo Finance adjusted daily OHLCV rows in the app's normalized schema.
    It selects a historical event with enough subsequent sessions for an honest reveal exercise.
    """
    if data is None or data.empty:
        return None

    candidates: list[dict] = []
    required_symbols = ("NVDA", "AAPL", "MSFT", "AMD", "SPY", "QQQ")
    for symbol in required_symbols:
        frame = data.loc[data["ticker"] == symbol].copy().sort_values("date").reset_index(drop=True)
        if len(frame) < 90:
            continue
        close = pd.to_numeric(frame["close"], errors="coerce")
        frame["ma5"] = close.rolling(5, min_periods=5).mean()
        frame["ma20"] = close.rolling(20, min_periods=20).mean()
        ema12 = close.ewm(span=12, adjust=False, min_periods=12).mean()
        ema26 = close.ewm(span=26, adjust=False, min_periods=26).mean()
        frame["macd"] = ema12 - ema26
        frame["macd_signal"] = frame["macd"].ewm(span=9, adjust=False, min_periods=9).mean()
        frame["macd_hist"] = frame["macd"] - frame["macd_signal"]

        ma_cross = (frame["ma5"] > frame["ma20"]) & (frame["ma5"].shift(1) <= frame["ma20"].shift(1))
        macd_cross = (frame["macd"] > frame["macd_signal"]) & (frame["macd"].shift(1) <= frame["macd_signal"].shift(1))
        ma_indices = np.flatnonzero(ma_cross.fillna(False).to_numpy())
        macd_indices = np.flatnonzero(macd_cross.fillna(False).to_numpy())

        for ma_idx in ma_indices:
            nearby_macd = [int(idx) for idx in macd_indices if abs(int(idx) - int(ma_idx)) <= max_gap]
            for macd_idx in nearby_macd:
                anchor_idx = max(int(ma_idx), int(macd_idx))
                # Reserve the full post-signal window; do not accidentally reveal partial/incomplete examples.
                if anchor_idx < 60 or anchor_idx + future_bars >= len(frame):
                    continue
                candidates.append({
                    "ticker": symbol,
                    "data": frame,
                    "anchor_idx": anchor_idx,
                    "ma_cross_idx": int(ma_idx),
                    "macd_cross_idx": int(macd_idx),
                    "gap": abs(int(ma_idx) - int(macd_idx)),
                    "date": pd.Timestamp(frame.iloc[anchor_idx]["date"]),
                })

    if not candidates:
        return None
    # Prefer the most recent usable historical example; when event dates tie, prefer the closest crossover pair.
    return max(candidates, key=lambda item: (item["date"], -item["gap"]))




@st.cache_data(ttl=86400, show_spinner=False)
def load_dual_golden_cross_case() -> dict | None:
    """Fetch five years of real Yahoo Finance daily history and select a double-bullish-crossover case."""
    symbols = ("NVDA", "AAPL", "MSFT", "AMD", "SPY", "QQQ")
    raw = load_prices(symbols, "5y")
    if raw is None or raw.empty:
        return None
    # Keep the exercise strictly historical and stop the visible/revealed window by 2026-10-06.
    cutoff = pd.Timestamp("2026-10-06")
    raw = raw.loc[pd.to_datetime(raw["date"]).dt.tz_localize(None) <= cutoff].copy()
    return find_dual_golden_cross_case(raw, future_bars=20, max_gap=3)


def dual_signal_figure(
    case_window: pd.DataFrame,
    x_end: pd.Timestamp,
    reveal_future: bool,
    ma_cross_date: pd.Timestamp,
    macd_cross_date: pd.Timestamp,
    height: int = 700,
) -> go.Figure:
    """Build a continuous 3-panel price/volume/MACD chart; reveal arrow-free signal labels after an answer."""
    data = case_window.copy().sort_values("date").reset_index(drop=True)
    visible_data = data.copy() if reveal_future else data.loc[data["is_future"] == False].copy()

    # Keep the panels clean: chart context is explained by the legend and axes, not duplicate titles.
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.035,
        row_heights=[0.61, 0.15, 0.24],
    )
    candle_up = "#22c55e"   # Green = up
    candle_down = "#ef4444" # Red = down
    fig.add_trace(go.Candlestick(
        x=visible_data["date"], open=visible_data["open"], high=visible_data["high"],
        low=visible_data["low"], close=visible_data["close"], name='Candles (green up / red down)',
        increasing_line_color=candle_up, decreasing_line_color=candle_down,
        increasing_fillcolor=candle_up, decreasing_fillcolor=candle_down,
        whiskerwidth=0.55,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=visible_data["date"], y=visible_data["ma5"], mode="lines", name='SMA 5 (5-day simple moving average)',
        line=dict(color="#a66a00", width=2.7), connectgaps=False,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=visible_data["date"], y=visible_data["ma20"], mode="lines", name='SMA 20 (20-day simple moving average)',
        line=dict(color="#2563eb", width=2.7), connectgaps=False,
    ), row=1, col=1)

    volume_colors = [candle_up if float(c) >= float(o) else candle_down
                     for o, c in zip(visible_data["open"], visible_data["close"])]
    fig.add_trace(go.Bar(
        x=visible_data["date"], y=visible_data["volume"], name='Volume (candle colours)',
        marker_color=volume_colors, opacity=0.9,
    ), row=2, col=1)

    macd_hist_colors = [candle_up if float(v) >= 0 else candle_down for v in visible_data["macd_hist"].fillna(0)]
    fig.add_trace(go.Bar(
        x=visible_data["date"], y=visible_data["macd_hist"], name='MACD histogram (positive green / negative red)',
        marker_color=macd_hist_colors, opacity=0.88,
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=visible_data["date"], y=visible_data["macd"], mode="lines", name='MACD line',
        line=dict(color="#7c3aed", width=2.8), connectgaps=False,
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=visible_data["date"], y=visible_data["macd_signal"], mode="lines", name='Signal line',
        line=dict(color="#a66a00", width=2.4), connectgaps=False,
    ), row=3, col=1)

    first_date = pd.Timestamp(data.iloc[0]["date"])
    last_date = pd.Timestamp(x_end)
    # Before submit, show only the observed lead-in in the left column; the answer panel occupies
    # the space where the future section will appear. After submit, the same chart widens and
    # the real future candles append to the right without a placeholder or break.
    chart_end = last_date if reveal_future else pd.Timestamp(visible_data.iloc[-1]["date"])

    # Signal markers and labels deliberately appear only after the learner submits an answer.
    if reveal_future:
        for event_date, trace_name, row_no, y_key, color, symbol, label in [
            (pd.Timestamp(ma_cross_date), 'SMA 5 crosses above SMA 20', 1, "ma5", "#a66a00", "triangle-up", 'SMA 5 crosses above<br>SMA 20'),
            (pd.Timestamp(macd_cross_date), 'MACD line crosses above signal line', 3, "macd", "#7c3aed", "diamond", 'MACD line crosses above signal line'),
        ]:
            event_row = data.loc[data["date"] == event_date]
            if event_row.empty:
                continue
            event_y = float(event_row.iloc[0][y_key])
            fig.add_trace(go.Scatter(
                x=event_row["date"], y=event_row[y_key], mode="markers", name=trace_name,
                marker=dict(color=color, size=16, symbol=symbol, line=dict(color="#07111f", width=2)),
                hovertemplate=f"%{{x|%Y-%m-%d}}<br>{trace_name}<extra></extra>",
            ), row=row_no, col=1)
            # Put a high-contrast label directly on the panel where the event occurs.
            fig.add_annotation(
                x=event_date, y=event_y, row=row_no, col=1, text=label,
                showarrow=False,
                xshift=28 if row_no == 1 else 20,
                yshift=78 if row_no == 1 else -46,
                bgcolor="#ffffff", bordercolor=color, borderwidth=1.5,
                borderpad=6, font=dict(size=13, color="#131722"), align="left",
            )
        for event_date, color, dash in [
            (pd.Timestamp(ma_cross_date), "#a66a00", "dot"),
            (pd.Timestamp(macd_cross_date), "#7c3aed", "dash"),
        ]:
            fig.add_shape(
                type="line", xref="x", yref="paper", x0=event_date, x1=event_date, y0=0, y1=1,
                line=dict(color=color, width=2, dash=dash), layer="above",
            )

    fig.update_layout(
        template="plotly_white",
        title=None,
        height=height, hovermode="x unified", margin=dict(l=25, r=24, t=108, b=38),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.025, xanchor="left", x=0,
            font=dict(size=12, color="#131722"),
            bgcolor="#ffffff", bordercolor="#8ba2bd", borderwidth=1.5,
        ),
        barmode="overlay", xaxis_rangeslider_visible=False,
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(color="#131722", family=plotly_font(), size=13),
        hoverlabel=dict(bgcolor="#ffffff", font_color="#131722", font_size=13, bordercolor="#8ba2bd"),
    )
    fig.update_xaxes(
        range=[first_date - pd.Timedelta(days=1), chart_end + pd.Timedelta(days=2)],
        rangeslider_visible=False, showgrid=True, gridcolor="rgba(180,204,232,.15)",
        linecolor="rgba(180,204,232,.35)", tickfont=dict(color="#6a6d78", size=11),
    )
    fig.update_yaxes(title_text='Price (USD)', row=1, col=1, gridcolor="rgba(180,204,232,.15)", tickfont=dict(color="#6a6d78", size=11))
    fig.update_yaxes(title_text='Volume', tickformat="~s", row=2, col=1, gridcolor="rgba(180,204,232,.15)", tickfont=dict(color="#6a6d78", size=11))
    fig.update_yaxes(title_text="MACD / Signal", row=3, col=1, zeroline=True, zerolinecolor="rgba(180,204,232,.38)", gridcolor="rgba(180,204,232,.15)", tickfont=dict(color="#6a6d78", size=11))
    return fig


def render_technical_indicator_lesson(choice: str) -> None:
    """Render the concise explanation for one selected indicator."""
    lessons: dict[str, tuple[str, str]] = {
        'Candles only': (
            'Start with price, then choose a question',
            """Candlesticks show open, high, low and close. First describe whether prices are generally rising, falling or moving sideways. Indicators reorganise existing price or volume data.

| What would you like to understand? | Tools |
|---|---|
| Average price direction | SMA, EMA |
| Momentum | RSI, MACD, Stochastic |
| Volatility | Bollinger Bands |
| Trend strength | ADX |
| Price and volume alignment | OBV |
| Price areas to watch | Support/resistance, Fibonacci retracement |
""",
        ),
        'MA | Simple Moving Average (SMA 5 / SMA 20)': (
            'SMA | The direction of average prices',
            """**What does it do?** A Simple Moving Average smooths recent closing prices into a line.

**How to read it**
- **Slope:** rising means average prices are increasing; falling means they are decreasing.
- **Price position:** being above or below the average is context, not a promise of a return to it.
- **Crossovers:** SMA 5 reacts faster than SMA 20. A shorter average crossing above a longer one is a bullish crossover; below is a bearish crossover.
- **Length:** shorter settings react faster but are noisier; longer settings are smoother but respond later.
""",
        ),
        'EMA | Exponential Moving Average (EMA 12 / EMA 26)': (
            'EMA | More weight on recent prices',
            """**What does it do?** An Exponential Moving Average gives more weight to recent prices than an SMA of the same length.

**How to read it** Look at direction, price relative to the lines, and the distance between EMA 12 and EMA 26. A widening gap means they are moving apart; a narrowing gap means they are converging. A crossover describes a changed historical relationship, not a prediction.

**Settings:** shorter lengths are more sensitive and can produce more noise. EMA 12 and EMA 26 are common MACD inputs.
""",
        ),
        'Bollinger Bands (20, 2)': (
            'Bollinger Bands | Price position and volatility',
            """**What do they show?** A 20-period SMA with upper and lower bands two standard deviations away is a common setting.

- **Wider bands:** greater recent variability, without guaranteeing direction.
- **Narrower bands:** quieter recent prices; they do not predict the direction of a future breakout.
- **Near a band:** price is high or low relative to its recent average. A strong trend may stay near a band.
- **Back to the middle:** a move toward the average does not guarantee a reversal.

For example, a middle band at $100 and outer bands at $90 and $110 describe a $90–$110 range. More variability generally widens the bands.
""",
        ),
        'RSI(14)': (
            'RSI | Relative Strength Index: recent momentum',
            """**What does it show?** RSI compares the size of recent gains and losses on a 0–100 scale. It compares one security with its own recent history, not with other stocks.

- **Above 70:** a common overbought reference; it does not guarantee an immediate fall.
- **Below 30:** a common oversold reference; it does not guarantee a rebound.
- **Around 50:** a reference for the balance of recent momentum.
- **Divergence:** price makes a new high or low while RSI does not. Investigate further rather than assuming a reversal.
""",
        ),
        'MACD(12, 26, 9)': (
            'MACD | Moving Average Convergence Divergence',
            """**What does it show?** MACD compares fast and slow EMAs to describe trend and momentum. It uses price, not volume.

**Three parts**
- **MACD line:** fast EMA minus slow EMA.
- **Signal line:** a smoothed average of the MACD line.
- **Histogram:** MACD line minus signal line; this app does not multiply it by two.

A crossover above or below the signal line describes a change in their relationship. Above zero, the fast EMA exceeds the slow EMA. A growing histogram shows the lines moving apart; a shrinking one shows them moving together.
""",
        ),
        'Stochastic': (
            'Stochastic | Where the close sits in the recent range',
            """**What does it show?** Stochastic compares the close with the recent high/low range. It uses %K and a smoother %D, usually on a 0–100 scale.

- **Around/above 80:** close is near the upper end; often called overbought.
- **Around/below 20:** close is near the lower end; often called oversold.
- **Crossovers:** changes in short-term momentum need trend and location context.

RSI compares gain/loss magnitudes; Stochastic emphasises the close's position inside a range. They are related, but different.
""",
        ),
        'ADX (trend strength)': (
            'ADX | Trend strength; +DI / −DI give direction context',
            """**What does it show?** Average Directional Index measures trend strength, not whether the trend is up or down. +DI and −DI compare directional movement.

- **ADX rising:** the trend may be strengthening in either direction.
- **ADX falling:** trend strength may be weakening, without guaranteeing reversal.
- **+DI above −DI:** relatively stronger upward directional movement; the reverse favours downward movement.
- **20 / 25:** common reference levels, not universal rules.
""",
        ),
        'OBV (On Balance Volume)': (
            'OBV | Is cumulative volume moving with price?',
            """**What does it show?** On Balance Volume adds volume when the close rises, subtracts it when the close falls, and leaves it unchanged for an unchanged close.

- Price and OBV rising/falling together can suggest alignment.
- A new price high without a new OBV high deserves a closer look.
- Directional OBV during sideways prices is a clue to investigate, not proof of a future breakout.

OBV cannot identify traders or prove actual money inflows and outflows.
""",
        ),
        'Support and Resistance': (
            'Support and resistance | Areas where prices have reacted',
            """**What are they?** Support is an area where falls have previously paused or reversed; resistance is an area where rises have paused or reversed. Neither is an unbreakable wall.

1. Look for swing highs and lows.
2. Check for repeated reactions near similar prices.
3. Think in areas rather than an exact cent.
4. Watch bodies, wicks, closes and volume; after a breakout, check subsequent action or a retest.

**This chart:** the automatic lines show the selected window's highest and lowest prices. They do not automatically identify repeatedly tested supply/demand areas.
""",
        ),
        'VWAP (concept)': (
            'VWAP | Volume Weighted Average Price',
            """**What is it?** VWAP weights prices by trading volume and usually resets each trading day. It is used to describe intraday prices and assess execution.

**How to read it:** above/below VWAP means price is above/below the volume-weighted average so far. Repeated crossings alone do not identify a lasting direction.

**Starting point matters:** different sessions and anchors produce different values. Being above VWAP does not prove more buyers or guarantee a rise.

**This course:** daily OHLCV does not contain every trade's price and timing. We teach the concept without drawing a supposedly precise intraday VWAP from daily bars.
""",
        ),
        'Ichimoku Cloud (concept)': (
            'Ichimoku Cloud | Conversion Line, Base Line and the cloud',
            """**What is it?** Ichimoku Cloud combines trend, price position and possible support/resistance context. Common settings are 9, 26 and 52.

- **Conversion Line:** shorter-term price balance.
- **Base Line:** longer-term price balance.
- **Leading Span A / B:** form the cloud, plotted ahead.
- **Lagging Span:** the current close shifted back for comparison.

Price above/below the cloud can suggest a stronger/weaker background; inside it may be less clear. Crossovers need price location and subsequent action for context.

Plotting a cloud ahead does not mean it knows future prices: it shifts already calculated values. Settings and plotting conventions can differ between platforms.
""",
        ),
    }

    if choice not in lessons:
        st.info('This indicator lesson is not available. Choose another indicator above.')
        return

    title, lesson_markdown = lessons[choice]
    content_heading(title)
    st.markdown(lesson_markdown)


def render_final_answer_review(number: int, question: str, options: list[str], selected: int,
                               correct: int, explanation: str, lesson: str) -> None:
    """Render review cards with green correct results and red incorrect results."""
    is_correct = selected == correct
    card_class = "quiz-correct" if is_correct else "quiz-incorrect"
    status = '✓ Correct' if is_correct else '✕ Incorrect · review this topic'
    rows = []
    alphabet = "ABCD"
    for idx, option in enumerate(options):
        option_class = "quiz-review-option"
        marker = alphabet[idx]
        suffix = ""
        if idx == correct:
            option_class += " answer-correct"
            suffix = ' (correct answer)'
        if idx == selected and selected != correct:
            option_class += " answer-wrong"
            suffix = ' (your choice)'
        elif idx == selected and selected == correct:
            suffix = ' (your choice)'
        rows.append(
            f'<div class="{option_class}"><span class="option-marker">{marker}</span>'
            f'<span>{escape(str(option))}<b>{escape(suffix)}</b></span></div>'
        )
    st.markdown(
        f"""<div class="quiz-review-card {card_class}"><div class="quiz-review-head"><div class="quiz-review-title">Question {number:02d} | {escape(question)}</div><span class="quiz-review-status">{status}</span></div>{''.join(rows)}<div class="quiz-review-explanation"><b>Explanation:</b>{escape(explanation)}</div></div>""",
        unsafe_allow_html=True,
    )
    st.caption(f'Related lesson: {lesson}')










def style_fig(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#131722", family=plotly_font(), size=13),
        height=height,
        margin=dict(l=8, r=8, t=56, b=12),
        legend=dict(bgcolor="#ffffff", orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(bgcolor="#ffffff", font_color="#131722", font_size=13, font_family=plotly_font()),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="rgba(180,204,232,.16)")
    fig.update_yaxes(gridcolor="rgba(180,204,232,.09)", zeroline=False, linecolor="rgba(180,204,232,.16)")
    return fig


def calculate_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate a consistent, educational set of daily technical indicators."""
    frame = data.copy().sort_values("date").reset_index(drop=True)
    for field in ("open", "high", "low", "close", "volume"):
        frame[field] = pd.to_numeric(frame[field], errors="coerce")
    close = frame["close"]
    high = frame["high"]
    low = frame["low"]
    volume = frame["volume"].fillna(0.0)

    # Trend overlays: simple and exponential moving averages.
    frame["ma5"] = close.rolling(5, min_periods=5).mean()
    frame["ma20"] = close.rolling(20, min_periods=20).mean()
    frame["ma50"] = close.rolling(50, min_periods=50).mean()
    frame["ema12"] = close.ewm(span=12, adjust=False, min_periods=12).mean()
    frame["ema26"] = close.ewm(span=26, adjust=False, min_periods=26).mean()

    # RSI (14): Wilder-style exponential smoothing; platform seeds may differ slightly.
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    frame["rsi14"] = 100 - (100 / (1 + rs))
    frame.loc[(avg_loss == 0) & (avg_gain > 0), "rsi14"] = 100.0
    frame.loc[(avg_gain == 0) & (avg_loss > 0), "rsi14"] = 0.0
    frame.loc[(avg_gain == 0) & (avg_loss == 0), "rsi14"] = 50.0

    # MACD: DIF = EMA12 - EMA26; DEA = 9-period EMA of DIF; histogram = DIF - DEA.
    frame["dif"] = frame["ema12"] - frame["ema26"]
    frame["dea"] = frame["dif"].ewm(span=9, adjust=False, min_periods=9).mean()
    frame["macd_hist"] = frame["dif"] - frame["dea"]

    # Bollinger Bands (20, 2): a 20-session SMA and two standard deviations.
    frame["bb_mid"] = close.rolling(20, min_periods=20).mean()
    rolling_std = close.rolling(20, min_periods=20).std(ddof=0)
    frame["bb_upper"] = frame["bb_mid"] + 2.0 * rolling_std
    frame["bb_lower"] = frame["bb_mid"] - 2.0 * rolling_std

    # Stochastic (14, 3): closing price within the recent 14-session high-low range.
    rolling_low = low.rolling(14, min_periods=14).min()
    rolling_high = high.rolling(14, min_periods=14).max()
    denominator = (rolling_high - rolling_low).replace(0, np.nan)
    frame["stoch_k"] = 100 * (close - rolling_low) / denominator
    frame["stoch_d"] = frame["stoch_k"].rolling(3, min_periods=3).mean()

    # ADX / directional indicators. ATR is used internally in the calculation, but is not taught
    # or displayed as a separate indicator in this course.
    prev_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=frame.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=frame.index)
    smoothed_tr_raw = true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    zero_range = smoothed_tr_raw.eq(0) & smoothed_tr_raw.notna()
    smoothed_tr = smoothed_tr_raw.replace(0, np.nan)
    smoothed_plus = plus_dm.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    smoothed_minus = minus_dm.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    frame["plus_di"] = 100 * smoothed_plus / smoothed_tr
    frame["minus_di"] = 100 * smoothed_minus / smoothed_tr
    # A completely flat window has no directional movement. Define both DI and DX as zero
    # after their normal warm-up rather than letting the entire ADX line disappear as NaN.
    frame.loc[zero_range, ["plus_di", "minus_di"]] = 0.0
    dx_sum = frame["plus_di"] + frame["minus_di"]
    dx = 100 * (frame["plus_di"] - frame["minus_di"]).abs() / dx_sum.replace(0, np.nan)
    dx.loc[dx_sum.eq(0) & dx_sum.notna()] = 0.0
    frame["adx14"] = dx.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()

    # OBV: cumulative volume signed by whether the close rose or fell versus the prior close.
    signed_volume = np.sign(delta.fillna(0.0)) * volume
    frame["obv"] = signed_volume.cumsum()
    return frame


def technical_range_extrema(data: pd.DataFrame) -> dict[str, object] | None:
    """Return high/low and their dates for the entire currently selected chart range."""
    if data is None or data.empty or not {"date", "high", "low"}.issubset(data.columns):
        return None
    window = data.dropna(subset=["date", "high", "low"]).sort_values("date").reset_index(drop=True).copy()
    if window.empty:
        return None
    low_pos = int(np.argmin(window["low"].to_numpy(dtype=float)))
    high_pos = int(np.argmax(window["high"].to_numpy(dtype=float)))
    return {
        "data": window,
        "low_pos": low_pos,
        "high_pos": high_pos,
        "low_row": window.iloc[low_pos],
        "high_row": window.iloc[high_pos],
    }


def technical_indicator_figure(
    data: pd.DataFrame,
    overlays: list[str],
    lower_indicator: str,
    show_levels: bool = False,
    show_fibonacci: bool = False,
    height: int = 610,
) -> go.Figure:
    """Plot indicators and price levels against the full selected historical window."""
    frame = data.copy().sort_values("date").reset_index(drop=True)
    valid_lower_indicators = {"RSI", "MACD", 'Stochastic', 'ADX (trend strength)', 'OBV (On Balance Volume)', 'No indicator pane'}
    if lower_indicator not in valid_lower_indicators:
        lower_indicator = 'No indicator pane'
    overlays = overlays or []
    has_lower = lower_indicator != 'No indicator pane'
    rows = 2 if has_lower else 1
    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True,
        vertical_spacing=0.035 if has_lower else 0,
        row_heights=[0.73, 0.27] if has_lower else [1.0],
    )
    fig.add_trace(go.Candlestick(
        x=frame["date"], open=frame["open"], high=frame["high"],
        low=frame["low"], close=frame["close"], name='Candles (green up / red down)',
        increasing_line_color="#059669", decreasing_line_color="#ef4444",
        increasing_fillcolor="#059669", decreasing_fillcolor="#ef4444",
        whiskerwidth=0.55,
    ), row=1, col=1)

    if "MA5 / MA20" in overlays:
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["ma5"], mode="lines", name='SMA 5 (5-day simple moving average)',
            line=dict(color="#a66a00", width=2.0), connectgaps=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["ma20"], mode="lines", name='SMA 20 (20-day simple moving average)',
            line=dict(color="#2563eb", width=2.0), connectgaps=False,
        ), row=1, col=1)
    if "EMA12 / EMA26" in overlays:
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["ema12"], mode="lines", name='EMA 12 (12-day exponential moving average)',
            line=dict(color="#7c3aed", width=1.9), connectgaps=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["ema26"], mode="lines", name='EMA 26 (26-day exponential moving average)',
            line=dict(color="#c2410c", width=1.9), connectgaps=False,
        ), row=1, col=1)
    if 'Bollinger Bands (20, 2)' in overlays:
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["bb_upper"], mode="lines", name='Upper Bollinger Band',
            line=dict(color="rgba(117,183,255,.78)", width=1.3, dash="dot"), connectgaps=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["bb_lower"], mode="lines", name='Bollinger Band range',
            line=dict(color="rgba(117,183,255,.78)", width=1.3, dash="dot"),
            fill="tonexty", fillcolor="rgba(117,183,255,.08)", connectgaps=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["bb_mid"], mode="lines", name='Middle Bollinger Band (20-day SMA)',
            line=dict(color="#2563eb", width=1.4), connectgaps=False,
        ), row=1, col=1)

    extrema = technical_range_extrema(frame)
    range_frame = extrema["data"] if extrema else frame.iloc[0:0]
    if extrema and len(range_frame) >= 5:
        low_row = extrema["low_row"]
        high_row = extrema["high_row"]
        support_level = float(low_row["low"])
        resistance_level = float(high_row["high"])
        end_date = pd.Timestamp(range_frame["date"].iloc[-1])
        if show_levels:
            fig.add_trace(go.Scatter(
                x=range_frame["date"].tolist(), y=[support_level] * len(range_frame), mode="lines",
                name='Window low (support illustration)', showlegend=False,
                line=dict(color="#059669", width=1.5, dash="dash"),
                hovertemplate='Window low (support illustration)<br>%{y:.2f}<extra></extra>',
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=range_frame["date"].tolist(), y=[resistance_level] * len(range_frame), mode="lines",
                name='Window high (resistance illustration)', showlegend=False,
                line=dict(color="#ef4444", width=1.5, dash="dash"),
                hovertemplate='Window high (resistance illustration)<br>%{y:.2f}<extra></extra>',
            ), row=1, col=1)
            fig.add_annotation(
                x=end_date, y=support_level, text='Window low', showarrow=False,
                xanchor="right", yshift=9, bgcolor="#ffffff",
                font=dict(size=10, color="#059669"), row=1, col=1,
            )
            fig.add_annotation(
                x=end_date, y=resistance_level, text='Window high', showarrow=False,
                xanchor="right", yshift=9, bgcolor="#ffffff",
                font=dict(size=10, color="#ef4444"), row=1, col=1,
            )
        if show_fibonacci:
            low_pos = int(extrema["low_pos"])
            high_pos = int(extrema["high_pos"])
            swing_low = float(low_row["low"])
            swing_high = float(high_row["high"])
            span = swing_high - swing_low
            # The extrema across the selected period are only a transparent teaching heuristic.
            # If both extrema occur on the same candle, direction cannot be inferred reliably.
            if span > 0 and low_pos != high_pos:
                if low_pos < high_pos:
                    levels = [(ratio, swing_high - span * ratio) for ratio in (0.236, 0.382, 0.500, 0.618, 0.786)]
                else:
                    levels = [(ratio, swing_low + span * ratio) for ratio in (0.236, 0.382, 0.500, 0.618, 0.786)]
                fib_colors = ["#a66a00", "#2563eb", "#7c3aed", "#059669", "#c2410c"]
                for (ratio, level), color in zip(levels, fib_colors):
                    fig.add_trace(go.Scatter(
                        x=range_frame["date"].tolist(), y=[level] * len(range_frame), mode="lines",
                        name=f'Fibonacci {ratio * 100:.1f}%', showlegend=False,
                        line=dict(color=color, width=1, dash="dot"),
                        hovertemplate=f'Fibonacci {ratio * 100:.1f}%<br>%{{y:.2f}}<extra></extra>',
                    ), row=1, col=1)
                    fig.add_annotation(
                        x=end_date, y=level, text=f'Fibonacci {ratio * 100:.1f}%',
                        showarrow=False, xanchor="right", yshift=1,
                        bgcolor="#ffffff", font=dict(size=9, color=color), row=1, col=1,
                    )

    if lower_indicator == "RSI":
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["rsi14"], mode="lines", name='RSI(14)',
            line=dict(color="#7c3aed", width=2.2), connectgaps=False,
        ), row=2, col=1)
        rsi_x = frame["date"].tolist()
        for y_value, color, label in [(70, "#ef4444", '70 reference'), (50, "rgba(180,204,232,.55)", '50 midpoint'), (30, "#059669", '30 reference')]:
            if rsi_x:
                fig.add_trace(go.Scatter(x=rsi_x, y=[y_value] * len(rsi_x), mode="lines", name=label, showlegend=False,
                    line=dict(color=color, dash="dot", width=1), hovertemplate=f"RSI {label}<extra></extra>"), row=2, col=1)
        fig.update_yaxes(title_text='RSI(0–100)', range=[0, 100], row=2, col=1)
    elif lower_indicator == "MACD":
        histogram_colors = ["#059669" if pd.notna(v) and v >= 0 else "#ef4444" for v in frame["macd_hist"]]
        fig.add_trace(go.Bar(
            x=frame["date"], y=frame["macd_hist"], name='Histogram (MACD − signal)',
            marker_color=histogram_colors, opacity=0.65,
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["dif"], mode="lines", name='MACD line',
            line=dict(color="#7c3aed", width=2), connectgaps=False,
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["dea"], mode="lines", name='Signal line',
            line=dict(color="#a66a00", width=2), connectgaps=False,
        ), row=2, col=1)
        macd_x = frame["date"].tolist()
        if macd_x:
            fig.add_trace(go.Scatter(
                x=macd_x, y=[0.0] * len(macd_x), mode="lines", name='MACD zero reference',
                showlegend=False, line=dict(color="rgba(180,204,232,.55)", dash="dot", width=1),
                hovertemplate='MACD zero reference: 0<extra></extra>',
            ), row=2, col=1)
        fig.update_yaxes(title_text='MACD value', row=2, col=1)
    elif lower_indicator == 'Stochastic':
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["stoch_k"], mode="lines", name='%K (fast line)',
            line=dict(color="#2563eb", width=2), connectgaps=False,
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["stoch_d"], mode="lines", name='%D (smoothed line)',
            line=dict(color="#a66a00", width=2), connectgaps=False,
        ), row=2, col=1)
        stoch_x = frame["date"].tolist()
        if stoch_x:
            fig.add_trace(go.Scatter(x=stoch_x, y=[80] * len(stoch_x), mode="lines", name='80 reference', showlegend=False,
                line=dict(color="#ef4444", dash="dot", width=1), hovertemplate='Stochastic 80 reference<extra></extra>'), row=2, col=1)
            fig.add_trace(go.Scatter(x=stoch_x, y=[20] * len(stoch_x), mode="lines", name='20 reference', showlegend=False,
                line=dict(color="#059669", dash="dot", width=1), hovertemplate='Stochastic 20 reference<extra></extra>'), row=2, col=1)
        fig.update_yaxes(title_text='Stochastic (0–100)', range=[0, 100], row=2, col=1)
    elif lower_indicator == 'ADX (trend strength)':
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["adx14"], mode="lines", name='ADX (trend strength)',
            line=dict(color="#7c3aed", width=2.2), connectgaps=False,
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["plus_di"], mode="lines", name='+DI (positive directional indicator)',
            line=dict(color="#059669", width=1.7), connectgaps=False,
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["minus_di"], mode="lines", name='−DI (negative directional indicator)',
            line=dict(color="#ef4444", width=1.7), connectgaps=False,
        ), row=2, col=1)
        adx_x = frame["date"].tolist()
        if adx_x:
            fig.add_trace(go.Scatter(x=adx_x, y=[20] * len(adx_x), mode="lines", name='ADX 20 reference', showlegend=False,
                line=dict(color="rgba(180,204,232,.45)", dash="dot", width=1), hovertemplate='ADX 20 reference<extra></extra>'), row=2, col=1)
            fig.add_trace(go.Scatter(x=adx_x, y=[25] * len(adx_x), mode="lines", name='ADX 25 reference', showlegend=False,
                line=dict(color="rgba(180,204,232,.45)", dash="dash", width=1), hovertemplate='ADX 25 reference<extra></extra>'), row=2, col=1)
        fig.update_yaxes(title_text='ADX / DI(0–100)', range=[0, 100], row=2, col=1)
    elif lower_indicator == 'OBV (On Balance Volume)':
        fig.add_trace(go.Scatter(
            x=frame["date"], y=frame["obv"], mode="lines", name='OBV (On Balance Volume)',
            line=dict(color="#059669", width=2.1), connectgaps=False,
        ), row=2, col=1)
        fig.update_yaxes(title_text='Cumulative volume (relative)', tickformat="~s", row=2, col=1)

    style_fig(fig, height)
    fig.update_layout(
        height=height, hovermode="x unified", xaxis_rangeslider_visible=False,
        # Reserve a generous top band for a multi-row legend on narrow screens.
        # Keeping the legend above the plot prevents it from covering candles or indicator lines.
        margin=dict(l=38, r=16, t=132, b=30),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            bgcolor="#ffffff", bordercolor="rgba(139,162,189,.35)", borderwidth=1,
            font=dict(size=11, color="#131722"),
        ),
    )
    fig.update_xaxes(
        rangeslider_visible=False, showgrid=True, gridcolor="rgba(180,204,232,.10)",
        tickfont=dict(color="#6a6d78", size=10),
        rangebreaks=[dict(bounds=["sat", "mon"])],
    )
    fig.update_yaxes(title_text='Price (USD)', row=1, col=1, gridcolor="rgba(180,204,232,.12)", tickfont=dict(color="#6a6d78", size=10))
    if has_lower:
        fig.update_xaxes(showgrid=True, gridcolor="rgba(180,204,232,.10)", row=2, col=1)
        fig.update_yaxes(gridcolor="rgba(180,204,232,.10)", tickfont=dict(color="#6a6d78", size=10), row=2, col=1)
    return fig



def hero(title: str, subtitle: str, eyebrow: str = "STOCKSCOPE LEARN · BEGINNER STOCK ACADEMY") -> None:
    # Keep intentional title line breaks rather than letting HTML collapse them into spaces.
    title_html = t(title).replace("""
""", "<br>")
    st.markdown(
        f"""
        <div class="hero">
          <div class="eyebrow">{t(eyebrow)}</div>
          <h1>{title_html}</h1>
          <p>{t(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_heading(kicker: str, title: str, desc: str | None = None) -> None:
    desc_html = f'<div class="section-desc">{t(desc)}</div>' if desc else ""
    st.markdown(
        f'<div class="section-block"><div class="section-kicker">{t(kicker)}</div>'
        f'<div class="section-title">{t(title)}</div>{desc_html}</div>',
        unsafe_allow_html=True,
    )


def content_heading(title: str, *, level: str = "h4") -> None:
    cls = "content-h3" if level == "h3" else "content-h4"
    st.markdown(f'<div class="{cls}">{t(title)}</div>', unsafe_allow_html=True)


def escape_markdown_dollars(content: str) -> str:
    """Keep dollar-denominated values literal instead of treating $ as LaTeX delimiters."""
    return str(content).replace("$", "&#36;")


def info_card(icon: str, title: str, body: str, tag: str | None = None) -> None:
    tag_html = f'<span class="tag">{t(tag)}</span>' if tag else ""
    st.markdown(
        f'''<div class="info-card"><div style="font-size:1.35rem">{icon}</div><h4>{t(title)}</h4><p>{t(body)}</p><div style="margin-top:.8rem">{tag_html}</div></div>''',
        unsafe_allow_html=True,
    )


def mark_complete(lesson: str) -> None:
    current = set(st.session_state.get("completed_lessons", []))
    current.add(lesson)
    st.session_state["completed_lessons"] = sorted(current)


def record_quiz_attempt(lesson: str, passed: bool) -> None:
    """Record quiz attempts while allowing learners to retake checks."""
    stats = st.session_state.setdefault("quiz_attempts", {})
    prior = stats.get(lesson, {"attempts": 0, "passed": False, "last_passed": False})
    stats[lesson] = {
        "attempts": int(prior.get("attempts", 0)) + 1,
        "passed": bool(prior.get("passed", False) or passed),
        "last_passed": bool(passed),
    }


def nav_to(page: str) -> None:
    st.session_state["main_nav"] = page


def reset_comprehensive_quiz() -> None:
    st.session_state.pop("comprehensive_quiz_result", None)
    for idx in range(24):
        st.session_state.pop(f"comprehensive_answer_{idx}", None)


def choose_company_statement(value: str) -> None:
    """Remember the selected financial statement before Streamlit reruns."""
    st.session_state["company_statement_choice"] = value


def scroll_main_to_top(trigger: str) -> None:
    """Scroll to the top once after a main-navigation page change only.

    Candle-pattern selection deliberately does not call this helper. Avoid retry
    loops because repeated calls can pull users back to the top during reading.
    """
    trigger_json = json.dumps(str(trigger), ensure_ascii=False)
    html = f"""
    <div style="font:1px sans-serif;color:transparent;height:1px;overflow:hidden">{escape(str(trigger))}</div>
    <script>
    (() => {{
      const trigger = {trigger_json};
      // One delayed action only. No polling/repeating timers.
      const jumpToTop = () => {{
        try {{
          const host = window.parent;
          const doc = host.document;
          const main = doc.querySelector('[data-testid="stMain"]')
            || doc.querySelector('section[data-testid="stMain"]')
            || doc.querySelector('section.main')
            || doc.querySelector('main');
          const target = doc.getElementById('stockscope-main-top');

          // Prefer scrolling the main Streamlit content container. Avoid resetting
          // every ancestor/document at once, which can create visible jumpiness.
          if (main && typeof main.scrollTo === 'function') {{
            main.scrollTo({{ top: 0, left: 0, behavior: 'instant' }});
          }} else if (target && typeof target.scrollIntoView === 'function') {{
            target.scrollIntoView({{ block: 'start', inline: 'nearest', behavior: 'instant' }});
          }} else if (typeof host.scrollTo === 'function') {{
            host.scrollTo({{ top: 0, left: 0, behavior: 'instant' }});
          }}
        }} catch (_) {{ /* Browser security restrictions should not break the app. */ }}
      }};
      // Trigger is referenced deliberately so each navigation event has distinct HTML.
      void trigger;
      window.requestAnimationFrame(() => window.setTimeout(jumpToTop, 120));
    }})();
    </script>
    """
    components.html(html, height=1, width=1, scrolling=False)


def show_data_warning(error: str | None) -> None:
    if error:
        st.warning(t('Market data could not be loaded. You can still read the lesson; check your connection or try again later to use the charts.'))
        # Keep raw technical exceptions out of the visible UI to avoid a stray code-style panel.


def format_money(value: float) -> str:
    return "—" if pd.isna(value) else f"${value:,.2f}"


def format_pct(value: float) -> str:
    return "—" if pd.isna(value) else f"{value:+.2f}%"


def lesson_completion_button(lesson: str, key: str) -> None:
    """Let learners mark a lesson complete without a separate reflection form."""
    completed = set(st.session_state.get("completed_lessons", []))
    already_done = lesson in completed
    label = t('✓ Lesson completed') if already_done else t('Mark lesson complete')
    if st.button(label, key=key, width="stretch", disabled=already_done,
                 on_click=mark_complete, args=(lesson,)):
        st.success(t('Lesson marked complete.'))


# ============================================================
# Candlestick pattern library and illustrative OHLC helper
# ============================================================
# These are common textbook-style descriptions. Exact pattern rules vary by source;
# none of these shapes is a standalone prediction or trading instruction.
CANDLE_PATTERNS = [
    {
        "group": 'Single candlesticks', "name": 'Long bullish candle', "bias": 'Bullish price action', "trend": "sideways",
        "bars": [(100, 112, 99, 111)], "structure": 'A long body closes well above the open; wicks are relatively short.',
        "recognize": """- Close is well above open.
- The body covers much of the high/low range.
- Judge length against recent candles, not a fixed dollar amount.""",
        "meaning": 'A substantial open-to-close rise suggests buyers were stronger during this bar. It does not guarantee another rise.',
        "context": 'After a decline it may suggest easing selling pressure; late in a rally it may reflect short-term overextension.',
        "confirmation": 'Check later closes, key levels, volume, the wider market and relevant company news.',
        "pitfall": 'Treating one long bullish candle as a buy signal while ignoring an already extended rally.',
    },
    {
        "group": 'Single candlesticks', "name": 'Long bearish candle', "bias": 'Bearish price action', "trend": "sideways",
        "bars": [(112, 113, 99, 100)], "structure": 'A long body closes well below the open; wicks are relatively short.',
        "recognize": """- Close is well below open.
- The body is long relative to recent bars.
- This describes a fall that already happened, not the next candle.""",
        "meaning": 'A substantial open-to-close fall suggests sellers were stronger during the bar.',
        "context": 'After a rally it may suggest weakening prices; late in a long decline it may accompany panic selling. Do not assume continued falls.',
        "confirmation": 'Check key-level breaks, unusual volume, earnings or economic events and subsequent prices.',
        "pitfall": 'Panic-selling on one candle without considering the investment horizon, business or risk plan.',
    },
    {
        "group": 'Single candlesticks', "name": 'Bullish Marubozu', "bias": 'Strong bullish momentum within the bar', "trend": "sideways",
        "bars": [(100, 112, 100, 112)], "structure": 'Open is near the low and close near the high, with a long body and almost no wicks.',
        "recognize": """- Open is near the bar's low.
- Close is near its high.
- Small data differences mean exact equality is not required for this lesson.""",
        "meaning": 'Buyers maintained relatively strong pressure during the bar.',
        "context": 'Determine whether this is an initial breakout, a mid-trend move or an extended rally.',
        "confirmation": 'Check the breakout location, subsequent support of the range, volume and market context.',
        "pitfall": "Confusing one bar's momentum with a lasting trend and overlooking pullback risk.",
    },
    {
        "group": 'Single candlesticks', "name": 'Bearish Marubozu', "bias": 'Strong bearish momentum within the bar', "trend": "sideways",
        "bars": [(112, 112, 100, 100)], "structure": 'Open is near the high and close near the low, with a long body and almost no wicks.',
        "recognize": """- Open is near the high.
- Close is near the low.
- Price generally moved downward across the bar.""",
        "meaning": 'Sellers maintained relatively strong pressure during the bar.',
        "context": 'Near support, watch whether a break continues; after a large decline, consider rebound risk.',
        "confirmation": 'Combine trend, levels, volume and later closes rather than relying on one body.',
        "pitfall": 'Assuming a long bearish candle must be followed by another.',
    },
    {
        "group": 'Single candlesticks', "name": 'Doji', "bias": 'Neutral / indecision', "trend": "sideways",
        "bars": [(100, 106, 95, 100.1)], "structure": 'Open and close are very close, making a tiny body. Wicks may be long or short.',
        "recognize": """- Open and close need not be identical.
- Compare with recent body sizes.
- Wick lengths distinguish Doji variations.""",
        "meaning": 'Prices moved during the bar but finished near the open, often interpreted as indecision or temporary balance.',
        "context": 'After a strong trend it can prompt a check for changing momentum; inside a narrow range it may be ordinary noise.',
        "confirmation": 'Check the direction of later bars, volume and key levels.',
        "pitfall": 'Assuming every Doji means reversal.',
    },
    {
        "group": 'Single candlesticks', "name": 'Long-legged Doji', "bias": 'Indecision / movement in both directions', "trend": "sideways",
        "bars": [(100, 110, 90, 100.1)], "structure": 'Open and close are close together, with long upper and lower wicks.',
        "recognize": """- Tiny body.
- High and low are far from the body.
- Large movement in both directions ended near the open.""",
        "meaning": 'Both buying and selling pressure moved prices substantially, but the close returned near the open.',
        "context": 'Around major news or volatile trading, consider event timing, volume and later price action.',
        "confirmation": 'Wait for subsequent direction and a sustained range break; wick direction alone is insufficient.',
        "pitfall": 'Mistaking large movement for a clear victory by buyers or sellers.',
    },
    {
        "group": 'Single candlesticks', "name": 'Dragonfly Doji', "bias": 'Potentially bullish in suitable context', "trend": "down",
        "bars": [(100, 101, 90, 100.1)], "structure": 'Open and close are near the high, with a long lower wick and little upper wick.',
        "recognize": """- Price fell substantially during the bar.
- It recovered near the opening/high area.
- The shape resembles a T; proportions and naming conventions vary.""",
        "meaning": 'Selling pushed price down, but buying brought it back near the open.',
        "context": 'More relevant after a decline or near support; elsewhere it may lack directional meaning.',
        "confirmation": 'Watch for stronger later closes, a defended low, volume and market context.',
        "pitfall": 'Treating a long lower wick as proof that buyers fully control the market.',
    },
    {
        "group": 'Single candlesticks', "name": 'Gravestone Doji', "bias": 'Potentially bearish in suitable context', "trend": "up",
        "bars": [(100, 110, 99, 100.05)], "structure": 'Open and close are near the low, with a long upper wick and little lower wick.',
        "recognize": """- Price rose substantially during the bar.
- It fell back near the opening/low area.
- The long wick points in the opposite direction from a Dragonfly Doji.""",
        "meaning": 'Buying failed to sustain the higher prices and selling pushed them back before the close.',
        "context": 'More relevant after a rally or near resistance; it does not guarantee reversal.',
        "confirmation": 'Check later weakness, a break below the pattern low, volume and market context.',
        "pitfall": 'Ignoring that a similar shape can form in sideways or thin trading without a prior trend.',
    },
    {
        "group": 'Single candlesticks', "name": 'Spinning Top', "bias": 'Neutral / indecision', "trend": "sideways",
        "bars": [(100, 106, 94, 101.5)], "structure": 'A small body with noticeable upper and lower wicks; little net open-to-close change.',
        "recognize": """- Small body.
- Wicks show movement in both directions.
- Unlike a Doji, it usually has a visible small body.""",
        "meaning": 'Both sides moved prices, but the closing price remained near the opening price.',
        "context": 'After a trend it may prompt a momentum check; inside consolidation it may not be significant.',
        "confirmation": 'Look for later direction, volatility context and relevant levels.',
        "pitfall": 'Calling indecision a confirmed reversal; it may simply be a pause.',
    },
    {
        "group": 'Single candlesticks', "name": 'Hammer', "bias": 'Potentially bullish after a decline', "trend": "down",
        "bars": [(100, 101.5, 91, 101)], "structure": 'A small body near the top of the range, a long lower wick and a short upper wick.',
        "recognize": """- A common guide is a lower wick around twice the body, but definitions vary.
- The body may be bullish or bearish.
- First check for a preceding downtrend.""",
        "meaning": 'A recovery from lower prices suggests buying interest; traditionally a possible strengthening clue after a decline.',
        "context": 'Look for a prior decline and proximity to a support area.',
        "confirmation": 'Later strength or a close above the Hammer high may add evidence; confirmation rules vary.',
        "pitfall": 'The same shape after a rally is usually called a Hanging Man rather than a Hammer.',
    },
    {
        "group": 'Single candlesticks', "name": 'Hanging Man', "bias": 'Potentially bearish after a rally', "trend": "up",
        "bars": [(100, 101.5, 91, 101)], "structure": 'Similar to a Hammer: a small upper body, long lower wick and short upper wick.',
        "recognize": """- Similar geometry to a Hammer.
- A preceding uptrend distinguishes it.
- Body colour alone is insufficient.""",
        "meaning": 'A substantial dip during an uptrend, despite recovery, may indicate more active selling.',
        "context": 'A prior rally is essential context; do not name the pattern from shape alone.',
        "confirmation": 'Watch for later weakness, such as a close below its body or low; rules vary.',
        "pitfall": 'Assuming every long lower wick is bullish; context changes the traditional interpretation.',
    },
    {
        "group": 'Single candlesticks', "name": 'Inverted Hammer', "bias": 'Potentially bullish after a decline', "trend": "down",
        "bars": [(100, 110, 99.8, 100.6)], "structure": 'A small body near the lower end, a long upper wick and a short lower wick. Proportions are descriptive guides, not universal thresholds.',
        "recognize": """- Small body near the bottom of the range.
- Long upper wick shows an upward attempt that was not held into the close.
- Similar to a Shooting Star; prior trend distinguishes them.""",
        "meaning": 'Buyers attempted a rally but did not maintain the high close, so later confirmation matters.',
        "context": 'Traditionally examined after a decline.',
        "confirmation": 'Check for a stronger bullish bar or a break above the pattern high; otherwise it may be a brief bounce.',
        "pitfall": 'Its shape resembles a Shooting Star; the preceding trend is the main distinction.',
    },
    {
        "group": 'Single candlesticks', "name": 'Shooting Star', "bias": 'Potentially bearish after a rally', "trend": "up",
        "bars": [(100, 110, 99.8, 100.5)], "structure": 'A small body near the low, a long upper wick and a short lower wick. Proportions vary with definitions and volatility.',
        "recognize": """- Price tested a noticeably higher level but retreated.
- Usually requires a prior uptrend.
- Prior trend distinguishes it from an Inverted Hammer.""",
        "meaning": 'Failure to maintain higher prices may indicate weaker buying momentum or selling pressure above.',
        "context": 'More relevant after a rally or near possible resistance than in a trendless range.',
        "confirmation": 'Check later weakness, support breaks and volume. Without confirmation it remains a clue.',
        "pitfall": 'Assuming a long upper wick guarantees a fall, despite a trend that may continue.',
    },
    {
        "group": 'Two-candle patterns', "name": 'Bullish Engulfing', "bias": 'Potentially bullish after a decline', "trend": "down",
        "bars": [(103, 104, 97, 98), (97, 106, 96, 105)], "structure": 'A bearish body is followed by a larger bullish body that covers the first body.',
        "recognize": """- First body is usually bearish; second bullish.
- Compare bodies; engulfing every wick is not always required.
- Classical definitions can impose stricter gap conditions.""",
        "meaning": "The second close recovers above the first body's upper edge, suggesting a possible change in pressure.",
        "context": 'Usually discussed after a decline or pullback; less meaningful in a sideways range.',
        "confirmation": 'Check later strength, support location and changes in volume.',
        "pitfall": 'Checking body overlap without considering the earlier trend or location.',
    },
    {
        "group": 'Two-candle patterns', "name": 'Bearish Engulfing', "bias": 'Potentially bearish after a rally', "trend": "up",
        "bars": [(97, 104, 96, 103), (105, 106, 94, 95)], "structure": 'A bullish body is followed by a larger bearish body that covers it.',
        "recognize": """- First body is usually bullish; second larger and bearish.
- Focus on bodies; exact boundaries vary between definitions.""",
        "meaning": "The second bar's selling covers the earlier body and may suggest weakening prices.",
        "context": 'Usually considered after a rally; the meaning differs after an already large decline.',
        "confirmation": 'Check later breaks below the pattern low or support, and whether new information emerged.',
        "pitfall": 'Calling any pair of opposite-coloured candles an engulfing pattern without context.',
    },
    {
        "group": 'Two-candle patterns', "name": 'Piercing Line', "bias": 'Potentially bullish after a decline', "trend": "down",
        "bars": [(105, 106, 94, 95), (92, 102, 91, 101)], "structure": "A long bearish candle is followed by a lower open and recovery above the first body's midpoint.",
        "recognize": """- The second bar recovers substantially.
- Classical definitions often require a lower open or downward gap.
- Its close exceeds the first body's midpoint, usually without exceeding the first open.""",
        "meaning": 'After a decline, recovery into the bearish body may suggest easing selling pressure.',
        "context": 'Usually discussed after a decline. Without the classical gap it may fit only a looser definition.',
        "confirmation": 'Check continued recovery, volume and support context.',
        "pitfall": 'Calling any bullish rebound a Piercing Line while ignoring the midpoint requirement.',
    },
    {
        "group": 'Two-candle patterns', "name": 'Dark Cloud Cover', "bias": 'Potentially bearish after a rally', "trend": "up",
        "bars": [(95, 106, 94, 105), (108, 109, 97, 99)], "structure": "A long bullish candle is followed by a higher open and a close below the first body's midpoint.",
        "recognize": """- Second candle is usually bearish.
- A higher open and close below the prior body's midpoint are common requirements.
- One bearish candle alone is insufficient.""",
        "meaning": 'The second bar loses its higher-open advantage and closes deep inside the previous bullish body.',
        "context": 'Usually more relevant after a rally or near resistance.',
        "confirmation": 'Check later weakness or a break below the pattern low, alongside new information.',
        "pitfall": 'Assigning a bearish meaning mechanically without a preceding rally.',
    },
    {
        "group": 'Two-candle patterns', "name": 'Bullish Harami', "bias": 'Possible stabilisation after a decline', "trend": "down",
        "bars": [(108, 109, 94, 96), (98, 101, 97, 100)], "structure": 'A large body is followed by a smaller body fully inside it.',
        "recognize": """- Second body is clearly smaller.
- Usually follows a decline; its colour and naming details vary by definition.""",
        "meaning": 'After strong selling, a smaller body may show a temporary easing of pressure, not confirmed direction.',
        "context": 'Check the earlier decline and containment of the second body.',
        "confirmation": 'A later break above the Harami high can add evidence; otherwise it may only be a pause.',
        "pitfall": 'Treating a Harami as a completed reversal rather than a possible pause.',
    },
    {
        "group": 'Two-candle patterns', "name": 'Bearish Harami', "bias": 'Possible weakness after a rally', "trend": "up",
        "bars": [(94, 109, 93, 107), (105, 106, 102, 103)], "structure": 'A large body is followed by a smaller body inside its range.',
        "recognize": """- Second body is smaller and contained.
- Traditional interpretation requires a prior uptrend.""",
        "meaning": 'Smaller price movement after a bullish body may suggest temporarily weaker upward momentum.',
        "context": 'Consider the earlier rally and resistance; in sideways trading it may be an ordinary small body.',
        "confirmation": "Check later weakness, the second candle's low and important support.",
        "pitfall": 'Interpreting a small body as bearish without trend context.',
    },
    {
        "group": 'Two-candle patterns', "name": 'Tweezer Bottom', "bias": 'Potentially bullish after a decline', "trend": "down",
        "bars": [(103, 105, 95, 97), (97, 102, 95, 101)], "structure": 'Two adjacent candles have roughly matching lows, followed by a recovery in the second bar.',
        "recognize": """- Similar lows show reactions near the same price.
- There is no universal tolerance for a matching low.""",
        "meaning": 'Two tests without a clear break below may suggest a support area.',
        "context": 'Usually examined after a decline or near possible support.',
        "confirmation": 'Check later strength and older reactions near the same level.',
        "pitfall": 'Matching lows can be coincidental and do not guarantee support will hold.',
    },
    {
        "group": 'Two-candle patterns', "name": 'Tweezer Top', "bias": 'Potentially bearish after a rally', "trend": "up",
        "bars": [(97, 105, 95, 103), (104, 105, 98, 99)], "structure": 'Two adjacent candles have roughly matching highs, followed by a retreat in the second bar.',
        "recognize": """- Similar highs.
- Weaker second-bar action.
- Whether resistance is meaningful matters more than perfect geometry.""",
        "meaning": 'Two failed tests of a high may suggest resistance or selling pressure.',
        "context": 'Usually examined after a rally or near possible resistance.',
        "confirmation": 'Check later declines and repeated historical reactions near that high.',
        "pitfall": 'Assuming two similar highs guarantee a reversal.',
    },
    {
        "group": 'Two-candle patterns', "name": 'Inside Bar', "bias": 'Neutral / contracting range', "trend": "up",
        "bars": [(100, 110, 95, 107), (106, 108, 99, 104)], "structure": "The second bar's high is lower and its low is higher than the first bar's.",
        "recognize": """- Compare the full high/low range, not just bodies.
- The second bar is completely inside the first.""",
        "meaning": 'A smaller range can describe a pause or volatility contraction; breakout direction is not known beforehand.',
        "context": 'Can occur during a trending consolidation or sideways phase.',
        "confirmation": 'Wait for a break above or below the range and check whether it continues.',
        "pitfall": 'Predicting the breakout direction or treating compression as directional confirmation.',
    },
    {
        "group": 'Three-candle patterns', "name": 'Morning Star', "bias": 'Potentially bullish after a decline', "trend": "down",
        "bars": [(108, 110, 97, 98), (96, 99, 94, 97), (97, 106, 96, 105)], "structure": 'A strong bearish candle, a small/indecisive candle, then a strong bullish candle recovering deeply into the first body.',
        "recognize": """- Selling pressure → pause → recovery.
- Classical definitions consider gaps around the middle body; these may not occur in every market.
- The strength of the third bar's recovery matters.""",
        "meaning": 'Traditionally a possible weakening of downward momentum and the start of recovery.',
        "context": "Requires a preceding downtrend; a weak third-bar recovery reduces the pattern's quality.",
        "confirmation": "Check whether the third close passes the first body's midpoint and whether strength continues.",
        "pitfall": 'Counting three candles without judging the recovery or preceding trend.',
    },
    {
        "group": 'Three-candle patterns', "name": 'Evening Star', "bias": 'Potentially bearish after a rally', "trend": "up",
        "bars": [(98, 109, 97, 108), (109, 112, 108, 110), (110, 111, 101, 102)], "structure": 'A strong bullish candle, a small/indecisive candle, then a strong bearish candle closing deeply inside the first body.',
        "recognize": """- Rally → pause → selling pressure.
- Classical definitions consider gaps and the third bar's decline; requirements vary.""",
        "meaning": 'Traditionally a possible weakening of upward momentum and the beginning of a retreat.',
        "context": 'Usually examined after a rally or near resistance.',
        "confirmation": "Check whether the third close falls below the first body's midpoint and whether weakness continues.",
        "pitfall": 'Ignoring that prices can recover; three-candle patterns can fail.',
    },
    {
        "group": 'Three-candle patterns', "name": 'Morning Doji Star', "bias": 'Potentially bullish after a decline', "trend": "down",
        "bars": [(108, 110, 97, 98), (96, 99, 93, 96.05), (97, 106, 96, 105)], "structure": 'A Morning Star whose middle candle is a Doji with open and close very close.',
        "recognize": """- Clear selling pressure first.
- A middle Doji.
- A clearly stronger third-bar recovery.""",
        "meaning": 'The Doji emphasises a pause visually, without automatically making reversal more reliable.',
        "context": 'Usually examined after a decline, with a meaningful first body.',
        "confirmation": 'A strong third close and subsequent action provide more evidence than the Doji alone.',
        "pitfall": 'Treating the Doji itself as a directional signal.',
    },
    {
        "group": 'Three-candle patterns', "name": 'Evening Doji Star', "bias": 'Potentially bearish after a rally', "trend": "up",
        "bars": [(98, 109, 97, 108), (110, 114, 107, 110.05), (110, 111, 101, 102)], "structure": 'An Evening Star with a Doji as its middle candle.',
        "recognize": """- Clear first-bar rally.
- Middle Doji.
- Stronger third-bar retreat.""",
        "meaning": 'Traditionally interpreted as a pause in upward momentum followed by selling pressure.',
        "context": 'Usually examined after a rally or near resistance.',
        "confirmation": 'Check the third close and whether later prices remain weak.',
        "pitfall": 'Assuming the middle Doji guarantees a top.',
    },
    {
        "group": 'Three-candle patterns', "name": 'Three White Soldiers', "bias": 'Successive bullish price action', "trend": "down",
        "bars": [(95, 102, 94, 101), (100, 106, 99, 105), (104, 110, 103, 109)], "structure": 'Three substantial bullish candles with successively higher closes.',
        "recognize": """- Three bullish closes.
- Progressively higher closes and noticeable bodies.
- Ideal opens are near the preceding body; exact definitions vary.""",
        "meaning": 'Repeated buying strength, traditionally interpreted as recovery or trend continuation.',
        "context": 'After a decline it may describe recovery; after an extended rally it may indicate overheating.',
        "confirmation": 'Check whether later prices hold, the distance to resistance, volume and market context.',
        "pitfall": 'Chasing an extended rally without assessing risk/reward.',
    },
    {
        "group": 'Three-candle patterns', "name": 'Three Black Crows', "bias": 'Successive bearish price action', "trend": "up",
        "bars": [(109, 110, 102, 103), (104, 105, 98, 99), (100, 101, 94, 95)], "structure": 'Three substantial bearish candles with successively lower closes.',
        "recognize": """- Three bearish closes.
- Lower successive closes and noticeable bodies.
- Distinguish a pattern after a rally from one after an already large decline.""",
        "meaning": 'Repeated selling pressure, traditionally interpreted as weakening prices or continuation.',
        "context": 'Relevant after a rally; after an extended decline, rebound risk matters.',
        "confirmation": 'Check support, later direction and any new fundamental information.',
        "pitfall": 'Treating a decline that already happened as a guarantee of further losses.',
    },
    {
        "group": 'Three-candle patterns', "name": 'Three Inside Up', "bias": 'Potentially bullish after a decline', "trend": "down",
        "bars": [(110, 111, 99, 100), (101, 105, 100, 104), (104, 112, 103, 111)], "structure": 'A long bearish body, a smaller body inside it, then a bullish close above the first open.',
        "recognize": """- A Harami-like pair followed by upward confirmation.
- Third close moves clearly above the first opening area.""",
        "meaning": 'Traditionally, a decline pauses before buying pressure recovers.',
        "context": 'Requires a preceding decline and meaningful third-bar directional evidence.',
        "confirmation": 'Check whether later prices hold above the breakout.',
        "pitfall": 'Calling reversal before the third candle confirms the first pair.',
    },
    {
        "group": 'Three-candle patterns', "name": 'Three Inside Down', "bias": 'Potentially bearish after a rally', "trend": "up",
        "bars": [(100, 111, 99, 110), (109, 110, 105, 106), (106, 107, 98, 99)], "structure": 'A long bullish body, a smaller body inside it, then a bearish close below the first open.',
        "recognize": """- A Harami-like pair followed by downward confirmation.
- Third close moves below the first opening area.""",
        "meaning": 'Traditionally, an uptrend pauses before selling pushes prices lower.',
        "context": "Consider the preceding rally, resistance and the third candle's decline.",
        "confirmation": 'Check whether later prices weaken or quickly recover.',
        "pitfall": 'Treating a short-term third-bar fall as proof of a long bear market.',
    },
    {
        "group": 'Continuation patterns', "name": 'Rising Three Methods', "bias": 'Possible consolidation within an uptrend', "trend": "up",
        "bars": [(100, 111, 99, 110), (109, 110, 105, 106), (108, 109, 104, 105), (106, 108, 103, 104), (105, 115, 104, 114)], "structure": 'A strong bullish candle, several smaller counter-trend bars largely inside its range, then an upward breakout.',
        "recognize": """- The classic version has roughly five bars.
- The middle pullback is limited.
- The final bar resumes the advance beyond the consolidation.""",
        "meaning": 'Traditionally a pause within a strong trend followed by possible continuation.',
        "context": 'Needs earlier upward momentum. A break of key structure during the pullback changes the interpretation.',
        "confirmation": 'Check the final breakout, subsequent hold, volume and broader trend.',
        "pitfall": 'Calling any sideways pause Rising Three Methods without checking containment and the final breakout.',
    },
    {
        "group": 'Continuation patterns', "name": 'Falling Three Methods', "bias": 'Possible consolidation within a downtrend', "trend": "down",
        "bars": [(110, 111, 99, 100), (101, 106, 100, 105), (103, 108, 102, 107), (105, 109, 103, 108), (109, 110, 95, 96)], "structure": 'A strong bearish candle, smaller counter-trend rebounds largely inside its range, then a downward breakout.',
        "recognize": """- Classic versions contain several small rebound bars.
- The rebound does not change the larger downtrend.
- A final bar resumes the decline.""",
        "meaning": 'Traditionally a brief rebound inside a downtrend followed by possible continuation.',
        "context": 'Needs preceding downward momentum; do not force the label if the rebound changes the structure.',
        "confirmation": 'Check the final range break, later action, support and news context.',
        "pitfall": 'Calling every small rebound bearish continuation despite a possible trend change.',
    },
]


def build_candle_pattern_figure(pattern: dict) -> go.Figure:
    """Create a schematic OHLC chart with a synthetic trend prefix and selected pattern."""
    bars = pattern["bars"]
    first_open = float(bars[0][0])
    trend = pattern.get("trend", "sideways")
    if trend == "down":
        closes = [first_open + 8, first_open + 6, first_open + 3.5, first_open + 1.2]
        prefix = []
        prev = closes[0] + 1.2
        for close in closes:
            open_ = prev
            high = max(open_, close) + 0.7
            low = min(open_, close) - 0.6
            prefix.append((open_, high, low, close))
            prev = close
    elif trend == "up":
        closes = [first_open - 8, first_open - 6, first_open - 3.5, first_open - 1.2]
        prefix = []
        prev = closes[0] - 1.2
        for close in closes:
            open_ = prev
            high = max(open_, close) + 0.6
            low = min(open_, close) - 0.7
            prefix.append((open_, high, low, close))
            prev = close
    else:
        offsets = [-1.4, 0.8, -0.7, 0.5]
        prefix = []
        prev = first_open - 0.2
        for offset in offsets:
            close = first_open + offset
            open_ = prev
            high = max(open_, close) + 1.0
            low = min(open_, close) - 1.0
            prefix.append((open_, high, low, close))
            prev = close

    labels = [f'Context {i + 1}' for i in range(len(prefix))] + [f'Pattern {i + 1}' for i in range(len(bars))]
    all_bars = prefix + [tuple(map(float, bar)) for bar in bars]
    prefix_bars, pattern_bars = all_bars[:len(prefix)], all_bars[len(prefix):]
    fig = go.Figure()
    if prefix_bars:
        fig.add_trace(go.Candlestick(
            x=labels[:len(prefix_bars)],
            open=[b[0] for b in prefix_bars], high=[b[1] for b in prefix_bars],
            low=[b[2] for b in prefix_bars], close=[b[3] for b in prefix_bars],
            name='Prior price action', increasing_line_color="#8ea5bf", decreasing_line_color="#64758d",
            increasing_fillcolor="#8ea5bf", decreasing_fillcolor="#64758d",
        ))
    fig.add_trace(go.Candlestick(
        x=labels[len(prefix):],
        open=[b[0] for b in pattern_bars], high=[b[1] for b in pattern_bars],
        low=[b[2] for b in pattern_bars], close=[b[3] for b in pattern_bars],
        name='Selected pattern', increasing_line_color="#059669", decreasing_line_color="#ef4444",
        increasing_fillcolor="#059669", decreasing_fillcolor="#ef4444",
    ))
    fig.update_layout(
        title=dict(text=f"{pattern['name']} · synthetic illustration", x=0.02, xanchor="left"),
        xaxis_title='Read the context before the pattern',
        yaxis_title='Illustrative price (not market data)',
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        # Keep the legend outside the plot area, below the x-axis labels.
        # Extra bottom margin prevents the legend from colliding with the chart.
        legend=dict(orientation="h", yanchor="top", y=-0.24, xanchor="left", x=0),
        margin=dict(l=30, r=28, t=82, b=112),
        height=490,
    )
    return fig


# ============================================================
# Sidebar navigation
# ============================================================
if "completed_lessons" not in st.session_state:
    st.session_state["completed_lessons"] = []
if "quiz_attempts" not in st.session_state:
    st.session_state["quiz_attempts"] = {}
if "main_sidebar_collapsed" not in st.session_state:
    st.session_state["main_sidebar_collapsed"] = False

# Legacy navigation keys for the retired risk/allocation course return to the learning home.
if st.session_state.get("main_nav") in {'06 Returns and Risk', '07 Asset Allocation and Practice', '06 Returns, Risk and Allocation'}:
    st.session_state["main_nav"] = 'Learning Home'
if st.session_state.get("main_nav") in {'07 Risk & Investor Protection', '08 Risk & Investor Protection'}:
    st.session_state["main_nav"] = '06 Risk & Investor Protection'

PAGES = [
    'Learning Home',
    '01 Stock Market Basics',
    '02 Reading Stock Charts',
    '02A Candlestick Patterns',
    '02B Technical Indicators',
    '03 How Orders Work',
    '04 Researching a Company',
    '05 Why Stock Prices Move',
    '06 Risk & Investor Protection',
    'Final Quiz',
    'Data & Methods',
]

if _EMBEDDED:
    chosen_page = st.session_state.get("main_nav", "Learning Home")
    _previous_page = st.session_state.get("_last_main_nav_for_scroll")
    _page_changed = _previous_page is not None and _previous_page != chosen_page
    st.session_state.setdefault("_scroll_sequence", 0)
    if _page_changed:
        st.session_state["_scroll_sequence"] += 1
    st.session_state["_last_main_nav_for_scroll"] = chosen_page
elif not st.session_state["main_sidebar_collapsed"]:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="brand-row">
              <div class="brand-mark">S</div>
              <div><div class="brand-name">StockScope</div><div class="brand-sub">{t("Learn · Market Basics")}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(t('← Hide study path'), key="collapse_main_sidebar", width="stretch"):
            st.session_state["main_sidebar_collapsed"] = True
            st.rerun()
        st.markdown(f'**{t("Your study path")}**')
        chosen_page = st.radio(t('Navigation'), PAGES, key="main_nav", label_visibility="collapsed", format_func=t)
        _previous_page = st.session_state.get("_last_main_nav_for_scroll")
        _page_changed = _previous_page is not None and _previous_page != chosen_page
        if "_scroll_sequence" not in st.session_state:
            st.session_state["_scroll_sequence"] = 0
        if _page_changed:
            st.session_state["_scroll_sequence"] += 1
        st.session_state["_last_main_nav_for_scroll"] = chosen_page
        st.markdown("---")
        completed = set(st.session_state["completed_lessons"])
        progress = len(completed.intersection(set(LESSON_GUIDE.keys()))) / len(LESSON_GUIDE)
        st.caption(t('Course progress'))
        st.progress(progress, text=t('Completed {pct}%', pct=round(progress * 100)))
        quiz_stats = st.session_state.get("quiz_attempts", {})
        mastered_count = sum(bool(quiz_stats.get(name, {}).get("passed")) for name in LESSON_GUIDE)
        st.caption(t('Knowledge checks passed at least once'))
        st.progress(mastered_count / len(LESSON_GUIDE), text=t('{n}/{total} lessons passed', n=mastered_count, total=len(LESSON_GUIDE)))
        st.markdown("---")
        if not _EMBEDDED:
            render_language_toggle()
        st.caption(t('Data sources'))
        st.caption(t('Yahoo Finance / yfinance (prototype)'))
        st.caption(t('Choose a history window on each chart page.'))
        st.caption(t('For learning; not investment advice.'))
else:
    # The floating control remains available after the sidebar contents are hidden.
    st.markdown(
        """<style>
        [data-testid="stSidebar"] { display: none !important; }
        div.st-key-expand_main_sidebar {
          position: fixed !important; left: .55rem !important; top: 3.65rem !important;
          z-index: 100000 !important; width: 154px !important; max-width: calc(100vw - 1rem) !important;
        }
        div.st-key-expand_main_sidebar button {
          min-height: 2.2rem !important; padding: .35rem .65rem !important;
          background: #fff !important; color: #131722 !important;
          border: 1px solid rgba(96,226,189,.55) !important; box-shadow: 0 5px 18px rgba(0,0,0,.25);
        }
        </style>""",
        unsafe_allow_html=True,
    )
    if st.button(t('☰ Show study path'), key="expand_main_sidebar"):
        st.session_state["main_sidebar_collapsed"] = False
        st.rerun()
    chosen_page = st.session_state.get("main_nav", 'Learning Home')
    _previous_page = st.session_state.get("_last_main_nav_for_scroll")
    _page_changed = _previous_page is not None and _previous_page != chosen_page
    if "_scroll_sequence" not in st.session_state:
        st.session_state["_scroll_sequence"] = 0
    if _page_changed:
        st.session_state["_scroll_sequence"] += 1
    st.session_state["_last_main_nav_for_scroll"] = chosen_page


# Stable top target. The actual scroll script is emitted at EOF after the page
# contents have been written, which avoids running before Streamlit's DOM exists.
st.markdown('<div id="stockscope-main-top" style="height:1px;scroll-margin-top:0" aria-hidden="true"></div>', unsafe_allow_html=True)

# ============================================================
# Home
# ============================================================
if chosen_page == 'Learning Home':
    hero("Learning Home", "Start with the basics, learn to read charts, and understand the business behind the numbers. Choose a lesson from your study path or try the historical market challenge below.", "STOCKSCOPE LEARN · START HERE")
    intro = st.columns(3)
    for column, icon, title, body in [
        (intro[0], "📊", "Read the market", "Explore price, volume and chart patterns. Learn what each chart can tell you and what still needs checking."),
        (intro[1], "🔎", "Understand a business", "Discover how companies earn money and connect revenue, profit and cash flow."),
        (intro[2], "🛡️", "Think about risk", "Compare possible returns with uncertainty, verify information and protect your account."),
    ]:
        with column:
            info_card(icon, title, body)
    st.write("")
    completed = set(st.session_state["completed_lessons"])
    n_complete = len(completed.intersection(set(LESSON_GUIDE.keys())))
    m1, m2, m3 = st.columns(3)
    m1.metric(t('Learning units'), t('{n} units', n=len(LESSON_GUIDE)), t('From basic concepts to investor protection'))
    m2.metric(t('Interactive charts'), t('3+ types'), t('Line · bar · scatter'))
    m3.metric(t('Your progress'), f"{n_complete}/{len(LESSON_GUIDE)}", t('Completed lessons'))
    mastered = sum(bool(st.session_state.get("quiz_attempts", {}).get(name, {}).get("passed")) for name in LESSON_GUIDE)
    st.caption(t('Knowledge checks: {mastered}/{total} lessons passed at least once. You can retry. Passing a check and marking a lesson complete are separate actions.', mastered=mastered, total=len(LESSON_GUIDE)))

    st.write("")
    section_heading("REAL-WORLD CHALLENGE", 'Historical Market Challenge', 'Read real historical prices, make your own judgement, then reveal what happened. This exercise does not show that indicators can reliably predict prices.')

    # 01 — A real historical case, with no explicit signal clue until after submission.
    with st.container(border=True):
        st.markdown(
            f'<div class="scenario-intro"><div class="scenario-index">01</div><div><div class="scenario-title">{t("Chart challenge | What happens next?")}</div><div class="scenario-subtitle">{t("Study historical candles, volume, SMA 5 / SMA 20 and MACD (12, 26, 9). Make your judgement, then reveal the next 20 trading days. Signal markers appear only after submission.")}</div></div></div>', unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="callout scenario-color-key"><b>{t("Chart colours:")}</b><span class="color-pill color-up">{t("Green = up")}</span> <span class="color-pill color-down">{t("Red = down")}</span> <span class="color-key-line" style="color:#a66a00">{t("Amber = SMA 5")}</span> <span class="color-key-line" style="color:#2563eb">{t("Blue = SMA 20")}</span><br><span class="scenario-color-note">{t("Volume uses each candle’s colour. MACD histogram colours show positive/negative values, not the stock’s direction.")}</span></div>', unsafe_allow_html=True,
        )
        try:
            signal_case = load_dual_golden_cross_case()
        except Exception:
            signal_case = None

        if signal_case is None:
            st.warning('No complete historical example was found through 2026-10-06. Check your connection and refresh. This question does not replace real data with fictional prices.')
        else:
            full_data = signal_case["data"].copy().sort_values("date").reset_index(drop=True)
            anchor_idx = int(signal_case["anchor_idx"])
            history_start = max(0, anchor_idx - 25)
            future_end_idx = min(anchor_idx + 20, len(full_data) - 1)
            case_data = full_data.iloc[history_start:future_end_idx + 1].copy().reset_index(drop=True)
            case_data["is_future"] = case_data.index >= (anchor_idx - history_start + 1)
            signal_date = pd.Timestamp(full_data.iloc[anchor_idx]["date"])
            ma_cross_date = pd.Timestamp(full_data.iloc[int(signal_case["ma_cross_idx"])]["date"])
            macd_cross_date = pd.Timestamp(full_data.iloc[int(signal_case["macd_cross_idx"])]["date"])
            future_data = full_data.iloc[anchor_idx + 1:future_end_idx + 1].copy()
            if future_data.empty:
                st.warning('This sample lacks a complete following 20 trading days. Refresh to choose another sample.')
            else:
                start_close = float(full_data.iloc[anchor_idx]["close"])
                end_close = float(future_data.iloc[-1]["close"])
                outcome_pct = (end_close / start_close - 1.0) * 100.0
                # Treat very small changes as "unchanged" so the three choices are meaningful.
                neutral_band_pct = 1.0
                actual_class = 0 if outcome_pct > neutral_band_pct else (1 if outcome_pct < -neutral_band_pct else 2)
                answer_options = ['Rise', 'Fall', 'Little change']
                if st.session_state.get("home_scenario_01_result") not in answer_options:
                    st.session_state.pop("home_scenario_01_result", None)
                if st.session_state.get("home_scenario_01_answer") not in answer_options:
                    st.session_state.pop("home_scenario_01_answer", None)
                result_01 = st.session_state.get("home_scenario_01_result")
                fig = dual_signal_figure(
                    case_data, pd.Timestamp(future_data.iloc[-1]["date"]),
                    reveal_future=result_01 is not None,
                    ma_cross_date=ma_cross_date, macd_cross_date=macd_cross_date, height=710,
                )
                if result_01 is None:
                    chart_col, answer_col = st.columns([1.52, 1], gap="large", vertical_alignment="top")
                    with chart_col:
                        st.plotly_chart(fig, width="stretch", key="home_scenario_01_continuous_chart", config={"displaylogo": False})
                        st.caption(
                            f"Historical sample: {signal_case['ticker']}({TICKERS.get(signal_case['ticker'], signal_case['ticker'])}) | Data cutoff: 2026-10-06. After submission, the following 20 trading days appear to the right. Source: Yahoo Finance adjusted daily data."
                        )
                    with answer_col:
                        with st.container(border=True):
                            content_heading("Your judgement", level="h3")
                            st.markdown(
                                f'Study the prices through **{signal_date:%Y-%m-%d}** on the left. Consider prices relative to the averages, volume, and both MACD lines and the histogram.'
                            )
                            st.markdown(f"**{t('Question: Compared with the signal day\'s close, where will the close be 20 trading days later?')}**")
                            st.caption(t('Classification: above +1% = rise; below −1% = fall; −1% to +1% = little change.'))
                            with st.form("home_scenario_01_form"):
                                scenario_01_answer = st.radio(
                                    t('Choose your judgement:'), answer_options, index=None,
                                    key="home_scenario_01_answer",
                                    format_func=t,
                                )
                                scenario_01_submit = st.form_submit_button(t('Reveal what happened'), width="stretch")
                            if scenario_01_submit:
                                if scenario_01_answer is None:
                                    st.warning(t('Choose an answer before revealing the result.'))
                                else:
                                    st.session_state["home_scenario_01_result"] = scenario_01_answer
                                    st.rerun()
                else:
                    # After submission, the question/choices disappear and the same chart expands to full width.
                    st.plotly_chart(fig, width="stretch", key="home_scenario_01_continuous_chart", config={"displaylogo": False})
                    chosen_class = answer_options.index(result_01) if result_01 in answer_options else -1
                    if chosen_class == actual_class:
                        st.success(escape_markdown_dollars(f'Your answer matches history: signal close ${start_close:.2f} → close 20 trading days later ${end_close:.2f}, total change {outcome_pct:+.2f}%。'))
                    else:
                        st.error(escape_markdown_dollars(f'Your answer did not match this sample. Actual change: {outcome_pct:+.2f}%; signal close ${start_close:.2f}; close 20 trading days later ${end_close:.2f}。'))
                    gap = int(signal_case["gap"])
                    gap_description = 'on the same trading day' if gap == 0 else f'separated by {gap} trading days'
                    st.markdown(
                        f'**Why these points matter:** SMA 5 crossed above SMA 20 on **{ma_cross_date:%Y-%m-%d}**; the MACD line crossed above the signal line on **{macd_cross_date:%Y-%m-%d}** (the events occurred {gap_description}). Amber triangles and a dotted line mark the average crossover; purple diamonds and a second vertical line mark the MACD crossover. These nearby events describe stronger short-term price/momentum relationships. Both use historical prices, may lag and can produce false signals; neither guarantees a rise.'
                    )
                    st.caption(
                        f"Sample: {signal_case['ticker']} | Observation date: {signal_date:%Y-%m-%d} | Reveal ends: {pd.Timestamp(future_data.iloc[-1]['date']):%Y-%m-%d}. Real Yahoo Finance adjusted daily data. Candle and volume colours compare open/close; MACD histogram colours show its sign."
                    )
                    if st.button('Try challenge 01 again', key="home_scenario_01_reset"):
                        st.session_state.pop("home_scenario_01_result", None)
                        st.session_state.pop("home_scenario_01_answer", None)
                        st.rerun()

                st.markdown(
                    '<div class="scenario-source">See Data & Methods for sources and definitions. The sample cutoff is 2026-10-06. This is a historical learning exercise, not a prediction or investment recommendation.</div>',
                    unsafe_allow_html=True,
                )

    st.write("")
    section_heading("YOUR LEARNING PATH", t('A beginner path of {n} learning units', n=len(LESSON_GUIDE)), 'Each lesson includes concepts, examples, exploration or practice. Study in order or revisit any topic.')
    cards_data = [
        ("01", "📘", 'Stock Market Basics', 'Stocks, bonds, indices, ETFs, exchanges and market capitalization.', 'Core concepts', '01 Stock Market Basics'),
        ("02", "📊", 'Reading Stock Charts', 'Candles, volume, quotes and timeframes.', 'Interactive charts', '02 Reading Stock Charts'),
        ("02A", "🕯️", 'Candlestick Patterns', 'Single and multiple-candle patterns with trend context and confirmation.', 'Pattern workshop', '02A Candlestick Patterns'),
        ("02B", "📈", 'Technical Indicators', 'Understand averages, momentum, volatility and volume alongside prices.', 'Charting extension', '02B Technical Indicators'),
        ("03", "🧾", 'How Orders Work', 'Brokers, order types, bid-ask spreads, costs and execution.', 'Trade mechanics', '03 How Orders Work'),
        ("04", "🔎", 'Researching a Company', 'Financial statements, key ratios and reliable sources.', 'Company research', '04 Researching a Company'),
        ("05", "🧩", 'Why Stock Prices Move', 'Earnings, rates, expectations and market influences.', 'Case studies', '05 Why Stock Prices Move'),
        ("06", "🛡️", 'Risk & Investor Protection', 'Scams, overconfidence, leverage and unreliable information.', 'Safety and discipline', '06 Risk & Investor Protection'),
    ]
    for row_start in range(0, len(cards_data), 2):
        row_cards = st.columns(2)
        for col, d in zip(row_cards, cards_data[row_start:row_start + 2]):
            with col:
                status = t('✓ Completed') if d[5].split(" ", 1)[-1] in completed else t(d[4])
                with st.container(key=f"home_lesson_{d[0]}"):
                    st.markdown(
                        f'<div class="lesson-card"><div class="lesson-top"><div class="lesson-icon">{d[1]}</div><div class="lesson-no">LESSON {d[0]}</div></div><div class="lesson-title">{t(d[2])}</div><div class="lesson-text">{t(d[3])}</div><span class="tag">{status}</span></div>',
                        unsafe_allow_html=True,
                    )
                    st.button(t('Open lesson →'), key=f"home_{d[0]}", width="stretch", on_click=nav_to, args=(d[5],))

    st.write("")
    section_heading("TOOLS FOR LEARNING", 'Quizzes and data tools', 'Review the course in the final quiz or download cleaned historical data for study.')
    quick_a, quick_b = st.columns(2)
    with quick_a:
        with st.container(key="home_tool_quiz"):
            info_card("✓", 'Final Quiz', 'Check your understanding of stock basics, charts, company research, returns and risk.')
            st.button(t('Start final quiz →'), key="home_open_comprehensive_quiz", width="stretch", on_click=nav_to, args=('Final Quiz',))
    with quick_b:
        with st.container(key="home_tool_data"):
            info_card("↗", 'Data & Methods', 'Review data sources, definitions and limitations; export a learning dataset.')
            st.button(t('Open Data & Methods →'), key="home_open_data_methods", width="stretch", on_click=nav_to, args=('Data & Methods',))

    st.write("")
    section_heading("START HERE", 'New to stocks? Remember these three ideas')
    c1, c2, c3 = st.columns(3)
    with c1:
        info_card("🧩", 'Price is not value', 'A share price quotes one unit. Comparing share prices alone does not value companies.')
    with c2:
        info_card("📉", 'Consider returns and risk together', 'Past gains do not guarantee future gains. Check variability, drawdowns and the time window.')
    with c3:
        info_card("🔎", 'Data needs context', 'Charts describe what happened; a line alone rarely proves why.')
    st.markdown('<div class="callout">Learning goal: ask better questions instead of memorising a supposedly guaranteed signal.</div>', unsafe_allow_html=True)



# ============================================================
# Lesson 1: Stock basics
# ============================================================
elif chosen_page == '01 Stock Market Basics':
    hero(
        'Lesson 01 | Understanding the Stock Market',
        'Start with what owning a share means, then explore issuance, trading, pricing, investment products, participants, returns and risks.',
        "LESSON 01 · THE BASICS",
    )

    section_heading(
        "THE BIG PICTURE",
        'Build a map of the market',
        'Begin with ownership and financing, move to markets and investment products, and finish with returns, risks and readiness.',
    )
    overview_cols = st.columns(3)
    with overview_cols[0]:
        info_card("🏢", 'Companies and shares', "Companies divide ownership into shares. Buying a stock gives you part of the company's equity; it is different from lending it money.", 'Ownership')
    with overview_cols[1]:
        info_card("🔄", 'Issuance and trading', 'Companies raise capital by issuing securities. Investors trade existing shares in the secondary market, where orders and expectations help form prices.', 'Market mechanics')
    with overview_cols[2]:
        info_card("⚖️", 'Returns and risk', 'Returns may come from price changes and dividends. Risks include falling prices, a weakening business, limited liquidity and concentrated holdings.', 'Investment judgement')

    lesson1_sections = [
        '01 What a share represents',
        '02 How markets work',
        '03 Common investment products',
        '04 Prices and returns',
        '05 Risk and getting started',
    ]
    with st.container(key="lesson1_section_nav"):
        lesson_section = st.pills(
            t("Lesson sections"),
            options=lesson1_sections,
            default=lesson1_sections[0],
            required=True,
            selection_mode="single",
            wrap=True,
            key=lang_key("lesson1_section"),
            format_func=t,
            label_visibility="collapsed",
            width="content",
        )

    if lesson_section == lesson1_sections[0]:
        section_heading("OWNERSHIP", "A share is part of a company's ownership", 'It is not a debt promise or a fixed-income product.')
        st.markdown(
            """Owning shares means owning part of a company's equity. Common shareholders may have voting rights and receive dividends; rights depend on share class, company documents and local rules. Dividends and price gains are not guaranteed.

Returns and risks depend on the business, finances, competition, expectations and broader markets. In a liquidation, common shareholders generally rank behind creditors and other senior claims. There may be nothing left for them."""
        )
        with st.container(border=True):
            section_heading("TRY THE NUMBERS", 'Use a fictional company to understand market capitalization', 'Change the share price and number of shares to see why unit price differs from total equity market value.')
            calc_a, calc_b, calc_c = st.columns(3)
            with calc_a:
                market_price = st.slider(
                    'Assumed share price (USD)', min_value=5, max_value=200, value=20, step=5,
                    key="lesson1_market_price",
                )
            with calc_b:
                shares_outstanding_m = st.slider(
                    'Shares outstanding (millions)', min_value=1, max_value=1000, value=100, step=1,
                    key="lesson1_shares_outstanding_m",
                )
            with calc_c:
                held_shares = st.number_input(
                    'Assumed shares held', min_value=1, max_value=100000, value=100, step=100,
                    key="lesson1_held_shares",
                )
            outstanding_shares = int(shares_outstanding_m) * 1_000_000
            market_cap = float(market_price) * outstanding_shares
            holding_value = float(market_price) * int(held_shares)
            ownership_pct = int(held_shares) / outstanding_shares * 100
            result_a, result_b, result_c = st.columns(3)
            with result_a:
                st.markdown(escape_markdown_dollars(f'**Assumed market capitalization**\n\n## ${market_cap:,.0f}'))
                st.caption('Share price × shares outstanding')
            with result_b:
                st.markdown(escape_markdown_dollars(f'**Market value of this holding**\n\n## ${holding_value:,.2f}'))
                st.caption('Assumed current price × shares held')
            with result_c:
                st.markdown(f'**Ownership percentage**\n\n## {ownership_pct:.6f}%')
                st.caption('Shares held ÷ shares outstanding')
            st.caption('This is a simplified learning calculation. Check share-count definitions in real data. Market capitalization is equity market value, not book assets, cash or enterprise value.')

        with st.expander('Share price and value: two different ideas'):
            st.markdown(
                """- **Share price:** the quoted or last traded price of one share at a point in time.
- **Market capitalization:** commonly estimated as price × shares outstanding.
- **Valuation:** also requires future cash flow, growth, competitive advantages, financial position and risk. Market cap alone does not tell you whether a stock is cheap."""
            )

    if lesson_section == lesson1_sections[1]:
        section_heading("MARKET STRUCTURE", 'From issuing shares to completing a trade', 'Separate issuers, investors, brokers, trading venues and regulators.')
        st.markdown(
            """**Primary market: issuing securities to raise capital.** An IPO or later share offering can raise money through newly issued shares. Structures and rules differ by market.

**Secondary market: trading existing securities.** Investors commonly trade through brokers. In an ordinary secondary trade, money changes hands between buyer and seller; the company does not directly receive the price every time a share is resold. Later offerings and buybacks are separate corporate actions."""
        )
        participants = st.columns(3)
        with participants[0]:
            info_card("🏭", 'Issuer', 'A company raises capital through securities and discloses important business and financial information under applicable rules.')
        with participants[1]:
            info_card("👥", 'Investors', 'Individuals, funds, pension plans and institutions submit orders according to their goals and constraints.')
        with participants[2]:
            info_card("🔗", 'Brokers and trading venues', 'Brokers receive and route orders. Exchanges and other venues provide matching and execution mechanisms.')
        with st.expander('A typical stock trade'):
            st.markdown(
                """**Investor decides → submits an order to a broker → broker routes the order → a venue or liquidity provider executes it → clearing and settlement deliver securities and cash.**

Execution depends on broker arrangements, market structure, order type and liquidity. Clicking Buy does not guarantee the last displayed price. Volatility and the bid-ask spread also affect the result."""
            )
        with st.expander('Why do public companies disclose information?'):
            st.markdown(
                'Investors need verifiable information. US filings commonly include annual reports (10-K), quarterly reports (10-Q) and current reports (8-K). Other markets have different rules. Financial statements, announcements and risk factors connect market stories with company research.'
            )

    if lesson_section == lesson1_sections[2]:
        section_heading("INVESTMENT VEHICLES", 'Stocks, bonds, indices and ETFs are different', 'Understand what you own before comparing price and risk.')
        tool_table = pd.DataFrame([
            {'Product': 'Stock', 'What you own': "Part of a company's equity", 'Possible returns': 'Price changes and possible dividends', 'Risks to understand': 'Business, valuation and market-price risk'},
            {'Product': 'Bond', 'What you own': 'Generally a claim against the issuer', 'Possible returns': 'Interest and repayment depend on terms and creditworthiness', 'Risks to understand': 'Credit, interest-rate, inflation and liquidity risk'},
            {'Product': 'Stock index', 'What you own': 'A rules-based measure of a group of securities', 'Possible returns': 'An index is a measure and generally cannot itself be traded like a share', 'Risks to understand': 'Constituents, weights and rebalancing affect what it represents'},
            {'Product': "ETF", 'What you own': 'Fund shares traded on an exchange', 'Possible returns': 'Depends on underlying assets, costs and market prices', 'Risks to understand': 'Market risk, costs, tracking error and liquidity'},
            {'Product': 'Mutual fund', 'What you own': "Pooled money invested according to a fund's objectives", 'Possible returns': 'Depends on holdings, strategy and costs', 'Risks to understand': 'Market/strategy risk, management fees and redemption terms'},
        ])
        st.dataframe(tool_table, width="stretch", hide_index=True)
        st.markdown(
            '**An index is not an index fund.** An index measures a market or basket of securities. An index fund, structured as an ETF or mutual fund, tries to follow it. A broader basket can reduce company-specific concentration but cannot remove a market-wide decline.'
        )
        with st.expander('Common/preferred shares and investment styles'):
            st.markdown(
                """- **Common and preferred shares:** voting, dividends and liquidation priority can differ; check terms.
- **Growth and value:** growth focuses on expected expansion; value compares market price with estimated business value. Neither label guarantees returns.
- **Large, mid and small cap:** categories based on market capitalization; thresholds vary.
- **Bull and bear markets:** describe broader trends, not a conclusion from one day's move."""
            )

    if lesson_section == lesson1_sections[3]:
        section_heading("PRICE & RETURN", 'Price is a trading outcome; return has several components', 'A market price reflects transactions and expectations at a moment in time, not a direct reading of intrinsic value.')
        st.markdown(
            """- **Bid:** a buyer's quoted price; the best bid is the highest available bid.
- **Ask:** a seller's quoted price; the best ask is the lowest available ask.
- **Bid-ask spread:** ask minus bid, one part of trading cost.
- **Last price:** a completed trade's price, not a guarantee for your next order.

Orders, company news, industries, interest rates, the economy, sentiment and liquidity can change prices. Good results may still disappoint expectations, and a stock can fall despite a strong business report."""
        )
        with st.container(border=True):
            section_heading("TRY A RETURN EXAMPLE", 'Try it: price changes plus dividends', 'Assume a $20 purchase price. Change the current price and dividends per share to see a simple total return.')
            return_a, return_b, return_c = st.columns(3)
            with return_a:
                purchase_price = 20.0
                st.markdown(escape_markdown_dollars("""**Assumed purchase price**

## $20.00"""))
                st.caption('Cost per share before fees')
            with return_b:
                ending_price = st.slider(
                    'Assumed current share price (USD)', min_value=5, max_value=35, value=22, step=1,
                    key="lesson1_ending_price",
                )
            with return_c:
                dividend_per_share = st.slider(
                    'Dividends per share during the period (USD)', min_value=0.0, max_value=2.0, value=0.5, step=0.25,
                    key="lesson1_dividend_per_share",
                )
            return_shares = st.number_input(
                'Assumed shares held', min_value=1, max_value=10000, value=100, step=10,
                key="lesson1_return_shares",
            )
            price_change_per_share = float(ending_price) - purchase_price
            total_return_cash = (price_change_per_share + float(dividend_per_share)) * int(return_shares)
            starting_value = purchase_price * int(return_shares)
            simple_total_return = total_return_cash / starting_value * 100
            st.markdown(escape_markdown_dollars(
                f'**Price change:** ${price_change_per_share:,.2f}/share    **Assumed dividend:** ${float(dividend_per_share):,.2f}/share    **Total return before taxes/fees:** ${total_return_cash:,.2f}({simple_total_return:+.2f}%)'
            ))
            st.caption('Assumes dividends have been received and excludes taxes, fees, reinvestment and holding-period differences. Dividends may not offset a price loss.')
        with st.expander('Basic stock order types'):
            st.markdown(
                'A **market order** prioritises prompt execution without guaranteeing price. A **limit order** sets an acceptable price or better, but may not fill. A **stop order** generally becomes a market order when triggered, so its trigger is not a guaranteed execution price. Broker and market rules vary; the next lesson explores execution.'
            )

    if lesson_section == lesson1_sections[4]:
        section_heading("RISK & READINESS", 'Set boundaries before choosing products', 'Risk includes timing, costs, liquidity and behaviour as well as price movement.')
        readiness = st.columns(2)
        with readiness[0]:
            info_card("🎯", 'Goals and time horizon', 'Write down what the money is for and when it is needed. Necessary short-term spending leaves less room for large price swings.')
            info_card("🧯", 'Cash and debt', 'Consider emergency funds, everyday costs and expensive debt before exposing essential money to volatile assets.')
            info_card("📚", 'Understand the product', 'Explain what you own, how returns arise and what could go wrong.')
        with readiness[1]:
            info_card("🧺", 'Diversification and concentration', 'Spreading across businesses, industries and asset classes can reduce some concentration risk, but cannot guarantee profit or prevent a broad decline.')
            info_card("💸", 'Costs and liquidity', 'Compare commissions, spreads, fund expenses, taxes and currency costs. Thinly traded securities can be difficult to sell at a desired price.')
            info_card("🔎", 'Verify sources', 'Check filings, announcements, fund documents and intermediary registration. Be wary of guaranteed returns, urgent transfers and secret tips.')
        with st.expander('Five common beginner mistakes'):
            st.markdown(
                """1. **Comparing unit prices only:** ignoring share count, market cap, earnings, growth and risk.
2. **Assuming past gains must continue:** history is not a guarantee.
3. **Treating dividends as free money:** total return includes price changes, distributions and costs.
4. **Treating ETFs as risk-free:** holdings, concentration, costs and tracking error still matter.
5. **Ignoring goals and timing:** choices need to reflect the purpose, horizon and ability to bear losses."""
            )

    section_heading("KEY TERMS", 'Quick glossary')
    glossary = pd.DataFrame([
        {'Term': 'Share', 'Plain-English meaning': 'An ownership interest in a company.'},
        {'Term': 'Initial Public Offering (IPO)', 'Plain-English meaning': 'An initial public share offering; structures differ by market.'},
        {'Term': 'Secondary market', 'Plain-English meaning': 'A market for existing securities; ordinary resales usually do not directly raise money for the issuer.'},
        {'Term': 'Market capitalization', 'Plain-English meaning': 'Commonly calculated as price × shares outstanding.'},
        {'Term': 'Index', 'Plain-English meaning': 'A rules-based measure of a group of securities.'},
        {'Term': 'Liquidity', 'Plain-English meaning': 'How easily an asset can trade without a large price concession.'},
        {'Term': 'Diversification', 'Plain-English meaning': 'Spreading sources of risk to reduce concentration, without guaranteeing against losses.'},
    ])
    st.dataframe(glossary, width="stretch", hide_index=True)

    st.write("")
    section_heading("QUICK CHECK", 'Check your understanding')
    answer = st.radio(
        'Company A trades at $20 a share and B at $200. Can this alone tell us which company is more expensive?',
        ["Yes: B's higher share price means it is more expensive.", 'No: we also need share count, market cap, earnings and other information.', 'Yes: a higher share price always means higher risk.'],
        key="basics_quiz",
    )
    if st.button('Submit answer', key="basics_submit"):
        if answer.startswith('No'):
            record_quiz_attempt('Stock Market Basics', True)
            st.success('Correct. A share price is a unit price. Valuation also needs share count, market cap, earnings, growth expectations and risk.')
        else:
            record_quiz_attempt('Stock Market Basics', False)
            st.error('Think again: share counts can differ greatly. Unit price alone cannot compare total market capitalization or valuation. Review the explanation and retry.')
    lesson_completion_button('Stock Market Basics', "finish_basics")


# ============================================================
# Lesson 2: Read charts
# ============================================================
elif chosen_page == '02 Reading Stock Charts':
    hero('Lesson 02 | Reading Stock Charts', 'Look beyond red and green. Read the open, high, low, close and volume behind a candle.', "LESSON 02 · READ THE CHART")
    left, right = st.columns([1.05, 2.0])
    with left:
        symbol = st.selectbox(t('Choose a stock'), list(TICKERS.keys()), index=list(TICKERS.keys()).index("NVDA"), format_func=ticker_label, key=lang_key("chart_ticker"))
        # Migrate a previously selected period that is no longer offered in this chart.
        chart_period_key = lang_key("chart_period")
        if st.session_state.get(chart_period_key) == "5y" or st.session_state.get("chart_period") == "5y":
            st.session_state[chart_period_key] = "3mo"
        lesson_period = st.selectbox(t('History window'), ["1mo", "3mo", "6mo", "1y"], index=1, format_func=lambda x: t(PERIODS[x]), key=chart_period_key)
        st.markdown('<div class="callout">Start with three months. Hover over candles and inspect the OHLC values one by one.</div>', unsafe_allow_html=True)
        content_heading('Five chart essentials')
        st.markdown("""**Open:** price at the start of the bar.

**High:** highest price during it.

**Low:** lowest price during it.

**Close:** price at the end.

**Volume:** reported shares traded during the bar.""")
    chart_data, chart_error = safe_prices([symbol], lesson_period)
    show_data_warning(chart_error)
    with right:
        if not chart_data.empty:
            one = chart_data[chart_data["ticker"] == symbol].sort_values("date").copy()
            latest = one.iloc[-1]
            previous = one.iloc[-2]["close"] if len(one) > 1 else np.nan
            daily_change = (latest["close"] / previous - 1) * 100 if pd.notna(previous) and previous else np.nan
            k1, k2, k3 = st.columns(3)
            k1.metric('Latest available close', format_money(latest["close"]))
            k2.metric('Vs previous trading day', format_pct(daily_change))
            k3.metric('Latest daily volume', f"{latest['volume']:,.0f}" if pd.notna(latest["volume"]) else "—")

            content_heading(f'{symbol} · daily candles')
            candle = go.Figure(data=[go.Candlestick(
                x=one["date"], open=one["open"], high=one["high"], low=one["low"], close=one["close"], name=symbol,
                increasing_line_color="#059669", decreasing_line_color="#ef4444",
                increasing_fillcolor="#059669", decreasing_fillcolor="#ef4444",
            )])
            candle.update_layout(title=None, xaxis_title='Date', yaxis_title='Price (USD)', xaxis_rangeslider_visible=False, hovermode="x unified")
            style_fig(candle, 440)
            candle.update_layout(margin=dict(l=32, r=18, t=24, b=36))
            st.plotly_chart(candle, width="stretch", key="lesson_candle")

    if not chart_data.empty:
        section_heading("LOOK CLOSER", 'Read price and volume together')
        # Keep a visual gap between the section heading and the standalone chart caption.
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)
        one = chart_data[chart_data["ticker"] == symbol].sort_values("date").copy()
        one['Volume colour'] = np.where(one["close"] >= one["open"], 'Close at/above open', 'Close below open')
        content_heading('Daily volume')
        st.caption('Taller bars mean more reported shares traded. Green means close at/above open; red means close below open.')
        vol = px.bar(
            one, x="date", y="volume", color='Volume colour',
            color_discrete_map={'Close at/above open': "#059669", 'Close below open': "#ef4444"},
        )
        vol.update_layout(
            xaxis_title='Date', yaxis_title='Volume (shares)', showlegend=False,
        )
        style_fig(vol, 350)
        vol.update_layout(margin=dict(l=34, r=18, t=22, b=42))
        st.plotly_chart(vol, width="stretch")
        st.markdown('Volume describes activity; direction needs price action and context.')
        with st.expander('Latest 12 trading days: OHLCV'):
            show = one.tail(12)[["date", "open", "high", "low", "close", "volume"]].rename(columns={"date": 'Date', "open": 'Open', "high": 'High', "low": 'Low', "close": 'Close', "volume": 'Volume'})
            st.dataframe(show.sort_values('Date', ascending=False), width="stretch", hide_index=True)
            st.download_button('Download stock data CSV', show.to_csv(index=False).encode("utf-8-sig"), file_name=f"{symbol}_OHLCV.csv", mime="text/csv")

        section_heading("QUICK CHECK", 'What can this chart tell you?')
        pick = st.radio("A day's volume rises sharply. What is the most careful interpretation?", ['The price must rise tomorrow.', 'Trading is busier; direction needs other evidence.', 'Company profit has definitely increased.'], key="volume_quiz")
        if st.button('Check understanding', key="volume_submit"):
            if pick.startswith('Trading'):
                record_quiz_attempt('Reading Stock Charts', True)
                st.success('Correct. Volume describes activity, not a standalone forecast. Write down one observation from the chart.')
            else:
                record_quiz_attempt('Reading Stock Charts', False)
                st.error('Volume does not guarantee direction or prove a change in company earnings. Review and retry.')
        with st.expander('More: timeframes, adjusted prices and common mistakes'):
            st.markdown("""**Timeframes:** minute candles show short-term detail; daily candles summarise trading days; weekly/monthly candles show longer periods. Noise and detail vary with the interval.

**Raw and adjusted prices:** splits and dividends can change historical adjusted OHLC. Check source definitions; adjusted history is not necessarily the price quoted at the time.

**Colours:** conventions differ by platform and market. Read the legend and OHLC, not colour alone.

**Limits:** candles and volume describe past activity. Explaining causes also requires events, fundamentals and market context.""")

        lesson_completion_button('Reading Stock Charts', "finish_chart")


# ============================================================
# Lesson 2A: Candlestick patterns (single / multi-candle)
# ============================================================
elif chosen_page == '02A Candlestick Patterns':
    st.markdown('<div id="candle-pattern-top"></div>', unsafe_allow_html=True)
    hero(
        'Lesson 02A | Candlestick Patterns',
        'Explore single and multiple-candle structures, their context and traditional interpretations. Patterns describe price action, not guaranteed outcomes.',
        "LESSON 02A · CANDLESTICK PATTERNS",
    )
    st.markdown('[↑ Back to lesson top](#candle-pattern-top)', unsafe_allow_html=False)
    st.markdown("**Read the context:** earlier trend, location, volume and later price action matter. A pattern's name is not an independent trading signal.")

    # The standalone candle anatomy/color explainer was removed at the user's request.

    group_names = list(dict.fromkeys(pattern["group"] for pattern in CANDLE_PATTERNS))
    selector_left, selector_right = st.columns([1, 1.5], gap="large")
    with selector_left:
        chosen_group = st.selectbox('Step 1: choose a pattern group', group_names, key="candle_pattern_group")
        candidates = [pattern for pattern in CANDLE_PATTERNS if pattern["group"] == chosen_group]
        available_pattern_names = [pattern["name"] for pattern in candidates]
        # When the category changes, reset an old pattern name that is no longer
        # available before Streamlit instantiates the dependent selectbox.
        if st.session_state.get("candle_pattern_name") not in available_pattern_names:
            st.session_state["candle_pattern_name"] = available_pattern_names[0]
        chosen_pattern_name = st.selectbox('Step 2: choose a pattern', available_pattern_names, key="candle_pattern_name")
        # Selecting another candle pattern intentionally does NOT scroll the page.
        # Users often compare patterns while reading farther down this lesson; keep
        # their current reading position. Auto-scroll is reserved for main navigation.
        chosen_pattern = next(pattern for pattern in candidates if pattern["name"] == chosen_pattern_name)
        st.markdown(
            f"""<div class="lesson-card"><div class="lesson-top"><div class="lesson-icon">🕯️</div><div class="lesson-no">{len(chosen_pattern['bars'])} candles</div></div><div class="lesson-title">{escape(chosen_pattern['name'])}</div><div class="lesson-text">{escape(chosen_pattern['structure'])}</div><div style="margin-top:.8rem"><span class="tag">Traditional interpretation: {escape(chosen_pattern['bias'])}</span></div></div>""",
            unsafe_allow_html=True,
        )
        content_heading('Recognition checklist')
        st.markdown(chosen_pattern["recognize"])
        content_heading('Common interpretation')
        st.markdown(chosen_pattern["meaning"])
    with selector_right:
        content_heading('Candle structure')
        pattern_fig = build_candle_pattern_figure(chosen_pattern)
        style_fig(pattern_fig, 490)
        # The selected pattern name is already shown in the information card.
        # Keep the chart itself title-free so long names never collide with the plot.
        pattern_fig.update_layout(
            title=None,
            height=490,
            margin=dict(l=30, r=28, t=28, b=112),
            legend=dict(orientation="h", yanchor="top", y=-0.24, xanchor="left", x=0),
        )
        st.plotly_chart(pattern_fig, width="stretch", key="candle_pattern_diagram")
        st.caption("Synthetic OHLC values illustrate structure, not a real security's history. Green means close above open; red means close below open.")

    context_cols = st.columns(2, gap="large")
    with context_cols[0]:
        info_card("📍", 'Context', chosen_pattern["context"], 'Read the preceding trend')
    with context_cols[1]:
        info_card("🔎", 'Later confirmation', chosen_pattern["confirmation"], 'Not an automatic trade signal')

    with st.expander('Pattern reference table', expanded=False):
        pattern_table = pd.DataFrame([
            {
                'Group': p["group"],
                'Pattern': p["name"],
                'Candle count': len(p["bars"]),
                'Traditional interpretation': p["bias"],
                'Key context': p["context"],
            }
            for p in CANDLE_PATTERNS
        ])
        filter_group = st.selectbox('Filter by group', ['All'] + group_names, key="candle_pattern_table_filter")
        if filter_group != 'All':
            pattern_table = pattern_table[pattern_table['Group'] == filter_group]
        st.dataframe(pattern_table, width="stretch", hide_index=True)

    st.write("")
    section_heading("STEP 2 · REAL MARKET", 'Practise on historical prices', 'Illustrations teach structure; real charts develop observation. Describe the prior trend first and avoid forcing an unclear shape into a pattern name.')
    real_left, real_right = st.columns([1, 2], gap="large")
    with real_left:
        real_symbol = st.selectbox(t('Real stock / ETF'), list(TICKERS.keys()), index=list(TICKERS.keys()).index("NVDA"), format_func=ticker_label, key=lang_key("candle_real_symbol"))
        real_period = st.selectbox(t('History range'), ["5d", "1mo", "3mo", "6mo", "1y"], index=2, format_func=lambda x: t(PERIODS[x]), key=lang_key("candle_real_period"))
        st.markdown('<div class="callout">Practice in this order: ① Check the earlier trend. ② Compare the body and wicks. ③ Notice where the pattern appears. ④ Check whether the next candles support the idea.</div>', unsafe_allow_html=True)
    real_data, real_error = safe_prices([real_symbol], real_period)
    show_data_warning(real_error)
    with real_right:
        # load_prices already respects the selected period; don't truncate a one-year view to 90 candles.
        real_one = real_data[real_data["ticker"] == real_symbol].sort_values("date").copy() if not real_data.empty else pd.DataFrame()
        if not real_one.empty:
            content_heading(f'{real_symbol} · Historical daily candles ({PERIODS[real_period]})')
            real_fig = go.Figure(data=[go.Candlestick(
                x=real_one["date"], open=real_one["open"], high=real_one["high"], low=real_one["low"], close=real_one["close"], name=real_symbol,
                increasing_line_color="#059669", decreasing_line_color="#ef4444",
                increasing_fillcolor="#059669", decreasing_fillcolor="#ef4444",
            )])
            real_fig.update_layout(title=None, xaxis_title='Date', yaxis_title='Adjusted price (USD)', xaxis_rangeslider_visible=False, hovermode="x unified")
            style_fig(real_fig, 430)
            real_fig.update_layout(margin=dict(l=30, r=18, t=24, b=36))
            st.plotly_chart(real_fig, width="stretch", key="candle_patterns_real_chart")
        else:
            st.info('No history is available right now. Explore the sample charts above and try again later.')

    st.markdown('**What candlestick patterns do:** They describe price structure and suggest questions to investigate. Results vary by market, sample, pattern definition and trading costs. Test an idea against historical data before judging its usefulness.')
    section_heading("STEP 3 · PRACTICE", 'Candlestick pattern check', 'Answer first, then read the explanations. Get at least 5 correct to pass this chapter. You can try again.')
    pattern_questions = [
        ('A Hammer and a Hanging Man look similar. What mainly distinguishes them?', ['The candle color', 'The trend before the pattern', 'The share price'], 1, 'A Hammer is usually discussed after a decline; a Hanging Man after a rise. Their shapes are similar, so the earlier trend matters more than color.'),
        ('What is the most careful basic reading of a Doji?', ['The price must reverse', 'Open and close are close together: neither side made much net progress in that interval', 'Trading volume is at its highest'], 1, 'A Doji describes an open and close close together. It does not choose the next direction. Check the earlier trend and later candles.'),
        ('What is the typical Bullish Engulfing structure?', ['A small green body fits inside the previous red body', 'A later green body covers the previous red body', 'Three candles with falling closes'], 1, 'A typical Bullish Engulfing has a bearish body followed by a larger bullish body. Context and confirmation still matter.'),
        ('What is the classic three-candle Morning Star structure?', ['A long red candle, a small body, then a strong green candle', 'Three long green candles', 'Three Doji candles'], 0, 'A Morning Star is a possible recovery after a decline: strong selling, then hesitation, then an upward recovery in the third candle.'),
        ('What can a long upper wick tell you?', ['The price will definitely fall', 'The price reached higher levels but did not hold them; check the trend, location and later candles', 'Company profits must be falling'], 1, 'An upper wick shows that price went higher during the interval and fell back before the close. It cannot prove what comes next.'),
        ('Why check later candles after spotting a pattern?', ['A pattern name cannot decide the future; later price action adds evidence', 'To make the chart colors look better', 'Every pattern finishes within two candles'], 0, 'Later price action can support or weaken the first interpretation, without guaranteeing a result. Waiting may also mean missing part of a move.'),
        ('What is a responsible way to use candlestick patterns?', ['Buy immediately whenever a bullish pattern appears', 'Use them as clues alongside trend, key levels, volume, risk and other evidence', 'Choose only the prettiest historical examples'], 1, 'Patterns describe price action. They are not standalone trading instructions. Use context, clear risk limits and independent checks.'),
    ]
    with st.form("candle_patterns_quiz_form"):
        quiz_answers = []
        for qi, (question, options, correct_idx, explanation) in enumerate(pattern_questions):
            quiz_answers.append(st.radio(f"{qi+1}. {question}", options, key=f"candle_pattern_quiz_{qi}", index=None))
        quiz_submit = st.form_submit_button('Submit chapter answers', width="stretch")
    if quiz_submit:
        score = sum(answer == question[1][question[2]] for answer, question in zip(quiz_answers, pattern_questions))
        all_answered = all(answer is not None for answer in quiz_answers)
        if not all_answered:
            st.warning('Answer every question before submitting.')
        else:
            passed = score >= 5
            record_quiz_attempt('Candlestick Patterns', passed)
            st.session_state["candle_pattern_quiz_result"] = {"score": score, "passed": passed, "answers": quiz_answers}
    result = st.session_state.get("candle_pattern_quiz_result")
    if result:
        if result["passed"]:
            st.success(f"You answered {result['score']}/{len(pattern_questions)} correctly and passed the pattern check.")
        else:
            st.warning(f"You answered {result['score']}/{len(pattern_questions)} correctly. Read the explanations and try again. Any earlier pass stays recorded.")
        for qi, (question, options, correct_idx, explanation) in enumerate(pattern_questions):
            chosen_answer = result["answers"][qi]
            with st.expander(f"{('✓' if chosen_answer == options[correct_idx] else '↻')} Question {qi + 1} explanation"):
                st.markdown(f'**Correct answer:** {options[correct_idx]}\n\n{explanation}')
    lesson_completion_button('Candlestick Patterns', "finish_candle_patterns")
    st.markdown('[↑ Back to lesson top](#candle-pattern-top)', unsafe_allow_html=False)


# ============================================================
# Lesson 02B: Technical indicators
# ============================================================
elif chosen_page == '02B Technical Indicators':
    hero(
        'Lesson 02B | Technical Indicators: From Lines to Meaning',
        'Learn what each indicator measures, then connect it to the price chart. Indicators help describe trend, momentum, volatility and volume; they do not predict the answer.',
        "LESSON 02B · TECHNICAL INDICATORS",
    )
    st.markdown(
        '<div class="callout"><b>Start with this idea:</b> Technical indicators turn past prices or volume into lines and readings that are easier to inspect. They organize information; they cannot reveal the future. Sensitive settings may react faster and produce more false signals. Several indicators using the same prices are not several independent pieces of evidence.</div>',
        unsafe_allow_html=True,
    )
    section_heading(
        "INTERACTIVE LAB", 'Indicator lab | Learn one tool at a time',
        'Start with candles alone. Choose one indicator to see its lines or lower panel, then read the explanation directly below the chart.',
    )
    control_a, control_b, control_c = st.columns([1.05, 1.05, 1.7], gap="medium")
    with control_a:
        tech_symbol = st.selectbox(
            t('Choose a stock / ETF'), list(TICKERS.keys()),
            index=list(TICKERS.keys()).index("NVDA"), format_func=ticker_label, key=lang_key("tech_lab_symbol"),
        )
    with control_b:
        # Migrate the old session value before the widget is created.
        tech_period_key = lang_key("tech_lab_period")
        if st.session_state.get(tech_period_key) == "5y" or st.session_state.get("tech_lab_period") == "5y":
            st.session_state[tech_period_key] = "3mo"
        tech_period = st.selectbox(
            t('History range'), ["1mo", "3mo", "6mo", "1y"], index=1,
            format_func=lambda value: t(PERIODS[value]), key=tech_period_key,
        )
    with control_c:
        tech_indicator_choice = st.selectbox(
            t('Choose one indicator'),
            [
                'Candles only',
                'MA | Simple Moving Average (SMA 5 / SMA 20)',
                'EMA | Exponential Moving Average (EMA 12 / EMA 26)',
                'Bollinger Bands (20, 2)',
                'RSI(14)',
                'MACD(12, 26, 9)',
                'Stochastic',
                'ADX (trend strength)',
                'OBV (On Balance Volume)',
                'Support and Resistance',
                'Fibonacci Retracement',
                'VWAP (concept)',
                'Ichimoku Cloud (concept)',
            ],
            index=0,
            key="tech_lab_indicator_choice",
            format_func=t,
            help=t('Choose one tool at a time. SMA, EMA, Bollinger Bands, Support and Resistance, and Fibonacci Retracement appear on the price chart. RSI, MACD, Stochastic, ADX and OBV appear below it.'),
        )

    # Enforce one indicator family at a time. This avoids stacked overlays hiding the candles.
    tech_overlays: list[str] = []
    tech_lower_indicator = 'No indicator pane'
    tech_show_levels = tech_indicator_choice == 'Support and Resistance'
    tech_show_fibonacci = tech_indicator_choice == 'Fibonacci Retracement'
    if tech_indicator_choice.startswith("MA |"):
        tech_overlays = ["MA5 / MA20"]
    elif tech_indicator_choice.startswith("EMA |"):
        tech_overlays = ["EMA12 / EMA26"]
    elif tech_indicator_choice == 'Bollinger Bands (20, 2)':
        tech_overlays = ['Bollinger Bands (20, 2)']
    elif tech_indicator_choice == 'RSI(14)':
        tech_lower_indicator = "RSI"
    elif tech_indicator_choice == 'MACD(12, 26, 9)':
        tech_lower_indicator = "MACD"
    elif tech_indicator_choice == 'Stochastic':
        tech_lower_indicator = 'Stochastic'
    elif tech_indicator_choice == 'ADX (trend strength)':
        tech_lower_indicator = 'ADX (trend strength)'
    elif tech_indicator_choice == 'OBV (On Balance Volume)':
        tech_lower_indicator = 'OBV (On Balance Volume)'

    # Calculate indicators on a longer history, then display only the requested range.
    tech_raw, tech_error = safe_prices([tech_symbol], "10y")
    show_data_warning(tech_error)
    tech_history = tech_raw.loc[tech_raw["ticker"] == tech_symbol].sort_values("date").copy() if not tech_raw.empty else pd.DataFrame()
    if not tech_history.empty:
        tech_history_frame = calculate_technical_indicators(tech_history)
        period_months = {"1mo": 1, "3mo": 3, "6mo": 6, "1y": 12}
        available_end = pd.Timestamp(tech_history_frame["date"].max())
        display_start = available_end - pd.DateOffset(months=period_months[tech_period])
        tech_frame = tech_history_frame.loc[pd.to_datetime(tech_history_frame["date"]) >= display_start].copy().reset_index(drop=True)
        # OBV's absolute origin is arbitrary; rebase it to the visible range.
        if not tech_frame.empty:
            tech_frame["obv"] = tech_frame["obv"] - float(tech_frame["obv"].iloc[0])
        if not tech_frame.empty:
            chart_height = 600 if tech_lower_indicator != 'No indicator pane' else 440
            tech_fig = technical_indicator_figure(
                tech_frame, tech_overlays, tech_lower_indicator,
                show_levels=tech_show_levels, show_fibonacci=tech_show_fibonacci,
                height=chart_height,
            )
            # Standard Streamlit Plotly rendering avoids custom iframe click/state bugs.
            st.plotly_chart(
                tech_fig, width="stretch", key="tech_indicator_chart",
                config={"displaylogo": False, "scrollZoom": False, "doubleClick": "reset"},
            )
            st.caption(
                f"Data: {tech_symbol} · {TICKERS.get(tech_symbol, tech_symbol)}|{PERIODS[tech_period]}|{pd.Timestamp(tech_frame['date'].min()):%Y-%m-%d} to {pd.Timestamp(tech_frame['date'].max()):%Y-%m-%d}. Source: Yahoo Finance adjusted daily data."
            )
            if tech_show_levels or tech_show_fibonacci:
                extrema = technical_range_extrema(tech_frame)
                if extrema and len(extrema["data"]) >= 5:
                    low_row = extrema["low_row"]
                    high_row = extrema["high_row"]
                    range_summary = (
                        f"Current reference range: {pd.Timestamp(extrema['data']['date'].iloc[0]):%Y-%m-%d} to {pd.Timestamp(extrema['data']['date'].iloc[-1]):%Y-%m-%d}. Range low ${float(low_row['low']):,.2f}({pd.Timestamp(low_row['date']):%Y-%m-%d}); range high ${float(high_row['high']):,.2f}({pd.Timestamp(high_row['date']):%Y-%m-%d})。"
                    )
                    if tech_show_fibonacci and int(extrema["low_pos"]) == int(extrema["high_pos"]):
                        range_summary += 'The highest and lowest prices occur in the same candle, so the swing direction is unclear. Try a shorter history range to draw Fibonacci levels.'
                    elif tech_show_fibonacci:
                        range_summary += "These Fibonacci levels follow the order of the range's extreme prices and are teaching examples."
                    range_summary += 'The app has not identified a confirmed swing or supply/demand zone. These lines are reference levels, not guaranteed turning points or trade instructions.'
                    st.info(range_summary)
                else:
                    st.info('Fewer than 5 valid candles are available, so this reference cannot be drawn reliably.')
        else:
            st.info('No data is available for this range. Try another range or check the data connection.')
    else:
        st.info('No history is available right now. Check your connection and refresh, or continue with the lesson below.')

    # The explanation is directly below the chart and follows the single selected indicator.
    with st.container(border=True):
        if tech_indicator_choice == 'Fibonacci Retracement':
            content_heading('Fibonacci Retracement | Divide a price move into reference levels')
            st.markdown(escape_markdown_dollars("""
**What is Fibonacci Retracement?** After a rise or fall, price may move back part of the way. Retracement lines mark commonly watched proportions of that earlier move.

| Level | Plain meaning | After a move from $100 to $150 |
|---|---|---:|
| 23.6% | Shallow pullback | $138.20 |
| 38.2% | Modest pullback | $130.90 |
| 50.0% | Halfway back | $125.00 |
| 61.8% | Often watched | $119.10 |
| 78.6% | Deep pullback | $110.70 |

**How to explore it:** Identify a clear low and high in the same swing. Choose whether you are studying a pullback after a rise or a rebound after a fall. Near a level, look for additional clues in candles, volume and earlier support or resistance.

**Where do these lines come from?** This lab uses the highest and lowest prices in your selected history range. It does not automatically choose the best local swing. Changing the range changes the endpoints and reference prices.

**Remember:** The 50% level is a common midpoint reference, not a ratio of adjacent Fibonacci numbers. None of these levels guarantees a reversal. Watch what price actually does around them.
"""))

        else:
            render_technical_indicator_lesson(tech_indicator_choice)

    with st.expander('Indicator groups | Ask a question, then choose a tool', expanded=False):
        map_cols = st.columns(4, gap="small")
        map_cards = [
            ("🧭", 'Trend and trend strength', "MA / EMA、ADX", 'Which way is the average price moving? Is a stronger trend developing?'),
            ("⚡", 'Momentum', 'RSI, MACD, Stochastic', 'How is the strength or recent position of price changing?'),
            ("〰️", 'Volatility', 'Bollinger Bands', 'Is the recent price range widening or narrowing?'),
            ("📊", 'Price and volume', "OBV", 'Does the direction of cumulative volume agree with price?'),
        ]
        for col, (icon_text, title_text, tags_text, body_text) in zip(map_cols, map_cards):
            with col:
                info_card(icon_text, title_text, body_text, tags_text)
    section_heading("A REPEATABLE METHOD", 'A repeatable chart-reading routine', 'Use the same order each time: describe the evidence, suggest an explanation, then look for opposing evidence and risks.')
    flow_cols = st.columns(4, gap="medium")
    flow_steps = [
        ("01", 'Location and trend', 'Start with price structure and SMA / EMA direction. A fresh crossover alone is not enough.'),
        ("02", 'Momentum', 'Next inspect RSI, MACD or Stochastic. Their information overlaps, so you do not need all three.'),
        ("03", 'Volatility and volume', 'Use Bollinger Bands for changes in volatility, and volume / OBV for price-volume clues.'),
        ("04", 'Check the opposite case and manage risk', 'Review support, resistance, events and what would invalidate your idea. Look for opposing evidence.'),
    ]
    for col, (number, title_text, body_text) in zip(flow_cols, flow_steps):
        with col:
            st.markdown(
                f'<div class="cycle-card"><div class="cycle-num">{number}</div><div class="cycle-title">{title_text}</div><div class="cycle-body">{body_text}</div></div>',
                unsafe_allow_html=True,
            )

    section_heading("KNOWLEDGE CHECK", 'Chapter check | Understand, then explain', 'Get at least 6 correct to pass. Submit to see answers and explanations. You can retry.')
    tech_questions = [
        ('What is a careful reading when SMA 5 crosses above SMA 20?', ['The short-term average has strengthened relative to the longer-term average; the signal may lag or fail in a sideways market.', 'The stock must rise for the next 20 days.', 'Volume must increase at the same time.'], 0, 'A crossover describes a relationship between past average prices. Check the trend, location and risks; it does not guarantee direction.'),
        ('What is a reasonable reading when RSI is above 70?', ['The stock must fall on the next candle.', 'Recent upward momentum is relatively strong; RSI may be in the commonly called overbought zone, but can stay high in a strong trend.', 'The company is cheaper than its peers.'], 1, '70 is a common reference, not a certain reversal level. RSI describes price momentum, not company value.'),
        ('Where do the MACD line and Signal line mainly come from?', ['Company revenue and net income.', 'Volume and shares outstanding.', 'Exponential moving averages of different lengths and a smoothed result.'], 2, 'The MACD line is EMA 12 minus EMA 26. The Signal line is usually its 9-period EMA. Both use past prices.'),
        ('What does a clear narrowing of Bollinger Bands describe?', ['An upward breakout must happen immediately.', 'Recent price volatility has become smaller; the direction of any later expansion is unknown.', 'The stock is proven to be undervalued.'], 1, 'Narrow bands describe volatility. They do not choose breakout direction. Check later price action and context.'),
        ('How does Stochastic differ from RSI?', ['Stochastic locates the close within a recent high-low range; RSI compares the relative size of recent gains and losses.', 'Stochastic uses only profit; RSI uses only volume.', 'Both can predict the exact reversal date.'], 0, 'Both are momentum oscillators, but use different calculations. Their signals may overlap.'),
        ('What is a reasonable reading when ADX is above 25?', ['The trend must be upward because ADX rises only in rising markets.', 'The trend may be stronger, but ADX alone does not show direction.', 'RSI must already be above 70.'], 1, 'ADX measures trend strength. +DI and −DI provide directional comparisons. 20 / 25 are common guidelines, not fixed rules.'),
        ('What should you do if price rises but OBV does not?', ['Assume price must fall and sell immediately.', 'Ignore volume because it is never useful.', 'Treat the disagreement as a clue; check price structure, unusual volume and later action.'], 2, 'OBV divergence or lack of confirmation deserves investigation. It does not prove a reversal.'),
        ('Why avoid treating all indicators as independent confirmations?', ['Some use the same prices, so their information overlaps; sensitive tools may also produce more false signals.', 'More indicators must mean better statistical accuracy.', 'Indicators work only for options, not stocks.'], 0, 'Know what each tool measures, avoid counting the same evidence twice, and seek opposing evidence.'),
    ]
    with st.form("technical_indicator_quiz_form"):
        tech_answers = []
        for qi, (question, options, correct_idx, explanation) in enumerate(tech_questions):
            tech_answers.append(st.radio(f"{qi + 1}. {question}", options, index=None, key=f"technical_indicator_quiz_{qi}"))
        tech_submit = st.form_submit_button('Submit chapter answers', width="stretch")
    if tech_submit:
        if any(answer is None for answer in tech_answers):
            st.warning(f'There are {sum((answer is None for answer in tech_answers))} unanswered questions. Answer all of them before submitting.')
        else:
            score = sum(answer == q[1][q[2]] for answer, q in zip(tech_answers, tech_questions))
            passed = score >= 6
            record_quiz_attempt('Technical Indicators', passed)
            st.session_state["tech_indicator_quiz_result"] = {"score": score, "passed": passed, "answers": tech_answers}
    tech_result = st.session_state.get("tech_indicator_quiz_result")
    if tech_result:
        if tech_result["passed"]:
            st.success(f"You answered {tech_result['score']}/{len(tech_questions)} correctly and passed this chapter.")
        else:
            st.warning(f"You answered {tech_result['score']}/{len(tech_questions)} correctly. Read the explanations and try again. Any earlier pass stays recorded.")
        for qi, (question, options, correct_idx, explanation) in enumerate(tech_questions):
            selected_answer = tech_result["answers"][qi]
            with st.expander(f"{('✓' if selected_answer == options[correct_idx] else '↻')} Question {qi + 1} explanation"):
                st.markdown(f'**Correct answer:** {options[correct_idx]}\n\n{explanation}')

    lesson_completion_button('Technical Indicators', "finish_technical_indicators")


# ============================================================
# Lesson 3: How a trade works
# ============================================================
elif chosen_page == '03 How Orders Work':
    hero('Lesson 03 | How Does a Stock Trade Happen?', 'Follow a trade from choosing a security to checking the fill. Explore brokers, quotes, order types, costs and records. These are simulations, with no broker connection.', "LESSON 03 · HOW TRADING WORKS")
    section_heading("THE WORKFLOW", 'The 6 basic steps of a trade')
    workflow = [
        ("01", 'Make a plan', 'Clarify your goal, time horizon, affordable loss and whether you need this money for everyday expenses.'),
        ("02", 'Research the security', 'Understand the business or product, asset type, risks, fees and reliable sources. Do not rely only on stock tips.'),
        ("03", 'Check the broker and account', "Verify the broker's regulatory status, fees, client-asset arrangements, account currency and local rules."),
        ("04", 'Choose the order', 'Check the symbol, buy or sell direction, quantity, order type, price conditions and duration.'),
        ("05", 'Review before submitting', 'Check the estimated amount, bid-ask spread, fees and order summary. This practice submits no real orders.'),
        ("06", 'Check fills and records', 'An order may fill fully, fill partly, remain unfilled, be rejected or be canceled. Check price, quantity, fees and statements after a fill.'),
    ]
    for num, title, body in workflow:
        st.markdown(f'<div class="step-line"><div class="step-num">{num}</div><div class="step-body"><b>{title}</b><br>{body}</div></div>', unsafe_allow_html=True)

    section_heading("ORDER TYPES", 'How do three common order types differ?')
    order_tabs = st.tabs([t('Market order'), t('Limit order'), t('Stop order')])
    with order_tabs[0]:
        st.markdown("""
A **market order** aims to buy or sell promptly at the best available market price. It puts more emphasis on execution than on a fixed price.

**Remember:** The last traded price is not a promised fill price. Prices can move before execution, and a less liquid market may fill parts of an order at different prices.
""")
    with order_tabs[1]:
        st.markdown("""
A **limit order** sets the highest price you will pay to buy or the lowest price you will accept to sell.

- A buy limit order can fill at the limit or lower, but may never fill.
- A sell limit order can fill at the limit or higher, but may never fill either.

Controlling price does not guarantee execution.
""")
    with order_tabs[2]:
        st.markdown("""
A **stop order** usually becomes a market order when its trigger condition is met. The actual fill can differ from the stop price.

Some brokers offer **stop-limit orders**, which may remain unfilled in a fast market. Names, triggers and availability depend on the broker's rules.
""")

    section_heading("ACCOUNT BASICS", 'Cash accounts, margin accounts and fractional shares')
    ac1, ac2, ac3 = st.columns(3)
    with ac1:
        info_card("💵", 'Cash account', "Purchases generally use available account funds. Understand settlement, when cash is available and your broker's rules.", 'Account basics')
    with ac2:
        info_card("⚠️", 'Margin account', 'May allow borrowing from a broker or leveraged exposure. Interest, maintenance requirements, margin calls and forced sales can apply.', 'More complex')
    with ac3:
        info_card("🧩", 'Fractional shares', 'Some brokers let you buy less than one share. Not all securities or order types qualify; transfers, voting and execution can differ.', 'Check broker terms')

    section_heading("TRY IT", 'Practice quote | Execution or price control?', 'These are fictional teaching prices, not current quotes for any security.')
    bid_col, ask_col, last_col = st.columns(3)
    bid_col.metric('Best bid', "$99.95")
    ask_col.metric('Best ask', "$100.05")
    last_col.metric('Last traded price', "$100.00")
    st.markdown(escape_markdown_dollars('<div class="callout">Bid-ask spread = best ask − best bid = $0.10. The spread is one trading cost. Quotes can change, and execution also depends on available liquidity and the order queue.</div>'), unsafe_allow_html=True)
    order_choice = st.radio('You want to buy 10 shares. What matters most?', [
        'Fill promptly, accepting that the price may change: a market order fits this aim',
        'Pay $99.90 or less: consider a buy limit order, which may not fill',
        'Any order can guarantee a fill at $100.00',
    ], key="order_type_practice")
    if st.button('Check the order exercise', key="order_type_submit"):
        passed = order_choice.startswith('Fill promptly') or order_choice.startswith('Pay $99.90')
        record_quiz_attempt('How Orders Work', passed)
        if passed:
            st.success('Correct: Order types involve different tradeoffs between price control and execution. Your aim, market conditions and broker rules matter.')
            st.session_state["order_practice_passed"] = True
        else:
            st.error('No common order guarantees the last traded price in all conditions. A market order has an uncertain price; a limit order may not fill.')
    with st.expander('More details to understand before trading'):
        st.markdown("""
- **Quantity:** Whole shares, fractional shares and minimum order sizes depend on the security and broker.
- **Time in force:** Day orders, Good-Till-Canceled and other choices depend on broker support.
- **Trading sessions:** Outside regular hours, liquidity may be lower, spreads wider and price movements larger. Some order types are restricted. Exchange hours and holiday schedules vary.
- **Costs:** Check commissions, spreads, trading or regulatory fees, currency conversion, fund expenses and applicable taxes. Costs vary by place, product and broker.
- **Settlement:** A trade executing and the cash/securities settling are different events. Check the market, product and broker's settlement rules.
- **Advanced trading:** Margin, short selling, options and leveraged products add mechanisms and risks. First understand ordinary cash purchases and sales.
""")
    st.markdown('<div class="warning-callout">This page does not connect to a broker or place real orders. For actual order choices, execution rules and fees, use your regulated broker’s current documents.</div>', unsafe_allow_html=True)
    lesson_completion_button('How Orders Work', "finish_trade_mechanics")


# ============================================================
# Lesson 4: Research a company — interactive beginner version
# ============================================================
elif chosen_page == '04 Researching a Company':
    hero(
        'Lesson 04 | Research a Company Like a Detective',
        'Start with three financial statements: Is the company profitable? Is cash coming in? What does it own and owe?',
        "LESSON 04 · COMPANY RESEARCH LAB",
    )
    st.markdown('**Start with a business question, then find financial evidence.**')
    st.write('Use fictional Orange Grove Drinks to explore statements, ratios and case studies, then apply the method to a real company.')

    # Use a stateful selector instead of st.tabs here. The chart controls below
    # trigger reruns; a keyed widget guarantees the selected lesson section persists.
    lesson_section = st.radio(
        'In this lesson',
        ['01 · Financial Statements', '02 · Ratio Translator', '03 · Company Detective', '04 · Research a Real Company'],
        key="company_research_section",
        horizontal=True,
        label_visibility="collapsed",
    )

    # --- Tab 2: statements as three different views ---
    if lesson_section == '01 · Financial Statements':
        section_heading("THREE STATEMENTS · ONE STORY", 'Three statements answer three different questions', 'The Income statement covers profit over a period. The Balance sheet shows assets, liabilities and equity on a reporting date. The Cash flow statement tracks cash over a period. All examples use Orange Grove Drinks.')
        content_heading('Choose a statement')
        st.markdown('Look at the chart first, then follow the calculations and questions.')
        statement_cards = [
            {"prefix": "①", "label": 'Income statement', "question": 'How much did it earn during the period?', "copy": 'Start with revenue and subtract direct costs, operating expenses, interest and taxes to understand gross profit, operating income and net income.', "value": '① Income statement'},
            {"prefix": "②", "label": 'Balance sheet', "question": 'What does it own and owe now?', "copy": 'Compare cash, receivables, inventory and equipment with liabilities and equity to understand financial position.', "value": '② Balance sheet'},
            {"prefix": "③", "label": 'Cash flow statement', "question": 'How did cash actually move?', "copy": 'Separate operating, investing and financing cash flows. Was cash generated by the business, spent on expansion or raised through funding?', "value": '③ Cash flow statement'},
        ]
        statement_mode = st.session_state.get("company_statement_choice", '① Income statement')
        nav_cols = st.columns(3, gap="medium")
        for i, card in enumerate(statement_cards):
            active = statement_mode == card["value"]
            with nav_cols[i]:
                active_class = " is-active" if active else ""
                st.markdown(
                    f'<div class="statement-nav-card{active_class}"><div class="statement-nav-number">FINANCIAL STATEMENT {card["prefix"]}</div><div class="statement-nav-title">{card["label"]}</div><div class="statement-nav-question">{card["question"]}</div><div class="statement-nav-copy">{card["copy"]}</div></div>',
                    unsafe_allow_html=True,
                )
                button_label = '✓ Currently viewing' if active else 'View chart + walkthrough →'
                st.button(
                    button_label,
                    key=f"statement_nav_{i}",
                    width="stretch",
                    on_click=choose_company_statement,
                    args=(card["value"],),
                )
        statement_mode = st.session_state.get("company_statement_choice", '① Income statement')
        st.caption('Orange Grove Drinks is fictional. Amounts are in USD and simplified to explain statements and calculations.')
        if statement_mode.startswith('① Income statement'):
            income_fig = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute", "relative", "total", "relative", "total", "relative", "total"],
                x=['Revenue', 'Direct costs', 'Gross profit', 'Operating expenses', 'Operating income', 'Interest and taxes', 'Net income'],
                y=[10000, -4000, 6000, -4000, 2000, -500, 1500],
                customdata=[["$10,000"], ["−$4,000"], ["$6,000"], ["−$4,000"], ["$2,000"], ["−$500"], ["$1,500"]],
                hovertemplate='<b>%{x}</b><br>Amount: %{customdata[0]}<extra></extra>',
                connector={"line": {"color": "#71849d", "width": 1.2}},
                increasing={"marker": {"color": "#059669"}},
                decreasing={"marker": {"color": "#ef4444"}},
                totals={"marker": {"color": "#2563eb"}},
            ))
            content_heading('Orange Grove Drinks · Profit bridge')
            style_fig(income_fig, 455)
            income_fig.update_layout(
                showlegend=False, title=None,
                yaxis_title='Amount (USD)', yaxis=dict(tickformat="$,.0f", rangemode="tozero", tickfont=dict(size=12)),
                # Angled category labels reduce collisions on phone-sized viewports.
                xaxis=dict(tickangle=-25, tickfont=dict(size=12), automargin=True),
                margin=dict(l=28, r=24, t=24, b=104), waterfallgap=0.28,
            )
            st.plotly_chart(income_fig, width="stretch", key="income_statement_waterfall")
            st.caption('Items run across the bottom; amounts run up the side. Costs reduce the previous total. Subtotals show what remains. Hover over a bar to check its value.')

            content_heading('Read the Income statement step by step', level="h3")
            st.markdown('**Revenue is the starting point.** Follow sales down through costs and expenses to profit. This chart shows accounting profit for a reporting period. Cash on hand, debt and whether a stock is attractively priced require other evidence.')
            income_steps = [
                ('Step 1 | Revenue $10,000', "Customers' drink and snack purchases create $10,000 of sales. Making products, paying staff and running stores still cost money. For a real company, ask whether growth came from more sales, higher prices, acquisitions or currency changes, and check how revenue is recognized."),
                ('Step 2 | Subtract direct costs of $4,000 → gross profit $6,000', 'Direct costs relate to providing the product: fruit, ingredients, cups and food in this example. $10,000 − $4,000 = $6,000. Gross margin = $6,000 ÷ $10,000 = 60%. Each $1 of sales leaves $0.60 after direct costs to cover other expenses and profit.'),
                ('Step 3 | Subtract operating expenses of $4,000 → operating income $2,000', "Operating expenses may include rent, administration, marketing, utilities and software. $6,000 − $4,000 = $2,000, a 20% operating margin. This shows profit after direct and operating costs. Real companies' classifications vary by industry and accounting policy."),
                ('Step 4 | Subtract interest and taxes of $500 → net income $1,500', 'Interest, income tax and related items total $500 here. Net income = $2,000 − $500 = $1,500. Net margin = $1,500 ÷ $10,000 = 15%: $0.15 of accounting profit per $1 of sales. Cash received can differ.'),
            ]
            for step_title, step_copy in income_steps:
                st.markdown(escape_markdown_dollars(f"**{step_title}**\n\n{step_copy}"))
            st.markdown(escape_markdown_dollars('Results: gross profit $6,000 (60% gross margin); operating income $2,000 (20% operating margin); net income $1,500 (15% net margin). Each margin represents a different stage of cost deductions.'))
            content_heading('What should you ask next?', level="h3")
            st.markdown("""- **Are margins improving?** Compare several quarters or years. Are costs growing faster than revenue?
- **Can growth continue?** Separate more sales, price increases and one-time effects. Read management discussion, segment data and notes.
- **Did profit become cash?** Accrual accounting can record a credit sale before the customer pays. Compare the Cash flow statement.""")
            st.markdown('Net income covers a specified period. Use the Balance sheet for cash balances and debt, the Cash flow statement for cash movements, and growth, risk and market prices when studying valuation.')
        elif statement_mode.startswith('② Balance sheet'):
            balance_df = pd.DataFrame({
                'Item': ['Cash', 'Accounts receivable', 'Inventory', 'Equipment and other assets', 'Accounts payable', 'Short-term debt', 'Long-term debt', "Shareholders' equity"],
                'Amount (USD)': [1800, 2200, 1800, 6500, 1800, 1500, 4000, 5000],
            })
            # Distinguish what the company owns from what it owes; equity is shown separately.
            balance_colors = ["#059669"] * 4 + ["#ef4444"] * 3 + ["#2563eb"]
            balance = go.Figure(go.Bar(
                x=balance_df['Amount (USD)'], y=balance_df['Item'], orientation="h",
                marker_color=balance_colors, text=[f"${v:,.0f}" for v in balance_df['Amount (USD)']],
                textposition="outside", cliponaxis=False,
                hovertemplate='<b>%{y}</b><br>Amount: $%{x:,.0f}<extra></extra>',
            ))
            content_heading('Orange Grove Drinks · Assets and funding')
            style_fig(balance, 455)
            balance.update_layout(
                title=None,
                xaxis_title='Amount (USD)', xaxis=dict(tickformat="$,.0f", range=[0, 7900], automargin=True, tickfont=dict(size=12)),
                yaxis=dict(title="", autorange="reversed", tickfont=dict(size=13), automargin=True),
                showlegend=False, margin=dict(l=36, r=112, t=24, b=38), bargap=0.3,
            )
            st.plotly_chart(balance, width="stretch", key="balance_sheet_components")
            st.caption('Green bars show assets; red bars show liabilities; blue shows equity. A longer horizontal bar means a larger amount.')
            st.markdown(escape_markdown_dollars('Assets $12,300 = liabilities $7,300 + equity $5,000'))

            content_heading('Read the Balance sheet step by step', level="h3")
            st.markdown("**Think of a photograph taken on one date.** The Balance sheet shows what a company controls, what it owes and the owners' remaining book equity on the reporting date. These balances do not represent a whole year's earnings.")
            st.markdown(escape_markdown_dollars("**Step 1 | Assets: What resources does it control?** Total assets of $12,300 include cash $1,800, receivables $2,200, inventory $1,800, and equipment and other assets $6,500. Cash pays bills directly. Receivables await customers' payments and carry collection risk. Inventory must sell and can expire, break or need discounts. Equipment supports operations but is harder to turn into cash. Assets differ in liquidity and risk."))
            st.markdown(escape_markdown_dollars('**Step 2 | Liabilities: What obligations must it meet?** Accounts payable $1,800, short-term debt $1,500 and long-term debt $4,000 total $7,300. Payables usually await payment to suppliers. Short-term debt falls due sooner; long-term debt still requires interest and repayment. For real companies, inspect cash, due dates, rates, interest expense and the ability to generate cash.'))
            st.markdown(escape_markdown_dollars('**Step 3 | Equity $5,000:** Assets − liabilities = equity: $12,300 − $7,300 = $5,000. This is accounting book equity. Cash balance and stock market capitalization are different measures. Market capitalization is share price × shares outstanding.'))
            content_heading('Three areas to investigate', level="h3")
            st.markdown("""- **Short-term payments:** Compare cash and current assets with upcoming obligations.
- **Working capital quality:** Compare receivables and inventory with revenue over several years.
- **Debt pressure:** Check rates, maturity dates and whether operating cash flow supports repayment.""")
        else:
            cash_flow = pd.DataFrame({'Activity': ['Cash from operating activities', 'Cash from investing activities', 'Cash from financing activities', 'Net change in cash'], 'Cash flow (USD)': [900, -1500, 1000, 400]})
            cf_colors = ["#059669" if v >= 0 else "#ef4444" for v in cash_flow['Cash flow (USD)']]
            cf_colors[-1] = "#2563eb"  # Net change / ending cash summary is a distinct total color.
            cf_fig = go.Figure(go.Bar(
                x=cash_flow['Cash flow (USD)'], y=cash_flow['Activity'], orientation="h",
                marker_color=cf_colors, text=[f"${v:+,.0f}" for v in cash_flow['Cash flow (USD)']],
                textposition="outside", cliponaxis=False,
                hovertemplate='<b>%{y}</b><br>Cash flow: $%{x:,.0f}<extra></extra>',
            ))
            content_heading('Orange Grove Drinks · Cash movements')
            style_fig(cf_fig, 430)
            cf_fig.update_layout(
                title=None,
                xaxis_title='Cash flow (USD)', xaxis=dict(tickformat="$,.0f", zeroline=True, zerolinecolor="#aabbd0", range=[-2050, 1550], tickfont=dict(size=12)),
                yaxis_title="", yaxis=dict(autorange="reversed", tickfont=dict(size=13), automargin=True),
                showlegend=False, margin=dict(l=42, r=112, t=24, b=38), bargap=0.32,
            )
            st.plotly_chart(cf_fig, width="stretch", key="cashflow_statement_bars")
            st.caption('Green shows cash coming in; red shows cash going out. Blue marks the total net change. Right of zero means inflow; left means outflow.')
            st.markdown(escape_markdown_dollars('Net change in cash = $900 − $1,500 + $1,000 = +$400'))

            content_heading('Read the Cash flow statement step by step', level="h3")
            st.markdown('**Profit and cash answer different questions.** Accounting can recognize revenue before payment and expenses before cash leaves. The Cash flow statement follows actual cash movements, helping show whether operations bring in cash and where it goes.')
            st.markdown(escape_markdown_dollars('**Step 1 | Operating cash flow +$900:** Cash collected from customers minus payments to suppliers, staff, landlords and taxes leaves $900. Compare it with net income and several years of data to study cash generation.'))
            st.markdown(escape_markdown_dollars('**Step 2 | Investing cash flow −$1,500:** Investing includes equipment, store improvements, acquisitions and investment assets. This example has a $1,500 net outflow. Check the detail to see where it went, then track later revenue, profit and cash flow.'))
            st.markdown(escape_markdown_dollars('**Step 3 | Financing cash flow +$1,000:** Financing includes borrowing, debt repayment, share issuance and dividends. This $1,000 inflow could have different effects: borrowing adds repayment obligations; issuing shares can dilute existing owners.'))
            st.markdown(escape_markdown_dollars('**Step 4 | Net cash increase $400:** To find closing cash, start with opening cash and include other statement items, such as exchange-rate effects.'))
            content_heading('Four areas to investigate', level="h3")
            st.markdown("""- **Operating cash trends:** Review several years and seasonal effects.
- **Profit versus cash:** Check receivables, inventory, payables and depreciation.
- **Investment spending:** Identify equipment spending, acquisitions and other investments.
- **Funding sources:** Distinguish operating cash, asset sales, borrowing and share issuance.""")
        content_heading('Connect the three statements')
        st.markdown("""- **Income statement:** Revenue, costs, expenses and profit over a period.
- **Balance sheet:** Assets, liabilities and equity on a reporting date.
- **Cash flow statement:** Where cash came from and went during a period.

Read them together. Receivables, inventory, depreciation, capital expenditures and financing link profit, financial position and cash movements.""")

    # --- Tab 3: Metric translator with editable inputs ---
    elif lesson_section == '02 · Ratio Translator':
        section_heading("METRIC TRANSLATOR", 'Translate financial terms into everyday questions', 'Ask what the measure answers, then look at the formula. Choose a measure and change the example numbers to see the result.')
        metric_options = ['Revenue growth', 'Gross margin', 'Net margin', 'Earnings per share (EPS)', 'Price to earnings ratio (P/E)', 'Interest-bearing debt / equity', 'Operating cash flow / net income', 'Free cash flow (FCF)']
        metric_choice = st.selectbox('Which measure would you like to explore?', metric_options, key="company_metric_translator")
        mleft, mright = st.columns([1, 1], gap="large")
        with mleft:
            st.markdown('**Change the example numbers**')
            if metric_choice == 'Revenue growth':
                old_value = st.number_input('Previous-period revenue (USD)', min_value=1.0, value=8000.0, step=500.0, key="metric_rev_old")
                new_value = st.number_input('Current-period revenue (USD)', min_value=0.0, value=10000.0, step=500.0, key="metric_rev_new")
                metric_result = (new_value / old_value - 1) * 100 if old_value > 0 else np.nan
                result_text = f"{metric_result:+.1f}%" if pd.notna(metric_result) else 'Cannot calculate'
                formula = '(Current revenue − previous revenue) ÷ previous revenue × 100%'
                example = f'(${new_value:,.0f} − ${old_value:,.0f})÷ ${old_value:,.0f} = {result_text}'
            elif metric_choice == 'Gross margin':
                revenue = st.number_input('Revenue (USD)', min_value=1.0, value=10000.0, step=500.0, key="metric_gm_rev")
                cogs = st.number_input('Direct costs (USD)', min_value=0.0, value=4000.0, step=250.0, key="metric_gm_cogs")
                metric_result = (revenue - cogs) / revenue * 100
                result_text = f"{metric_result:.1f}%"
                formula = '(Revenue − direct costs) ÷ revenue × 100%'
                example = f'(${revenue:,.0f} − ${cogs:,.0f})÷ ${revenue:,.0f} = {result_text}'
            elif metric_choice == 'Net margin':
                revenue = st.number_input('Revenue (USD)', min_value=1.0, value=10000.0, step=500.0, key="metric_nm_rev")
                net_income = st.number_input('Net income (USD)', value=1500.0, step=250.0, key="metric_nm_ni")
                metric_result = net_income / revenue * 100
                result_text = f"{metric_result:.1f}%"
                formula = 'Net income ÷ revenue × 100%'
                example = f"${net_income:,.0f} ÷ ${revenue:,.0f} = {result_text}"
            elif metric_choice == 'Earnings per share (EPS)':
                net_income = st.number_input('Net income attributable to common shareholders (USD)', min_value=-100000000.0, value=1500.0, step=250.0, key="metric_eps_ni")
                shares = st.number_input('Weighted average common shares (example)', min_value=1.0, value=1000.0, step=100.0, key="metric_eps_shares")
                metric_result = net_income / shares
                result_text = f'${metric_result:,.2f}/share'
                formula = 'Net income attributable to common shareholders ÷ weighted average common shares'
                example = f'${net_income:,.0f} ÷ {shares:,.0f} shares = {result_text}'
            elif metric_choice == 'Price to earnings ratio (P/E)':
                price = st.number_input('Current share price (USD)', min_value=0.01, value=30.0, step=1.0, key="metric_pe_price")
                eps = st.number_input('Earnings per share (USD)', value=1.5, step=0.25, key="metric_pe_eps")
                metric_result = price / eps if eps > 0 else np.nan
                result_text = f'{metric_result:.1f}×' if pd.notna(metric_result) else 'Zero or negative earnings: simple P/E not applicable'
                formula = 'Share price ÷ EPS (check the earnings period and definition)'
                example = f"${price:,.2f} ÷ ${eps:,.2f} = {result_text}" if eps > 0 else 'When EPS ≤ 0, ordinary P/E is generally unsuitable for direct comparisons.'
            elif metric_choice == 'Interest-bearing debt / equity':
                debt = st.number_input('Short-term + long-term debt (USD)', min_value=0.0, value=5500.0, step=500.0, key="metric_debt")
                equity = st.number_input("Shareholders' equity (USD)", min_value=-100000000.0, value=5000.0, step=500.0, key="metric_equity")
                metric_result = debt / equity if equity > 0 else np.nan
                result_text = f'{metric_result:.2f}×' if pd.notna(metric_result) else 'Zero or negative equity: interpret with care'
                formula = "Interest-bearing debt ÷ shareholders' equity"
                example = f"${debt:,.0f} ÷ ${equity:,.0f} = {result_text}" if equity > 0 else 'With zero or negative equity, a simple multiple may lose its usual meaning.'
            elif metric_choice == 'Operating cash flow / net income':
                cfo = st.number_input('Cash from operating activities (USD)', value=900.0, step=250.0, key="metric_cfo")
                net_income = st.number_input('Net income (USD)', value=1500.0, step=250.0, key="metric_cfo_ni")
                metric_result = cfo / net_income if net_income != 0 else np.nan
                result_text = f'{metric_result:.2f}×' if pd.notna(metric_result) else 'Net income is zero: cannot calculate'
                formula = 'Operating cash flow ÷ net income'
                example = f"${cfo:,.0f} ÷ ${net_income:,.0f} = {result_text}" if net_income != 0 else 'Cannot calculate when net income is zero.'
            else:
                cfo = st.number_input('Cash from operating activities (USD)', value=900.0, step=250.0, key="metric_fcf_cfo")
                capex = st.number_input('Capital expenditures (USD)', min_value=0.0, value=1200.0, step=250.0, key="metric_fcf_capex")
                metric_result = cfo - capex
                result_text = f"${metric_result:,.0f}"
                formula = 'Simplified free cash flow = operating cash flow − capital expenditures'
                example = f"${cfo:,.0f} − ${capex:,.0f} = {result_text}"
        with mright:
            st.markdown(escape_markdown_dollars(f'**{metric_choice}**\n\nFormula: {formula}\n\nExample: {example}'))
            st.markdown(escape_markdown_dollars(f'Current example result: {result_text}'))
            explainers = {
                'Revenue growth': ('Question: Did sales revenue rise or fall compared with the earlier period?', 'Growth can come from volume, price increases, acquisitions or currency changes. Revenue growth does not automatically mean profit or cash growth.', "Check gross margin, net margin, cash flow and management's explanation of growth."),
                'Gross margin': ('How much remains from each $100 of revenue after direct costs?', 'Gross profit still has to cover other research, marketing, administration, interest and tax costs.', "Compare the company's history and peers in the same industry."),
                'Net margin': ('How much accounting net income remains from each $100 of revenue?', 'One-time gains, taxes or accounting estimates may make one period unusually high or low.', 'Check cash flow and whether profit can continue.'),
                'Earnings per share (EPS)': ("Allocate a period's earnings across its weighted average shares.", 'EPS can rise because of share buybacks or changes in share count; total profit may not rise by the same percentage.', 'Check changes in both net income and weighted average shares.'),
                'Price to earnings ratio (P/E)': ('How much market price is being paid for each unit of earnings per share?', 'Low P/E does not guarantee a bargain; high P/E does not prove overvaluation. Growth expectations, risk and accounting definitions matter.', "Compare peers, the company's history, growth prospects and earnings quality."),
                'Interest-bearing debt / equity': ("A rough comparison of interest-bearing borrowing with the owners' book equity.", 'Sources may define debt and equity differently. Banks and insurers require particular care.', 'Check maturities, interest rates, cash and interest coverage.'),
                'Operating cash flow / net income': ('Did accounting earnings turn into operating cash in the same period?', 'A single-period ratio can reflect seasonality, payment timing or working capital changes. It cannot judge quality alone.', 'Review several periods and changes in receivables, inventory and payables.'),
                'Free cash flow (FCF)': ('A simplified measure of operating cash remaining after capital expenditures.', 'Negative free cash flow can reflect expansion or financial pressure. Companies may use different definitions.', 'Check why capital expenditures were needed, operating cash trends, funding needs and debt maturities.'),
            }
            plain, caution, next_evidence = explainers[metric_choice]
            st.markdown(f'**In everyday words:** {plain}')
            st.markdown(f'**Easy mistake:** {caution}')
            st.markdown(f'**Find more evidence:** {next_evidence}')
        with st.expander('Quick review of other common measures'):
            quick_table = pd.DataFrame([
                {'Measure': 'Revenue', 'Question it answers': 'How much did the company sell in goods or services?'},
                {'Measure': 'Gross margin', 'Question it answers': 'What percentage of revenue remains after direct costs?'},
                {'Measure': 'Net income', 'Question it answers': 'What accounting profit remains after costs, expenses, interest and taxes?'},
                {'Measure': "EPS", 'Question it answers': 'How much profit belongs to each weighted average share?'},
                {'Measure': "P/E", 'Question it answers': 'How many times EPS is the current share price?'},
                {'Measure': 'Free cash flow (FCF)', 'Question it answers': 'How much operating cash remains after capital expenditures, in this simplified definition?'},
            ])
            st.dataframe(quick_table, width="stretch", hide_index=True)

    # --- Tab 4: Case-based reasoning, not rote definitions ---
    elif lesson_section == '03 · Company Detective':
        section_heading("CASE INVESTIGATION", 'When numbers disagree, investigate before deciding', 'Real company data often gives mixed signals. Your first job is to find the next useful piece of evidence.')
        st.caption('These are three separate fictional scenarios for Orange Grove Drinks, not facts from the same reporting period.')
        cases = {
            'Case A · Revenue rises, operating cash flow falls': {
                "story": 'Revenue rises 25% and net income rises 10% year over year, but operating cash flow falls 30%. Receivables and inventory both rise sharply.',
                "question": 'What should you investigate next?',
                "options": ['Assume the company is doing well because revenue rose', "Check collections, unsold inventory, cash flow adjustments and management's explanation", "Look only at last week's share price"],
                "correct": 1,
                "answer": 'Check whether cash is tied up in unpaid customer bills or inventory. Read the Cash flow statement, notes and management discussion. Revenue growth starts an investigation.',
            },
            'Case B · P/E is lower than peers': {
                "story": 'Orange Grove Drinks trades at 9× earnings versus a peer median of 18×. Product sales are falling and debt is high.',
                "question": 'Can you immediately call it undervalued?',
                "options": ['Yes: a lower P/E always means a bargain', 'No: check growth prospects, earnings quality, debt risk and reasons for the lower valuation', 'Yes: its share price just needs to be below peers'],
                "correct": 1,
                "answer": 'A low multiple may reflect weak growth expectations, higher risk or unusually high cyclical earnings. Ask why the market pays less for each unit of current earnings.',
            },
            'Case C · EPS rises while total profit barely changes': {
                "story": 'Net income stays roughly flat, but EPS rises 8%. The company also buys back some shares.',
                "question": 'What should you check first?',
                "options": ['Whether weighted average shares fell and how much cash the buyback used', 'Assume the core business grew 8%', 'Stop researching because EPS rose'],
                "correct": 0,
                "answer": 'EPS = relevant net income ÷ weighted average shares. Fewer shares can lift EPS without much total profit growth. Investigate buyback costs, cash flow and business performance.',
            },
        }
        case_name = st.selectbox('Choose a case to investigate', list(cases.keys()), key="company_investigation_case")
        case = cases[case_name]
        # Each case has different answer choices. Clear a stale answer before
        # constructing the radio widget so a previous case's option cannot linger.
        if st.session_state.get("company_case_answer") not in case["options"]:
            st.session_state["company_case_answer"] = case["options"][0]
        st.markdown(f"**{case_name}**")
        st.write(case["story"])
        case_answer = st.radio(case["question"], case["options"], key="company_case_answer")
        if st.button('Submit and review the evidence', key="company_case_submit"):
            passed = case_answer == case["options"][case["correct"]]
            st.session_state["company_case_last"] = {"case": case_name, "passed": passed, "answer": case_answer}
            record_quiz_attempt('Researching a Company', passed)
        last_case_result = st.session_state.get("company_case_last", {})
        if last_case_result.get("case") == case_name:
            if last_case_result.get("passed"):
                st.success('Good reasoning. You chose to gather evidence before drawing a trading conclusion from one number.')
            else:
                st.error('Look again at the conflicting signals and try another answer.')
            st.markdown(f"**Explanation:** {case['answer']}")
        with st.expander('Hint: What does evidence first mean?'):
            st.write('When numbers disagree, seek time series, statement notes, management discussion, industry comparisons and cash flow explanations. Write down what remains unknown.')

    # --- Tab 5: apply framework to real data without pretending all fields are available ---
    elif lesson_section == '04 · Research a Real Company':
        section_heading("APPLY TO A REAL COMPANY", 'Apply the method to a real company', 'Start with official filings. Data summaries can help locate numbers, but do not cover everything.')
        stock_symbols = [s for s in TICKERS.keys() if s not in {"SPY", "QQQ", "EFA", "EEM", "EWJ", "FXI"}]
        real_symbol = st.selectbox(t('Choose a company'), stock_symbols, format_func=ticker_label, key=lang_key("company_real_lookup_symbol"))
        st.markdown('**Start with official filings.** Find US company disclosures through SEC EDGAR on the Data & Methods page.')
        st.caption("Start with the 10-K annual report and 10-Q quarterly report: business description, risk factors, Management's Discussion and Analysis (MD&A), and the three financial statements. Investor Relations pages can help; check filing and announcement dates.")
        if st.button('Try loading a company summary from the data service', key="company_fetch_yahoo_info"):
            with st.spinner('Loading the public company summary; some fields may be missing…'):
                try:
                    raw_info = yf.Ticker(real_symbol).get_info()
                    if not isinstance(raw_info, dict):
                        raw_info = {}
                    st.session_state["company_lookup_cache"] = {"symbol": real_symbol, "info": raw_info, "error": None}
                except Exception as exc:
                    st.session_state["company_lookup_cache"] = {"symbol": real_symbol, "info": {}, "error": str(exc)[:500]}
        lookup = st.session_state.get("company_lookup_cache", {})
        if lookup.get("symbol") == real_symbol:
            if lookup.get("error"):
                st.warning('The company summary is unavailable. You can still use the teaching examples above and verify real data through SEC EDGAR.')
            elif lookup.get("info"):
                raw_info = lookup["info"]
                def _fmt_company_number(value, kind="money"):
                    try:
                        val = float(value)
                        if kind == "pct":
                            return f"{val * 100:.2f}%"
                        if kind == "ratio":
                            return f'{val:.2f}×'
                        if abs(val) >= 1e12:
                            return f"${val / 1e12:.2f}T"
                        if abs(val) >= 1e9:
                            return f"${val / 1e9:.2f}B"
                        if abs(val) >= 1e6:
                            return f"${val / 1e6:.2f}M"
                        return f"${val:,.2f}"
                    except (TypeError, ValueError):
                        return "—"
                profile_rows = [
                    ('Sector', "sector", "text"), ('Industry', "industry", "text"),
                    ('Market capitalization', "marketCap", "money"), ('Total revenue', "totalRevenue", "money"),
                    ('Revenue growth', "revenueGrowth", "pct"), ('Net margin', "profitMargins", "pct"),
                    ('P/E (TTM)', "trailingPE", "ratio"), ('Forward P/E', "forwardPE", "ratio"),
                    ('Operating cash flow', "operatingCashflow", "money"), ('Free cash flow', "freeCashflow", "money"),
                    ('Total debt', "totalDebt", "money"), ('Current ratio', "currentRatio", "ratio"),
                ]
                rows = []
                for label, key, typ in profile_rows:
                    val = raw_info.get(key)
                    if val is None or val == "":
                        continue
                    shown = str(val) if typ == "text" else _fmt_company_number(val, typ)
                    rows.append({'Measure': label, 'Value returned by data service': shown})
                if rows:
                    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
                else:
                    st.info('No company summary fields were returned. Use official filings.')
                st.caption("Definitions and update times may differ. Verify key figures against the company's latest filings.")
                if raw_info.get("website"):
                    website = str(raw_info.get("website"))
                    if website.startswith("https://") or website.startswith("http://"):
                        st.markdown(f'Company website: [{website}]({website})')
        content_heading('Company research checklist')
        checklist_items = [
            'I can explain what the company sells, who its customers are and how it earns money.',
            'I checked revenue and profit across several periods.',
            'I compared the Income statement with operating cash flow.',
            'I checked cash, receivables, inventory, interest-bearing debt and maturities.',
            "I understand the valuation measure's definition and used more than a single multiple.",
            'I read risk factors and management discussion, and recorded open questions.',
        ]
        checklist_cols = st.columns(2)
        checked_count = 0
        for idx, item in enumerate(checklist_items):
            with checklist_cols[idx % 2]:
                if st.checkbox(item, key=f"company_research_check_{idx}"):
                    checked_count += 1
        st.progress(checked_count / len(checklist_items), text=f'Research checklist: {checked_count}/{len(checklist_items)} items')
        content_heading('Write your research conclusion')
        research_note = st.text_area('Use three sentences: What do I know? What must I verify? What is the biggest uncertainty?', key="company_research_note", height=110, placeholder='The company earns money by… Current data shows… I still need to verify…')
        if st.button('Save research notes', key="company_research_save_note"):
            if not research_note.strip():
                st.warning('Write at least one sentence of your own conclusion first.')
            else:
                st.session_state["company_research_saved_note"] = research_note.strip()
                st.success('Saved for this session. You can return later; restarting the app may reset it.')
        if st.session_state.get("company_research_saved_note"):
            with st.expander('View saved research notes'):
                st.write(st.session_state["company_research_saved_note"])

    st.markdown("---")
    st.caption('These example numbers are fictional teaching data.')
    lesson_completion_button('Researching a Company', "finish_company_research")


# ============================================================
# Lesson 4: Why prices move
# ============================================================
elif chosen_page == '05 Why Stock Prices Move':
    hero('Lesson 05 | Why Do Stock Prices Move?', 'Prices reflect current performance, future expectations, funding costs and market sentiment. Explore several possible causes.', "LESSON 05 · WHAT MOVES PRICES")
    factors = [
        ("📈", 'Company performance', 'Revenue, profit, cash flow and guidance change expectations about the business. Results relative to earlier expectations also matter.', 'Company factors'),
        ("🏦", 'Interest rates and inflation', 'Rates affect borrowing costs, the appeal of bonds and valuations of future cash flows. Companies respond differently.', 'Economic conditions'),
        ("🧠", 'Market expectations', 'Prices can already reflect expectations. Earnings may grow and the price still fall if results disappoint.', 'Expectation gap'),
        ("🌍", 'Industry and competition', "Products, competitors, supply chains, policy and technology can change an industry's outlook, with different effects on each company.", 'Industry factors'),
        ("💧", 'Supply, demand and liquidity', 'Buy/sell orders and available trading quantities affect short-term moves. High volume alone does not set direction.', 'Trading conditions'),
        ("⚡", 'Unexpected events and sentiment', 'Geopolitics, regulation, surprise news and changes in risk appetite can move prices quickly. Context helps explain the reaction.', 'Uncertainty'),
    ]
    for i in range(0, len(factors), 3):
        row = st.columns(3)
        for col, f in zip(row, factors[i:i+3]):
            with col:
                info_card(f[0], f[1], f[2], f[3])

    st.write("")
    section_heading("CASE PRACTICE", 'Case study | Why might a stock fall after good earnings?', 'This is a fictional teaching scenario.')
    st.markdown('<div class="lesson-card"><div class="lesson-title">The situation</div><div class="lesson-text">A technology company reports quarterly profit growth of 20%. Analysts had expected 30%, and the company lowers next quarter’s sales guidance.</div></div>', unsafe_allow_html=True)
    case_answer = st.radio('Which explanation makes most sense?', [
        'Profit growth must raise the price, so the market reaction makes no sense',
        'Investors may focus on the missed expectation and weaker future guidance',
        'Higher daily volume proves the price must fall',
    ], key="factor_case")
    if st.button('Review the case', key="factor_submit"):
        passed = case_answer.startswith('Investors may')
        record_quiz_attempt('Why Stock Prices Move', passed)
        if passed:
            st.success('Correct. Markets compare results with earlier expectations. The gap often helps explain a short-term reaction.')
        else:
            st.error('20% growth is the reported result. Investors also compare what they expected and assess the future outlook.')
    with st.expander('Investigate price changes at four levels'):
        st.markdown("""
1. **Company:** Sales, pricing, costs, management, products, competitors, earnings and guidance.
2. **Industry:** Supply/demand, new technology, supply chains, regulation and cycles.
3. **Economy:** Rates, inflation, jobs, growth, currencies and policy.
4. **Market:** Expectations, risk appetite, fund flows, liquidity and valuations.

One event may affect several levels and may already be expected. Record event dates, original sources, price changes and alternative explanations. Avoid selecting only supporting evidence after the fact.
""")
    with st.expander('Fundamental analysis and technical analysis'):
        st.markdown("""
- **Fundamental analysis:** Studies the business, financial statements, competition, management, valuation and external conditions to understand the business and market price.
- **Technical analysis:** Studies prices, volume and indicators for historical patterns. A pattern may not repeat or establish a future direction.
- **Limits:** Expectations may already be reflected in prices; accounting definitions differ; charts contain noise. Neither method guarantees a result.
- **Timing:** Entry price, holding period, costs and investor behavior affect returns even when a longer-term idea seems reasonable.
""")
    st.markdown('**Verify the data:** Compare prices and volume with official filings, announcement dates and economic data for the same period. Sources are collected on Data & Methods.')
    st.markdown('<div class="warning-callout">Build a useful habit: describe what the data shows, then seek evidence for an explanation. One event happening before another does not prove it caused it.</div>', unsafe_allow_html=True)
    lesson_completion_button('Why Stock Prices Move', "finish_factors")


# ============================================================
# ============================================================
# Lesson 6: Risk and investor protection
# ============================================================
elif chosen_page == '06 Risk & Investor Protection':
    hero('Lesson 06 | Risk & Investor Protection', 'Learn to recognize risk, reduce avoidable mistakes and protect your account and judgment.', "LESSON 06 · RISK & INVESTOR PROTECTION")
    section_heading("RISK MAP", 'Six risks every beginner should recognize')
    risks = [
        ("📉", 'Market risk', 'Many securities can fall together in a market decline, even if an individual company has changed little.'),
        ("🏢", 'Company and industry risk', 'Product failures, competition, lawsuits, management problems or industry pressures can affect one company or a whole sector.'),
        ("💧", 'Liquidity risk', 'There may be too few willing counterparties, leading to wider spreads or worse execution prices.'),
        ("💱", 'Currency, inflation and interest-rate risk', "If an asset's currency differs from your spending currency, exchange rates affect your return. Inflation and rates also affect purchasing power and valuations."),
        ("🧺", 'Concentration and correlation', 'Diversification depends on industries, risk sources, correlation and overlapping holdings, as well as the number of symbols.'),
        ("🧠", 'Behavioral and operational risk', 'Chasing rises, panic selling, fear of missing out, overtrading, ignoring fees, doubling down and order mistakes can hurt results.'),
    ]
    risk_cols = st.columns(3)
    for col, item in zip(risk_cols, risks[:3]):
        with col:
            info_card(item[0], item[1], item[2])
    risk_cols2 = st.columns(3)
    for col, item in zip(risk_cols2, risks[3:]):
        with col:
            info_card(item[0], item[1], item[2])

    section_heading("PROTECT YOURSELF", 'Before-investing self-check')
    check_items = [
        'I can explain the investment, its possible returns and how it could lose money.',
        'This money is not needed soon for rent, tuition, daily living or emergencies.',
        'I checked product fees, trading costs, currency conversion and applicable taxes.',
        'I understand my time horizon and ability to absorb losses.',
        'I checked the security, broker/adviser and sources independently.',
        'I can explain my diversification and understand that market risk remains.',
        'I will pause when someone pressures me, promises guaranteed profit or claims inside information.',
    ]
    checks = []
    for idx, label in enumerate(check_items):
        checks.append(st.checkbox(label, key=f"investor_check_{idx}"))
    checked_count = sum(checks)
    st.progress(checked_count / len(check_items), text=f'You completed {checked_count}/{len(check_items)} self-check items')
    if checked_count < len(check_items):
        st.caption('Use this checklist to review risk recognition. Return to the relevant lesson for any unclear item.')
    else:
        st.success('All items reviewed. For a real investment, verify the security, local rules and your personal circumstances again.')

    section_heading("RED FLAGS", 'Warning signs to recognize')
    red_cols = st.columns(2)
    with red_cols[0]:
        info_card("🚩", 'Promises of high returns with little or no risk', 'Every investment has risk. Guaranteed high returns with almost no risk are a warning sign.')
        info_card("🚩", 'Pressure to act immediately', 'Urgency, secrecy, very short deadlines or pressure to borrow money are reasons to pause and verify.')
    with red_cols[1]:
        info_card("🚩", 'Social-media stock groups and fake experts', 'Strangers may impersonate professionals, brokers or regulators, or promote prices before selling. Group chats, screenshots and celebrity pictures are not verification.')
        info_card("🚩", 'Pay first to withdraw or recover losses', 'Unfreezing fees and recovery fees may be another scam. Do not send further funds or sensitive information to the requester.')

    with st.expander('Account security and common thinking traps'):
        st.markdown("""
**Account security**
- Use official broker websites or apps rather than sign-in links in unfamiliar messages.
- Enable multi-factor authentication where supported. Use a strong, unique password. Keep passwords, one-time codes and recovery codes private.
- Treat requests for remote device control, transfers to personal accounts, verification codes or unfreezing fees with suspicion.
- Check login alerts, orders and statements. Contact the broker through an official channel if something looks wrong.

**Thinking traps**
- **FOMO:** Rushing in after a fast rise.
- **Loss aversion:** Focusing only on getting back to even while ignoring a changed investment case.
- **Confirmation bias:** Seeking supporting news and ignoring opposing evidence.
- **Overconfidence and overtrading:** Overestimating short-term forecasting skill and underestimating costs and mistakes.
- **Sunk costs:** Continuing an unsupported decision because you already spent time or money on it.

Before investing, record your reasons, main risks, verification sources and when to reassess.
""")
    with st.expander('Advanced tools to recognize before considering them'):
        st.markdown("""
- **Margin / leverage:** Borrowing or derivatives can magnify losses and lead to margin calls or forced sales.
- **Short selling:** Borrow securities to sell, then buy them back to return. Rising prices can create very large losses; the process is more complex than an ordinary purchase.
- **Options:** Values depend on the underlying price, time, volatility and more. Risks differ by strategy; some selling strategies have extremely high or theoretically unlimited losses.
- **Leveraged / inverse ETFs:** Targets usually apply to a specified daily multiple or inverse return. Daily resets and compounding can make longer-term results differ from a simple multiple.

You do not need to master these tools now. Learn their added complexity and risk before considering their use.
""")

    scam_answer = st.radio('A social-media group promises high monthly profits and asks you to transfer money today for an inside stock list. What is the careful response?', [
        'Transfer quickly to avoid missing out', 'Pause and independently verify the organization and sources', 'Send a little first, then add more after the guaranteed profit'], key="scam_practice")
    if st.button('Check your scam awareness', key="scam_submit"):
        passed = scam_answer.startswith('Pause')
        record_quiz_attempt('Risk & Investor Protection', passed)
        if passed:
            st.success('Correct. Guaranteed returns and pressure to transfer are warning signs. Verify independently and protect your personal and account information.')
        else:
            st.error("Guaranteed returns and urgency deserve caution. A chat group's recommendation is not a reason to transfer funds or trade.")
    lesson_completion_button('Risk & Investor Protection', "finish_investor_protection")


# ============================================================
# Comprehensive final quiz
# ============================================================
elif chosen_page == 'Final Quiz':
    hero('Final Quiz | Connect What You Have Learned', '24 scenario questions cover stocks, candles, indicators, orders, statements, price drivers and investor protection. Submit to see each result, its explanation and the lesson to revisit.', "FINAL ASSESSMENT · BEGINNER PATHWAY")
    questions = [
        (
            'You buy one common share in the secondary market. What does that represent?',
            ['A small equity stake in the company, without a promise of fixed principal repayment or interest.', 'A loan to the company with a maturity date and required principal repayment.', 'Direct ownership of a separately allocated portion of every company asset.', 'Only an index-tracking unit, with no security ownership rights.'],
            0, 'Common stock represents equity. Dividends and capital returns are not guaranteed; creditors usually rank ahead of shareholders in liquidation.', '01 Stock Market Basics'),
        (
            'Which description of an index and an ETF is most accurate?',
            ['An index is usually a measurement framework; an ETF is an exchange-traded fund that may track it.', 'Both are fund shares; only their trading hours differ.', 'An ETF price must equal its index level, so tracking error is impossible.', 'An ETF removes market risk because it holds multiple securities.'],
            0, "An index measures a basket's performance and usually cannot be bought directly. An ETF is a product with possible market risk, costs and tracking error.", '01 Stock Market Basics'),
        (
            'Company A has 6 billion shares at $18; B has 1 billion shares at $120. Which has the higher market capitalization?',
            ['A is worth $108 billion and B $120 billion, so B is higher.', 'A is higher because it has more shares; price does not matter.', "B must be vastly larger because its share price is about 6.7 times A's.", 'You cannot calculate it without annual revenue.'],
            0, 'Market capitalization = share price × shares outstanding. A: $18 × 6 billion; B: $120 × 1 billion. Market cap differs from enterprise value and does not establish whether a stock is cheap.', '01 Stock Market Basics'),
        (
            'A daily candle has Open=50, High=54, Low=47, Close=48 and volume of 8 million shares. Which statement fits?',
            ['The close is below the open; the range is $7; volume measures shares traded that day.', 'Because the close is below the open, the low must be $48.', 'Volume means exactly $8 million changed hands.', 'All 8 million shares traded at the $48 close.'],
            0, "High minus low gives the interval's range. Close below open means a lower close. Volume counts traded shares, not people, and trades occur at different prices.", '02 Reading Stock Charts'),
        (
            'A stock falls 2% on about twice its 20-day average volume. What can you reliably conclude?',
            ["Trading is more active and the day's price is weaker, but these facts alone do not establish the cause or next day's direction.", 'Institutions are proven to be selling, so the decline must continue.', 'The company must have reported disappointing profit that day.', 'Double volume confirms a downtrend without earlier context.'],
            0, "Volume describes activity and price describes the period's outcome. They do not establish trader identity, business changes or future direction alone.", '02 Reading Stock Charts'),
        (
            'A small body with a long lower wick appears after a decline, then a similar shape appears after a rise. Which reading fits?',
            ['The first may be a Hammer and the second a Hanging Man. Shape alone does not settle the outcome.', 'Both are Hammers regardless of the earlier trend.', 'Both prove buyers are in control and price will rise.', 'The name depends only on whether volume is above average.'],
            0, 'Hammer and Hanging Man shapes are similar. Traditional naming depends on the prior trend. Location and later confirmation still matter.', '02A Candlestick Patterns'),
        (
            'A Bullish Engulfing appears after a decline near an earlier support area. How can you use it carefully?',
            ['Treat it as a possible recovery clue and check trend, later confirmation, volume and risk.', 'The bottom is proven, so position size and risk controls do not matter.', 'Any second green candle qualifies without comparing bodies.', 'The pattern exists only when volume exactly doubles.'],
            0, 'Use a clear pattern definition and check context and later evidence. Several agreeing clues still cannot guarantee the next move.', '02A Candlestick Patterns'),
        (
            'For the same length, how does EMA mainly differ from SMA?',
            ['EMA gives recent prices greater weight, usually reacting faster but potentially adding short-term noise.', 'EMA uses only volume.', 'EMA removes all lag and knows future prices.', 'Only the chart color differs; their calculations are identical.'],
            0, 'EMA weights recent data more heavily. SMA weights each price in its window equally. Faster response does not guarantee better accuracy.', '02B Technical Indicators'),
        (
            'RSI exceeds 70 and Stochastic exceeds 80. Which interpretation is reasonable?',
            ['Both use price data and overlap. Recent momentum or range position is high, but an immediate reversal is not guaranteed.', 'The next day must fall because both thresholds were crossed.', 'The company P/E exceeds industry values by 70% and 80%.', 'Stochastic uses only volume and RSI only volatility, so they are independent.'],
            0, 'Both are momentum oscillators with different calculations. Extreme readings are references, not reversal dates or fully independent evidence.', '02B Technical Indicators'),
        (
            'Bollinger Bands narrow, then price breaks above the upper band. Which statement is accurate?',
            ['Volatility must keep expanding upward.', 'This guarantees mean reversion and an immediate sale.', 'Narrow bands describe earlier low volatility. A breakout is a clue whose direction and persistence need later evidence.', 'The upper band is a guaranteed maximum fair price.'],
            2, 'Band width relates to standard deviation. Narrowing does not predict direction. Price may follow the upper band or return inside.', '02B Technical Indicators'),
        (
            'ADX is 32 and −DI exceeds +DI. What does this suggest?',
            ['Price must rise 32%.', 'Trend strength may be more pronounced, with −DI giving a downward directional clue. Neither guarantees what comes next.', 'Direction must be up because ADX rises only with rising prices.', 'Volume can be ignored because ADX counts buyers and sellers.'],
            1, 'ADX measures strength; +DI and −DI compare direction. Thresholds are guidelines, and the calculations lag prices.', '02B Technical Indicators'),
        (
            'You prioritize a prompt purchase over fixing a maximum buy price. Which order fits that aim?',
            ['Market order: seeks prompt execution, with a fill that may differ from the displayed quote.', 'Buy limit order: guarantees immediate execution at the ask.', 'Stop order: guarantees both execution and price.', 'A buy limit order automatically becomes a market order whenever price exceeds the limit.'],
            0, 'Market orders prioritize execution, with uncertain prices. Limit orders control price but may not fill. Stop triggers do not guarantee a fill price.', '03 How Orders Work'),
        (
            'The best ask is $101.20 and best bid $101.05. You submit a buy limit at $100.80. What is generally likely?',
            ['It remains unfilled for now; a seller at an acceptable price and suitable market conditions are needed.', 'A last trade at $100.80 guarantees an immediate full fill even with a higher ask.', 'It fills at $101.20 because a limit does not restrict the price.', 'It controls price, but the broker automatically raises the limit to the current ask.'],
            0, 'A buy limit generally does not buy above its limit. This order cannot immediately match the current ask. Execution remains uncertain; check broker rules.', '03 How Orders Work'),
        (
            'The best bid is $49.95 and best ask $50.10. Which statement is accurate?',
            ['The spread is $0.15, a trading-cost and liquidity clue that does not predict direction.', "The $0.15 spread is also the day's entire high-low range.", "The spread is $50.10; the bid is yesterday's closing price.", 'A narrower spread guarantees lower market risk and higher future returns.'],
            0, 'Spread = best ask − best bid. A narrower spread may reduce immediate trading costs without guaranteeing stable prices or lower investment risk.', '03 How Orders Work'),
        (
            'Where would you first find annual revenue/expenses, December 31 assets/liabilities, and annual cash inflows/outflows, respectively?',
            ['Income statement; Balance sheet; Cash flow statement.', 'Cash flow statement; Income statement; Balance sheet.', 'Balance sheet; Cash flow statement; Income statement.', 'All three are found only on the Income statement.'],
            0, "The Income statement covers a period's performance. The Balance sheet is a dated snapshot. The Cash flow statement explains cash movements.", '04 Researching a Company'),
        (
            'Revenue rises 25% and profit rises, but operating cash flow turns negative while receivables and inventory grow. What should you check?',
            ['Cash flow, receivables, inventory, revenue recognition and notes to investigate cash conversion and working capital.', 'Ignore cash flow because profit and cash are identical.', 'Assume revenue is fake because every increase in receivables means nonpayment.', "The day's stock price alone establishes revenue quality."],
            0, 'Revenue and accounting profit can precede cash collection. Working capital affects operating cash; capital expenditures also affect overall cash flow. Verify the statements and notes.', '04 Researching a Company'),
        (
            "A stock is $40 and last year's EPS is $2. What is its simple trailing P/E?",
            ['20×: price relative to EPS, without proving the stock cheap or expensive.', '0.05×: EPS divided by price is P/E.', '20×: investors are guaranteed to recover their cost in exactly 20 years.', '20×: this number alone proves it is cheaper than peers.'],
            0, 'Trailing P/E = $40 ÷ $2 = 20. Compare growth, industry, risk, earnings quality and expectations. It is not a payback guarantee.', '04 Researching a Company'),
        (
            'A company reports 40% revenue growth but its stock falls. Which explanation fits?',
            ['Investors compare results with expectations, guidance, margins, risk and market conditions. Positive growth alone does not guarantee a price rise.', 'Positive revenue growth proves a falling stock price is wrong.', 'The revenue number must be false.', 'Earnings cannot affect short-term expectations or prices.'],
            0, 'The market considers whether growth exceeded expectations, the outlook and the surrounding industry and market.', '05 Why Stock Prices Move'),
        (
            'What does historical volatility best describe?',
            ['Past variability of returns, rather than a future loss limit or probability of rising.', 'An exact future price forecast that improves with higher volatility.', 'A maximum loss that can never be exceeded.', 'The short-term debt proportion on a Balance sheet.'],
            0, 'This course estimates volatility using the standard deviation of daily returns, with √252 as an annualizing approximation. It cannot set a future risk limit.', 'Investor protection'),
        (
            'An asset falls from a peak of 100 to 72, then recovers to 90. What was its maximum drawdown?',
            ['28%: the fall from 100 to 72. The recovery does not erase the earlier drawdown.', '10%: only the final value of 90 matters.', '72%: the low is 72% of the peak.', "It cannot be calculated without the year's final close."],
            0, 'Maximum drawdown measures the largest peak-to-later-trough decline: (72 ÷ 100) − 1 = −28%. It describes the path, not just the ending change.', 'Investor protection'),
        (
            'A portfolio holds AAPL, MSFT, NVDA and Nasdaq-100 ETF QQQ. Which diversification statement makes sense?',
            ['Four symbols can still share large technology-stock risks and overlapping holdings. Check weights, sectors and overlap.', 'Four symbols mean four independent risks and complete diversification.', 'Weights at or below 25% eliminate the need to consider correlation.', 'An ETF prevents technology-sector or market declines from affecting the portfolio.'],
            0, 'Diversification depends on sectors, correlation, overlap and weights as well as security count. An ETF can own the same large technology stocks.', 'Investor protection'),
        (
            'You need tuition money next month and have no alternative funds. What is the key problem with putting it into a volatile single stock?',
            ['There may be too little time to recover from a decline, forcing a sale at a poor time.', "Choosing last year's top performer makes the deadline irrelevant.", 'Splitting purchases removes short-term loss risk.', 'Stocks are tradable, so market price and liquidity cannot affect the payment date.'],
            0, "Match money's purpose and timing to asset risk. Funds needed soon have less room for losses or recovery time.", 'Investor protection'),
        (
            'A social-media group promises stable high monthly returns, a deadline today and payment to a personal account. What is the safest first step?',
            ['Pause the transfer and independently verify the people, organization, platform and sources.', 'Send a small amount; a small transfer proves legitimacy.', 'Trust a profit screenshot with a plausible balance.', 'Transfer before the deadline and research afterward.'],
            0, 'Guaranteed returns, urgency and personal-account transfers are warning signs. Screenshots and unfamiliar links are insufficient verification.', '06 Risk & Investor Protection'),
        (
            'Which description of SEC EDGAR is correct?',
            ['An official source of public company filings; a filing does not mean SEC endorsement or a safety guarantee.', 'A searchable company is guaranteed free of fraud or bankruptcy.', 'EDGAR contains only social-media articles.', 'A press release removes any need to read filings or notes.'],
            0, 'EDGAR is a primary source for company filings. Readers must still read, cross-check and assess risks.', '06 Risk & Investor Protection'),
    ]
    # Move correct options into a balanced, non-obvious order so the answer key is not always A.
    target_positions = [2, 0, 3, 1, 0, 2, 1, 3, 2, 0, 3, 1, 2, 1, 0, 3, 1, 2, 0, 3, 1, 3, 0, 2]
    reordered_questions = []
    for item, target in zip(questions, target_positions):
        question_text, options, original_correct, explanation, lesson = item
        correct_option = options[original_correct]
        distractors = [option for idx, option in enumerate(options) if idx != original_correct]
        distractors.insert(target, correct_option)
        reordered_questions.append((question_text, distractors, target, explanation, lesson))
    questions = reordered_questions

    with st.form("final_comprehensive_quiz_form"):
        answers: list[int | None] = []
        for i, q in enumerate(questions):
            st.markdown(f'<div class="section-kicker">QUESTION {i+1:02d} / {len(questions):02d} · {escape(q[4])}</div><div style="font-size:1.02rem;font-weight:750;color:#131722;margin:.25rem 0 .7rem">{escape(q[0])}</div>', unsafe_allow_html=True)
            answer = st.radio('Choose an answer', q[1], key=f"comprehensive_answer_{i}", index=None, label_visibility="collapsed")
            answers.append(q[1].index(answer) if answer is not None else None)
            st.markdown("<hr style='margin:.8rem 0 1.2rem'>", unsafe_allow_html=True)
        submitted = st.form_submit_button('Submit quiz and view each result', width="stretch")
    if submitted:
        if any(answer is None for answer in answers):
            st.warning(f'There are {sum((answer is None for answer in answers))} questions are unanswered. Complete all 24 before submitting.')
        else:
            score = sum(answer == q[2] for answer, q in zip(answers, questions))
            st.session_state["comprehensive_quiz_result"] = {"score": score, "answers": answers}
            record_quiz_attempt('Final Quiz', score >= 20)
    result = st.session_state.get("comprehensive_quiz_result")
    if result:
        score = result["score"]
        required_score = 20  # At least 80% of 24 questions, rounded up.
        st.metric('Your score', f"{score}/{len(questions)}", f"{score / len(questions) * 100:.0f}%")
        if score >= required_score:
            st.success('Passed! You reached the 80% threshold. Keep applying the concepts to real evidence; a quiz pass does not establish forecasting skill.')
            if st.button('✓ Complete Final Quiz', key="comprehensive_quiz_complete"):
                mark_complete('Final Quiz')
                st.success('Quiz completion recorded.')
        else:
            st.info(f'You have not yet reached {required_score}/{len(questions)} points. Review the lessons linked to incorrect answers, then try again.')
        content_heading('Your results | Green = correct; red = incorrect', level="h3")
        for i, q in enumerate(questions):
            render_final_answer_review(i + 1, q[0], q[1], int(result["answers"][i]), q[2], q[3], q[4])
        st.button('Restart the 24-question quiz', key="comprehensive_quiz_retry", on_click=reset_comprehensive_quiz)

# ============================================================
# Data and methodology
# ============================================================
elif chosen_page == 'Data & Methods':
    hero('Data & Methods | Understand and Verify', 'The lessons use historical market data for interaction and explain definitions, calculations and limitations.', "DATA NOTES · TRANSPARENCY")
    c1, c2 = st.columns(2)
    with c1:
        info_card("🗂️", 'Data structure', 'Daily data contains date, symbol, open, high, low, close and volume. Several securities across dates form the dataset.', '7 fields')
    with c2:
        info_card("🧮", 'Measure definitions', 'Period return uses the first and last valid closes. Annualized volatility approximates daily-return standard deviation × √252. Maximum drawdown is the largest decline from an earlier peak.', 'Checkable calculations')

    section_heading("CURRICULUM SCOPE", 'What does the course cover?')
    st.markdown("""
The beginner path covers:

1. Stocks, bonds, indices, ETFs, dividends, market capitalization, exchanges and brokers.
2. OHLC, candlesticks, patterns, volume, quotes, timeframes and adjusted prices.
3. SMA / EMA, RSI, MACD, Bollinger Bands, Stochastic, ADX, OBV, Support and Resistance, and Fibonacci Retracement, including their limits.
4. Market, limit and stop orders; spreads, liquidity, costs, time in force, execution and settlement.
5. The Income statement, Balance sheet, Cash flow statement, revenue, profit, EPS, P/E, margins, debt and filings.
6. Company, industry, economic, expectation and liquidity drivers of prices.
7. Price return, total return, compounding, benchmarks, volatility, drawdowns, inflation, currencies and fees.
8. Investor protection, social-media scams, account security, thinking traps and advanced-product risks.

**Scope:** Introductory stock investing. Consult official documents for local taxes, trading rules and product terms. Short selling, margin, options, futures and leveraged products are introduced only at a basic risk-awareness level.
""")

    section_heading("DATA SOURCE", 'Sources and use limitations')
    st.markdown("""
- **Market data:** The third-party Python package `yfinance` retrieves Yahoo Finance historical data.
- **Data rights:** Availability for download does not establish permission for public redistribution. `yfinance` is not an officially endorsed Yahoo open API.
- **Course submissions:** If an assignment requires an open API or verifiable open dataset, confirm that this source qualifies or choose a source with clear licensing.
- **Adjusted prices:** Daily OHLC with `auto_adjust=True` is adjusted. Check definitions, missing data and corporate actions.
- **Candlestick examples:** The pattern gallery uses synthetic OHLC to show structure. The Learning Home price challenge and real-market lab use historical OHLCV. The price challenge selects a historical sample with nearby SMA and MACD crossovers, hides its next 20 trading days, and reveals them after submission. The selected symbol, dates and source appear beside the exercise. Pattern names and definitions can vary and do not establish predictions.
- **Earnings example:** Learning Home uses NVIDIA's November 20, 2024 announcement of fiscal Q3 2025 results, with the announcement linked on the page, to explore expectations and price reactions.
- **Trading:** Educational exploration only; there is no broker connection or real order submission.
""")
    with st.expander('Teaching structure and further learning'):
        st.markdown("""
The project takes inspiration from the public structure of IBKR Campus / Traders' Academy, without copying its lesson content:
- Start with stocks and ETFs, then explore market structure, research, risk and practice.
- Combine concepts, examples, interactive exploration and knowledge checks.
- Allow retries and distinguish lesson completion from quiz results.

The explanations and examples are independently written and do not represent IBKR courses or advice. English indicator and financial-statement names follow TradingView's published terminology.

**IBKR references:** [Course directory](https://www.interactivebrokers.com/campus/traders-academy/finance-courses/) · [Introduction to Stocks](https://www.interactivebrokers.com/campus/trading-course/intro-to-stocks/) · [Progress and quizzes](https://www.interactivebrokers.com/campus/about-academy-quizzes/)

**TradingView terminology:** [Candlesticks](https://www.tradingview.com/support/solutions/43000745269-introduction-to-candlestick-charts-and-patterns/) · [Technical indicators](https://www.tradingview.com/support/solutions/43000614331-technical-ratings/) · [Financial statements](https://www.tradingview.com/support/solutions/43000543506-how-to-access-financial-data-on-tradingview/)
""")
    with st.expander('Official resources and verification'):
        st.markdown("""
- [Investor.gov: Investing basics, risk, compounding and diversification](https://www.investor.gov/introduction-investing)
- [Investor.gov: Order types](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders)
- [Investor.gov: Common scams](https://www.investor.gov/additional-resources/spotlight/common-scams)
- [SEC EDGAR: Public company filings](https://www.sec.gov/edgar/search/)

These resources primarily address the US. Broker authorization, taxes, trading, settlement and investor protection vary elsewhere. Check your local regulator and broker's documents.
""")
    method_period = st.selectbox(t('Create a downloadable dataset'), list(PERIODS.keys()), index=4, format_func=lambda x: t(PERIODS[x]), key=lang_key("method_period"))
    method_symbols = st.multiselect(t('Choose symbols'), list(TICKERS.keys()), default=["AAPL", "MSFT", "NVDA", "SPY", "QQQ"], format_func=ticker_label, key=lang_key("method_symbols"))
    if st.button('Load and clean data', key="method_fetch"):
        method_data, method_error = safe_prices(method_symbols, method_period)
        st.session_state["method_data"] = method_data
        st.session_state["method_error"] = method_error
    method_data = st.session_state.get("method_data", pd.DataFrame())
    if st.session_state.get("method_error"):
        show_data_warning(st.session_state["method_error"])
    if isinstance(method_data, pd.DataFrame) and not method_data.empty:
        s1, s2, s3 = st.columns(3)
        s1.metric('Rows', f"{len(method_data):,}")
        s2.metric('Securities', f"{method_data['ticker'].nunique()}")
        s3.metric('Fields', f"{method_data.shape[1]}")
        st.dataframe(method_data.head(30), width="stretch", hide_index=True)
        st.download_button('Download cleaned CSV', method_data.to_csv(index=False).encode("utf-8-sig"), file_name="stockscope_cleaned_daily_prices.csv", mime="text/csv")


# Footer
if not _EMBEDDED:
    st.markdown("---")
    st.caption('StockScope Learn · Introductory investing course prototype. Historical data may be delayed, missing or revised; past performance does not predict future results. Check data-use and redistribution rights before public release.')

# Auto-scroll is deliberately reserved for a real main-navigation change.
# Changing the selected candle pattern never triggers a scroll-to-top action.
if _page_changed:
    scroll_main_to_top(f"page:{st.session_state.get('_scroll_sequence', 0)}:{chosen_page}")
