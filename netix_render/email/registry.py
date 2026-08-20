"""Template registry: id -> (contract model, templates, default subject, sample); render_email_template is the API."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import cache
from typing import Any

import css_inline
from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment
from pydantic import BaseModel

from netix_render import renderer, tokens
from netix_render.email import schema
from netix_render.email.strings import translator


class RenderedEmail(BaseModel):
    subject: str
    html: str
    text: str


@dataclass(frozen=True)
class EmailTemplate:
    id: str
    model: type[schema.TransactionalEmail]
    description: str
    default_subject: Callable[[Any, Callable[..., str]], str]
    sample: dict


@cache
def _text_environment() -> SandboxedEnvironment:
    env = SandboxedEnvironment(
        loader=FileSystemLoader(str(renderer.TEMPLATES_DIR)),
        autoescape=False,
        trim_blocks=False,
        keep_trailing_newline=False,
    )
    return env


_SAMPLE_META = {"locale": "en", "org": {"name": "Acme Facilities"}}

TEMPLATES: dict[str, EmailTemplate] = {
    template.id: template
    for template in (
        EmailTemplate(
            id="otp_code",
            model=schema.OtpCodeEmail,
            description="One-time verification code (MFA / login).",
            default_subject=lambda payload, t: f"{t('verification_code')} — {payload.product_name}",
            sample={"meta": _SAMPLE_META, "code": "482913", "expires_minutes": 10},
        ),
        EmailTemplate(
            id="report_ready",
            model=schema.ReportReadyEmail,
            description="A generated file is ready to download.",
            default_subject=lambda payload, t: f"{t('report_ready')}: {payload.file_name}",
            sample={
                "meta": _SAMPLE_META,
                "file_name": "attendance_2026-08.xlsx",
                "download_url": "https://example.invalid/download/abc",
                "expiry_note": "This link expires in 7 days.",
            },
        ),
        EmailTemplate(
            id="entity_event",
            model=schema.EntityEventEmail,
            description="Generic CAFM lifecycle notice (complaint, work order, PPM, audit, contract).",
            default_subject=lambda payload, t: f"{payload.entity_type}: {payload.title}",
            sample={
                "meta": _SAMPLE_META,
                "entity_type": "Complaint",
                "entity_ref": "CMP-1042",
                "title": "AHU-3 abnormal noise",
                "status": {"label": "IN PROGRESS", "level": "warn"},
                "fields": [
                    {"label": "Location", "value": "Tower B · L4"},
                    {"label": "Assigned to", "value": "R. Verma"},
                ],
                "cta": {"label": "Open complaint", "url": "https://example.invalid/complaints/1042"},
            },
        ),
        EmailTemplate(
            id="staff_alert",
            model=schema.StaffAlertEmail,
            description="Staff/attendance alert or escalation.",
            default_subject=lambda payload, t: payload.heading,
            sample={
                "meta": _SAMPLE_META,
                "heading": "Staff absent without leave",
                "severity": "warn",
                "body_lines": ["A. Kumar did not check in today."],
                "fields": [{"label": "Site", "value": "Plant 2"}],
            },
        ),
        EmailTemplate(
            id="report_pack",
            model=schema.ReportPackEmail,
            description="Scheduled report pack delivery summary.",
            default_subject=lambda payload, t: payload.pack_label,
            sample={
                "meta": _SAMPLE_META,
                "pack_label": "Monthly performance pack",
                "period_label": "July 2026",
                "files": [{"name": "enpi_performance.pdf", "size_label": "1.2 MB"}],
            },
        ),
        EmailTemplate(
            id="alarm_notice",
            model=schema.AlarmNoticeEmail,
            description="Telemetry alarm notice wrapping a user-authored body.",
            default_subject=lambda payload, t: f"{t('alarm_triggered')}: {payload.alarm_name}",
            sample={
                "meta": _SAMPLE_META,
                "severity": "crit",
                "alarm_name": "Chiller supply temp high",
                "asset_name": "CH-01",
                "triggered_at_label": "20 Aug 2026 14:05 GST",
                "body_text": "Supply temperature 9.4°C exceeded the 8.0°C threshold.",
            },
        ),
        EmailTemplate(
            id="feedback_request",
            model=schema.FeedbackRequestEmail,
            description="Post-resolution feedback / survey request.",
            default_subject=lambda payload, t: t("feedback_intro"),
            sample={
                "meta": _SAMPLE_META,
                "greeting_name": "Sara",
                "prompt_text": "How satisfied were you with the resolution of your complaint?",
                "entity_ref": "CMP-1042",
                "cta": {"label": "Give feedback", "url": "https://example.invalid/feedback/xyz"},
            },
        ),
    )
}


def render_email_template(template_id: str, context: Mapping[str, Any]) -> RenderedEmail:
    """Validate context against the template's contract, then render subject + inlined HTML + text alternative."""
    template = TEMPLATES.get(template_id)
    if template is None:
        raise KeyError(f"Unknown email template: {template_id!r}")
    payload = template.model.model_validate(dict(context))
    translate = translator(payload.meta.locale)
    render_context = {"payload": payload, "t": translate, "tokens": tokens.tokens()}
    subject = payload.meta.subject or template.default_subject(payload, translate)
    html = renderer.environment().get_template(f"email/{template_id}.html.j2").render(subject=subject, **render_context)
    text = _text_environment().get_template(f"email/{template_id}.txt.j2").render(**render_context).strip() + "\n"
    return RenderedEmail(subject=subject, html=css_inline.inline(html), text=text)
