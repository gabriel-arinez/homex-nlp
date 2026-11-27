"""Independent composition and ownership regressions; no evaluation identifiers."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="independent-relations", text=text, currency_context="BOB")
    )
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


@pytest.mark.parametrize("connector", ["con", "incluye", "incorpora", "compuesto por"])
def test_desk_sideboard_composition_does_not_need_integrated_keyword(connector):
    result = extract(
        f"Un escritorio {connector} credenza. Escritorio de 140 cm de ancho. Credenza de 90 cm de ancho."
    )
    item = result.item_proposal
    assert item is not None and item.quantity == 1
    side = next(c for c in item.components if "credenza" in c.name.lower())
    assert any(d.value_mm == "1400" and d.component_ref is None for d in item.dimensions)
    assert any(
        d.value_mm == "900" and d.component_ref == side.component_id for d in item.dimensions
    )


def test_kitchen_upper_and_lower_cabinets_remain_independent_owners():
    item = extract(
        "Una cocineta con gabinete superior de 130 cm de ancho y 70 cm de alto. Gabinete inferior de 160 cm de ancho y 80 cm de alto."
    ).item_proposal
    assert item is not None
    upper = next(c for c in item.components if "superior" in c.name)
    lower = next(c for c in item.components if "inferior" in c.name)
    assert upper.component_id != lower.component_id
    assert any(
        d.value_mm == "1300" and d.component_ref == upper.component_id for d in item.dimensions
    )
    assert any(
        d.value_mm == "1600" and d.component_ref == lower.component_id for d in item.dimensions
    )


def test_reception_top_is_a_spatial_component_not_a_second_order():
    item = extract(
        "Un mueble de recepción de 150 cm de ancho. Mesa superior con vidrio templado. Mueble móvil con ruedas."
    ).item_proposal
    assert item is not None and item.quantity == 1
    assert any("mesa superior" in c.name.lower() for c in item.components)


@pytest.mark.parametrize(
    "text",
    [
        "Dos escritorios y tres credenzas de melamina",
        "Un escritorio y una credenza",
        "Una mesa y un escritorio",
        "Un escritorio con dos mesas de madera",
    ],
)
def test_separate_main_products_still_abstain(text):
    result = extract(text)
    assert result.item_proposal is None
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in result.warnings)


def test_drawer_description_repetition_does_not_duplicate_a_component():
    result = extract(
        "Un gavetero de tres cajones de 50 cm de ancho y 100 cm de alto. Tablero de melamina. Tres cajones con rieles telescópicos."
    )
    item = result.item_proposal
    assert len([c for c in item.components if c.name == "cajones"]) == 1
    assert all(d.component_ref is None for d in item.dimensions)
    assert item.quantity == 1


def test_explicit_other_drawer_component_is_not_merged():
    item = extract("Un escritorio con dos cajones. Otros dos cajones laterales.").item_proposal
    assert len([c for c in item.components if "cajones" in c.name]) == 2


def test_frame_description_does_not_steal_main_dimensions_or_make_apron_height():
    result = extract(
        "Dos escritorios con patas metálicas de 120 cm de largo, 75 cm de alto y 60 cm de profundidad. Faldón a media altura de 18 mm."
    )
    item = result.item_proposal
    assert any(
        d.axis == "largo" and d.value_mm == "1200" and d.component_ref is None
        for d in item.dimensions
    )
    assert not any(d.axis == "alto" and d.value_mm == "18" for d in item.dimensions)
    apron = next(c for c in item.components if "faldón" in c.name.lower())
    assert any(
        m.value_mm == "18" and m.component_ref == apron.component_id for m in item.thicknesses
    )


def test_explicit_leg_height_stays_a_leg_dimension():
    item = extract("Una mesa con patas de 70 cm de alto.").item_proposal
    leg = next(c for c in item.components if c.name == "patas")
    assert any(d.axis == "alto" and d.component_ref == leg.component_id for d in item.dimensions)


def test_accessory_material_does_not_become_main_or_board_material():
    result = extract(
        "Un escritorio con tablero de melamina y tapacantos de PVC, jaladores metálicos."
    )
    assert not any(
        c.label == "MATERIAL" and c.text in {"PVC", "metálicos"} and c.decision == "ACCEPTED"
        for c in result.candidates
    )
    assert any(c.label == "MATERIAL_ACCESORIO" and c.text == "PVC" for c in result.candidates)


def test_two_explicit_colors_are_a_combination_not_an_alternative():
    item = extract("Un escritorio de melamina. Color wengué con negro.").item_proposal
    assert item.primary_color.value == "wengué" and item.secondary_color.value == "negro"


def test_l_arms_keep_two_values_without_assigning_conventional_axes():
    result = extract(
        "Un escritorio en L, de un metro sesenta por un metro ochenta de largo, 60 cm de profundidad."
    )
    dims = result.item_proposal.dimensions
    assert len([d for d in dims if d.axis is None]) == 2
    assert not any(d.axis == "largo" for d in dims)
    assert any(c.label == "GEOMETRIA" and c.decision == "UNRESOLVED" for c in result.candidates)


def test_regulable_range_remains_reviewable_not_a_single_false_dimension():
    result = extract("Una mesa con altura regulable de 70 a 110 cm.")
    assert any(
        c.label == "RANGO_DIMENSIONAL"
        and c.normalized_value["minimum"] == "70"
        and c.normalized_value["maximum"] == "110"
        for c in result.candidates
    )
    assert not any(d.axis == "alto" and d.value == "70" for d in result.item_proposal.dimensions)


@pytest.mark.parametrize(
    "text",
    [
        "Un cubo móvil con tres cajones, dos papeleros y uno archivador.",
        "Una credenza con dos cajones para archivadores.",
        "Un escritorio con credenza. Credenza con cajones para archivadores de palanca.",
    ],
)
def test_filing_drawer_functions_and_storage_capacity_are_not_main_products(text):
    result = extract(text)
    assert result.item_proposal is not None
    assert result.item_proposal.quantity == 1
    assert not any(c.name.startswith("archivadores") for c in result.item_proposal.components)


def test_later_spatial_qualifier_refines_the_same_introduced_sideboard():
    item = extract(
        "Un escritorio con credenza. Credenza de 90 cm de ancho. Credenza lateral con una puerta."
    ).item_proposal
    assert len([c for c in item.components if c.name.casefold().startswith("credenza")]) == 1


def test_per_side_count_is_not_a_whole_furniture_internal_total():
    result = extract("Un escritorio con tres cajones por lado.")
    assert result.item_proposal.quantity == 1
    assert any(
        c.label == "DISTRIBUCION" and c.normalized_value["basis"] == "per_side"
        for c in result.candidates
    )
    assert not any(
        c.label == "CANTIDAD_INTERNA" and c.decision == "ACCEPTED" for c in result.candidates
    )


def test_written_range_uses_the_same_scalar_grammar():
    result = extract("Una mesa con altura regulable de setenta a ciento diez centímetros.")
    assert any(
        c.label == "RANGO_DIMENSIONAL"
        and c.normalized_value["minimum"] == "70"
        and c.normalized_value["maximum"] == "110"
        for c in result.candidates
    )


def test_unknown_first_color_does_not_silently_become_only_the_second_color():
    result = extract("Un escritorio de melamina. Color maderable con negro.")
    assert result.item_proposal.primary_color is None
    assert any(
        c.label == "COLOR_NO_RESUELTO" and c.decision == "UNRESOLVED" for c in result.candidates
    )


def test_color_to_be_selected_stays_a_pending_selection():
    result = extract("Una mesa simple. Color a elección.")
    assert result.item_proposal.primary_color is None
    assert any(
        c.label == "SELECCION_COLOR" and c.decision == "UNRESOLVED" for c in result.candidates
    )


def test_composition_does_not_depend_on_asr_periods_instead_of_commas():
    item = extract(
        "Un mueble de recepción de 150 cm de ancho, tablero de melamina, mesa superior con vidrio templado, mueble móvil con ruedas con freno."
    ).item_proposal
    assert item is not None and item.quantity == 1
    assert any("mesa superior" in c.name.casefold() for c in item.components)


def test_introduced_sideboard_can_be_described_again_after_a_technical_list():
    item = extract(
        "Un escritorio con credenza, escritorio de 140 cm de ancho, credenza de 90 cm de ancho, tablero de melamina, credenza con dos cajones."
    ).item_proposal
    assert item is not None
    assert len([c for c in item.components if c.name.casefold().startswith("credenza")]) == 1


def test_a_freshly_counted_sideboard_after_a_pause_is_still_independent():
    assert extract("Un escritorio de madera, una credenza con dos cajones.").item_proposal is None
