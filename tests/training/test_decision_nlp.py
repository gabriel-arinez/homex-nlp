"""Invented inputs only; evaluate comparators without fitting models."""

from training.decision_nlp import evaluate_rows, field_errors, metrics, wilson


def test_missing_reference_never_creates_audio_accuracy():
    rows = evaluate_rows(
        [
            {
                "id": "invented-audio",
                "text": "Una mesa inventada.",
                "subset": "real_audio_asr",
                "category": "muebles_pedido",
                "entities": None,
                "expected": None,
                "reference_kind": "NO_INDEPENDENT_AUDIO_REFERENCE",
            }
        ],
        "M-A",
    )
    summary = metrics(rows)
    assert summary["commercial_n"] == 0
    assert summary["full_exact_ratio"] is None
    assert summary["raw_ner"] is None
    assert summary["ner_n"] == 0


def test_correct_negative_is_not_complete_furniture_success():
    rows = evaluate_rows(
        [
            {
                "id": "invented-negative",
                "text": "No cotices ningún mueble.",
                "subset": "invented",
                "category": "muebles_pedido",
                "entities": [],
                "expected": {
                    "status": "NO_PROPOSAL",
                    "comercial": {},
                    "especificacion": {"datos_tecnicos": {}},
                },
            }
        ],
        "M-A",
    )
    summary = metrics(rows)
    assert summary["negative_n"] == 1
    assert summary["correct_negative_abstentions"] == 1
    assert summary["positive_full_n"] == 0
    assert summary["full_exact"] == 0
    assert summary["full_exact_ratio"] is None


def test_scoped_attribute_error_is_preserved():
    wanted = {("COMP:tapa", "espesor"): ("29", "mm")}
    actual = {("COMP:patas", "espesor"): ("29", "mm")}
    errors = field_errors(wanted, actual)
    assert len(errors) == 2
    assert {e["kind"] for e in errors} == {"false_assertion", "omission"}


def test_interval_and_absence_are_not_perfect_scores():
    assert wilson(0, 0) is None
    assert wilson(0, 5)[1] > 0.4
    assert wilson(5, 5)[0] < 0.6


def test_hybrid_contract_failure_is_not_a_correct_abstention(monkeypatch):
    from types import SimpleNamespace

    import training.decision_nlp as decision
    from homex_nlp.engine import RulesEngine

    monkeypatch.setattr(
        decision,
        "instrument",
        lambda engine, request: (RulesEngine().extract(request), [], 0.0, 0.0),
    )

    def incompatible(*args):
        raise ValueError("invented incompatible evidence")

    monkeypatch.setattr(decision, "hybrid", incompatible)
    rows = decision.evaluate_rows(
        [
            {
                "id": "invented-error",
                "text": "No cotices ningún mueble.",
                "subset": "invented",
                "category": "muebles_pedido",
                "entities": [],
                "expected": {
                    "status": "NO_PROPOSAL",
                    "comercial": {},
                    "especificacion": {"datos_tecnicos": {}},
                },
            }
        ],
        "M-C",
        SimpleNamespace(model_version="invented"),
    )
    summary = decision.metrics(rows)
    assert rows[0]["result"] is None
    assert rows[0]["status"] == "ENGINE_ERROR"
    assert summary["contract_failures"] == 1
    assert summary["correct_negative_abstentions"] == 0
