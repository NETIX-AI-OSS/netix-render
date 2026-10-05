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
    summary_kinds = {"banner", "kpi_grid", "ai_insight"}
    # Weekly briefs without live KPI cards have room for their trend evidence.
    if not any(s.kind == "kpi_grid" for s in document.sections):
        summary_kinds.add("trend_pair")
    summary: list[ReportSection] = [s for s in document.sections if s.kind in summary_kinds]
    # Site context already appears in the page kicker; avoid repeating it in every headline.
    headlines = [
        item.model_copy(update={"title": item.title.removeprefix(f"{document.meta.asset.name} · ")})
        for item in details.items
    ]
    pages = [ReportPage("Executive summary", summary, headlines=headlines)]
    pages.extend(ReportPage(item.title, detail=item) for item in headlines)
    for section in document.sections:
        if section.kind in summary_kinds | {"headline_details", "footer"}:
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
    # Keep a short issue register and its actions together; long tables retain
    # their existing pagination bounds. Text budget includes every cell.
    for index in range(len(pages) - 1, 0, -1):
        previous, current = pages[index - 1], pages[index]
        if len(previous.sections) != 1 or len(current.sections) != 1:
            continue
        issues, actions = previous.sections[0], current.sections[0]
        if issues.kind != "exceptions" or actions.kind != "actions":
            continue
        rows = [*issues.rows, *actions.rows]
        text_size = sum(len(str(value)) for row in rows for value in row.model_dump().values())
        if len(issues.rows) <= 3 and len(actions.rows) <= 3 and text_size <= 1300:
            previous.title = "Issues and coming-week priorities"
            previous.sections.append(actions)
            pages.pop(index)
    footers = [s for s in document.sections if s.kind == "footer"]
    pages[-1].sections.extend(footers)
    return pages
