# StockScope Dashboard

Beginner-friendly US market summary. Top navigation: **Home**, **Market Overview**, **Screener**, **Live Quotes**, **Returns & Risk**, **Stock Research**.

Market Overview groups the heatmap, top performers, movers and volume leaders. Screener filters the stock list; Live Quotes follows intraday bars; Returns & Risk compares performance and volatility; Stock Research focuses on one symbol. The watchlist is managed on Home. Its rows show company icons, names, ticker chips, prices and color-coded daily changes. Select a row to update the chart, add names with **＋**, and remove them through **Manage watchlist**. Icons are bundled locally so they do not depend on a logo service at runtime.

The **book icon in the right-edge semicircle** opens the English learning path. Select a lesson or Learning Home to display it below the site navigation at full content width. The study path is available only through the book-button popup. All learning pages and the drawer use white backgrounds; **Back to markets** returns to the dashboard. Lessons, chart labs, exercises, the final quiz and progress come from the integrated V20 course in `../learn/app.py`.

Each chart-help popup has a **Want to learn more?** section with a relevant lesson and an arrow button to open it.

Needs **Python 3.11+** and internet (`yfinance`). On Windows, use `py` or `python` — not `python3`.

## Windows (easiest)

In File Explorer, open the `dashboard` folder and double-click **`start_windows.bat`**.

Or in **PowerShell** or **cmd** from `dashboard`:

```bat
py --version
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

If `py` is not found, try `python` in place of `py`.

Then open **http://localhost:8501**. Leave the black window / PowerShell tab open while you use the app.

Optional venv in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If activation is blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or skip the venv and use `start_windows.bat`.

If both `py --version` and `python --version` fail, install Python 3.11+ from https://www.python.org/downloads/ and tick **Add python.exe to PATH**.

## macOS / Linux

```bash
cd dashboard
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Optional venv: `python3 -m venv .venv` then `source .venv/bin/activate`.

## Learning in the same app

No second Learn server is needed. On this Mac, use the existing dashboard virtual environment:

```bash
cd /Users/tamcalix/Desktop/StockScope/dashboard
./.venv/bin/python -m streamlit run app.py
```
