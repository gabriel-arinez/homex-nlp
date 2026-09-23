import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.contracts.item import ItemProposal

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "request_path",
    sorted((ROOT / "examples" / "requests").glob("*.json")),
    ids=lambda path: path.stem,
)
def test_normative_request_and_result_are_strict_and_correlated(request_path: Path) -> None:
    request = ExtractionRequest.model_validate(load(request_path))
    result_path = ROOT / "examples" / "expected" / request_path.name
    result = ExtractionResult.model_validate(load(result_path))

    assert result.request_id == request.request_id
    assert result.text_original == request.text
    if result.item_proposal is not None and result.item_proposal.price is not None:
        assert result.item_proposal.price.currency == request.currency_context


def test_negotiated_total_is_authoritative() -> None:
    result = ExtractionResult.model_validate(
        load(ROOT / "examples" / "expected" / "total-negociado.json")
    )
    assert result.item_proposal is not None
    assert result.item_proposal.price is not None
    assert result.item_proposal.price.line_total == "100.00"
    assert result.item_proposal.price.unit_price_reference == "33.333333"


def test_unit_total_must_equal_quantity_times_unit_price() -> None:
    data = load(ROOT / "examples" / "expected" / "precio-unitario.json")["item_proposal"]
    data["price"]["line_total"] = "299.99"

    with pytest.raises(ValidationError, match="cantidad × unitario"):
        ItemProposal.model_validate(data)


def test_empty_proposal_is_null_instead_of_an_empty_item() -> None:
    with pytest.raises(ValidationError, match="propuesta vacía"):
        ItemProposal.model_validate({})


def test_transport_rejects_numeric_money_and_boolean_quantity() -> None:
    data = load(ROOT / "examples" / "expected" / "precio-unitario.json")["item_proposal"]
    data["price"]["line_total"] = 300.0
    data["quantity"] = True

    with pytest.raises(ValidationError):
        ItemProposal.model_validate(data)


def test_result_rejects_offset_not_matching_original_text() -> None:
    data = load(ROOT / "examples" / "expected" / "conflicto-multiproducto.json")
    data["candidates"][0]["start"] = 2

    with pytest.raises(ValidationError, match="Span no coincide"):
        ExtractionResult.model_validate(data)


def test_missing_quantity_requires_warning_in_result() -> None:
    result = {
        "request_id": "missing-quantity-1",
        "status": "REQUIRES_REVIEW",
        "text_original": "escritorio",
        "item_proposal": {"name": "escritorio"},
        "proposed_item_count": 1,
        "engine": {"mode": "RULES_ONLY", "model_version": None, "rules_version": "r1"},
    }
    with pytest.raises(ValidationError, match="Cantidad ausente requiere advertencia"):
        ExtractionResult.model_validate(result)


def test_unicode_offsets_use_python_code_points_and_exclusive_end() -> None:
    result = {
        "schema_version": "1.0",
        "request_id": "unicode-1",
        "status": "REQUIRES_REVIEW",
        "text_original": "😀 escritorio",
        "item_proposal": {"name": "escritorio", "quantity": 1},
        "proposed_item_count": 1,
        "candidates": [
            {
                "candidate_id": "p-1",
                "label": "PRODUCTO",
                "start": 2,
                "end": 12,
                "text": "escritorio",
                "source": "NER",
                "decision": "ACCEPTED",
            }
        ],
        "warnings": [],
        "engine": {"mode": "HYBRID", "model_version": "m1", "rules_version": "r1"},
    }
    assert ExtractionResult.model_validate(result).candidates[0].text == "escritorio"
