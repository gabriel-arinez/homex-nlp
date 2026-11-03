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
