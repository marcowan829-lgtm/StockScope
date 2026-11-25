from __future__ import annotations

from datetime import datetime
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf


st.set_page_config(
    page_title="StockScope｜美股探索仪表盘",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# A curated, editable starter universe. Sector labels are a project-level grouping,
# not a claim that this list represents the complete US stock market.
UNIVERSE = {
    "AAPL": "科技", "MSFT": "科技", "NVDA": "科技", "GOOGL": "科技",
    "AMZN": "科技/消费", "META": "科技", "AVGO": "科技", "ORCL": "科技",
    "CRM": "科技", "AMD": "科技", "QCOM": "科技", "INTC": "科技",
    "CSCO": "科技", "ADBE": "科技", "IBM": "科技",
    "JPM": "金融", "BAC": "金融", "GS": "金融", "MS": "金融",
    "V": "金融", "MA": "金融", "PYPL": "金融", "BRK-B": "金融",
    "LLY": "医疗保健", "JNJ": "医疗保健", "UNH": "医疗保健",
    "ABBV": "医疗保健", "MRK": "医疗保健", "PFE": "医疗保健", "ISRG": "医疗保健",
    "WMT": "消费", "COST": "消费", "HD": "消费", "NKE": "消费",
    "MCD": "消费", "KO": "消费", "PG": "消费", "DIS": "消费", "NFLX": "消费/媒体",
    "CAT": "工业", "GE": "工业", "RTX": "工业", "HON": "工业", "UPS": "工业", "DE": "工业",
    "XOM": "能源", "CVX": "能源", "SLB": "能源",
    "SPY": "市场基准", "QQQ": "市场基准", "DIA": "市场基准",
}


COMPANY_NAMES = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA", "GOOGL": "Alphabet A",
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

PERIOD_LABELS = {
    "1mo": "近 1 个月",
    "3mo": "近 3 个月",
    "6mo": "近 6 个月",
    "1y": "近 1 年",
    "2y": "近 2 年",
    "5y": "近 5 年",
}

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.25rem; padding-bottom: 2rem;}
      div[data-testid="stMetric"] {background: rgba(128,128,128,0.06); border: 1px solid rgba(128,128,128,0.16); padding: 0.8rem 0.9rem; border-radius: 12px;}
      .small-note {font-size: 0.88rem; opacity: 0.82;}
    </style>
    """,
    unsafe_allow_html=True,
)


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
            # yfinance versions can vary in which MultiIndex level holds the field.
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
            out = out.to_frame(name=tickers[0] if len(tickers) == 1 else field)
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
    """Fetch one symbol's latest intraday bars. Yahoo may delay, omit, or throttle data."""
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


def to_new_york_time(value) -> pd.Timestamp:
    """Normalize Yahoo bar timestamp to America/New_York for display and age checks."""
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        return stamp.tz_localize("America/New_York")
    return stamp.tz_convert("America/New_York")


def estimated_us_session(now_et: pd.Timestamp) -> str:
    """Rough clock-based session label; intentionally does not verify exchange holidays."""
    if now_et.weekday() >= 5:
        return "周末：常规美股市场通常休市"
    current_minutes = now_et.hour * 60 + now_et.minute
    if 4 * 60 <= current_minutes < 9 * 60 + 30:
        return "盘前时段（按当地时钟估算）"
    if 9 * 60 + 30 <= current_minutes < 16 * 60:
        return "常规交易时段（按当地时钟估算）"
    if 16 * 60 <= current_minutes < 20 * 60:
        return "盘后时段（按当地时钟估算）"
    return "常规交易时段之外"


@st.cache_data(ttl=3600, show_spinner=False)
def get_ticker_info(ticker: str) -> dict:
    """Yahoo metadata can be incomplete or unavailable for some symbols."""
    try:
        info = yf.Ticker(ticker).get_info()
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


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
            "代码": ticker,
            "类别": UNIVERSE.get(ticker, "其他"),
            "最新收盘价": last_price,
            "区间涨跌幅 (%)": total_return,
            "年化波动率 (%)": volatility,
            "最大回撤 (%)": float(drawdown),
            "平均日成交量": float(g["volume"].mean()) if g["volume"].notna().any() else np.nan,
            "最新日成交量": float(g["volume"].iloc[-1]) if pd.notna(g["volume"].iloc[-1]) else np.nan,
            "数据起始日": g["date"].min().date(),
            "最新数据日": g["date"].max().date(),
        })
    return pd.DataFrame(rows)


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



def calculate_daily_snapshot(prices: pd.DataFrame) -> pd.DataFrame:
    """Create per-ticker latest-close and prior-session change for the homepage."""
    rows = []
    if prices.empty:
        return pd.DataFrame(columns=["代码", "公司", "最近交易日涨跌幅 (%)"])
    for ticker, group in prices.groupby("ticker"):
        g = group.sort_values("date").dropna(subset=["close"])
        if g.empty:
            continue
        last = g.iloc[-1]
        previous_close = float(g.iloc[-2]["close"]) if len(g) >= 2 else np.nan
        last_close = float(last["close"])
        daily_change = ((last_close / previous_close) - 1) * 100 if pd.notna(previous_close) and previous_close else np.nan
        rows.append({
            "代码": str(ticker),
            "公司": COMPANY_NAMES.get(str(ticker), str(ticker)),
            "最近交易日涨跌幅 (%)": daily_change,
        })
    return pd.DataFrame(rows)


