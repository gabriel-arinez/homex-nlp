"""Commercial names and finite domain knowledge preserve original evidence."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="independent-identity", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


@pytest.mark.parametrize(
    "noun",
    [
        "cocineta",
        "gabinete",
        "alacena",
        "mostrador",
        "estantería",
        "aparador",
        "repisero",
        "zapatero",
        "tocador",
        "cubo móvil",
        "cubos móviles",
    ],
)
def test_named_furniture_is_a_partial_proposal(noun):
    item = extract("Un " + noun).item_proposal
    assert item is not None
    assert item.name == noun
    assert not item.dimensions and item.price is None


@pytest.mark.parametrize(
    "name,family",
    [
        ("escritorio gerencial", "escritorio"),
        ("mesa circular", "mesa"),
        ("mesa simple", "mesa"),
        ("mesa plegable", "mesa"),
        ("mesa archivadora", "mesa"),
        ("escritorio en L", "escritorio"),
        ("mueble aguatero", "mueble"),
        ("mueble para escobas", "mueble"),
    ],
)
def test_full_name_is_separate_from_family_without_absorbing_specs(name, family):
    text = f"Un {name} de 120 cm de ancho, color blanco."
    item = extract(text).item_proposal
    assert item is not None and item.name == name
    assert item.furniture_type_candidate == family
    assert "120" not in item.name and "blanco" not in item.name


def test_contextual_product_alias_is_proposed_not_a_rewritten_transcript():
    text = "Un gadetero con tres cajones de melamina."
    result = extract(text)
    assert result.item_proposal.name == "gavetero"
    evidence = next(c for c in result.candidates if c.label == "RECUPERACION_LEXICA")
    assert evidence.text == "gadetero"
    assert evidence.normalized_value == "gavetero"
    assert evidence.decision == "UNRESOLVED" and evidence.reason


@pytest.mark.parametrize(
    "text",
    [
        "gadetero",
        "La marca Gadetero",
        "hola probando uno dos tres",
        "estoy probando el micrófono sobre la mesa",
        "ayer hablamos de una mesa pero hoy no vamos a comprar nada",
        "no quiero una cocineta",
    ],
)
def test_noncommercial_or_unsupported_alias_context_does_not_propose(text):
    assert extract(text).item_proposal is None


@pytest.mark.parametrize("raw,canonical", [("me lamina", "melamina"), ("melaménico", "melamínico")])
def test_contextual_material_recovery_keeps_full_original_span(raw, canonical):
    text = "Un estante con tablero de " + raw + "."
    result = extract(text)
    assert any(
        c.label == "MATERIAL" and c.text == raw and c.normalized_value == canonical
        for c in result.candidates
    )
    assert any(
        c.label == "RECUPERACION_LEXICA" and c.text == raw and c.decision == "UNRESOLVED"
        for c in result.candidates
    )


@pytest.mark.parametrize("raw", ["Novopan", "nobopan", "novo pan"])
def test_board_brand_is_scoped_domain_evidence_not_a_catalog_creation(raw):
    result = extract("Un estante de tablero melamínico " + raw + ".")
    assert any(
        c.label == "MARCA" and c.text == raw and c.normalized_value == "Novopan"
        for c in result.candidates
    )


@pytest.mark.parametrize(
    "color", ["sapelli", "wengué", "cerezo", "chumbo", "cedro", "maderable oscuro"]
)
def test_explicit_decorative_color_is_preserved(color):
    result = extract("Un gavetero de melamina. Color " + color + ".")
    assert result.item_proposal.primary_color.value == color
    assert any(c.label == "COLOR" and c.text == color for c in result.candidates)


def test_solid_wood_species_is_not_invented_as_a_decorative_color():
    result = extract("Una mesa de madera de cedro.")
    assert not any(c.label == "COLOR" and c.text == "cedro" for c in result.candidates)


def test_generic_metal_is_not_promoted_to_a_specific_alloy():
    result = extract("Un escritorio con jaladores metálicos.")
    assert not any("acero" in str(c.normalized_value).lower() for c in result.candidates)


def test_unstructured_service_facts_survive_as_bounded_observations():
    text = "Una mesa simple de melamina. Garantía de un año. Procedencia Bolivia. Incluye instalación y entrega."
    result = extract(text)
    assert "Garantía de un año" in result.item_proposal.observations
    assert "Procedencia Bolivia" in result.item_proposal.observations
    assert "Incluye instalación y entrega" in result.item_proposal.observations
    assert text != result.item_proposal.observations
    assert all(c.normalized_value for c in result.candidates if c.label == "ESPECIFICACION")


@pytest.mark.parametrize(
    "detail,expected",
    [
        ("tablero melamínico de 18 mm de grosor", "18"),
        ("panel frontal 18 mm", "18"),
        ("mesón engrosado a 27 mm", "27"),
        ("superficie auxiliar de 27 mm", "27"),
    ],
)
def test_board_thickness_licenses_do_not_require_a_bare_material_word(detail, expected):
    item = extract("Un escritorio; " + detail).item_proposal
    assert [m.value_mm for m in item.thicknesses] == [expected]


@pytest.mark.parametrize(
    "material,role",
    [
        ("MDF", "substrate"),
        ("melamina", "coating_or_board_description"),
        ("acero cromado", "treated_structural_material"),
    ],
)
def test_material_role_is_separate_reviewable_knowledge_not_a_spoken_claim(material, role):
    result = extract("Un escritorio de " + material + ".")
    c = next(c for c in result.candidates if c.label == "ROL_MATERIAL")
    assert c.normalized_value["role"] == role
    assert c.decision == "UNRESOLVED"
    assert c.reason
