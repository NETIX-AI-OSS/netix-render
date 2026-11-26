"""Every registered template: sample validates, renders in all locales, output is email-safe and snapshot-stable."""

import re
from string import Formatter
from typing import get_args

import pytest

from netix_render.email.registry import TEMPLATES, render_email_template
from netix_render.email.schema import RTL_LOCALES, Locale, OfflineMonthlyReportEmail
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


# The exact context a 0.1.5 data-service sender produces; it must keep validating and rendering.
LEGACY_DAILY_CONTEXT = {
    "organization_name": "Acme Facilities",
    "report_name": "Daily offline report",
    "report_date": "17 Nov 2026",
    "timezone": "Asia/Dubai",
    "totals": {"monitored": 128, "online": 121, "degraded": 2, "offline": 5},
    "availability_pct_24h": 96.84,
    "new_24h": 3,
    "recovered_24h": 4,
    "offline_items": [
        {
            "display_name": "AHU-3",
            "subject_kind": "asset",
            "building": "Tower B",
            "since": "16 Nov 2026 22:41",
            "duration": "9 h 19 min",
        }
    ],
    "offline_more": 2,
    "by_building": [{"building": "Tower B", "monitored": 74, "offline": 4, "degraded": 1}],
    "gateway_impact": [{"display_name": "GW-Tower-B-02", "since": "16 Nov 2026 22:40", "affected_assets": 3}],
    "dashboard_url": "https://example.invalid/connectivity",
    "attachment_note": "The full list is in the attached spreadsheet.",
    "language": "en",
}


def test_offline_daily_report_flat_context_sets_locale_and_org_name():
    rendered = render_email_template("offline_daily_report", _offline_report(language="ar", subject_line=None))
    assert 'dir="rtl"' in rendered.html and 'lang="ar"' in rendered.html
    assert "Acme Facilities" in " ".join(visible_text_chunks(rendered.html))
    assert translator("ar")("offline_now") in rendered.text
    assert rendered.subject == "Daily offline report, 17 Nov 2026"


def test_offline_daily_report_explicit_meta_wins_over_flat_keys():
    sample = _offline_report(language="ar", meta={"locale": "fr", "org": {"name": "Override"}})
    rendered = render_email_template("offline_daily_report", sample)
    assert 'lang="fr"' in rendered.html
    assert "Override" in rendered.html and "Acme Facilities" not in rendered.html


def test_offline_daily_report_subject_line_wins_over_default_and_meta_subject_wins_over_both():
    rendered = render_email_template("offline_daily_report", _offline_report())
    assert rendered.subject == "3 new offline, 4 back online, 96.8% available, Tue 17 Nov"
    assert f"<title>{rendered.subject}</title>" in rendered.html
    sample = _offline_report(meta={"subject": "Override subject"})
    assert render_email_template("offline_daily_report", sample).subject == "Override subject"


def test_offline_daily_report_legacy_015_context_still_validates_and_renders():
    rendered = render_email_template("offline_daily_report", LEGACY_DAILY_CONTEXT)
    assert rendered.subject == "Daily offline report, 17 Nov 2026"
    # Without `changes`, the movement row falls back to new_24h / recovered_24h and offline now as still down.
    assert "What changed since yesterday: Went offline 3, Back online 4, Still down 5" in rendered.text
    assert "- AHU-3 (Asset), Building: Tower B, Since: 16 Nov 2026 22:41, Duration: 9 h 19 min" in rendered.text
    assert "Incidents" not in rendered.text and "Not included" not in rendered.text
    assert "than yesterday" not in rendered.html
    assert 'href="https://example.invalid/connectivity"' in rendered.html
    assert "cx-link" not in rendered.html


def test_offline_daily_report_leads_with_changes_then_incidents_then_offline_list():
    rendered = render_email_template("offline_daily_report", TEMPLATES["offline_daily_report"].sample)
    visible = " ".join(visible_text_chunks(rendered.html))
    order = ["What changed since yesterday", "Right now", "Incidents", "Offline now", "By building", "Gateway impact"]
    positions = [visible.index(heading) for heading in order]
    assert positions == sorted(positions)
    for fact in ("2 more than yesterday", "Still down", "-0.4 points", "96.8%", "+2 more offline"):
        assert fact in visible, fact
    assert "What changed since yesterday: Went offline 3 (2 more than yesterday), Back online 4, Still down 2" in (
        rendered.text
    )
    assert "Availability, 24 h 96.8% (-0.4 points)" in rendered.text
    assert "Not included in this report: 1 snoozed, 2 in maintenance." in rendered.text


