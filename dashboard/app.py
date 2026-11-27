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

TOP_NAV = ["Home", "Market Overview", "Screener", "Stock Research"]
LEGACY_MARKET_NAV = {
    "Overview": "Market Overview", "Screener": "Screener", "Live quotes": "Market Overview",
    "Returns & risk": "Screener", "Returns & Risk": "Screener", "Stock": "Stock Research",
}
LEARN_TABS = ["Start here", "Data & methods"]
UP_COLOR = "#089981"
DOWN_COLOR = "#f23645"
PREV_CLOSE_COLOR = "#787b86"
GRID_COLOR = "#f0f3fa"
SPIKE_COLOR = "#9598a1"

CHART_RANGES = {
    "1D": {"period": "1d", "interval": "5m"},
    "1M": {"period": "1mo", "interval": "1d"},
    "6M": {"period": "6mo", "interval": "1d"},
    "1Y": {"period": "1y", "interval": "1d"},
}
CHART_TYPES = ["Candle", "Line", "Area"]
INTRADAY_RANGES = {"1D"}
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
        "name_zh": "標普500指數",
        "blurb": "500 leading U.S. large-cap companies across major sectors",
        "blurb_zh": "涵蓋美國主要行業的500家大型上市公司",
        "unit": "point",
        "badge": "500",
        "badge_bg": "#f23645",
        "proxy": "SPY",
        "members": "500 companies · Float-adjusted market-cap weighted",
        "members_zh": "500家公司 · 自由流通市值加權",
        "about": (
            "The S&P 500 tracks 500 leading U.S. large-cap companies across major sectors. "
            "It is weighted by float-adjusted market capitalization, so companies with larger float-adjusted market values "
            "have a greater influence on the index."
        ),
        "about_zh": (
            "標普500指數追蹤500家美國大型上市公司，涵蓋多個主要行業。指數按自由流通市值加權，"
            "因此可投資市值較大的公司對指數走勢影響更大。"
        ),
        "related": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"],
    },
    "^NDX": {
        "display": "NDX",
        "name": "NASDAQ 100",
        "name_zh": "納斯達克100指數",
        "blurb": "100 of the largest non-financial companies listed on Nasdaq",
        "blurb_zh": "納斯達克上市的100家大型非金融公司",
        "unit": "point",
        "badge": "100",
        "badge_bg": "#2962ff",
        "proxy": "QQQ",
        "members": "100 companies · Modified market-cap weighted",
        "members_zh": "100家公司 · 經修訂市值加權",
        "about": (
            "The Nasdaq-100 tracks 100 of the largest non-financial companies listed on the Nasdaq Stock Market. "
            "Because many of its largest members are technology and growth companies, it is widely used as a benchmark "
            "for the technology sector and U.S. large-cap growth. The index uses modified market-capitalization weighting."
        ),
        "about_zh": (
            "納斯達克100指數追蹤在納斯達克上市的100家大型非金融公司。由於多家大型成分公司屬於科技及成長型企業，"
            "市場廣泛以它作為觀察科技板塊及美國大型成長股的重要基準。指數採用經修訂的市值加權方法。"
        ),
        "related": ["NVDA", "AAPL", "MSFT", "AMZN", "META"],
    },
    "^DJI": {
        "display": "DJI",
        "name": "Dow Jones Industrial Average",
        "name_zh": "道瓊斯工業平均指數",
        "blurb": "30 U.S. blue-chip companies, weighted by share price",
        "blurb_zh": "由30家美國藍籌公司組成，按股價加權",
        "unit": "point",
        "badge": "30",
        "badge_bg": "#131722",
        "proxy": "DIA",
        "members": "30 companies · Price-weighted",
        "members_zh": "30家公司 · 股價加權",
        "about": (
            "The Dow Jones Industrial Average tracks 30 established U.S. blue-chip companies across mature industries. "
            "It is a long-standing gauge of traditional blue-chip businesses and uses price weighting, so each company's "
            "share price—not its total market value—determines its weight in the index. Its members also include major "
            "technology companies."
        ),
        "about_zh": (
            "道瓊斯工業平均指數由30家美國成熟藍籌企業組成，是觀察傳統大型藍籌公司的重要指標。"
            "指數按股價加權，因此成分股的股價，而非公司總市值，決定其在指數中的權重；成分股亦包括大型科技公司。"
        ),
        "related": ["JPM", "UNH", "HD", "CAT", "MCD"],
    },
}

