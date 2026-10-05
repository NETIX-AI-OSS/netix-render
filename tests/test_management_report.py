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
