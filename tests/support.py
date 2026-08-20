"""Shared test helpers: fixture loading, snapshot assertions, visible-text extraction for HTML parity."""

import json
import os
from html.parser import HTMLParser
from pathlib import Path

from netix_render.schema import ReportDocument

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SNAPSHOTS_DIR = Path(__file__).resolve().parent / "snapshots"
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"

FIXTURE_NAMES = ("villa63_daily", "villa63_weekly", "villa63_monthly")


def load_fixture_json(name: str) -> dict:
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def load_document(name: str) -> ReportDocument:
    return ReportDocument.model_validate(load_fixture_json(name))


def assert_matches_snapshot(name: str, content: str) -> None:
    """Compares content against the stored snapshot; regenerate all snapshots with UPDATE_SNAPSHOTS=1."""
    path = SNAPSHOTS_DIR / name
    if os.environ.get("UPDATE_SNAPSHOTS") == "1":  # pragma: no cover - regeneration mode
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    assert path.exists(), f"Missing snapshot {path}; run with UPDATE_SNAPSHOTS=1 to create it."
    assert content == path.read_text(encoding="utf-8"), (
        f"Rendered output differs from snapshot {name}; run with UPDATE_SNAPSHOTS=1 to update after reviewing."
    )


def normalize_text(text: str) -> str:
    return " ".join(text.replace("\xa0", " ").split())


class VisibleTextExtractor(HTMLParser):
    SKIP_TAGS = frozenset({"style", "script", "title"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth:
            return
        normalized = normalize_text(data)
        if normalized:
            self.chunks.append(normalized)


def visible_text_chunks(html: str) -> list[str]:
    extractor = VisibleTextExtractor()
    extractor.feed(html)
    return extractor.chunks