# Editorial copy for the three index detail pages. Each page uses the same
# layout, but the explanation is specific to the index's construction and role.
INDEX_GUIDE = {
    "^GSPC": {
        "eyebrow": "A BROAD MEASURE OF U.S. LARGE-CAP STOCKS",
        "eyebrow_zh": "觀察美國大型上市公司的重要指標",
        "lead": (
            "The S&P 500 tracks 500 selected large U.S. companies across major parts of the economy, including technology, "
            "healthcare, financials and consumer businesses. According to S&P Dow Jones Indices, the index covers approximately "
            "80% of the available U.S. equity market capitalization. The companies in the index therefore represent a large share "
            "of the value of the U.S. stock market, making the S&P 500 a widely used measure of the performance of U.S. large-cap stocks."
        ),
        "lead_zh": (
            "標普500指數追蹤500家經挑選的美國大型上市公司，涵蓋科技、醫療保健、金融及消費等主要經濟領域。根據標普道瓊斯指數公司的資料，"
            "標普500涵蓋約80%的美國可投資股票市值。換言之，這500家公司合計佔美國股票市場相當大的比重，因此標普500常被用來觀察美國大型股市場的整體表現。"
        ),
        "composition": "500 selected large U.S. companies across major industries",
        "composition_zh": "500家橫跨主要行業的美國大型上市公司",
        "weighting": "Float-adjusted market-cap weighted",
        "weighting_zh": "自由流通市值加權",
        "market_lens": "The performance of major U.S. large-cap companies",
        "market_lens_zh": "美國大型上市公司的整體表現",
        "why_important": (
            "The S&P 500 is one of the main benchmarks used to describe the U.S. stock market. Investors compare funds and "
            "portfolios with it to see how their results measure up against large U.S. companies over the same period. Many "
            "index funds and ETFs are designed to track the S&P 500, so its performance affects how millions of people follow "
            "their investments and long-term savings. Financial news also uses it as a headline measure of the U.S. market."
        ),
        "why_important_zh": (
            "標普500是觀察美國股市時最常用的基準之一。投資者會把基金及個人投資組合的回報與標普500比較，了解自己的投資在同一段期間"
            "相對於美國大型公司表現如何。許多指數基金及ETF都以追蹤標普500為目標，因此它的升跌與大眾的投資及長期儲蓄息息相關。"
            "財經新聞亦經常用它作為報道美國股市的主要指標。"
        ),
        "weighting_explained": (
            "Companies are assessed for inclusion using criteria such as large-cap size, public float, trading liquidity, financial "
            "viability and sector representation. Trading activity is one part of the liquidity test, helping ensure that index "
            "constituents can be traded by investors and funds that track the index. Once selected, companies are weighted by "
            "float-adjusted market capitalization: the share price multiplied by the number of shares available to public investors. "
            "A company with a larger investable market value receives a higher index weight, so a 2% move in that company has a "
            "greater effect on the index than a 2% move in a smaller-weighted company."
        ),
        "weighting_explained_zh": (
            "公司入選時會按多項條件評估，包括大型企業市值、公開流通股份、交易流動性、財務狀況及行業代表性。交易活躍程度是流動性評估的一部分，"
            "確保成分股有足夠市場交易，方便投資者及追蹤指數的基金買賣。入選後，標普500採用自由流通市值加權：以股價乘以可供公眾投資者買賣的股份數目，"
            "計算每家公司的指數權重。可投資市值愈大的公司，權重愈高；因此，同樣上升2%，權重較高的公司對指數帶來的影響也會更大。"
        ),
    },
    "^NDX": {
        "eyebrow": "LARGE NON-FINANCIAL COMPANIES LISTED ON NASDAQ",
        "eyebrow_zh": "納斯達克上市的大型非金融企業",
        "lead": (
            "The Nasdaq-100 follows 100 of the largest non-financial companies listed on the Nasdaq Stock Market. Its members "
            "include major businesses in software, semiconductors, internet services, retail, consumer products and healthcare. "
            "Because many of its largest members are influential technology companies, the market widely uses the Nasdaq-100 "
            "as a benchmark for technology stocks and U.S. large-cap growth."
        ),
        "lead_zh": (
            "納斯達克100指數追蹤在納斯達克股票市場上市的100家大型非金融公司，涵蓋軟件、半導體、互聯網服務、零售、消費產品及醫療保健等領域。"
            "由於多家大型成分公司是具全球影響力的科技企業，市場廣泛以納斯達克100作為觀察科技股及美國大型成長股的重要基準。"
        ),
        "composition": "100 of the largest Nasdaq-listed non-financial companies",
        "composition_zh": "納斯達克上市的100家大型非金融公司",
        "weighting": "Modified market-cap weighted",
        "weighting_zh": "經修訂市值加權",
        "market_lens": "Large Nasdaq-listed companies, especially growth and technology leaders",
        "market_lens_zh": "納斯達克大型企業，尤其是成長型及科技領軍公司",
        "why_important": (
            "Investors and financial news outlets watch the Nasdaq-100 to follow the direction of major technology and growth "
            "companies. Its performance is often compared with the S&P 500 to show whether technology-led and growth-oriented "
            "stocks are rising faster or falling further than the broader U.S. large-cap market."
        ),
        "why_important_zh": (
            "投資者及財經媒體會透過納斯達克100觀察大型科技及成長型公司的市場走勢。把它與標普500比較，可以看出科技及成長股的表現"
            "是領先美國大型股市場，還是落後於整體市場。"
        ),
        "weighting_explained": (
            "The Nasdaq-100 uses modified market-cap weighting. Company size provides the starting point: larger companies generally "
            "receive larger weights. Nasdaq's methodology then adjusts those weights and applies concentration limits at scheduled "
            "reviews. This keeps the index linked to the market value of its members while managing the influence of its largest "
            "companies. The result is an index where major companies have a strong influence, with weighting rules guiding how "
            "that influence is distributed."
        ),
        "weighting_explained_zh": (
            "納斯達克100採用經修訂市值加權，首先以公司的市值作為權重基礎，規模較大的公司通常佔有較高比重。納斯達克再按照指數方法，"
            "在定期檢討時調整權重及集中度上限。這套安排讓指數反映成分公司的市場價值，同時管理最大型公司的影響力，令整體權重按照既定規則分配。"
        ),
    },
    "^DJI": {
        "eyebrow": "A LONG-STANDING GAUGE OF U.S. BLUE-CHIP COMPANIES",
        "eyebrow_zh": "歷史悠久的美國藍籌股指標",
        "lead": (
            "The Dow Jones Industrial Average, commonly called the Dow, is one of the world's best-known traditional blue-chip "
            "benchmarks. It began in 1896 with 12 stocks and expanded to 30 companies in 1928. Today, it tracks 30 established "
            "U.S. blue-chip businesses, with strong representation from mature industries such as finance, industrials, healthcare "
            "and consumer goods. The index also includes several major technology companies, but its role is to follow established "
            "blue-chip stocks rather than serve as the market's main technology benchmark."
        ),
        "lead_zh": (
            "道瓊斯工業平均指數通常簡稱「道指」，是美國歷史悠久的傳統藍籌股指標。它於1896年以12隻股票開始計算，並於1928年擴展至30家公司。"
            "今天，道指追蹤30家美國成熟大型藍籌企業，主要涵蓋金融、工業、醫療保健及消費等行業。成分股中亦有蘋果、微軟及英偉達等科技公司，"
            "但道指的定位是觀察成熟藍籌企業，而非作為市場觀察科技股的主要基準。"
        ),
        "composition": "30 established U.S. blue-chip companies",
        "composition_zh": "30家成熟的美國藍籌企業",
        "weighting": "Price-weighted",
        "weighting_zh": "股價加權",
        "market_lens": "The performance of 30 established U.S. blue-chip companies",
        "market_lens_zh": "30家美國大型藍籌企業的表現",
        "why_important": (
            "The Dow is widely followed because it has appeared in market reports for generations and offers a familiar reading "
            "of established U.S. blue-chip companies. It gives investors and the public a quick view of how major, mature businesses "
            "are performing, while the Nasdaq-100 is more commonly used to track technology and growth stocks."
        ),
        "why_important_zh": (
            "道指長年出現在財經新聞中，是大眾觀察美國成熟藍籌企業表現的熟悉指標。它讓投資者快速了解大型傳統企業的整體走勢；"
            "至於科技股及成長型公司的市場方向，市場更常參考納斯達克100。"
        ),
        "weighting_explained": (
            "The Dow uses price weighting. Its calculation is based on the share prices of its 30 companies, added together and "
            "divided by an adjusted divisor. The divisor is maintained to account for events such as stock splits and changes "
            "to the index members. A higher-priced share therefore has more influence on the index than a lower-priced share. "
            "For example, a 2% move in a $200 stock has about twice the price-point impact of a 2% move in a $100 stock."
        ),
        "weighting_explained_zh": (
            "道指採用股價加權，計算時會把30家成分公司的股價加總，再除以經調整的除數。除數會因應股份拆細及成分股變動等事件作出調整，"
            "以保持指數計算的連續性。因此，每股價格較高的公司對指數的影響力較大。例如，股價為200美元的股票上升2%，對指數帶來的點數影響，"
            "大約是股價100美元的股票上升2%的兩倍。"
        ),
    },
}

INDEX_ORDER = ["^GSPC", "^NDX", "^DJI"]
INDEX_ALIASES = {
    "SPX": "^GSPC", "SP": "^GSPC", "S&P": "^GSPC", "S&P500": "^GSPC", "SP500": "^GSPC",
    "GSPC": "^GSPC", "^GSPC": "^GSPC", "SNP": "^GSPC",
    "NDX": "^NDX", "NASDAQ": "^NDX", "NASDAQ100": "^NDX", "IXIC": "^NDX",
    "^NDX": "^NDX",
    "DJI": "^DJI", "DJIA": "^DJI", "DOW": "^DJI", "DOWJONES": "^DJI",
    "DOWJONESINDUSTRIALAVERAGE": "^DJI", "^DJI": "^DJI",
}

UNIVERSE = {
    "AAPL": "Information Technology", "MSFT": "Information Technology",
    "NVDA": "Information Technology", "AVGO": "Information Technology",
    "ORCL": "Information Technology", "CRM": "Information Technology",
    "AMD": "Information Technology", "QCOM": "Information Technology",
    "INTC": "Information Technology", "CSCO": "Information Technology",
    "ADBE": "Information Technology", "IBM": "Information Technology",
    "GOOGL": "Communication Services", "META": "Communication Services",
    "DIS": "Communication Services", "NFLX": "Communication Services",
    "AMZN": "Consumer Discretionary", "HD": "Consumer Discretionary",
    "NKE": "Consumer Discretionary", "MCD": "Consumer Discretionary",
    "WMT": "Consumer Staples", "COST": "Consumer Staples",
    "KO": "Consumer Staples", "PG": "Consumer Staples",
    "JPM": "Financials", "BAC": "Financials", "GS": "Financials",
    "MS": "Financials", "V": "Financials", "MA": "Financials",
    "PYPL": "Financials", "BRK-B": "Financials",
    "LLY": "Health Care", "JNJ": "Health Care", "UNH": "Health Care",
    "ABBV": "Health Care", "MRK": "Health Care", "PFE": "Health Care",
    "ISRG": "Health Care",
    "CAT": "Industrials", "GE": "Industrials", "RTX": "Industrials",
    "HON": "Industrials", "UPS": "Industrials", "DE": "Industrials",
    "XOM": "Energy", "CVX": "Energy", "SLB": "Energy",
    "SPY": "Market benchmark", "QQQ": "Market benchmark", "DIA": "Market benchmark",
}

