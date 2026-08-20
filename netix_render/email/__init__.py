"""Transactional email rendering: validated contracts in, (subject, html, text) out."""

from netix_render.email.registry import TEMPLATES, RenderedEmail, render_email_template

__all__ = ["TEMPLATES", "RenderedEmail", "render_email_template"]
