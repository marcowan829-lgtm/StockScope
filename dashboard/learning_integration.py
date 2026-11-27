"""One-app navigation between market tools and the English V20 course."""
from pathlib import Path
import runpy

import streamlit as st
from i18n import t


COURSE_PAGES = [
    ("Learning Home", "Learning Home", "Start here"),
    ("01 Stock Market Basics", "Stock Market Basics", "10–12 min"),
    ("02 Reading Stock Charts", "Reading Stock Charts", "8–10 min"),
    ("02A Candlestick Patterns", "Candlestick Patterns", "15–25 min"),
    ("02B Technical Indicators", "Technical Indicators", "25–35 min"),
    ("03 How Orders Work", "How Orders Work", "8–10 min"),
    ("04 Researching a Company", "Researching a Company", "15–20 min"),
    ("05 Why Stock Prices Move", "Why Stock Prices Move", "6–8 min"),
    ("06 Risk & Investor Protection", "Risk & Investor Protection", "6–8 min"),
    ("Final Quiz", "Final Quiz", "24 questions"),
    ("Data & Methods", "Data & Methods", "Sources & downloads"),
]


def open_lesson(page: str) -> None:
    st.session_state.nav = "Lesson"
    st.session_state.main_nav = page
    st.session_state.learn_embedded = True
    st.session_state.main_sidebar_collapsed = False
    st.session_state._pending_nav_pills = None


def return_to_markets() -> None:
    st.session_state.nav = "Home"
    st.session_state._pending_nav_pills = "Home"
    st.session_state.learn_embedded = False


@st.dialog(t("Your study path"), position="right", width="small")
def show_study_path() -> None:
    st.markdown(
        '<span class="study-path-marker"></span>'
        '<div class="study-path-brand"><span class="study-path-logo">S</span>'
        "<div><b>StockScope Learn</b><small>"
        + t("Build your market knowledge, one lesson at a time.")
        + "</small></div></div>",
        unsafe_allow_html=True,
    )
    completed = set(st.session_state.get("completed_lessons", []))
    done = sum(name in completed for _, name, _ in COURSE_PAGES[1:9])
    st.progress(done / 8, text=t("{done} of 8 lessons completed", done=done))
    for index, (page, name, duration) in enumerate(COURSE_PAGES):
        mark = "✓" if name in completed else "○"
        if st.button(f"{mark}  {t(page)}", key=f"study_lesson_{index}", width="stretch", help=t(duration),
                     on_click=open_lesson, args=(page,)):
            st.rerun()
    st.caption(t("Your progress is saved in this browser session."))


def render_study_launcher() -> None:
    st.markdown('''<style>
      .st-key-study_path_launcher {position:fixed!important;right:0!important;top:32vh!important;width:62px!important;z-index:80!important;}
      .st-key-study_path_launcher button {width:62px!important;height:104px!important;min-height:104px!important;border-radius:55px 0 0 55px!important;background:#fff!important;border:1px solid #b2b5be!important;border-right:0!important;box-shadow:-3px 3px 12px #13172212;padding:0 0 0 8px!important;}
      .st-key-study_path_launcher button:hover {background:#fff!important;border-color:#131722!important;}
      .st-key-study_path_launcher button [data-testid="stIconMaterial"] {font-size:28px!important;color:#e34545!important;}
      .st-key-study_path_launcher button p {position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;}
    </style>''', unsafe_allow_html=True)
    with st.container(key="study_path_launcher"):
        if st.button(t("Study path"), icon=":material/menu_book:", key="open_study_path", help=t("Open your study path")):
            show_study_path()


def render_learning_page() -> None:
    st.session_state.learn_embedded = True
    # Keep the selected lesson as application state after retiring the page radio.
    # This also preserves it in sessions opened before that widget was removed.
    st.session_state.main_nav = st.session_state.get("main_nav", "Learning Home")
    with st.container(key="learning_content"):
        st.button(t("Back to markets"), key="back_to_markets", on_click=return_to_markets)
        runpy.run_path(str(Path(__file__).resolve().parents[1] / "learn" / "app.py"), run_name="__main__")
