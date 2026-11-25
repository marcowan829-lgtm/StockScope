# StockScope Dashboard

Beginner-friendly US market summary. Top navigation: **Home**, **Learn**, **Markets**, **Watchlist**.

## Run

Needs **Python 3.11+** and internet (`yfinance`).

```bash
cd dashboard
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Then open **http://localhost:8501**.

To keep Learn running at the same time, give this app a free port:

```bash
python3 -m streamlit run app.py --server.port 8501
```

On Windows you can also double-click `start_windows.bat`.

Optional virtualenv:

```bash
cd dashboard
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
