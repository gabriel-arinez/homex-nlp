"""Independent reference proposals must never become acoustic ground truth."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "reference_annotations", Path(__file__).parents[2] / "tools/annotate_real_voice.py"
)
annotations = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(annotations)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("dos mil novecientos", 2900),
        ("treinta y seis", 36),
        ("uno coma cinco", 1.5),
        ("2.400,50", 2400.5),
        ("ciento treinta y cinco", 135),
        ("desconocido", None),
        ("veinticinco", 25),
        ("mil noventa", 1090),
    ],
)
def test_independent_numbers(text, expected):
    assert annotations.number(text) == expected


def test_reference_distinguishes_document_script_and_asr():
    result = annotations.annotate(
        "Dos mesas de un metro cuarenta de largo. Precio unitario de dos mil bolivianos.",
        "document",
        "",  # document proposals cannot enter spoken denominator
    )
    assert all(not f["eligible_script_denominator"] for f in result)
    script = annotations.annotate(
        "Dos mesas de un metro cuarenta de largo. Precio unitario de dos mil bolivianos.",
        "script",
        "Dos mesas de 1.40 de largo. Precio de 2.000 bolivianos.",
    )
    price = next(f for f in script if f["field"] == "price" and f["value"])
    assert price["value"] == 2000
    assert price["modality"] == "UNIT"
    assert price["currency"] == "BOB"
    assert price["acoustic_status"] == "PENDING_HUMAN_LISTENING"
    assert price["verification_status"] == "SCRIPT_EVIDENCE_VERIFIED"
    assert next(f for f in script if f["field"] == "quantity")["value"] == 2


def test_all_evidence_offsets_and_residual_clauses_are_lossless():
    text = "Una mesa roja. Mesón engrosado a veintisiete, con pieza desconocida."
    fields = annotations.annotate(text, "script", text)
    for field in fields:
        for evidence in field["evidence"]:
            assert text[evidence["start"] : evidence["end"]] == evidence["raw"]
    residuals = [f for f in fields if f["field"] == "technical_description"]
    assert "".join(f["evidence"][0]["raw"] for f in residuals) == text
    assert all(not f["eligible_script_denominator"] for f in residuals)
    assert {f["field"] for f in fields} >= set(annotations.FIELDS)


def test_component_dimensions_never_invent_an_axis_or_association():
    text = "Cajonera de treinta y tres por cuarenta por sesenta y tres centímetros."
    fields = annotations.annotate(text, "script", "")
    dims = [f for f in fields if f["field"] == "dimensions"]
    assert dims and all(not f["eligible_script_denominator"] for f in dims)
    assert all(f["association"]["status"] == "UNRESOLVED" for f in dims)
    assert all(f["axis"] is None for f in dims)


def test_grouping_joins_family_and_source_overlap_transitively():
    rows = [
        {"id": "A", "grupo_familia": "F", "archivo_origen": "x", "registros_fuente": [1]},
        {"id": "B", "grupo_familia": "F", "archivo_origen": "x", "registros_fuente": [2]},
        {"id": "C", "grupo_familia": "G", "archivo_origen": "x", "registros_fuente": [2]},
        {"id": "D", "grupo_familia": "H", "archivo_origen": "x", "registros_fuente": [3]},
    ]
    groups = annotations.leakage_groups(rows)
    assert groups["A"] == groups["B"] == groups["C"]
    assert groups["A"] != groups["D"]


def test_output_directory_cannot_overwrite_existing_history(tmp_path):
    tmp_path.joinpath("output").mkdir()
    with pytest.raises(FileExistsError):
        annotations.prepare_output(tmp_path / "output")


def test_document_only_total_without_currency_is_not_spoken_price():
    fields = annotations.annotate("precio unitario 4200,00. total 8400,00.", "document", "")
    prices = [f for f in fields if f["field"] == "price" and f["value"]]
    assert [(f["value"], f["modality"], f["currency"]) for f in prices] == [
        (4200.0, "UNIT", None),
        (8400.0, "TOTAL", None),
    ]
    assert all(not f["eligible_script_denominator"] for f in prices)


def test_explicit_absence_is_distinct_from_unsupported_parser_match():
    fields = annotations.annotate("Una mesa roja.", "script", "")
    price = next(f for f in fields if f["field"] == "price")
    dimension = next(f for f in fields if f["field"] == "dimensions")
    assert price["absence_status"] == "NOT_STATED"
    assert dimension["absence_status"] == "UNSUPPORTED_OR_UNPARSED_NOT_CONFIRMED_ABSENT"


def test_literal_scalar_denominators_do_not_verify_component_relations():
    fields = annotations.annotate(
        "Tablero de melamina de veinticinco milímetros. Ochenta centímetros de ancho. Dos puertos USB.",
        "script",
        "",
    )
    for name in ("materials", "thicknesses", "dimensions", "accessories"):
        field = next(f for f in fields if f["field"] == name and f["value"])
        assert field["eligible_script_denominator"]
        assert field["verification_scope"] == "LITERAL_OR_SCALAR_ONLY"
        assert field["association"]["status"] == "UNRESOLVED"
    usb = next(f for f in fields if f["field"] == "accessories" and f["value"] == "usb")
    assert usb["count_proposal"] == 2
    assert usb["count_unit"] == "units"
    assert usb["count_status"] == "LITERAL_COUNT_VERIFIED_ASSOCIATION_PENDING"


@pytest.mark.parametrize(
    "text", ["setenta y cinco y sesenta", "treinta y un dos", "dos tres", "y un"]
)
def test_coordinated_or_invalid_cardinals_abstain(text):
    assert annotations.number(text) is None


@pytest.mark.parametrize(
    "text",
    [
        "Lados de un metro treinta y un metro sesenta.",
        "Profundidades de setenta y cinco y sesenta centímetros.",
        "Cajonera de treinta y tres por cuarenta por sesenta y tres centímetros.",
    ],
)
def test_ambiguous_measure_chains_never_propose_partial_scalars(text):
    fields = annotations.annotate(text, "script", "")
    dimensions = [f for f in fields if f["field"] == "dimensions"]
    assert dimensions
    assert all(f["value"] is None for f in dimensions)
    assert all(not f["eligible_script_denominator"] for f in dimensions)


def test_explicit_compound_metres_are_normalized_without_association():
    fields = annotations.annotate("Armario de dos metros diez de alto.", "script", "")
    dims = [f for f in fields if f["field"] == "dimensions"]
    assert len(dims) == 1
    assert dims[0]["value"] == 210
    assert dims[0]["unit"] == "cm"
    assert dims[0]["axis"] == "alto"
    assert dims[0]["association"]["status"] == "UNRESOLVED"
    assert dims[0]["evidence"][0]["raw"] == "dos metros diez de alto"
    assert not dims[0]["eligible_acoustic_denominator"]


def test_conjunction_between_complete_axis_measures_is_not_inside_cardinal():
    fields = annotations.annotate(
        "Dos metros de largo y ochenta centímetros de ancho.", "script", ""
    )
    dims = [f for f in fields if f["field"] == "dimensions"]
    assert [(f["value"], f["unit"], f["axis"]) for f in dims] == [
        (2, "m", "largo"),
        (80, "cm", "ancho"),
    ]
    assert all(f["eligible_script_denominator"] for f in dims)
