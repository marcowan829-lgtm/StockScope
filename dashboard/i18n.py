"""English / Hong Kong Traditional Chinese UI strings.

Stock-market wording follows Hong Kong usage (HKEX, SFC and Futu 富途牛牛):
自選, 選股器, 實時報價, 升跌額, 升跌幅, 前收, 成交量, K線, 市值, 市盈率, 市賬率, 波幅.
"""
from __future__ import annotations

import streamlit as st

LANG_EN = "en"
LANG_ZH = "zh-HK"
LANGS = (LANG_EN, LANG_ZH)

# English source text is the lookup key. Missing keys fall back to English.
ZH: dict[str, str] = {}


def peek_lang() -> str:
    try:
        qp = st.query_params.get("lang", LANG_EN)
        if isinstance(qp, list):
            qp = qp[0] if qp else LANG_EN
        return qp if qp in LANGS else LANG_EN
    except Exception:
        return LANG_EN


def current_lang() -> str:
    try:
        if "lang" in st.session_state:
            return st.session_state.lang
    except Exception:
        pass
    return peek_lang()


def is_zh() -> bool:
    return current_lang() == LANG_ZH


def t(key: str, **kwargs) -> str:
    text = ZH.get(key, key) if is_zh() else key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text


def init_language() -> None:
    if "lang" not in st.session_state:
        st.session_state.lang = peek_lang()
    if "lang_pills" not in st.session_state:
        st.session_state.lang_pills = "繁" if st.session_state.lang == LANG_ZH else "EN"


def _on_lang_change() -> None:
    picked = st.session_state.get("lang_pills")
    st.session_state.lang = LANG_ZH if picked == "繁" else LANG_EN
    st.query_params["lang"] = st.session_state.lang


def render_language_toggle() -> None:
    st.pills(
        "Language",
        ["EN", "繁"],
        key="lang_pills",
        on_change=_on_lang_change,
        label_visibility="collapsed",
        help="English / 繁體中文",
    )


def lang_key(name: str) -> str:
    """Widget key that rebuilds labels when the language changes.

    Streamlit selectboxes keep the last formatted option text if the key is
    unchanged, so each language gets its own key. The selected value is copied
    across so the choice itself is preserved.
    """
    wk = f"{name}__{current_lang()}"
    if wk not in st.session_state:
        for lang in LANGS:
            other = f"{name}__{lang}"
            if other != wk and other in st.session_state:
                st.session_state[wk] = st.session_state[other]
                break
        else:
            if name in st.session_state:
                st.session_state[wk] = st.session_state[name]
    return wk


def plotly_font() -> str:
    if is_zh():
        return "Microsoft JhengHei, PingFang HK, Noto Sans TC, Trebuchet MS, sans-serif"
    return "Trebuchet MS, Segoe UI, sans-serif"


def language_css() -> str:
    family = (
        '-apple-system, BlinkMacSystemFont, "PingFang HK", "PingFang TC", '
        '"Microsoft JhengHei", "Noto Sans TC", "Trebuchet MS", Roboto, Ubuntu, sans-serif'
    )
    extra = ""
    if is_zh():
        extra = """
  .watchlist-group-title { text-transform: none; letter-spacing: 0.02em; font-size: 0.82rem; }
  div.st-key-nav_pills [data-testid="stMarkdownContainer"] p { font-size: 0.88rem; }
"""
    return f"""
<style>
  html, body, [data-testid="stAppViewContainer"], .stApp {{
    font-family: {family};
  }}
  div.st-key-lang_pills {{ min-width: 5.5rem; }}
  div.st-key-lang_pills [data-testid="stButtonGroup"] {{
    background: #f0f3fa;
    border: 1px solid #e0e3eb;
    border-radius: 999px;
    padding: 2px;
    gap: 0;
  }}
  div.st-key-lang_pills button {{
    min-height: 1.85rem !important;
    padding: 0.12rem 0.55rem !important;
    border-radius: 999px !important;
    font-weight: 750 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.02em;
  }}
  {extra}
</style>
"""


# ---------------------------------------------------------------------------
# Navigation, search, watchlist
# ---------------------------------------------------------------------------
ZH.update({
    "StockScope · Stock market for beginner": "StockScope · 股市入門",
    "StockScope Learn | Beginner Stock Academy": "StockScope 學習｜股票入門學堂",
    "Home": "首頁",
    "Market Overview": "市場概覽",
    "Screener": "選股器",
    "Live Quotes": "實時報價",
    "Returns & Risk": "回報與風險",
    "Stock Research": "個股研究",
    "Search": "搜尋",
    "Search stocks or indices": "搜尋股票或指數",
    "Search a ticker or company in the starter list, or a main US index such as SPX.":
        "搜尋入門名單內的股份代號或公司名稱，或主要美股指數如 SPX。",
    "Matches": "搜尋結果",
    "Open": "開啟",
    "Type a ticker or company name, for example AAPL or Apple.":
        "請輸入股份代號或公司名稱，例如 AAPL 或蘋果。",
    "No match in the starter list. Try a US ticker such as AAPL, MSFT, or SPX.":
        "入門名單沒有相符項目。請試試美股代號，例如 AAPL、MSFT 或 SPX。",
    "Watchlist": "自選",
    "{n_idx} indices · {n_stocks} stocks & funds": "{n_idx} 隻指數 · {n_stocks} 隻股票及基金",
    "Add a company or fund to your watchlist": "將公司或基金加入自選",
    "Add ticker": "加入代碼",
    "Name or ticker, e.g. NVDA": "名稱或代號，例如 NVDA",
    "Add symbol": "加入自選",
    "Could not add that symbol.": "未能加入該代碼。",
    "Market indices": "市場指數",
    "Stocks & funds": "股票及基金",
    "Manage watchlist": "管理自選",
    "Remove": "移除",
    "Remove from watchlist": "移出自選",
    "Your list starts here. Use ＋ to add a company or fund.": "自選由這裏開始。按 ＋ 加入公司或基金。",
    "Select a row to update the chart. Yahoo Finance quotes may be delayed.":
        "點選列項以更新圖表。Yahoo Finance 報價或會延遲。",
    "Add {proxy} (tracks this index) to Watchlist": "將 {proxy}（追蹤此指數）加入自選",
    "Open {name} page": "開啟 {name} 頁面",
    "Show {name} ({symbol}) on chart. Price {last}; daily change {change}.":
        "在圖表顯示 {name}（{symbol}）。最新價 {last}；當日升跌 {change}。",
    " Selected.": " 已選取。",
    "Currently shown on the chart": "目前顯示於圖表",
    "Show {symbol} on the chart": "在圖表顯示 {symbol}",
    "{ticker} already sits in Indices.": "{ticker} 已在指數一欄。",
    "{ticker} is already on your watchlist.": "{ticker} 已在自選內。",
    "Added {ticker} to Watchlist.": "已將 {ticker} 加入自選。",
    "Add this symbol to Watchlist": "將此代碼加入自選",
    "Add {proxy} to Watchlist": "將 {proxy} 加入自選",
})

# ---------------------------------------------------------------------------
# Chart controls and quotes
# ---------------------------------------------------------------------------
ZH.update({
    "Line": "線圖",
    "Candle": "K線",
    "Area": "面積圖",
    "Baseline": "基準線",
    "Chart type": "圖表類型",
    "Range": "週期",
    "All Time": "全部",
    "1 month": "1個月",
    "3 months": "3個月",
    "6 months": "6個月",
    "1 year": "1年",
    "2 years": "2年",
    "5 years": "5年",
    "point": "點",
    "USD": "美元",
    "Add ＋": "加入 ＋",
    "Open stock details": "開啟個股詳情",
    "Loading chart…": "正在載入圖表…",
    "Loading index chart…": "正在載入指數圖表…",
    "Loading index quotes…": "正在載入指數報價…",
    "Updating quotes…": "正在更新報價…",
    "No bars for this range yet. Markets may be closed, or Yahoo did not return data.":
        "此週期暫未有K線。市場或已休市，或 Yahoo 未有傳回數據。",
    "Range {range} · last bar {as_of}. Regular US hours only — nights, weekends, and holidays are hidden so the line stays continuous. Yahoo Finance / yfinance; may be delayed.":
        "週期 {range} · 最新一根K線 {as_of}。只顯示美股正常交易時段——夜市、週末及假期已隱藏，令走勢保持連續。數據來自 Yahoo Finance / yfinance，或會延遲。",
    "Stock market for beginner.": "股市入門。",
    "US stock market main indices": "美股主要指數",
    "Weekend: the regular US session is usually closed": "週末：美股正常交易時段一般休市",
    "Pre-market (clock estimate)": "盤前（按時鐘估算）",
    "Regular session (clock estimate)": "正常交易時段（按時鐘估算）",
    "After hours (clock estimate)": "盤後（按時鐘估算）",
    "Outside the regular session": "非正常交易時段",
    "{session} · quotes via Yahoo Finance, may be delayed.": "{session} · 報價來自 Yahoo Finance，或會延遲。",
    "Back to home": "返回首頁",
    "Full chart": "全圖",
    "Exit full chart": "退出全圖",
    "Full chart uses the same data as the index page. Weekends and closed hours stay hidden. Yahoo Finance; may be delayed.":
        "全圖使用與指數頁相同的數據。週末及休市時段保持隱藏。Yahoo Finance，或會延遲。",
    "Same four chart types as Home. Closed-market hours are hidden so the line stays continuous.":
        "圖表類型與首頁相同。休市時段已隱藏，令走勢保持連續。",
    "Session open": "即市開市",
    "Session high": "即市最高",
    "Session low": "即市最低",
    "Range open": "區間開市",
    "Range high": "區間最高",
    "Range low": "區間最低",
    "Prev close": "前收",
    "What this index is": "這是甚麼指數",
    "How it has moved": "近期走勢",
    "5-year range": "5年高低區間",
    "Low {lo}": "最低 {lo}",
    "Last {last}": "最新 {last}",
    "High {hi}": "最高 {hi}",
    "The other US indices": "其他美股指數",
    "Index": "指數",
    "Last": "最新價",
    "Chg%": "升跌幅",
    "Start = 100": "起始＝100",
    "Each line starts at 100 one year ago, so you can compare path, not the raw index level.":
        "每條線在一年前由100起計，方便比較走勢，而非比較指數點位。",
    "Names inside this index": "指數成分例子",
    "{proxy} is a fund that tracks {display}. The names below are well-known members, not a complete list.":
        "{proxy} 是追蹤 {display} 的基金。下列為常見成分股，並非完整名單。",
    "How to read this page": "如何閱讀本頁",
    "- **Full chart** hides the notes and enlarges the same quote chart.\n"
    "- **＋ {proxy}** adds a fund that follows this index to your watchlist. You cannot buy the index itself.\n"
    "- Header change is versus the **previous close**, not versus the left edge of the chart.\n"
    "- This is a classroom summary, not a trading terminal.":
        "- **全圖**會隱藏說明並放大同一報價圖表。\n"
        "- **＋ {proxy}** 把追蹤此指數的基金加入自選。指數本身不能直接買賣。\n"
        "- 頁頂升跌是對比**前收**，不是對比圖表左端。\n"
        "- 這是課堂摘要，並非交易終端機。",
    "Close: %{y:,.2f}<extra></extra>": "收市：%{y:,.2f}<extra></extra>",
    "Volume: %{y:,.0f}<extra></extra>": "成交量：%{y:,.0f}<extra></extra>",
    "Volume": "成交量",
})

