import re

import pytest
from pydantic import ValidationError

from netix_render.management import management_pages
from netix_render.management_locale import management_labels
from netix_render.renderer import render_report
from tests.test_report_pages import multipage_document


def context():
    return {
        "metrics": [{"label": "Open critical", "value": "0", "note": "At collection"}],
        "coverage": "Incomplete work-order coverage",
        "comparison": {"complete": False},
    }


def test_management_layout_preserves_source_links_without_raw_identifiers():
    document = multipage_document()
    original = document.model_dump()
    html = render_report(
        document,
        layout="community",
        management=context(),
        source_links={"tag:3": [{"label": "Meter", "url": "https://example.org/assets/3?from=1&to=2"}]},
    )
    assert "Previous-period" not in html
    assert "previous-period comparison is unavailable" in html
    assert 'href="https://example.org/assets/3?from=1&amp;to=2"' in html
    assert 'data-source="tag:3"' in html
    assert "E001" not in html
    assert document.model_dump() == original
    assert any(page.title == "Supporting measurements" for page in management_pages(document))


def test_management_context_is_per_render_and_escaped():
    document = multipage_document()
    ctx = context()
    ctx["metrics"][0]["label"] = "<script>unsafe</script>"
    html = render_report(document, layout="community", management=ctx)
    assert "<script>unsafe" not in html
    assert "&lt;script&gt;unsafe" in html
    standard = render_report(document)
    assert "management-metrics" not in standard


def test_management_context_bounds_metric_count():
    ctx = context()
    ctx["metrics"] *= 7
    with pytest.raises(ValidationError):
        render_report(multipage_document(), layout="community", management=ctx)


@pytest.mark.parametrize(
    ("language", "summary", "comparison", "priorities"),
    [
        ("en", "Executive summary", "What changed since last week", "Priorities for the coming week"),
        ("ar-AE", "الملخص التنفيذي", "ما الذي تغيّر منذ الأسبوع الماضي", "أولويات الأسبوع المقبل"),
        ("fr", "Synthèse de direction", "Évolution depuis la semaine dernière", "Priorités de la semaine à venir"),
        ("es", "Resumen ejecutivo", "Cambios desde la semana pasada", "Prioridades de la próxima semana"),
        ("nl", "Managementsamenvatting", "Verandering ten opzichte van vorige week", "Prioriteiten voor komende week"),
        ("de", "Management-Zusammenfassung", "Änderung zur Vorwoche", "Prioritäten für die kommende Woche"),
        ("ru-RU", "Сводка для руководства", "Что изменилось с прошлой недели", "Приоритеты на предстоящую неделю"),
    ],
)
def test_weekly_management_localizes_roles_and_renders_structured_comparison(language, summary, comparison, priorities):
    document = multipage_document()
    document.meta.language = language
    doc_before = document.model_dump()
    ctx = context()
    ctx["comparison"] = {
        "complete": True,
        "previous_count": 80,
        "change": -10,
        "change_pct": -12.5,
        "evidence": [{"observation": "Old summary from the provider"}],
        "rows": [{"label": "Tenant alarm A-12", "previous": 40, "current": 30, "change": -10}],
    }
    html = render_report(document, layout="community", management=ctx)
    assert f'aria-label="{summary}"' in html
    assert f"<h3>{comparison}</h3>" in html
    assert f'aria-label="{priorities}"' in html
    assert "Tenant alarm A-12" in html and "Old summary from the provider" not in html
    assert all(value in html for value in ("80", "70", "-10"))
    assert ("-12.5" if language in {"en", "ar-AE"} else "-12,5") in html
    assert ctx["comparison"]["evidence"][0]["observation"] == "Old summary from the provider"
    assert document.model_dump() == doc_before
    source = management_labels("en")
    labels = management_labels(language)
    assert labels.keys() == source.keys()
    for key, text in labels.items():
        assert sorted(re.findall(r"%\((\w+)\)s", text)) == sorted(re.findall(r"%\((\w+)\)s", source[key]))


def test_complete_comparison_keeps_legacy_evidence_and_handles_zero_baseline():
    document = multipage_document()
    ctx = context()
    ctx["comparison"] = {"complete": True, "evidence": [{"observation": "Custom <baseline>"}]}
    assert "Custom &lt;baseline&gt;" in render_report(document, layout="community", management=ctx)

    ctx["comparison"] = {"complete": True, "previous_count": 0, "change": 6, "change_pct": None}
    html = render_report(document, layout="community", management=ctx)
    assert "6 this week, 0 last week, change +6." in html
    assert "The previous baseline is zero." in html


def test_action_without_model_source_resolves_exact_collected_asset():
    document = multipage_document()
    actions = next(s for s in document.sections if s.kind == "actions")
    actions.rows[0].action = "Check Pump A and document pressure."
    actions.rows[0].source = None
    html = render_report(
        document,
        layout="community",
        management=context(),
        source_links={
            "alarm:1": [{"label": "Pump A", "url": "https://example.org/assets/12?from=1&to=2"}],
            "alarm:2": [{"label": "Pump AB", "url": "https://example.org/assets/13"}],
        },
    )
    assert 'href="https://example.org/assets/12?from=1&amp;to=2"' in html
    assert 'href="https://example.org/assets/13"' not in html


def test_daily_cycle_chart_highlights_validated_focus_index():
    from netix_render.charts import analysis_svg
    from netix_render.schema import AnalysisChart

    chart = AnalysisChart(
        kind="line",
        title="Measured profile",
        unit="kW",
        labels=["00:00", "01:00"],
        series=[{"name": "Pump", "values": [10, 20], "color": "#196796"}],
        note="Observed means",
        focus_index=1,
    )
    assert 'stroke-dasharray="3 3"' in analysis_svg(chart)
    chart.focus_index = 2
    with pytest.raises(ValueError, match="existing label"):
        analysis_svg(chart)


def test_evidence_precision_keeps_timestamps_and_original_document_intact():
    from netix_render.renderer import evidence_text

    assert evidence_text("-1.5295 kW · quality ok") == "-1.53 kW"
    assert evidence_text("2026-10-04T17:18:31.337325Z") == "2026-10-04T17:18:31.337325Z"


def test_composite_measurements_show_means_without_repeating_ranges():
    from netix_render.renderer import evidence_text

    source = "Room: Hourly mean readings: minimum 21.00, maximum 26.00, mean 24.00 Degrees Celsius. "
    source += "Setpoint: Hourly mean readings: minimum 22.00, maximum 22.00, mean 22.00 Degrees Celsius."
    result = evidence_text(source)
    assert "mean 24.00 °C" in result and "mean 22.00 °C" in result
    assert "minimum" not in result


@pytest.mark.parametrize("separator", [", ", " \u2014 "])
def test_community_heading_strips_current_and_historical_asset_prefix(separator):
    document = multipage_document()
    document.meta.title = document.meta.asset.name + separator + "Daily Brief"
    html = render_report(document, layout="community", management=context())
    assert "<h1>Daily Brief</h1>" in html
