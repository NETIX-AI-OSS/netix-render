import pytest
from pydantic import ValidationError

from netix_render.schema import ReportDocument
from tests.support import FIXTURE_NAMES, load_document, load_fixture_json

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_parses_into_report_document(name):
    document = load_document(name)
    assert document.meta.report_id.startswith("NTX-V63-")
    assert document.meta.asset.name == "Villa 63"
    assert document.sections[0].kind == "banner"
    assert document.sections[-1].kind == "footer"


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_round_trips(name):
    document = load_document(name)
    assert ReportDocument.model_validate(document.model_dump()) == document


def test_extra_meta_key_is_rejected():
    payload = load_fixture_json("villa63_daily")
    payload["meta"]["hallucinated"] = "value"
    with pytest.raises(ValidationError, match="hallucinated"):
        ReportDocument.model_validate(payload)


def test_extra_section_key_is_rejected():
    payload = load_fixture_json("villa63_daily")
    payload["sections"][0]["markup"] = "<b>nope</b>"
    with pytest.raises(ValidationError, match="markup"):
        ReportDocument.model_validate(payload)


def test_unknown_section_kind_is_rejected():
    payload = load_fixture_json("villa63_daily")
    payload["sections"].append({"kind": "raw_html", "html": "<script></script>"})
    with pytest.raises(ValidationError, match="raw_html"):
        ReportDocument.model_validate(payload)


def test_accent_gradient_requires_three_hex_stops():
    payload = load_fixture_json("villa63_daily")
    payload["meta"]["accent"]["gradient"] = ["#0e1320", "#173d33"]
    with pytest.raises(ValidationError, match="gradient"):
        ReportDocument.model_validate(payload)

    payload["meta"]["accent"]["gradient"] = ["#0e1320", "#173d33", "not-a-color"]
    with pytest.raises(ValidationError, match="gradient"):
        ReportDocument.model_validate(payload)


def test_banner_level_is_constrained():
    payload = load_fixture_json("villa63_daily")
    payload["sections"][0]["level"] = "purple"
    with pytest.raises(ValidationError, match="level"):
        ReportDocument.model_validate(payload)
