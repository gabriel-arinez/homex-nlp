"""Invented malformed predictions must be scored as errors, not crash metrics."""

from training.integral_v2.project import fields


def test_measurement_like_accessory_name_is_lexical():
    expected = {
        "comercial": {},
        "especificacion": {
            "datos_tecnicos": {
                "componentes": [],
                "accesorios": ["47 mm"],
                "caracteristicas_generales": {},
            }
        },
    }
    assert fields(expected)["ACCESSORY:47 mm", "nombre"] == "47 mm"


def test_measurement_like_component_name_is_lexical():
    expected = {
        "comercial": {},
        "especificacion": {
            "datos_tecnicos": {
                "componentes": [{"uid": "invented", "nombre": "53 cm"}],
                "accesorios": [],
                "caracteristicas_generales": {},
            }
        },
    }
    assert fields(expected)["COMP:53 cm", "nombre"] == "53 cm"
