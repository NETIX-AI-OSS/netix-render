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
