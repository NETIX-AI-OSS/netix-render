import pytest

from netix_render.charts import hbar_svg, ring_svg, sparkline_svg
from netix_render.schema import HBarRow, RingItem, TrendPoint

pytestmark = pytest.mark.unit

ENERGY_SERIES = [
    TrendPoint(label="Thu", value=2.0),
    TrendPoint(label="Fri", value=3.0),
    TrendPoint(label="Sat", value=4.0),
    TrendPoint(label="Sun", value=5.0),
    TrendPoint(label="Mon", value=6.0),
    TrendPoint(label="Tue", value=7.0),
    TrendPoint(label="Wed", value=8.0),
]


def test_sparkline_draws_a_rounded_bar_per_point():
    svg = sparkline_svg(ENERGY_SERIES, "MWh")
    assert svg.startswith('<svg class="chart" width="100%" viewBox="0 0 330 126"')
    assert svg.count("<rect") == 7
    assert svg.count('rx="3"') == 7
    for point in ENERGY_SERIES:
        assert f">{point.label}</text>" in svg
        assert f">{point.value:.2f}</text>" in svg


def test_sparkline_highlights_the_last_bar():
    svg = sparkline_svg(ENERGY_SERIES, "MWh")
    rects = [chunk for chunk in svg.split("<rect")[1:]]
    assert all('fill="#2e5bd7" opacity="0.55"' in rect for rect in rects[:-1])
    assert 'fill="#dd4257" opacity="1"' in rects[-1]


def test_sparkline_without_highlight_keeps_uniform_bars():
    svg = sparkline_svg(ENERGY_SERIES, "MWh", highlight_last=False)
    assert svg.count('opacity="0.55"') == 7
    assert "#dd4257" not in svg


def test_sparkline_scales_bars_against_the_series_max():
    svg = sparkline_svg(ENERGY_SERIES, "MWh")
    assert 'height="87"' in svg
    assert 'height="22"' in svg


def test_sparkline_renders_null_values_as_gap_with_dash_caption():
    series = [TrendPoint(label="Mon", value=1.0), TrendPoint(label="Tue"), TrendPoint(label="Wed", value=2.0)]
    svg = sparkline_svg(series, "MWh")
    assert svg.count("<rect") == 2
    assert ">—</text>" in svg
    assert ">Tue</text>" in svg


def test_sparkline_handles_all_null_and_single_point_series():
    svg = sparkline_svg([TrendPoint(label="Mon"), TrendPoint(label="Tue")], "MWh")
    assert svg.count("<rect") == 0
    assert svg.count(">—</text>") == 2

    svg = sparkline_svg([TrendPoint(label="Mon", value=3.0)], "MWh")
    assert svg.count("<rect") == 1


def test_sparkline_wide_layout_and_decimals():
    svg = sparkline_svg(ENERGY_SERIES[:6], "MWh", width=640, height=136, decimals=1)
    assert 'viewBox="0 0 640 136"' in svg
    assert 'width="62"' in svg
    assert ">2.0</text>" in svg


def test_sparkline_escapes_labels():
    svg = sparkline_svg([TrendPoint(label="<b>Mon</b>", value=1.0)], "MWh")
    assert "<b>" not in svg
    assert "&lt;b&gt;Mon&lt;/b&gt;" in svg


def test_hbar_scales_against_explicit_max_and_colours_by_status():
    rows = [
        HBarRow(label="Example zone A", value=80, display="80%", status="ok"),
        HBarRow(label="Example zone B", value=60, display="60% ▼", status="warn"),
    ]
    svg = hbar_svg(rows, scale_max=100)
    assert 'viewBox="0 0 640 52"' in svg
    assert 'width="336" height="17" rx="4" fill="#16a571"' in svg
    assert 'width="252" height="17" rx="4" fill="#e0a512"' in svg
    assert ">80%</text>" in svg
    assert ">60% ▼</text>" in svg


def test_hbar_defaults_to_row_maximum():
    rows = [
        HBarRow(label="Example pump A", value=30, display="30 h (50%)", status="warn"),
        HBarRow(label="Example pump B", value=20, display="20 h (33%)"),
        HBarRow(label="Example pump C", value=10, display="10 h (17%)"),
    ]
    svg = hbar_svg(rows)
    assert 'width="420" height="17" rx="4" fill="#e0a512"' in svg
    assert 'width="280" height="17" rx="4" fill="#2e5bd7"' in svg
    assert 'width="140" height="17" rx="4" fill="#2e5bd7"' in svg


def test_hbar_with_zero_maximum_draws_empty_bars():
    svg = hbar_svg([HBarRow(label="X", value=0, display="0")])
    assert 'width="0" height="17"' in svg


def test_ring_dash_matches_percentage():
    svg = ring_svg(
        RingItem(pct=75, value_label="75%", label="Comfort", sublabel="3 of 4 synthetic sensors", status="ok")
    )
    assert 'stroke-dasharray="160 214"' in svg
    assert 'stroke="#16a571"' in svg
    assert ">75%</text>" in svg
    assert ">Comfort</text>" in svg
    assert ">3 of 4 synthetic sensors</text>" in svg

    full = ring_svg(RingItem(pct=100, value_label="100%", label="Safety", sublabel="LPG", status="info"))
    assert 'stroke-dasharray="214 214"' in full
    assert 'stroke="#2e5bd7"' in full
