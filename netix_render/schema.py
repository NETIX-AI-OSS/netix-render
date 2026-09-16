"""The JSON contract between report generation and rendering; extra="forbid" rejects fabricated keys."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

HEX_COLOR = r"^#[0-9a-fA-F]{6}$"

StatusLevel = Literal["ok", "warn", "crit"]
TextStatus = Literal["ok", "warn", "crit", "mut"]
PillLevel = Literal["ok", "warn", "crit", "grey"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReportPeriod(StrictModel):
    start: datetime
    end: datetime
    label: str


class ReportAsset(StrictModel):
    id: str
    name: str
    location: str | None = None


class ReportAccent(StrictModel):
    gradient: list[Annotated[str, Field(pattern=HEX_COLOR)]] = Field(min_length=3, max_length=3)
    logo_color: Annotated[str, Field(pattern=HEX_COLOR)] = "#7fb0ff"


class ReportMeta(StrictModel):
    report_id: str
    engine_version: str
    generated_at: datetime
    period: ReportPeriod
    asset: ReportAsset
    title: str
    tag_line: str
    language: str = "en"
    dir: Literal["ltr", "rtl"] = "ltr"
    accent: ReportAccent = ReportAccent(gradient=["#0e1320", "#1d2b52", "#2e4a8c"])
    # Branding override for masthead logo; None keeps the builtin NETIX line.
    logo_line: str | None = None
    timezone_label: str = "GST"
    manual_edits: int = 0
    sha256: str | None = None


class BannerSection(StrictModel):
    kind: Literal["banner"]
    level: StatusLevel
    text: str


class KpiItem(StrictModel):
    value: str
    label: str
    status: TextStatus = "ok"
    note: str | None = None
    note_status: TextStatus | None = None


class KpiGridSection(StrictModel):
    kind: Literal["kpi_grid"]
    items: list[KpiItem]


class PillState(StrictModel):
    label: str
    level: PillLevel


class CheckRow(StrictModel):
    system: str
    state: PillState
    detail: str


class CheckTableSection(StrictModel):
    kind: Literal["check_table"]
    title: str
    icon: str
    subtitle: str | None = None
    rows: list[CheckRow]


class ExceptionRow(StrictModel):
    rank: int
    event: str
    asset: str
    assessment: str
    owner: str


class ExceptionsSection(StrictModel):
    kind: Literal["exceptions"]
    title: str
    icon: str
    subtitle: str | None = None
    rows: list[ExceptionRow]


class TrendPoint(StrictModel):
    label: str
    value: float | None = None


class TrendChart(StrictModel):
    title: str
    icon: str | None = None
    subtitle: str | None = None
    unit: str
    series: list[TrendPoint]
    highlight_last: bool = True
    color: Annotated[str, Field(pattern=HEX_COLOR)] = "#2e5bd7"
    highlight_color: Annotated[str, Field(pattern=HEX_COLOR)] = "#dd4257"
    decimals: int = 2


class TrendPairSection(StrictModel):
    kind: Literal["trend_pair"]
    charts: list[TrendChart] = Field(min_length=1, max_length=2)


class AiInsightSection(StrictModel):
    kind: Literal["ai_insight"]
    title: str | None = None
    text: str


class HeadlineEvidence(StrictModel):
    evidence_id: str
    label: str
    observation: str
    context: str
    source: str


class HeadlineDetail(StrictModel):
    headline_id: str
    title: str
    finding: str
    impact: str
    uncertainty: str
    checks: list[str] = Field(max_length=3)
    action: str
    owner: str
    evidence: list[HeadlineEvidence] = Field(max_length=4)


class HeadlineDetailsSection(StrictModel):
    kind: Literal["headline_details"]
    items: list[HeadlineDetail] = Field(max_length=3)


class ActionRow(StrictModel):
    due: str
    action: str
    owner: str
    source: str | None = None


class ActionsSection(StrictModel):
    kind: Literal["actions"]
    title: str
    icon: str
    subtitle: str | None = None
    rows: list[ActionRow]


class TableCell(StrictModel):
    text: str = ""
    bold: bool = False
    status: TextStatus | None = None
    pill: PillState | None = None


class DataTablePanel(StrictModel):
    title: str | None = None
    icon: str | None = None
    subtitle: str | None = None
    columns: list[str]
    rows: list[list[TableCell]]


class DataTableSection(DataTablePanel):
    kind: Literal["data_table"]


class TwoColSection(StrictModel):
    kind: Literal["twocol"]
    panels: list[DataTablePanel] = Field(min_length=2, max_length=2)


class HBarRow(StrictModel):
    label: str
    value: float
    display: str
    status: Literal["ok", "warn", "crit", "neutral"] = "neutral"


class HBarChartSection(StrictModel):
    kind: Literal["hbar_chart"]
    title: str
    icon: str
    subtitle: str | None = None
    rows: list[HBarRow]
    scale_max: float | None = None


class RingItem(StrictModel):
    pct: float = Field(ge=0, le=100)
    value_label: str
    label: str
    sublabel: str
    status: Literal["ok", "info", "warn", "crit"] = "ok"


class RingsSection(StrictModel):
    kind: Literal["rings"]
    items: list[RingItem]


class FooterLink(StrictModel):
    label: str
    url: str


class FooterButton(StrictModel):
    label: str
    url: str
    ghost: bool = False


class FooterSection(StrictModel):
    kind: Literal["footer"]
    note: str
    distribution: list[str] = []
    links: list[FooterLink] = []
    buttons: list[FooterButton] = []


ReportSection = Annotated[
    BannerSection
    | KpiGridSection
    | CheckTableSection
    | ExceptionsSection
    | TrendPairSection
    | AiInsightSection
    | HeadlineDetailsSection
    | ActionsSection
    | DataTableSection
    | TwoColSection
    | HBarChartSection
    | RingsSection
    | FooterSection,
    Field(discriminator="kind"),
]


class ReportDocument(StrictModel):
    meta: ReportMeta
    sections: list[ReportSection]
