"""Every registered template: sample validates, renders in all locales, output is email-safe and snapshot-stable."""

import re

import pytest

from netix_render.email.registry import TEMPLATES, render_email_template
from netix_render.email.schema import RTL_LOCALES
from tests.support import assert_matches_snapshot, visible_text_chunks

pytestmark = pytest.mark.unit

EXTERNAL_ASSET_PATTERN = re.compile(r'(?:src|href)="http', re.IGNORECASE)
GMAIL_CLIP_LIMIT = 102 * 1024


@pytest.mark.parametrize("template_id", sorted(TEMPLATES))
def test_sample_renders_and_matches_snapshot(template_id):
    rendered = render_email_template(template_id, TEMPLATES[template_id].sample)
    assert rendered.subject
    assert rendered.text.strip()
    assert_matches_snapshot(f"email_{template_id}.html", rendered.html)


@pytest.mark.parametrize("template_id", sorted(TEMPLATES))
@pytest.mark.parametrize("locale", ["en", "ar", "es"])
def test_renders_in_every_locale(template_id, locale):
    sample = dict(TEMPLATES[template_id].sample)
    sample["meta"] = {**sample.get("meta", {}), "locale": locale}
    rendered = render_email_template(template_id, sample)
    expected_dir = "rtl" if locale in RTL_LOCALES else "ltr"
    assert f'dir="{expected_dir}"' in rendered.html
    assert f'lang="{locale}"' in rendered.html


@pytest.mark.parametrize("template_id", sorted(TEMPLATES))
def test_email_safety_constraints(template_id):
    rendered = render_email_template(template_id, TEMPLATES[template_id].sample)
    assert len(rendered.html.encode()) < GMAIL_CLIP_LIMIT
    assert "<svg" not in rendered.html
    for match in EXTERNAL_ASSET_PATTERN.finditer(rendered.html):
        line = rendered.html[max(0, match.start() - 60) : match.end() + 120]
        assert "example.invalid" in line or "logo" in line, f"Unexpected external asset in {template_id}: {line}"


def test_html_is_escaped():
    sample = dict(TEMPLATES["entity_event"].sample)
    sample["title"] = "<script>alert(1)</script>"
    rendered = render_email_template("entity_event", sample)
    assert "<script>" not in rendered.html
    assert "&lt;script&gt;" in rendered.html


def test_subject_override_wins():
    sample = dict(TEMPLATES["otp_code"].sample)
    sample["meta"] = {**sample["meta"], "subject": "Custom subject"}
    rendered = render_email_template("otp_code", sample)
    assert rendered.subject == "Custom subject"


def test_unknown_template_raises():
    with pytest.raises(KeyError):
        render_email_template("nope", {})


def test_unknown_keys_rejected():
    sample = dict(TEMPLATES["otp_code"].sample)
    sample["fabricated"] = True
    with pytest.raises(ValueError):
        render_email_template("otp_code", sample)


def test_org_logo_replaces_wordmark():
    sample = dict(TEMPLATES["report_ready"].sample)
    sample["meta"] = {**sample["meta"], "org": {"name": "Acme", "logo_url": "https://cdn.example.invalid/logo.png"}}
    rendered = render_email_template("report_ready", sample)
    assert "cdn.example.invalid/logo.png" in rendered.html


def test_text_alternative_contains_payload_facts():
    rendered = render_email_template("report_ready", TEMPLATES["report_ready"].sample)
    assert "attendance_2026-08.xlsx" in rendered.text
    assert "https://example.invalid/download/abc" in rendered.text


def test_visible_text_contains_code():
    rendered = render_email_template("otp_code", TEMPLATES["otp_code"].sample)
    assert "482913" in " ".join(visible_text_chunks(rendered.html))


@pytest.mark.parametrize("template_id", sorted(TEMPLATES))
def test_no_escaped_entities_inside_inlined_styles(template_id):
    rendered = render_email_template(template_id, TEMPLATES[template_id].sample)
    for fragment in re.findall(r'style="[^"]*"', rendered.html):
        assert "&#39;" not in fragment and "&amp;" not in fragment, fragment
    assert "font-family: Inter" in rendered.html
