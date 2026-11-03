import pytest

from homex_nlp.catalog import CatalogRequest, CatalogValue, extract_catalog

VALUES = [
    CatalogValue(id=1, concept="COLOR", code="NEGRO", name="Negro"),
    CatalogValue(id=2, concept="COLOR", code="AZUL", name="Azul"),
    CatalogValue(id=3, concept="MATERIAL_PISO", code="HDF", name="HDF"),
]


def extract(category, text):
    return extract_catalog(CatalogRequest(category=category, text=text, values=VALUES))


def test_chair_homex_features():
    r = extract("SILLA", "nombre: Silla B15b; modelo: B15b; color negro, malla, apoyo lumbar")
    assert r.fields["modelo"] == "B15b"
    assert r.fields["color_primario"] == 1
    assert r.fields["especificaciones"]["material_respaldo"] == "malla"
    for e in r.evidence:
        assert (
            e.text
            == "nombre: Silla B15b; modelo: B15b; color negro, malla, apoyo lumbar"[e.start : e.end]
        )


def test_floor_homex_hdf():
    r = extract("PISO_FLOTANTE", "HDF de 8mm de espesor. COD: NA9118. largo 1,2 metros")
    assert r.fields["material"] == 3
    assert r.fields["espesor_mm"] == "8"
    assert r.fields["largo_mm"] == "1200.0"
    assert r.fields["modelo"] == "NA9118"


def test_other_no_rigid_product_profile():
    r = extract("OTRO", "nombre: Zócalo; descripción: alto tráfico de 80mm x 15mm. 7 barras")
    assert r.fields["nombre"] == "Zócalo"
    assert "espesor_mm" not in r.fields
    assert "cantidad" not in r.fields


def test_negation_correction_and_ambiguity():
    assert "color_primario" not in extract("SILLA", "negro o azul").fields
    assert extract("SILLA", "no negro, azul").fields["color_primario"] == 2
    assert extract("SILLA", "negro, mejor azul").fields["color_primario"] == 2
    assert "especificaciones" not in extract("SILLA", "sin apoyo lumbar").fields


@pytest.mark.parametrize("category", ["PISO_FLOTANTE", "OTRO"])
def test_isolation(category):
    r = extract(category, "color negro con apoyo lumbar y malla")
    assert "color_primario" not in r.fields
    assert "especificaciones" not in r.fields


def test_unknown_catalog_no_invention():
    r = extract("SILLA", "marca inexistente color turquesa stock 66 precio total 343200")
    assert not r.fields
    assert r.unrecognized


def test_price_is_suggestion_not_total():
    r = extract("OTRO", "precio unitario 1.750,00. total 12250,00. existencias 7")
    assert r.fields["precio_lista"] == "1750.00"
    assert "stock" not in r.fields
    assert r.warnings


def test_explicit_category_required():
    with pytest.raises(ValueError):
        CatalogRequest(category="MUEBLE", text="silla")


def test_word_measures_and_money_reuse_common_parser():
    r = extract("PISO_FLOTANTE", "espesor ocho mm; precio unitario ciento veinticinco bolivianos")
    assert r.fields["espesor_mm"] == "8"
    assert r.fields["precio_lista"] == "125.00"


@pytest.mark.parametrize("category", ["SILLA", "PISO_FLOTANTE", "OTRO"])
def test_spoken_name_without_punctuation(category):
    r = extract(category, "nombre producto de prueba modelo B15 color negro")
    assert r.fields["nombre"] == "producto de prueba"


def test_commercial_decimal_and_box_area_are_separate():
    values = [CatalogValue(id=4, concept="UNIDAD_MEDIDA", code="M2", name="Metro cuadrado")]
    r = extract_catalog(
        CatalogRequest(
            category="PISO_FLOTANTE",
            text="cantidad 52,50 metros cuadrados, 2,25 m2 por caja; espesor ocho milímetros",
            values=values,
        )
    )
    assert r.fields["unidad_stock"] == 4
    assert r.fields["m2_por_caja"] == "2.25"
    assert r.fields["espesor_mm"] == "8"
    assert "cantidad" not in r.fields


@pytest.mark.parametrize(
    "text",
    ["modelo B quince", "modelo NA nueve uno uno ocho", "modelos B15", "Nombres ergonómicos"],
)
def test_no_partial_labels_or_spoken_codes(text):
    r = extract("SILLA", text)
    assert "modelo" not in r.fields
    assert "nombre" not in r.fields


