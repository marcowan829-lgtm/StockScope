# StockScope

One Streamlit app combining the market dashboard and the English StockScope Learn V20 course.

## Structure

- `dashboard/app.py`: Yahoo Finance downloads, quote snapshots, return/risk calculations, Plotly charts, and direct navigation to Home, Market Overview, Screener, Live Quotes, Returns & Risk, and Stock Research. Its `main()` function renders the selected section; index details open from Home or search.
- `dashboard/.streamlit/config.toml`: the dashboard's light theme and Streamlit settings. Run from `dashboard/` so Streamlit loads this configuration.
- `dashboard/watchlist_design.py`: local company logos, index badges and the compact watchlist row layout. Bundled marks and source credits are in `dashboard/assets/company-icons/`.
- `dashboard/chart_help.py`: beginner-friendly chart guides and the native right-hand help drawer, opened by the ? buttons beside charts.
- `dashboard/learning_integration.py`: book-icon launcher, white study-path drawer, and navigation between markets and lessons in the same session.
- `learn/app.py`: the English V20 course, including its white Learning Home, technical indicators, synthetic candle examples, eight learning units, quizzes and session progress. It renders inside the main app and can also run independently.
- Both modules use the same Python dependencies. Data caches and user selections are held by Streamlit; there is no application database or brokerage integration.
- `tests/`: offline regression tests for both apps, including page rendering and interactions with deterministic market data.

## Dashboard

US-stock research workbench (intraday watch plus historical analysis).

| Top navigation | Functions |
| --- | --- |
| Home | Main indices, selected-symbol chart, and the session watchlist |
| Market Overview | Group return heatmap, top performers, daily movers, volume leaders, and universe table |
| Screener | Return/volatility filters, sorting, and shortlist export |
| Live Quotes | Intraday candles, volume, refresh controls, and monitored symbols |
| Returns & Risk | Rebased performance comparison and return-versus-volatility chart |
| Stock Research | Individual price history, return/risk metrics, and company fundamentals |

The former Markets sub-tabs now open directly from the top navigation.

The watchlist uses clickable rows with a circular company mark or index badge, full name, ticker chip, latest price, and daily absolute/percentage change. The selected symbol has a blue border. Add names with **＋**; remove them through **Manage watchlist**. Icons are bundled locally, with initial badges for symbols without a bundled logo.

Each chart has a **?** button. It opens a guide on the right with reading steps, a made-up numerical example, what the chart can tell you, and common misunderstandings. Home and index price guides follow the selected Line/Candle/Area/Baseline view. Close with **×**, **Esc**, or a click outside the guide.

Chart-help popups also include a **Want to learn more?** description and an arrow button that opens the relevant lesson directly. Candle guides link to Lesson 02A Candlestick Patterns.

The guide opens with an annotated example drawing: three numbered notes, curved arrows, and highlighted values. Each chart family has its own illustration in `dashboard/chart_examples.py`. Longer explanations are available in the collapsed **Read more** section. Drawings use fictional data and include accessible text descriptions.

```bash
cd dashboard
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows you can also double-click `dashboard/start_windows.bat`.

Open **http://localhost:8501**. Needs Python 3.11+ and internet (`yfinance`).

## Integrated learning

Click the **book icon inside the semicircle at the right edge** of a market page. A white study-path drawer lists all lessons, the final quiz and Data & Methods. Click any item to display it across the content area below the existing site navigation. The study path stays in the book-button popup, so lesson pages have no permanent study-path panel. Learning Home, lessons, cards, quiz results and chart backgrounds all use white surfaces. Use **Back to markets** to return; the watchlist, chart settings and completed lessons remain in the session.

All learner-facing text, controls, exercises, chart labels and quiz explanations are in English. Indicator and financial-statement names follow [TradingView Technical Ratings](https://www.tradingview.com/support/solutions/43000614331-technical-ratings/), [candlestick terminology](https://www.tradingview.com/support/solutions/43000745269-introduction-to-candlestick-charts-and-patterns/) and [financial data terminology](https://www.tradingview.com/support/solutions/43000543506-how-to-access-financial-data-on-tradingview/). The explanations are written independently for beginners.

Run the combined app from Terminal:

```bash
cd /Users/tamcalix/Desktop/StockScope/dashboard
./.venv/bin/python -m streamlit run app.py
```

For a new environment, complete the dependency setup in the Dashboard section first.

The source learning folder is preserved separately. `learn/app.py` remains available as a standalone course, but a second server is not needed for the combined website. Progress is session-based and may reset when the app/server restarts.

## Development checks

From the repository root, with a Python 3.11+ virtual environment active:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check --select F,E9 dashboard learn tests
python -m compileall -q dashboard learn tests
```

Tests mock Yahoo Finance and do not require network access. They cover navigation, chart ranges/types, watchlist selection handling, missing/duplicate data, market outages, technical indicators, financial lesson controls, and quiz submission/retry flows.

`dashboard/test_intraday.py` remains a manual network diagnostic; run it directly with Python when investigating the live feed.
