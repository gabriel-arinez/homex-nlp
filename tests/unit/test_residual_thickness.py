"""Material gauges need linguistic context and retain review boundaries."""

import pytest
from test_residual_dimensions import extract


@pytest.mark.parametrize(
    "text,values",
    [
        ("Mesa de melamina de dieciocho de espesor", ["18"]),
        ("Mesa de melamina de 18", ["18"]),
        ("Melamina de 18 y mesón engrosado a 25", ["18", "25"]),
        ("Tablero MDF de 15", ["15"]),
        ("Tapacanto de 2 milímetros", ["2"]),
        ("Vidrio templado de 6", ["6"]),
    ],
)
def test_exact_fragments_and_wrapped_gauges(text, values):
    for raw in (
        text,
        "Una " + text.lower() if text.startswith("Mesa") else "Una mesa con " + text.lower(),
    ):
        result = extract(raw)
        gauges = [c for c in result.candidates if c.label == "ESPESOR"]
        assert [
            c.normalized_value["value"]
            if isinstance(c.normalized_value, dict)
            else c.normalized_value[0]
            for c in gauges
        ] == values
        if result.item_proposal:
            assert [m.value_mm for m in result.item_proposal.thicknesses] == values
            assert all(c.decision == "UNRESOLVED" for c in gauges if "milímetros" not in c.text)
        else:
            assert result.status == "NO_PROPOSAL"


@pytest.mark.parametrize(
    "tail",
    [
        "melamina modelo 18",
        "melamina a 18 bolivianos",
        "18 tableros MDF",
        "tapacanto de 2 metros de largo",
        "vidrio de 60 de ancho",
        "melamina de 120",
    ],
)
def test_non_gauges_are_not_promoted(tail):
    assert not extract("Una mesa con " + tail).item_proposal.thicknesses


def test_accessory_gauge_never_becomes_parent_board():
    result = extract(
        "Una mesa con tablero de melamina de 18 milímetros y tapacanto de 2 milímetros"
    )
    gauge = next(c for c in result.candidates if c.label == "ESPESOR" and c.text == "2 milímetros")
    assert gauge.decision == "UNRESOLVED"
    assert gauge.reason and "accessory" in gauge.reason.lower()
    assert next(m for m in result.item_proposal.thicknesses if m.value == "2").component_ref is None