# ---------------------------------------------------------------------------
# Indices, sectors, company names
# ---------------------------------------------------------------------------
ZH.update({
    "S&P 500": "標普500",
    "NASDAQ 100": "納斯達克100",
    "Dow Jones": "道瓊斯",
    "Broad view of large US companies": "涵蓋美國大型公司的廣泛指標",
    "Largest non-financial Nasdaq companies": "納斯達克最大的非金融公司",
    "30 major US industrial companies": "30間主要美國工業公司",
    "About 500 large US companies": "約500間美國大型公司",
    "About 100 large non-financial Nasdaq names": "約100間納斯達克大型非金融公司",
    "30 large US companies": "30間美國大型公司",
    "The S&P 500 is a single number that follows 500 large companies listed in the United States. When this number rises, that slice of the market is generally up; when it falls, that slice is generally down. You cannot buy the index itself. A fund such as SPY is a common way to follow it in a brokerage account.":
        "標普500是追蹤約500間在美國上市大型公司的指數。指數上升，表示這批股份整體偏升；指數下跌，表示整體偏跌。指數本身不能直接買賣。常見做法是透過 SPY 等交易所買賣基金（ETF），在證券戶口跟蹤。",
    "The Nasdaq 100 follows the largest non-financial companies listed on Nasdaq. Technology names have a heavy weight, so this index can move more than the S&P 500 on tech news. A fund such as QQQ is a common way to follow it.":
        "納斯達克100追蹤在納斯達克上市、市值最大的非金融公司。科技股權重較高，科技消息往往令這指數的波幅大於標普500。常見做法是透過 QQQ 等交易所買賣基金跟蹤。",
    "The Dow Jones Industrial Average follows 30 well-known US companies. It is a short list, so one member can move the number more than in the S&P 500. A fund such as DIA is a common way to follow it.":
        "道瓊斯工業平均指數追蹤30間知名美國公司。成分股數目較少，單一公司對指數的影響可以大於標普500。常見做法是透過 DIA 等交易所買賣基金跟蹤。",
    "Technology": "科技",
    "Tech / consumer": "科技／消費",
    "Financials": "金融",
    "Health care": "醫療保健",
    "Consumer": "消費",
    "Consumer / media": "消費／媒體",
    "Industrials": "工業",
    "Energy": "能源",
    "Market benchmark": "市場基準",
    "Other": "其他",
    "Apple Inc": "蘋果",
    "Microsoft": "微軟",
    "NVIDIA": "英偉達",
    "Alphabet A": "字母控股A",
    "Amazon": "亞馬遜",
    "Meta Platforms": "元平台",
    "Broadcom": "博通",
    "Oracle": "甲骨文",
    "Salesforce": "賽富時",
    "AMD": "超微半導體",
    "Qualcomm": "高通",
    "Intel": "英特爾",
    "Cisco": "思科",
    "Adobe": "奧多比",
    "IBM": "IBM",
    "JPMorgan Chase": "摩根大通",
    "Bank of America": "美國銀行",
    "Goldman Sachs": "高盛",
    "Morgan Stanley": "摩根士丹利",
    "Visa": "威士",
    "Mastercard": "萬事達",
    "PayPal": "PayPal",
    "Berkshire Hathaway B": "伯克希爾哈撒韋B",
    "Eli Lilly": "禮來",
    "Johnson & Johnson": "強生",
    "UnitedHealth Group": "聯合健康",
    "AbbVie": "艾伯維",
    "Merck": "默沙東",
    "Pfizer": "輝瑞",
    "Intuitive Surgical": "直覺外科",
    "Walmart": "沃爾瑪",
    "Costco": "好市多",
    "Home Depot": "家得寶",
    "Nike": "耐克",
    "McDonald's": "麥當勞",
    "Coca-Cola": "可口可樂",
    "Procter & Gamble": "寶潔",
    "Walt Disney": "華特迪士尼",
    "Netflix": "奈飛",
    "Caterpillar": "卡特彼勒",
    "GE Aerospace": "通用電氣航空航天",
    "RTX": "RTX",
    "Honeywell": "霍尼韋爾",
    "UPS": "UPS",
    "Deere & Company": "迪爾",
    "Exxon Mobil": "埃克森美孚",
    "Chevron": "雪佛龍",
    "SLB": "斯倫貝謝",
    "SPDR S&P 500 ETF": "標普500 ETF",
    "Invesco Nasdaq-100 ETF": "納斯達克100 ETF",
    "SPDR Dow Jones ETF": "道瓊斯 ETF",
    "Apple": "蘋果",
    "Alphabet": "字母控股",
    "Tesla": "特斯拉",
    "S&P 500 ETF proxy": "標普500 ETF 代替品",
    "Nasdaq-100 ETF proxy": "納斯達克100 ETF 代替品",
    "Developed markets ETF proxy": "發達市場 ETF 代替品",
    "Emerging markets ETF proxy": "新興市場 ETF 代替品",
    "Japan equity ETF proxy": "日本股票 ETF 代替品",
    "China large-cap ETF proxy": "中國大型股 ETF 代替品",
    "Vanguard Total Bond Market ETF (US aggregate bonds)": "Vanguard 總債券市場 ETF（美國綜合債券）",
    "iShares 0-3 Month Treasury Bond ETF (short-term US Treasuries)": "iShares 0-3個月美國國債 ETF（短期美債）",
})

# ---------------------------------------------------------------------------
# Market tools
# ---------------------------------------------------------------------------
ZH.update({
    "The wider market at a glance: group heatmaps, leading stocks, daily movers and volume.":
        "一覽大市：行業熱力圖、領先股份、當日升跌股份及成交量。",
    "Find stocks by return, volatility and trading activity, then export your shortlist.":
        "按回報、波幅及交投篩選股票，再匯出候選名單。",
    "Follow intraday price, candles and volume, with a short list of symbols to monitor.":
        "跟進即市價格、K線及成交量，並監察一組代碼。",
    "Compare historical performance, volatility and drawdowns across stocks and ETFs.":
        "比較股票及交易所買賣基金的歷史表現、波幅及回撤。",
    "Explore one stock or index through price history, return metrics and company fundamentals.":
        "以價格走勢、回報數據及公司基本面研究一隻股票或指數。",
    "Look-back window": "回看區間",
    "Group filter": "分類篩選",
    "All groups": "全部分類",
    "Could not load daily history. Check the network or Yahoo Finance, then retry.":
        "未能載入日線歷史。請檢查網絡或 Yahoo Finance，然後重試。",
    "Loading the starter universe from Yahoo Finance…": "正在從 Yahoo Finance 載入入門名單…",
    "Symbols loaded": "已載入代碼",
    "Starter watch universe, not the whole US market.": "入門觀察名單，並非整個美股市場。",
    "Average return · {period}": "平均回報 · {period}",
    "Share with a positive return": "錄得正回報的比例",
    "Median annualized volatility": "年率化波幅中位數",
    "As of {date} · {period} · {n} starter symbols": "截至 {date} · {period} · {n} 隻入門代碼",
    "Not enough history in this window to draw the monthly heatmap.": "此區間歷史不足，未能繪製每月熱力圖。",
    "Today's movers in the starter list": "入門名單今日升跌股份",
    "Stocks watched": "觀察股份",
    "Up": "上升",
    "Down": "下跌",
    "Flat": "平市",
    "Gainers · top 10": "升幅榜 · 首10",
    "Losers · bottom 10": "跌幅榜 · 後10",
    "Day change": "當日升跌",
    "Not enough data for a gainer list.": "數據不足，未能列出升幅榜。",
    "Not enough data for a loser list.": "數據不足，未能列出跌幅榜。",
    "Volume leaders": "成交量領先",
    "Highest volume in the latest session": "最近一個交易時段成交量最高",
    "Shares": "股數",
    "%{y}: %{x:,.0f} shares<extra></extra>": "%{y}：%{x:,.0f} 股<extra></extra>",
    "Starter universe": "入門名單",
    "Ticker": "代碼",
    "Company": "公司",
    "Group": "分類",
    "Period return (%)": "期內回報（%）",
    "Ann. volatility (%)": "年率化波幅（%）",
    "Max drawdown (%)": "最大回撤（%）",
    "Avg volume": "平均成交量",
    "As of": "截至",
    "Download this table as CSV": "下載此表為 CSV",
    "Narrow the starter list by return and risk": "按回報與風險收窄入門名單",
    "Minimum period return (%)": "最低期內回報（%）",
    "Maximum annualized volatility (%)": "最高年率化波幅（%）",
    "Sort by": "排序",
    "Symbols that match: **{n}**": "符合條件的代碼：**{n}**",
    "Download screener CSV": "下載選股結果 CSV",
    "**What the numbers mean:** period return uses the first and last valid close in the window; "
    "annualized volatility is the daily-return standard deviation × √252; "
    "max drawdown is the worst drop from a peak close.":
        "**數字含義：**期內回報用區間內首個及最後一個有效收市價；"
        "年率化波幅為每日回報標準差 × √252；"
        "最大回撤是由高位收市價計起的最大跌幅。",
    "Compare return and volatility": "比較回報與波幅",
    "Symbols to compare": "比較代碼",
    "Up to about eight names keeps the chart readable.": "選約八隻以內，圖表較易閱讀。",
    "Pick at least one symbol.": "請至少選一隻代碼。",
    "No history for those symbols in this window.": "此區間沒有這些代碼的歷史數據。",
    "Rebased performance · {period}": "還原表現 · {period}",
    "Date": "日期",
    "Rebased (start = 100)": "還原（起始＝100）",
    "Rebased level (start of window = 100)": "還原水平（區間起始＝100）",
    "This is not the share price. Each series is rebased to 100 at the start of the window so you can compare percentage paths.":
        "這不是股價。每條序列在區間開始時還原為100，方便比較百分比走勢。",
    "Return vs risk": "回報對風險",
    "Past return and volatility describe history. They are not a forecast.":
        "過往回報及波幅只描述歷史，並非預測。",
    "Symbol": "代碼",
    "Custom symbol": "自訂代碼",
    "History window": "歷史區間",
    "Loading this symbol…": "正在載入此代碼…",
    "Yahoo did not return history for this symbol.": "Yahoo 未有傳回此代碼的歷史數據。",
    "Last close": "最新收市",
    "Period return": "期內回報",
    "Ann. volatility": "年率化波幅",
    "Max drawdown": "最大回撤",
    "Daily OHLC candles. Weekends and holidays are hidden. Green = close ≥ open. Scale is zoomed to this window.":
        "每日開市／最高／最低／收市 K線。週末及假期已隱藏。綠色＝收市 ≥ 開市。縱軸已放大至此區間。",
    "Add to watchlist": "加入自選",
    "Open live quotes": "開啟實時報價",
    "Optional Yahoo fundamentals (often incomplete)": "Yahoo 基本面（往往不完整，可選）",
    "Reading fundamentals…": "正在讀取基本面…",
    "Market cap": "市值",
    "P/E (TTM)": "市盈率（TTM）",
    "Forward P/E": "預測市盈率",
    "Price / book": "市賬率",
    "Revenue growth": "營業額增長",
    "Profit margin": "溢利率",
    "Return on equity": "股本回報率",
    "Revenue": "營業額",
    "Free cash flow": "自由現金流",
    "52-week high": "52週最高",
    "52-week low": "52週最低",
    "Field": "項目",
    "Value": "數值",
    "Yahoo did not return fundamentals. Price and volume still work.":
        "Yahoo 未有傳回基本面。價格及成交量仍可使用。",
    "Confirm anything important in company filings. Yahoo fields vary by name and update schedule.":
        "重要資料請以公司披露文件核實。Yahoo 欄位因股份而異，更新時間亦不固定。",
    "Top 15 in this window": "此區間表現首15",
    "Period return": "期內回報",
    "Group monthly returns (0% = unchanged · equal-weighted inside each group)":
        "分類每月回報（0%＝不變 · 分類內平均加權）",
    "Month": "月份",
    "Monthly %": "每月%",
    "Group: %{y}<br>Month: %{x}<br>Avg return: %{z:.2f}%<extra></extra>":
        "分類：%{y}<br>月份：%{x}<br>平均回報：%{z:.2f}%<extra></extra>",
})

