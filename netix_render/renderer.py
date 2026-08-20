"""Report Document to HTML in a sandboxed Jinja2 env; render_email inlines styles via css-inline."""

import re
from datetime import datetime
from functools import cache
from pathlib import Path

import css_inline
from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment
from markupsafe import Markup, escape

from netix_render import charts
from netix_render.schema import HBarChartSection, ReportDocument, RingItem, TrendChart

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
    env.globals.update(sparkline=_sparkline, hbar=_hbar, ring=_ring)
    return env


def render_report(document: ReportDocument) -> str:
    """Render the canonical web report for a validated Report Document."""
    return environment().get_template("reports/report_base.html.j2").render(doc=document)


def render_email(document: ReportDocument) -> str:
    """Render the email-safe variant: table layout, no SVG, styles inlined per element."""
    html = environment().get_template("reports/report_email.html.j2").render(doc=document)
    return css_inline.inline(html)
