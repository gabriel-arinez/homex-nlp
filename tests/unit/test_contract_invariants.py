import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from homex_nlp.contracts.input import ExtractionRequest, TranscriptionResult, TranscriptSegment
from homex_nlp.contracts.review import ReviewComparison
from homex_nlp.resources import load_furniture_profiles
from homex_nlp.settings import RuntimeSettings


def test_transcript_must_match_extraction_text_exactly() -> None:
    transcript = TranscriptionResult(
        text_original="Un escritorio",
        language="es",
        model_version="whisper-example",
        segments=[TranscriptSegment(start_seconds="0", end_seconds="1.2", text="Un escritorio")],
        duration_seconds="1.2",
    )
    with pytest.raises(ValidationError, match="transcripción original exacta"):
        ExtractionRequest(
            request_id="r-1",
            text="un escritorio",
            currency_context="BOB",
            transcription=transcript,
        )


def test_profile_resource_stays_unconfigured_and_non_blocking() -> None:
    profiles = load_furniture_profiles()
    assert profiles.status == "UNCONFIGURED"
    assert profiles.profiles == {}


def test_settings_are_explicit_and_paths_are_absolute() -> None:
    settings = RuntimeSettings.from_environment({"HOMEX_NLP_MODE": "RULES_ONLY"})
    assert settings.nlp_mode == "RULES_ONLY"

    with pytest.raises(ValidationError, match="rutas deben ser absolutas"):
        RuntimeSettings(
            nlp_mode="HYBRID",
            ner_model_path=Path("model"),
            ner_model_sha256="a" * 64,
        )


def test_hybrid_requires_model_and_hash() -> None:
    with pytest.raises(ValidationError, match="HYBRID requiere"):
        RuntimeSettings(nlp_mode="HYBRID")


def test_review_precision_without_denominator_is_null() -> None:
    valid = ReviewComparison(
        metric_version="1",
        evaluable_fields=0,
        corrected_fields=0,
        added_fields=0,
        removed_fields=0,
        field_precision=None,
        item_equal=None,
    )
    assert valid.field_precision is None

    with pytest.raises(ValidationError, match="precisión debe ser null"):
        ReviewComparison(
            metric_version="1",
            evaluable_fields=0,
            corrected_fields=0,
            added_fields=0,
            removed_fields=0,
            field_precision="1.0",
            item_equal=True,
        )


def test_all_resources_declare_schema_and_resource_versions() -> None:
    resource_dir = Path(__file__).resolve().parents[2] / "src" / "homex_nlp" / "resources"
    for name in ("labels.json", "units.json", "vocabulary.json", "patterns.json"):
        content = json.loads((resource_dir / name).read_text(encoding="utf-8"))
        assert content["schema_version"] == "1.0"
        assert content["resource_version"] == "1.0"
