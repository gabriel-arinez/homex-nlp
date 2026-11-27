from decimal import Decimal

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine

CASES = [
    (
        "Un gavetero de tres cajones de 50 centímetros de ancho, 45 de profundidad y un metro de alto, fabricado en tablero de melamina de 18 milímetros con tapacantos de PVC, tres cajones con rieles telescopicos, jaladores metálicos y chapa de seguridad, color sapelli, garantía de un año, precio de 1100 bolivianos.",
        "45",
        "450",
    ),
    (
        "Un estante de 70 centímetros de ancho, 40 de profundidad y 2 metros de alto, fabricado en tablero melamínico nobopan de 18 milímetros de espesor con tapacantos de PVC, incluye múltiples puertas y espacios abiertos según diseño, color a elección garantía de un año precio de 2100 bolivianos",
        "40",
        "400",
    ),
    (
        "Un escritorio gerencial con credenza, escritorio de 2 metros de ancho, 80 centímetros de alto y 80 de profundidad, credenza de 1 metro 65 de ancho, 65 centímetros de alto y 60 de profundidad, melamina de 18 y 36 milímetros con tapacantos de PVC, cuatro repisas laterales, pasacables sobre el mesón y faldón hasta el piso, credenza con dos cajones superiores y espacio inferior para archivadores de palanca con puertas, chapa de seguridad, jaladores metálicos y rieles telescópicos, color a elección, precio de 7 mil bolivianos.",
        "80",
        "800",
    ),
]


@pytest.mark.parametrize("text,value,value_mm", CASES)
def test_same_owner_elliptical_depth_is_reviewable_cm(text, value, value_mm):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="s4-elliptical", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(text[c.start : c.end] == c.text for c in result.candidates)
    depth = next(
        d for d in result.item_proposal.dimensions if d.axis == "profundidad" and d.value == value
    )
    assert depth.unit == "cm"
    assert Decimal(depth.value_mm) == Decimal(value_mm)
    inferred = [
        c
        for c in result.candidates
        if c.candidate_id in depth.evidence_ids
        and isinstance(c.normalized_value, dict)
        and c.normalized_value.get("unit_inferred") is True
    ]
    assert inferred and all(c.decision == "UNRESOLVED" for c in inferred)
    assert all(c.candidate_id in result.item_proposal.unresolved for c in inferred)
    assert any(w.code == "MISSING_UNIT" and w.severity == "REVIEW" for w in result.warnings)
