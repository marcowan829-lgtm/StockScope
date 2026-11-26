import ast
import re

import pytest
from streamlit.testing.v1 import AppTest

from conftest import ROOT


PAGES = [
    "Learning Home", "01 Stock Market Basics", "02 Reading Stock Charts",
    "02A Candlestick Patterns", "02B Technical Indicators", "03 How Orders Work",
    "04 Researching a Company", "05 Why Stock Prices Move",
    "06 Risk & Investor Protection", "Final Quiz", "Data & Methods",
]


def assert_clean(app):
    assert not app.exception, [item.message for item in app.exception]


@pytest.mark.parametrize("index,page", list(enumerate(PAGES)))
def test_drawer_opens_each_course_page_in_main_app(index, page):
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=45).run()
    app.button(key="open_study_path").click().run()
    assert_clean(app)
    assert len([b for b in app.button if (b.key or "").startswith("study_lesson_")]) == 11
    app.button(key=f"study_lesson_{index}").click().run()
    assert_clean(app)
    assert app.session_state["nav"] == "Lesson"
    assert app.session_state["main_nav"] == page
    assert not any(radio.key == "main_nav" for radio in app.radio)
    assert "Your study path" not in [item.value for item in app.subheader]
    assert app.pills(key="nav_pills").options == [
        "Home", "Market Overview", "Screener", "Live Quotes", "Returns & Risk", "Stock Research",
    ]
    assert not app.sidebar.radio
    assert app.button(key="open_study_path")
    app.button(key="back_to_markets").click().run()
    assert_clean(app)
    assert app.session_state["nav"] == "Home"
    assert app.pills(key="nav_pills").value == "Home"


def test_learning_round_trip_preserves_market_selections_and_progress():
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=45).run()
    app.segmented_control(key="chart_type").set_value("Area").run()
    app.pills(key="chart_range").set_value("6M").run()
    app.session_state["watchlist"] = ["AAPL", "NVDA"]
    app.session_state["completed_lessons"] = ["Stock Market Basics"]
    app.button(key="open_study_path").click().run()
    assert app.progress[0].value == 12
    assert app.button(key="study_lesson_1").label.startswith("✓")
    app.button(key="study_lesson_1").click().run()
    app.button(key="open_study_path").click().run()
    app.button(key="study_lesson_2").click().run()
    assert_clean(app)
    app.button(key="back_to_markets").click().run()
    assert_clean(app)
    assert app.segmented_control(key="chart_type").value == "Area"
    assert app.pills(key="chart_range").value == "6M"
    assert app.session_state["watchlist"] == ["AAPL", "NVDA"]
    assert app.session_state["completed_lessons"] == ["Stock Market Basics"]


def test_learning_page_can_return_through_the_site_navigation():
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=45).run()
    app.button(key="open_study_path").click().run()
    app.button(key="study_lesson_4").click().run()
    app.pills(key="nav_pills").set_value("Screener").run()
    assert_clean(app)
    assert app.session_state["nav"] == "Screener"
    assert app.session_state["learn_embedded"] is False
    assert app.dataframe


def test_lesson_selection_survives_interacting_without_a_page_selector():
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=45).run()
    app.button(key="open_study_path").click().run()
    app.button(key="study_lesson_3").click().run()
    groups = app.selectbox(key="candle_pattern_group").options
    app.selectbox(key="candle_pattern_group").select(groups[1]).run()
    assert_clean(app)
    assert app.session_state["main_nav"] == "02A Candlestick Patterns"
    patterns = app.selectbox(key="candle_pattern_name").options
    app.selectbox(key="candle_pattern_name").select(patterns[-1]).run()
    assert_clean(app)
    assert app.session_state["main_nav"] == "02A Candlestick Patterns"
    assert app.get("plotly_chart")


def test_learning_home_stays_in_the_content_area():
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=45).run()
    app.button(key="open_study_path").click().run()
    app.button(key="study_lesson_0").click().run()
    assert_clean(app)
    markup = "\n".join(item.value for item in app.markdown)
    assert '<h1>Learning Home</h1>' in markup
    assert 'cinematic-bg' not in markup
    assert '<video' not in markup


def test_completing_a_lesson_updates_the_popup_progress():
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=45).run()
    app.button(key="open_study_path").click().run()
    app.button(key="study_lesson_1").click().run()
    app.button(key="finish_basics").click().run()
    assert_clean(app)
    assert "Stock Market Basics" in app.session_state["completed_lessons"]
    assert app.button(key="finish_basics").disabled
    assert not app.progress
    app.button(key="open_study_path").click().run()
    assert app.progress[0].value == 12
    assert app.button(key="study_lesson_1").label.startswith("✓")


def test_learning_chart_uses_canvas_surfaces(learn):
    import plotly.graph_objects as go
    figure = learn.style_fig(go.Figure())
    assert figure.layout.paper_bgcolor == "#f5f7fa"
    assert figure.layout.plot_bgcolor == "#f5f7fa"
    assert figure.layout.font.color == "#131722"
    assert figure.layout.hoverlabel.bgcolor == "#ffffff"


def test_course_interface_and_embedded_markup_are_english():
    tree = ast.parse((ROOT / "learn/app.py").read_text())
    strings = [node.value for node in ast.walk(tree)
               if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    assert not [value for value in strings if re.search(r"[\u3400-\u9fff]", value)]


@pytest.mark.parametrize("option,series", [
    ("MA | Simple Moving Average (SMA 5 / SMA 20)", ["SMA 5", "SMA 20"]),
    ("EMA | Exponential Moving Average (EMA 12 / EMA 26)", ["EMA 12", "EMA 26"]),
])
def test_translated_moving_average_options_draw_their_lines(option, series):
    app = AppTest.from_file(str(ROOT / "learn/app.py"), default_timeout=45)
    app.session_state["main_nav"] = "02B Technical Indicators"
    app.run()
    app.selectbox(key="tech_lab_indicator_choice").select(option).run()
    assert_clean(app)
    chart_spec = app.get("plotly_chart")[0].proto.spec
    for name in series:
        assert name in chart_spec
