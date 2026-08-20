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
    email = render_email(load_document("synthetic_daily"))
    assert "background: #0e1320" in email
    assert "EXAMPLE-DAILY-20300108" in email
    assert "Example Exceptions" in email


def test_email_charts_fall_back_to_mini_tables():
    email = render_email(load_document("synthetic_daily"))
    assert "Value (MWh)" in email
    assert ">2.00</td>" in email or ">2.00<" in email
    assert ">Wed<" in email

    weekly = render_email(load_document("synthetic_weekly"))
    assert "80%" in weekly
    assert "30 h (50%)" in weekly

    monthly = render_email(load_document("synthetic_monthly"))
    assert "3 / 4 samples" in monthly
