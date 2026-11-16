"""Public-API regressions for literal retake measurements and safe references."""

import pytest

from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="retake-regression", text=text, currency_context="BOB")
    )
    assert ExtractionResult.model_validate_json(result.model_dump_json()) == result
    assert result.schema_version == "1.0" and result.engine.mode == "RULES_ONLY"
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


def test_article_before_explicit_height_is_not_a_measurement():
    result = extract("Dos escritorios con una altura de 73 cm. Precio unitario 2500 bolivianos.")
    assert [(d.axis, d.value_mm) for d in result.item_proposal.dimensions] == [("alto", "730")]
    assert result.item_proposal.quantity == 2
    assert result.item_proposal.price.line_total == "5000.00"
    assert not any(c.text == "una altura" for c in result.candidates)


@pytest.mark.parametrize("boundary", [", ", ". "])
def test_descriptive_desktop_and_introduced_drawer_keep_their_scopes(boundary):
    result = extract(
        "Tres escritorios rectos operativos con cajonera rodante"
        f"{boundary}Escritorio de 140 cm de ancho{boundary}Cajonera rodante de 33 cm de ancho. "
        "Precio unitario 1600 bolivianos."
    )
    assert result.status == "REQUIRES_REVIEW" and result.proposed_item_count == 1
    item = result.item_proposal
    assert item.quantity == 3 and item.price.line_total == "4800.00"
    drawers = [c for c in item.components if c.name == "cajonera"]
    assert len(drawers) == 1
    assert {(d.value_mm, d.component_ref) for d in item.dimensions} == {
        ("1400", None),
        ("330", drawers[0].component_id),
    }


@pytest.mark.parametrize(
    "suffix",
    [
        "dos escritorios de 140 cm de ancho",
        "otro escritorio de 140 cm de ancho",
        "otra cajonera de 33 cm de ancho",
        "dos cajoneras de 33 cm de ancho",
        "y cajonera de 33 cm de ancho",
        "cajonera de madera",
        "credenza lateral derecha de 90 cm de ancho",
    ],
)
def test_comma_does_not_merge_independent_or_ambiguous_orders(suffix):
    result = extract(f"Tres escritorios con cajonera, {suffix}.")
    assert result.status == "NO_PROPOSAL" and result.proposed_item_count == 0
    assert result.item_proposal is None


@pytest.mark.parametrize(
    "chain, expected",
    [
        ("1,40 m × 70 cm", [("1.40", "m", "1400.00"), ("70", "cm", "700")]),
        ("un metro 40 x 70 centímetros", [("140", "cm", "1400"), ("70", "cm", "700")]),
        ("33 × 40 × 63 cm", [("33", "cm", "330"), ("40", "cm", "400"), ("63", "cm", "630")]),
        ("33x40x63cm", [("33", "cm", "330"), ("40", "cm", "400"), ("63", "cm", "630")]),
        ("33 x 40 x 63", [("33", None, None), ("40", None, None), ("63", None, None)]),
        ("1 m x 40 x 63 cm", [("1", "m", "1000"), ("40", None, None), ("63", "cm", "630")]),
    ],
)
def test_ordered_chains_preserve_units_and_leave_axes_unknown(chain, expected):
    result = extract(f"Una mesa de {chain}. Precio unitario 900 bolivianos.")
    assert result.status == "REQUIRES_REVIEW"
    dims = result.item_proposal.dimensions
    assert [(d.value, d.unit, d.value_mm) for d in dims] == expected
    assert all(d.axis is None and d.component_ref is None for d in dims)
    assert any(w.code == "MISSING_AXIS" for w in result.warnings)
    assert result.item_proposal.quantity == 1
    assert result.item_proposal.price.line_total == "900.00"


