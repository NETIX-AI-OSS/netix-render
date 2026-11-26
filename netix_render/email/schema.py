"""Contracts for the transactional email templates; extra="forbid" rejects fabricated keys."""

import math
from decimal import ROUND_FLOOR, Decimal
from typing import Annotated, Any, Literal, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Locale = Literal["en", "ar", "fr", "es", "nl", "de"]
Severity = Literal["ok", "warn", "crit"]

RTL_LOCALES = frozenset({"ar"})


def _safe_link(value: str) -> str:
    # HTML escaping protects the attribute boundary, but does not make an active URI safe.
    if urlsplit(value).scheme.lower() in {"javascript", "vbscript", "data", "file"}:
        raise ValueError("Unsupported link scheme")
    return value


def _percent_text(value: float | None, floor: bool = False) -> str | None:
    """Percentage without the sign: one decimal, or a whole number when exact; None when unknown.

    floor=True never rounds up (98.96 shows as 98.9), so an SLA figure cannot appear to meet a target it missed.
    """
    if value is None:
        return None
    number = (
        Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_FLOOR) if floor else Decimal(str(round(value, 1)))
    )
    return str(int(number)) if number == int(number) else f"{number:.1f}"


Percent = Annotated[float, Field(ge=0, le=100)]
Count = Annotated[int, Field(ge=0)]


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


class FlatOrgContextEmail(TransactionalEmail):
    """Takes data-service's flat context: `language` and `organization_name` fill `meta.locale` and `meta.org.name`
    unless `meta` sets them; `dashboard_url` is the link-checked call to action."""

    organization_name: str | None = None
    language: Locale | None = None
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
    # Deep link to the outage in Prism (dashboard URL + /offline?outage=<id>).
    link: str | None = None

    @field_validator("link")
    @classmethod
    def safe_item_link(cls, value: str | None) -> str | None:
        return None if value is None else _safe_link(value)


class OfflineBuilding(StrictModel):
    building: str
    monitored: int = 0
    offline: int = 0
    degraded: int = 0


class OfflineGatewayImpact(StrictModel):
    display_name: str
    since: str | None = None
    affected_assets: int = 0


class OfflineChanges(StrictModel):
    """Movement over the report's 24 hours; new_vs_yesterday is new_24h minus the previous 24 hours' new count."""

    new_24h: Count = 0
    recovered_24h: Count = 0
    still_down: Count = 0
    new_vs_yesterday: int | None = None


class OfflineIncident(StrictModel):
    """One incident group, biggest first. A gateway incident's `affected` counts the assets unreachable behind it."""

    title: str
    kind: Literal["gateway", "building", "single"]
    since: str | None = None
    duration: str | None = None
    affected: Count = 0
    link: str | None = None

    @field_validator("link")
    @classmethod
    def safe_incident_link(cls, value: str | None) -> str | None:
        return None if value is None else _safe_link(value)


class OfflineDailyReportEmail(FlatOrgContextEmail):
    """Daily summary of offline assets and gateways for one organization.

    Dates, times and durations arrive already formatted. Every key added in 0.1.6 (subject_line, all_clear, changes,
    incidents, availability_delta, snoozed_count, maintenance_count, offline_items[].link) is optional, so a 0.1.5
    sender still validates. `all_clear` switches to the short "Everything is reporting" variant.
    """

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
    subject_line: str | None = None
    all_clear: bool = False
    changes: OfflineChanges | None = None
    incidents: list[OfflineIncident] = Field(default=[], max_length=20)
    availability_delta: str | None = None
    snoozed_count: Count = 0
    maintenance_count: Count = 0

    @property
    def severity(self) -> Severity:
        if self.all_clear:
            return "ok"
        return "crit" if self.totals.offline else "warn" if self.totals.degraded else "ok"

    @property
    def all_online(self) -> bool:
        return not self.totals.offline and not self.totals.degraded

    @property
    def availability_value(self) -> str | None:
        """Percentage without the sign: one decimal, or a whole number when exact; None when unknown."""
        return _percent_text(self.availability_pct_24h)

    @property
    def movement(self) -> OfflineChanges:
        """`changes` when sent; a 0.1.5 sender's new_24h / recovered_24h otherwise (still down = offline now)."""
        return self.changes or OfflineChanges(
            new_24h=max(self.new_24h, 0), recovered_24h=max(self.recovered_24h, 0), still_down=self.totals.offline
        )


