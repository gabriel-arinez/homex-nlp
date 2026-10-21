from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine


def extraer(text):
    resultado = RulesEngine().extract(
        ExtractionRequest(request_id="prf04", text=text, currency_context="BOB")
    )
    return ExtractionResult.model_validate_json(resultado.model_dump_json())


def test_cantidad_comercial_y_cajones_conservan_ambitos():
    resultado = extraer("Seis veladores con dos cajones, a 750 bolivianos por unidad")
    assert resultado.item_proposal.quantity == 6
    assert resultado.item_proposal.price.unit_price_input == "750.00"
    internos = [c for c in resultado.candidates if c.label == "CANTIDAD_INTERNA"]
    assert internos[0].normalized_value == 2
    assert internos[0].component_ref == resultado.item_proposal.components[0].component_id


def test_material_y_espesores_no_se_cruzan():
    resultado = extraer("Un escritorio; tapa de melamina MDP 25 mm; panel frontal 18 mm")
    item = resultado.item_proposal
    assert len(item.components) == 2
    assert [m.component_ref for m in item.thicknesses] == [c.component_id for c in item.components]
    materiales = [c for c in resultado.candidates if c.label == "MATERIAL"]
    assert len(materiales) == 1
    assert materiales[0].component_ref == item.components[0].component_id


def test_interno_no_se_convierte_en_cantidad_comercial():
    resultado = extraer("Escritorio con dos cajones")
    assert resultado.item_proposal.quantity is None


def test_productos_comerciales_multiples_no_proponen():
    assert extraer("Dos escritorios y tres veladores").status == "NO_PROPOSAL"


def test_escritorio_con_cajonera_no_es_multiproducto():
    assert extraer("Un escritorio con cajonera").status == "REQUIRES_REVIEW"


def test_moneda_dictada_distinta_no_se_convierte_silenciosamente():
    resultado = extraer("Dos escritorios a 100 USD por unidad")
    assert resultado.item_proposal.price is None
    assert any(w.code == "UNSUPPORTED_CURRENCY" for w in resultado.warnings)
    assert any(c.label == "PRECIO" and c.decision == "REJECTED" for c in resultado.candidates)


def test_conjunto_explicito_solo_si_contiene_componentes():
    resultado = extraer("Un escritorio, conjunto inferior: tapa de 25 mm; panel frontal 18 mm")
    grupos = [c for c in resultado.candidates if c.label == "CONJUNTO"]
    assert len(grupos) == 1
    miembros = [c for c in resultado.candidates if c.label == "COMPONENTE"]
    assert all(
        c.normalized_value == {"conjunto_ref": grupos[0].normalized_value["group_id"]}
        for c in miembros
    )


def test_unidades_habladas_compartidas_en_enumeracion_explicita():
    resultado = extraer("Seis veladores, 45 ancho, 45 profundo, 60 alto centímetros")
    dims = {d.axis: (d.value, d.unit, d.value_mm) for d in resultado.item_proposal.dimensions}
    assert dims == {
        "ancho": ("45", "cm", "450"),
        "profundidad": ("45", "cm", "450"),
        "alto": ("60", "cm", "600"),
    }
    assert not any(w.code == "MISSING_UNIT" for w in resultado.warnings)


def test_dimensiones_adicionales_y_ambito_explicito_de_pieza():
    resultado = extraer("Una mesa de largo 250 cm, diámetro 180 cm; tapa de 43 cm de ancho")
    dims = {d.axis: d for d in resultado.item_proposal.dimensions}
    assert dims["largo"].value == "250"
    assert dims["diametro"].value == "180"
    assert dims["ancho"].component_ref == resultado.item_proposal.components[0].component_id


def test_mesada_no_es_otra_mesa_comercial_y_rieles_se_conservan():
    resultado = extraer("Un mueble con mesada de 25 mm, rieles telescópicos")
    assert resultado.status == "REQUIRES_REVIEW"
    assert any(a.name == "rieles telescópicos" for a in resultado.item_proposal.accessories)
