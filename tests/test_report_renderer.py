import pytest

from netix_render.renderer import bold_markup, display_datetime, render_email, render_report
from netix_render.schema import ReportDocument
from tests.support import (
    FIXTURE_NAMES,
    assert_matches_snapshot,
    load_document,
    load_fixture_json,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_render_report_matches_snapshot(name):
    html = render_report(load_document(name))
    assert_matches_snapshot(f"{name}.html", html)


def test_daily_render_preserves_component_classes_and_section_order():
    rendered = render_report(load_document("synthetic_daily"))
    for marker in (
        '<html lang="en" dir="ltr">',
        "<title>Daily Brief, Example Research Hub</title>",
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
        "Example Equipment Checks",
        "Example Exceptions",
        "Example Energy Trend",
        "Example Temperature Trend",
        'class="ai"',
        "Example Follow-up Actions",
        'class="foot"',
        'class="genfoot"',
    )
    positions = [rendered.index(marker) for marker in order]
    assert positions == sorted(positions)


def test_values_are_autoescaped():
    payload = load_fixture_json("synthetic_daily")
    payload["sections"][1]["items"][0]["value"] = "<script>alert(1)</script>"
    rendered = render_report(ReportDocument.model_validate(payload))
    assert "<script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered


def test_rtl_direction_reaches_the_html_tag():
    payload = load_fixture_json("synthetic_daily")
    payload["meta"]["language"] = "ar"
    payload["meta"]["dir"] = "rtl"
    rendered = render_report(ReportDocument.model_validate(payload))
    assert '<html lang="ar" dir="rtl">' in rendered
    assert "RTL overrides" in rendered
    assert "margin-right: auto;" in rendered


@pytest.mark.parametrize(
    "locale,direction,report_id,month,cover",
    [
        ("en", "ltr", "Report ID", "Jun", "Report cover"),
        ("ar-AE", "rtl", "معرّف التقرير", "يونيو", "غلاف التقرير"),
        ("fr", "ltr", "ID du rapport", "juin", "Couverture du rapport"),
        ("es", "ltr", "ID del informe", "jun.", "Portada del informe"),
        ("nl", "ltr", "Rapport-ID", "jun.", "Omslag van het rapport"),
        ("de", "ltr", "Berichts-ID", "Juni", "Berichtsdeckblatt"),
        ("ru", "ltr", "ID отчёта", "июня", "Обложка отчёта"),
    ],
)
def test_fixed_report_copy_uses_the_report_locale(locale, direction, report_id, month, cover):
    payload = load_fixture_json("synthetic_daily")
    payload["meta"]["language"] = locale
    payload["meta"]["dir"] = direction
    payload["meta"]["generated_at"] = "2026-06-11T06:30:00+00:00"
    document = ReportDocument.model_validate(payload)

    for surface in (render_report(document), render_email(document)):
        assert f'<html lang="{locale}" dir="{direction}">' in surface
        assert report_id in surface
        assert f"11 {month} 2026" in surface
    assert f'aria-label="{cover}"' in render_report(document, layout="community")


@pytest.mark.parametrize(
    ("language", "direction", "state", "due"),
    [
        ("en", "ltr", "State", "Due"),
        ("ar-AE", "rtl", "الحالة", "الموعد"),
        ("fr-FR", "ltr", "État", "Échéance"),
        ("es", "ltr", "Estado", "Plazo"),
        ("nl", "ltr", "Status", "Uiterlijk"),
        ("de", "ltr", "Status", "Frist"),
        ("ru-RU", "ltr", "Состояние", "Срок"),
    ],
)
def test_fixed_table_labels_render_on_desktop_mobile_and_email(language, direction, state, due):
    document = load_document("synthetic_daily")
    document.meta.language = language
    document.meta.dir = direction
    web, email = render_report(document), render_email(document)

    assert f">{state}</th>" in web and f'data-label="{state}"' in web
    assert f">{due}</th>" in web and f'data-label="{due}"' in web
    assert f">{state}</th>" in email and f">{due}</th>" in email


def test_rtl_isolates_numeric_values_in_kpis_and_authored_data_cells():
    payload = load_fixture_json("synthetic_daily")
    payload["meta"].update(language="ar-AE", dir="rtl")
    kpi = next(s for s in payload["sections"] if s["kind"] == "kpi_grid")
    kpi["items"][0]["value"] = "53 500 kWh"
    payload["sections"].append(
        {
            "kind": "data_table",
            "columns": ["مؤشر"],
            "rows": [[{"text": "18.2 °C"}], [{"text": "AHU-17"}]],
        }
    )
    document = ReportDocument.model_validate(payload)

    for html in (render_report(document), render_email(document)):
        for value in ("53 500 kWh", "18.2 °C", "AHU-17"):
            assert f"\u2068{value}\u2069" in html
    assert kpi["items"][0]["value"] == "53 500 kWh"


def test_chart_gaps_and_decimals_use_the_report_locale():
    payload = load_fixture_json("synthetic_daily")
    payload["meta"].update(language="fr", dir="ltr")
    chart = next(s for s in payload["sections"] if s["kind"] == "trend_pair")["charts"][0]
    chart["series"][0]["value"] = 12.5
    chart["series"][1]["value"] = None
    document = ReportDocument.model_validate(payload)

    for html in (render_report(document), render_email(document)):
        assert "12,50" in html
        assert ">N/D<" in html


def test_accent_gradient_is_parameterized():
    payload = load_fixture_json("synthetic_daily")
    payload["meta"]["accent"] = {"gradient": ["#0e1320", "#1d2b52", "#2e4a8c"]}
    rendered = render_report(ReportDocument.model_validate(payload))
    assert "linear-gradient(120deg, #0e1320, #1d2b52 70%, #2e4a8c)" in rendered
    assert ".mast .logo span {\n        color: #7fb0ff;" in rendered


@pytest.mark.parametrize("brand", [None, "", "Example Operations", "<b>Example & Company</b>"])
@pytest.mark.parametrize("paged", [False, True])
def test_report_branding_is_caller_supplied_on_every_surface(brand, paged):
    from html import escape

    from netix_render.pages import compose_pages
    from netix_render.renderer import render_email
    from tests.test_report_pages import multipage_document

    document = multipage_document() if paged else load_document("synthetic_daily")
    document.meta.logo_line = brand
    html = render_report(document)
    email = render_email(document)
    for output in (html, email):
        assert "IFM" not in output
        assert "NETIX" not in output
        assert "©" not in output
        assert "Platform → Reports → Verify" not in output
        if brand:
            assert escape(brand) in output
            assert "<b>Example & Company</b>" not in output
        else:
            assert 'class="logo"' not in output
    if paged:
        kicker = f"{escape(brand)} · " if brand else ""
        expected = f'<div class="page-kicker">{kicker}{document.meta.asset.name}</div>'
        assert html.count(expected) == len(compose_pages(document))


def test_ai_insight_bold_markers_render_as_bold():
    payload = load_fixture_json("synthetic_daily")
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