def ticker_label(ticker: str) -> str:
    return f"{ticker} · {COMPANY_NAMES.get(ticker, ticker)}"

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
    monthly_returns["类别"] = [UNIVERSE.get(t, "其他") for t in monthly_returns.index]
    sect = monthly_returns.groupby("类别").mean(numeric_only=True)
    if sect.empty or sect.shape[1] == 0:
        return None
    labels = [pd.Timestamp(c).strftime("%Y-%m") for c in sect.columns]
    fig = go.Figure(data=go.Heatmap(
        z=sect.values,
        x=labels,
        y=sect.index.tolist(),
        colorscale="RdYlGn",
        zmid=0,
        colorbar={"title": "月涨跌幅 %"},
        hovertemplate="类别：%{y}<br>月份：%{x}<br>平均涨跌幅：%{z:.2f}%<extra></extra>",
    ))
    fig.update_layout(title="行业分组月度表现热力图（组内股票等权平均）", xaxis_title="月份", yaxis_title="分类", height=420, margin=dict(l=10, r=10, t=60, b=10))
    return fig


# Header and navigation
st.title("📈 StockScope｜美股研究工作台")
st.markdown("以盘中分钟行情为核心，兼顾历史收益、风险与个股研究。")
st.caption("盘中数据来自 Yahoo Finance 的第三方 yfinance 接口；时间戳接近当前时间不代表已验证的实时或固定延迟行情。")

if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = ["NVDA", "AAPL", "MSFT", "SPY"]
if "detail_ticker" not in st.session_state or st.session_state.get("detail_ticker") not in UNIVERSE:
    st.session_state["detail_ticker"] = "NVDA"

st.sidebar.title("StockScope")
selected_page = st.sidebar.radio(
    "主要功能",
    options=["实时看盘", "市场首页", "市场概览", "股票筛选器", "收益与风险", "个股详情", "方法与数据"],
    index=0,
    key="main_navigation",
)

if selected_page != "实时看盘":
    with st.form("global_ticker_search", clear_on_submit=False):
        search_col, search_button_col = st.columns([5, 1])
        search_query = search_col.text_input(
            "全局搜索",
            placeholder="输入股票代码或公司名称，例如 NVDA、NVIDIA、Apple",
            help="可搜索内置观察列表中的股票与 ETF。",
        )
        search_submitted = search_button_col.form_submit_button("搜索股票", use_container_width=True)

    if search_submitted:
        q = search_query.strip()
        q_upper = q.upper()
        q_lower = q.casefold()
        exact_ticker = q_upper if q_upper in UNIVERSE else None
        if exact_ticker is None:
            exact_ticker = next((t for t, name in COMPANY_NAMES.items() if name.casefold() == q_lower), None)
        if exact_ticker:
            st.session_state["detail_ticker"] = exact_ticker
            st.session_state.pop("search_candidates", None)
            st.success(f"已定位：{ticker_label(exact_ticker)}。个股详情选择器已更新。")
        elif q:
            matches = [t for t in UNIVERSE if q_upper in t.upper() or q_lower in COMPANY_NAMES.get(t, t).casefold()]
            if len(matches) == 1:
                st.session_state["detail_ticker"] = matches[0]
                st.session_state.pop("search_candidates", None)
                st.success(f"已定位：{ticker_label(matches[0])}。个股详情选择器已更新。")
            elif matches:
                st.session_state["search_candidates"] = matches
                st.info(f"找到 {len(matches)} 个匹配代码，请从下方选择。")
            else:
                st.session_state.pop("search_candidates", None)
                st.warning("没有在当前内置观察列表中找到匹配项。请尝试输入准确的股票代码。")
        else:
            st.session_state.pop("search_candidates", None)
            st.warning("请输入股票代码或公司名称。")

    if st.session_state.get("search_candidates"):
        candidate_col, candidate_button_col = st.columns([4, 1])
        candidate = candidate_col.selectbox(
            "搜索匹配结果",
            options=st.session_state["search_candidates"],
            format_func=ticker_label,
            key="search_candidate_choice",
        )
        if candidate_button_col.button("设为详情股票", use_container_width=True):
            st.session_state["detail_ticker"] = candidate
            st.session_state.pop("search_candidates", None)
            st.success(f"已选择 {ticker_label(candidate)}。个股详情选择器已更新。")

