# StockScope

Two separate Streamlit apps. They are **not combined** yet — run each from its own folder.

## Dashboard

US-stock research workbench (intraday watch plus historical analysis).

```bash
cd dashboard
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows you can also double-click `dashboard/start_windows.bat`.

Open **http://localhost:8501**. Needs Python 3.11+ and internet (`yfinance`).

## Learn

Cinematic home / lesson app (StockScope Learn V20).

```bash
cd learn
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows you can also double-click `learn/start_windows.bat`.

Open **http://localhost:8501**. Needs Python 3.11+ and internet (`yfinance`). Do not run both apps on the same port at once.
