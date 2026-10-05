from netix_render.pages import compose_pages
from netix_render.renderer import render_email, render_report
from netix_render.schema import HeadlineDetailsSection
from tests.support import load_document


def multipage_document():
    document = load_document("synthetic_daily")
    detail = {
        "headline_id": "H1",
        "title": "Meter evidence needs verification",
        "finding": "The energy meter is missing.",
        "impact": "Utility assessment remains incomplete.",
        "uncertainty": "The cause of missing readings has not been established.",
        "checks": ["Check the meter connection."],
        "action": "Restore telemetry and validate the reading.",
        "owner": "MEP",
        "evidence": [
            {
                "evidence_id": "E001",
                "label": "Meter",
                "observation": "Missing",
                "context": "Snapshot",
                "source": "tag:3",
            }
        ],
    }
    document.sections.append(HeadlineDetailsSection(kind="headline_details", items=[detail]))
    return document


def test_pages_link_summary_to_details_and_preserve_supporting_sections():
    document = multipage_document()
    before = document.model_dump()
    pages = compose_pages(document)
    assert pages[0].headlines[0].headline_id == "H1"
    assert pages[1].detail.title == "Meter evidence needs verification"
    assert {s.kind for p in pages for s in p.sections} == {
        s.kind for s in document.sections if s.kind != "headline_details"
    }
    html = render_report(document)
    assert 'href="#report-page-2"' in html and 'id="report-page-2"' in html
    assert "break-before: page" in html and "Why it matters" in html and "tag:3" in html
    assert "Headline deep dive" in render_email(document)
    assert document.model_dump() == before


def test_details_escape_source_text_and_long_tables_continue_on_new_pages():
    document = multipage_document()
    detail = document.sections[-1].items[0]
    detail.finding = "<script>alert('unsafe')</script>"
    table = next(s for s in document.sections if s.kind == "check_table")
    table.rows = [table.rows[0]] * 23
    pages = compose_pages(document)
    chunks = [s for p in pages for s in p.sections if s.kind == "check_table"]
    assert [len(s.rows) for s in chunks] == [10, 10, 3]
    html = render_report(document)
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_legacy_report_keeps_continuous_layout():
    document = load_document("synthetic_daily")
    assert compose_pages(document) == []
    assert 'class="report-page"' not in render_report(document)


def test_short_weekly_report_keeps_trends_and_action_plan_compact():
    document = multipage_document()
    document.sections = [s for s in document.sections if s.kind != "kpi_grid"]
    for section in document.sections:
        if section.kind in ("exceptions", "actions"):
            section.rows = section.rows[:1]
    before = document.model_dump()
    pages = compose_pages(document)
    assert "trend_pair" in {s.kind for s in pages[0].sections}
    plan = next(p for p in pages if p.title == "Issues and coming-week priorities")
    assert [s.kind for s in plan.sections if s.kind != "footer"] == ["exceptions", "actions"]
    assert document.model_dump() == before
    assert {s.kind for p in pages for s in p.sections} == {
        s.kind for s in document.sections if s.kind != "headline_details"
    }


def test_dense_planning_register_keeps_separate_pages():
    document = multipage_document()
    issues = next(s for s in document.sections if s.kind == "exceptions")
    actions = next(s for s in document.sections if s.kind == "actions")
    issues.rows = [issues.rows[0].model_copy(update={"assessment": "Evidence qualification. " * 40})] * 3
    actions.rows = [actions.rows[0]] * 3
    pages = compose_pages(document)
    assert not any(p.title == "Issues and coming-week priorities" for p in pages)


def test_community_layout_preserves_evidence_uncertainty_and_actions():
    document = multipage_document()
    before = document.model_dump()
    rendered = render_report(document, layout="community")
    for detail in document.sections[-1].items:
        for value in (detail.finding, detail.impact, detail.uncertainty, detail.action, detail.owner, *detail.checks):
            assert value in rendered
        for evidence in detail.evidence:
            assert evidence.evidence_id in rendered and evidence.source in rendered
    assert 'id="report-cover"' in rendered
    assert 'href="#report-page-2"' in rendered
    assert "Comment · operational impact" in rendered
    assert document.model_dump() == before


def test_community_cover_rejects_external_images_and_escapes_branding():
    import pytest

    document = multipage_document()
    document.meta.logo_line = '<script>brand</script>'
    html = render_report(document, layout="community", cover_image="data:image/jpeg;base64,YQ==")
    assert '<script>brand</script>' not in html
    assert '&lt;script&gt;brand&lt;/script&gt;' in html
    with pytest.raises(ValueError, match="embedded"):
        render_report(document, layout="community", cover_image="https://example.com/cover.jpg")


def test_community_layout_paginates_legacy_weekly_document_without_mutation():
    document = load_document("synthetic_weekly")
    before = document.model_dump()
    html = render_report(document, layout="community")
    assert 'id="report-cover"' in html
    assert 'id="report-page-1"' in html
    assert 'id="report-page-2"' in html
    assert document.model_dump() == before
