"""Every registered template: sample validates, renders in all locales, output is email-safe and snapshot-stable."""

import re
from string import Formatter
from typing import get_args

import pytest

from netix_render.email.registry import TEMPLATES, render_email_template
from netix_render.email.schema import RTL_LOCALES, Locale
from netix_render.email.strings import STRINGS, translator
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
@pytest.mark.parametrize("locale", get_args(Locale))
def test_renders_in_every_locale(template_id, locale):
    sample = dict(TEMPLATES[template_id].sample)
    sample["meta"] = {**sample.get("meta", {}), "locale": locale}
    rendered = render_email_template(template_id, sample)
    expected_dir = "rtl" if locale in RTL_LOCALES else "ltr"
    assert f'dir="{expected_dir}"' in rendered.html
    assert f'lang="{locale}"' in rendered.html


@pytest.mark.parametrize(
    ("requested", "locale"),
    [
        ("en-GB", "en"),
        ("ar-AE", "ar"),
        ("fr-CA", "fr"),
        ("es-MX", "es"),
        ("nl-BE", "nl"),
        ("de-AT", "de"),
        (" RU_ru ", "ru"),
    ],
)
def test_email_language_aliases_render_the_canonical_template(requested, locale):
    sample = dict(TEMPLATES["otp_code"].sample)
    sample["meta"] = {**sample["meta"], "locale": requested}
    regional = render_email_template("otp_code", sample)
    sample["meta"]["locale"] = locale
    assert regional == render_email_template("otp_code", sample)


@pytest.mark.parametrize("locale", ["it-IT", 12])
def test_email_language_still_rejects_unsupported_values(locale):
    sample = dict(TEMPLATES["otp_code"].sample)
    sample["meta"] = {**sample["meta"], "locale": locale}
    with pytest.raises(ValueError, match=r"meta.locale"):
        render_email_template("otp_code", sample)


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


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        " \tjava\nscript:alert(1)",
        "VBScript:msgbox(1)",
        "data:text/html,unsafe",
        "file:///private",
    ],
)
def test_email_links_reject_active_and_local_file_schemes(url):
    with pytest.raises(ValueError, match="Unsupported link scheme"):
        render_email_template("report_ready", {"file_name": "example.pdf", "download_url": url})
    sample = {**TEMPLATES["entity_event"].sample, "cta": {"label": "Open", "url": url}}
    with pytest.raises(ValueError, match="Unsupported link scheme"):
        render_email_template("entity_event", sample)


@pytest.mark.parametrize(
    "url", ["https://example.invalid/report", "/reports/one", "#report", "mailto:team@example.invalid"]
)
def test_email_links_preserve_supported_web_and_contact_targets(url):
    sample = {**TEMPLATES["entity_event"].sample, "cta": {"label": "Open", "url": url}}
    assert f'href="{url}"' in render_email_template("entity_event", sample).html


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


def test_arabic_wordmark_preserves_latin_order_in_the_masthead():
    sample = {**TEMPLATES["report_pack"].sample, "meta": {"locale": "ar"}}
    html = render_email_template("report_pack", sample).html

    assert re.search(r'<div class="wordmark"[^>]*dir="ltr"[^>]*>NETIX<span[^>]*>\.AI</span>', html)


def test_arabic_report_pack_protects_file_name_and_size_direction():
    sample = {
        **TEMPLATES["report_pack"].sample,
        "meta": {"locale": "ar"},
        "files": [{"name": "AHU-17.pdf", "size_label": "41,3 KB"}],
    }
    rendered = render_email_template("report_pack", sample)
    for surface in (rendered.html, rendered.text):
        assert "\u2068AHU-17.pdf\u2069" in surface
        assert "\u206841,3 KB\u2069" in surface


def test_visible_text_contains_code():
    rendered = render_email_template("otp_code", TEMPLATES["otp_code"].sample)
    assert "482913" in " ".join(visible_text_chunks(rendered.html))


@pytest.mark.parametrize("template_id", sorted(TEMPLATES))
def test_no_escaped_entities_inside_inlined_styles(template_id):
    rendered = render_email_template(template_id, TEMPLATES[template_id].sample)
    for fragment in re.findall(r'style="[^"]*"', rendered.html):
        assert "&#39;" not in fragment and "&amp;" not in fragment, fragment
    assert "font-family: Inter" in rendered.html


def test_status_digest_rejects_counts_that_do_not_match_columns():
    sample = dict(TEMPLATES["status_digest"].sample)
    sample["totals"] = [1, 2]
    with pytest.raises(ValueError):
        render_email_template("status_digest", sample)


def test_status_digest_text_lists_every_group_row_and_total():
    rendered = render_email_template("status_digest", TEMPLATES["status_digest"].sample)
    assert "Acme Facilities: Went offline 2, Degraded 1, Back online 2, Offline now 9" in rendered.text
    assert "  - Tower B: Went offline 2, Degraded 0, Back online 1, Offline now 6" in rendered.text
    assert "Total: Went offline 2" in rendered.text
    assert "iot-status-2026-10-15-1915.xlsx" in rendered.text


def test_every_supported_locale_has_complete_chrome_and_matching_placeholders():
    assert set(STRINGS) == set(get_args(Locale))
    english = STRINGS["en"]
    formatter = Formatter()
    for locale, strings in STRINGS.items():
        assert strings.keys() == english.keys(), locale
        for key, value in strings.items():
            assert value.strip(), (locale, key)
            expected = sorted(field for _, field, _, _ in formatter.parse(english[key]) if field is not None)
            actual = sorted(field for _, field, _, _ in formatter.parse(value) if field is not None)
            assert actual == expected, (locale, key)


