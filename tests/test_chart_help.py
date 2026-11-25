import pytest
from streamlit.proto.Block_pb2 import Block
from streamlit.testing.v1 import AppTest

from conftest import ROOT


@pytest.mark.parametrize("page,key,title", [
    ("Home", "home", "Price chart: line"),
    ("Market Overview", "heatmap", "Group monthly returns"),
    ("Market Overview", "ranking", "Top performers in this window"),
    ("Market Overview", "gainers", "Daily movers: highest changes"),
    ("Market Overview", "losers", "Daily movers: lowest changes"),
    ("Market Overview", "volume", "Trading volume leaders"),
    ("Returns & Risk", "comparison", "Compare performance: everyone starts at 100"),
    ("Returns & Risk", "risk", "Return versus price swings"),
    ("Stock Research", "stock", "Historical daily candles"),
    ("Live Quotes", "intraday", "Intraday candles: one trading day"),
    ("Index", "index_price", "Price chart: candles and volume"),
    ("Index", "index_comparison", "Compare performance: everyone starts at 100"),
])
def test_question_buttons_open_the_correct_right_drawer(page, key, title):
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30)
    app.session_state["nav"] = page
    app.session_state["_last_nav_pill"] = page
    if page == "Index":
        app.session_state["selected_symbol"] = "^GSPC"
    app.run()
    assert not app.exception
    assert not app.get("dialog")
    app.button(key=f"chart_help_{key}").click().run()
    assert not app.exception, [error.message for error in app.exception]
    dialog = app.get("dialog")[0]
    assert dialog.proto.dialog.position == Block.Dialog.DialogPosition.RIGHT
    assert dialog.proto.dialog.dismissible
    assert dialog.proto.dialog.is_open
    assert title in [item.value for item in app.subheader]
    assert app.info  # Every guide has its own illustrated numerical example.
    content = "\n".join(item.value for item in app.markdown)
    for heading in ["What am I looking at?", "How to read it", "A simple example", "What can I learn?", "Keep in mind"]:
        assert heading in content
    assert app.session_state["nav"] == page
    assert "Want to learn more?" in content


@pytest.mark.parametrize("kind,title", [
    ("Line", "Price chart: line"), ("Candle", "Price chart: candles and volume"),
    ("Area", "Price chart: area"), ("Baseline", "Price chart: baseline"),
])
def test_price_help_follows_selected_chart_and_preserves_range(kind, title):
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30).run()
    app.segmented_control(key="chart_type").set_value(kind).run()
    app.pills(key="chart_range").set_value("6M").run()
    app.button(key="chart_help_home").click().run()
    assert not app.exception
    assert title in [item.value for item in app.subheader]
    assert app.segmented_control(key="chart_type").value == kind
    assert app.pills(key="chart_range").value == "6M"


@pytest.mark.parametrize("page,key,kind,topic,lesson", [
    ("Home", "home", "Line", "price_line", "02 Reading Stock Charts"),
    ("Home", "home", "Candle", "price_candle", "02A Candlestick Patterns"),
    ("Home", "home", "Area", "price_area", "02 Reading Stock Charts"),
    ("Home", "home", "Baseline", "price_baseline", "02 Reading Stock Charts"),
    ("Market Overview", "heatmap", None, "heatmap", "01 Stock Market Basics"),
    ("Market Overview", "ranking", None, "ranking", "01 Stock Market Basics"),
    ("Market Overview", "gainers", None, "gainers", "05 Why Stock Prices Move"),
    ("Market Overview", "losers", None, "losers", "05 Why Stock Prices Move"),
    ("Market Overview", "volume", None, "volume", "02 Reading Stock Charts"),
    ("Returns & Risk", "comparison", None, "comparison", "01 Stock Market Basics"),
    ("Returns & Risk", "risk", None, "risk", "06 Risk & Investor Protection"),
    ("Live Quotes", "intraday", None, "intraday", "02A Candlestick Patterns"),
    ("Stock Research", "stock", None, "stock", "02A Candlestick Patterns"),
])
def test_chart_help_opens_the_related_lesson(page, key, kind, topic, lesson):
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=45)
    app.session_state["nav"] = page
    app.session_state["_last_nav_pill"] = page
    app.run()
    if kind:
        app.segmented_control(key="chart_type").set_value(kind).run()
    app.button(key=f"chart_help_{key}").click().run()
    assert app.button(key=f"chart_lesson_{topic}").label == f"Lesson {lesson} →"
    app.button(key=f"chart_lesson_{topic}").click().run()
    assert not app.exception, [error.message for error in app.exception]
    assert app.session_state["nav"] == "Lesson"
    assert app.session_state["main_nav"] == lesson
    assert app.button(key="back_to_markets")
    assert app.button(key="open_study_path")
    assert not any(radio.key == "main_nav" for radio in app.radio)
