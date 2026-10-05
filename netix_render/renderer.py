"""Report Document to HTML in a sandboxed Jinja2 env; render_email inlines styles via css-inline."""

import re
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import css_inline
from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment
from markupsafe import Markup, escape

from netix_render import charts
from netix_render.pages import compose_pages
from netix_render.schema import (
    AnalysisChart,
    HBarChartSection,
    HeadlineDetailsSection,
    ReportDocument,
    RingItem,
    TrendChart,
)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

MONTH_ABBREVIATIONS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

BOLD_MARKER_PATTERN = re.compile(r"\*\*(.+?)\*\*", flags=re.DOTALL)


def display_datetime(value: datetime) -> str:
    """Locale-independent '11 Jun 2026 06:30' formatting used by the generation chrome."""
    month = MONTH_ABBREVIATIONS[value.month - 1]
    return f"{value.day:02d} {month} {value.year} {value.hour:02d}:{value.minute:02d}"  # noqa: E231


def bold_markup(value: str) -> Markup:
    """Escapes value, then applies the only markup AI-insight text may carry: **bold** markers become <b> elements."""
    escaped = str(escape(value))
    return Markup(BOLD_MARKER_PATTERN.sub(r"<b>\1</b>", escaped))


def _sparkline(chart: TrendChart, wide: bool) -> Markup:
    width, height = (640, 136) if wide else (330, 126)
    return Markup(
        charts.sparkline_svg(
            chart.series,
            chart.unit,
            highlight_last=chart.highlight_last,
            width=width,
            height=height,
            color=chart.color,
            highlight_color=chart.highlight_color,
            decimals=chart.decimals,
        )
    )


def _hbar(section: HBarChartSection) -> Markup:
    return Markup(charts.hbar_svg(section.rows, section.scale_max))


def _analysis(chart: AnalysisChart, wide: bool = False) -> Markup:
    return Markup(charts.analysis_svg(chart, wide=wide))


def _ring(item: RingItem) -> Markup:
    return Markup(charts.ring_svg(item))


@cache
def environment() -> SandboxedEnvironment:
    """The shared autoescaping environment, rooted at the package templates dir (reports/ and email/ trees)."""
    # Both roots so the verbatim report templates keep their "components/x.j2" imports
    # while email templates are addressed namespaced as "email/x.html.j2".
    env = SandboxedEnvironment(
        loader=FileSystemLoader([str(TEMPLATES_DIR), str(TEMPLATES_DIR / "reports")]),
        autoescape=True,
    )
    env.filters["display_datetime"] = display_datetime
    env.filters["bold_markup"] = bold_markup
    env.tests["hourly_source"] = lambda value: str(value).startswith("data_query:hourly:")
    env.globals.update(sparkline=_sparkline, hbar=_hbar, ring=_ring, analysis_chart=_analysis)
    return env


def local_document(document: ReportDocument) -> ReportDocument:
    """Align generation time with the report period's explicit timezone, including saved artifacts."""
    zone = document.meta.period.end.tzinfo
    if zone is None or document.meta.generated_at.tzinfo is None:
        return document
    meta = document.meta.model_copy(update={"generated_at": document.meta.generated_at.astimezone(zone)})
    return document.model_copy(update={"meta": meta})


def render_report(
    document: ReportDocument,
    *,
    layout: Literal["standard", "community"] = "standard",
    cover_image: str | None = None,
    analysis_charts: list[AnalysisChart] | None = None,
    source_links: dict[str, list[dict[str, str]]] | None = None,
    management: dict | None = None,
) -> str:
    """Render the canonical web report for a validated Report Document."""
    document = local_document(document)
    if cover_image and not cover_image.startswith(("data:image/jpeg;base64,", "data:image/png;base64,")):
        raise ValueError("Cover images must be embedded JPEG or PNG data URLs.")
    validated_links: dict[str, list[dict[str, str]]] = {}
    for source, links in (source_links or {}).items():
        validated_links[source] = []
        for link in links:
            url = link["url"]
            parsed = urlsplit(url)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.username
                or parsed.password
                or any(ord(char) < 32 for char in url)
            ):
                raise ValueError("Report links must be HTTP(S) URLs without credentials or control characters.")
            validated_links[source].append({"url": url, "label": link["label"]})

    def links_for(sources):
        result, seen = [], set()
        for source in sources.split(";"):
            for link in validated_links.get(source.strip(), []):
                if link["url"] not in seen:
                    result.append(link)
                    seen.add(link["url"])
        return result

    pages = compose_pages(document, compact_sources=layout == "community")
    if layout == "community" and not pages:
        # Apply the same bounded composition to older weekly documents without deep dives.
        paged_document = document.model_copy(
            update={"sections": [*document.sections, HeadlineDetailsSection(kind="headline_details", items=[])]}
        )
        pages = compose_pages(paged_document, compact_sources=True)
    if management and layout == "community":
        from netix_render.management import management_pages, validate_context

        management = validate_context(management)
        pages = management_pages(document)
    return (
        environment()
        .get_template("reports/report_base.html.j2")
        .render(
            doc=document,
            pages=pages,
            layout=layout,
            cover_image=cover_image,
            analysis_charts=analysis_charts or [],
            links_for=links_for,
            management=management,
        )
    )


def render_email(document: ReportDocument) -> str:
    """Render the email-safe variant: table layout, no SVG, styles inlined per element."""
    html = environment().get_template("reports/report_email.html.j2").render(doc=local_document(document))
    return css_inline.inline(html)
