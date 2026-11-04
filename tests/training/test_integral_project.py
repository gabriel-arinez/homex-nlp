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


def test_unbacked_predicted_group_is_not_projected():
    from training.integral_v2.project import project

    result = {
        "text_original": "Invented fixture",
        "warnings": [],
        "item_proposal": {
            "name": "mesa inventada",
            "quantity": None,
            "components": [{"component_id": "c1", "name": "tapa"}],
            "accessories": [],
            "dimensions": [],
            "thicknesses": [],
            "price": None,
        },
        "candidates": [
            {
                "label": "COMPONENTE",
                "decision": "ACCEPTED",
                "normalized_value": {"conjunto_ref": "unbacked"},
                "component_ref": "c1",
            }
        ],
    }
    reference = project(result)
    assert "conjunto_uid" not in reference["especificacion"]["datos_tecnicos"]["componentes"][0]
    assert reference["especificacion"]["datos_tecnicos"]["advertencias"]
    assert fields(reference)