def test_offline_daily_report_incidents_show_unreachable_assets_and_deep_links():
    rendered = render_email_template("offline_daily_report", TEMPLATES["offline_daily_report"].sample)
    visible = " ".join(visible_text_chunks(rendered.html))
    assert "14 assets unreachable" in visible
    assert "2 devices affected" in visible
    assert 'href="https://example.invalid/connectivity/offline?outage=5012"' in rendered.html
    assert "- [Gateway] GW-Tower-B-02 offline, 14 assets unreachable, Since: 16 Nov 2026 22:40" in rendered.text
    assert "- [Device] Meter M-7, Since: 17 Nov 2026 06:12, Duration: 1 h 48 min" in rendered.text
    assert "  https://example.invalid/connectivity/offline?outage=5020" in rendered.text


@pytest.mark.parametrize(
    ("kind", "affected", "expected"),
    [("gateway", 1, "1 asset unreachable"), ("building", 3, "3 devices affected"), ("single", 2, "2 devices affected")],
)
def test_offline_daily_report_incident_affected_wording(kind, affected, expected):
    incident = {"title": "Example", "kind": kind, "affected": affected}
    rendered = render_email_template("offline_daily_report", _offline_report(incidents=[incident]))
    assert expected in rendered.text
    assert expected in " ".join(visible_text_chunks(rendered.html))


def test_offline_daily_report_single_device_incident_has_no_affected_count():
    incident = {"title": "Meter M-9", "kind": "single", "affected": 1}
    rendered = render_email_template("offline_daily_report", _offline_report(incidents=[incident]))
    assert "- [Device] Meter M-9\n" in rendered.text
    assert "device affected" not in rendered.html


def test_offline_daily_report_offline_items_link_to_the_outage():
    rendered = render_email_template("offline_daily_report", TEMPLATES["offline_daily_report"].sample)
    assert 'href="https://example.invalid/connectivity/offline?outage=4999"' in rendered.html
    assert "- Pump P-4 (Asset), Building: Plant 2, Since: 16 Nov 2026 13:10, Duration: 18 h 50 min\n  https://" in (
        rendered.text
    )
    assert "- GW-Tower-B-02, Since: 16 Nov 2026 22:40, Assets affected: 14" in rendered.text
    assert "Open dashboard: https://example.invalid/connectivity" in rendered.text


def test_offline_daily_report_colour_rule_pairs_icon_word_and_colour():
    rendered = render_email_template("offline_daily_report", TEMPLATES["offline_daily_report"].sample)
    html = rendered.html
    # Offline: red text and soft band with the octagon; degraded: amber triangle; online: neutral hollow circle.
    assert "cx-band-crit" in html and "background: #fdecec" in html and "color: #b91c1c" in html
    assert "\U0001f6d1" in html and "color: #d97706" in html and "▲" in html
    assert "○" in html and "color: #64748b" in html
    # The old status palette no longer tints connectivity states.
    assert "#d72828" not in html and "#b97600" not in html
    for word in ("Offline", "Degraded", "Online"):
        assert word in " ".join(visible_text_chunks(html))


@pytest.mark.parametrize(
    ("totals", "band"),
    [
        ({"monitored": 12, "online": 11, "degraded": 0, "offline": 1}, "cx-band-crit"),
        ({"monitored": 12, "online": 11, "degraded": 1, "offline": 0}, "cx-band-warn"),
        ({"monitored": 12, "online": 12, "degraded": 0, "offline": 0}, "cx-band-ok"),
    ],
)
def test_offline_daily_report_band_follows_worst_status(totals, band):
    rendered = render_email_template("offline_daily_report", _offline_report(totals=totals))
    assert band in rendered.html


def _all_clear(**overrides):
    defaults = dict(
        all_clear=True,
        subject_line="All 128 devices reporting, 100% available, Tue 17 Nov",
        totals={"monitored": 128, "online": 128, "degraded": 0, "offline": 0},
        availability_pct_24h=100.0,
        availability_delta="+0.2 points",
        changes={"new_24h": 0, "recovered_24h": 2, "still_down": 0, "new_vs_yesterday": -1},
        incidents=[],
        offline_items=[],
        offline_more=0,
        by_building=[],
        gateway_impact=[],
        snoozed_count=0,
        maintenance_count=0,
    )
    return _offline_report(**{**defaults, **overrides})