if selected_page == "实时看盘":
    st.header("🔴 实时看盘")
    st.markdown("这是 StockScope 的核心页面：尝试获取盘中分钟 K 线，查看价格、区间变化和成交量。")

    live_controls = st.columns([1.5, 1, 1.2, 1.4, 1.1])
    live_ticker = live_controls[0].selectbox(
        "看盘股票",
        options=list(UNIVERSE.keys()),
        index=list(UNIVERSE.keys()).index(st.session_state.get("live_ticker", "NVDA")),
        format_func=ticker_label,
        key="live_ticker",
    )
    live_interval = live_controls[1].selectbox(
        "K 线周期",
        options=["1m", "5m", "15m", "30m", "60m"],
        index=0,
        format_func=lambda x: {"1m": "1 分钟", "5m": "5 分钟", "15m": "15 分钟", "30m": "30 分钟", "60m": "60 分钟"}[x],
        key="live_interval",
    )
    refresh_label = live_controls[2].selectbox(
        "自动刷新",
        options=["手动刷新", "每 15 秒", "每 30 秒", "每 60 秒"],
        index=2,
        key="live_refresh_mode",
    )
    refresh_seconds = {"手动刷新": None, "每 15 秒": 15, "每 30 秒": 30, "每 60 秒": 60}[refresh_label]
    include_extended = live_controls[3].checkbox("包含盘前/盘后", value=True, key="live_extended")
    if live_controls[4].button("↻ 立即刷新", use_container_width=True, key="live_force_refresh"):
        download_intraday_one.clear()
        st.rerun()

    live_watchlist = st.multiselect(
        "同时监控的自选股（建议不超过 6 只，减少数据请求）",
        options=list(UNIVERSE.keys()),
        default=[t for t in st.session_state.get("watchlist", ["NVDA", "AAPL", "MSFT", "SPY"]) if t in UNIVERSE][:6],
        format_func=ticker_label,
        key="live_watchlist",
        help="该表展示各股票最新返回的分钟 K 线，并非逐笔实时成交。",
    )

    interval_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "60m": 60}
    st.info(
        "数据说明：刷新频率代表应用重新请求数据的频率，不代表行情一定实时或固定延迟 15 分钟。"
        "Yahoo Finance/yfinance 可能延迟、缺失或限流；此功能用于观察和课程原型，不用于交易执行。"
    )

    @st.fragment(run_every=refresh_seconds)
    def render_live_monitor(selected_symbol: str, selected_interval: str, extended: bool, watchlist_symbols: list[str]):
        now_et = pd.Timestamp.now(tz="America/New_York")
        st.caption(
            f"当前美东时间：{now_et.strftime('%Y-%m-%d %H:%M:%S %Z')} · "
            f"时段参考：{estimated_us_session(now_et)} · 自动刷新：{refresh_label}。"
            "时段估算未核对交易所假日。"
        )

        try:
            intraday = download_intraday_one(selected_symbol, selected_interval, extended)
        except Exception as exc:
            st.error("暂时无法获取该股票的分钟行情。可能是网络、Yahoo Finance 接口或请求频率限制导致。")
            with st.expander("查看技术错误信息"):
                st.code(str(exc))
            intraday = pd.DataFrame()

        if intraday.empty:
            st.warning(
                f"{selected_symbol} 当前没有返回 {selected_interval} 分钟数据。"
                "如果现在不是美股交易时段，可能需要等到下一个交易日再测试；也可以关闭盘前/盘后选项后重试。"
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
                status_text = "最新 K 线时间戳略晚于本机取时；请结合下一次刷新复核"
            elif age_minutes <= stale_threshold:
                status_text = "最新 K 线时间戳接近当前时间（不构成实时性或延迟保证）"
            else:
                status_text = "最新 K 线时间较旧；可能是休市、盘前盘后结束或接口未更新"
            st.caption(
                f"数据状态：{status_text} · 最新 K 线时间：{last_ts_et.strftime('%Y-%m-%d %H:%M:%S %Z')} · "
                f"与当前时间戳相差约 {age_minutes:.1f} 分钟。"
            )

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("最新返回价格", f"${last_close:,.2f}", help="分钟 K 线的 Close，不是逐笔成交价。")
            m2.metric(
                "较上一根 K 线",
                f"{bar_change:+.2f}%" if pd.notna(bar_change) else "—",
                help="当前最后一根 K 线收盘价相对上一根 K 线收盘价的变化。",
            )
            m3.metric("最新一根 K 线成交量", f"{last_volume:,.0f}" if pd.notna(last_volume) else "—")
            m4.metric("返回 K 线数量", f"{len(valid):,}")

            chart_left, chart_right = st.columns([1.6, 1], gap="large")
            with chart_left:
                candle = go.Figure(data=[go.Candlestick(
                    x=valid.index,
                    open=valid["Open"], high=valid["High"], low=valid["Low"], close=valid["Close"],
                    name=selected_symbol,
                )])
                candle.update_layout(
                    title=f"{selected_symbol} · {selected_interval} 分钟 K 线",
                    height=480,
                    margin=dict(l=5, r=5, t=55, b=5),
                    xaxis_title="时间（Yahoo 返回时区）",
                    yaxis_title="价格（美元）",
                    xaxis_rangeslider_visible=False,
                    hovermode="x unified",
                )
                st.plotly_chart(candle, use_container_width=True, key=f"live_candle_{selected_symbol}_{selected_interval}")
            with chart_right:
                volume_figure = go.Figure(data=[go.Bar(x=valid.index, y=valid["Volume"], name="成交量")])
                volume_figure.update_layout(
                    title="每根 K 线成交量",
                    height=480,
                    margin=dict(l=5, r=5, t=55, b=5),
                    xaxis_title="时间（Yahoo 返回时区）",
                    yaxis_title="成交量",
                    hovermode="x unified",
                )
                st.plotly_chart(volume_figure, use_container_width=True, key=f"live_volume_{selected_symbol}_{selected_interval}")

            with st.expander("查看最新分钟数据明细", expanded=False):
                detail = valid.tail(30).copy()
                detail.index.name = "时间（Yahoo 返回时区）"
                st.dataframe(detail.sort_index(ascending=False), use_container_width=True)
                st.download_button(
                    "下载当前股票分钟数据 CSV",
                    data=detail.reset_index().to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"{selected_symbol}_{selected_interval}_intraday.csv",
                    mime="text/csv",
                    key=f"download_live_{selected_symbol}_{selected_interval}",
                )

        st.markdown("### 自选股盘中监控")
        if not watchlist_symbols:
            st.info("请在上方选择至少一只股票，查看其最新返回的分钟 K 线。")
        else:
            records = []
            # Keep requests bounded. One selected chart plus up to six watchlist symbols.
            symbols = list(dict.fromkeys(watchlist_symbols[:6]))
            for symbol in symbols:
                try:
                    bars = download_intraday_one(symbol, selected_interval, extended)
                    if bars.empty:
                        records.append({
                            "代码": symbol, "公司": COMPANY_NAMES.get(symbol, symbol), "最新返回价格": np.nan,
                            "较上一根 K 线 (%)": np.nan, "最新 K 线成交量": np.nan, "最新 K 线时间（美东）": "无数据",
                            "时间戳差值（分钟）": np.nan, "状态": "无数据",
                        })
                        continue
                    bars = bars.dropna(subset=["Close"]).sort_index()
                    latest = bars.iloc[-1]
                    latest_time = to_new_york_time(bars.index[-1])
                    now = pd.Timestamp.now(tz="America/New_York")
                    age = (now - latest_time).total_seconds() / 60
                    previous = float(bars["Close"].iloc[-2]) if len(bars) >= 2 else np.nan
                    change = (float(latest["Close"]) / previous - 1) * 100 if pd.notna(previous) and previous else np.nan
                    status = "时间戳较新" if 0 <= age <= max(3, interval_minutes[selected_interval] * 2) else "需核实更新状态"
                    records.append({
                        "代码": symbol,
                        "公司": COMPANY_NAMES.get(symbol, symbol),
                        "最新返回价格": float(latest["Close"]),
                        "较上一根 K 线 (%)": change,
                        "最新 K 线成交量": float(latest["Volume"]) if pd.notna(latest["Volume"]) else np.nan,
                        "最新 K 线时间（美东）": latest_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                        "时间戳差值（分钟）": age,
                        "状态": status,
                    })
                except Exception as exc:
                    records.append({
                        "代码": symbol, "公司": COMPANY_NAMES.get(symbol, symbol), "最新返回价格": np.nan,
                        "较上一根 K 线 (%)": np.nan, "最新 K 线成交量": np.nan,
                        "最新 K 线时间（美东）": "请求失败", "时间戳差值（分钟）": np.nan,
                        "状态": str(exc)[:80],
                    })
            quote_table = pd.DataFrame(records)
            st.dataframe(
                quote_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "最新返回价格": st.column_config.NumberColumn(format="$%.2f"),
                    "较上一根 K 线 (%)": st.column_config.NumberColumn(format="%.2f%%"),
                    "最新 K 线成交量": st.column_config.NumberColumn(format="%.0f"),
                    "时间戳差值（分钟）": st.column_config.NumberColumn(format="%.1f"),
                },
            )
        st.caption("重要：时间戳差值只是 K 线时间标签与当前时间之差，不等于数据从交易所到 Yahoo 再到本应用的真实传输延迟。")

    render_live_monitor(live_ticker, live_interval, include_extended, live_watchlist)