# ---------------------------------------------------------------------------
# Live quotes
# ---------------------------------------------------------------------------
ZH.update({
    "This is a classroom feed, not an execution quote.": "這是課堂行情，並非可執行報價。",
    "Bar size": "K線週期",
    "1 min": "1分鐘",
    "5 min": "5分鐘",
    "15 min": "15分鐘",
    "30 min": "30分鐘",
    "60 min": "60分鐘",
    "Auto refresh": "自動重新整理",
    "Manual": "手動",
    "Every 15s": "每15秒",
    "Every 30s": "每30秒",
    "Every 60s": "每60秒",
    "Include pre/post": "包括盤前／盤後",
    "↻ Refresh now": "↻ 立即重新整理",
    "Also watch (keep to six names to limit requests)": "同時監察（最多六隻，以免過多請求）",
    "Each row is the latest returned minute bar, not a time-and-sales print.":
        "每列是最新傳回的分鐘K線，並非逐筆成交。",
    "Refresh is how often this app asks again. It is not a promise of a live or 15-minute-delayed feed. "
    "Yahoo / yfinance can lag, skip bars, or throttle.":
        "重新整理只表示本應用再次請求的頻率，並不保證實時或延遲15分鐘行情。"
        "Yahoo / yfinance 可能滯後、缺K線或限流。",
    "New York time: {now} · {session} · auto refresh: {refresh}. "
    "The session label does not check exchange holidays.":
        "紐約時間：{now} · {session} · 自動重新整理：{refresh}。"
        "交易時段標籤並不核對交易所假期。",
    "Could not load minute bars. Network, Yahoo, or rate limits are the usual causes.":
        "未能載入分鐘K線。常見原因是網絡、Yahoo 或限流。",
    "Technical error": "技術錯誤",
    "{symbol} did not return {interval} bars. "
    "If the US session is closed, wait for the next trading day, or turn off pre/post and retry.":
        "{symbol} 未有傳回 {interval} K線。"
        "若美股已休市，請待下一個交易日，或關閉盤前／盤後後重試。",
    "Latest bar timestamp is slightly ahead of this clock; check again on the next refresh":
        "最新K線時間略早於本機時鐘；請待下次重新整理再看",
    "Latest bar timestamp is close to now (not a live-data guarantee)":
        "最新K線時間接近現在（並非實時數據保證）",
    "Latest bar looks stale; the session may be closed or the feed may have paused":
        "最新K線看似過時；可能已休市或行情暫停",
    "{status} · bar time {bar_time} · about {age:.1f} minutes from this clock.":
        "{status} · K線時間 {bar_time} · 距本機時鐘約 {age:.1f} 分鐘。",
    "Last returned price": "最新傳回價格",
    "Close of the minute bar, not a trade print.": "分鐘K線收市價，並非逐筆成交價。",
    "Vs previous bar": "對上一根K線",
    "Bar volume": "K線成交量",
    "Bars returned": "已傳回K線數",
    "Intraday OHLC candles including pre/post-market hours. ":
        "即市開市／最高／最低／收市 K線，包括盤前／盤後。",
    "Intraday OHLC candles on regular US hours only (nights hidden). ":
        "即市開市／最高／最低／收市 K線，只顯示美股正常交易時段（夜市已隱藏）。",
    "Green = that bar closed ≥ open. This is a classroom feed, not an exchange plot.":
        "綠色＝該根K線收市 ≥ 開市。這是課堂行情，並非交易所圖表。",
    "Latest minute rows": "最新分鐘數據",
    "Download minute CSV": "下載分鐘 CSV",
    "Watchlist bars": "自選K線",
    "Pick at least one extra symbol above.": "請在上方至少再選一隻代碼。",
    "No data": "沒有數據",
    "Fresh timestamp": "時間較新",
    "Check update status": "請核對更新狀態",
    "Request failed": "請求失敗",
    "Bar chg (%)": "K線升跌幅（%）",
    "Bar time (ET)": "K線時間（美東）",
    "Age (min)": "時差（分鐘）",
    "Status": "狀態",
    "Age is only the gap between the bar timestamp and this clock, not the true exchange-to-screen delay.":
        "時差只是K線時間與本機時鐘的差距，並非真正的交易所至畫面延遲。",
})

# ---------------------------------------------------------------------------
# Footer, methods, learning launcher
# ---------------------------------------------------------------------------
ZH.update({
    "StockScope · classroom prototype · verify definitions and data rights yourself. "
    "This tool is not investment advice.":
        "StockScope · 課堂原型 · 請自行核實定義及數據權利。本工具並不構成投資建議。",
    "Your study path": "你的學習路徑",
    "Build your market knowledge, one lesson at a time.": "一課一課建立市場知識。",
    "{done} of 8 lessons completed": "已完成 8 課中的 {done} 課",
    "Your progress is saved in this browser session.": "進度保存在今次瀏覽器工作階段。",
    "Study path": "學習路徑",
    "Open your study path": "開啟學習路徑",
    "Back to markets": "返回市場",
    "Start here": "由這裏開始",
    "Data & methods": "數據與方法",
    "10–12 min": "10–12分鐘",
    "8–10 min": "8–10分鐘",
    "15–25 min": "15–25分鐘",
    "25–35 min": "25–35分鐘",
    "15–20 min": "15–20分鐘",
    "6–8 min": "6–8分鐘",
    "24 questions": "24題",
    "Sources & downloads": "來源與下載",
    "Learning Home": "學習主頁",
    "01 Stock Market Basics": "01 股票市場基礎",
    "02 Reading Stock Charts": "02 閱讀股票圖表",
    "02A Candlestick Patterns": "02A K線形態",
    "02B Technical Indicators": "02B 技術指標",
    "03 How Orders Work": "03 買賣盤如何運作",
    "04 Researching a Company": "04 研究一間公司",
    "05 Why Stock Prices Move": "05 股價為何變動",
    "06 Risk & Investor Protection": "06 風險與投資者保障",
    "Final Quiz": "綜合測驗",
    "Data & Methods": "數據與方法",
    "Stock Market Basics": "股票市場基礎",
    "Reading Stock Charts": "閱讀股票圖表",
    "Candlestick Patterns": "K線形態",
    "Technical Indicators": "技術指標",
    "How Orders Work": "買賣盤如何運作",
    "Researching a Company": "研究一間公司",
    "Why Stock Prices Move": "股價為何變動",
    "Risk & Investor Protection": "風險與投資者保障",
})

# ---------------------------------------------------------------------------
# Chart help
# ---------------------------------------------------------------------------
ZH.update({
    "How to read this chart": "如何閱讀此圖表",
    "Price chart: line": "價格圖：線圖",
    "Price chart: candles and volume": "價格圖：K線及成交量",
    "Price chart: area": "價格圖：面積圖",
    "Price chart: baseline": "價格圖：基準線",
    "Group monthly returns": "分類每月回報",
    "Top performers in this window": "此區間表現領先",
    "Daily movers: highest changes": "當日升跌：升幅最大",
    "Daily movers: lowest changes": "當日升跌：跌幅最大",
    "Trading volume leaders": "成交量領先",
    "Compare performance: everyone starts at 100": "比較表現：全部由100起計",
    "Return versus price swings": "回報對價格上落",
    "Intraday candles: one trading day": "即市K線：一個交易日",
    "Historical daily candles": "歷史日K線",
    "MADE-UP EXAMPLE · Follow the drawing notes: 1 → 2 → 3.":
        "虛構例子 · 請按圖註 1 → 2 → 3 閱讀。",
    "Annotated example. {summary} Follow the three numbered drawing notes.":
        "註解例子。{summary} 請跟從三個編號圖註。",
    "Read more · step-by-step explanation": "閱讀更多 · 逐步說明",
    "What am I looking at?": "我在看甚麼？",
    "How to read it": "如何閱讀",
    "A simple example": "簡單例子",
    "What can I learn?": "可以學到甚麼？",
    "Keep in mind": "請記住",
    "Want to learn more?": "想學多一點？",
    "Lesson {lesson} →": "課堂 {lesson} →",
    "Open Lesson {lesson}": "開啟課堂 {lesson}",
    "Close with ×, press Esc, or click outside the panel to return to your chart.":
        "按 ×、Esc，或點擊面板外，即可返回圖表。",
    "How to read: {title}": "如何閱讀：{title}",
    "**Bars underneath:** when volume is available, these count shares traded in each time block. Taller means more shares traded. Green/red compares that block's close with its open, rather than the whole line's reference. Index volume can be missing or zero.":
        "**下方柱狀：**有成交量時，這些柱代表每個時段成交的股數。越高代表成交越多。綠／紅是比較該時段收市與開市，而非整條線的參考價。指數成交量可以缺失或為零。",
    "Explore prices, timeframes and volume, one step at a time.": "逐步認識價格、週期及成交量。",
    "Learn to recognize candle shapes and read them in context.": "學習辨認K線形態，並在市況中閱讀。",
    "Build confidence reading prices, timeframes and volume.": "建立閱讀價格、週期及成交量的信心。",
    "Learn what chart values and price changes tell you.": "了解圖表數字及價格變動說明甚麼。",
    "Understand percentage returns and how market groups fit together.": "理解百分比回報，以及市場分類如何組成。",
    "Learn how returns help compare stocks over the same period.": "學習如何用回報在同一期間比較股票。",
    "Explore news, expectations and other reasons prices change.": "認識消息、預期及其他令價格變動的原因。",
    "Explore why prices fall and what evidence to check next.": "認識價格下跌的原因，以及下一步應核對甚麼證據。",
    "Learn what trading volume shows alongside price.": "了解成交量在價格以外說明甚麼。",
    "Understand returns, benchmarks and percentage comparisons.": "理解回報、基準及百分比比較。",
    "Explore different kinds of risk and ways to recognize them.": "認識不同風險，以及如何辨認。",
    "Read candle bodies and wicks, then explore common patterns.": "閱讀K線實體及影線，再認識常見形態。",
    "Explore candle structures, trend context and confirmation.": "認識K線結構、趨勢背景及確認。",
})

