"""Independent semantic-owner and lossless literal-field regressions."""

import pytest

from homex_nlp.catalog import CatalogRequest, extract_catalog
from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def furniture(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="semantic-closure", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    assert result.item_proposal is not None
    return result


def catalog(text, category="SILLA"):
    result = extract_catalog(CatalogRequest(category=category, text=text))
    assert all(c.text == text[c.start : c.end] for c in result.evidence)
    return result


@pytest.mark.parametrize("height", ["un metro cuarenta", "1 metro 45", "un metro ochenta"])
def test_compound_height_before_conjoined_next_axis(height):
    item = furniture(
        f"Un atril de setenta centímetros de ancho, {height} de alto y cincuenta centímetros de profundidad."
    ).item_proposal
    assert any(d.axis == "alto" for d in item.dimensions)
    assert {d.axis for d in item.dimensions} == {"ancho", "alto", "profundidad"}


@pytest.mark.parametrize(
    "substrate",
    ["Tablero melamínico Novopan", "Me lamina", "Melamina Novopan", "tablero de melamina,"],
)
def test_explicit_board_gauge_survives_brand_alias_and_pause(substrate):
    result = furniture(
        f"Un estante de 80 cm de ancho. {substrate} de dieciséis milímetros con tapacantos de PVC."
    )
    assert [g.value_mm for g in result.item_proposal.thicknesses] == ["16"]
    assert not any(
        g.component_ref
        and g.component_ref
        == next((c.component_id for c in result.item_proposal.components if c.name == "tapa"), None)
        for g in result.item_proposal.thicknesses
    )


def test_recovered_head_keeps_general_dimensions_on_furniture():
    result = furniture(
        "Un gadetero de cinco cajones de 54 cm de ancho, 48 de profundidad, un metro 40 de alto tablero de melamina de 16 mm."
    )
    assert len(result.item_proposal.dimensions) == 3
    assert all(d.component_ref is None for d in result.item_proposal.dimensions)
    assert any(
        c.label == "RECUPERACION_LEXICA" and c.decision == "UNRESOLVED" for c in result.candidates
    )


def test_split_edge_banding_is_not_a_tapa_component():
    result = furniture("Un gavetero de melamina de 16 mm con tapa cantos de PVC y dos cajones.")
    assert not any(c.name.lower() == "tapa" for c in result.item_proposal.components)
    assert any("tapa cantos" in a.name.lower() for a in result.item_proposal.accessories)
    assert not any(
        c.label == "MATERIAL" and c.text == "PVC" and c.component_ref for c in result.candidates
    )


def test_terminal_color_without_clear_owner_stays_pending_not_last_shelf():
    result = furniture(
        "Un escritorio con credenza. Credenza lateral con dos repisas color sapelli, precio de 2100 bolivianos."
    )
    colors = [c for c in result.candidates if c.label == "COLOR" and c.text == "sapelli"]
    assert colors
    assert all(c.component_ref is None and c.decision == "UNRESOLVED" for c in colors)
    assert result.item_proposal.primary_color is None


def test_material_alias_at_measured_clause_head_is_reviewable():
    result = furniture(
        "Un escritorio con credenza. Me lamina de 16 milímetros con tapacantos de PVC."
    )
    assert any(
        c.label == "RECUPERACION_LEXICA"
        and c.text.lower() == "me lamina"
        and c.normalized_value == "melamina"
        for c in result.candidates
    )
    assert any(g.value_mm == "16" for g in result.item_proposal.thicknesses)


@pytest.mark.parametrize(
    "padding", ["Reposapiés plegable acolchado", "Apoyo lumbar acolchado ajustable en altura"]
)
def test_other_owner_padding_does_not_conflict_with_seat(padding):
    result = catalog(
        f"Una silla operativa. Asiento de espuma de alta densidad. {padding}. Precio unitario de 750 bolivianos."
    )
    assert "espuma de alta densidad" in result.fields["especificaciones"]["asiento"]
    assert not any(r.field == "especificaciones.asiento" for r in result.field_reviews)


def test_complete_model_stops_at_explicit_next_component_without_punctuation():
    result = catalog(
        "Una silla operativa modelo NF Guion 628 espaldar de malla asiento de espuma de alta densidad"
    )
    assert result.fields["modelo"] == "NF-628"
    assert all("espaldar" not in e.text.lower() for e in result.evidence if e.label == "modelo")


@pytest.mark.parametrize("count", ["Veinte", "24"])
def test_bar_quote_quantity_is_not_name_or_stock(count):
    result = catalog(
        f"{count} barras de zócalo de alto tráfico, de 90 milímetros de alto y 12 milímetros de espesor. Cada barra mide dos metros con treinta centímetros lineales. Precio unitario de 65 bolivianos por barra.",
        "OTRO",
    )
    assert result.fields["nombre"] == "barras de zócalo de alto tráfico"
    assert not {"stock", "cantidad", "existencias"} & result.fields.keys()
    notes = result.fields["observaciones"]
    assert "90 milímetros de alto" in notes and "12 milímetros de espesor" in notes
    assert "dos metros con treinta centímetros lineales" in notes
    assert count not in notes and "Precio" not in notes


def test_unmapped_technical_clauses_retained_without_transcript_dump():
    result = furniture(
        "Un escritorio de melamina con regatones engomados antideslizantes y acabado con pintura al horno. Garantía de dos años. Precio unitario de 900 bolivianos."
    )
    assert "pintura al horno" in result.item_proposal.observations
    assert "antideslizantes" in result.item_proposal.observations
    assert "Precio" not in result.item_proposal.observations


def test_previous_price_and_ambiguous_code_guards_still_hold():
    result = furniture("Una mesa de melamina de 16 mm. Precio de 13 mil 400 bolivianos.")
    assert any(
        c.label == "PRECIO_AMBIGUO" and c.normalized_value == "13400" for c in result.candidates
    )
    assert result.item_proposal.price is None
    code = catalog("Una silla modelo NF guion 8,341, color negro")
    assert code.fields.get("modelo") in (None, "NF-8341")
    assert code.fields.get("modelo") != "NF-8"
    assert catalog("Una silla modelo 82A").fields["modelo"] == "82A"
    assert (
        catalog("Piso flotante código N8261, espesor 80 mm", "PISO_FLOTANTE").fields["modelo"]
        == "N8261"
    )


def test_unclassified_explicit_measurement_is_retained_without_guessing_substrate():
    result = furniture(
        "Una estación de trabajo. De la mina no hubo pan de 16 milímetros, mesón engrosado a 28."
    )
    assert any(
        c.label == "MEDIDA_NO_CLASIFICADA"
        and c.text == "16 milímetros"
        and c.decision == "UNRESOLVED"
        for c in result.candidates
    )
    assert "16 milímetros" in result.item_proposal.observations
    assert not any(
        c.label == "MATERIAL" and c.normalized_value in {"melamina", "Novopan"}
        for c in result.candidates
    )
    assert all(g.unit is None for g in result.item_proposal.thicknesses)
