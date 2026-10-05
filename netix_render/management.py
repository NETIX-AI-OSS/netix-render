"""Bounded management presentation metadata; never part of ReportDocument's public API."""

from pydantic import BaseModel, ConfigDict, Field

from netix_render.pages import ReportPage, compose_pages
from netix_render.schema import ReportDocument, ReportSection


class Metric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(max_length=100)
    value: str = Field(max_length=50)
    note: str = Field(max_length=180)


class Context(BaseModel):
    metrics: list[Metric] = Field(max_length=6)
    families: list[dict] = Field(default_factory=list, max_length=8)
    comparison: dict = Field(default_factory=dict)
    reliability: dict = Field(default_factory=dict)
    coverage: str = Field(max_length=1000)
    clock: dict = Field(default_factory=dict)


def validate_context(value):
    return Context.model_validate(value).model_dump()


def management_pages(document: ReportDocument) -> list[ReportPage]:
    details = next((s.items for s in document.sections if s.kind == "headline_details"), [])
    # Bound two short diagnostic findings per page; telemetry gets its own visual page.
    operating = [item for item in details if not any(e.source.startswith("data_query:hourly:") for e in item.evidence)]
    power = [item for item in details if item not in operating]
    sections: list[ReportSection] = [s for s in document.sections if s.kind == "ai_insight"]
    pages = [ReportPage("Executive summary", sections, headlines=list(details))]
    for start in range(0, len(operating), 2):
        pages.append(ReportPage("Reliability and comfort", headlines=operating[start : start + 2]))
    for item in power:
        pages.append(ReportPage("Plant operating patterns", detail=item))
    # Preserve additional customer sections; core weekly sections have dedicated presentation above.
    core = {"banner", "ai_insight", "headline_details", "exceptions", "actions", "footer", "trend_pair"}
    for page in compose_pages(document, compact_sources=True):
        extra = [section for section in page.sections if section.kind not in core]
        if extra:
            pages.append(ReportPage("Supporting measurements", extra))
    action_sections: list[ReportSection] = [s for s in document.sections if s.kind == "actions"]
    pages.append(ReportPage("Priorities for the coming week", action_sections, headlines=list(details)))
    return pages
