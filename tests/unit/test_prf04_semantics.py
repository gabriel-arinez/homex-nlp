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


def test_mesa_reunion_relaciones_prf04():
    resultado = extraer(
        "Mesa de reunión para 10 personas, "
        "tablero melamínico de 18 milímetros de grosor; "
        "mesón engrosado a 27 milímetros; "
        "estructura con tablero melamínico; "
        "tapacanto PVC y dos tomacorrientes al centro; "
        "color a elección; precio total 7.300"
    )

    item = resultado.item_proposal
    assert resultado.status == "REQUIRES_REVIEW"
    assert item.name == "Mesa de reunión para 10 personas"
    assert item.furniture_type_candidate == "mesa de reunión"
    assert item.quantity is None
    assert item.price.line_total == "7300.00"
    assert [pieza.name.lower() for pieza in item.components] == ["tablero", "mesón", "estructura"]
    assert [medida.component_ref for medida in item.thicknesses] == [
        item.components[0].component_id,
        item.components[1].component_id,
    ]
    assert any(
        accesorio.quantity == 2 and "tomacorrientes" in accesorio.name.lower()
        for accesorio in item.accessories
    )
    assert any("tapacanto" in accesorio.name.lower() for accesorio in item.accessories)
    assert item.observations == "color a elección"


def test_ruido_asr_no_inventa_componentes():
    resultado = extraer(
        "Mesa de reunión para 10 personas, "
        "tablero menamínico de 18 milímetros, "
        "me sona engrosado a 27 milímetros, "
        "tapa canto en plume vc y dos tomas corrientes al centro, "
        "estructura con tablero menamínico, "
        "color elección, precio total 7.300"
    )

    item = resultado.item_proposal
    assert item.quantity is None
    assert item.furniture_type_candidate == "mesa de reunión"
    assert all(pieza.name.lower() != "tapa" for pieza in item.components)
    assert item.thicknesses[0].component_ref is not None
    assert item.thicknesses[1].component_ref is None
    assert any(
        accesorio.quantity == 2 and "tomas corrientes" in accesorio.name.lower()
        for accesorio in item.accessories
    )
    assert item.observations == "color elección"


def test_ambitos_respetan_comas_y_decimales():
    for decimal in ("18.5", "18,5"):
        resultado = extraer(
            f"Un escritorio, tablero melamínico de {decimal} mm, superficie auxiliar de 27 mm"
        )

        item = resultado.item_proposal

        assert item is not None
        assert len(item.thicknesses) == 2
        assert item.thicknesses[0].value == "18.5"
        assert item.thicknesses[0].component_ref is not None
        assert item.thicknesses[1].component_ref is None


def test_componentes_distintos_con_comas_conservan_espesores():
    resultado = extraer("Un escritorio con tablero de 18.5 mm, estructura de 27 mm")

    item = resultado.item_proposal

    assert item is not None
    assert len(item.components) == 2
    assert len(item.thicknesses) == 2

    assert item.thicknesses[0].component_ref == (item.components[0].component_id)
    assert item.thicknesses[1].component_ref == (item.components[1].component_id)


def test_transcripciones_reales_208_209():
    textos = (
        "Mesa de reunión para 10 personas, tamaño 2.40 metros de largo "
        "por 1.20 metros de ancho por 0.80 metros de alto tablero "
        "melamínico de 18 milímetros de grosor, mesón engrosado a "
        "27 milímetros, tapacanto en PVC y dos tomacorrientes al centro, "
        "estructura en tablero melamínico, color a elección, "
        "precio total 7.300",
        "Mesa de reunión para 10 personas tamaño 2.40 metros de largo "
        "por 1.20 metros de ancho por 0.80 metros de alto, tablero "
        "melamínico de 18 milímetros de grosor me son engrosado a "
        "27 milímetros, tapacanto en PVC y 2 tomacorrientes al centro, "
        "estructura en tablero melamínico, color a elección total 7300",
    )

    for texto in textos:
        resultado = extraer(texto)
        item = resultado.item_proposal

        assert item is not None
        assert resultado.status == "REQUIRES_REVIEW"
        assert item.quantity is None
        assert item.price.line_total == "7300.00"
        assert item.observations == "color a elección"

        assert [p.name.casefold() for p in item.components] == ["tablero", "mesón", "estructura"]

        assert [m.value_mm for m in item.thicknesses] == ["18", "27"]
        assert [m.component_ref for m in item.thicknesses] == [
            item.components[0].component_id,
            item.components[1].component_id,
        ]

        accesorios = [a.name for a in item.accessories]
        assert "tapacanto en PVC" in accesorios
        assert "tapacanto en PVC y" not in accesorios

        assert any(a.quantity == 2 and "tomacorrientes" in a.name for a in item.accessories)

        assert not any(w.code == "CONFLICTING_VALUES" for w in resultado.warnings)

        if "me son engrosado" in texto:
            alias = [
                c
                for c in resultado.candidates
                if c.label == "COMPONENTE" and c.normalized_value == "mesón"
            ]
            assert len(alias) == 1
            assert alias[0].text == "me son"
            assert texto[alias[0].start : alias[0].end] == "me son"
            assert any(
                w.code == "UNKNOWN_TERM" and "me son" in w.message for w in resultado.warnings
            )


def test_alias_asr_no_se_activa_fuera_del_contexto():
    resultado = extraer("Una mesa donde me son útiles dos tableros de madera")

    assert resultado.item_proposal is not None
    assert not any(c.name == "mesón" for c in resultado.item_proposal.components)
    assert not any(w.code == "UNKNOWN_TERM" and "me son" in w.message for w in resultado.warnings)
