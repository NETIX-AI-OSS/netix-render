from datetime import datetime
from xml.etree import ElementTree

from netix_render.charts import sparkline_svg, value_caption
from netix_render.renderer import render_email, render_report
from netix_render.schema import TrendPoint
from tests.support import load_document


def test_generation_time_uses_the_report_period_offset():
    document = load_document("synthetic_daily")
    document.meta.generated_at = datetime.fromisoformat("2026-09-16T03:01:00+00:00")
    document.meta.period.end = datetime.fromisoformat("2026-09-16T06:00:00+04:00")
    document.meta.timezone_label = "+04"
    for render in (render_report, render_email):
        html = render(document)
        assert "16 Sep 2026 07:01 +04" in html
        assert "16 Sep 2026 03:01 +04" not in html
    assert document.meta.generated_at.hour == 3  # rendering must not mutate the stored document


def test_a_fingerprint_does_not_claim_verification():
    document = load_document("synthetic_daily")
    for fingerprint in (None, "a" * 64):
        document.meta.sha256 = fingerprint
        for render in (render_report, render_email):
            html = render(document)
            assert "SHA-256 verified" not in html
            assert ("Artifact fingerprint recorded" in html) == bool(fingerprint)


def test_empty_sections_have_no_table_headers():
    document = load_document("synthetic_daily")
    document.sections = [section for section in document.sections if section.kind in ("actions", "exceptions")]
    for section in document.sections:
        section.rows = []
        section.subtitle = "Coverage unavailable"
    html = render_report(document)
    assert "<table" not in html and "Coverage unavailable" in html


def test_signed_chart_bars_stay_inside_the_plot():
    svg = sparkline_svg([TrendPoint(label="A", value=-10), TrendPoint(label="B", value=10)], "kW")
    root = ElementTree.fromstring(svg)
    bars = root.findall("{http://www.w3.org/2000/svg}rect")
    assert len(bars) == 2
    for bar in bars:
        assert 0 <= int(bar.attrib["y"]) <= 100
        assert int(bar.attrib["height"]) > 0
        assert int(bar.attrib["y"]) + int(bar.attrib["height"]) <= 100
    assert "-10.00" in svg


def test_large_chart_values_have_compact_signed_captions():
    assert value_caption(1500000, 2) == "1.50M"
    assert value_caption(-120000, 2) == "-120.0k"
    assert value_caption(18.5, 2) == "18.50"