ZH.update({
    "This line shows how one stock's price, or one index's level, changed over time. An index is a score that follows a group of stocks, rather than a share you can buy directly.":
        "這條線顯示一隻股票的價格，或一隻指數的點位，如何隨時間變動。指數是追蹤一組股票的分數，並不是可以直接買入的股份。",
    "Read from left to right: earlier times are on the left, later times on the right. The numbers on the side show the price or index level.":
        "由左至右閱讀：較早時間在左，較後時間在右。旁邊數字是價格或指數點位。",
    "A rising section means the value increased during that part of the chart. A falling section means it decreased. Hover over the line to read a value and time.":
        "上升段表示該段時間數值上升；下跌段表示下跌。把游標移到線上可看到數值及時間。",
    "The whole line's green/red colour compares its latest value with the previous close when available, otherwise the first value shown. A red line can still have rising sections.":
        "整條線的綠／紅，是比較最新值與前收（若有），否則與圖上第一個值比較。紅線仍然可以有上升段。",
    "1D means one trading day; 5D means five trading days; 1M means one month; 6M means six months; 1Y means one year. All Time uses the available history.":
        "1D 是一個交易日；5D 是五個交易日；1M 是一個月；6M 是六個月；1Y 是一年。「全部」使用可取得的歷史。",
    "A stock moves from $100 on the left to $110 on the right. Its price rose $10, or 10%, during that window. An index moving from 7,000 to 7,070 rose 70 points, or 1%.":
        "一隻股票由左面 100 美元升至右面 110 美元，期內升了 10 美元，即 10%。指數由 7,000 點升至 7,070 點，即升 70 點或 1%。",
    "Spot the overall direction, turning points, and when larger moves happened. Use the numbers as well as the shape.":
        "找出整體方向、轉折點，以及較大升跌出現的時間。數字與形態都要看。",
    "The vertical scale is zoomed in, so a small change can look large. The change beside the chart heading is against the previous close, which can differ from the change across your selected window.":
        "縱軸已放大，細小變動看起來可以很大。圖表標題旁的升跌是對比前收，可能與所選區間的升跌不同。",
    "Each candle summarises prices during one time block. This could be five minutes, one day, or one week, depending on the selected range.":
        "每根K線總結一個時段的價格。可以是五分鐘、一日或一週，視乎所選週期。",
    "Read the time along the bottom and the price or index level on the side. Hover over a candle to see its four numbers.":
        "底部是時間，旁邊是價格或指數點位。把游標移到K線上可看到四個數字。",
    "Open is the price at the start of the block. Close is the price at its end. High is the highest price reached; Low is the lowest.":
        "開市是時段開始時的價格，收市是結束時的價格。最高是期間最高價；最低是期間最低價。",
    "The thick body runs between open and close. The thin lines, called wicks, reach the high and low.":
        "粗的實體連接開市與收市。幼線稱為影線，伸延至最高及最低。",
    "Green means the close was at least as high as the open. Red means it was lower. This compares the start and end of that candle, not necessarily the previous day.":
        "綠色表示收市不低於開市；紅色表示收市低於開市。這是比較該根K線的開與收，不一定是對比前一日。",
    "When available, bars below the candles show volume: the number of shares traded in each block. Taller bars mean more shares changed hands.":
        "若有數據，K線下方的柱是成交量：每個時段成交的股數。柱越高，代表轉手股數越多。",
    "A candle opens at $100, reaches a high of $105 and a low of $98, then closes at $103. Its body is green, from $100 to $103; its wicks reach $98 and $105.":
        "一根K線開市 100 美元，最高 105 美元，最低 98 美元，收市 103 美元。實體為綠色，由 100 至 103 美元；影線伸至 98 及 105 美元。",
    "See both the direction and the range of movement inside each time block. Compare nearby volume bars to see when trading was busier.":
        "同時看每個時段的方向及上落幅度。比較附近成交量柱，可知何時交投較活躍。",
    "A green candle can still be below yesterday's close. A large candle or busy volume bar does not tell you what happens next. Index values are points, not a stock's dollar price; index volume can be missing or zero.":
        "綠色K線仍可以低於昨日收市。大K線或高成交量並不告訴你下一步會怎樣。指數以點計，不是股票美元價；指數成交量可以缺失或為零。",
    "This is a price line with the space beneath it shaded. The top edge of the shaded area is the value to read.":
        "這是一條價格線，下方有陰影。陰影的上沿才是要讀的數值。",
    "Follow the top edge from left to right to see how the price or index level changed. Read its value using the scale on the side.":
        "沿上沿由左至右看價格或指數如何變動。用旁邊的刻度讀數。",
    "The shading makes the shape easier to see. It does not show how many shares were bought or how much money entered the market.":
        "陰影只是方便看出形態，並不代表買了多少股或有多少資金入市。",
    "Green/red compares the latest value with the previous close when available, otherwise the first value in this window. Hover to see an exact value and time.":
        "綠／紅是比較最新值與前收（若有），否則與本區間第一個值比較。把游標移上去可看精確數值及時間。",
    "If the top edge rises from $50 to $55, the stock rose $5, or 10%, across those two points. A larger shaded area does not mean more money was invested.":
        "若上沿由 50 美元升至 55 美元，股票在這兩點之間升了 5 美元，即 10%。陰影面積較大，並不代表投入了更多資金。",
    "Quickly see the overall direction and periods of larger price movement.":
        "快速看出整體方向，以及價格上落較大的時段。",
    "The scale is zoomed in rather than starting at zero. Compare the numbers, not the amount of shaded space. Historical movement does not predict the next move.":
        "刻度已放大，並非由零起計。請比較數字，而非陰影面積。歷史走勢並不能預測下一步。",
    "This view compares the price with a reference level, called the baseline. Here that is the previous close when available, otherwise the first price in this window.":
        "此視圖把價格與一條參考水平（基準線）比較。這裏的基準線是前收（若有），否則是本區間第一個價格。",
    "Find the horizontal baseline. Green sections are above it; red sections are below it.":
        "找出橫向基準線。綠色在線上，紅色在線下。",
    "Read time along the bottom and price or index points on the side. Hover to check exact values.":
        "底部是時間，旁邊是價格或指數點位。把游標移上去核對精確數值。",
    "Crossing the baseline only means the value moved from one side of this reference to the other. It is not a buy or sell instruction.":
        "穿越基準線只表示數值由參考的一邊走到另一邊，並不是買入或賣出指示。",
    "Yesterday's close was $100. A price of $102 appears above the baseline in green; $98 appears below it in red. Moving from $98 to $99 is a rise, even though both values remain red.":
        "昨日收市為 100 美元。102 美元在基準線之上顯示綠色；98 美元在線下顯示紅色。由 98 升至 99 仍是上升，即使兩點都保持紅色。",
    "See when the price was above or below the reference and how far it moved away.":
        "看出價格何時高於或低於參考，以及偏離多遠。",
    "The baseline can be outside the visible price range. The reference is not a guaranteed fair price or a level the stock must return to.":
        "基準線可以在可見價格範圍之外。參考價並非保證的合理價，股票也不一定會回到該水平。",
})

ZH.update({
    "This colour grid compares groups of stocks month by month. A return is the percentage change in value over a period.":
        "這張顏色網格按月比較各類股票。回報是一段時間內價值的百分比變動。",
    "Choose a group from the labels down the left, then a month along the bottom. Their meeting point is one coloured cell.":
        "由左邊標籤選一個分類，再由底部選一個月份。相交的一格就是一個顏色格。",
    "Green means an average gain; red means an average loss. Colours near the middle of the colour scale mean a smaller change near zero. Use the colour key and hover for the exact percentage.":
        "綠色代表平均上升；紅色代表平均下跌。接近色階中間的顏色表示接近零的較小變動。請看色階，並把游標移上去看精確百分比。",
    "Each cell is the simple average of available stock returns in that group: each included stock counts equally. The benchmark row contains funds that follow the wider market.":
        "每一格是該分類內可用股票回報的簡單平均：每隻計入的股票權重相同。基準列是跟蹤大市的基金。",
    "Two stocks in a group return +10% and −2% in a month. Their average is +4%, so that group's cell shows a 4% gain for that month. It does not mean every stock gained 4%.":
        "同一分類兩隻股票某月分別錄得 +10% 及 −2%。平均為 +4%，該格便顯示該月升 4%。這不代表每隻股票都升了 4%。",
    "Compare which groups rose or fell in the same month, and whether a group's results changed from month to month.":
        "比較同一個月哪些分類升或跌，以及同一分類是否每月結果不同。",
    "A monthly percentage is not the whole-window return; the latest month may still be in progress. These are this app's stock groups, not official sector indices. Missing data is not a zero return.":
        "每月百分比不是整個區間的回報；最近一個月可能尚未完結。這些是本應用的股票分類，並非官方行業指數。缺失數據並不代表零回報。",
    "These bars rank up to 15 stocks or funds by their percentage price change over the selected look-back window.":
        "這些柱按所選回看區間的價格百分比變動，排列最多15隻股票或基金。",
    "The short names on the side are ticker symbols: for example, AAPL means Apple. The bottom scale shows percentage change.":
        "旁邊短名是股份代號：例如 AAPL 即蘋果。底部刻度是百分比變動。",
    "A bar to the right of zero is a gain and is green. A bar to the left is a loss and is red. Compare lengths, then hover for the exact result.":
        "零的右邊是升幅，顯示綠色；左邊是跌幅，顯示紅色。先比較長度，再把游標移上去看精確結果。",
    "Check the selected window first: a one-month result and a one-year result describe different periods.":
        "先核對所選區間：一個月與一年的結果描述的是不同時段。",
    "A +20% bar means a price rose from $100 to $120 over that window. A +5% bar means $100 became $105. This does not mean the first stock costs more per share.":
        "+20% 的柱表示該區間價格由 100 美元升至 120 美元；+5% 表示 100 美元變成 105 美元。這不代表第一隻股票的每股價格較高。",
    "See which names in the displayed list had the highest returns during the same window.":
        "看出顯示名單中，同一區間回報最高的代碼。",
    "Top means highest in the available list, not guaranteed profit. If every result is negative, even the top names can show losses. A high past return is not a forecast.":
        "「領先」只是在現有名單中最高，並非保證獲利。若全部結果都是負數，領先者也可以是虧損。過往高回報並非預測。",
    "This chart shows up to 10 stocks with the highest latest daily percentage changes in the app's starter list.":
        "此圖顯示入門名單中，最新每日升跌幅最高的最多10隻股票。",
    "Each row is a stock, identified by its ticker symbol. The percentage compares its latest daily close with its previous trading day's close.":
        "每一列是一隻股票，以股份代號識別。百分比是比較最新每日收市與上一個交易日收市。",
    "Green/right of zero means a rise; red/left of zero means a fall. Hover to read the exact percentage.":
        "綠色／零的右邊是上升；紅色／零的左邊是下跌。把游標移上去讀精確百分比。",
    "These are daily changes, even when the page's look-back window is one year. Check the page's data date.":
        "即使頁面回看區間是一年，這些仍是每日升跌。請核對頁面的數據日期。",
    "A stock closes at $50, then $51 the next trading day. Its daily change is +2%. That is different from its return over the whole year.":
        "一隻股票收市 50 美元，下一個交易日收市 51 美元，當日升跌為 +2%。這與全年回報不同。",
    "Find stocks with the strongest latest daily changes in this list, then investigate what happened.":
        "找出此名單中最新每日升跌最大的股票，再查發生了甚麼事。",
    "Highest is a ranking, not a promise that all the bars are positive. A move does not explain its cause or predict tomorrow's price.":
        "「最高」只是排名，並不保證所有柱都是正數。升跌並不解釋原因，也不能預測明日價格。",
    "This chart shows up to 10 stocks with the lowest latest daily percentage changes in the app's starter list.":
        "此圖顯示入門名單中，最新每日升跌幅最低的最多10隻股票。",
    "Read the ticker symbol on the side and the percentage change on the bottom. The comparison is with the previous trading day's close.":
        "旁邊是股份代號，底部是百分比變動。比較基準是上一個交易日收市。",
    "A red bar to the left of zero is a loss. A green bar to the right is a gain. Hover to see the exact number.":
        "零左邊的紅柱是下跌；右邊的綠柱是上升。把游標移上去看精確數字。",
    "Lowest means the weakest changes within this list. On a strong day, a stock can be in this ranking while still showing a small gain.":
        "「最低」是此名單內最弱的變動。在升市日子，上榜股份仍可以錄得小幅上升。",
    "A price falls from $80 to $76 between daily closes. It lost $4, which is 5% of $80, so its bar is −5%.":
        "每日收市由 80 美元跌至 76 美元，跌了 4 美元，即 80 美元的 5%，柱便是 −5%。",
    "Spot stocks with weaker daily results and compare how large their moves were.":
        "找出當日較弱的股票，並比較其升跌幅度。",
    "A fall does not automatically mean a stock is cheap, or that it must bounce back. This chart covers the starter list rather than every stock in the market.":
        "下跌並不自動代表股票便宜，也不代表一定反彈。此圖只覆蓋入門名單，並非市場所有股票。",
    "Volume counts the number of shares traded. These bars show the busiest stocks in the starter list's latest available daily session.":
        "成交量計算成交股數。這些柱顯示入門名單在最近一個可取得的每日交易時段交投最活躍的股票。",
    "Read the ticker on the side. A longer bar means more shares traded. On the scale, k means thousand and M means million.":
        "旁邊是股份代號。柱越長代表成交股數越多。刻度上 k 是千，M 是百萬。",
    "Here the colour shows the latest daily price change: green for a rise or no change, red for a fall. The bar's length shows share count, not price change.":
        "顏色顯示最新每日價格升跌：綠色為升或平，紅色為跌。柱的長度是股數，不是價格變動。",
    "Hover over a bar for its share count. Every trade has both a buyer and a seller.":
        "把游標移到柱上看股數。每宗成交都有買家也有賣家。",
    "A volume of 2M means 2 million shares changed hands. It does not mean $2 million was invested, or that there were 2 million different investors.":
        "成交量 2M 代表 200 萬股轉手。這不代表投資了 200 萬美元，也不代表有 200 萬名不同投資者。",
    "See which names attracted more trading activity in the latest session.":
        "看出最近一個交易時段交投較多的代碼。",
    "Busy trading alone does not show whether a price will rise. Large and small companies naturally trade different share counts, and a session still in progress has an incomplete total.":
        "交投活躍本身並不說明價格會否上升。大小公司成交股數本來不同；若時段尚未完結，總數也不完整。",
    "Each line is a stock, fund or index reset to 100 at its first available date in the selected window. This makes percentage changes easier to compare even when original prices differ.":
        "每條線是一隻股票、基金或指數，在所選區間第一個可取得日期還原為100。即使原價不同，也較易比較百分比變動。",
    "Read dates along the bottom. Match each line's colour to the name in the legend, then read the level on the side.":
        "底部是日期。用圖例顏色對應名稱，再讀旁邊的水平。",
    "100 is the starting point. Above 100 means a gain since that start; below 100 means a loss. The dashed line marks 100.":
        "100 是起點。高於 100 表示由該日起計有升幅；低於 100 表示有跌幅。虛線標示 100。",
    "Subtract 100 from a level to get the percentage change from that series' start. Hover over a date to compare the lines there.":
        "水平減 100 即是該序列由起點計的百分比變動。把游標移到某一日期，可比較當日各線。",
    "Imagine each line began as $100: a level of 120 means a 20% gain; 90 means a 10% loss. A stock at 120 on this chart does not necessarily have a $120 share price.":
        "假設每條線由 100 美元開始：120 代表升 20%；90 代表跌 10%。圖上 120 並不一定代表股價是 120 美元。",
    "Compare gains and losses and how smooth or bumpy each path was. Two lines can end together but have very different journeys.":
        "比較升跌，以及每條路徑是平穩還是上落大。兩條線可以同期結束，過程卻很不同。",
    "The result depends on the starting date and available data. The chart uses adjusted historical prices where supplied; it does not include your fees or taxes. Past winners can become future losers.":
        "結果取決於起始日期及可取得數據。圖表在有提供時使用經調整歷史價；並未計入你的費用或稅項。過往贏家可以變成未來輸家。",
    "Each dot is one selected stock or fund. It combines its past return with how much its daily returns moved around, called volatility.":
        "每一點是一隻已選股票或基金。它把過往回報，與每日回報上落幅度（稱為波幅）放在一起。",
    "Up/down shows the total return over your selected window. Above zero means a gain; below zero means a loss.":
        "上下顯示所選區間的總回報。零以上是升；零以下是跌。",
    "Left/right shows annualized volatility: daily price-change variability expressed on a common yearly scale. Farther right means more variable daily returns in this history.":
        "左右顯示年率化波幅：把每日價格變動的上落，用同一年化尺度表達。越右代表這段歷史中每日回報越不穩定。",
    "Read the ticker beside a dot to identify it. Colours identify groups, not good or bad investments. Hover for more details.":
        "點旁的股份代號用作識別。顏色代表分類，不是好或壞投資。把游標移上去看更多詳情。",
    "Max drawdown in the hover details means the largest fall from an earlier high within the window. It is different from volatility.":
        "游標詳情中的最大回撤，是區間內由較早高位計起的最大跌幅。這與波幅不同。",
    "A dot at 20 on the bottom and +10 on the side had 20% annualized volatility and gained 10% over the selected window. Another dot at 40 and +5 had more variable daily returns but a smaller total gain in that history.":
        "底部 20、旁邊 +10 的點，年率化波幅為 20%，所選區間升了 10%。另一點在 40 及 +5，每日回報上落較大，但該段歷史總升幅較小。",
    "Compare the return achieved with the amount of price movement along the way, rather than looking at gains alone.":
        "把所取得的回報，與過程中的價格上落一併比較，不要只看升幅。",
    "20% volatility is not a 20% chance of losing money, a predicted 20% loss, or a limit on losses. This chart does not measure every kind of risk or predict future returns.":
        "20% 波幅不是有 20% 機會虧錢，也不是預測會虧 20%，更不是虧損上限。此圖並不量度所有風險，也不能預測未來回報。",
    "Intraday means within a trading day. Each candle summarises one block of time, such as one minute or five minutes, set by Bar size.":
        "即市是指同一個交易日之內。每根K線總結一個時段，例如1分鐘或5分鐘，由「K線週期」設定。",
    "Time runs left to right in New York time. The side scale shows price, or index points for an index. Hover to see open, high, low and close.":
        "時間由左至右，以紐約時間顯示。旁邊刻度是價格，指數則是點。把游標移上去看開市、最高、最低及收市。",
    "Open is the start of a block, close its end, high its highest value and low its lowest. The body connects open and close; thin wicks show the extremes.":
        "開市是時段開始，收市是結束，最高是期間最高，最低是期間最低。實體連接開與收；幼影線顯示極端。",
    "Green means close was at least open; red means close was below open. Bars below show shares traded in the same block when volume is available.":
        "綠色表示收市不低於開市；紅色表示收市低於開市。下方柱在有成交量時顯示同一時段成交股數。",
    "Vs previous bar compares the latest block's close with the block before it. Include pre/post adds trading before and after regular US hours. Refresh asks for another data update.":
        "「對上一根K線」比較最新時段收市與前一時段。包括盤前／盤後會加入美股正常時段以外的交易。重新整理會再請求一次數據。",
    "With 5 min selected, one candle opens at $100, reaches $102, falls to $99 and ends at $101. It is green. If the previous candle closed at $100, Vs previous bar is +1%.":
        "選5分鐘時，一根K線開市 100 美元，最高 102 美元，最低 99 美元，收市 101 美元，顯示綠色。若上一根收市 100 美元，「對上一根K線」為 +1%。",
    "See how the day unfolded, when prices moved more, and when trading was busier.":
        "看出當日如何展開、價格何時上落較大，以及何時交投較活躍。",
    "The newest candle may still be forming. Refresh does not guarantee a real-time feed. Zero or missing index volume can mean no volume was supplied; it does not prove that no underlying stocks traded.":
        "最新一根K線可能仍在形成。重新整理並不保證實時行情。指數成交量為零或缺失，可能只是沒有提供成交量，並不證明成分股沒有成交。",
    "This chart shows one selected stock or index over the History window. Each candle summarises one trading day.":
        "此圖顯示所選股票或指數在歷史區間的走勢。每根K線總結一個交易日。",
    "Read dates at the bottom and prices, or index points, on the side. Hover for the day's open, high, low and close.":
        "底部是日期，旁邊是價格或指數點位。把游標移上去看當日開市、最高、最低及收市。",
    "The body connects the opening and closing values; the thin wicks reach the day's high and low. Green means close was at least open, red means it was lower.":
        "實體連接開市與收市；幼影線伸至當日最高及最低。綠色表示收市不低於開市，紅色表示較低。",
    "Volume bars below show shares traded that day when supplied. Taller bars mean more shares changed hands.":
        "下方成交量柱在有提供時顯示當日成交股數。柱越高，轉手股數越多。",
    "Period return above the chart compares the first and last close in this window. Volatility describes how variable daily returns were. Max drawdown is the worst fall from an earlier high in the window.":
        "圖表上方的期內回報比較本區間首個及最後收市。波幅描述每日回報上落有多大。最大回撤是區間內由較早高位計起的最大跌幅。",
    "A day's open is $100, high $106, low $97 and close $104: a green body runs from $100 to $104. Separately, if a past peak of $120 later fell to $90, that fall was a 25% drawdown.":
        "某日開市 100 美元，最高 106 美元，最低 97 美元，收市 104 美元：綠色實體由 100 至 104 美元。另外，若曾經高見 120 美元其後跌至 90 美元，該段跌幅即 25% 回撤。",
    "See the longer price history and compare its gains, daily movement and past declines.":
        "查看較長的價格歷史，並比較升幅、每日上落及過往跌幅。",
    "Historical prices can be adjusted for stock splits and dividends, so they may differ from the prices originally quoted. Index volume can be unavailable. A past drawdown is not a limit on future losses.":
        "歷史價格可因股份拆細及股息而調整，因此可能與當初報價不同。指數成交量可以無法提供。過往回撤並非未來虧損上限。",
})

