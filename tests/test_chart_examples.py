import xml.etree.ElementTree as ET

import pytest
from streamlit.testing.v1 import AppTest

from conftest import ROOT


@pytest.mark.parametrize("topic", [
    "price_line", "price_area", "price_baseline", "price_candle", "intraday", "stock",
    "heatmap", "ranking", "gainers", "losers", "volume", "comparison", "risk",
])
def test_example_drawings_are_accessible_and_self_contained(topic, dashboard):
    from chart_examples import annotated_example

    drawing = ET.fromstring(annotated_example(topic))
    ns = {"s": "http://www.w3.org/2000/svg"}
    assert drawing.attrib["role"] == "img"
    assert drawing.find("s:title", ns).text
    description = drawing.find("s:desc", ns).text
    assert "Fictional" in description
    assert len(drawing.findall("s:defs/s:marker", ns)) == 3
    all_text = [item.text for item in drawing.findall(".//s:text", ns)]
    assert all(str(number) in all_text for number in [1, 2, 3])
    assert not drawing.findall(".//s:script", ns)
    assert not drawing.findall(".//s:image", ns)


def test_all_chart_guides_have_a_visual_example(dashboard):
    from chart_examples import EXAMPLE_SUMMARIES
    from chart_help import CHART_GUIDES

    assert set(EXAMPLE_SUMMARIES) == set(CHART_GUIDES)


def test_visual_guide_keeps_long_instructions_collapsed():
    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30).run()
    app.button(key="chart_help_home").click().run()
    assert not app.exception
    assert app.image
    reading = next(item for item in app.expander if item.label.startswith("Read more"))
    assert not reading.proto.expanded
