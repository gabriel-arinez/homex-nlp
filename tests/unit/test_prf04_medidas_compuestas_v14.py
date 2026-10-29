"""Reproductor proporcionado por el usuario y controles sintéticos de v14."""

from decimal import Decimal

import pytest

from homex_nlp import __version__
from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine
from homex_nlp.rules import find_measurements

VARIANTES = ("un metro 20", "un metro veinte", "un metro y veinte centímetros")


def extraer(texto):
    r = RulesEngine().extract(
        ExtractionRequest(request_id="v14", text=texto, currency_context="BOB")
    )
    return ExtractionResult.model_validate_json(r.model_dump_json())


@pytest.mark.parametrize("medida", VARIANTES)
@pytest.mark.parametrize("material", ["melamina", "melamine"])
def test_captura_23_tres_variantes_y_especificaciones(medida, material):
    texto = (
        f"Necesito un escritorio de {material} blanca, de {medida} de ancho, "
        "60 centímetros de profundidad y 75 centímetros de alto."
    )
    r = extraer(texto)
    item = r.item_proposal
    assert r.status == "REQUIRES_REVIEW"
    assert r.engine.mode == "RULES_ONLY"
    assert r.engine.rules_version == "prf04-rules-final"
    assert r.engine.model_version is None
    assert r.schema_version == "1.0"
    assert __version__ == "0.1.18"
    assert len(item.dimensions) == 3
    assert {d.axis: d.value_mm for d in item.dimensions} == {
        "ancho": "1200",
        "alto": "750",
        "profundidad": "600",
    }
    assert not any(w.code == "MISSING_UNIT" for w in r.warnings)
    ancho = next(d for d in item.dimensions if d.axis == "ancho")
    assert (ancho.value, ancho.unit, ancho.original_text) == ("120", "cm", medida + " de ancho")
    evidence = next(c for c in r.candidates if c.candidate_id == ancho.evidence_ids[0])
    assert (evidence.start, evidence.end) == (
        texto.index(medida),
        texto.index(medida) + len(medida + " de ancho"),
    )
    assert evidence.normalized_value == ["120", "cm"]
    assert item.quantity == 1 and item.price is None and item.thicknesses == []
    assert item.components == []  # material is evidence, not a fabricated component/catalog ID
    materiales = [c for c in r.candidates if c.label == "MATERIAL"]
    assert len(materiales) == 1
    assert materiales[0].text == material and materiales[0].component_ref is None
    assert materiales[0].decision == "ACCEPTED"
    if material == "melamine":
        assert materiales[0].normalized_value == "melamina"
        assert any(w.code == "UNKNOWN_TERM" for w in r.warnings)
    assert item.primary_color.value == "blanco"
    assert item.primary_color.component_ref is None
    color = next(c for c in r.candidates if c.candidate_id in item.primary_color.evidence_ids)
    assert color.text == "blanca" and color.normalized_value == "blanco"
    assert item.secondary_color is None
    assert all(texto[c.start : c.end] == c.text for c in r.candidates)


@pytest.mark.parametrize("eje", ["ancho", "alto", "profundidad", "largo", "diametro"])
@pytest.mark.parametrize(
    "fragmento", ["un metro 20", "un metro veinte", "un metro y veinte centímetros"]
)
def test_medidas_compuestas_en_ambos_ordenes(eje, fragmento):
    for texto in [f"{fragmento} de {eje}", f"{eje} de {fragmento}"]:
        matches = find_measurements(texto, eje)
        assert len(matches) == 1
        m = matches[0]
        assert m.value == (Decimal(120), "cm")
        assert m.text == texto and m.start == 0 and m.end == len(texto)


