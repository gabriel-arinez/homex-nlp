"""Unknown technical descriptions stay literal, unresolved, and reviewable."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="unknown-specs", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


def retained(result, literal):
    item = result.item_proposal
    assert item is not None
    evidence = [c for c in result.candidates if c.label == "ESPECIFICACION" and c.text == literal]
    assert len(evidence) == 1
    c = evidence[0]
    assert c.decision == "UNRESOLVED" and c.candidate_id in item.unresolved
    assert c.normalized_value == literal
    assert literal in item.observations
    return c


def test_mdf_veneer_and_polyurethane_are_reviewable_not_invented_materials():
    result = extract("una mesa de MDF enchapado con acabado poliuretano")
    retained(result, "enchapado")
    retained(result, "acabado poliuretano")
    assert any(
        c.label == "MATERIAL" and c.text == "MDF" and c.decision == "ACCEPTED"
        for c in result.candidates
    )
    assert not any(c.label == "MATERIAL" and "poliuretano" in c.text for c in result.candidates)


def test_unknown_brand_does_not_consume_color_or_create_a_commercial_reference():
    result = extract("una mesa marca Xylotron color qhantati")
    retained(result, "marca Xylotron")
    assert any(
        c.label == "COLOR_NO_RESUELTO" and c.text == "qhantati" and c.decision == "UNRESOLVED"
        for c in result.candidates
    )
    assert not any(c.label == "MARCA" for c in result.candidates)
    assert result.item_proposal.primary_color is None


def test_unknown_material_is_description_not_canonical_material():
    result = extract("un escritorio de corcho")
    retained(result, "de corcho")
    assert not any(c.label in {"MATERIAL", "ROL_MATERIAL"} for c in result.candidates)
    assert result.item_proposal.quantity == 1


@pytest.mark.parametrize(
    "text,literal",
    [
        ("Dos mesas de MDF enchapadas con acabado de poliuretano.", "enchapadas"),
        ("Una mesa de madera enchapada.", "enchapada"),
        ("Una mesa con acabado de poliuretano.", "acabado de poliuretano"),
        ("Dos escritorios de corcho.", "de corcho"),
        ("Una mesa de fibra volcánica.", "de fibra volcánica"),
        ("Un escritorio. Material corcho.", "Material corcho"),
        ("Un escritorio. Material de corcho.", "Material de corcho"),
        ("Una mesa marca Xylotron modelo XT42.", "marca Xylotron"),
        ("Una mesa marca Xylotron de 120 cm de ancho.", "marca Xylotron"),
        ("Una mesa marca Xylotron precio 1500 bolivianos.", "marca Xylotron"),
    ],
)
def test_bounded_positive_variants(text, literal):
    retained(extract(text), literal)


@pytest.mark.parametrize(
    "text",
    [
        "Una mesa sin acabado de poliuretano.",
        "Una mesa no lleva enchapado.",
        "Una mesa sin marca Xylotron.",
        "Una mesa no lleva material corcho.",
        "Una mesa de melamina.",
        "Una mesa de MDF.",
        "Una mesa de 120 cm de ancho.",
        "Una mesa de ciento veinte centímetros de ancho.",
        "Una mesa de cuatro personas.",
        "Una mesa de modelo XT42.",
        "Una mesa de precio 1500 bolivianos.",
        "Una mesa de ruedas.",
        "Una mesa Xylotron.",
    ],
)
def test_unknown_retention_does_not_invent_positive_technical_specs(text):
    result = extract(text)
    assert not any(c.label == "ESPECIFICACION" for c in result.candidates)


def test_review_evidence_preserves_approved_commercial_fields():
    result = extract(
        "Dos escritorios de corcho de 120 cm de ancho y 60 cm de profundidad, "
        "marca Xylotron color negro, precio unitario 1500 bolivianos."
    )
    retained(result, "de corcho")
    retained(result, "marca Xylotron")
    item = result.item_proposal
    assert item.quantity == 2
    assert {(d.axis, d.value_mm, d.component_ref) for d in item.dimensions} == {
        ("ancho", "1200", None),
        ("profundidad", "600", None),
    }
    assert item.primary_color.value == "negro"
    assert item.price.stated_amount == "1500.00"
    assert not item.components
    assert not any(c.label in {"MARCA", "MATERIAL"} for c in result.candidates)


@pytest.mark.parametrize(
    "text",
    [
        "Una mesa de melamina marca Novopan.",
        "Un escritorio de acero inoxidable.",
        "Una mesa de vidrio templado.",
        "Una mesa de MDF con rieles telescópicos.",
        "Una mesa de 120 por 60 centímetros.",
        "Una mesa de cuatro puestos.",
    ],
)
def test_known_material_brand_and_numeric_clauses_do_not_become_unknown(text):
    assert not any(c.label == "ESPECIFICACION" for c in extract(text).candidates)


def test_brand_alternative_remains_one_literal_unresolved_description():
    result = extract("Una mesa marca Xylotron o Qhapaq color negro.")
    retained(result, "marca Xylotron o Qhapaq")
    assert not any(c.label == "MARCA" for c in result.candidates)
    # Preserve the existing conservative alternative-clause color abstention.
    assert result.item_proposal.primary_color is None


def test_noncommercial_negated_order_has_no_structured_unknown_information():
    result = extract("No quiero una mesa de corcho marca Xylotron.")
    assert result.item_proposal is None
    assert not any(c.label == "ESPECIFICACION" for c in result.candidates)


@pytest.mark.parametrize(
    "brand", ["Casa de Roble del Sur", "Acme 2000", "Diseño y Madera del Valle"]
)
def test_complete_unknown_brand_clause_is_not_truncated(brand):
    result = extract(f"Una mesa marca {brand} color negro.")
    retained(result, f"marca {brand}")
    assert not any(c.label == "MARCA" for c in result.candidates)


def test_numeric_brand_does_not_absorb_a_commercial_amount():
    result = extract("Una mesa marca Acme 2000 por quinientos bolivianos.")
    retained(result, "marca Acme 2000")
    assert result.item_proposal.price is None
    assert "quinientos" not in result.item_proposal.observations


@pytest.mark.parametrize("tail", ["de 120 cm de ancho", "con dos cajones", "y una mesa de madera"])
def test_unknown_brand_stops_before_measurement_component_or_independent_owner(tail):
    result = extract(f"Un escritorio marca Casa de Roble del Sur {tail}.")
    if "una mesa" in tail:
        assert result.item_proposal is None
    else:
        retained(result, "marca Casa de Roble del Sur")


def test_unknown_multiword_brand_exclusion_is_not_affirmed():
    result = extract("Una mesa sin marca Casa de Muebles del Sur.")
    assert not any(c.label == "ESPECIFICACION" for c in result.candidates)


def test_furniture_word_inside_unknown_brand_preserves_original_abstention():
    result = extract("Una mesa marca Casa de Muebles del Sur color negro.")
    assert result.item_proposal is None
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in result.warnings)


@pytest.mark.parametrize(
    "phrase", ["marca Cajón color negro", "modelo cajón", "marca El Cajón", "modelo El Cajón"]
)
def test_drawer_word_in_explicit_brand_or_model_is_not_a_physical_component(phrase):
    result = extract(f"Una mesa {phrase}.")
    assert result.item_proposal is not None
    assert not result.item_proposal.components
    assert not result.item_proposal.accessories


def test_explicit_component_after_brand_still_owns_its_dimension():
    result = extract("Un escritorio marca Xylotron con un cajón de 40 cm de ancho.")
    retained(result, "marca Xylotron")
    item = result.item_proposal
    assert len(item.components) == 1 and item.components[0].name == "cajón"
    assert any(
        d.value_mm == "400" and d.component_ref == item.components[0].component_id
        for d in item.dimensions
    )