GROUP_LABELS_ZH = {
    "Information Technology": "資訊科技",
    "Communication Services": "通訊服務",
    "Consumer Discretionary": "非必需消費",
    "Consumer Staples": "必需消費",
    "Financials": "金融",
    "Health Care": "醫療保健",
    "Industrials": "工業",
    "Energy": "能源",
    "Market benchmark": "市場基準 ETF",
    "Other": "其他",
}


def group_label(group: str) -> str:
    """Return a localized label for one unambiguous universe group."""
    if is_zh() and group in GROUP_LABELS_ZH:
        return GROUP_LABELS_ZH[group]
    return t(group)

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
  .home-index-intro {
    background: #ffffff;
    border: 1px solid #e0e3eb;
    border-radius: 12px;
    padding: 1rem 1.15rem;
    margin: 0 0 1rem 0;
    color: #4c4f59;
    line-height: 1.65;
  }
  div[class*="st-key-home_learning_banner"] [data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(112deg, #edf6f2 0%, #e2f0ea 100%) !important;
    border: 1px solid #c5ddd2 !important;
    border-left: 5px solid #4a927b !important;
    border-radius: 15px !important;
    padding: 0.9rem 1.15rem !important;
    box-shadow: 0 4px 14px rgba(19, 55, 43, 0.07);
  }
  .home-learning-eyebrow {
    margin: 0 0 0.35rem 0; color: #477868; font-size: 0.72rem;
    font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase;
  }
  .home-learning-title {
    margin: 0 0 0.35rem 0; color: #173d32; font-size: 1.28rem;
    font-weight: 800; letter-spacing: -0.025em; line-height: 1.3;
  }
  .home-learning-copy {
    margin: 0; color: #405d53; font-size: 0.9rem; line-height: 1.6;
  }
  div.st-key-home_start_learning button {
    min-height: 3.15rem !important; width: 100% !important;
    border-radius: 10px !important; border: 1px solid #7eaa98 !important;
    background: #d2e8de !important; color: #173d32 !important;
    font-size: 0.98rem !important; font-weight: 800 !important;
    box-shadow: 0 2px 7px rgba(19, 55, 43, 0.08);
  }
  div.st-key-home_start_learning button:hover {
    background: #c1dfd1 !important; border-color: #5c947e !important;
  }
  div.st-key-home_start_learning button p { color: #173d32 !important; font-weight: 800 !important; }
  .home-index-intro > p { margin: 0 0 0.65rem 0; }
  .home-index-intro-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.5rem 1.1rem; }
  .home-index-intro-list p { margin: 0; font-size: 0.88rem; }
  .home-index-intro-list strong { color: #131722; }
  div[class*="st-key-idx_card_"] { margin-bottom: 0.55rem; }
  @media (max-width: 900px) {
    .home-index-intro-list { grid-template-columns: 1fr; gap: 0.45rem; }
  }
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
  .index-education-hero {
    background: #ffffff;
    border: 1px solid #e0e3eb;
    border-radius: 16px;
    padding: 1.45rem 1.55rem 1.35rem;
    margin: 0.85rem 0 0.9rem;
    box-shadow: 0 1px 2px rgba(19, 23, 34, 0.035);
  }
  .index-education-kicker {
    color: #787b86;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    margin-bottom: 0.55rem;
  }
  .index-education-title {
    color: #131722;
    font-size: clamp(1.55rem, 3vw, 2.15rem);
    font-weight: 800;
    letter-spacing: -0.045em;
    line-height: 1.12;
    margin: 0;
  }
  .index-education-symbol {
    display: inline-block;
    vertical-align: middle;
    margin-left: 0.55rem;
    padding: 0.18rem 0.48rem;
    border-radius: 6px;
    background: #f0f3fa;
    color: #6a6d78;
    font-size: 0.78rem;
    font-weight: 750;
    letter-spacing: 0;
  }
  .index-education-dek {
    margin: 0.55rem 0 0;
    color: #555a66;
    font-size: 1rem;
    font-weight: 650;
    line-height: 1.5;
  }
  .index-education-lead {
    max-width: 1040px;
    margin: 1.05rem 0 0;
    color: #303541;
    font-size: 1.02rem;
    line-height: 1.86;
  }
  .index-fact-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin: 0.85rem 0 0.9rem;
  }
  .index-fact {
    min-width: 0;
    padding: 0.85rem 0.95rem;
    background: #ffffff;
    border: 1px solid #e0e3eb;
    border-radius: 12px;
  }
  .index-fact-label {
    color: #787b86;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-bottom: 0.32rem;
  }
  .index-fact-value {
    color: #202532;
    font-size: 0.92rem;
    font-weight: 700;
    line-height: 1.48;
  }
  .index-basics-note {
    margin: 0.9rem 0 0.25rem;
    padding: 0.9rem 1rem;
    border: 1px solid #dfe5ef;
    border-radius: 10px;
    background: #fbfcfe;
    color: #4b5260;
    font-size: 0.9rem;
    line-height: 1.7;
  }
  .index-explain-card {
    height: 100%;
    padding: 1rem 1.05rem;
    border: 1px solid #e0e3eb;
    border-radius: 12px;
    background: #ffffff;
  }
  .index-learning-section { margin: 0.85rem 0; }
  .index-explain-title {
    margin: 0 0 0.5rem;
    color: #202532;
    font-size: 0.95rem;
    font-weight: 750;
    line-height: 1.4;
  }
  .index-explain-body {
    margin: 0;
    color: #424753;
    font-size: 0.9rem;
    line-height: 1.75;
  }
  .index-explain-grid [data-testid="column"] { display: flex; }
  .index-reading-note {
    border-left: 3px solid #2962ff;
    background: #f7f9fd;
    border-radius: 0 10px 10px 0;
    padding: 0.85rem 1rem;
    margin: 0.85rem 0 1.15rem;
    color: #424753;
    font-size: 0.9rem;
    line-height: 1.65;
  }
  .index-quote-strip {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
    padding: 0.8rem 0;
    border-top: 1px solid #e0e3eb;
    border-bottom: 1px solid #e0e3eb;
    margin: 1.1rem 0 1.15rem;
  }
  .index-quote-label {
    color: #787b86;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  .index-quote-value {
    color: #131722;
    font-size: 1.45rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    font-variant-numeric: tabular-nums;
  }
  .index-constituent-caption {
    color: #6a6d78;
    font-size: 0.84rem;
    margin: 0.1rem 0 0.65rem;
  }
  @media (max-width: 900px) {
    .index-fact-grid { grid-template-columns: 1fr; }
    .index-education-hero { padding: 1.1rem 1rem; }
  }
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


def index_text(ticker: str, field: str) -> str:
    """Return index copy in the active app language."""
    meta = INDEX_META[ticker]
    localized_key = f"{field}_zh"
    if is_zh() and localized_key in meta:
        return meta[localized_key]
    return t(meta[field])


def index_guide_text(ticker: str, field: str) -> str:
    """Return index-specific editorial copy in the active app language."""
    guide = INDEX_GUIDE[ticker]
    localized_key = f"{field}_zh"
    if is_zh() and localized_key in guide:
        return guide[localized_key]
    return guide[field]


def index_name(ticker: str) -> str:
    return index_text(ticker, "name")


def company_name(ticker: str) -> str:
    if ticker in INDEX_META:
        return index_name(ticker)
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
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert(None).dt.normalize()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    df = df.dropna(subset=["close"]).sort_values(["ticker", "date"])
    return df.reset_index(drop=True)


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
        else:
            return pd.DataFrame()
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
    temp = temp[temp["ticker"].map(UNIVERSE).ne("Market benchmark")].copy()
    if temp.empty:
        return None
    temp["month"] = pd.to_datetime(temp["date"]).dt.to_period("M").dt.to_timestamp()
    month_ends = temp.sort_values("date").groupby(["ticker", "month"], as_index=False).tail(1)
    pivot = month_ends.pivot(index="ticker", columns="month", values="close").sort_index(axis=1)
    monthly_returns = pivot.pct_change(axis=1, fill_method=None) * 100
    if monthly_returns.empty:
        return None
    monthly_returns = monthly_returns.iloc[:, 1:]
    if monthly_returns.empty:
        return None
    monthly_returns["Sector"] = [UNIVERSE.get(sym, "Other") for sym in monthly_returns.index]
    sector_returns = monthly_returns.groupby("Sector").mean(numeric_only=True)
    if sector_returns.empty or sector_returns.shape[1] == 0:
        return None
    labels = [pd.Timestamp(c).strftime("%Y-%m") for c in sector_returns.columns]
    sector_word = "板塊" if is_zh() else "Sector"
    average_word = "平均回報" if is_zh() else "Average return"
    hover_template = (
        f"{sector_word}: %{{y}}<br>{t('Month')}: %{{x}}<br>"
        f"{average_word}: %{{z:.2f}}%<extra></extra>"
    )
    chart_title = (
        "板塊每月回報（0% 代表持平 · 各板塊內等權平均）"
        if is_zh() else
        "Sector monthly returns (0% = unchanged · equal-weighted within each sector)"
    )
    fig = go.Figure(data=go.Heatmap(
        z=sector_returns.values,
        x=labels,
        y=[group_label(sector) for sector in sector_returns.index.tolist()],
        colorscale="RdYlGn",
        zmid=0,
        colorbar={"title": t("Monthly %")},
        hovertemplate=hover_template,
    ))
    fig.update_layout(
        title=dict(text=chart_title, x=0.5, xanchor="center"),
        xaxis_title=t("Month"),
        yaxis_title=sector_word,
        height=420,
        margin=dict(l=10, r=10, t=70, b=10),
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
    pad = (ymax - ymin) * 0.08 if ymax > ymin else max(abs(ymin) * 0.01, 0.5)

    tickformat = "%I:%M %p" if range_key == "1D" else "%b %d"

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
    st.session_state.watchlist = [sym for sym in st.session_state.get("watchlist", []) if sym != ticker]


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
        or lower in meta.get("name_zh", "").casefold()
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
    previous_nav = st.session_state.nav
    if previous_nav == "Markets":
        previous_tab = st.session_state.get("_pending_markets_tab") or st.session_state.get("markets_tab") or st.session_state.get("markets_tab_persist", "Overview")
        st.session_state.nav = LEGACY_MARKET_NAV.get(previous_tab, "Market Overview")
        st.session_state._pending_nav_pills = st.session_state.nav
    elif previous_nav == "Returns & Risk":
        st.session_state.nav = "Screener"
        st.session_state._pending_nav_pills = "Screener"
    elif previous_nav not in [*TOP_NAV, "Index", "Lesson"]:
        st.session_state.nav = "Home"
        st.session_state._pending_nav_pills = "Home"
    st.session_state.setdefault("markets_tab_persist", "Overview")
    st.session_state.setdefault("learn_tab_persist", "Start here")
    st.session_state.setdefault("selected_symbol", "^GSPC")
    if not st.session_state.get("_home_default_index_migrated", False):
        if st.session_state.get("selected_symbol") == "AAPL":
            st.session_state.selected_symbol = "^GSPC"
        st.session_state._home_default_index_migrated = True
    st.session_state.setdefault("chart_range_persist", "1D")
    if st.session_state.chart_range_persist not in CHART_RANGES:
        st.session_state.chart_range_persist = "1Y" if st.session_state.chart_range_persist == "All Time" else "1D"
    st.session_state.setdefault("chart_type_persist", "Candle")
    if not st.session_state.get("_default_candle_migrated", False):
        if st.session_state.get("chart_type_persist") == "Line" and "chart_type" not in st.session_state:
            st.session_state.chart_type_persist = "Candle"
        st.session_state._default_candle_migrated = True
    if st.session_state.chart_type_persist not in CHART_TYPES:
        st.session_state.chart_type_persist = "Candle"
    if st.session_state.get("chart_range") not in CHART_RANGES:
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
    if st.session_state.idx_chart_range_persist not in CHART_RANGES:
        st.session_state.idx_chart_range_persist = "1Y" if st.session_state.idx_chart_range_persist == "All Time" else "1D"
    if st.session_state.get("idx_chart_range") not in CHART_RANGES:
        st.session_state.idx_chart_range = st.session_state.idx_chart_range_persist
    st.session_state.setdefault("idx_chart_type_persist", "Candle")
    if st.session_state.idx_chart_type_persist not in CHART_TYPES:
        st.session_state.idx_chart_type_persist = "Candle"
    if st.session_state.get("idx_chart_type") not in CHART_TYPES:
        st.session_state.idx_chart_type = st.session_state.idx_chart_type_persist


def render_top_nav() -> None:
    brand, navigation, tools = st.columns([0.95, 5.05, 2.4], gap="small", vertical_alignment="center")
    with brand:
        st.markdown('<div class="topnav"><div class="brand">StockScope</div></div>', unsafe_allow_html=True)
    with navigation:
        apply_pending_nav_pills()
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
        f'<div class="idx-name">{html.escape(index_name(ticker))}<span class="idx-ticker">{html.escape(meta["display"])}</span></div>'
        f'<div class="idx-blurb">{html.escape(index_text(ticker, "blurb"))}</div>'
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
    """Show the three major U.S. indices as horizontal cards, in INDEX_ORDER."""
    cols = st.columns(3, gap="small")
    for col, ticker in zip(cols, INDEX_ORDER):
        meta = INDEX_META[ticker]
        with col:
            with st.container(border=True, key=widget_key("idx_card", ticker)):
                info, plus_col, open_col = st.columns([4.15, 0.55, 0.55])
                with info:
                    st.markdown(index_card_title_html(ticker), unsafe_allow_html=True)
                with plus_col:
                    if st.button(
                        "＋",
                        key=widget_key("idx_add", ticker),
                        help=t("Add {proxy} (tracks this index) to Watchlist", proxy=meta["proxy"]),
                    ):
                        st.session_state.flash = add_to_watchlist(meta["proxy"])
                        st.rerun()
                with open_col:
                    if st.button(
                        "↗",
                        key=widget_key("idx_open", ticker),
                        help=t("Open {name} page", name=index_name(ticker)),
                    ):
                        open_index_page(ticker)
                        st.rerun()
                st.markdown(
                    index_card_quote_html(ticker, lookup_snapshot(snap, ticker)),
                    unsafe_allow_html=True,
                )


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
    """Explain the selected index first, then provide its quote and price chart."""
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
        except Exception:
            snap_prices = pd.DataFrame()
    snap = snapshot_from_prices(snap_prices)
    quote = lookup_snapshot(snap, ticker)

    if st.session_state.get("index_full_chart"):
        top_l, top_r = st.columns([3.4, 1])
        with top_l:
            st.markdown(
                f'<p class="quote-name">{html.escape(index_name(ticker))}'
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
        unit_text = t(meta["unit"])
        st.markdown(
            f'<div class="quote-last">{html.escape(format_last(ticker, last))} '
            f'<span class="last-unit">{html.escape(unit_text)}</span> '
            f'<span class="{chg_class(chg_pct)}">{html.escape(format_chg(chg))} {html.escape(format_chg(chg_pct, True))}</span></div>',
            unsafe_allow_html=True,
        )
        _index_chart_figure(ticker, snap, tall=True)
        st.caption(t("Full chart uses the same data as the index page. Weekends and closed hours stay hidden. Yahoo Finance; may be delayed."))
        return

    nav_l, nav_mid, nav_r = st.columns([1.2, 2.5, 2.0])
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
            format_func=lambda symbol: INDEX_META[symbol]["display"],
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

    kicker = index_guide_text(ticker, "eyebrow")
    lead = index_guide_text(ticker, "lead")
    dek = index_text(ticker, "blurb")
    page_name = index_name(ticker)
    st.markdown(
        f'<section class="index-education-hero">'
        f'<div class="index-education-kicker">{html.escape(kicker)}</div>'
        f'<h1 class="index-education-title">{html.escape(page_name)}'
        f'<span class="index-education-symbol">{html.escape(meta["display"])}</span></h1>'
        f'<p class="index-education-dek">{html.escape(dek)}</p>'
        f'</section>',
        unsafe_allow_html=True,
    )

    what_heading = "What is it?" if not is_zh() else "是甚麼？"
    why_heading = "Why does it matter?" if not is_zh() else "為甚麼重要？"
    how_heading = "How does it work?" if not is_zh() else "怎樣運作？"
    learning_sections = [
        (what_heading, lead),
        (why_heading, index_guide_text(ticker, "why_important")),
        (how_heading, index_guide_text(ticker, "weighting_explained")),
    ]
    for section_heading, section_copy in learning_sections:
        st.markdown(
            f'<section class="index-explain-card index-learning-section">'
            f'<h2 class="index-explain-title">{html.escape(section_heading)}</h2>'
            f'<p class="index-explain-body">{html.escape(section_copy)}</p>'
            f'</section>',
            unsafe_allow_html=True,
        )

    last = quote.get("last", np.nan)
    chg = quote.get("chg", np.nan)
    chg_pct = quote.get("chg_pct", np.nan)
    if pd.notna(last):
        quote_label = "Latest index level" if not is_zh() else "最新指數點數"
        unit_text = t(meta["unit"])
        quote_html = (
            f'<div class="index-quote-strip"><div>'
            f'<div class="index-quote-label">{quote_label}</div>'
            f'<div class="index-quote-value">{html.escape(format_last(ticker, last))} '
            f'<span class="last-unit">{html.escape(unit_text)}</span></div></div>'
            f'<div class="{chg_class(chg_pct)}">{html.escape(format_chg(chg))} '
            f'({html.escape(format_chg(chg_pct, True))})</div></div>'
        )
        st.markdown(quote_html, unsafe_allow_html=True)
    else:
        unavailable_note = (
            "最新指數報價暫時無法取得，價格圖表仍會另外嘗試載入。"
            if is_zh() else
            "The latest index quote is unavailable; the price chart will still try to load."
        )
        st.caption(unavailable_note)

    chart_heading = "Explore the index price history" if not is_zh() else "查看指數價格走勢"
    st.markdown(f"### {chart_heading}")
    _index_chart_figure(ticker, snap, tall=False)
    chart_note = (
        "圖表資料由 Yahoo Finance 透過 yfinance 提供，可能有所延遲。可透過歷史走勢了解指數在不同時期的價格變化。"
        if is_zh() else
        "Chart data is supplied by Yahoo Finance via yfinance and may be delayed. Use the historical chart to explore how the index price has changed over time."
    )
    st.caption(chart_note)

    members_heading = "Examples of constituent companies" if not is_zh() else "部分成分公司例子"
    members_note = (
        "Selected examples of companies in the index. Select a company to continue to its stock page."
        if not is_zh() else
        "以下列出部分具代表性的成分公司。點選公司可繼續查看其股票資料。"
    )
    st.markdown(f"#### {members_heading}")
    st.markdown(f'<p class="index-constituent-caption">{html.escape(members_note)}</p>', unsafe_allow_html=True)
    rel = st.columns(len(meta["related"]))
    for col, symbol in zip(rel, meta["related"]):
        label = f"{symbol} · {company_name(symbol)}"
        if col.button(label, key=f"idx_rel_{symbol}", width="stretch"):
            st.session_state.selected_symbol = symbol
            go_to("Home")
            st.rerun()

    data_note = (
        f"{proxy} is an ETF designed to track this index. Add it to your watchlist to follow the ETF's market price."
        if not is_zh() else
        f"{proxy} 是追蹤此指數的 ETF。加入自選股後，即可查看這項 ETF 的市場價格。"
    )
    st.caption(data_note)


def render_home_learning_entry() -> None:
    """Prominent homepage entry to the existing structured learning experience."""
    with st.container(border=True, key="home_learning_banner"):
        copy_col, action_col = st.columns([3.7, 1.25], gap="large", vertical_alignment="center")
        with copy_col:
            if is_zh():
                st.markdown(
                    '<div class="home-learning-eyebrow">STOCKSCOPE LEARN · 正式課程</div>'
                    '<div class="home-learning-title">從零開始，系統學懂美股</div>'
                    '<p class="home-learning-copy">由股票市場基礎、報價與K線，到技術指標、交易流程及公司研究，循序建立金融知識。</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="home-learning-eyebrow">STOCKSCOPE LEARN · STRUCTURED COURSE</div>'
                    '<div class="home-learning-title">Learn the U.S. stock market, step by step</div>'
                    '<p class="home-learning-copy">Build your knowledge from market basics and price charts to technical indicators, trade execution and company research.</p>',
                    unsafe_allow_html=True,
                )
        with action_col:
            button_label = "開始正式學習 →" if is_zh() else "Start learning →"
            if st.button(button_label, key="home_start_learning", type="primary", width="stretch"):
                st.session_state["_scroll_to_top"] = True
                go_to("Lesson", learn_tab="Start here")
                st.rerun()


def render_chart_reading_lesson() -> None:
    """A 3-month annotated S&P 500 proxy chart for first-time chart readers."""
    heading = "先學識看圖：用標普 500 作例子" if is_zh() else "Learn to read a chart: the S&P 500 as an example"
    intro = (
        "先認清圖表的三個部分：K 線看價格、量能柱看成交活躍程度、均線看一段時間的平均價格。"
        "以下使用追蹤標普 500 的 SPY ETF 近三個月日 K 線作示範；留意，成交量是 SPY ETF 本身的成交股數，並非標普 500 指數直接成交量。"
        if is_zh() else
        "Start with three parts: candlesticks show price, volume bars show trading activity, and moving averages smooth price over time. "
        "This example uses three months of daily SPY candles (an ETF tracking the S&P 500). Its volume is SPY ETF shares traded—not direct index volume."
    )
    st.markdown(f"### {heading}")
    st.markdown(intro)

    with st.spinner(t("Loading chart…")):
        try:
            frame = download_ohlc("SPY", "3mo", "1d")
        except Exception:
            frame = pd.DataFrame()

    required = {"Open", "High", "Low", "Close"}
    if frame.empty or not required.issubset(frame.columns):
        st.info("暫時未能載入示範圖表，請稍後再試。" if is_zh() else "The teaching chart is temporarily unavailable. Please try again later.")
        return

    frame = frame.copy()
    if "Volume" not in frame.columns:
        frame["Volume"] = np.nan
    for column in ["Open", "High", "Low", "Close", "Volume"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=["Open", "High", "Low", "Close"]).sort_index()
    if len(frame) < 20:
        st.info("示範數據不足，暫時未能繪製 5 日及 20 日均線。" if is_zh() else "There is not enough data to draw the 5-day and 20-day moving averages yet.")
        return

    close = frame["Close"].astype(float)
    ma5 = close.rolling(window=5, min_periods=5).mean()
    ma20 = close.rolling(window=20, min_periods=20).mean()
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
        row_heights=[0.74, 0.26],
    )
    fig.add_trace(go.Candlestick(
        x=frame.index, open=frame["Open"], high=frame["High"],
        low=frame["Low"], close=frame["Close"], name="SPY",
        increasing=dict(line=dict(color=UP_COLOR, width=1.1), fillcolor=UP_COLOR),
        decreasing=dict(line=dict(color=DOWN_COLOR, width=1.1), fillcolor=DOWN_COLOR),
        hovertemplate=(
            "%{x|%Y-%m-%d}<br>開：%{open:.2f}<br>高：%{high:.2f}<br>低：%{low:.2f}<br>收：%{close:.2f}<extra></extra>"
            if is_zh() else
            "%{x|%Y-%m-%d}<br>Open: %{open:.2f}<br>High: %{high:.2f}<br>Low: %{low:.2f}<br>Close: %{close:.2f}<extra></extra>"
        ),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=frame.index, y=ma5, mode="lines", name="5 日均線" if is_zh() else "5-day MA",
        line=dict(color="#f0a12b", width=1.8), connectgaps=False,
        hovertemplate="5 日均線：%{y:.2f}<extra></extra>" if is_zh() else "5-day MA: %{y:.2f}<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=frame.index, y=ma20, mode="lines", name="20 日均線" if is_zh() else "20-day MA",
        line=dict(color="#2962ff", width=2.0), connectgaps=False,
        hovertemplate="20 日均線：%{y:.2f}<extra></extra>" if is_zh() else "20-day MA: %{y:.2f}<extra></extra>",
    ), row=1, col=1)
    valid_volume = frame["Volume"].notna() & (frame["Volume"] >= 0)
    has_volume = bool(valid_volume.any())
    if has_volume:
        volume_frame = frame.loc[valid_volume]
        fig.add_trace(go.Bar(
            x=volume_frame.index, y=volume_frame["Volume"], name="成交量" if is_zh() else "Volume",
            marker_color=volume_bar_colors(volume_frame), marker_line_width=0, opacity=0.85,
            hovertemplate="成交股數：%{y:,.0f}<extra></extra>" if is_zh() else "Shares traded: %{y:,.0f}<extra></extra>",
        ), row=2, col=1)

    # Keep callout boxes concise so they only name each element cleanly
    # while detailed explanations appear directly below the chart.
    sep16_matches = np.flatnonzero((frame.index.month == 9) & (frame.index.day == 16))
    if len(sep16_matches) > 0:
        candle_i = int(sep16_matches[-1])
    else:
        target_ts = pd.Timestamp(year=frame.index[-1].year, month=9, day=16)
        candle_i = int(np.argmin(np.abs((frame.index - target_ts).total_seconds())))
    candle_x = frame.index[candle_i]
    candle_y = float(frame["Low"].iloc[candle_i])

    ma_valid_positions = np.flatnonzero(ma20.notna().to_numpy())
    ma_i = int(ma_valid_positions[max(0, min(len(ma_valid_positions) - 2, int(len(ma_valid_positions) * 0.75)))])
    ma_x = frame.index[ma_i]
    ma_y = float(ma20.iloc[ma_i])

    callouts = [
        (
            candle_x, candle_y, "x", "y", "center",
            "① K 線｜價格" if is_zh() else "① Candlesticks | Price",
            0, 52,
        ),
        (
            ma_x, ma_y, "x", "y", "center",
            "③ 均線｜平均趨勢" if is_zh() else "③ Moving averages | Trend",
            0, -48,
        ),
    ]
    if has_volume:
        volume_candidates = frame.index[valid_volume]
        vol_pos = max(0, min(len(volume_candidates) - 1, int(len(volume_candidates) * 0.45)))
        vol_x = volume_candidates[vol_pos]
        vol_y = float(frame.loc[vol_x, "Volume"])
        callouts.append((
            vol_x, vol_y, "x2", "y2", "center",
            "② 量能柱｜成交" if is_zh() else "② Volume bars | Activity",
            0, -28,
        ))

    for x_value, y_value, x_ref, y_ref, x_anchor, label, ax, ay in callouts:
        fig.add_annotation(
            x=x_value, y=y_value, xref=x_ref, yref=y_ref, text=label,
            xanchor=x_anchor,
            showarrow=True, arrowhead=3, arrowsize=1.2, arrowwidth=2.2,
            arrowcolor="#64748b", ax=ax, ay=ay,
            bgcolor="rgba(255,255,255,0.98)", bordercolor="#94a3b8",
            borderwidth=1.5, borderpad=9,
            font=dict(size=12.5, color="#263244", family=plotly_font()),
            align="left", opacity=1,
        )

    apply_market_layout(fig, height=700, tickformat="%b %d")
    fig.update_layout(
        showlegend=True,
        margin=dict(l=24, r=76, t=68, b=48),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )
    fig.update_yaxes(side="right", showgrid=True, gridcolor=GRID_COLOR, row=1, col=1)
    fig.update_yaxes(title_text="", showticklabels=False, showgrid=False, row=2, col=1)
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_xaxes(showticklabels=True, showgrid=False, row=2, col=1)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    if not has_volume:
        st.info("目前未能取得 SPY 成交量資料，因此暫時無法顯示量能柱；價格及均線教學仍可閱讀。" if is_zh() else "SPY volume data is unavailable, so volume bars are hidden for now. The price and moving-average lesson remains available.")

    if is_zh():
        lesson_cols = st.columns(3, gap="medium")
        lesson_copy = [
            ("① K 線｜價格", "綠色代表收市高於開市；紅色代表收市低於開市。實體是開市與收市之間，影線延伸至當日高位及低位。"),
            ("② 量能柱｜成交", "柱越高，代表該交易日成交股數越多。成交量要配合價格及市場背景閱讀，不能單靠一根高柱判斷升跌。"),
            ("③ 均線｜平均趨勢", "5 日線及 20 日線會隨每個交易日滾動計算最近 5 或 20 個交易日收市價的平均。市場上還有很多種不同的線，都可以為股價走勢作出解釋，但屬滯後指標，也是出了名的不靠譜。"),
        ]
    else:
        lesson_cols = st.columns(3, gap="medium")
        lesson_copy = [
            ("① Candlesticks | Price", "Green means the close was above the open; red means it was below. The body spans open to close, while the wicks show the period high and low."),
            ("② Volume bars | Activity", "A taller bar means more shares traded that day. Read volume alongside price and market context; one spike alone does not predict direction."),
            ("③ Moving averages | Trend", "The 5-day and 20-day lines rollingly average the latest 5 or 20 trading sessions. There are many different kinds of lines—each can offer an explanation for price behavior, but they lag the market and are famously unreliable."),
        ]
    for col, (title, copy) in zip(lesson_cols, lesson_copy):
        with col:
            st.markdown(f"**{title}**")
            st.caption(copy)
    st.caption(
        "教學示意：SPY 是追蹤標普 500 的 ETF；圖表資料可能延遲。圖表只呈現過往市場活動，不構成買賣建議。"
        if is_zh() else
        "For education only: SPY is an ETF tracking the S&P 500; data may be delayed. Charts show historical activity and are not buy or sell recommendations."
    )


def render_home() -> None:
    home_title = "股市入門。" if is_zh() else "Stock Market Basics"
    home_subtitle = "從香港出發，學會讀懂金融市場" if is_zh() else "Practical stock-market skills, step by step"
    st.markdown(
        f'<div class="hero-title">{home_title}</div>'
        f'<p class="hero-sub">{home_subtitle}</p>',
        unsafe_allow_html=True,
    )

    if is_zh():
        intro_html = (
            '<section class="home-index-intro">'
            '<p>香港作為國際金融中心，近年愈來愈多人關心理財與投資，卻未必知道如何踏出第一步。StockScope 希望把股市中真正實用的硬技能化繁為簡，從市場基礎、閱讀圖表、K線形態與技術指標，到交易流程、公司研究及風險管理，帶領初學者循序漸進建立知識，學會理解市場、分析資訊，並作出更有根據的投資判斷。</p>'
            '</section>'
            '<section class="index-explain-card index-learning-section">'
            '<h2 class="index-explain-title">什麼是指數</h2>'
            '<p class="index-explain-body">由一籃子代表性股票按特定規則加權計算出的指標（如標普 500、納斯達克 100、道瓊斯工業平均指數），用來觀察整類市場或板塊的整體表現，本身不是單一公司股票。</p>'
            '</section>'
            '<section class="index-explain-card index-learning-section">'
            '<h2 class="index-explain-title">什麼是個股</h2>'
            '<p class="index-explain-body">單一上市公司的股票，反映該家公司的營運表現、盈利能力與市場預期；單一個股的波動通常大於大盤指數，需要結合公司基本面與風險承受度來看。</p>'
            '</section>'
        )
    else:
        intro_html = (
            '<section class="home-index-intro">'
            '<p>As an international financial centre, Hong Kong has seen growing interest in personal finance and investing, yet many people are unsure how to get started. StockScope makes practical stock-market skills easier to learn, guiding beginners step by step through market fundamentals, chart reading, candlestick patterns and technical indicators, trading mechanics, company research and risk management—so they can understand markets, assess information and make more informed investment decisions.</p>'
            '</section>'
            '<section class="index-explain-card index-learning-section">'
            '<h2 class="index-explain-title">What is an index</h2>'
            '<p class="index-explain-body">A benchmark calculated from a basket of representative stocks under specific weighting rules (such as the S&amp;P 500, Nasdaq-100, or Dow Jones), used to gauge broader market or sector performance rather than a single company.</p>'
            '</section>'
            '<section class="index-explain-card index-learning-section">'
            '<h2 class="index-explain-title">What is an individual stock</h2>'
            '<p class="index-explain-body">Shares of a single listed company that reflect that company&apos;s operations, earnings, and market expectations, typically with higher single-name volatility than a broad index.</p>'
            '</section>'
        )
    st.markdown(intro_html, unsafe_allow_html=True)

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

    try:
        render_chart_reading_lesson()
    except Exception:
        st.info(
            "K 線教學圖暫時未能載入；上方指數圖表仍可正常使用。" if is_zh()
            else "The chart-reading demo could not load; the index chart above remains available."
        )

    render_home_learning_entry()


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
    active_chart_type = st.session_state.get("chart_type") or st.session_state.get("chart_type_persist") or "Candle"
    with help_col:
        chart_help_button(f"price_{active_chart_type.lower()}", "home")
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
            active_chart_type,
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
        "Screener": t("Filter stocks, rank candidates and compare the shortlisted names."),
        "Stock Research": t("Study one stock or index through its price history and company fundamentals."),
    }
    st.markdown(f'<div class="hero-title">{html.escape(t(section))}</div><p class="hero-sub">{html.escape(descriptions[section])}</p>', unsafe_allow_html=True)

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
    if section == "Screener":
        with group_col:
            sector_options = ["All groups"] + sorted(set(UNIVERSE.values()))
            selected_sector = st.selectbox(
                t("Group filter"), options=sector_options, index=0, key=lang_key("market_group_filter"),
                format_func=group_label,
            )

    prices, metrics, load_error = load_universe(period)
    if prices.empty:
        st.error(t("Could not load daily history. Check the network or Yahoo Finance, then retry."))
        if load_error:
            st.code(load_error)
        return

    if selected_sector != "All groups":
        metrics_view = metrics[metrics["Group"] == selected_sector].copy()
        active_tickers = [ticker for ticker, group in UNIVERSE.items() if group == selected_sector]
    else:
        metrics_view = metrics.copy()
        active_tickers = list(UNIVERSE.keys())
    prices_active = prices[prices["ticker"].isin(active_tickers)].copy()

    if section == "Market Overview":
        render_overview(prices, prices_active, metrics, period)
    elif section == "Screener":
        render_screener(metrics_view, prices, metrics, period)


def render_overview(
    prices: pd.DataFrame,
    prices_active: pd.DataFrame,
    metrics: pd.DataFrame,
    period: str,
) -> None:
    latest_bar_timestamp = pd.to_datetime(prices["date"]).max()
    latest_date = latest_bar_timestamp.date()
    loaded_tickers = prices["ticker"].nunique()
    positive_share = (metrics["Period return (%)"] > 0).mean() * 100 if not metrics.empty else np.nan

    stock_symbols = set(metrics.loc[~metrics["Ticker"].isin(["SPY", "QQQ", "DIA"]), "Ticker"]) if not metrics.empty else set()
    daily_move_rows = []
    if stock_symbols:
        stock_prices = prices[prices["ticker"].isin(stock_symbols)]
        for ticker, group in stock_prices.groupby("ticker"):
            group = group.sort_values("date").dropna(subset=["close"])
            latest_rows = group[group["date"] == latest_bar_timestamp]
            previous_rows = group[group["date"] < latest_bar_timestamp]
            if latest_rows.empty or previous_rows.empty:
                continue
            latest_row = latest_rows.iloc[-1]
            previous_close = float(previous_rows.iloc[-1]["close"])
            latest_close = float(latest_row["close"])
            if previous_close == 0:
                continue
            daily_move_rows.append({
                "Ticker": str(ticker),
                "Day chg (%)": (latest_close / previous_close - 1) * 100,
                "Volume": float(latest_row["volume"]) if pd.notna(latest_row.get("volume")) else np.nan,
            })
    daily_movers = pd.DataFrame(daily_move_rows, columns=["Ticker", "Day chg (%)", "Volume"])
    median_vol = metrics["Ann. volatility (%)"].median() if not metrics.empty else np.nan
    mean_return = metrics["Period return (%)"].mean() if not metrics.empty else np.nan

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(t("Symbols loaded"), f"{loaded_tickers}", help=t("Starter watch universe, not the whole US market."))
    k2.metric(t("Average return · {period}", period=period_label(period)), pct(mean_return))
    k3.metric(t("Share with a positive return"), pct(positive_share))
    k4.metric(t("Median annualized volatility"), pct(median_vol))
    st.caption(t("As of {date} · {period} · {n} starter symbols", date=latest_date, period=period_label(period), n=len(UNIVERSE)))

    fig_heat = make_monthly_sector_heatmap(prices_active)
    if fig_heat is not None:
        help_chart(fig_heat, "heatmap", "heatmap", width="stretch", config={"displayModeBar": False})
    else:
        st.info(t("Not enough history in this window to draw the monthly heatmap."))

    period_movers = metrics.loc[~metrics["Ticker"].astype(str).isin(["SPY", "QQQ", "DIA"])].copy()
    period_movers["Period return (%)"] = pd.to_numeric(
        period_movers["Period return (%)"], errors="coerce"
    )
    period_movers = period_movers.dropna(subset=["Period return (%)"])

    movers_left, movers_right = st.columns(2, gap="large")
    with movers_left:
        gainers = period_movers.nlargest(10, "Period return (%)")
        if not gainers.empty:
            fig_gainers = signed_hbar(
                gainers, "Period return (%)", "Ticker",
                t("Gainers · top 10 · {period}", period=period_label(period)),
                t("Return over selected period (%)"),
            )
            help_chart(fig_gainers, "gainers", "gainers", width="stretch", config={"displayModeBar": False})
        else:
            st.info(t("Not enough data for a gainer list in this period."))
    with movers_right:
        losers = period_movers.nsmallest(10, "Period return (%)")
        if not losers.empty:
            fig_losers = signed_hbar(
                losers, "Period return (%)", "Ticker",
                t("Losers · bottom 10 · {period}", period=period_label(period)),
                t("Return over selected period (%)"),
            )
            help_chart(fig_losers, "losers", "losers", width="stretch", config={"displayModeBar": False})
        else:
            st.info(t("Not enough data for a loser list in this period."))

    st.caption(t(
        "Gainers and losers rank individual stocks by cumulative return over the selected {period} window, using each stock's first and last available adjusted close in that window. Broad-market ETFs are excluded. Individual stocks may have slightly different first available dates.",
        period=period_label(period),
    ))

    st.markdown(f"#### {t('Volume leaders')}")
    volume_rank = daily_movers.dropna(subset=["Volume"]).nlargest(10, "Volume")
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

    st.caption(t("Market Overview focuses on market breadth, leaders and volume. Use the Screener for individual stock filtering and comparison."))


def render_screener(
    metrics_view: pd.DataFrame,
    prices: pd.DataFrame,
    all_metrics: pd.DataFrame,
    period: str,
) -> None:
    """One workspace for filtering, ranking and comparing multiple stocks."""
    st.subheader(t("Narrow the starter list by return and risk"))
    fc1, fc2, fc3 = st.columns(3)
    min_return = fc1.slider(t("Minimum period return (%)"), min_value=-100, max_value=200, value=-100, step=5)
    max_vol = fc2.slider(t("Maximum annualized volatility (%)"), min_value=0, max_value=300, value=300, step=5)
    sort_keys = ["Period return (%)", "Ann. volatility (%)", "Max drawdown (%)", "Avg volume"]
    sort_by = fc3.selectbox(t("Sort by"), sort_keys, index=0, format_func=lambda col: t(col))

    filtered = metrics_view[
        (metrics_view["Period return (%)"].fillna(-999) >= min_return)
        & (metrics_view["Ann. volatility (%)"].fillna(999) <= max_vol)
    ].copy()
    ascending = sort_by in ["Ann. volatility (%)", "Max drawdown (%)"]
    filtered = filtered.sort_values(sort_by, ascending=ascending)

    st.write(t("Symbols that match: **{n}**", n=len(filtered)))
    display_filtered = filtered.copy()
    if "Group" in display_filtered.columns:
        display_filtered["Group"] = display_filtered["Group"].map(group_label)
    st.dataframe(
        display_filtered,
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
        data=display_filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="stockscope_filtered_stocks.csv",
        mime="text/csv",
    )
    st.caption(t(
        "Period return uses the first and last valid close; annualized volatility is daily-return standard deviation × √252; "
        "max drawdown is the worst decline from a prior peak."
    ))

    st.markdown("---")
    st.subheader(t("Compare shortlisted stocks"))
    st.caption(t("Choose from the stocks that passed your filters. Both charts below use the same selected names and look-back window."))

    available_tickers = filtered["Ticker"].astype(str).tolist() if not filtered.empty else []
    if not available_tickers:
        st.info(t("No stocks match the current filters. Adjust the return or volatility limits to compare candidates."))
        return

    default_candidates = [symbol for symbol in ["AAPL", "MSFT", "NVDA", "SPY"] if symbol in available_tickers]
    if not default_candidates:
        default_candidates = available_tickers[:min(4, len(available_tickers))]
    compare_key = lang_key("screener_compare_tickers")
    previous_selection = st.session_state.get(compare_key)
    if previous_selection is not None:
        st.session_state[compare_key] = [symbol for symbol in previous_selection if symbol in available_tickers]

    compare_tickers = st.multiselect(
        t("Symbols to compare"),
        options=available_tickers,
        default=default_candidates,
        format_func=ticker_label,
        key=compare_key,
        help=t("Select up to about eight names to keep the charts readable."),
    )
    if not compare_tickers:
        st.info(t("Pick at least one symbol to compare."))
        return

    compare_data = prices[prices["ticker"].isin(compare_tickers)].copy()
    if compare_data.empty:
        st.warning(t("No history for those symbols in this window."))
        return

    normalized = compare_data.sort_values(["ticker", "date"]).copy()
    normalized["Indexed (start = 100)"] = normalized.groupby("ticker")["close"].transform(
        lambda values: values / values.dropna().iloc[0] * 100 if not values.dropna().empty else values
    )
    fig_line = px.line(
        normalized,
        x="date",
        y="Indexed (start = 100)",
        color="ticker",
        title=t("Rebased performance · {period}", period=period_label(period)),
        labels={
            "date": t("Date"),
            "ticker": t("Ticker"),
            "Indexed (start = 100)": t("Rebased (start = 100)"),
        },
    )
    fig_line.add_hline(y=100, line_dash="dot", line_color=PREV_CLOSE_COLOR, line_width=1)
    fig_line.update_layout(
        height=500,
        hovermode="x unified",
        title=dict(
            text=t("Rebased performance · {period}", period=period_label(period)),
            x=0.5,
            xanchor="center",
            y=0.99,
            yanchor="top",
        ),
        yaxis_title=t("Rebased level (start of window = 100)"),
        xaxis_title=t("Date"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin=dict(l=55, r=25, t=75, b=115),
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.28,
            yanchor="top",
            title_text="",
            itemsizing="constant",
        ),
    )
    fig_line.update_xaxes(showgrid=False)
    fig_line.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, side="right")
    help_chart(fig_line, "comparison", "comparison", width="stretch", config={"displayModeBar": False})
    st.caption(t("This is not the share price. Each series starts at 100 so you can compare percentage paths."))

    selected_metrics = all_metrics[all_metrics["Ticker"].isin(compare_tickers)].copy()
    if not selected_metrics.empty:
        fig_scatter = px.scatter(
            selected_metrics,
            x="Ann. volatility (%)",
            y="Period return (%)",
            color="Group",
            text="Ticker",
            hover_data={"Last": ":.2f", "Max drawdown (%)": ":.2f", "Avg volume": ":,.0f"},
            title=t("Return vs risk"),
        )
        fig_scatter.update_traces(textposition="top center", marker={"size": 12, "opacity": 0.8})
        fig_scatter.add_hline(y=0, line_dash="dot", line_color=PREV_CLOSE_COLOR, line_width=1)
        fig_scatter.update_layout(
            height=420,
            xaxis_title=t("Ann. volatility (%)"),
            yaxis_title=t("Period return (%)"),
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
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
    quote = lookup_snapshot(snapshot_from_prices(one_prices), focus) if not one_prices.empty else {}
    last_close = quote.get("last", np.nan)
    day_change = quote.get("chg", np.nan)
    st.metric(t("Last close"), format_last(focus, last_close))

    if not series.empty:
        prev_close = last_close - day_change if pd.notna(last_close) and pd.notna(day_change) else None
        price_fig = build_price_chart(series, focus, "Candle", previous_close=prev_close, range_key="1M" if period == "1mo" else "1Y")
        help_chart(price_fig, "stock", "stock", width="stretch", config={"displayModeBar": False})
        st.caption(t("Daily OHLC candles. Weekends and holidays are hidden. Green = close ≥ open. Scale is zoomed to this window."))

    if st.button(t("Add to watchlist"), width="stretch"):
        st.session_state.flash = add_to_watchlist(focus)
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
        - Home, index, screener, and stock-research prices: Yahoo Finance through the Python package `yfinance`.
        - Main indices use Yahoo symbols `^GSPC` (shown as SPX), `^NDX` (NDX), and `^DJI` (DJI).
        - Home and index charts: selectable intraday and daily chart ranges, with price and volume where available.
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


def main() -> None:
    init_state()
    reset_viewport_to_top = bool(st.session_state.pop("_scroll_to_top", False))
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

    if reset_viewport_to_top:
        st.components.v1.html(
            """<script>
            (() => {
              const scrollTop = () => {
                try {
                  const parentWindow = window.parent;
                  const parentDocument = parentWindow.document;
                  const targets = [
                    parentDocument.querySelector('section.main'),
                    parentDocument.querySelector('[data-testid="stAppViewContainer"]'),
                    parentDocument.scrollingElement,
                    parentDocument.documentElement,
                    parentDocument.body
                  ].filter(Boolean);
                  for (const target of targets) target.scrollTop = 0;
                  parentWindow.scrollTo(0, 0);
                } catch (error) {
                  window.scrollTo(0, 0);
                }
              };
              scrollTop();
              requestAnimationFrame(scrollTop);
              setTimeout(scrollTop, 120);
              setTimeout(scrollTop, 320);
              setTimeout(scrollTop, 650);
            })();
            </script>""",
            height=0,
            scrolling=False,
        )


main()