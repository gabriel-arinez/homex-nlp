"""Synthetic-only regression gates for the offline ASR→NLP bridge."""

from types import SimpleNamespace

import pytest

from training.audio_pilot.dataset import PilotError
from training.audio_pilot.nlp_replay import _safe_record, evaluate_run


def _asr_run(text="Un escritorio, precio unitario de 800 bolivianos"):
    ids = [f"{n:02d}" for n in range(1, 21)]
    return {
        "schema_version": "audio-pilot-run-1",
        "status": "ASR_EXECUTED",
        "input": {"dataset_digest": "synthetic-data"},
        "quality_digest": "synthetic-quality",
        "provenance": {"code_commit": "synthetic-asr-commit"},
        "records": [
            {"id": number, "status": "OK", "audio_sha256": number * 32, "text": text}
            for number in ids
        ],
    }


class FakeRequest:
    def __init__(self, *, request_id, text, currency_context):
        self.request_id = request_id
        self.text = text
        self.currency_context = currency_context


class FakeEngine:
    def extract(self, request):
        return SimpleNamespace(
            model_dump=lambda **_: {
                "status": "REQUIRES_REVIEW",
                "text_original": request.text,
                "item_proposal": {"name": "escritorio"},
                "candidates": [],
            }
        )


def test_replay_20_synthetic_records_preserves_evidence():
    run = _asr_run()
    summary, cases = evaluate_run(run, FakeEngine(), FakeRequest, currency="BOB")
    assert summary["cases"] == 20
    assert summary["statuses"] == {
        "REQUIRES_REVIEW": 20,
        "NO_PROPOSAL": 0,
        "ERROR": 0,
    }
    assert summary["WER"] == "N/A"
    assert summary["PROMOCION"] == "NO"
    assert summary["historical_attempt_binding"] == "NOT_VERIFIED"
    assert cases[0]["result"]["text_original"] == run["records"][0]["text"]
    assert cases[0]["audio_sha256"] == run["records"][0]["audio_sha256"]


@pytest.mark.parametrize("bad_status", ["ASR_PARTIAL_FAILURE", "ASR_NO_EJECUTADO"])
def test_rejects_incomplete_run(bad_status):
    run = _asr_run()
    run["status"] = bad_status
    with pytest.raises(PilotError, match="ASR_RUN_INCOMPLETE"):
        evaluate_run(run, FakeEngine(), FakeRequest, currency="BOB")


def test_rejects_transcription_mismatch():
    result = SimpleNamespace(
        model_dump=lambda **_: {"status": "REQUIRES_REVIEW", "text_original": "inventado"}
    )
    case = _asr_run()["records"][0]
    with pytest.raises(PilotError, match="NLP_TRANSCRIPT_EVIDENCE_MISMATCH"):
        _safe_record(result, case)


def test_rejects_unfinished_case():
    run = _asr_run()
    run["records"][4]["status"] = "ERROR"
    with pytest.raises(PilotError, match="ASR_RUN_HAS_ERRORS"):
        evaluate_run(run, FakeEngine(), FakeRequest, currency="BOB")


def test_rejects_extra_case():
    run = _asr_run()
    run["records"].append(run["records"][-1].copy())
    with pytest.raises(PilotError, match="ASR_RUN_MEMBERSHIP_MISMATCH"):
        evaluate_run(run, FakeEngine(), FakeRequest, currency="BOB")


def test_no_promotion_on_abstention():
    class AbstainingEngine:
        def extract(self, request):
            return SimpleNamespace(
                model_dump=lambda **_: {
                    "status": "NO_PROPOSAL",
                    "text_original": request.text,
                    "item_proposal": None,
                    "candidates": [],
                }
            )

    summary, details = evaluate_run(_asr_run(), AbstainingEngine(), FakeRequest, currency="BOB")
    assert summary["statuses"]["NO_PROPOSAL"] == 20
    assert summary["PROMOCION"] == "NO"
    assert all(item["result"]["item_proposal"] is None for item in details)
