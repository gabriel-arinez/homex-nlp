"""Reporting predicates do not treat missed names or review needs as successes."""

from tools.report_commercial_differential import commercial_payload, probe_outcome


def probe(**updates):
    return {
        "expected_name": "prueba",
        "expected_proposal": True,
        "expected_review": "AMBIGUOUS_COMMERCIAL_NAME",
        **updates,
    }


def test_name_match_does_not_mask_missing_human_review():
    result = probe_outcome(probe(), {"fields": {"nombre": "prueba"}})
    assert result["name_correct"] and result["proposal_correct"]
    assert not result["review_correct"]


def test_abstention_is_not_counted_as_a_correct_positive_name():
    result = probe_outcome(probe(), {"fields": {}})
    assert not result["name_correct"] and not result["proposal_correct"]


def test_unrequested_fields_do_not_count_as_abstention():
    result = probe_outcome(
        probe(expected_name=None, expected_proposal=False, expected_review=None),
        {"fields": {"precio_lista": "350"}},
    )
    assert result["name_correct"] and not result["proposal_correct"]


def test_payload_keeps_associations_and_evidence_but_not_time_or_engine_version():
    raw = {
        "item_proposal": {"dimensions": [{"component_ref": "c1", "value": "20"}]},
        "evidence": [{"start": 1, "decision": "UNRESOLVED"}],
        "engine": {"library_version": "0.1.29"},
        "latency_nlp_ms": 6,
    }
    payload = commercial_payload(raw)
    assert payload["item_proposal"] == raw["item_proposal"]
    assert payload["evidence"] == raw["evidence"]
    assert "engine" not in payload and "latency_nlp_ms" not in payload
