"""Deterministic market fixtures: the regression suite never calls Yahoo."""
import ast
from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd
import pytest
import streamlit as st
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]


def app_functions(name):
    """Load app helpers without running its page rendering or navigation."""
    path = ROOT / name / "app.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    nodes = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            nodes.append(node)
        elif isinstance(node, ast.Assign):
            try:
                ast.literal_eval(node.value)
            except (ValueError, TypeError):
                if not isinstance(node.value, ast.BinOp):
                    continue
            nodes.append(node)
    module = ModuleType(f"stockscope_{name}")
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), module.__dict__)
    return module


def ohlc(index):
    step = np.arange(len(index), dtype=float)
    close = 100 + step * 0.04 + 7 * np.sin(step / 9)
    return pd.DataFrame({
        "Open": close - 0.3, "High": close + 2, "Low": close - 2,
        "Close": close, "Volume": 100000 + step * 10,
    }, index=index)


def fake_history(self, period="1y", interval="1d", **kwargs):
    if interval.endswith("m") or interval.endswith("h"):
        minutes = int(interval[:-1]) * (60 if interval.endswith("h") else 1)
        days = pd.bdate_range("2026-09-28", "2026-10-02")[-(1 if period == "1d" else 5):]
        index = pd.DatetimeIndex([
            ts for day in days for ts in pd.date_range(
                day + pd.Timedelta(hours=9, minutes=30),
                day + pd.Timedelta(hours=15, minutes=59), freq=f"{minutes}min",
                tz="America/New_York",
            )
        ])
    else:
        count = {"5d": 5, "1mo": 23, "3mo": 66, "6mo": 132, "1y": 260}.get(period, 1300)
        index = pd.bdate_range(end="2026-10-02", periods=count)
        if interval == "1wk":
            index = index[::5]
    return ohlc(index)


def fake_download(tickers, period="1y", group_by="column", **kwargs):
    symbols = tickers.split() if isinstance(tickers, str) else tickers
    frames = {symbol: fake_history(None, period=period) for symbol in symbols}
    raw = pd.concat(frames, axis=1)
    return raw if group_by == "ticker" else raw.swaplevel(axis=1).sort_index(axis=1)


@pytest.fixture(autouse=True)
def offline_market(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "dashboard"))
    st.cache_data.clear()
    monkeypatch.setattr(yf, "download", fake_download)
    monkeypatch.setattr(yf.Ticker, "history", fake_history)
    monkeypatch.setattr(yf.Ticker, "get_info", lambda self: {})
    yield
    st.cache_data.clear()


@pytest.fixture
def dashboard():
    return app_functions("dashboard")


@pytest.fixture
def learn():
    return app_functions("learn")
