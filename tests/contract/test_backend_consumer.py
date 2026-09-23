"""Contrato mínimo que F08.0 del backend puede asumir de homex-nlp 0.1.x."""

import homex_nlp
from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine


def test_backend_consumer_contract_v1() -> None:
    request = ExtractionRequest(
        request_id="backend-contract-001",
        text="tres muebles, total 100",
        currency_context="BOB",
    )

    result = RulesEngine().extract(request)

    assert isinstance(result, ExtractionResult)
    assert homex_nlp.__version__ == "0.1.0"
    assert result.schema_version == "1.0"
    assert result.status == "REQUIRES_REVIEW"
    assert result.engine.mode == "RULES_ONLY"
    assert result.item_proposal is not None
    assert result.item_proposal.quantity == 3
    assert result.item_proposal.price is not None
    assert result.item_proposal.price.mode == "TOTAL_NEGOCIADO"
    assert result.item_proposal.price.line_total == "100.00"


def test_backend_can_roundtrip_strict_json_v1() -> None:
    request = ExtractionRequest(
        request_id="backend-contract-002",
        text="dos escritorios a 1000 cada uno",
        currency_context="BOB",
    )

    produced = RulesEngine().extract(request)
    payload = produced.model_dump(mode="json")
    restored = ExtractionResult.model_validate(payload)

    assert restored == produced
    assert restored.schema_version == "1.0"
    assert restored.item_proposal is not None
    assert restored.item_proposal.price is not None
    assert restored.item_proposal.price.line_total == "2000.00"
