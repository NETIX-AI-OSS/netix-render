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
            default_subject=lambda payload, t: f"{t('verification_code')}, {payload.product_name}",
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
            id="status_digest",
            model=schema.StatusDigestEmail,
            description="Periodic digest of status changes, counted per group and sub-group, detail file attached.",
            default_subject=lambda payload, t: payload.heading,
            sample={
                "meta": _SAMPLE_META,
                "heading": "IoT connectivity: 5 changes in 2 buildings",
                "period_label": "15 Oct 2026, 19:15-19:30 GST",
                "columns": ["Went offline", "Degraded", "Back online", "Offline now"],
                "groups": [
                    {
                        "label": "Acme Facilities",
                        "counts": [2, 1, 2, 9],
                        "rows": [
                            {"label": "Tower B", "counts": [2, 0, 1, 6]},
                            {"label": "Plant 2", "counts": [0, 1, 1, 3]},
                        ],
                    }
                ],
                "totals": [2, 1, 2, 9],
                "files": [{"name": "iot-status-2026-10-15-1915.xlsx", "size_label": "18 KB"}],
                "cta": {"label": "Download Excel", "url": "https://example.invalid/static/iot-status.xlsx"},
            },
        ),
        EmailTemplate(
            id="offline_daily_report",
            model=schema.OfflineDailyReportEmail,
            description="Daily summary of offline IoT assets and gateways for one organization.",
            # data-service's counted subject_line wins over "<report name>, <date>"; meta.subject wins over both.
            default_subject=lambda payload, t: payload.subject_line or f"{payload.report_name}, {payload.report_date}",
            sample={
                "organization_name": "Acme Facilities",
                "report_name": "Daily offline report",
                "report_date": "17 Nov 2026",
                "timezone": "Asia/Dubai",
                "subject_line": "3 new offline, 4 back online, 96.8% available, Tue 17 Nov",
                "totals": {"monitored": 128, "online": 121, "degraded": 2, "offline": 5},
                "availability_pct_24h": 96.84,
                "availability_delta": "-0.4 points",
                "new_24h": 3,
                "recovered_24h": 4,
                "changes": {"new_24h": 3, "recovered_24h": 4, "still_down": 2, "new_vs_yesterday": 2},
                "incidents": [
                    {
                        "title": "GW-Tower-B-02 offline",
                        "kind": "gateway",
                        "since": "16 Nov 2026 22:40",
                        "duration": "9 h 20 min",
                        "affected": 14,
                        "link": "https://example.invalid/connectivity/offline?outage=5012",
                    },
                    {
                        "title": "Plant 2",
                        "kind": "building",
                        "since": "15 Nov 2026 08:05",
                        "duration": "2 d 0 h",
                        "affected": 2,
                        "link": "https://example.invalid/connectivity/offline?outage=4981",
                    },
                    {
                        "title": "Meter M-7",
                        "kind": "single",
                        "since": "17 Nov 2026 06:12",
                        "duration": "1 h 48 min",
                        "affected": 1,
                        "link": "https://example.invalid/connectivity/offline?outage=5020",
                    },
                ],
                "snoozed_count": 1,
                "maintenance_count": 2,
                "offline_items": [
                    {
                        "display_name": "GW-Tower-B-02",
                        "subject_kind": "gateway",
                        "building": "Tower B",
                        "since": "16 Nov 2026 22:40",
                        "duration": "9 h 20 min",
                        "link": "https://example.invalid/connectivity/offline?outage=5012",
                    },
                    {
                        "display_name": "Chiller CH-01",
                        "subject_kind": "asset",
                        "building": "Plant 2",
                        "since": "15 Nov 2026 08:05",
                        "duration": "2 d 0 h",
                        "link": "https://example.invalid/connectivity/offline?outage=4981",
                    },
                    {
                        "display_name": "Pump P-4",
                        "subject_kind": "asset",
                        "building": "Plant 2",
                        "since": "16 Nov 2026 13:10",
                        "duration": "18 h 50 min",
                        "link": "https://example.invalid/connectivity/offline?outage=4999",
                    },
                ],
                "offline_more": 2,
                "by_building": [
                    {"building": "Tower B", "monitored": 74, "offline": 3, "degraded": 1},
                    {"building": "Plant 2", "monitored": 54, "offline": 2, "degraded": 1},
                ],
                "gateway_impact": [
                    {"display_name": "GW-Tower-B-02", "since": "16 Nov 2026 22:40", "affected_assets": 14}
                ],
                "dashboard_url": "https://example.invalid/connectivity",
                "attachment_note": "The full list is in the attached spreadsheet.",
                "language": "en",
            },
        ),
        EmailTemplate(
            id="offline_monthly_report",
            model=schema.OfflineMonthlyReportEmail,
            description="Monthly availability (SLA) per building for one organization's monitored IoT devices.",
            default_subject=lambda payload, t: f"{payload.report_name}, {payload.period_label}",
            sample={
                "organization_name": "Acme Facilities",
                "report_name": "Monthly availability report",
                "period_label": "October 2026",
                "timezone": "Asia/Dubai",
                "language": "en",
                "dashboard_url": "https://example.invalid/connectivity/history",
                "totals": {"monitored": 128, "availability_pct": 99.12, "outages": 37, "total_offline": "6 d 4 h"},
                "availability_target": 99.0,
                "buildings": [
                    {
                        "building": "Plant 2",
                        "availability": 97.48,
                        "outages": 21,
                        "total_offline": "4 d 2 h",
                        "worst_device": "Chiller CH-01",
                    },
                    {
                        "building": "Tower B",
                        "availability": 99.41,
                        "outages": 14,
                        "total_offline": "1 d 22 h",
                        "worst_device": "GW-Tower-B-02",
                    },
                    {
                        "building": "Harbour Office",
                        "availability": 99.99,
                        "outages": 2,
                        "total_offline": "4 min",
                        "worst_device": None,
                    },
                ],
                "worst_devices": [
                    {"display_name": "Chiller CH-01", "building": "Plant 2", "outages": 6, "total_offline": "2 d 5 h"},
                    {
                        "display_name": "GW-Tower-B-02",
                        "building": "Tower B",
                        "outages": 3,
                        "total_offline": "19 h 40 min",
                    },
                    {"display_name": "AHU-3", "building": "Tower B", "outages": 4, "total_offline": "11 h 5 min"},
                ],
                "attachment_note": "Daily availability per device is in the attached spreadsheet.",
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
