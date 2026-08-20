"""Loads tokens.json once; templates receive the dict as `tokens` so brand values are never hardcoded twice."""

import colorsys
import json
import re
from functools import cache
from pathlib import Path

TOKENS_PATH = Path(__file__).resolve().parent / "tokens.json"

HSL_PATTERN = re.compile(r"^hsl\((?P<h>[\d.]+)[ ,]+(?P<s>[\d.]+)%[ ,]+(?P<l>[\d.]+)%\)$")


@cache
def tokens() -> dict:
    return json.loads(TOKENS_PATH.read_text(encoding="utf-8"))


def hsl_to_hex(value: str) -> str:
    """CSS `hsl(H S% L%)` (or comma form) to lowercase #rrggbb; used to check drift against globals.css."""
    match = HSL_PATTERN.match(value.strip())
    if not match:
        raise ValueError(f"Not an hsl() color: {value!r}")
    hue = float(match.group("h")) / 360.0
    saturation = float(match.group("s")) / 100.0
    lightness = float(match.group("l")) / 100.0
    red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
    return f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"  # noqa: E231
