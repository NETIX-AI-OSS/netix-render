import pytest
from pydantic import ValidationError

from netix_render.management import management_pages
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