else:
    # Historical-analysis controls
    st.sidebar.caption("历史行情与风险分析")
    period = st.sidebar.selectbox("分析时间范围", options=list(PERIOD_LABELS.keys()), index=3, format_func=lambda x: PERIOD_LABELS[x])
    sector_options = ["全部分类"] + sorted(set(UNIVERSE.values()))
    selected_sector = st.sidebar.selectbox("股票分类筛选", options=sector_options, index=0)
    def_tickers = ["NVDA", "AAPL", "MSFT", "SPY"]
    compare_tickers = st.sidebar.multiselect(
        "股价走势对比（可多选）",
        options=list(UNIVERSE.keys()),
        default=def_tickers,
        format_func=ticker_label,
        help="最多建议选择 8 只，图表会更清晰。",
    )
    focus_ticker = st.sidebar.selectbox(
        "个股详情",
        options=list(UNIVERSE.keys()),
        format_func=ticker_label,
        key="detail_ticker",
    )
    if st.sidebar.button("🔄 清除缓存并刷新数据", use_container_width=True):
        download_prices.clear()
        get_ticker_info.clear()
        st.rerun()
    st.sidebar.markdown("---")
    st.sidebar.markdown("**数据说明**")
    st.sidebar.caption("本区主要使用日线历史数据。数据可能延迟、缺失或受接口限制；本工具不提供投资建议。")

    selected_tickers = tuple(UNIVERSE.keys())
    with st.spinner("正在从 Yahoo Finance 获取股票日线数据……首次加载可能需要一点时间。"):
        try:
            prices = download_prices(selected_tickers, period)
        except Exception as exc:
            prices = pd.DataFrame()
            load_error = str(exc)
        else:
            load_error = ""

    if prices.empty:
        st.error("没有成功获取行情数据。请检查网络连接、Yahoo Finance 接口状态，或稍后点击左侧“清除缓存并刷新数据”。")
        if load_error:
            st.code(load_error)
        st.info("你可以先确认本机已安装依赖：在 Windows 命令提示符（不是 Python 的 >>>）中运行 `pip install -r requirements.txt`。")
        st.stop()

    metrics = calculate_metrics(prices)
    daily_snapshot = calculate_daily_snapshot(prices)
    if not daily_snapshot.empty:
        metrics = metrics.merge(
            daily_snapshot[["代码", "公司", "最近交易日涨跌幅 (%)"]],
            on="代码",
            how="left",
        )
    if selected_sector != "全部分类":
        metrics_view = metrics[metrics["类别"] == selected_sector].copy()
    else:
        metrics_view = metrics.copy()

    latest_date = prices["date"].max().date()
    loaded_tickers = prices["ticker"].nunique()
    positive_share = (metrics["区间涨跌幅 (%)"] > 0).mean() * 100 if not metrics.empty else np.nan
    median_vol = metrics["年化波动率 (%)"].median() if not metrics.empty else np.nan
    mean_return = metrics["区间涨跌幅 (%)"].mean() if not metrics.empty else np.nan

    # Prepare filtered prices for visual panels.
    if selected_sector == "全部分类":
        active_tickers = list(UNIVERSE.keys())
    else:
        active_tickers = [t for t, s in UNIVERSE.items() if s == selected_sector]
    prices_active = prices[prices["ticker"].isin(active_tickers)].copy()
    metrics_active = metrics_view.copy()

    if selected_page == "市场首页":
        st.subheader("主要指数快照")
        benchmark_tickers = ["SPY", "QQQ", "DIA"]
        benchmark_labels = {
            "SPY": "标普 500（SPY）",
            "QQQ": "纳斯达克 100（QQQ）",
            "DIA": "道琼斯工业平均（DIA）",
        }
        benchmark_cols = st.columns(3)
        for col, ticker in zip(benchmark_cols, benchmark_tickers):
            row = metrics[metrics["代码"] == ticker]
            with col:
                if row.empty:
                    st.metric(benchmark_labels[ticker], "暂无数据")
                else:
                    r = row.iloc[0]
                    delta = r.get("最近交易日涨跌幅 (%)", np.nan)
                    st.metric(
                        benchmark_labels[ticker],
                        f"${r['最新收盘价']:,.2f}" if pd.notna(r.get("最新收盘价", np.nan)) else "—",
                        delta=f"{delta:+.2f}%" if pd.notna(delta) else None,
                        help=f"最新数据日期：{r.get('最新数据日', '未知')}。显示的是最近可用日线收盘价，不是实时价格。",
                    )

        stocks_only = metrics[~metrics["代码"].isin(["SPY", "QQQ", "DIA"])].copy()
        valid_daily_returns = stocks_only["最近交易日涨跌幅 (%)"].dropna()
        advancers = int((valid_daily_returns > 0).sum())
        decliners = int((valid_daily_returns < 0).sum())
        unchanged = int((valid_daily_returns == 0).sum())
        market_cols = st.columns(4)
        market_cols[0].metric("观察股票数", f"{len(stocks_only)}")
        market_cols[1].metric("上涨股票", f"{advancers}")
        market_cols[2].metric("下跌股票", f"{decliners}")
        market_cols[3].metric("持平股票", f"{unchanged}")
        snapshot_dates = pd.to_datetime(stocks_only["最新数据日"], errors="coerce").dropna()
        snapshot_date = snapshot_dates.max().date() if not snapshot_dates.empty else latest_date
        st.caption(f"观察列表市场广度 · 最新可用数据日期约为 {snapshot_date}。该统计只覆盖本应用内置股票列表，不代表整个美股市场。")

        st.markdown("### 最近交易日涨跌榜")
        movers_left, movers_right = st.columns(2, gap="large")
        with movers_left:
            gainers = stocks_only.dropna(subset=["最近交易日涨跌幅 (%)"]).nlargest(10, "最近交易日涨跌幅 (%)")
            if not gainers.empty:
                fig_gainers = px.bar(
                    gainers.sort_values("最近交易日涨跌幅 (%)"),
                    x="最近交易日涨跌幅 (%)", y="代码", orientation="h",
                    color="最近交易日涨跌幅 (%)", color_continuous_scale="RdYlGn",
                    hover_data={"公司": True, "最新收盘价": ":.2f", "最新日成交量": ":,.0f"},
                    title="涨幅榜 · Top 10",
                )
                fig_gainers.update_layout(height=390, showlegend=False, xaxis_title="最近交易日涨跌幅 (%)", yaxis_title="", margin=dict(l=5, r=5, t=55, b=5), coloraxis_showscale=False)
                st.plotly_chart(fig_gainers, use_container_width=True)
            else:
                st.info("暂无足够数据生成涨幅榜。")
        with movers_right:
            losers = stocks_only.dropna(subset=["最近交易日涨跌幅 (%)"]).nsmallest(10, "最近交易日涨跌幅 (%)")
            if not losers.empty:
                fig_losers = px.bar(
                    losers.sort_values("最近交易日涨跌幅 (%)", ascending=False),
                    x="最近交易日涨跌幅 (%)", y="代码", orientation="h",
                    color="最近交易日涨跌幅 (%)", color_continuous_scale="RdYlGn",
                    hover_data={"公司": True, "最新收盘价": ":.2f", "最新日成交量": ":,.0f"},
                    title="跌幅榜 · Bottom 10",
                )
                fig_losers.update_layout(height=390, showlegend=False, xaxis_title="最近交易日涨跌幅 (%)", yaxis_title="", margin=dict(l=5, r=5, t=55, b=5), coloraxis_showscale=False)
                st.plotly_chart(fig_losers, use_container_width=True)
            else:
                st.info("暂无足够数据生成跌幅榜。")

        st.markdown("### 成交量榜")
        volume_rank = stocks_only.dropna(subset=["最新日成交量"]).nlargest(10, "最新日成交量")
        if not volume_rank.empty:
            fig_volume_rank = px.bar(
                volume_rank.sort_values("最新日成交量"),
                x="最新日成交量", y="代码", orientation="h",
                color="最近交易日涨跌幅 (%)", color_continuous_scale="RdYlGn",
                hover_data={"公司": True, "最新收盘价": ":.2f", "最近交易日涨跌幅 (%)": ":.2f"},
                title="最近交易日成交量最高的 10 只股票",
            )
            fig_volume_rank.update_layout(height=410, xaxis_title="成交量（股）", yaxis_title="", margin=dict(l=5, r=5, t=55, b=5), coloraxis_showscale=False)
            st.plotly_chart(fig_volume_rank, use_container_width=True)
        else:
            st.info("暂无成交量数据。")

        st.markdown("### 我的自选股")
        add_col, edit_col = st.columns([1, 3])
        with add_col:
            add_ticker = st.selectbox("添加代码", options=list(UNIVERSE.keys()), format_func=ticker_label, key="watchlist_add_ticker")
            if st.button("＋ 加入自选", use_container_width=True):
                current_watchlist = list(st.session_state.get("watchlist", []))
                if add_ticker not in current_watchlist:
                    st.session_state["watchlist"] = current_watchlist + [add_ticker]
                    st.success(f"已将 {add_ticker} 加入自选股。")
                else:
                    st.info(f"{add_ticker} 已在自选列表中。")
        with edit_col:
            st.multiselect(
                "编辑自选列表（取消选择即可移除）",
                options=list(UNIVERSE.keys()),
                format_func=ticker_label,
                key="watchlist",
            )
        watchlist_now = list(st.session_state.get("watchlist", []))
        watchlist_table = metrics[metrics["代码"].isin(watchlist_now)].copy()
        if watchlist_table.empty:
            st.info("自选列表暂时为空。请从左侧添加股票。")
        else:
            order_map = {t: i for i, t in enumerate(watchlist_now)}
            watchlist_table["_顺序"] = watchlist_table["代码"].map(order_map)
            watchlist_table = watchlist_table.sort_values("_顺序")
            watchlist_cols = ["代码", "公司", "最新收盘价", "最近交易日涨跌幅 (%)", "区间涨跌幅 (%)", "年化波动率 (%)", "最新日成交量", "最新数据日"]
            watchlist_table = watchlist_table[watchlist_cols]
            st.dataframe(
                watchlist_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "最新收盘价": st.column_config.NumberColumn(format="$%.2f"),
                    "最近交易日涨跌幅 (%)": st.column_config.NumberColumn(format="%.2f%%"),
                    "区间涨跌幅 (%)": st.column_config.NumberColumn(format="%.2f%%"),
                    "年化波动率 (%)": st.column_config.NumberColumn(format="%.2f%%"),
                    "最新日成交量": st.column_config.NumberColumn(format="%.0f"),
                },
            )
            st.download_button("下载自选股数据 CSV", data=watchlist_table.to_csv(index=False).encode("utf-8-sig"), file_name="stockscope_watchlist.csv", mime="text/csv")

    elif selected_page == "市场概览":
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("已加载股票 / ETF", f"{loaded_tickers}", help="来自本应用内置的观察列表，不代表全部美股。")
        k2.metric(f"观察列表平均涨跌幅 · {PERIOD_LABELS[period]}", pct(mean_return))
        k3.metric("区间上涨占比", pct(positive_share))
        k4.metric("股票年化波动率中位数", pct(median_vol))
        st.caption(f"最后数据日期：{latest_date} · 数据范围：{PERIOD_LABELS[period]} · 当前观察列表共 {len(UNIVERSE)} 个代码")
        left, right = st.columns([1.15, 0.85], gap="large")
        with left:
            fig_heat = make_monthly_sector_heatmap(prices_active)
            if fig_heat is not None:
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.info("当前时间范围的数据不足以生成月度热力图。")
        with right:
            ranked = metrics_active.sort_values("区间涨跌幅 (%)", ascending=False).head(15)
            fig_rank = px.bar(
                ranked.sort_values("区间涨跌幅 (%)"),
                x="区间涨跌幅 (%)", y="代码", color="区间涨跌幅 (%)",
                color_continuous_scale="RdYlGn", orientation="h",
                hover_data={"类别": True, "年化波动率 (%)": ":.2f", "最大回撤 (%)": ":.2f"},
                title="区间表现靠前的 15 个代码",
            )
            fig_rank.update_layout(height=420, coloraxis_colorbar_title="涨跌幅 %", margin=dict(l=10, r=10, t=60, b=10), yaxis_title="代码", xaxis_title="区间涨跌幅 (%)")
            st.plotly_chart(fig_rank, use_container_width=True)
        st.subheader("观察列表数据表")
        table_cols = ["代码", "类别", "最新收盘价", "区间涨跌幅 (%)", "年化波动率 (%)", "最大回撤 (%)", "平均日成交量", "最新日成交量", "最新数据日"]
        display_metrics = metrics_active.sort_values("区间涨跌幅 (%)", ascending=False)[table_cols].copy()
        st.dataframe(
            display_metrics,
            use_container_width=True,
            hide_index=True,
            column_config={
                "最新收盘价": st.column_config.NumberColumn(format="$%.2f"),
                "区间涨跌幅 (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "年化波动率 (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "最大回撤 (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "平均日成交量": st.column_config.NumberColumn(format="%.0f"),
                "最新日成交量": st.column_config.NumberColumn(format="%.0f"),
            },
        )
        st.download_button("下载当前筛选结果 CSV", data=display_metrics.to_csv(index=False).encode("utf-8-sig"), file_name="stockscope_screener.csv", mime="text/csv")

    elif selected_page == "股票筛选器":
        st.subheader("按历史收益与风险缩小观察范围")
        fc1, fc2, fc3 = st.columns(3)
        min_return = fc1.slider("最低区间涨跌幅 (%)", min_value=-100, max_value=200, value=-100, step=5)
        max_vol = fc2.slider("最高年化波动率 (%)", min_value=0, max_value=150, value=150, step=5)
        sort_by = fc3.selectbox("排序依据", ["区间涨跌幅 (%)", "年化波动率 (%)", "最大回撤 (%)", "平均日成交量"], index=0)
        filtered = metrics_active[
            (metrics_active["区间涨跌幅 (%)"].fillna(-999) >= min_return)
            & (metrics_active["年化波动率 (%)"].fillna(999) <= max_vol)
        ].copy()
        ascending = sort_by in ["年化波动率 (%)", "最大回撤 (%)"]
        filtered = filtered.sort_values(sort_by, ascending=ascending)
        st.write(f"符合条件的代码：**{len(filtered)}** 个")
        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "最新收盘价": st.column_config.NumberColumn(format="$%.2f"),
                "区间涨跌幅 (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "年化波动率 (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "最大回撤 (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "平均日成交量": st.column_config.NumberColumn(format="%.0f"),
                "最新日成交量": st.column_config.NumberColumn(format="%.0f"),
            },
        )
        st.download_button("下载筛选器结果 CSV", data=filtered.to_csv(index=False).encode("utf-8-sig"), file_name="stockscope_filtered_stocks.csv", mime="text/csv")
        st.markdown("**指标解释**：区间涨跌幅用时间范围内首个有效收盘价与最新收盘价计算；年化波动率为日收益率标准差乘以 √252；最大回撤为价格相对历史峰值的最大跌幅。")

    elif selected_page == "收益与风险":
        st.subheader("比较不同股票的收益与波动")
        if not compare_tickers:
            st.info("请在左侧选择至少一只股票。")
        else:
            compare_data = prices[prices["ticker"].isin(compare_tickers)].copy()
            if compare_data.empty:
                st.warning("所选代码暂时没有可用数据。")
            else:
                normalized = compare_data.sort_values("date").copy()
                normalized["基准化价格（起点=100）"] = normalized.groupby("ticker")["close"].transform(lambda s: s / s.dropna().iloc[0] * 100 if not s.dropna().empty else s)
                fig_line = px.line(normalized, x="date", y="基准化价格（起点=100）", color="ticker", title="基准化股价走势（各股票起点设为 100）", labels={"date": "日期", "ticker": "代码"})
                fig_line.update_layout(height=470, hovermode="x unified", yaxis_title="基准化价格", xaxis_title="日期", legend_title="代码")
                st.plotly_chart(fig_line, use_container_width=True)
            scat = metrics[metrics["代码"].isin(compare_tickers)].copy()
            if not scat.empty:
                fig_scatter = px.scatter(
                    scat, x="年化波动率 (%)", y="区间涨跌幅 (%)", color="类别", text="代码",
                    hover_data={"最新收盘价": ":.2f", "最大回撤 (%)": ":.2f", "平均日成交量": ":,.0f"},
                    title="收益—风险散点图",
                )
                fig_scatter.update_traces(textposition="top center", marker={"size": 12, "opacity": 0.8})
                fig_scatter.update_layout(height=450, xaxis_title="年化波动率 (%)", yaxis_title="区间涨跌幅 (%)", legend_title="分类")
                st.plotly_chart(fig_scatter, use_container_width=True)
            st.caption("历史收益与波动只用于描述过去，不是对未来表现的预测。")

    elif selected_page == "个股详情":
        st.subheader(f"{focus_ticker}｜{COMPANY_NAMES.get(focus_ticker, focus_ticker)} · {UNIVERSE.get(focus_ticker, '其他')} 个股详情")
        one = prices[prices["ticker"] == focus_ticker].sort_values("date").copy()
        one_metric = metrics[metrics["代码"] == focus_ticker]
        if one.empty:
            st.warning("该代码当前没有返回数据。")
        else:
            m = one_metric.iloc[0] if not one_metric.empty else {}
            a, b, c, dcol = st.columns(4)
            a.metric("最新收盘价", f"${m.get('最新收盘价', np.nan):,.2f}" if pd.notna(m.get("最新收盘价", np.nan)) else "—")
            b.metric("区间涨跌幅", pct(m.get("区间涨跌幅 (%)", np.nan)))
            c.metric("年化波动率", pct(m.get("年化波动率 (%)", np.nan)))
            dcol.metric("最大回撤", pct(m.get("最大回撤 (%)", np.nan)))
            price_fig = go.Figure()
            price_fig.add_trace(go.Scatter(x=one["date"], y=one["close"], mode="lines", name="调整后收盘价", line={"width": 2}))
            price_fig.update_layout(title=f"{focus_ticker} 历史收盘价", height=360, xaxis_title="日期", yaxis_title="价格（美元）", hovermode="x unified")
            st.plotly_chart(price_fig, use_container_width=True)
            vol_fig = px.bar(one, x="date", y="volume", title=f"{focus_ticker} 每日成交量", labels={"date": "日期", "volume": "成交量（股）"})
            vol_fig.update_layout(height=320, xaxis_title="日期", yaxis_title="成交量（股）")
            st.plotly_chart(vol_fig, use_container_width=True)

            with st.expander("可选：查看 Yahoo Finance 基本面字段（可能缺失）", expanded=False):
                with st.spinner("正在读取个股基本面字段……"):
                    info = get_ticker_info(focus_ticker)
                fundamental_fields = [
                    ("marketCap", "市值", money),
                    ("trailingPE", "市盈率（TTM）", lambda x: f"{x:.2f} 倍" if pd.notna(x) else "—"),
                    ("forwardPE", "预期市盈率", lambda x: f"{x:.2f} 倍" if pd.notna(x) else "—"),
                    ("priceToBook", "市净率", lambda x: f"{x:.2f} 倍" if pd.notna(x) else "—"),
                    ("revenueGrowth", "营收同比增长", lambda x: pct(x * 100) if pd.notna(x) else "—"),
                    ("profitMargins", "净利润率", lambda x: pct(x * 100) if pd.notna(x) else "—"),
                    ("returnOnEquity", "净资产收益率", lambda x: pct(x * 100) if pd.notna(x) else "—"),
                    ("totalRevenue", "总营收", money),
                    ("freeCashflow", "自由现金流", money),
                    ("fiftyTwoWeekHigh", "52 周最高价", lambda x: f"${x:,.2f}" if pd.notna(x) else "—"),
                    ("fiftyTwoWeekLow", "52 周最低价", lambda x: f"${x:,.2f}" if pd.notna(x) else "—"),
                ]
                if not info:
                    st.warning("Yahoo Finance 当前没有返回基本面数据。价格与成交量功能不受此项影响。")
                else:
                    fundamental_rows = []
                    for key, label, formatter in fundamental_fields:
                        value = info.get(key)
                        try:
                            val_num = float(value) if value is not None else np.nan
                            shown = formatter(val_num)
                        except (ValueError, TypeError):
                            shown = "—"
                        fundamental_rows.append({"指标": label, "数值": shown})
                    st.dataframe(pd.DataFrame(fundamental_rows), use_container_width=True, hide_index=True)
                    st.caption("基本面字段由 Yahoo Finance 返回，定义、更新时点和可用性可能因公司而异；正式研究时应回到公司申报文件核对。")

    elif selected_page == "方法与数据":
        st.subheader("数据来源与计算口径")
        st.markdown(
            """
            **数据来源**
            - 实时看盘：尝试获取 1m、5m、15m、30m 或 60m 分钟 K 线，展示蜡烛图、每根 K 线成交量、最新返回价格、时间戳状态及自选股分钟表。
            - 历史首页：全局股票搜索、指数快照、最近交易日涨跌榜、成交量榜和可编辑的会话自选股。
            - 历史行情：通过 Python 包 `yfinance` 读取 Yahoo Finance 历史日线数据。
            - 默认观察列表：本应用内置约 50 个美国股票与市场 ETF 代码，按便于课堂分析的类别整理，不是完整的美股名录，也不是官方行业分类。
            - 价格：使用 `auto_adjust=True`，因此下载字段 `Close` 为调整后收盘价；不同版本返回的数据字段可能不同。
            - 成交量：使用 Yahoo Finance 返回的 `Volume` 字段。对拆股、数据缺失或异常零值应额外检查。

            **计算口径**
            - 区间涨跌幅 =（区间最新收盘价 ÷ 区间首个有效收盘价 − 1）× 100。
            - 年化波动率 = 区间内日收益率标准差 × √252 × 100；短时间区间的估计可能不稳定。
            - 最大回撤 = 收盘价相对截至当日历史最高收盘价的最大跌幅。
            - 行业月度热力图 = 分类内股票月度收益率的简单平均；不是市值加权行业收益率。

            **重要限制**
            - 自选股保存在当前应用会话中；新会话或重启应用后可能重置。
            - 这是学习与分析原型，不是交易系统，也不构成投资建议。
            - Yahoo 数据可能延迟、缺失、修订或受请求限制。分钟 K 线和自动刷新不构成实时数据保证；时间戳差值不能单独证明真实传输延迟。自动刷新会增加请求频率，若出现限流可改为每 60 秒或手动刷新。
            - 使用 `yfinance` 不等于获得 Yahoo 行情的公开再分发授权。公开部署前应核对 Yahoo Finance 的适用条款，并确认课程对“开放数据/API”的要求。
            - 为满足课程研究规范，建议记录抓取日期、清洗步骤、变量定义、缺失值处理，并保存清洗后的数据集与代码版本。
            """
        )
        st.subheader("当前加载数据概况")
        data_summary = pd.DataFrame([
            {"项目": "数据行数", "值": f"{len(prices):,}"},
            {"项目": "不同代码数", "值": str(prices["ticker"].nunique())},
            {"项目": "起始日期", "值": str(prices["date"].min().date())},
            {"项目": "最后日期", "值": str(prices["date"].max().date())},
            {"项目": "缺失成交量比例", "值": f"{prices['volume'].isna().mean() * 100:.2f}%"},
        ])
        st.dataframe(data_summary, use_container_width=True, hide_index=True)
        st.download_button("下载已清洗日线数据 CSV", data=prices.to_csv(index=False).encode("utf-8-sig"), file_name="stockscope_daily_prices.csv", mime="text/csv")
st.markdown("---")
st.markdown("<div class='small-note'>StockScope · 课堂项目原型 · 请独立核实数据定义与使用权限；本工具不构成投资建议。</div>", unsafe_allow_html=True)