def test_offline_daily_report_all_clear_is_a_short_green_email():
    rendered = render_email_template("offline_daily_report", _all_clear())
    visible = " ".join(visible_text_chunks(rendered.html))
    assert rendered.subject == "All 128 devices reporting, 100% available, Tue 17 Nov"
    assert "cx-band-ok" in rendered.html and "✓" in rendered.html
    assert "Everything is reporting" in visible and "Everything is reporting" in rendered.text
    assert "Every monitored asset and gateway is online and sending data." in rendered.text
    for absent in ("Offline now", "Incidents", "By building", "Gateway impact", "What changed since yesterday"):
        assert absent not in visible and absent not in rendered.text, absent
    assert "Monitored 128, Availability, 24 h 100% (+0.2 points), Back online 2" in rendered.text
    assert 'href="https://example.invalid/connectivity"' in rendered.html
    assert len(rendered.html.encode()) < len(render_email_template("offline_daily_report", _offline_report()).html)


def test_offline_daily_report_all_clear_mentions_excluded_snoozed_and_maintenance():
    rendered = render_email_template("offline_daily_report", _all_clear(maintenance_count=3))
    assert "Not included in this report: 3 in maintenance." in rendered.text


def test_offline_daily_report_hides_optional_sections():
    sample = _offline_report(
        offline_more=0, gateway_impact=[], attachment_note=None, incidents=[], snoozed_count=0, maintenance_count=0
    )
    rendered = render_email_template("offline_daily_report", sample)
    assert "more offline" not in rendered.html and "more offline" not in rendered.text
    assert "Gateway impact" not in rendered.html and "Gateway impact" not in rendered.text
    assert "Incidents" not in rendered.html and "Incidents" not in rendered.text
    assert "Not included" not in rendered.html and "Not included" not in rendered.text
    assert "attached spreadsheet" not in rendered.text


def test_offline_daily_report_all_online_state():
    sample = _offline_report(
        totals={"monitored": 12, "online": 12, "degraded": 0, "offline": 0},
        offline_items=[],
        offline_more=0,
        gateway_impact=[],
        incidents=[],
        availability_pct_24h=100.0,
    )
    rendered = render_email_template("offline_daily_report", sample)
    assert "All assets and gateways are online." in rendered.html
    assert "All assets and gateways are online." in rendered.text
    assert "cx-band-ok" in rendered.html
    assert "Offline now" not in rendered.html and "Offline now" not in rendered.text
    assert "100%" in rendered.text


def test_offline_daily_report_degraded_only_says_nothing_offline():
    sample = _offline_report(
        totals={"monitored": 12, "online": 11, "degraded": 1, "offline": 0}, offline_items=[], offline_more=0
    )
    rendered = render_email_template("offline_daily_report", sample)
    assert "cx-band-warn" in rendered.html
    assert "Nothing is offline right now." in rendered.html
    assert "All assets and gateways are online." not in rendered.html


@pytest.mark.parametrize(
    ("vs", "expected"), [(2, "2 more than yesterday"), (-3, "3 fewer than yesterday"), (0, "Same as yesterday")]
)
def test_offline_daily_report_new_vs_yesterday_wording(vs, expected):
    changes = {"new_24h": 3, "recovered_24h": 4, "still_down": 2, "new_vs_yesterday": vs}
    rendered = render_email_template("offline_daily_report", _offline_report(changes=changes))
    assert expected in rendered.text and expected in " ".join(visible_text_chunks(rendered.html))


