import math

import pytest
from streamlit.testing.v1 import AppTest

from conftest import ROOT


def app():
    return AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=45).run()


def assert_clean(page):
    assert not page.exception, [item.message for item in page.exception]


def test_company_marks_and_custom_symbol_fallback():
    from watchlist_design import company_icon_html
    for ticker in ["AAPL", "MCD", "NVDA", "MSFT", "AMZN"]:
        assert '<img src="data:image/' in company_icon_html(ticker)
    fallback = company_icon_html("NEW-STOCK")
    assert ">NE</span>" in fallback
    assert "<img" not in fallback
    assert 'is-index' in company_icon_html("^GSPC", index_badge="500", index_color="#f23645")


@pytest.mark.parametrize("last,change,percent,is_index,expected", [
    (100, 2, 2.04, False, ("$100.00", "+2.00 (+2.04%)", "is-up")),
    (7127.86, -73.23, -1.02, True, ("7,127.86", "-73.23 (-1.02%)", "is-down")),
    (0, 0, 0, False, ("$0.00", "+0.00 (+0.00%)", "is-flat")),
    (math.nan, None, math.inf, False, ("—", "—", "is-flat")),
    (10, None, -3, False, ("$10.00", "-3.00%", "is-down")),
])
def test_quote_labels_preserve_units_signs_and_missing_values(last, change, percent, is_index, expected):
    from watchlist_design import quote_labels
    assert quote_labels(last, change, percent, is_index=is_index) == expected


def test_watchlist_text_is_escaped():
    from watchlist_design import watchlist_row_html
    row = watchlist_row_html('TEST', '<script>alert(1)</script>', 'A&B', 10, 1, 10)
    assert '<script>' not in row
    assert '&lt;script&gt;' in row
    assert 'A&amp;B' in row


def test_watchlist_row_changes_chart_and_search_can_choose_another_symbol():
    page = app()
    page.button(key="wl_pick_MCD").click().run()
    assert_clean(page)
    assert page.session_state["selected_symbol"] == "MCD"
    assert "Selected." in page.button(key="wl_pick_MCD").label
    page.segmented_control(key="chart_type").set_value("Candle").run()
    assert page.session_state["selected_symbol"] == "MCD"
    page.text_input(key="nav_search").set_value("MSFT").run()
    assert_clean(page)
    assert page.session_state["selected_symbol"] == "MSFT"
    page.button(key="wl_pick_IGSPC").click().run()
    assert_clean(page)
    assert page.session_state["selected_symbol"] == "^GSPC"
    assert page.session_state["nav"] == "Home"


def test_add_duplicate_and_remove_watchlist_symbol():
    page = app()
    page.text_input(key="wl_add_query").set_value("NVDA")
    page.button(key="wl_add_btn").click().run()
    assert_clean(page)
    assert page.session_state["watchlist"] == ["AAPL", "MCD", "NVDA"]
    assert page.button(key="wl_pick_NVDA")
    page.button(key="wl_add_btn").click().run()
    assert_clean(page)
    assert page.session_state["watchlist"].count("NVDA") == 1
    page.selectbox(key="wl_remove_choice").select("NVDA").run()
    page.button(key="wl_remove_btn").click().run()
    assert_clean(page)
    assert page.session_state["watchlist"] == ["AAPL", "MCD"]
    assert not any(button.key == "wl_pick_NVDA" for button in page.button)


def test_empty_stock_watchlist_keeps_index_rows_and_add_control():
    page = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=45)
    page.session_state["watchlist"] = []
    page.run()
    assert_clean(page)
    assert len([button for button in page.button if (button.key or "").startswith("wl_pick_")]) == 3
    assert page.button(key="wl_add_btn")
    assert not any(button.key == "wl_remove_btn" for button in page.button)
