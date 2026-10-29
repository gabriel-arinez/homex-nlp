"""Controles textuales; no constituyen evaluación de audio ni GOLD."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    return RulesEngine().extract(
        ExtractionRequest(request_id="voice-next", text=text, currency_context="BOB")
    )


@pytest.mark.parametrize("marker", ["presionitario", "presunitario", "prese unitario"])
@pytest.mark.parametrize("amount", ["8.50", "12.30", "45.5"])
def test_degraded_decimal_requires_confirmation(marker, amount):
    result = extract(f"Una mesa {marker} {amount} bolivianos")
    assert result.item_proposal.price is None
    assert any(w.code == "INVALID_PRICE" for w in result.warnings)
    assert any(c.text == amount and c.decision == "UNRESOLVED" for c in result.candidates)


@pytest.mark.parametrize(
    ("phrase", "amount"),
    [
        ("precio unitario 8.50 bolivianos", "8.50"),
        ("precio unitario 8,50 bolivianos", "8.50"),
        ("presionitario 8.500 bolivianos", "8500.00"),
        ("presionitario 1850 bolivianos", "1850.00"),
        ("precio total negociado 5400 bolivianos", "5400.00"),
    ],
)
def test_unambiguous_prices_preserved(phrase, amount):
    result = extract(f"Dos mesas {phrase}")
    assert result.item_proposal.price.stated_amount == amount


@pytest.mark.parametrize(
    "piece", ["repisas", "divisiones interiores", "paneles", "cubierta superior", "patas metálicas"]
)
def test_explicit_pieces_and_internal_quantities(piece):
    result = extract(f"Cuatro veladores con dos {piece}")
    assert result.item_proposal.quantity == 4
    assert [c.name for c in result.item_proposal.components] == [piece]
    internal = [c for c in result.candidates if c.label == "CANTIDAD_INTERNA"]
    assert len(internal) == 1 and internal[0].normalized_value == 2


@pytest.mark.parametrize("color", ["gris claro", "roble claro", "no-gal", "madera clara"])
def test_compound_color_is_complete_and_not_material(color):
    result = extract(f"Un atril de melamina con una puerta y una repisa interior color {color}")
    assert [c.text for c in result.candidates if c.label == "COLOR"] == [color]
    assert [c.text for c in result.candidates if c.label == "MATERIAL"] == ["melamina"]
    assert not any(c.component_ref for c in result.candidates if c.label == "MATERIAL")


@pytest.mark.parametrize("restriction", ["sin puertas", "sin cajones", "no lleva puertas"])
def test_negative_pieces_are_consultable_and_never_positive(restriction):
    result = extract(f"Un estante {restriction}, pero con dos repisas laterales")
    assert [c.name for c in result.item_proposal.components] == ["repisas laterales"]
    assert restriction in result.item_proposal.observations
    assert any(c.label == "COMPONENTE" and c.decision == "REJECTED" for c in result.candidates)


@pytest.mark.parametrize(
    "accessory",
    [
        "ruedas",
        "tiradores metálicos",
        "cerradura",
        "chapa de seguridad",
        "soporte lateral para CPU",
    ],
)
def test_literal_accessories(accessory):
    result = extract(f"Un escritorio con dos {accessory}")
    assert result.item_proposal.accessories[0].name == accessory
    assert result.item_proposal.accessories[0].quantity == 2
    negative = extract(f"Un escritorio sin {accessory}")
    assert not negative.item_proposal.accessories


def test_multiple_explicit_thicknesses_do_not_cross():
    result = extract("Un mueble con cubierta superior de 25 mm, paneles de 18 mm")
    assert [c.name for c in result.item_proposal.components] == ["cubierta superior", "paneles"]
    assert [t.component_ref for t in result.item_proposal.thicknesses] == [
        c.component_id for c in result.item_proposal.components
    ]


def test_l_sides_never_replace_overall_length():
    result = extract(
        "Dos escritorios en L, cada escritorio tiene dos lados de 1.40 metros de largo"
    )
    assert result.item_proposal.quantity == 2
    assert not result.item_proposal.dimensions
    assert any(c.label == "DIMENSION" and c.decision == "UNRESOLVED" for c in result.candidates)


def test_tapacanto_retains_literal_termination():
    result = extract("Un escritorio con tapacanto de P.V.C. y dos cajones")
    assert result.item_proposal.accessories[0].name == "tapacanto de P.V.C"


def test_nogal_hyphen_normalization_retains_offsets():
    result = extract("Una credenza color no-gal")
    color = next(c for c in result.candidates if c.label == "COLOR")
    assert color.text == "no-gal"
    assert color.normalized_value == "nogal"


def test_papeleros_and_archivador_are_literal_internal_pieces():
    result = extract("Un escritorio con dos papeleros y un archivador")
    assert [c.name for c in result.item_proposal.components] == ["papeleros", "archivador"]


def test_hardware_is_not_swallowed_by_drawer_accessory():
    result = extract("Una credenza con dos cajones con rieles telescópicos y tiradores metálicos")
    assert [c.name for c in result.item_proposal.components] == ["cajones"]
    assert [a.name for a in result.item_proposal.accessories] == [
        "rieles telescópicos",
        "tiradores metálicos",
    ]


def test_explicit_component_axis_is_not_overall_dimension():
    result = extract(
        "Dos escritorios en L, profundidad de cubierta de 0.60 metros y altura de 0.74 metros"
    )
    depth = next(d for d in result.item_proposal.dimensions if d.axis == "profundidad")
    height = next(d for d in result.item_proposal.dimensions if d.axis == "alto")
    assert depth.component_ref == result.item_proposal.components[0].component_id
    assert height.component_ref is None


def test_negative_restriction_preserves_existing_observation():
    result = extract("Un estante color a elección, sin puertas pero con dos repisas")
    assert "color a elección" in result.item_proposal.observations
    assert "sin puertas" in result.item_proposal.observations


def test_no_gal_is_not_a_negation_of_coordinated_drawers():
    result = extract("Un escritorio color no-gal y dos cajones")
    assert [c.name for c in result.item_proposal.components] == ["cajones"]
    assert not any(c.label == "COMPONENTE" and c.decision == "REJECTED" for c in result.candidates)


def test_singular_panel_has_its_explicit_thickness():
    result = extract("Un escritorio con panel de 18 mm")
    assert result.item_proposal.components[0].name == "panel"
    assert (
        result.item_proposal.thicknesses[0].component_ref
        == result.item_proposal.components[0].component_id
    )


@pytest.mark.parametrize("color", ["nogal", "gris claro", "roble claro"])
def test_explicit_color_prefix_joined_by_asr_preserves_offsets(color):
    text = f"Un escritorio. Color{color}, precio unitario 1000 bolivianos"
    result = extract(text)
    colors = [c for c in result.candidates if c.label == "COLOR"]
    assert len(colors) == 1 and colors[0].text == color
    assert text[colors[0].start : colors[0].end] == color
    assert colors[0].component_ref is None
    assert not [
        c for c in extract(f"Un escritorio decolor{color}").candidates if c.label == "COLOR"
    ]
