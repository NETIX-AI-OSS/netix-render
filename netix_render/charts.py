"""Deterministic SVG chart generators for reports -- trusted markup via |safe, so data strings are escaped here."""

from markupsafe import escape

from netix_render.schema import HBarRow, RingItem, TrendPoint

SVG_XMLNS = 'xmlns="http://www.w3.org/2000/svg"'
BAR_CAPTION_COLOR = "#5a6a8e"
BAR_LABEL_COLOR = "#8a97b5"
TRACK_COLOR = "#eef1f6"
TEXT_COLOR = "#1c2434"

HBAR_STATUS_COLORS = {
    "ok": "#16a571",
    "warn": "#e0a512",
    "crit": "#dd4257",
    "neutral": "#2e5bd7",
}

RING_STATUS_COLORS = {
    "ok": "#16a571",
    "info": "#2e5bd7",
    "warn": "#e0a512",
    "crit": "#dd4257",
}


def value_caption(value: float, decimals: int) -> str:
    """Keep a seven-point chart legible without long overlapping register labels."""
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 10_000:
        return f"{value / 1_000:.1f}k"
    return f"{value:.{decimals}f}"


def sparkline_svg(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    series: list[TrendPoint],
    _unit: str,
    highlight_last: bool = True,
    width: int = 330,
    height: int = 126,
    color: str = "#2e5bd7",
    highlight_color: str = "#dd4257",
    decimals: int = 2,
) -> str:
    """Bar sparkline scaled to series max, value captions, day labels, highlighted last bar; None renders as a gap."""
    baseline = height - 26
    label_y = height - 12
    x_start = 30
    bar_width = 26 if width <= 400 else 62
    max_bar = baseline - (13 if bar_width == 26 else 14)
    right_margin = round(width * 0.075)
    pitch = (width - x_start - bar_width - right_margin) / (len(series) - 1) if len(series) > 1 else 0.0
    values = [point.value for point in series if point.value is not None]
    low = min([0.0, *values])
    high = max([0.0, *values])
    span = high - low
    zero_y = baseline - round(max_bar * -low / span) if span else baseline

    parts = [f'<svg class="chart" width="100%" viewBox="0 0 {width} {height}" {SVG_XMLNS}>']
    for index, point in enumerate(series):
        bar_x = int(x_start + pitch * index)
        center = bar_x + bar_width // 2
        if point.value is None:
            caption = "—"
            caption_y = baseline - 5
        else:
            value_y = baseline - round(max_bar * (point.value - low) / span) if span else baseline
            bar_height = abs(value_y - zero_y)
            bar_y = min(value_y, zero_y)
            highlighted = highlight_last and index == len(series) - 1
            fill = highlight_color if highlighted else color
            opacity = "1" if highlighted else "0.55"
            parts.append(
                f'<rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="{bar_height}" rx="3" '
                f'fill="{escape(fill)}" opacity="{opacity}" />'
            )
            caption = value_caption(point.value, decimals)  # noqa: E231
            caption_y = value_y - 5 if point.value >= 0 else value_y + 10
        parts.append(
            f'<text x="{center}" y="{caption_y}" font-size="9" fill="{BAR_CAPTION_COLOR}" '
            f'text-anchor="middle" font-weight="700">{escape(caption)}</text>'
        )
        parts.append(
            f'<text x="{center}" y="{label_y}" font-size="9" fill="{BAR_LABEL_COLOR}" '
            f'text-anchor="middle">{escape(point.label)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def hbar_svg(rows: list[HBarRow], scale_max: float | None = None) -> str:
    """Horizontal compliance bars: right-anchored label, grey track, status-coloured bar scaled to scale_max."""
    track_x = 150
    track_width = 420
    row_pitch = 24
    height = row_pitch * len(rows) + 4
    maximum = scale_max if scale_max is not None else max((row.value for row in rows), default=0.0)

    parts = [f'<svg class="chart" width="100%" viewBox="0 0 640 {height}" {SVG_XMLNS}>']
    for index, row in enumerate(rows):
        y = row_pitch * index + 2
        text_y = y + 12.5
        bar_width = round(track_width * row.value / maximum) if maximum else 0
        parts.append(
            f'<text x="142" y="{text_y}" font-size="10.5" fill="{BAR_CAPTION_COLOR}" '
            f'text-anchor="end" font-weight="600">{escape(row.label)}</text>'
        )
        parts.append(f'<rect x="{track_x}" y="{y}" width="{track_width}" height="17" rx="4" fill="{TRACK_COLOR}" />')
        parts.append(
            f'<rect x="{track_x}" y="{y}" width="{bar_width}" height="17" rx="4" '
            f'fill="{HBAR_STATUS_COLORS[row.status]}" />'
        )
        parts.append(
            f'<text x="{track_x + bar_width + 8}" y="{text_y}" font-size="10.5" fill="{TEXT_COLOR}" '
            f'font-weight="700">{escape(row.display)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def ring_svg(item: RingItem) -> str:
    """Donut ring with a centred percentage and caption, matching the monthly pack's scorecard geometry."""
    circumference = 214
    dash = round(2 * 3.14159265 * 34 * item.pct / 100)
    color = RING_STATUS_COLORS[item.status]
    return (
        '<svg width="178" height="96" viewBox="0 0 178 96">'
        f'<circle cx="48" cy="48" r="34" fill="none" stroke="{TRACK_COLOR}" stroke-width="11" />'
        f'<circle cx="48" cy="48" r="34" fill="none" stroke="{color}" stroke-width="11" '
        f'stroke-linecap="round" stroke-dasharray="{dash} {circumference}" transform="rotate(-90 48 48)" />'
        f'<text x="48" y="53" font-size="16" font-weight="800" text-anchor="middle" fill="{TEXT_COLOR}">'
        f"{escape(item.value_label)}</text>"
        f'<text x="100" y="44" font-size="11.5" font-weight="800" fill="{TEXT_COLOR}">{escape(item.label)}</text>'
        f'<text x="100" y="60" font-size="10" fill="#7585a8">{escape(item.sublabel)}</text>'
        "</svg>"
    )


def analysis_svg(chart, wide: bool = False) -> str:
    """Axes, readable legends and gap-preserving lines for weekly diagnostics."""
    if any(len(series.values) != len(chart.labels) for series in chart.series):
        raise ValueError("Analysis chart labels and series must have equal lengths")
    if chart.kind == "ranked":
        return _ranked_analysis(chart)
    width, height = (640, 175) if wide else (360, 210)
    left, top, right, bottom = 38, 30, width - 10, height - 43
    maximum = (
        max(
            (
                sum((series.values[i] or 0) for series in chart.series)
                if chart.kind == "stacked"
                else max((series.values[i] or 0) for series in chart.series)
                for i in range(len(chart.labels))
            ),
            default=0,
        )
        or 1
    )
    maximum *= 1.1
    parts = [
        f'<svg class="chart" role="img" aria-label="{escape(chart.title)}" viewBox="0 0 {width} {height}" {SVG_XMLNS}>'
    ]
    for i in range(5):
        y = bottom - (bottom - top) * i / 4
        value = maximum * i / 4
        parts.append(f'<line x1="{left}" x2="{right}" y1="{y}" y2="{y}" stroke="#dce5ee" />')
        parts.append(
            f'<text x="{left - 8}" y="{y + 4}" text-anchor="end" font-size="12" fill="#668398">'
            f"{value_caption(value, 0)}</text>"
        )
    count = len(chart.labels)
    pitch = (right - left) / max(count, 1)
    for i, label in enumerate(chart.labels):
        if count <= 7 or i % max(1, count // 7) == 0:
            x = left + (i + 0.5) * pitch
            parts.append(
                f'<text x="{x}" y="{bottom + 18}" text-anchor="middle" font-size="11" fill="#668398">'
                f"{escape(label)}</text>"
            )
    if chart.kind == "stacked":
        for i in range(count):
            accumulated = 0
            for series in chart.series:
                value = series.values[i]
                if value is None:
                    continue
                h = value / maximum * (bottom - top)
                y = bottom - (accumulated + value) / maximum * (bottom - top)
                parts.append(
                    f'<rect x="{left + (i + 0.15) * pitch}" y="{y}" width="{pitch * 0.7}" height="{h}" '
                    f'fill="{escape(series.color)}" />'
                )
                accumulated += value
    else:
        for series in chart.series:
            paths: list[list[str]] = []
            path: list[str] = []
            for i, value in enumerate(series.values):
                if value is None:
                    if path:
                        paths.append(path)
                    path = []
                    continue
                x = left + (i + 0.5) * pitch
                y = bottom - value / maximum * (bottom - top)
                path.append(f"{'L' if path else 'M'}{x:.2f},{y:.2f}")
            if path:
                paths.append(path)
            for segment in paths:
                if len(segment) == 1:
                    circle_x, circle_y = segment[0][1:].split(",")
                    parts.append(f'<circle cx="{circle_x}" cy="{circle_y}" r="2.5" fill="{escape(series.color)}" />')
                else:
                    parts.append(
                        f'<path d="{" ".join(segment)}" fill="none" stroke="{escape(series.color)}" '
                        f'stroke-width="2.5" />'
                    )
    for i, series in enumerate(chart.series):
        x = left + i * (150 if len(chart.series) <= 2 else 100)
        parts.append(f'<rect x="{x}" y="9" width="14" height="8" fill="{escape(series.color)}" />')
        parts.append(f'<text x="{x + 20}" y="17" font-size="12" fill="#303234">{escape(series.name)}</text>')
    parts.append(f'<text x="{left}" y="{height - 8}" font-size="11" fill="#668398">{escape(chart.unit)}</text></svg>')
    return "".join(parts)


def _ranked_analysis(chart) -> str:
    values = chart.series[0].values
    maximum = max((value or 0 for value in values), default=0) or 1
    height = len(values) * 44 + 28
    parts = [
        f'<svg class="chart" role="img" aria-label="{escape(chart.title)}" viewBox="0 0 360 {height}" {SVG_XMLNS}>'
    ]
    for i, (label, value) in enumerate(zip(chart.labels, values, strict=True)):
        y = i * 44 + 8
        parts.append(f'<text x="0" y="{y + 12}" font-size="12" fill="#303234">{escape(label)}</text>')
        w = (value or 0) / maximum * 300
        parts.append(f'<rect x="0" y="{y + 18}" width="{w}" height="13" fill="{escape(chart.series[0].color)}" />')
        caption = "—" if value is None else value_caption(value, 0)
        parts.append(f'<text x="{w + 8}" y="{y + 29}" font-size="12" fill="#196796">{escape(caption)}</text>')
    parts.append("</svg>")
    return "".join(parts)