@pytest.mark.parametrize(
    ("locale", "pct", "expected"),
    [("en", 96.84, "96.8%"), ("de", 96.84, "96,8 %"), ("en", None, "Availability, 24 h - (")],
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


@pytest.mark.parametrize(
    "overrides",
    [
        {"incidents": [{"title": "x", "kind": "gateway", "link": "javascript:alert(1)"}]},
        {"offline_items": [{"display_name": "x", "link": "data:text/html,unsafe"}]},
    ],
)
def test_offline_daily_report_rejects_unsafe_deep_links(overrides):
    with pytest.raises(ValueError, match="Unsupported link scheme"):
        render_email_template("offline_daily_report", _offline_report(**overrides))


@pytest.mark.parametrize(
    "overrides",
    [
        {"incidents": [{"title": "x", "kind": "outage"}]},
        {"incidents": [{"title": "x", "kind": "single", "status": "offline"}]},
        {"incidents": [{"title": f"x{index}", "kind": "single"} for index in range(21)]},
        {"changes": {"new_24h": 1, "recovered_24h": 0, "still_down": 0, "fabricated": 1}},
        {"changes": {"new_24h": -1}},
        {"snoozed_count": -1},
    ],
)
def test_offline_daily_report_rejects_invalid_v2_keys(overrides):
    with pytest.raises(ValueError):
        render_email_template("offline_daily_report", _offline_report(**overrides))


def _monthly(**overrides):
    return {**TEMPLATES["offline_monthly_report"].sample, **overrides}


def test_offline_monthly_report_renders_header_kpis_buildings_and_devices():
    rendered = render_email_template("offline_monthly_report", TEMPLATES["offline_monthly_report"].sample)
    visible = " ".join(visible_text_chunks(rendered.html))
    assert rendered.subject == "Monthly availability report, October 2026"
    for fact in (
        "Acme Facilities",
        "October 2026. Time zone: Asia/Dubai",
        "128",
        "99.1%",
        "Target 99%",
        "37",
        "6 d 4 h",
        "Availability met the 99% target.",
        "Availability by building",
        "Most offline: Chiller CH-01",
        "Devices with the most offline time",
        "19 h 40 min",
        "Daily availability per device is in the attached spreadsheet.",
    ):
        assert fact in visible, fact
    assert 'href="https://example.invalid/connectivity/history"' in rendered.html
    assert (
        "- Plant 2: Availability 97.4% (Below target), Outages 21, Offline time 4 d 2 h, Most offline: Chiller CH-01"
        in rendered.text
    )
    assert "- Harbour Office: Availability 99.9%, Outages 2, Offline time 4 min\n" in rendered.text
    assert "- GW-Tower-B-02, Building: Tower B, Outages 3, Offline time 19 h 40 min" in rendered.text
    assert "Open dashboard: https://example.invalid/connectivity/history" in rendered.text


def test_offline_monthly_report_bars_are_zoomed_email_safe_tables_with_a_target_marker():
    rendered = render_email_template("offline_monthly_report", TEMPLATES["offline_monthly_report"].sample)
    # Scale 90..100: Plant 2 (97.48, below target) amber 74 %, Tower B (99.41) neutral 94 %; target 99 sits at 90 %.
    assert '<td width="74%" height="6" bgcolor="#d97706"' in rendered.html
    assert '<td width="90%" height="6" bgcolor="#94a3b8"' in rendered.html
    assert (
        '<td width="2" height="6" bgcolor="#2d2e2f"></td><td width="4%" height="6" bgcolor="#94a3b8"' in rendered.html
    )
    assert 'bgcolor="#e7ecf1"' in rendered.html  # the neutral lane behind every bar
    assert "<svg" not in rendered.html and "<img" not in rendered.html
    visible = " ".join(visible_text_chunks(rendered.html))
    assert "Bars start at 90%. The dark line marks the target." in visible
    assert visible.count("Bars start at") == 1


@pytest.mark.parametrize(("lowest", "floor"), [(97.48, 90), (90.5, 89), (88.2, 87), (0.4, 0), (100, 90)])
def test_offline_monthly_report_bar_floor(lowest, floor):
    sample = _monthly(buildings=[{"building": "A", "availability": 99.5}, {"building": "B", "availability": lowest}])
    assert OfflineMonthlyReportEmail.model_validate(sample).bar_floor == floor


@pytest.mark.parametrize(
    ("availability", "target", "cells"),
    [
        (97.48, 99.0, [("fill", 74), ("lane", 16), ("marker", 0), ("lane", 10)]),
        (99.41, 99.0, [("fill", 90), ("marker", 0), ("fill", 4), ("lane", 6)]),
        (100, 99.0, [("fill", 90), ("marker", 0), ("fill", 10)]),
        (90, 99.0, [("lane", 90), ("marker", 0), ("lane", 10)]),
        (99.99, None, [("fill", 99), ("lane", 1)]),
        (95.0, 80.0, [("fill", 50), ("lane", 50)]),  # target below the scale: no marker
    ],
)
def test_offline_monthly_report_bar_cells(availability, target, cells):
    email = OfflineMonthlyReportEmail.model_validate(_monthly(availability_target=target))
    assert email.bar_floor == 90
    assert email.bar_cells(availability) == cells
    assert sum(width for kind, width in cells if kind != "marker") == 100


def test_offline_monthly_report_without_target_has_no_marker_note():
    rendered = render_email_template("offline_monthly_report", _monthly(availability_target=None))
    assert "Bars start at 90%." in rendered.html and "dark line" not in rendered.html
    assert 'bgcolor="#2d2e2f"' not in rendered.html


@pytest.mark.parametrize("availability", [0, 100])
def test_offline_monthly_report_bar_keeps_its_height_at_the_extremes(availability):
    sample = _monthly(buildings=[{"building": "B", "availability": availability}], availability_target=None)
    html = render_email_template("offline_monthly_report", sample).html
    assert 'height="6"' in html


def test_offline_monthly_report_flags_buildings_below_target_with_icon_and_word():
    rendered = render_email_template("offline_monthly_report", TEMPLATES["offline_monthly_report"].sample)
    visible = " ".join(visible_text_chunks(rendered.html))
    assert visible.count("Below target") == 1
    assert "▲" in rendered.html


def test_offline_monthly_report_target_missed_and_floor_formatting():
    totals = {"monitored": 10, "availability_pct": 98.96, "outages": 4, "total_offline": "7 h"}
    rendered = render_email_template("offline_monthly_report", _monthly(totals=totals))
    # 98.96 must not round up to the 99% target it missed.
    assert "Availability 98.9% (Target 99%)" in rendered.text
    assert "Availability was below the 99% target." in rendered.text
    assert "Availability was below the 99% target." in " ".join(visible_text_chunks(rendered.html))


def test_offline_monthly_report_without_target_flags_nothing():
    rendered = render_email_template("offline_monthly_report", _monthly(availability_target=None))
    for absent in ("Target", "Below target", "target."):
        assert absent not in rendered.text and absent not in rendered.html, absent
    assert 'bgcolor="#d97706"' not in rendered.html


def test_offline_monthly_report_empty_period():
    sample = _monthly(
        totals={"monitored": 0, "availability_pct": None, "outages": 0, "total_offline": None},
        buildings=[],
        worst_devices=[],
        attachment_note=None,
    )
    rendered = render_email_template("offline_monthly_report", sample)
    assert "No buildings had monitored devices in this period." in rendered.text
    assert "No buildings had monitored devices in this period." in rendered.html
    assert "Devices with the most offline time" not in rendered.html
    assert "met the" not in rendered.text and "below the" not in rendered.text
    assert "Availability - (Target 99%)" in rendered.text


def test_offline_monthly_report_flat_context_rtl_and_meta_override():
    rendered = render_email_template("offline_monthly_report", _monthly(language="ar"))
    assert 'dir="rtl"' in rendered.html and 'lang="ar"' in rendered.html
    assert translator("ar")("availability_by_building") in rendered.text
    assert "text-align: left" in rendered.html
    rendered = render_email_template("offline_monthly_report", _monthly(meta={"locale": "de", "subject": "Custom"}))
    assert 'lang="de"' in rendered.html and rendered.subject == "Custom"
    assert "99,1 %" in rendered.text


@pytest.mark.parametrize(
    "overrides",
    [
        {"fabricated": True},
        {"language": "xx"},
        {"dashboard_url": "javascript:alert(1)"},
        {"availability_target": 101},
        {"totals": {"monitored": 1, "availability_pct": -1}},
        {"totals": {"monitored": 1, "fabricated": 1}},
        {"buildings": [{"building": "B", "availability": 100.5}]},
        {"buildings": [{"building": "B", "status": "ok"}]},
        {"buildings": [{"building": f"B{index}"} for index in range(101)]},
        {"worst_devices": [{"display_name": f"D{index}"} for index in range(21)]},
        {"worst_devices": [{"display_name": "D", "outages": -1}]},
    ],
)
def test_offline_monthly_report_rejects_invalid_context(overrides):
    with pytest.raises(ValueError):
        render_email_template("offline_monthly_report", _monthly(**overrides))


def test_offline_monthly_report_largest_allowed_payload_stays_under_gmail_clip():
    buildings = [
        {
            "building": f"Building {index:03d} North Wing",
            "availability": 90 + index / 10,
            "outages": index,
            "total_offline": "3 d 22 h",
            "worst_device": f"Air handling unit AHU-{index:03d}",
        }
        for index in range(100)
    ]
    devices = [
        {"display_name": f"Device {index}", "building": "Building 001", "outages": 9, "total_offline": "2 d"}
        for index in range(20)
    ]
    rendered = render_email_template("offline_monthly_report", _monthly(buildings=buildings, worst_devices=devices))
    assert len(rendered.html.encode()) < GMAIL_CLIP_LIMIT


def test_offline_daily_report_largest_allowed_incident_list_stays_under_gmail_clip():
    incidents = [
        {
            "title": f"Gateway GW-{index:02d} offline",
            "kind": "gateway",
            "since": "16 Nov 2026 22:40",
            "duration": "9 h 20 min",
            "affected": 14,
            "link": f"https://example.invalid/connectivity/offline?outage={index}",
        }
        for index in range(20)
    ]
    items = [
        {**TEMPLATES["offline_daily_report"].sample["offline_items"][0], "display_name": f"GW-{i}"} for i in range(50)
    ]
    rendered = render_email_template("offline_daily_report", _offline_report(incidents=incidents, offline_items=items))
    assert len(rendered.html.encode()) < GMAIL_CLIP_LIMIT
