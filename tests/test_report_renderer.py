import pytest

from netix_render.renderer import bold_markup, display_datetime, render_report
from netix_render.schema import ReportDocument
from tests.support import (
    FIXTURE_NAMES,
    GOLDEN_DIR,
    assert_matches_snapshot,
    load_document,
    load_fixture_json,
    normalize_text,
    visible_text_chunks,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_render_report_matches_snapshot(name):
    html = render_report(load_document(name))
    assert_matches_snapshot(f"{name}.html", html)


def test_daily_render_contains_every_visible_demo_text():
    demo_html = (GOLDEN_DIR / "Villa63_Report_Daily.html").read_text(encoding="utf-8")
    rendered = render_report(load_document("villa63_daily"))
    rendered_text = normalize_text(" ".join(visible_text_chunks(rendered)))
    missing = [chunk for chunk in visible_text_chunks(demo_html) if chunk not in rendered_text]
    assert not missing, f"Demo text missing from rendered report: {missing}"


def test_daily_render_preserves_component_classes_and_section_order():
    rendered = render_report(load_document("villa63_daily"))
    for marker in (
        '<html lang="en" dir="ltr">',
        "<title>Villa 63 — Daily Brief — Villa 63</title>",
        "linear-gradient(120deg, #0e1320, #173d33 70%, #1f7a5c)",
        'class="genbar"',
        'class="gb-badge"',
        'class="gb-right"',
        'class="mast"',
        'class="tag"',
        'class="sheet"',
        'class="banner bn-ok"',
        'class="dot d-ok"',
        'class="kpis"',
        'class="kpi"',
        'class="pill p-ok"',
        'class="pill p-warn"',
        'class="twocol"',
        'class="chart"',
        'class="ai"',
        'class="btn"',
        'class="btn ghost"',
        'class="foot"',
        'class="genfoot"',
    ):
        assert marker in rendered, f"Missing markup: {marker}"

    order = (
        'class="genbar"',
        'class="mast"',
        'class="banner bn-ok"',
        'class="kpis"',
        "Safety &amp; Plant Positive Check (06:00)",
        "Overnight Exceptions (22:00–06:00)",
        "Energy — last 7 days (MWh)",
        "FAHU supply-air offset — last 7 days (°C)",
        'class="ai"',
        "Today&#39;s Actions",
        'class="foot"',
        'class="genfoot"',
    )
    positions = [rendered.index(marker) for marker in order]
    assert positions == sorted(positions)


def test_values_are_autoescaped():
    payload = load_fixture_json("villa63_daily")
    payload["sections"][1]["items"][0]["value"] = "<script>alert(1)</script>"
    rendered = render_report(ReportDocument.model_validate(payload))
    assert "<script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered


def test_rtl_direction_reaches_the_html_tag():
    payload = load_fixture_json("villa63_daily")
    payload["meta"]["language"] = "ar"
    payload["meta"]["dir"] = "rtl"
    rendered = render_report(ReportDocument.model_validate(payload))
    assert '<html lang="ar" dir="rtl">' in rendered
    assert "RTL overrides" in rendered
    assert "margin-right: auto;" in rendered


def test_accent_gradient_is_parameterized():
    payload = load_fixture_json("villa63_daily")
    payload["meta"]["accent"] = {"gradient": ["#0e1320", "#1d2b52", "#2e4a8c"]}
    rendered = render_report(ReportDocument.model_validate(payload))
    assert "linear-gradient(120deg, #0e1320, #1d2b52 70%, #2e4a8c)" in rendered
    assert ".mast .logo span {\n        color: #7fb0ff;" in rendered


def test_default_logo_line_keeps_builtin_branding():
    rendered = render_report(load_document("villa63_daily"))
    assert "IFM <span>NETIX</span> · AI PLATFORM" in rendered


def test_logo_line_override_renders_in_mast_and_email():
    from netix_render.renderer import render_email

    payload = load_fixture_json("villa63_daily")
    payload["meta"]["logo_line"] = "ACME FM · OPS"
    document = ReportDocument.model_validate(payload)
    rendered = render_report(document)
    assert "ACME FM · OPS" in rendered
    assert "IFM <span>NETIX</span> · AI PLATFORM" not in rendered
    assert "ACME FM · OPS" in render_email(document)


def test_ai_insight_bold_markers_render_as_bold():
    payload = load_fixture_json("villa63_daily")
    payload["sections"][5]["text"] = "Numbers are **grounded** & <i>safe</i>."
    rendered = render_report(ReportDocument.model_validate(payload))
    assert "Numbers are <b>grounded</b> &amp; &lt;i&gt;safe&lt;/i&gt;." in rendered


def test_bold_markup_filter():
    assert str(bold_markup("**a** and **b**")) == "<b>a</b> and <b>b</b>"
    assert str(bold_markup("<b>raw</b>")) == "&lt;b&gt;raw&lt;/b&gt;"


def test_display_datetime_is_locale_independent():
    from datetime import datetime

    assert display_datetime(datetime(2026, 6, 1, 7, 0)) == "01 Jun 2026 07:00"
    assert display_datetime(datetime(2026, 12, 31, 23, 59)) == "31 Dec 2026 23:59"
