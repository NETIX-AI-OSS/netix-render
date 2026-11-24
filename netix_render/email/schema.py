"""Contracts for the transactional email templates; extra="forbid" rejects fabricated keys."""

from typing import Any, Literal, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

Locale = Literal["en", "ar", "fr", "es", "nl", "de", "ru"]
Severity = Literal["ok", "warn", "crit"]

RTL_LOCALES = frozenset({"ar"})


def _safe_link(value: str) -> str:
    # HTML escaping protects the attribute boundary, but does not make an active URI safe.
    if urlsplit(value).scheme.lower() in {"javascript", "vbscript", "data", "file"}:
        raise ValueError("Unsupported link scheme")
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OrgBrand(StrictModel):
    """Per-tenant branding; logo_url must be an absolute URL reachable by mail clients."""

    name: str | None = None
    logo_url: str | None = None


class EmailMeta(StrictModel):
    locale: Locale = "en"
    org: OrgBrand = OrgBrand()
    # Overrides the template's default subject when set.
    subject: str | None = None

    @property
    def dir(self) -> Literal["ltr", "rtl"]:
        return "rtl" if self.locale in RTL_LOCALES else "ltr"


class TransactionalEmail(StrictModel):
    """Base for every registered email contract; guarantees the chrome always has meta."""

    meta: EmailMeta = EmailMeta()


class Cta(StrictModel):
    label: str
    url: str

    @field_validator("url")
    @classmethod
    def safe_url(cls, value: str) -> str:
        return _safe_link(value)


class FieldItem(StrictModel):
    label: str
    value: str


class StatusPill(StrictModel):
    label: str
    level: Literal["ok", "warn", "crit", "grey"] = "grey"


class OtpCodeEmail(TransactionalEmail):
    code: str
    expires_minutes: int | None = None
    product_name: str = "Netix.AI"


class ReportReadyEmail(TransactionalEmail):
    file_name: str
    download_url: str
    report_label: str | None = None
    expiry_note: str | None = None

    @field_validator("download_url")
    @classmethod
    def safe_download_url(cls, value: str) -> str:
        return _safe_link(value)


class EntityEventEmail(TransactionalEmail):
    """Generic CAFM lifecycle notice: complaint / work order / PPM / audit / inspection / contract events."""

    entity_type: str
    entity_ref: str | None = None
    title: str
    status: StatusPill | None = None
    fields: list[FieldItem] = []
    body_text: str | None = None
    cta: Cta | None = None
    note: str | None = None


class StaffAlertEmail(TransactionalEmail):
    heading: str
    severity: Severity = "warn"
    body_lines: list[str] = []
    fields: list[FieldItem] = []
    cta: Cta | None = None


class PackFile(StrictModel):
    name: str
    size_label: str | None = None


class ReportPackEmail(TransactionalEmail):
    pack_label: str
    period_label: str | None = None
    files: list[PackFile] = []
    portal: Cta | None = None
    note: str | None = None


class AlarmNoticeEmail(TransactionalEmail):
    """Chrome around a user-authored alarm body; body_text is treated as plain text and escaped."""

    severity: Severity = "warn"
    alarm_name: str
    asset_name: str | None = None
    triggered_at_label: str | None = None
    body_text: str
    fields: list[FieldItem] = []
    cta: Cta | None = None


class DigestRow(StrictModel):
    label: str
    counts: list[int]


class DigestGroup(StrictModel):
    label: str
    counts: list[int]
    rows: list[DigestRow] = []


class StatusDigestEmail(TransactionalEmail):
    """Counts table grouped in two levels (e.g. org, then building) with the detail file attached."""

    heading: str
    severity: Severity = "warn"
    period_label: str | None = None
    intro: str | None = None
    columns: list[str]
    groups: list[DigestGroup] = []
    totals: list[int] | None = None
    files: list[PackFile] = []
    cta: Cta | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _counts_match_columns(self) -> Self:
        counts = [group.counts for group in self.groups] + [row.counts for group in self.groups for row in group.rows]
        if any(len(entry) != len(self.columns) for entry in [*counts, *([self.totals] if self.totals else [])]):
            raise ValueError("every counts list must have one entry per column")
        return self


class OfflineTotals(StrictModel):
    monitored: int = 0
    online: int = 0
    degraded: int = 0
    offline: int = 0


class OfflineItem(StrictModel):
    display_name: str
    # "asset" and "gateway" are shown with the localized label; any other value is shown as given.
    subject_kind: str = ""
    building: str | None = None
    since: str | None = None
    duration: str | None = None


class OfflineBuilding(StrictModel):
    building: str
    monitored: int = 0
    offline: int = 0
    degraded: int = 0


class OfflineGatewayImpact(StrictModel):
    display_name: str
    since: str | None = None
    affected_assets: int = 0


class OfflineDailyReportEmail(TransactionalEmail):
    """Daily summary of offline assets and gateways for one organization.

    Takes the flat context data-service sends: `language` and `organization_name` fill `meta.locale` and
    `meta.org.name` unless `meta` sets them. Dates, times and durations arrive already formatted.
    """

    organization_name: str | None = None
    language: Locale | None = None
    report_name: str
    report_date: str
    timezone: str
    totals: OfflineTotals
    availability_pct_24h: float | None = None
    new_24h: int = 0
    recovered_24h: int = 0
    offline_items: list[OfflineItem] = []
    offline_more: int = 0
    by_building: list[OfflineBuilding] = []
    gateway_impact: list[OfflineGatewayImpact] = []
    dashboard_url: str
    attachment_note: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _flat_context_fills_meta(cls, data: Any) -> Any:
        if not isinstance(data, dict) or not isinstance(data.get("meta") or {}, dict):
            return data
        meta = dict(data.get("meta") or {})
        if data.get("language"):
            meta.setdefault("locale", data["language"])
        org = meta.get("org") or {}
        if data.get("organization_name") and isinstance(org, dict) and not org.get("name"):
            meta["org"] = {**org, "name": data["organization_name"]}
        return {**data, "meta": meta}

    @field_validator("dashboard_url")
    @classmethod
    def safe_dashboard_url(cls, value: str) -> str:
        return _safe_link(value)

    @property
    def severity(self) -> Severity:
        return "crit" if self.totals.offline else "warn" if self.totals.degraded else "ok"

    @property
    def all_online(self) -> bool:
        return not self.totals.offline and not self.totals.degraded

    @property
    def availability_value(self) -> str | None:
        """Percentage without the sign: one decimal, or a whole number when exact; None when unknown."""
        if self.availability_pct_24h is None:
            return None
        rounded = round(self.availability_pct_24h, 1)
        return str(int(rounded)) if rounded == int(rounded) else f"{rounded:.1f}"


class FeedbackRequestEmail(TransactionalEmail):
    greeting_name: str | None = None
    prompt_text: str
    entity_ref: str | None = None
    cta: Cta
    note: str | None = None