# Chart example notes
ZH.update({
    "Read time across, price up the side, then compare the first and last values.":
        "橫軸看時間，縱軸看價格，再比較首尾數值。",
    "Read the top edge. The shaded space is decoration, not money or trading volume.":
        "讀上沿。陰影只是裝飾，不是資金或成交量。",
    "Colour compares price with the reference line. A price can rise while staying below it.":
        "顏色比較價格與參考線。價格可以上升，但仍低於參考線。",
    "The body shows start to finish; the thin wicks show the highest and lowest prices.":
        "實體顯示由開到收；幼影線顯示最高及最低價。",
    "One candle is one time block. Here it is five minutes, not a whole day.":
        "一根K線是一個時段。這裏是五分鐘，不是一整天。",
    "One candle is one trading day. Its colour compares that day's close with its open.":
        "一根K線是一個交易日。顏色比較當日收市與開市。",
    "Read one cell at a time: group + month + average percentage change.":
        "一次讀一格：分類 + 月份 + 平均百分比變動。",
    "The bar measures percentage change, not the stock's dollar price.":
        "柱量度的是百分比變動，不是股票美元價。",
    "These are daily percentage changes, even when your look-back window is a year.":
        "即使回看區間是一年，這些仍是每日百分比變動。",
    "A bar left of zero shows a loss. Compare the percentages, not just the colours.":
        "零左邊的柱是跌幅。請比較百分比，不要只看顏色。",
    "A longer bar means more shares traded, not more profit or more dollars invested.":
        "較長的柱代表成交股數較多，不是較多溢利或投入了更多資金。",
    "Everyone begins at 100. A level of 120 means +20%; 90 means −10%.":
        "全部由100開始。120 代表 +20%；90 代表 −10%。",
    "Read both directions: up/down is past return; left/right is how variable daily returns were.":
        "兩個方向都要看：上下是過往回報；左右是每日回報上落有多大。",
    "Price ($)": "價格（美元）",
    "Time →": "時間 →",
    "$100 reference": "100美元參考",
    "Find the": "先找出",
    "$100 reference.": "100美元參考。",
    "Above = green": "線上＝綠色",
    "Below = red": "線下＝紅色",
    "$98 → $99 rises,": "98→99美元是上升，",
    "but stays red!": "但仍是紅色！",
    "Read the top edge.": "讀上沿。",
    "Shading ≠ volume!": "陰影≠成交量！",
    "Read from earlier": "由較早",
    "to later →": "讀到較後 →",
    "Higher on the page": "頁面較高",
    "= higher price.": "＝價格較高。",
    "That's a +{change:.0f}% change.": "即是 +{change:.0f}% 變動。",
    "Start": "起點",
    "Close ${close}": "收市 ${close}",
    "Open ${open}": "開市 ${open}",
    "High ${high}": "最高 ${high}",
    "Low ${low}": "最低 ${low}",
    "Day 1": "第1日",
    "Day 2": "第2日",
    "Body = start": "實體＝由開",
    "to finish.": "到收。",
    "Thin wicks show": "幼影線顯示",
    "the high + low.": "最高 + 最低。",
    "Taller volume bar": "較高的成交量柱",
    "= more shares traded.": "＝成交股數較多。",
    "Jan": "1月",
    "Feb": "2月",
    "Mar": "3月",
    "Tech": "科技",
    "Choose a group": "選一個分類",
    "+ a month.": "+ 一個月。",
    "Green = up": "綠色＝升",
    "Red = down": "紅色＝跌",
    "(+10% − 2%) ÷ 2": "(+10% − 2%) ÷ 2",
    "= +4% group average": "＝+4% 分類平均",
    "One cell = one group, one month": "一格＝一個分類、一個月",
    "Stock {letter}": "股票 {letter}",
    "Shares traded (M = million)": "成交股數（M＝百萬）",
    "Price change (%)": "價格變動（%）",
    "2M = 2m shares": "2M＝200萬股",
    "NOT $2m of money.": "不是200萬美元。",
    "Longer = more": "越長＝越多",
    "shares traded.": "成交股數。",
    "$100 → $120": "100→120美元",
    "means +20%.": "即 +20%。",
    "Longer = bigger": "越長＝越大",
    "percentage change.": "百分比變動。",
    "$50 → $51": "50→51美元",
    "means +2% today.": "即今日 +2%。",
    "Compare daily": "比較每日",
    "percentage moves.": "百分比升跌。",
    "$80 → $76": "80→76美元",
    "means −5% today.": "即今日 −5%。",
    "Left of zero": "零的左邊",
    "= a price fall.": "＝價格下跌。",
    "Each row is": "每一列是",
    "one stock.": "一隻股票。",
    "Starting level = 100": "起始水平＝100",
    "Start together": "一齊由",
    "at 100.": "100開始。",
    "120 means +20%": "120 即 +20%",
    "since the start.": "由起點計。",
    "90 means −10%.": "90 即 −10%。",
    "Not a share price!": "不是股價！",
    "Past return (%)": "過往回報（%）",
    "Annualized volatility (%)": "年率化波幅（%）",
    "Up / down": "上／下",
    "= past return.": "＝過往回報。",
    "Further right": "越向右",
    "= bigger swings.": "＝上落越大。",
    "A: 20% volatility": "A：20% 波幅",
    "+10% past return": "+10% 過往回報",
    "A LITTLE CHART FIELD NOTE": "圖表閱讀小筆記",
    "Made-up numbers · learn the picture, not a prediction": "虛構數字 · 學看圖，不是預測",
    "Fictional figures. {summary} Follow notes 1, 2 and 3 and their arrows.":
        "虛構數字。{summary} 請跟從註 1、2、3 及其箭嘴。",
    "Annotated teaching example: {topic}": "註解教學例子：{topic}",
})

