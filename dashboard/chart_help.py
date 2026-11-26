"""Plain-language, chart-specific guides shown in a native right-hand drawer."""
import html

import plotly.graph_objects as go
import streamlit as st
from chart_examples import EXAMPLE_SUMMARIES, annotated_example
from i18n import is_zh, t
from learning_integration import open_lesson


CHART_GUIDES = {
    "price_line": {
        "title": "Price chart: line",
        "what": "This line shows how one stock's price, or one index's level, changed over time. An index is a score that follows a group of stocks, rather than a share you can buy directly.",
        "steps": [
            "Read from left to right: earlier times are on the left, later times on the right. The numbers on the side show the price or index level.",
            "A rising section means the value increased during that part of the chart. A falling section means it decreased. Hover over the line to read a value and time.",
            "The whole line's green/red colour compares its latest value with the previous close when available, otherwise the first value shown. A red line can still have rising sections.",
            "1D means one trading day; 5D means five trading days; 1M means one month; 6M means six months; 1Y means one year. All Time uses the available history.",
        ],
        "example": "A stock moves from $100 on the left to $110 on the right. Its price rose $10, or 10%, during that window. An index moving from 7,000 to 7,070 rose 70 points, or 1%.",
        "learn": "Spot the overall direction, turning points, and when larger moves happened. Use the numbers as well as the shape.",
        "note": "The vertical scale is zoomed in, so a small change can look large. The change beside the chart heading is against the previous close, which can differ from the change across your selected window.",
    },
    "price_candle": {
        "title": "Price chart: candles and volume",
        "what": "Each candle summarises prices during one time block. This could be five minutes, one day, or one week, depending on the selected range.",
        "steps": [
            "Read the time along the bottom and the price or index level on the side. Hover over a candle to see its four numbers.",
            "Open is the price at the start of the block. Close is the price at its end. High is the highest price reached; Low is the lowest.",
            "The thick body runs between open and close. The thin lines, called wicks, reach the high and low.",
            "Green means the close was at least as high as the open. Red means it was lower. This compares the start and end of that candle, not necessarily the previous day.",
            "When available, bars below the candles show volume: the number of shares traded in each block. Taller bars mean more shares changed hands.",
        ],
        "example": "A candle opens at $100, reaches a high of $105 and a low of $98, then closes at $103. Its body is green, from $100 to $103; its wicks reach $98 and $105.",
        "learn": "See both the direction and the range of movement inside each time block. Compare nearby volume bars to see when trading was busier.",
        "note": "A green candle can still be below yesterday's close. A large candle or busy volume bar does not tell you what happens next. Index values are points, not a stock's dollar price; index volume can be missing or zero.",
    },
    "price_area": {
        "title": "Price chart: area",
        "what": "This is a price line with the space beneath it shaded. The top edge of the shaded area is the value to read.",
        "steps": [
            "Follow the top edge from left to right to see how the price or index level changed. Read its value using the scale on the side.",
            "The shading makes the shape easier to see. It does not show how many shares were bought or how much money entered the market.",
            "Green/red compares the latest value with the previous close when available, otherwise the first value in this window. Hover to see an exact value and time.",
        ],
        "example": "If the top edge rises from $50 to $55, the stock rose $5, or 10%, across those two points. A larger shaded area does not mean more money was invested.",
        "learn": "Quickly see the overall direction and periods of larger price movement.",
        "note": "The scale is zoomed in rather than starting at zero. Compare the numbers, not the amount of shaded space. Historical movement does not predict the next move.",
    },
    "price_baseline": {
        "title": "Price chart: baseline",
        "what": "This view compares the price with a reference level, called the baseline. Here that is the previous close when available, otherwise the first price in this window.",
        "steps": [
            "Find the horizontal baseline. Green sections are above it; red sections are below it.",
            "Read time along the bottom and price or index points on the side. Hover to check exact values.",
            "Crossing the baseline only means the value moved from one side of this reference to the other. It is not a buy or sell instruction.",
        ],
        "example": "Yesterday's close was $100. A price of $102 appears above the baseline in green; $98 appears below it in red. Moving from $98 to $99 is a rise, even though both values remain red.",
        "learn": "See when the price was above or below the reference and how far it moved away.",
        "note": "The baseline can be outside the visible price range. The reference is not a guaranteed fair price or a level the stock must return to.",
    },
    "heatmap": {
        "title": "Group monthly returns",
        "what": "This colour grid compares groups of stocks month by month. A return is the percentage change in value over a period.",
        "steps": [
            "Choose a group from the labels down the left, then a month along the bottom. Their meeting point is one coloured cell.",
            "Green means an average gain; red means an average loss. Colours near the middle of the colour scale mean a smaller change near zero. Use the colour key and hover for the exact percentage.",
            "Each cell is the simple average of available stock returns in that group: each included stock counts equally. The benchmark row contains funds that follow the wider market.",
        ],
        "example": "Two stocks in a group return +10% and −2% in a month. Their average is +4%, so that group's cell shows a 4% gain for that month. It does not mean every stock gained 4%.",
        "learn": "Compare which groups rose or fell in the same month, and whether a group's results changed from month to month.",
        "note": "A monthly percentage is not the whole-window return; the latest month may still be in progress. These are this app's stock groups, not official sector indices. Missing data is not a zero return.",
    },
    "ranking": {
        "title": "Top performers in this window",
        "what": "These bars rank up to 15 stocks or funds by their percentage price change over the selected look-back window.",
        "steps": [
            "The short names on the side are ticker symbols: for example, AAPL means Apple. The bottom scale shows percentage change.",
            "A bar to the right of zero is a gain and is green. A bar to the left is a loss and is red. Compare lengths, then hover for the exact result.",
            "Check the selected window first: a one-month result and a one-year result describe different periods.",
        ],
        "example": "A +20% bar means a price rose from $100 to $120 over that window. A +5% bar means $100 became $105. This does not mean the first stock costs more per share.",
        "learn": "See which names in the displayed list had the highest returns during the same window.",
        "note": "Top means highest in the available list, not guaranteed profit. If every result is negative, even the top names can show losses. A high past return is not a forecast.",
    },
    "gainers": {
        "title": "Daily movers: highest changes",
        "what": "This chart shows up to 10 stocks with the highest latest daily percentage changes in the app's starter list.",
        "steps": [
            "Each row is a stock, identified by its ticker symbol. The percentage compares its latest daily close with its previous trading day's close.",
            "Green/right of zero means a rise; red/left of zero means a fall. Hover to read the exact percentage.",
            "These are daily changes, even when the page's look-back window is one year. Check the page's data date.",
        ],
        "example": "A stock closes at $50, then $51 the next trading day. Its daily change is +2%. That is different from its return over the whole year.",
        "learn": "Find stocks with the strongest latest daily changes in this list, then investigate what happened.",
        "note": "Highest is a ranking, not a promise that all the bars are positive. A move does not explain its cause or predict tomorrow's price.",
    },
    "losers": {
        "title": "Daily movers: lowest changes",
        "what": "This chart shows up to 10 stocks with the lowest latest daily percentage changes in the app's starter list.",
        "steps": [
            "Read the ticker symbol on the side and the percentage change on the bottom. The comparison is with the previous trading day's close.",
            "A red bar to the left of zero is a loss. A green bar to the right is a gain. Hover to see the exact number.",
            "Lowest means the weakest changes within this list. On a strong day, a stock can be in this ranking while still showing a small gain.",
        ],
        "example": "A price falls from $80 to $76 between daily closes. It lost $4, which is 5% of $80, so its bar is −5%.",
        "learn": "Spot stocks with weaker daily results and compare how large their moves were.",
        "note": "A fall does not automatically mean a stock is cheap, or that it must bounce back. This chart covers the starter list rather than every stock in the market.",
    },
    "volume": {
        "title": "Trading volume leaders",
        "what": "Volume counts the number of shares traded. These bars show the busiest stocks in the starter list's latest available daily session.",
        "steps": [
            "Read the ticker on the side. A longer bar means more shares traded. On the scale, k means thousand and M means million.",
            "Here the colour shows the latest daily price change: green for a rise or no change, red for a fall. The bar's length shows share count, not price change.",
            "Hover over a bar for its share count. Every trade has both a buyer and a seller.",
        ],
        "example": "A volume of 2M means 2 million shares changed hands. It does not mean $2 million was invested, or that there were 2 million different investors.",
        "learn": "See which names attracted more trading activity in the latest session.",
        "note": "Busy trading alone does not show whether a price will rise. Large and small companies naturally trade different share counts, and a session still in progress has an incomplete total.",
    },
    "comparison": {
        "title": "Compare performance: everyone starts at 100",
        "what": "Each line is a stock, fund or index reset to 100 at its first available date in the selected window. This makes percentage changes easier to compare even when original prices differ.",
        "steps": [
            "Read dates along the bottom. Match each line's colour to the name in the legend, then read the level on the side.",
            "100 is the starting point. Above 100 means a gain since that start; below 100 means a loss. The dashed line marks 100.",
            "Subtract 100 from a level to get the percentage change from that series' start. Hover over a date to compare the lines there.",
        ],
        "example": "Imagine each line began as $100: a level of 120 means a 20% gain; 90 means a 10% loss. A stock at 120 on this chart does not necessarily have a $120 share price.",
        "learn": "Compare gains and losses and how smooth or bumpy each path was. Two lines can end together but have very different journeys.",
        "note": "The result depends on the starting date and available data. The chart uses adjusted historical prices where supplied; it does not include your fees or taxes. Past winners can become future losers.",
    },
    "risk": {
        "title": "Return versus price swings",
        "what": "Each dot is one selected stock or fund. It combines its past return with how much its daily returns moved around, called volatility.",
        "steps": [
            "Up/down shows the total return over your selected window. Above zero means a gain; below zero means a loss.",
            "Left/right shows annualized volatility: daily price-change variability expressed on a common yearly scale. Farther right means more variable daily returns in this history.",
            "Read the ticker beside a dot to identify it. Colours identify groups, not good or bad investments. Hover for more details.",
            "Max drawdown in the hover details means the largest fall from an earlier high within the window. It is different from volatility.",
        ],
        "example": "A dot at 20 on the bottom and +10 on the side had 20% annualized volatility and gained 10% over the selected window. Another dot at 40 and +5 had more variable daily returns but a smaller total gain in that history.",
        "learn": "Compare the return achieved with the amount of price movement along the way, rather than looking at gains alone.",
        "note": "20% volatility is not a 20% chance of losing money, a predicted 20% loss, or a limit on losses. This chart does not measure every kind of risk or predict future returns.",
    },
    "intraday": {
        "title": "Intraday candles: one trading day",
        "what": "Intraday means within a trading day. Each candle summarises one block of time, such as one minute or five minutes, set by Bar size.",
        "steps": [
            "Time runs left to right in New York time. The side scale shows price, or index points for an index. Hover to see open, high, low and close.",
            "Open is the start of a block, close its end, high its highest value and low its lowest. The body connects open and close; thin wicks show the extremes.",
            "Green means close was at least open; red means close was below open. Bars below show shares traded in the same block when volume is available.",
            "Vs previous bar compares the latest block's close with the block before it. Include pre/post adds trading before and after regular US hours. Refresh asks for another data update.",
        ],
        "example": "With 5 min selected, one candle opens at $100, reaches $102, falls to $99 and ends at $101. It is green. If the previous candle closed at $100, Vs previous bar is +1%.",
        "learn": "See how the day unfolded, when prices moved more, and when trading was busier.",
        "note": "The newest candle may still be forming. Refresh does not guarantee a real-time feed. Zero or missing index volume can mean no volume was supplied; it does not prove that no underlying stocks traded.",
    },
    "stock": {
        "title": "Historical daily candles",
        "what": "This chart shows one selected stock or index over the History window. Each candle summarises one trading day.",
        "steps": [
            "Read dates at the bottom and prices, or index points, on the side. Hover for the day's open, high, low and close.",
            "The body connects the opening and closing values; the thin wicks reach the day's high and low. Green means close was at least open, red means it was lower.",
            "Volume bars below show shares traded that day when supplied. Taller bars mean more shares changed hands.",
            "Period return above the chart compares the first and last close in this window. Volatility describes how variable daily returns were. Max drawdown is the worst fall from an earlier high in the window.",
        ],
        "example": "A day's open is $100, high $106, low $97 and close $104: a green body runs from $100 to $104. Separately, if a past peak of $120 later fell to $90, that fall was a 25% drawdown.",
        "learn": "See the longer price history and compare its gains, daily movement and past declines.",
        "note": "Historical prices can be adjusted for stock splits and dividends, so they may differ from the prices originally quoted. Index volume can be unavailable. A past drawdown is not a limit on future losses.",
    },
}


