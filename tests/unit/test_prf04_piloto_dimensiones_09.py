"""Regresiones de profundidad de superficie dictada."""

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def test_piloto_09_profundidad_cubierta():
    texto = "Dos escritorios en L, profundidad de cubierta de 0.60 metros y altura de 0.74 metros"
    resultado = RulesEngine().extract(
        ExtractionRequest(request_id="p09", text=texto, currency_context="BOB")
    )
    assert resultado.status == "REQUIRES_REVIEW"
    profundidad = [m for m in resultado.item_proposal.dimensions if m.axis == "profundidad"]
    assert len(profundidad) == 1
    assert profundidad[0].value_mm == "600.00"
    assert profundidad[0].original_text == "profundidad de cubierta de 0.60 metros"


def test_profundidad_sin_unidad_no_se_infiere():
    resultado = RulesEngine().extract(
        ExtractionRequest(
            request_id="p10",
            text="Un atril, 0.50 de profundidad y 0.48 metros de ancho",
            currency_context="BOB",
        )
    )
    profundidad = [m for m in resultado.item_proposal.dimensions if m.axis == "profundidad"]
    assert len(profundidad) == 1
    assert profundidad[0].value_mm is None
    assert any(a.code == "MISSING_UNIT" for a in resultado.warnings)