# ---------------------------------------------------------------------------
# Learn chrome and lesson titles
# ---------------------------------------------------------------------------
ZH.update({
    "STOCKSCOPE LEARN · BEGINNER STOCK ACADEMY": "STOCKSCOPE 學習 · 股票入門學堂",
    "STOCKSCOPE LEARN · START HERE": "STOCKSCOPE 學習 · 由這裏開始",
    "LESSON 01 · THE BASICS": "第01課 · 基礎",
    "LESSON 02 · READ THE CHART": "第02課 · 閱讀圖表",
    "LESSON 03 · HOW TRADING WORKS": "第03課 · 交易如何運作",
    "LESSON 05 · WHAT MOVES PRICES": "第05課 · 價格為何變動",
    "LESSON 06 · RISK & INVESTOR PROTECTION": "第06課 · 風險與投資者保障",
    "FINAL ASSESSMENT · BEGINNER PATHWAY": "綜合評估 · 入門路徑",
    "DATA NOTES · TRANSPARENCY": "數據說明 · 透明度",
    "Learn · Market Basics": "學習 · 市場基礎",
    "← Hide study path": "← 隱藏學習路徑",
    "☰ Show study path": "☰ 顯示學習路徑",
    "Navigation": "導航",
    "Course progress": "課程進度",
    "Completed {pct}%": "已完成 {pct}%",
    "Knowledge checks passed at least once": "知識檢查至少通過一次",
    "{n}/{total} lessons passed": "{n}/{total} 課已通過",
    "Data sources": "數據來源",
    "Yahoo Finance / yfinance (prototype)": "Yahoo Finance / yfinance（原型）",
    "Choose a history window on each chart page.": "每個圖表頁可選擇歷史區間。",
    "For learning; not investment advice.": "供學習用；並不構成投資建議。",
    "Start with the basics, learn to read charts, and understand the business behind the numbers. Choose a lesson from your study path or try the historical market challenge below.":
        "由基礎開始，學習閱讀圖表，並理解數字背後的業務。從學習路徑選一課，或試試下方的歷史市況挑戰。",
    "Read the market": "閱讀市場",
    "Explore price, volume and chart patterns. Learn what each chart can tell you and what still needs checking.":
        "認識價格、成交量及圖表形態。了解每張圖能說明甚麼，以及仍需核對甚麼。",
    "Understand a business": "理解一盤生意",
    "Discover how companies earn money and connect revenue, profit and cash flow.":
        "了解公司如何賺錢，並把營業額、溢利及現金流連起來。",
    "Think about risk": "思考風險",
    "Compare possible returns with uncertainty, verify information and protect your account.":
        "把可能回報與不確定性比較，核實資料，並保障戶口。",
    "Learning units": "學習單元",
    "{n} units": "{n} 個單元",
    "From basic concepts to investor protection": "由基本概念到投資者保障",
    "Interactive charts": "互動圖表",
    "3+ types": "3種以上",
    "Line · bar · scatter": "線圖 · 柱狀圖 · 散點圖",
    "Your progress": "你的進度",
    "Completed lessons": "已完成課堂",
    "Knowledge checks: {mastered}/{total} lessons passed at least once. You can retry. Passing a check and marking a lesson complete are separate actions.":
        "知識檢查：{mastered}/{total} 課至少通過一次。可以重試。通過檢查與標記完成是兩件獨立事情。",
    "REAL-WORLD CHALLENGE": "真實挑戰",
    "Historical Market Challenge": "歷史市況挑戰",
    "Read real historical prices, make your own judgement, then reveal what happened. This exercise does not show that indicators can reliably predict prices.":
        "閱讀真實歷史價格，自行判斷，再揭示後來發生的事。此練習並不證明指標可以可靠預測價格。",
    "Chart challenge | What happens next?": "圖表挑戰｜下一步會怎樣？",
    "Study historical candles, volume, SMA 5 / SMA 20 and MACD (12, 26, 9). Make your judgement, then reveal the next 20 trading days. Signal markers appear only after submission.":
        "研讀歷史K線、成交量、5天／20天簡單移動平均線及 MACD（12, 26, 9）。先作判斷，再揭示其後20個交易日。訊號標記只在提交後出現。",
    "Chart colours:": "圖表顏色：",
    "Green = up": "綠色＝升",
    "Red = down": "紅色＝跌",
    "Amber = SMA 5": "琥珀色＝5天簡單移動平均線",
    "Blue = SMA 20": "藍色＝20天簡單移動平均線",
    "Volume uses each candle’s colour. MACD histogram colours show positive/negative values, not the stock’s direction.":
        "成交量沿用該根K線顏色。MACD 柱狀圖顏色顯示正負值，不是股票方向。",
    "Your judgement": "你的判斷",
    "Question: Compared with the signal day's close, where will the close be 20 trading days later?":
        "問題：對比訊號日收市，20個交易日後的收市會在哪裏？",
    "Classification: above +1% = rise; below −1% = fall; −1% to +1% = little change.":
        "分類：高於 +1%＝升；低於 −1%＝跌；−1% 至 +1%＝變化不大。",
    "Choose your judgement:": "選擇你的判斷：",
    "Rise": "上升",
    "Fall": "下跌",
    "Little change": "變化不大",
    "Reveal what happened": "揭示後來如何",
    "Choose an answer before revealing the result.": "揭示結果前請先選擇答案。",
    "Try challenge 01 again": "再試挑戰01",
    "YOUR LEARNING PATH": "你的學習路徑",
    "A beginner path of {n} learning units": "共 {n} 個入門學習單元",
    "Each lesson includes concepts, examples, exploration or practice. Study in order or revisit any topic.":
        "每課包括概念、例子、探索或練習。可按順序學習，或重溫任何主題。",
    "Open lesson →": "開啟課堂 →",
    "✓ Completed": "✓ 已完成",
    "TOOLS FOR LEARNING": "學習工具",
    "Quizzes and data tools": "測驗與數據工具",
    "Review the course in the final quiz or download cleaned historical data for study.":
        "用綜合測驗重溫課程，或下載整理後的歷史數據供學習。",
    "Check your understanding of stock basics, charts, company research, returns and risk.":
        "檢查你對股票基礎、圖表、公司研究、回報及風險的理解。",
    "Start final quiz →": "開始綜合測驗 →",
    "Review data sources, definitions and limitations; export a learning dataset.":
        "查看數據來源、定義及限制；匯出學習數據集。",
    "Open Data & Methods →": "開啟數據與方法 →",
    "START HERE": "由這裏開始",
    "New to stocks? Remember these three ideas": "剛接觸股票？記住這三點",
    "Price is not value": "價格不是價值",
    "A share price quotes one unit. Comparing share prices alone does not value companies.":
        "股價報的是一股的價格。只比較股價，並不能為公司估值。",
    "Consider returns and risk together": "回報與風險要一併考慮",
    "Past gains do not guarantee future gains. Check variability, drawdowns and the time window.":
        "過往升幅不保證未來升幅。請查看上落、回撤及時間區間。",
    "Data needs context": "數據需要背景",
    "Charts describe what happened; a line alone rarely proves why.":
        "圖表描述已發生的事；單靠一條線很少能證明原因。",
    "Learning goal: ask better questions instead of memorising a supposedly guaranteed signal.":
        "學習目標：提出更好的問題，而不是背誦據說保證有效的訊號。",
    "✓ Lesson completed": "✓ 課堂已完成",
    "Mark lesson complete": "標記課堂完成",
    "Lesson marked complete.": "已標記課堂完成。",
    "Submit answer": "提交答案",
    "Check understanding": "檢查理解",
    "Choose a stock": "選擇股票",
    "Choose a stock / ETF": "選擇股票／ETF",
    "Real stock / ETF": "真實股票／ETF",
    "History range": "歷史區間",
    "Choose one indicator": "選擇一項指標",
    "Choose a company": "選擇公司",
    "Create a downloadable dataset": "建立可下載數據集",
    "Choose symbols": "選擇代碼",
    "Candles only": "只顯示K線",
    "MA | Simple Moving Average (SMA 5 / SMA 20)": "MA｜簡單移動平均線（SMA 5／SMA 20）",
    "EMA | Exponential Moving Average (EMA 12 / EMA 26)": "EMA｜指數移動平均線（EMA 12／EMA 26）",
    "Bollinger Bands (20, 2)": "保力加通道（20, 2）",
    "Support and Resistance": "支持及阻力",
    "Fibonacci Retracement": "斐波那契回撤",
    "VWAP (concept)": "VWAP（概念）",
    "Ichimoku Cloud (concept)": "一目均衡表（概念）",
    "OBV (On Balance Volume)": "OBV（能量潮）",
    "ADX (trend strength)": "ADX（趨勢強度）",
    "Stochastic": "隨機指數",
    "Choose one tool at a time. SMA, EMA, Bollinger Bands, Support and Resistance, and Fibonacci Retracement appear on the price chart. RSI, MACD, Stochastic, ADX and OBV appear below it.":
        "每次只選一項工具。SMA、EMA、保力加通道、支持及阻力、斐波那契回撤顯示在價格圖上。RSI、MACD、隨機指數、ADX及OBV顯示在下方。",
    "No market data was returned. Check your connection or try again later.":
        "未有傳回市場數據。請檢查網絡，或稍後再試。",
    "Market data could not be loaded. You can still read the lesson; check your connection or try again later to use the charts.":
        "未能載入市場數據。你仍可閱讀課堂；請檢查網絡，或稍後再試以使用圖表。",
    "Last 5 days": "最近5日",
    "Last month": "最近一個月",
    "Last 3 months": "最近3個月",
    "Last 6 months": "最近6個月",
    "Last year": "最近一年",
    "Last 5 years": "最近5年",
    "Last 10 years": "最近10年",
    "All available history": "全部可取得歷史",
})

