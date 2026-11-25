# StockScope Dashboard

Beginner-friendly US market summary. Top navigation: **Home**, **Learn**, **Markets**, **Watchlist**.

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

## Two apps at once

Do not run Dashboard and Learn on the same port. Example:

```bat
py -m streamlit run app.py --server.port 8501
```