def test_natural_chair_and_two_colors():
    text = "Silla ergonómica de malla con apoyabrazos regulables y asiento de espuma inyectada. Color negro con azul. Modelo B15b."
    r = extract("SILLA", text)
    assert r.fields["nombre"] == "Silla ergonómica"
    assert r.fields["color_primario"] == 1
    assert r.fields["color_secundario"] == 2
    assert r.fields["modelo"] == "B15b"
    assert r.fields["especificaciones"]["brazos_regulables"] == "apoyabrazos regulables"
    assert r.fields["observaciones"] == text
    for e in r.evidence:
        assert e.text == text[e.start : e.end]


@pytest.mark.parametrize(
    "text", ["negro o azul", "negro, azul", "no negro con azul", "negro, mejor azul"]
)
def test_secondary_color_needs_combination_evidence(text):
    assert "color_secundario" not in extract("SILLA", text).fields


def test_natural_floor_spoken_dimensions_and_box_yield():
    r = extract(
        "PISO_FLOTANTE",
        "Piso flotante Ganesha, HDF, espesor doce milímetros, largo ciento veinte centímetros, ancho veinte centímetros, dos coma veinticinco metros cuadrados por caja. Cantidad cincuenta cajas, total seis mil bolivianos.",
    )
    assert r.fields["nombre"] == "Piso flotante Ganesha"
    assert r.fields["espesor_mm"] == "12"
    assert r.fields["largo_mm"] == "1200"
    assert r.fields["ancho_mm"] == "200"
    assert r.fields["m2_por_caja"] == "2.25"
    assert "precio_lista" not in r.fields
    assert "stock" not in r.fields


def test_other_literal_specifications_not_floor_fields():
    text = "Zócalo de alto tráfico de 80mm x 15mm. Cada barra de 2,44 metros lineales. Precio unitario cincuenta bolivianos."
    r = extract("OTRO", text)
    assert r.fields["nombre"] == "Zócalo de alto tráfico"
    assert r.fields["observaciones"] == text
    assert r.fields["precio_lista"] == "50.00"
    assert "espesor_mm" not in r.fields


@pytest.mark.parametrize(
    "text",
    [
        "espesor doce o quince mm",
        "espesor menos ocho mm",
        "cantidad veinte metros cuadrados",
        "largo ciento veinte",
        "dos metros cuadrados",
    ],
)
def test_uncertain_measurements_are_not_fabricated(text):
    r = extract("PISO_FLOTANTE", text)
    assert not {"espesor_mm", "largo_mm", "m2_por_caja"} & r.fields.keys()


def test_natural_code_without_label_and_rectified_measure():
    r = extract("PISO_FLOTANTE", "Piso flotante NA9118. espesor ocho mm, corrijo espesor doce mm")
    assert r.fields["modelo"] == "NA9118"
    assert r.fields["espesor_mm"] == "12"


def test_decomposed_unicode_catalog_offsets_are_original():
    text = "Silla cafe\u0301, color azul"
    r = extract("SILLA", text)
    c = next(e for e in r.evidence if e.label == "color_primario")
    assert c.text == "azul"
    assert text[c.start : c.end] == "azul"


def test_chair_materials_are_not_assigned_to_the_wrong_component():
    r = extract(
        "SILLA",
        "Silla de espera. Espaldar de espuma de alta densidad. Asiento de malla. Cuerpo de nylon de alta resistencia.",
    )
    specs = r.fields["especificaciones"]
    assert specs["material_respaldo"] == "Espaldar de espuma de alta densidad"
    assert "asiento" not in specs
    assert "base" not in specs


def test_reverse_word_dimensions_and_negated_correction():
    r = extract(
        "PISO_FLOTANTE",
        "ciento veinte centímetros de largo. sin espesor ocho mm, mejor espesor doce mm",
    )
    assert r.fields["largo_mm"] == "1200"
    assert r.fields["espesor_mm"] == "12"


@pytest.mark.parametrize("marker", ["corrijo", "mejor", "perdón"])
def test_explicit_name_rectification(marker):
    r = extract("SILLA", f"nombre Silla, {marker} nombre Sillón")
    assert r.fields["nombre"] == "Sillón"
    assert any(e.decision == "REJECTED" for e in r.evidence if e.label == "nombre")


def test_ambiguous_model_retains_unresolved_literal_evidence():
    r = extract("SILLA", "modelo B quince")
    assert "modelo" not in r.fields
    assert any(e.text == "B quince" and e.decision == "UNRESOLVED" for e in r.evidence)