def test_chain_belongs_to_explicit_drawer_not_desktop_or_later_clause():
    result = extract(
        "Dos escritorios con cajonera, escritorio de 1,40 m x 70 cm, "
        "cajonera de 33 x 40 x 63 cm. Escritorio de 73 cm de alto. Precio unitario 1600 bolivianos."
    )
    item = result.item_proposal
    drawer = next(c.component_id for c in item.components if c.name == "cajonera")
    assert [(d.value_mm, d.component_ref) for d in item.dimensions if d.axis is None] == [
        ("1400.00", None),
        ("700", None),
        ("330", drawer),
        ("400", drawer),
        ("630", drawer),
    ]
    assert [(d.value_mm, d.component_ref) for d in item.dimensions if d.axis == "alto"] == [
        ("730", None)
    ]
    evidence = {c.candidate_id: c for c in result.candidates}
    assert all(
        evidence[d.evidence_ids[0]].component_ref == d.component_ref for d in item.dimensions
    )
    assert item.quantity == 2 and item.price.line_total == "3200.00"


@pytest.mark.parametrize(
    "text",
    [
        "Una mesa. Embalaje 33 x 40 x 63 cm.",
        "Una mesa de -33 x 40 x 63 cm.",
        "Una mesa de 0 x 40 x 63 cm.",
    ],
)
def test_unknown_owner_and_invalid_chains_do_not_gain_dimensions(text):
    assert extract(text).item_proposal.dimensions == []


def test_existing_explicit_height_and_real_one_unit_height_remain_supported():
    result = extract("Dos escritorios de 1 cm de alto y 73 cm de ancho.")
    assert {(d.axis, d.value_mm) for d in result.item_proposal.dimensions} == {
        ("alto", "10"),
        ("ancho", "730"),
    }


def test_chain_preservation_does_not_reassign_an_existing_height():
    result = extract(
        "Un escritorio operativo con cajonera rodante de 1,40 m x 70 cm y 73 cm de altura."
    )
    height = next(d for d in result.item_proposal.dimensions if d.axis == "alto")
    assert height.value_mm == "730" and height.component_ref is None


@pytest.mark.parametrize("quantity, drawer_height", [(2, 73), (6, 63)])
def test_recognized_quantities_and_drawer_values_are_never_replaced_from_a_script(
    quantity, drawer_height
):
    result = extract(
        f"{quantity} escritorios con cajonera, escritorio de 1,40 m x 70 cm, "
        f"cajonera de 33 x 40 x {drawer_height} cm. Precio unitario 1600 bolivianos."
    )
    item = result.item_proposal
    drawer = next(c.component_id for c in item.components if c.name == "cajonera")
    assert item.quantity == quantity and item.price.line_total == f"{quantity * 1600}.00"
    assert [d.value_mm for d in item.dimensions if d.component_ref == drawer] == [
        "330",
        "400",
        str(drawer_height * 10),
    ]


@pytest.mark.parametrize("measure", ["0 x 40 x 63 cm", "33 x 0 x 63 cm", "33 cm x -40 cm"])
def test_invalid_measurements_do_not_license_a_comma_reference(measure):
    result = extract(f"Un escritorio con cajonera, cajonera de {measure}.")
    assert result.status == "NO_PROPOSAL" and result.item_proposal is None


def test_eleven_independent_drawers_are_not_a_descriptive_reference():
    result = extract("Un escritorio con cajonera, once cajoneras de 33 cm.")
    assert result.status == "NO_PROPOSAL" and result.item_proposal is None


@pytest.mark.parametrize("unit", ["mt", "mts"])
def test_chain_accepts_existing_metre_unit_aliases(unit):
    result = extract(f"Una mesa de 1,40 {unit} x 70 cm.")
    assert [(d.value_mm, d.unit, d.axis) for d in result.item_proposal.dimensions] == [
        ("1400.00", "m", None),
        ("700", "cm", None),
    ]


def test_chain_cannot_assert_the_same_evidence_as_both_thickness_and_dimension():
    result = extract("Una mesa de 1400 mm x 700 mm.")
    assert result.item_proposal.dimensions == []
    assert any(
        c.text == "1400 mm x 700 mm" and c.decision == "UNRESOLVED" for c in result.candidates
    )