class MonthlyTotals(StrictModel):
    monitored: Count = 0
    availability_pct: Percent | None = None
    outages: Count = 0
    # Formatted duration, e.g. "3 d 4 h".
    total_offline: str | None = None

    @property
    def availability_value(self) -> str | None:
        return _percent_text(self.availability_pct, floor=True)


class MonthlyBuilding(StrictModel):
    building: str
    availability: Percent | None = None
    outages: Count = 0
    total_offline: str | None = None
    worst_device: str | None = None

    @property
    def availability_value(self) -> str | None:
        return _percent_text(self.availability, floor=True)


class MonthlyDevice(StrictModel):
    display_name: str
    building: str | None = None
    outages: Count = 0
    total_offline: str | None = None


class OfflineMonthlyReportEmail(FlatOrgContextEmail):
    """Monthly availability (SLA) per building for one organization.

    Takes data-service's flat context like offline_daily_report. Durations and the period label arrive formatted;
    availability figures are percentages (0-100) shown floored to one decimal, never rounded up to a target.
    """

    report_name: str
    period_label: str
    timezone: str
    totals: MonthlyTotals
    availability_target: Percent | None = None
    buildings: list[MonthlyBuilding] = Field(default=[], max_length=100)
    worst_devices: list[MonthlyDevice] = Field(default=[], max_length=20)

    @property
    def target_value(self) -> str | None:
        return _percent_text(self.availability_target)

    @property
    def any_building_below_target(self) -> bool:
        return any(self.below_target(row.availability) for row in self.buildings)

    def below_target(self, availability: float | None) -> bool:
        return (
            availability is not None
            and self.availability_target is not None
            and availability < self.availability_target
        )

    @property
    def bar_floor(self) -> int:
        """Where the zoomed availability bars start: 90%, lower when a building is within a point of that or below."""
        lows = [row.availability for row in self.buildings if row.availability is not None]
        return max(0, min(90, math.floor(min(lows)) - 1)) if lows else 90

    def _bar_position(self, value: float) -> int:
        """Whole percent of the bar for a value on the bar_floor..100 scale; only exactly 100 fills the bar."""
        floor = self.bar_floor
        if value <= floor:
            return 0
        if value >= 100:
            return 100
        return min(99, max(1, int((value - floor) * 100 / (100 - floor))))

    def bar_cells(self, availability: float) -> list[tuple[str, int]]:
        """Email-safe bar as (kind, width %) cells: "fill", "lane", and a 2 px "marker" at the target when it is on the
        scale. Zero-width cells are dropped; widths of the percent cells add up to 100."""
        fill = self._bar_position(availability)
        target = self.availability_target
        if target is None or target <= self.bar_floor or target >= 100:
            cells = [("fill", fill), ("lane", 100 - fill)]
        else:
            mark = self._bar_position(target)
            if fill <= mark:
                cells = [("fill", fill), ("lane", mark - fill), ("marker", 0), ("lane", 100 - mark)]
            else:
                cells = [("fill", mark), ("marker", 0), ("fill", fill - mark), ("lane", 100 - fill)]
        return [cell for cell in cells if cell[0] == "marker" or cell[1] > 0]


class FeedbackRequestEmail(TransactionalEmail):
    greeting_name: str | None = None
    prompt_text: str
    entity_ref: str | None = None
    cta: Cta
    note: str | None = None
