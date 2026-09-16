"""Deterministic page composition; the model never emits HTML or page breaks."""

from dataclasses import dataclass, field

from netix_render.schema import HeadlineDetail, ReportDocument, ReportSection


@dataclass
class ReportPage:
    title: str
    sections: list[ReportSection] = field(default_factory=list)
    detail: HeadlineDetail | None = None
    headlines: list[HeadlineDetail] = field(default_factory=list)


def compose_pages(document: ReportDocument) -> list[ReportPage]:
    details = next((s for s in document.sections if s.kind == "headline_details"), None)
    if details is None:
        return []
    summary: list[ReportSection] = [s for s in document.sections if s.kind in ("banner", "kpi_grid", "ai_insight")]
    pages = [ReportPage("Executive summary", summary, headlines=details.items)]
    pages.extend(ReportPage(item.title, detail=item) for item in details.items)
    for section in document.sections:
        if section.kind in ("banner", "kpi_grid", "ai_insight", "headline_details", "footer"):
            continue
        if section.kind in ("check_table", "exceptions", "actions"):
            if not section.rows:
                continue
            limit = 10 if section.kind == "check_table" else 5
            for start in range(0, len(section.rows), limit):
                chunk = section.model_copy(update={"rows": section.rows[start : start + limit]})
                title = section.title + (" (continued)" if start else "")
                pages.append(ReportPage(title, [chunk]))
        else:
            pages.append(ReportPage("Supporting evidence", [section]))
    footers = [s for s in document.sections if s.kind == "footer"]
    pages[-1].sections.extend(footers)
    return pages
