"""Bounded management presentation metadata; never part of ReportDocument's public API."""

from pydantic import BaseModel, ConfigDict, Field

from netix_render.management_locale import management_labels
from netix_render.pages import ReportPage, compose_pages
from netix_render.report_locale import _language
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


def _isolate_number(value: str, locale: str) -> str:
    return f"\u2066{value}\u2069" if _language(locale) == "ar" else value


def comparison_summary(comparison: dict, locale: str) -> str:
    copy = management_labels(locale)
    if not comparison.get("complete"):
        return copy["comparison_unavailable"]

    previous = comparison.get("previous_count")
    delta = comparison.get("change")
    if isinstance(previous, int) and isinstance(delta, int):
        change = format(delta, "+d")
        percent = comparison.get("change_pct")
        if isinstance(percent, int | float) and previous:
            percent_label = format(percent, "+.1f")
            if _language(locale) in {"fr", "es", "nl", "de", "ru"}:
                percent_label = percent_label.replace(".", ",")
            change = copy["comparison_pct"] % {"change": change, "percent": percent_label}
        summary = copy["comparison"] % {
            "current": _isolate_number(str(previous + delta), locale),
            "previous": _isolate_number(str(previous), locale),
            "change": _isolate_number(change, locale),
        }
        return f"{summary} {copy['zero_baseline']}" if previous == 0 else summary

    # Older callers only supplied evidence prose. Preserve that authored text when available.
    for evidence in comparison.get("evidence") or []:
        if isinstance(evidence, dict) and isinstance(observation := evidence.get("observation"), str) and observation:
            return observation
    return copy["comparison_unavailable"]


def comparison_rows(comparison: dict, locale: str) -> list[dict[str, str]]:
    if not comparison.get("complete"):
        return []
    copy = management_labels(locale)
    return [
        {
            "label": row["label"],
            "summary": copy["comparison_row"]
            % {
                "previous": _isolate_number(str(row["previous"]), locale),
                "current": _isolate_number(str(row["current"]), locale),
                "change": _isolate_number(format(row["change"], "+d"), locale),
            },
        }
        for row in (comparison.get("rows") or [])[:3]
    ]


def management_pages(document: ReportDocument) -> list[ReportPage]:
    copy = management_labels(document.meta.language)
    details = next((s.items for s in document.sections if s.kind == "headline_details"), [])
    # Bound two short diagnostic findings per page; telemetry gets its own visual page.
    operating = [item for item in details if not any(e.source.startswith("data_query:hourly:") for e in item.evidence)]
    power = [item for item in details if item not in operating]
    sections: list[ReportSection] = [s for s in document.sections if s.kind == "ai_insight"]
    pages = [ReportPage(copy["executive"], sections, headlines=list(details), role="executive")]
    for start in range(0, len(operating), 2):
        pages.append(ReportPage(copy["reliability"], headlines=operating[start : start + 2], role="reliability"))
    for item in power:
        pages.append(ReportPage(copy["plant"], detail=item, role="plant"))
    # Preserve additional customer sections; core weekly sections have dedicated presentation above.
    core = {"banner", "ai_insight", "headline_details", "exceptions", "actions", "footer", "trend_pair"}
    for page in compose_pages(document, compact_sources=True):
        extra = [section for section in page.sections if section.kind not in core]
        if extra:
            pages.append(ReportPage(copy["supporting"], extra, role="supporting"))
    action_sections: list[ReportSection] = [s for s in document.sections if s.kind == "actions"]
    pages.append(ReportPage(copy["priorities"], action_sections, headlines=list(details), role="priorities"))
    return pages
