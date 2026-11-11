"""Four-cell evaluation must not promote partial references into acoustic gold."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "semantic_voice", Path(__file__).parents[2] / "tools/evaluate_semantic_voice.py"
)
evaluator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluator)


def reference(field, value, **kwargs):
    return dict(
        field=field,
        value=value,
        unit=None,
        axis=None,
        currency=None,
        modality=None,
        eligible_script_denominator=True,
        association={"status": "UNRESOLVED"},
        evidence=[],
        **kwargs,
    )


def test_scoring_deduplicates_mentions_and_excludes_pending_relations():
    refs = [reference("materials", "melamina"), reference("materials", "melamina")]
    refs += [dict(reference("name", "mesa"), eligible_script_denominator=False)]
    result = evaluator.score(refs, [{"field": "materials", "value": "melamina"}])
    assert result["denominator"] == 1
    assert result["numerator"] == 1
    assert result["association_denominator"] == 0
    assert result["confirmed_false_positives"] is None


def test_unmatched_predictions_are_candidates_not_confirmed_false_positives():
    result = evaluator.score([reference("quantity", 2)], [dict(field="quantity", value=3)])
    assert result["numerator"] == 0
    assert len(result["false_positive_candidates"]) == 1
    assert result["confirmed_false_positives"] is None


def test_explicit_measure_unit_equivalence_preserves_axis():
    ref = reference("dimensions", 80)
    ref.update(unit="cm", axis="altura")
    actual = [dict(field="dimensions", value=800, unit="mm", axis="alto")]
    assert evaluator.score([ref], actual)["numerator"] == 1
    actual[0]["axis"] = "ancho"
    assert evaluator.score([ref], actual)["numerator"] == 0


def test_strict_metric_has_offsets_and_never_repairs_bad_asr():
    raw = "Precio de dos mil bolivianos y modelo ene a nueve."
    normalized, changes = evaluator.strict_normalize(raw)
    assert "2000" in normalized
    assert "modelo ene a nueve" in normalized
    for change in changes:
        assert raw[change["start"] : change["end"]] == change["raw"]
    assert evaluator.strict_normalize("setenta y cinco y sesenta centímetros")[0].startswith(
        "setenta y cinco y sesenta"
    )
    assert evaluator.edit_counts(["a", "b"], ["a"])["errors"] == 1


def test_resume_identity_mismatch_fails_before_overwriting(tmp_path):
    evaluator.check_identity(tmp_path, {"source": "one"}, False)
    with pytest.raises(ValueError, match="identity"):
        evaluator.check_identity(tmp_path, {"source": "two"}, True)
    assert evaluator.check_identity(tmp_path, {"source": "one"}, True) is None


def test_catalog_observations_do_not_count_as_extracted_materials():
    raw = {
        "category": "SILLA",
        "fields": {"observaciones": "melamina USB rojo", "precio_lista": "2000.00"},
        "evidence": [],
    }
    predicted = evaluator.predictions(raw, [])
    assert not any(p["field"] == "materials" for p in predicted)
    assert next(p for p in predicted if p["field"] == "price")["value"] == "2000.00"


def test_field_abstention_and_wrong_value_are_distinct():
    refs = [reference("quantity", 2)]
    missing = evaluator.score(refs, [])["by_field"]["quantity"]
    wrong = evaluator.score(refs, [dict(field="quantity", value=3)])["by_field"]["quantity"]
    assert missing["abstentions"] == 1 and missing["mismatches"] == 0
    assert wrong["abstentions"] == 0 and wrong["mismatches"] == 1


def test_price_qualifiers_are_separate_from_scalar_recall():
    ref = reference("price", 2000)
    ref.update(currency="BOB", modality="UNIT")
    result = evaluator.score(
        [ref], [dict(field="price", value=2000, currency="USD", modality="TOTAL")]
    )
    assert result["numerator"] == 1
    assert {r["qualifier"]: r["outcome"] for r in result["qualifier_results"]} == {
        "currency": "MISMATCH",
        "modality": "MISMATCH",
    }


def test_prediction_adapter_reads_color_value_and_floor_numeric_contract():
    raw = {"item_proposal": {"primary_color": {"value": "blanco", "evidence_ids": ["c1"]}}}
    assert evaluator.predictions(raw, []) == [{"field": "colors", "value": "blanco"}]
    predicted = evaluator.predictions(
        {
            "category": "PISO_FLOTANTE",
            "fields": {"espesor_mm": "8", "ancho_mm": "200", "largo_mm": "1200"},
        },
        [],
    )
    assert (
        evaluator.score([dict(reference("thicknesses", 8), unit="mm")], predicted)["numerator"] == 1
    )
    assert {p.get("axis") for p in predicted if p["field"] == "dimensions"} == {"ancho", "largo"}


def test_supported_denominator_does_not_require_furniture_fields_from_other_catalog():
    refs = [reference("quantity", 2), reference("materials", "melamina"), reference("price", 900)]
    score = evaluator.score_supported(refs, [{"field": "price", "value": 900}], "OTRO")
    assert score["denominator"] == score["numerator"] == 1
    assert score["unsupported_verified_reference_indices"] == [0, 1]