@pytest.mark.parametrize("locale", ["fr", "nl", "de"])
def test_new_locale_renders_translated_subject_expiry_and_footer(locale):
    rendered = render_email_template("otp_code", {"meta": {"locale": locale}, "code": "482913", "expires_minutes": 10})
    t = translator(locale)
    assert rendered.subject == f"{t('verification_code')}, Netix.AI"
    assert t("code_expires", minutes=10) in rendered.text
    assert t("code_ignore") in rendered.text
    assert t("automated_note") in rendered.html
    assert STRINGS["en"]["verification_code"] not in rendered.text


def _offline_report(**overrides):
    return {**TEMPLATES["offline_daily_report"].sample, **overrides}


def test_offline_daily_report_flat_context_sets_locale_and_org_name():
    rendered = render_email_template("offline_daily_report", _offline_report(language="ar"))
    assert 'dir="rtl"' in rendered.html and 'lang="ar"' in rendered.html
    assert "Acme Facilities" in " ".join(visible_text_chunks(rendered.html))
    assert translator("ar")("offline_now") in rendered.text
    assert rendered.subject == "Daily offline report, 17 Nov 2026"


def test_offline_daily_report_explicit_meta_wins_over_flat_keys():
    sample = _offline_report(language="ar", meta={"locale": "fr", "org": {"name": "Override"}})
    rendered = render_email_template("offline_daily_report", sample)
    assert 'lang="fr"' in rendered.html
    assert "Override" in rendered.html and "Acme Facilities" not in rendered.html


def test_offline_daily_report_lists_offline_items_more_line_and_gateways():
    rendered = render_email_template("offline_daily_report", TEMPLATES["offline_daily_report"].sample)
    visible = " ".join(visible_text_chunks(rendered.html))
    for fact in ("AHU-3", "Chiller CH-01", "2 d 0 h", "Plant 2", "Gateway impact", "+2 more offline", "96.8%"):
        assert fact in visible, fact
    assert 'href="https://example.invalid/connectivity"' in rendered.html
    assert "band-crit" in rendered.html
    assert "- AHU-3 (Asset), Building: Tower B, Since: 16 Nov 2026 22:41, Duration: 9 h 19 min" in rendered.text
    assert "+2 more offline, not listed here." in rendered.text
    assert "- GW-Tower-B-02, Since: 16 Nov 2026 22:40, Assets affected: 3" in rendered.text
    assert "Open dashboard: https://example.invalid/connectivity" in rendered.text


def test_offline_daily_report_hides_optional_sections():
    sample = _offline_report(offline_more=0, gateway_impact=[], attachment_note=None)
    rendered = render_email_template("offline_daily_report", sample)
    assert "more offline" not in rendered.html and "more offline" not in rendered.text
    assert "Gateway impact" not in rendered.html and "Gateway impact" not in rendered.text
    assert "attached spreadsheet" not in rendered.text


def test_offline_daily_report_all_online_state():
    sample = _offline_report(
        totals={"monitored": 12, "online": 12, "degraded": 0, "offline": 0},
        offline_items=[],
        offline_more=0,
        gateway_impact=[],
        availability_pct_24h=100.0,
    )
    rendered = render_email_template("offline_daily_report", sample)
    assert "All assets and gateways are online." in rendered.html
    assert "All assets and gateways are online." in rendered.text
    assert "band-ok" in rendered.html
    assert "Offline now" not in rendered.html and "Offline now" not in rendered.text
    assert "100%" in rendered.text


def test_offline_daily_report_degraded_only_says_nothing_offline():
    sample = _offline_report(
        totals={"monitored": 12, "online": 11, "degraded": 1, "offline": 0}, offline_items=[], offline_more=0
    )
    rendered = render_email_template("offline_daily_report", sample)
    assert "band-warn" in rendered.html
    assert "Nothing is offline right now." in rendered.html
    assert "All assets and gateways are online." not in rendered.html


@pytest.mark.parametrize(
    ("locale", "pct", "expected"), [("en", 96.84, "96.8%"), ("de", 96.84, "96,8 %"), ("en", None, "Availability -")]
)
def test_offline_daily_report_availability_format(locale, pct, expected):
    rendered = render_email_template("offline_daily_report", _offline_report(language=locale, availability_pct_24h=pct))
    assert expected in rendered.text


def test_offline_daily_report_unknown_subject_kind_is_shown_as_given():
    items = [
        {"display_name": "Meter M-7", "subject_kind": "Energy meter", "building": None, "since": "x", "duration": "y"}
    ]
    rendered = render_email_template("offline_daily_report", _offline_report(offline_items=items))
    assert "- Meter M-7 (Energy meter), Building: -" in rendered.text


def test_offline_daily_report_rejects_unsafe_dashboard_url_and_unknown_keys():
    with pytest.raises(ValueError, match="Unsupported link scheme"):
        render_email_template("offline_daily_report", _offline_report(dashboard_url="javascript:alert(1)"))
    with pytest.raises(ValueError):
        render_email_template("offline_daily_report", _offline_report(fabricated=True))
    with pytest.raises(ValueError):
        render_email_template("offline_daily_report", _offline_report(language="xx"))