RELATED_LESSONS = {
    "price_line": ("02 Reading Stock Charts", "Explore prices, timeframes and volume, one step at a time."),
    "price_candle": ("02A Candlestick Patterns", "Learn to recognize candle shapes and read them in context."),
    "price_area": ("02 Reading Stock Charts", "Build confidence reading prices, timeframes and volume."),
    "price_baseline": ("02 Reading Stock Charts", "Learn what chart values and price changes tell you."),
    "heatmap": ("01 Stock Market Basics", "Understand percentage returns and how market groups fit together."),
    "ranking": ("01 Stock Market Basics", "Learn how returns help compare stocks over the same period."),
    "gainers": ("05 Why Stock Prices Move", "Explore news, expectations and other reasons prices change."),
    "losers": ("05 Why Stock Prices Move", "Explore why prices fall and what evidence to check next."),
    "volume": ("02 Reading Stock Charts", "Learn what trading volume shows alongside price."),
    "comparison": ("01 Stock Market Basics", "Understand returns, benchmarks and percentage comparisons."),
    "risk": ("06 Risk & Investor Protection", "Explore different kinds of risk and ways to recognize them."),
    "intraday": ("02A Candlestick Patterns", "Read candle bodies and wicks, then explore common patterns."),
    "stock": ("02A Candlestick Patterns", "Explore candle structures, trend context and confirmation."),
}