# Lesson guide
ZH.update({
    "About 10–12 minutes": "約10–12分鐘",
    "About 8–10 minutes": "約8–10分鐘",
    "About 15–25 minutes": "約15–25分鐘",
    "About 25–35 minutes": "約25–35分鐘",
    "About 15–20 minutes": "約15–20分鐘",
    "About 6–8 minutes": "約6–8分鐘",
    "Explain share ownership, primary and secondary markets, market participants, how prices form, returns and key risks.":
        "解釋股份擁有權、一級及二級市場、市場參與者、價格如何形成、回報及主要風險。",
    "Start with why companies issue shares, then learn who participates and how stocks differ from other investments.":
        "先了解公司為何發行股份，再認識誰參與市場，以及股票與其他投資有何不同。",
    "Build number skills by calculating market capitalization, ownership percentage and a simple total return.":
        "透過計算市值、持股百分比及簡單總回報，建立數字能力。",
    "Complete the knowledge check and explain your reasoning using price, share count and risk.":
        "完成知識檢查，並用價格、股數及風險解釋你的理由。",
    "If someone says a company is more expensive just because its share price is higher, what other information would you check?":
        "若有人只因股價較高便說公司較貴，你還會核對哪些資料？",
    "Identify open, high, low and close (OHLC), explain volume, and understand why a chart cannot prove what happens next.":
        "辨認開市、最高、最低及收市（OHLC），解釋成交量，並理解圖表為何不能證明下一步。",
    "Learn the meaning of open, high, low, close and trading volume.":
        "學習開市、最高、最低、收市及成交量的含義。",
    "Choose a security and hover over candles and volume bars to compare dates.":
        "選擇一隻證券，把游標移到K線及成交量柱上比較日期。",
    "Explain what a sudden increase in volume can mean; try again if needed.":
        "解釋成交量突然增加可以代表甚麼；有需要可再試。",
    "Besides colour, what information should you check when reading a candlestick chart?":
        "閱讀K線圖時，除了顏色，還應核對哪些資料？",
    "Recognise common single-candle, two-candle, three-candle and continuation patterns. Explain why trend, location and confirmation matter.":
        "辨認常見單根、兩根、三根及持續形態。解釋趨勢、位置及確認為何重要。",
    "Learn bodies, upper and lower wicks, and proportions; then explore single and multiple-candle patterns.":
        "學習實體、上影線、下影線及比例；再認識單根及多根K線形態。",
    "Compare synthetic candle examples, then look for similar structures in real historical prices.":
        "比較教學用K線例子，再在真實歷史價格中找相似結構。",
    "Answer pattern and context questions, review explanations and try again.":
        "回答形態及背景問題，查看解釋，然後再試。",
    "When you recognise a pattern, which three types of context would you check?":
        "辨認出形態後，你會核對哪三類背景？",
    "Understand SMA, EMA, RSI, MACD, Stochastic, Bollinger Bands, ADX and OBV, plus support and resistance, Fibonacci retracement, VWAP and Ichimoku Cloud.":
        "理解簡單移動平均線、指數移動平均線、相對強弱指數、MACD、隨機指數、保力加通道、平均動向指數及能量潮，以及支持位與阻力位、斐波那契回撤、成交量加權平均價及一目均衡表。",
    "Start with the question each indicator answers, then learn its calculation, settings, interpretation and limitations.":
        "先問每個指標回答甚麼問題，再學習其計算、設定、解讀及限制。",
    "Switch overlays and indicator panes on historical candlesticks. Compare signals with the trend and possible failure cases.":
        "在歷史K線上切換疊加及指標視窗。把訊號與趨勢及可能失效的情況比較。",
    "Use chart evidence to distinguish direction, momentum, volatility and price/volume relationships.":
        "用圖表證據分辨方向、動力、波幅及價量關係。",
    "Which signals use the same price data, and which observations still need independent evidence?":
        "哪些訊號用同一組價格數據，哪些觀察仍需要獨立證據？",
    "Describe a trade's main steps and the trade-offs between market, limit and stop orders.":
        "描述一宗交易的主要步驟，以及市價盤、限價盤與止蝕盤的取捨。",
    "Work through securities, brokers, order types, costs and execution records.":
        "認識證券、經紀、盤種、費用及成交紀錄。",
    "Use fictional bid and ask quotes to calculate the spread and compare price control with execution priority.":
        "用虛構買入價及賣出價計算買賣差價，並比較價格控制與成交優先。",
    "Choose an order approach for a scenario and review why execution is uncertain.":
        "為情景選擇下盤方式，並複習為何成交並不確定。",
    "Why can a limit order control the acceptable price without guaranteeing a fill?":
        "為何限價盤可以控制可接受價格，卻不保證成交？",
    "Build a picture of a business from its model, three financial statements, key ratios and reliable sources.":
        "由業務模式、三份財務報表、主要比率及可靠來源，建立對一盤生意的認識。",
    "Use a familiar business to understand revenue, costs and profit, then read the income statement, balance sheet and cash flow statement.":
        "用熟悉的生意理解營業額、成本及溢利，再閱讀損益表、資產負債表及現金流量表。",
    "Explore consistent fictional company accounts and change ratio inputs to see the effect.":
        "瀏覽前後一致的虛構公司賬目，並改動比率輸入看效果。",
    "Investigate a case where revenue rises but cash flow falls, then choose the next evidence to check.":
        "調查營業額上升但現金流下跌的個案，再選擇下一步要核對的證據。",
    "Which evidence most changed your view of the company, and what is still missing?":
        "哪項證據最改變你對公司的看法，還缺了甚麼？",
    "Distinguish company, industry, economic and market influences. Avoid confusing events happening together with proof of cause.":
        "分辨公司、行業、經濟及市場影響。避免把同時發生的事件當成因果證明。",
    "Learn how earnings, interest rates, expectations, competition, liquidity and unexpected events can matter.":
        "了解盈利、利率、預期、競爭、流動性及突發事件可以如何影響。",
    "Compare actual results, earlier expectations and forward guidance in a case study.":
        "在個案中比較實際業績、較早預期及前瞻指引。",
    "Explain why a stock can fall even when profit grows.":
        "解釋為何溢利增長，股票仍可以下跌。",
    "If a stock rises after a news story, what else would you check before explaining the cause?":
        "若股票在一則新聞後上升，解釋原因前你還會核對甚麼？",
    "Recognise market risks, behavioural biases and investment scam warning signs, and know where to check information.":
        "辨認市場風險、行為偏差及投資騙局警號，並知道到哪裏核對資料。",
    "Explore the risk map, account security and common scam signals.":
        "認識風險地圖、戶口安全及常見騙局訊號。",
    "Work through a pre-investment checklist for a hypothetical situation.":
        "就假設情況走一次投資前清單。",
    "Assess a social-media investment group promising high returns and demanding an urgent transfer.":
        "評估一個承諾高回報並要求緊急轉賬的社交媒體投資群組。",
    "What three things would you verify before making an investment?":
        "作出投資前，你會核實哪三件事？",
})

# Lesson 1 headings / tabs
ZH.update({
    "Lesson 01 | Understanding the Stock Market": "第01課｜認識股票市場",
    "Start with what owning a share means, then explore issuance, trading, pricing, investment products, participants, returns and risks.":
        "先由持有股份代表甚麼開始，再認識發行、買賣、定價、投資產品、參與者、回報及風險。",
    "THE BIG PICTURE": "整體圖景",
    "Build a map of the market": "建立市場地圖",
    "Begin with ownership and financing, move to markets and investment products, and finish with returns, risks and readiness.":
        "由擁有權及融資開始，再到市場及投資產品，最後談回報、風險及準備。",
    "Companies and shares": "公司與股份",
    "Companies divide ownership into shares. Buying a stock gives you part of the company's equity; it is different from lending it money.":
        "公司把擁有權分成股份。買入股票即持有公司部分股本權益；這與借錢給公司不同。",
    "Ownership": "擁有權",
    "Issuance and trading": "發行與買賣",
    "Companies raise capital by issuing securities. Investors trade existing shares in the secondary market, where orders and expectations help form prices.":
        "公司透過發行證券集資。投資者在二級市場買賣已發行股份，買賣盤及預期有助形成價格。",
    "Market mechanics": "市場機制",
    "Returns and risk": "回報與風險",
    "Returns may come from price changes and dividends. Risks include falling prices, a weakening business, limited liquidity and concentrated holdings.":
        "回報可來自價格變動及股息。風險包括價格下跌、業務轉弱、流動性有限及持倉過於集中。",
    "Investment judgement": "投資判斷",
    "01 What a share represents": "01 股份代表甚麼",
    "02 How markets work": "02 市場如何運作",
    "03 Common investment products": "03 常見投資產品",
    "04 Prices and returns": "04 價格與回報",
    "05 Risk and getting started": "05 風險與起步",
    "OWNERSHIP": "擁有權",
    "A share is part of a company's ownership": "股份是公司擁有權的一部分",
    "It is not a debt promise or a fixed-income product.": "它不是債務承諾，也不是固定收益產品。",
    "TRY THE NUMBERS": "試算數字",
    "Use a fictional company to understand market capitalization": "用虛構公司理解市值",
    "Change the share price and number of shares to see why unit price differs from total equity market value.":
        "改動股價及股數，看出單位價格為何不同於股本總市值。",
    "MARKET STRUCTURE": "市場結構",
    "From issuing shares to completing a trade": "由發行股份到完成一宗交易",
    "Separate issuers, investors, brokers, trading venues and regulators.":
        "分清發行人、投資者、經紀、交易場所及監管機構。",
    "INVESTMENT VEHICLES": "投資工具",
    "Stocks, bonds, indices and ETFs are different": "股票、債券、指數及交易所買賣基金並不相同",
    "Understand what you own before comparing price and risk.": "比較價格及風險前，先搞清楚你持有甚麼。",
    "PRICE & RETURN": "價格與回報",
    "Price is a trading outcome; return has several components": "價格是成交結果；回報有多個組成部分",
    "A market price reflects transactions and expectations at a moment in time, not a direct reading of intrinsic value.":
        "市價反映某一刻的成交及預期，並不是內在價值的直接讀數。",
    "TRY A RETURN EXAMPLE": "試算回報例子",
    "Try it: price changes plus dividends": "試一試：價格變動加股息",
    "Assume a $20 purchase price. Change the current price and dividends per share to see a simple total return.":
        "假設買入價 20 美元。改動現價及每股股息，看簡單總回報。",
    "RISK & READINESS": "風險與準備",
    "Set boundaries before choosing products": "選擇產品前先設界限",
    "Risk includes timing, costs, liquidity and behaviour as well as price movement.":
        "風險包括時機、費用、流動性及行為，不只是價格上落。",
    "KEY TERMS": "關鍵用語",
    "Quick glossary": "速查詞彙",
    "QUICK CHECK": "快速檢查",
    "Check your understanding": "檢查你的理解",
    "Assumed market capitalization": "假設市值",
    "Share price × shares outstanding": "股價 × 已發行股份",
    "Market value of this holding": "此持股市值",
    "Assumed current price × shares held": "假設現價 × 持股數目",
    "Ownership percentage": "持股百分比",
    "Shares held ÷ shares outstanding": "持股數目 ÷ 已發行股份",
    "Assumed purchase price": "假設買入價",
    "Cost per share before fees": "未計費用的每股成本",
    "Issuer": "發行人",
    "A company raises capital through securities and discloses important business and financial information under applicable rules.":
        "公司透過證券集資，並按適用規則披露重要業務及財務資料。",
    "Investors": "投資者",
    "Individuals, funds, pension plans and institutions submit orders according to their goals and constraints.":
        "個人、基金、退休計劃及機構按其目標及限制下盤。",
    "Brokers and trading venues": "經紀與交易場所",
    "Brokers receive and route orders. Exchanges and other venues provide matching and execution mechanisms.":
        "經紀接收及傳送買賣盤。交易所及其他場所提供配對及成交機制。",
    "Goals and time horizon": "目標與投資年期",
    "Write down what the money is for and when it is needed. Necessary short-term spending leaves less room for large price swings.":
        "寫下資金用途及何時需要。短期必要開支，承受價格大上大落的空間較少。",
    "Cash and debt": "現金與負債",
    "Consider emergency funds, everyday costs and expensive debt before exposing essential money to volatile assets.":
        "在把必需資金投放於波幅大的資產前，先考慮應急錢、日常開支及高息負債。",
    "Understand the product": "理解產品",
    "Explain what you own, how returns arise and what could go wrong.":
        "解釋你持有甚麼、回報如何產生，以及甚麼可能出錯。",
    "Diversification and concentration": "分散與集中",
    "Spreading across businesses, industries and asset classes can reduce some concentration risk, but cannot guarantee profit or prevent a broad decline.":
        "分散於不同業務、行業及資產類別，可減低部分集中風險，但不能保證獲利，也不能防止大市下跌。",
    "Costs and liquidity": "費用與流動性",
    "Compare commissions, spreads, fund expenses, taxes and currency costs. Thinly traded securities can be difficult to sell at a desired price.":
        "比較佣金、買賣差價、基金開支、稅項及匯兌成本。交投淡靜的證券，可能難以按理想價格賣出。",
    "Verify sources": "核實來源",
    "Check filings, announcements, fund documents and intermediary registration. Be wary of guaranteed returns, urgent transfers and secret tips.":
        "核對披露文件、公告、基金文件及中介人註冊。小心保證回報、緊急轉賬及秘密貼士。",
})

