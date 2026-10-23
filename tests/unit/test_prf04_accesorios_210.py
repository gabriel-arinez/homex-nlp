"""Regresión de la transcripción real PRF-04, captura 210."""

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine
from homex_nlp.rules import find_accessories

TEXTO_210 = (
    "Mesa de reunión para 10 personas tamaño 2.4 metros de largo "
    "por 1.20 metros de ancho por 0.80 metros de alto tablero "
    "melamínico de 18 milímetros de grosor mesón engrosado a "
    "27 milímetros tapacanto en PVC y 2 tomacorrientes al centro "
    "de estructura en tablero melamínico color a elección "
    "precio total 7.300"
)


def test_accesorios_sin_preposicion_huerfana():
    encontrados = find_accessories(TEXTO_210)

    pvc = next(a for a in encontrados if "tapacanto" in a.text.lower())
    tomas = next(a for a in encontrados if "tomacorrientes" in a.text.lower())

    assert pvc.text == "tapacanto en PVC"
    assert tomas.text == "tomacorrientes al centro"
    assert tomas.value == 2

    for accesorio in encontrados:
        assert TEXTO_210[accesorio.start : accesorio.end] == accesorio.text


def test_pipeline_conserva_componentes_y_accesorios_210():
    resultado = RulesEngine().extract(
        ExtractionRequest(
            request_id="regresion-210",
            text=TEXTO_210,
            currency_context="BOB",
        )
    )

    assert resultado.status == "REQUIRES_REVIEW"
    item = resultado.item_proposal
    assert item is not None

    assert item.quantity is None
    assert item.price.line_total == "7300.00"

    assert [c.name.lower() for c in item.components] == [
        "tablero",
        "mesón",
        "estructura",
    ]

    assert [m.value_mm for m in item.thicknesses] == [
        "18",
        "27",
    ]

    nombres = [a.name.lower() for a in item.accessories]
    assert "tapacanto en pvc" in nombres
    assert any(
        a.quantity == 2 and a.name.lower().endswith("tomacorrientes al centro")
        for a in item.accessories
    )
    assert not any(nombre.endswith(" de") for nombre in nombres)

    assert item.observations == "color a elección"

    for evidencia in resultado.candidates:
        assert TEXTO_210[evidencia.start : evidencia.end] == evidencia.text


def test_otros_accesorios_conservan_descripciones_validas():
    casos = [
        ("rieles telescópicos", "rieles telescópicos"),
        ("tapacanto en PVC", "tapacanto en PVC"),
        ("tomacorrientes al centro", "tomacorrientes al centro"),
        ("pasacable de", "pasacable"),
    ]

    for texto, esperado in casos:
        encontrados = find_accessories(texto)
        assert len(encontrados) == 1
        assert encontrados[0].text == esperado