@pytest.mark.parametrize(
    ("fragmento", "mm"),
    [
        ("dos metros treinta y cinco", "2350"),
        ("2 metros 35", "2350"),
        ("un metro y cinco centímetros", "1050"),
        ("un metro 99 cm", "1990"),
        ("nueve metros noventa y nueve centímetros", "9990"),
        ("UN METRO Y VEINTIDÓS CENTÍMETROS", "1220"),
    ],
)
def test_rango_y_aritmetica_decimal_exacta(fragmento, mm):
    texto = f"Una mesa de {fragmento} de largo."
    r = extraer(texto)
    assert [d.value_mm for d in r.item_proposal.dimensions] == [mm]
    assert all(texto[c.start : c.end] == c.text for c in r.candidates)


@pytest.mark.parametrize(
    "fragmento",
    [
        "un metro y veinte",
        "un metro cinco",
        "un metro 5",
        "un metro 100",
        "un metro 020",
        "un metro ciento veinte centímetros",
        "un metro 20 milímetros",
        "un metro 20 metros",
        "un metro 20 pulgadas",
        "un metro 0 centímetros",
        "cero metros veinte",
        "diez metros veinte",
        "dos metro veinte",
        "un metros veinte",
        "1.5 metros veinte",
        "un metro veinte y treinta centímetros",
        "dos y tres metros veinte",
    ],
)
def test_no_normalizar_resto_unidad_o_gramatica_ambiguos(fragmento):
    # También se bloquea el fallback que truncaría el prefijo o el sufijo.
    for texto in [f"{fragmento} de ancho", f"ancho de {fragmento}"]:
        assert find_measurements(texto, "ancho") == []


@pytest.mark.parametrize(
    "texto",
    [
        "Una mesa de un metro veinte",  # sin eje
        "Una mesa con veinte puertas",  # cantidad interna no dimensional
        "Una mesa de un metro y medio de ancho",  # fracción aún no soportada
        "Una mesa de dos coma cinco metros de ancho",  # decimal oral fuera del alcance
    ],
)
def test_no_inferir_dimensiones(texto):
    assert extraer(texto).item_proposal.dimensions == []


def test_cantidad_precio_y_espesores_no_se_reinterpretan():
    r = extraer(
        "Dos escritorios de un metro veinte de ancho; tapa de melamina blanca de 18 mm; "
        "precio unitario 1500 bolivianos."
    )
    item = r.item_proposal
    assert item.quantity == 2
    assert item.price.unit_price_input == "1500.00" and item.price.line_total == "3000.00"
    assert [(d.axis, d.value_mm) for d in item.dimensions] == [("ancho", "1200")]
    assert [t.value_mm for t in item.thicknesses] == ["18"]
    assert item.thicknesses[0].component_ref == item.components[0].component_id
    assert item.primary_color is None  # no propagar el color de la tapa al mueble
    assert all(
        c.component_ref == item.components[0].component_id
        for c in r.candidates
        if c.label in {"MATERIAL", "COLOR"}
    )


def test_unidad_ausente_permanece_pendiente():
    r = extraer("Un escritorio de 120 de ancho. Alto de 75 centímetros.")
    ancho = next(d for d in r.item_proposal.dimensions if d.axis == "ancho")
    assert ancho.value_mm is None and ancho.unit is None
    assert any(w.code == "MISSING_UNIT" for w in r.warnings)


@pytest.mark.parametrize(
    "texto",
    [
        "Un escritorio de melamina blanca o negra.",
        "Un escritorio de melamine blanca o azul.",
        "Un escritorio de melamina blanca, mejor azul.",
        "Un escritorio sin melamine blanca.",
        "Un escritorio con tapa de melamine blanca.",
        "Un escritorio; melamina blanca.",
        "Un escritorio de melamina, color a elección.",
    ],
)
def test_color_sin_asociacion_global_inequivoca_no_se_proyecta(texto):
    r = extraer(texto)
    assert r.item_proposal.primary_color is None
    assert r.item_proposal.secondary_color is None


def test_negacion_no_acepta_nuevos_atributos():
    r = extraer("Un escritorio sin melamine blanca.")
    attrs = [c for c in r.candidates if c.label in {"MATERIAL", "COLOR"}]
    assert len(attrs) == 2 and all(c.decision == "REJECTED" for c in attrs)