# Lesson 02–06 / quiz / data headings
ZH.update({
    "Lesson 02 | Reading Stock Charts": "第02課｜閱讀股票圖表",
    "Look beyond red and green. Read the open, high, low, close and volume behind a candle.":
        "不要只看紅綠。閱讀K線背後的開市、最高、最低、收市及成交量。",
    "LOOK CLOSER": "再看清楚",
    "Read price and volume together": "一併閱讀價格與成交量",
    "What can this chart tell you?": "這張圖能告訴你甚麼？",
    "Five chart essentials": "圖表五要點",
    "Daily volume": "每日成交量",
    "Taller bars mean more reported shares traded. Green means close at/above open; red means close below open.":
        "較高的柱代表呈報成交股數較多。綠色＝收市不低於開市；紅色＝收市低於開市。",
    "Volume describes activity; direction needs price action and context.":
        "成交量描述交投活躍程度；方向需要價格走勢及背景。",
    "A day's volume rises sharply. What is the most careful interpretation?":
        "某日成交量急升。最審慎的解讀是甚麼？",
    "The price must rise tomorrow.": "明日價格一定上升。",
    "Trading is busier; direction needs other evidence.": "交投較活躍；方向需要其他證據。",
    "Company profit has definitely increased.": "公司溢利肯定已增加。",
    "STEP 2 · REAL MARKET": "步驟2 · 真實市場",
    "Practise on historical prices": "用歷史價格練習",
    "Illustrations teach structure; real charts develop observation. Describe the prior trend first and avoid forcing an unclear shape into a pattern name.":
        "圖解教結構；真實圖表練觀察。先描述先前趨勢，避免把不清楚的形態硬套名稱。",
    "STEP 3 · PRACTICE": "步驟3 · 練習",
    "Candlestick pattern check": "K線形態檢查",
    "Answer first, then read the explanations. Get at least 5 correct to pass this chapter. You can try again.":
        "先作答，再看解釋。至少答對5題才通過本章。可以重試。",
    "A REPEATABLE METHOD": "可重複的方法",
    "A repeatable chart-reading routine": "可重複的圖表閱讀步驟",
    "Use the same order each time: describe the evidence, suggest an explanation, then look for opposing evidence and risks.":
        "每次用同一順序：描述證據、提出解釋，再尋找相反證據及風險。",
    "KNOWLEDGE CHECK": "知識檢查",
    "Chapter check | Understand, then explain": "本章檢查｜先理解，再解釋",
    "Get at least 6 correct to pass. Submit to see answers and explanations. You can retry.":
        "至少答對6題才通過。提交後可看答案及解釋。可以重試。",
    "Lesson 03 | How Does a Stock Trade Happen?": "第03課｜一宗股票交易如何發生？",
    "Follow a trade from choosing a security to checking the fill. Explore brokers, quotes, order types, costs and records. These are simulations, with no broker connection.":
        "由選擇證券到核對成交，跟進一宗交易。認識經紀、報價、盤種、費用及紀錄。這些是模擬，並無連接經紀。",
    "THE WORKFLOW": "流程",
    "The 6 basic steps of a trade": "一宗交易的6個基本步驟",
    "ORDER TYPES": "盤種",
    "How do three common order types differ?": "三種常見盤種有何分別？",
    "ACCOUNT BASICS": "戶口基礎",
    "Cash accounts, margin accounts and fractional shares": "現金戶口、保證金戶口及碎股",
    "TRY IT": "試一試",
    "Practice quote | Execution or price control?": "練習報價｜成交優先還是價格控制？",
    "These are fictional teaching prices, not current quotes for any security.":
        "這些是虛構教學價格，並非任何證券的現價。",
    "Cash account": "現金戶口",
    "Purchases generally use available account funds. Understand settlement, when cash is available and your broker's rules.":
        "買入一般使用戶口可用資金。了解交收、現金何時可用，以及經紀規則。",
    "Account basics": "戶口基礎",
    "Margin account": "保證金戶口",
    "May allow borrowing from a broker or leveraged exposure. Interest, maintenance requirements, margin calls and forced sales can apply.":
        "或可向經紀借貸或使用槓桿。可能涉及利息、維持按金、追繳保證金及強制平倉。",
    "More complex": "較複雜",
    "Fractional shares": "碎股",
    "Some brokers let you buy less than one share. Not all securities or order types qualify; transfers, voting and execution can differ.":
        "部分經紀容許買入少於一股。並非所有證券或盤種都適用；轉倉、投票及成交可以不同。",
    "Check broker terms": "請核對經紀條款",
    "THREE STATEMENTS · ONE STORY": "三份報表 · 同一個故事",
    "Three statements answer three different questions": "三份報表回答三個不同問題",
    "The Income statement covers profit over a period. The Balance sheet shows assets, liabilities and equity on a reporting date. The Cash flow statement tracks cash over a period. All examples use Orange Grove Drinks.":
        "損益表涵蓋一段期間的溢利。資產負債表顯示報告日的資產、負債及股東權益。現金流量表追蹤一段期間的現金。所有例子以橙園飲品為教學公司。",
    "METRIC TRANSLATOR": "指標翻譯",
    "Translate financial terms into everyday questions": "把財務用語譯成日常問題",
    "Ask what the measure answers, then look at the formula. Choose a measure and change the example numbers to see the result.":
        "先問這個指標回答甚麼，再看法。選一項指標並改動例子數字看結果。",
    "CASE INVESTIGATION": "個案調查",
    "When numbers disagree, investigate before deciding": "數字不一致時，先調查再決定",
    "Real company data often gives mixed signals. Your first job is to find the next useful piece of evidence.":
        "真實公司數據往往訊號混雜。第一步是找出下一件有用的證據。",
    "APPLY TO A REAL COMPANY": "套用到真實公司",
    "Apply the method to a real company": "把方法套用到真實公司",
    "Start with official filings. Data summaries can help locate numbers, but do not cover everything.":
        "由官方披露文件開始。數據摘要有助找到數字，但不能涵蓋一切。",
    "Lesson 05 | Why Do Stock Prices Move?": "第05課｜股價為何變動？",
    "Prices reflect current performance, future expectations, funding costs and market sentiment. Explore several possible causes.":
        "價格反映當前表現、未來預期、資金成本及市場氣氛。認識多種可能原因。",
    "CASE PRACTICE": "個案練習",
    "Case study | Why might a stock fall after good earnings?": "個案｜為何業績好，股票仍可能跌？",
    "This is a fictional teaching scenario.": "這是虛構教學情景。",
    "Lesson 06 | Risk & Investor Protection": "第06課｜風險與投資者保障",
    "Learn to recognize risk, reduce avoidable mistakes and protect your account and judgment.":
        "學習辨認風險、減少可避免的錯誤，並保障戶口及判斷。",
    "RISK MAP": "風險地圖",
    "Six risks every beginner should recognize": "每個初學者都應辨認的六種風險",
    "PROTECT YOURSELF": "保護自己",
    "Before-investing self-check": "投資前自我檢查",
    "RED FLAGS": "警號",
    "Warning signs to recognize": "要辨認的警號",
    "Promises of high returns with little or no risk": "承諾高回報而幾乎沒有風險",
    "Every investment has risk. Guaranteed high returns with almost no risk are a warning sign.":
        "每項投資都有風險。保證高回報而幾乎沒有風險，本身就是警號。",
    "Pressure to act immediately": "催促立刻行動",
    "Urgency, secrecy, very short deadlines or pressure to borrow money are reasons to pause and verify.":
        "緊急、保密、極短限期或催促借錢，都是應暫停並核實的理由。",
    "Social-media stock groups and fake experts": "社交媒體股票群組及假專家",
    "Strangers may impersonate professionals, brokers or regulators, or promote prices before selling. Group chats, screenshots and celebrity pictures are not verification.":
        "陌生人可能冒充專業人士、經紀或監管機構，或先推高價格再賣出。群組對話、截圖及名人相片都不是核實。",
    "Pay first to withdraw or recover losses": "先付款才能提款或追回虧損",
    "Unfreezing fees and recovery fees may be another scam. Do not send further funds or sensitive information to the requester.":
        "解凍費及追回費可能是另一場騙局。不要再向對方匯款或提供敏感資料。",
    "Final Quiz | Connect What You Have Learned": "綜合測驗｜把所學連起來",
    "24 scenario questions cover stocks, candles, indicators, orders, statements, price drivers and investor protection. Submit to see each result, its explanation and the lesson to revisit.":
        "24道情景題涵蓋股票、K線、指標、買賣盤、報表、價格驅動因素及投資者保障。提交後可看每題結果、解釋及應重溫的課堂。",
    "Data & Methods | Understand and Verify": "數據與方法｜理解與核實",
    "The lessons use historical market data for interaction and explain definitions, calculations and limitations.":
        "課堂用歷史市場數據作互動，並解釋定義、計算及限制。",
    "CURRICULUM SCOPE": "課程範圍",
    "What does the course cover?": "課程涵蓋甚麼？",
    "DATA SOURCE": "數據來源",
    "Sources and use limitations": "來源及使用限制",
    "Data structure": "數據結構",
    "Daily data contains date, symbol, open, high, low, close and volume. Several securities across dates form the dataset.":
        "每日數據包括日期、代碼、開市、最高、最低、收市及成交量。多隻證券跨越多個日期組成數據集。",
    "7 fields": "7個欄位",
    "Measure definitions": "指標定義",
    "Period return uses the first and last valid closes. Annualized volatility approximates daily-return standard deviation × √252. Maximum drawdown is the largest decline from an earlier peak.":
        "期內回報用首個及最後有效收市價。年率化波幅約為每日回報標準差 × √252。最大回撤是由較早高位計起的最大跌幅。",
    "Checkable calculations": "可核對的計算",
    "Single candlesticks": "單根K線",
    "Two-candle patterns": "兩根K線形態",
    "Three-candle patterns": "三根K線形態",
    "Continuation patterns": "持續形態",
    "Long bullish candle": "長陽線",
    "Long bearish candle": "長陰線",
    "Bullish Marubozu": "上升光頭光腳",
    "Bearish Marubozu": "下跌光頭光腳",
    "Doji": "十字星",
    "Long-legged Doji": "長腳十字星",
    "Dragonfly Doji": "蜻蜓十字星",
    "Gravestone Doji": "墓碑十字星",
    "Spinning Top": "紡錘線",
    "Hammer": "錘頭",
    "Hanging Man": "上吊線",
    "Inverted Hammer": "倒錘頭",
    "Shooting Star": "射擊之星",
    "Bullish Engulfing": "上升吞噬",
    "Bearish Engulfing": "下跌吞噬",
    "Piercing Line": "刺透線",
    "Dark Cloud Cover": "烏雲蓋頂",
    "Bullish Harami": "上升孕育",
    "Bearish Harami": "下跌孕育",
    "Morning Star": "晨星",
    "Evening Star": "暮星",
    "Three White Soldiers": "三白兵",
    "Three Black Crows": "三黑鴉",
    "Rising Three Methods": "上升三法",
    "Falling Three Methods": "下跌三法",
    "Bullish price action": "看好價格走勢",
    "Bearish price action": "看淡價格走勢",
    "Neutral / indecision": "中性／猶豫",
    "Context": "背景",
    "Read the preceding trend": "先看先前趨勢",
    "Later confirmation": "其後確認",
    "Not an automatic trade signal": "不是自動買賣訊號",
    "Price (USD)": "價格（美元）",
    "Candles (green up / red down)": "K線（綠升紅跌）",
    "SMA 5 (5-day simple moving average)": "5天簡單移動平均線",
    "SMA 20 (20-day simple moving average)": "20天簡單移動平均線",
    "Volume (candle colours)": "成交量（沿用K線顏色）",
    "MACD histogram (positive green / negative red)": "MACD 柱狀圖（正綠負紅）",
    "MACD line": "MACD 線",
    "Signal line": "訊號線",
    "SMA 5 crosses above SMA 20": "5天簡單移動平均線升穿20天線",
    "MACD line crosses above signal line": "MACD 線升穿訊號線",
    "Submit quiz and view each result": "提交測驗並查看每題結果",
    "Market order": "市價盤",
    "Limit order": "限價盤",
    "Stop order": "止蝕盤",
    "Stocks, bonds, indices, ETFs, exchanges and market capitalization.":
        "股票、債券、指數、交易所買賣基金、交易所及市值。",
    "Candles, volume, quotes and timeframes.": "K線、成交量、報價及週期。",
    "Single and multiple-candle patterns with trend context and confirmation.":
        "單根及多根K線形態，連同趨勢背景及確認。",
    "Understand averages, momentum, volatility and volume alongside prices.":
        "連同價格理解平均線、動力、波幅及成交量。",
    "Brokers, order types, bid-ask spreads, costs and execution.":
        "經紀、盤種、買賣差價、費用及成交。",
    "Financial statements, key ratios and reliable sources.":
        "財務報表、主要比率及可靠來源。",
    "Earnings, rates, expectations and market influences.":
        "盈利、利率、預期及市場影響。",
    "Scams, overconfidence, leverage and unreliable information.":
        "騙局、過度自信、槓桿及不可靠資料。",
    "Core concepts": "核心概念",
    "Pattern workshop": "形態工作坊",
    "Charting extension": "圖表延伸",
    "Trade mechanics": "交易機制",
    "Company research": "公司研究",
    "Case studies": "個案",
    "Safety and discipline": "安全與紀律",
    "Choose an answer before revealing the result.": "揭示結果前請先選擇答案。",
})