def _plain_markdown(text: str) -> str:
    return text.replace("$", r"\$")


@st.dialog("How to read this chart", position="right", width="small")
def show_chart_guide(topic: str) -> None:
    dialog_title_css = ""
    if is_zh():
        dialog_title_css = (
            '[data-testid="stDialog"]:has(.chart-guide-marker) [role="dialog"] h2'
            "{font-size:0!important;line-height:0;}"
            '[data-testid="stDialog"]:has(.chart-guide-marker) [role="dialog"] h2::after'
            f'{{content:"{t("How to read this chart")}";font-size:1.45rem;line-height:1.3;'
            "color:#131722;display:block;font-weight:700;letter-spacing:-0.02em;}"
        )
    st.markdown(
        f'<span class="chart-guide-marker"></span><style>{dialog_title_css}</style>',
        unsafe_allow_html=True,
    )
    guide = CHART_GUIDES[topic]
    st.subheader(t(guide["title"]))
    st.caption(t("MADE-UP EXAMPLE · Follow the drawing notes: 1 → 2 → 3."))
    summary = t(EXAMPLE_SUMMARIES[topic])
    st.image(annotated_example(topic), width="stretch", alt=t("Annotated example. {summary} Follow the three numbered drawing notes.", summary=summary))
    st.info(summary)
    with st.expander(t("Read more · step-by-step explanation"), expanded=False):
        st.markdown(f"#### {t('What am I looking at?')}")
        st.markdown(_plain_markdown(t(guide["what"])))
        st.markdown(f"#### {t('How to read it')}")
        for number, step in enumerate(guide["steps"], start=1):
            st.markdown(_plain_markdown(f"**{number}.** {t(step)}"))
        if topic in {"price_line", "price_area", "price_baseline"}:
            st.markdown(t("**Bars underneath:** when volume is available, these count shares traded in each time block. Taller means more shares traded. Green/red compares that block's close with its open, rather than the whole line's reference. Index volume can be missing or zero."))
        st.markdown(f"#### {t('A simple example')}")
        st.info(_plain_markdown(t(guide["example"])))
        st.markdown(f"#### {t('What can I learn?')}")
        st.markdown(_plain_markdown(t(guide["learn"])))
        st.markdown(f"#### {t('Keep in mind')}")
        st.markdown(_plain_markdown(t(guide["note"])))
    lesson, description = RELATED_LESSONS[topic]
    st.divider()
    st.markdown(f"**{t('Want to learn more?')}**")
    st.caption(t(description))
    if st.button(t("Lesson {lesson} →", lesson=t(lesson)), key=f"chart_lesson_{topic}", width="stretch",
                 help=t("Open Lesson {lesson}", lesson=t(lesson)), on_click=open_lesson, args=(lesson,)):
        st.rerun()
    st.caption(t("Close with ×, press Esc, or click outside the panel to return to your chart."))


def chart_help_button(topic: str, key: str) -> None:
    if st.button("?", key=f"chart_help_{key}", help=t("How to read: {title}", title=t(CHART_GUIDES[topic]["title"]))):
        show_chart_guide(topic)


def help_chart(fig: go.Figure, topic: str, key: str, **chart_options):
    """Place a guide beside a chart heading without covering the plotted data."""
    title, question = st.columns([0.92, 0.08], gap="small", vertical_alignment="center")
    with title:
        heading = fig.layout.title.text or t(CHART_GUIDES[topic]["title"])
        st.markdown(f'<p class="chart-help-title">{html.escape(heading)}</p>', unsafe_allow_html=True)
    with question:
        chart_help_button(topic, key)
    display_fig = go.Figure(fig)
    display_fig.update_layout(title=None)
    if display_fig.layout.margin.t is not None and display_fig.layout.margin.t >= 48:
        display_fig.update_layout(margin_t=16)
    chart_options.setdefault("key", f"plot_{key}")
    return st.plotly_chart(display_fig, **chart_options)
