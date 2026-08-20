"""tokens.json stays in sync with its declared HSL sources and reaches every template through the env."""

import pytest

from netix_render.tokens import hsl_to_hex, tokens

pytestmark = pytest.mark.unit


def _lookup(data: dict, dotted: str):
    node = data
    for part in dotted.split("."):
        node = node[part]
    return node


def test_hex_values_match_declared_hsl_sources():
    data = tokens()
    for dotted, hsl in data["source"]["hsl"].items():
        assert _lookup(data["color"], dotted).lower() == hsl_to_hex(hsl), f"{dotted} drifted from {hsl}"


def test_hsl_to_hex_rejects_garbage():
    with pytest.raises(ValueError):
        hsl_to_hex("#196594")


def test_email_frame_width_is_email_safe():
    assert tokens()["email"]["frame_width"] <= 640
