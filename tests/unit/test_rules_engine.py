from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def run(text: str):
    return RulesEngine().extract(
        ExtractionRequest(request_id="f03", text=text, currency_context="BOB")
    )


def test_negotiated_and_unit_prices_keep_their_authority() -> None:
    total = run("dos escritorios, total 2000")
    unit = run("dos escritorios a 1000 cada uno")
    exact = run("tres muebles, total 100")
    assert total.item_proposal.price.mode == "TOTAL_NEGOCIADO"
    assert unit.item_proposal.price.line_total == "2000.00"
    assert exact.item_proposal.price.line_total == "100.00"
    assert exact.item_proposal.price.unit_price_reference == "33.333333"


def test_measurements_thickness_and_empty_input() -> None:
    result = run("un escritorio de ancho 1.80 m y alto 0.8 m, estructura de 18 mm y meson a 25 mm")
    assert [item.value_mm for item in result.item_proposal.dimensions] == ["1800.00", "800.0"]
    assert [item.value for item in result.item_proposal.thicknesses] == ["18", "25"]
    assert run("sin datos").status == "NO_PROPOSAL"


def test_catalog_and_multiple_products_do_not_create_a_line() -> None:
    assert run("una silla ejecutiva total 500").status == "NO_PROPOSAL"
    assert run("un escritorio y una mesa, total 2000").status == "NO_PROPOSAL"


def test_prices_are_parsed_completely_and_missing_unit_requires_review() -> None:
    thousands = run("un escritorio, total 1,500.00")
    malformed = run("un escritorio, total 1.5.0")
    missing_unit = run("un escritorio de ancho 1.80")
    assert thousands.item_proposal.price.line_total == "1500.00"
    assert any(warning.code == "INVALID_PRICE" for warning in malformed.warnings)
    assert any(warning.code == "MISSING_UNIT" for warning in missing_unit.warnings)


def test_explicit_rectification_keeps_rejected_evidence() -> None:
    result = run("un escritorio, no mesa, total 100")
    assert result.item_proposal.name == "mesa"
    assert any(candidate.decision == "REJECTED" for candidate in result.candidates)
