import pytest

from netix_render.renderer import render_email
from tests.support import FIXTURE_NAMES, assert_matches_snapshot, load_document

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_email_variant_is_email_safe(name):
    email = render_email(load_document(name))
    assert "<svg" not in email
    assert "<style" not in email
    assert "display: flex" not in email
    assert 'style="' in email


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_email_variant_matches_snapshot(name):
    assert_matches_snapshot(f"{name}_email.html", render_email(load_document(name)))


def test_email_styles_are_inlined_per_element():
    email = render_email(load_document("villa63_daily"))
    assert "background: #0e1320" in email
    assert "NTX-V63-DLY-260611" in email
    assert "Overnight Exceptions (22:00–06:00)" in email


def test_email_charts_fall_back_to_mini_tables():
    email = render_email(load_document("villa63_daily"))
    assert "Value (MWh)" in email
    assert ">1.92</td>" in email or ">1.92<" in email
    assert ">Wed<" in email

    weekly = render_email(load_document("villa63_weekly"))
    assert "99.1%" in weekly
    assert "81 h (48%)" in weekly

    monthly = render_email(load_document("villa63_monthly"))
    assert "98.2% in-band avg" in monthly
