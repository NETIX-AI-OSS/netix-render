"""NETIX HTML render engine: brand-token Jinja rendering for reports and transactional email."""

from netix_render.email.registry import TEMPLATES, RenderedEmail, render_email_template
from netix_render.renderer import render_email, render_report
from netix_render.schema import ReportDocument
from netix_render.tokens import tokens

__all__ = [
    "TEMPLATES",
    "RenderedEmail",
    "ReportDocument",
    "render_email",
    "render_email_template",
    "render_report",
    "tokens",
]
