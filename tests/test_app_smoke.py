import pytest
from streamlit.testing.v1 import AppTest

from conftest import ROOT


def assert_clean(app):
    assert not app.exception, [exception.message for exception in app.exception]


@pytest.mark.parametrize("page", [
    'Learning Home', '01 Stock Market Basics', '02 Reading Stock Charts', '02A Candlestick Patterns',
    '02B Technical Indicators', '03 How Orders Work', '04 Researching a Company',
    '05 Why Stock Prices Move', '06 Risk & Investor Protection', 'Final Quiz', 'Data & Methods',
])
def test_learn_pages(page):
    app = AppTest.from_file(str(ROOT / "learn/app.py"), default_timeout=30)
    app.session_state["main_nav"] = page
    app.run()
    assert_clean(app)


@pytest.mark.parametrize("page", [
    "Home", "Index", "Market Overview", "Screener", "Live Quotes", "Returns & Risk", "Stock Research",
])
def test_dashboard_pages(page):
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30)
    app.session_state["nav"] = page
    app.session_state["_last_nav_pill"] = page if page != "Index" else "Home"
    if page == "Index":
        app.session_state["selected_symbol"] = "^GSPC"
    app.run()
    assert_clean(app)
    assert app.pills(key="nav_pills").value == (None if page == "Index" else page)
    assert "markets_tab" not in [item.key for item in app.segmented_control]


def test_all_technical_indicator_options():
    app = AppTest.from_file(str(ROOT / "learn/app.py"), default_timeout=30)
    app.session_state["main_nav"] = '02B Technical Indicators'
    app.run()
    assert_clean(app)
    for option in app.selectbox(key="tech_lab_indicator_choice").options:
        app.selectbox(key="tech_lab_indicator_choice").select(option).run()
        assert_clean(app)


def test_dashboard_chart_controls_and_persistence():
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30).run()
    for chart_type in ["Line", "Candle", "Area", "Baseline"]:
        app.segmented_control(key="chart_type").set_value(chart_type).run()
        for chart_range in ["1D", "5D", "1M", "6M", "1Y", "All Time"]:
            app.pills(key="chart_range").set_value(chart_range).run()
            assert_clean(app)
    app.pills(key="nav_pills").set_value("Screener").run()
    app.pills(key="nav_pills").set_value("Home").run()
    assert_clean(app)
    assert app.segmented_control(key="chart_type").value == "Baseline"
    assert app.pills(key="chart_range").value == "All Time"


def test_index_switch_and_full_chart():
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30).run()
    app.text_input(key="nav_search").set_value("SPX").run()
    app.pills(key="idx_switcher").set_value("^NDX").run()
    assert app.session_state["selected_symbol"] == "^NDX"
    app.button(key="idx_full_chart").click().run()
    assert_clean(app)
    assert app.session_state["index_full_chart"]
    app.button(key="idx_exit_full").click().run()
    app.button(key="idx_back").click().run()
    assert_clean(app)
    assert app.session_state["nav"] == "Home"


def test_market_tools_are_reachable_from_top_navigation():
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30).run()
    sections = ["Home", "Market Overview", "Screener", "Live Quotes", "Returns & Risk", "Stock Research"]
    assert app.pills(key="nav_pills").options == sections
    for page in sections[1:]:
        app.pills(key="nav_pills").set_value(page).run()
        assert_clean(app)
        assert app.session_state["nav"] == page
        if page == "Screener":
            assert app.dataframe
            assert app.slider
        else:
            assert app.get("plotly_chart")
    app.pills(key="nav_pills").set_value("Home").run()
    assert_clean(app)
    assert app.session_state["nav"] == "Home"


@pytest.mark.parametrize("tab,page", [
    ("Overview", "Market Overview"), ("Screener", "Screener"),
    ("Live quotes", "Live Quotes"), ("Returns & risk", "Returns & Risk"), ("Stock", "Stock Research"),
])
def test_existing_market_sessions_migrate(tab, page):
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30)
    app.session_state["nav"] = "Markets"
    app.session_state["nav_pills"] = "Markets"
    app.session_state["markets_tab_persist"] = tab
    app.run()
    assert_clean(app)
    assert app.session_state["nav"] == page
    assert app.pills(key="nav_pills").value == page


@pytest.mark.parametrize("removed_page", ["Learn", "Watchlist"])
def test_removed_dashboard_sections_return_to_home(removed_page):
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30)
    app.session_state["nav"] = removed_page
    app.session_state["nav_pills"] = removed_page
    app.run()
    assert_clean(app)
    assert app.session_state["nav"] == "Home"
    assert app.pills(key="nav_pills").value == "Home"


def test_stock_and_live_links_use_new_navigation():
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30).run()
    next(button for button in app.button if button.label == "Open stock details").click().run()
    assert_clean(app)
    assert app.pills(key="nav_pills").value == "Stock Research"
    next(button for button in app.button if button.label == "Open live quotes").click().run()
    assert_clean(app)
    assert app.pills(key="nav_pills").value == "Live Quotes"


def test_financial_statement_and_metric_controls():
    app = AppTest.from_file(str(ROOT / "learn/app.py"), default_timeout=30)
    app.session_state["main_nav"] = '04 Researching a Company'
    app.run()
    for i in range(3):
        app.button(key=f"statement_nav_{i}").click().run()
        assert_clean(app)
    app.radio(key="company_research_section").set_value('02 · Ratio Translator').run()
    for option in app.selectbox(key="company_metric_translator").options:
        app.selectbox(key="company_metric_translator").select(option).run()
        assert_clean(app)
    for section in ['03 · Company Detective', '04 · Research a Real Company']:
        app.radio(key="company_research_section").set_value(section).run()
        assert_clean(app)


def test_final_quiz_submission_and_reset():
    app = AppTest.from_file(str(ROOT / "learn/app.py"), default_timeout=30)
    app.session_state["main_nav"] = 'Final Quiz'
    app.run()
    submit_key = 'FormSubmitter:final_comprehensive_quiz_form-Submit quiz and view each result'
    app.button(key=submit_key).click().run()
    assert "comprehensive_quiz_result" not in app.session_state
    answer_key = [2, 0, 3, 1, 0, 2, 1, 3, 2, 0, 3, 1, 2, 1, 0, 3, 1, 2, 0, 3, 1, 3, 0, 2]
    for i, answer in enumerate(answer_key):
        radio = app.radio(key=f"comprehensive_answer_{i}")
        radio.set_value(radio.options[answer])
    app.button(key=submit_key).click().run()
    assert_clean(app)
    assert app.session_state["comprehensive_quiz_result"]["score"] == 24
    app.button(key="comprehensive_quiz_complete").click().run()
    assert 'Final Quiz' in app.session_state["completed_lessons"]
    app.button(key="comprehensive_quiz_retry").click().run()
    assert_clean(app)
    assert "comprehensive_quiz_result" not in app.session_state
    assert all(app.radio(key=f"comprehensive_answer_{i}").value is None for i in range(24))


def test_home_challenge_reveal_and_retry():
    app = AppTest.from_file(str(ROOT / "learn/app.py"), default_timeout=30).run()
    app.radio(key="home_scenario_01_answer").set_value('Rise')
    app.button(key='FormSubmitter:home_scenario_01_form-Reveal what happened').click().run()
    assert_clean(app)
    assert app.session_state["home_scenario_01_result"] == 'Rise'
    app.button(key="home_scenario_01_reset").click().run()
    assert_clean(app)
    assert "home_scenario_01_result" not in app.session_state