def test_melamine_no_es_coincidencia_parcial_ni_identificador():
    r = extraer("Un escritorio de melamineado blanco.")
    assert not any(c.label == "MATERIAL" for c in r.candidates)
    assert r.item_proposal.primary_color is None
    assert r.item_proposal.components == []


def test_offsets_unicode_y_datos_previos_conservados():
    texto = "¡Sí! Necesito un escritorio de melamine blanca, un metro veinte de ancho."
    r = extraer(texto)
    assert [d.value_mm for d in r.item_proposal.dimensions] == ["1200"]
    assert all(texto[c.start : c.end] == c.text for c in r.candidates)
    assert r.text_original == texto


def test_no_consumir_cantidad_interna_despues_de_metro_simple():
    r = extraer("Un escritorio de ancho un metro y dos cajones.")
    assert [(d.axis, d.value_mm) for d in r.item_proposal.dimensions] == [("ancho", "1000")]
    assert [c.normalized_value for c in r.candidates if c.label == "CANTIDAD_INTERNA"] == [2]


def test_compuesta_prefija_seguida_de_otro_eje():
    r = extraer("Un escritorio de ancho un metro veinte y alto setenta y cinco centímetros.")
    assert {d.axis: d.value_mm for d in r.item_proposal.dimensions} == {
        "ancho": "1200",
        "alto": "750",
    }


@pytest.mark.parametrize(
    "texto",
    [
        "Quiero un escritorio de 120 de ancho y 75 centímetros de alto",
        "Quiero un escritorio de ancho 120 y alto 75 cm",
        "Quiero un escritorio de 120 de ancho, 75 cm de alto",
    ],
)
def test_voz_real_no_comparte_unidad_local(texto):
    r = extraer(texto)
    dims = {d.axis: d for d in r.item_proposal.dimensions}
    assert (dims["ancho"].value, dims["ancho"].unit, dims["ancho"].value_mm) == ("120", None, None)
    assert (dims["alto"].unit, dims["alto"].value_mm) == ("cm", "750")
    assert any(w.code == "MISSING_UNIT" for w in r.warnings)
    assert len(dims["ancho"].evidence_ids) == 1


@pytest.mark.parametrize("pieza", ["etapa", "pieza desconocida", "base"])
@pytest.mark.parametrize("material", ["melamine", "melamina"])
def test_voz_real_otra_entidad_no_presta_espesor_a_cajones(pieza, material):
    texto = (
        f"Necesito un escritorio de {material} a blanca de 120 centímetros de ancho "
        f"con 2 cajones y una {pieza} de 18 milímetros de espesor"
    )
    r = extraer(texto)
    item = r.item_proposal
    assert [(d.axis, d.value_mm) for d in item.dimensions] == [("ancho", "1200")]
    assert [c.name for c in item.components] == ["cajones"]
    assert [c.normalized_value for c in r.candidates if c.label == "CANTIDAD_INTERNA"] == [2]
    assert len(item.thicknesses) == 1
    assert item.thicknesses[0].value_mm == "18"
    assert item.thicknesses[0].component_ref is None
    assert any(w.path == "/item_proposal/thicknesses" for w in r.warnings)
    assert all(texto[c.start : c.end] == c.text for c in r.candidates)


def test_voz_real_espesor_explicito_de_cajones_se_conserva():
    r = extraer("Un escritorio con 2 cajones de melamina de 18 milímetros de espesor")
    assert (
        r.item_proposal.thicknesses[0].component_ref == r.item_proposal.components[0].component_id
    )


@pytest.mark.parametrize("unidad", ["mm", "milímetros"])
def test_conflicto_seguro_espesores_no_es_otra_entidad(unidad):
    r = extraer(f"Una mesa; tapa de 18 {unidad} y 25 {unidad}")
    item = r.item_proposal
    assert [t.value_mm for t in item.thicknesses] == ["18", "25"]
    assert all(t.component_ref == item.components[0].component_id for t in item.thicknesses)
