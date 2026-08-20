"""Contracts for the transactional email templates; extra="forbid" rejects fabricated keys."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

Locale = Literal["en", "ar", "es"]
Severity = Literal["ok", "warn", "crit"]

RTL_LOCALES = frozenset({"ar"})


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


class FeedbackRequestEmail(TransactionalEmail):
    greeting_name: str | None = None
    prompt_text: str
    entity_ref: str | None = None
    cta: Cta
    note: str | None = None
