import numpy as np
import pandas as pd
import pytest
import streamlit as st
import yfinance as yf
from streamlit.testing.v1 import AppTest

from conftest import ROOT, ohlc


def test_candle_axis_includes_wicks(dashboard):
    frame = ohlc(pd.date_range("2026-10-02 09:30", periods=3, freq="5min"))
    frame["Low"] = 50.0
    frame["High"] = 200.0
    fig = dashboard.build_price_chart(frame, "AAPL", "Candle")
    bottom, top = fig.layout.yaxis.range
    assert bottom < 50
    assert top > 200


def test_baseline_line_keeps_segments_at_exact_crossing(dashboard):
    dates = pd.date_range("2026-10-02 09:30", periods=3, freq="5min")
    high_x, high_y, low_x, low_y = dashboard._split_at_baseline(dates, [101, 100, 99], 100)
    assert high_y == [101, 100, None]
    assert low_y == [None, 100, 99]


def test_extended_hours_are_visible_when_requested(dashboard):
    frame = ohlc(pd.DatetimeIndex(["2026-10-02 08:00", "2026-10-02 10:00", "2026-10-02 18:00"]))
    fig = dashboard.build_price_chart(frame, "AAPL", "Candle", include_extended=True)
    assert len(fig.data[0].x) == 3
    assert fig.layout.xaxis.rangebreaks[1].bounds == (20, 4)


def test_ohlc_deduplicates_before_one_day_fallback(dashboard, monkeypatch):
    frame = ohlc(pd.DatetimeIndex([
        "2026-10-02 10:00", "2026-10-02 09:30", "2026-10-02 09:30", "2026-10-01 09:30",
    ]))
    monkeypatch.setattr(yf.Ticker, "history", lambda self, **kw: pd.DataFrame() if kw["period"] == "1d" else frame)
    result = dashboard.download_ohlc("AAPL", "1d", "5m")
    assert result.index.is_unique
    assert result.index.is_monotonic_increasing
    assert {stamp.date() for stamp in result.index} == {pd.Timestamp("2026-10-02").date()}


@pytest.mark.parametrize("app_name,loader", [("dashboard", "download_prices"), ("learn", "load_prices")])
def test_daily_history_keeps_one_quote_per_symbol_date(app_name, loader, request, monkeypatch):
    app = request.getfixturevalue(app_name)
    raw = ohlc(pd.DatetimeIndex(["2026-10-01", "2026-10-02", "2026-10-02"]))
    monkeypatch.setattr(yf, "download", lambda **kw: raw)
    result = getattr(app, loader)(("AAPL",), "5d")
    assert len(result) == 2
    assert result.iloc[-1]["close"] == raw.iloc[-1]["Close"]


@pytest.mark.parametrize("app_name,loader", [("dashboard", "download_prices"), ("learn", "load_prices")])
def test_missing_volume_still_loads_prices(app_name, loader, request, monkeypatch):
    app = request.getfixturevalue(app_name)
    raw = ohlc(pd.bdate_range("2026-10-01", periods=3)).drop(columns="Volume")
    monkeypatch.setattr(yf, "download", lambda **kw: raw)
    result = getattr(app, loader)(("AAPL",), "5d")
    assert len(result) == 3
    assert result["volume"].isna().all()


def test_watchlist_selection_is_an_event_not_a_persistent_override(dashboard):
    state = {"wl_stocks": {"selection": {"rows": [1]}}, "selected_symbol": "AAPL"}
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(st, "session_state", state)
        dashboard.on_watchlist_selection("wl_stocks", ["AAPL", "MCD"])
        assert state["selected_symbol"] == "MCD"


def test_search_synchronizes_navigation():
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30).run()
    app.pills(key="nav_pills").set_value("Screener").run()
    app.text_input(key="nav_search").set_value("MSFT").run()
    assert not app.exception
    assert app.session_state["nav"] == "Home"
    assert app.pills(key="nav_pills").value == "Home"


def test_index_page_allows_one_click_home_navigation():
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30).run()
    app.text_input(key="nav_search").set_value("SPX").run()
    assert app.session_state["nav"] == "Index"
    assert app.pills(key="nav_pills").value is None
    app.pills(key="nav_pills").set_value("Home").run()
    assert app.session_state["nav"] == "Home"


def test_stock_details_shows_load_failure_instead_of_crashing(monkeypatch):
    def fail(**kwargs):
        raise ConnectionError("offline")
    monkeypatch.setattr(yf, "download", fail)
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30)
    app.session_state["nav"] = "Stock Research"
    app.session_state["_last_nav_pill"] = "Stock Research"
    app.run()
    assert not app.exception
    assert app.warning


@pytest.mark.parametrize("app_name", ["dashboard", "learn"])
@pytest.mark.parametrize("failure", ["empty", "exception"])
def test_initial_page_survives_market_outage(app_name, failure, monkeypatch):
    def unavailable(*args, **kwargs):
        if failure == "exception":
            raise ConnectionError("offline")
        return pd.DataFrame()
    monkeypatch.setattr(yf, "download", unavailable)
    monkeypatch.setattr(yf.Ticker, "history", unavailable)
    app = AppTest.from_file(str(ROOT / app_name / "app.py"), default_timeout=30).run()
    assert not app.exception


def test_technical_indicator_bounds_and_flat_prices(learn):
    raw = ohlc(pd.bdate_range("2026-01-01", periods=100))
    raw.loc[:, ["Open", "High", "Low", "Close"]] = 100.0
    frame = raw.rename(columns=str.lower).reset_index(names="date")
    result = learn.calculate_technical_indicators(frame)
    assert result["rsi14"].iloc[-1] == 50
    assert result["adx14"].iloc[-1] == 0
    assert result["obv"].iloc[-1] == 0
    assert not np.isinf(result.select_dtypes("number").to_numpy()).any()


def test_monthly_heatmap_does_not_invent_returns_across_missing_months(dashboard):
    prices = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-30", "2026-03-31", "2026-01-30", "2026-02-27", "2026-03-31"]),
        "ticker": ["AAPL", "AAPL", "MSFT", "MSFT", "MSFT"],
        "close": [100.0, 150.0, 100.0, 110.0, 121.0],
    })
    fig = dashboard.make_monthly_sector_heatmap(prices)
    assert fig is not None
    assert np.asarray(fig.data[0].z)[0] == pytest.approx([10.0, 10.0])
