import copy
import json
import shutil
from hashlib import sha256
from pathlib import Path

import pytest

from training.closure_v2.audit import audit
from training.closure_v2.experiment import latency, metrics
from training.closure_v2.oral import validate


def oral(identifier="ORAL-001"):
    text = "Mesa azul"
    return {
        "id": identifier,
        "text": text,
        "text_sha256": sha256(text.encode()).hexdigest(),
        "origin": "SINTETICO_ORAL",
        "split": "train",
        "source_case_id": "case-1",
        "paraphrase_group_id": "para-1",
        "template_id": "template-1",
        "parent_record_id": "parent",
        "session_id": None,
        "speaker_id": None,
        "audio_sha256": None,
        "authorization_ref": None,
        "retention_policy_ref": None,
        "privacy_review_ref": None,
        "human_review_ref": None,
        "human_transcription_from_audio": False,
        "entities": [(0, 4, "PRODUCTO")],
        "phenomena": ["direct"],
    }


def test_baseline_has_no_public_test_detail_and_is_immutable():
    paths = list(Path("data/corpus").glob("*.jsonl")) + list(Path("data/splits").glob("*.json"))
    before = {str(p): p.read_bytes() for p in paths}
    report, review = audit()
    assert report["records"] == 675
    assert report["splits"] == {"train": 483, "dev": 94, "test": 98}
    assert not report["formal_errors"]
    assert len(review) == 577
    assert all(r["split"] in {"train", "dev"} and "text" not in r for r in review)
    assert before == {str(p): p.read_bytes() for p in paths}


def test_audit_detects_changed_seal_and_cross_partition_parent(tmp_path):
    shutil.copytree("data", tmp_path / "data")
    path = tmp_path / "data/corpus/sillas.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["text_sha256"] = "0" * 64
    other = next(r for r in rows if r["split"] != rows[0]["split"])
    rows[0]["family_id"] = other["family_id"]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    report, _ = audit(tmp_path / "data")
    assert report["formal_errors"]["unsealed_or_hash"] == 1
    assert report["formal_errors"]["text_hash"] == 1
    assert report["cross_split_groups"]["family_id"] > 0


def test_oral_valid_synthetic_is_not_real_or_gold():
    result = validate([oral()], {"PRODUCTO"}, {"parent": "train"})
    assert result["synthetic"] == 1 and result["real"] == 0 and result["wer"] is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("text_sha256", "0" * 64),
        ("origin", "TRANSCRIPCION_HUMANA"),
        ("origin", "ASR_REAL"),
        ("audio_sha256", "a" * 64),
        ("entities", [(False, 4, "PRODUCTO")]),
        ("entities", [(0, 3, "PRODUCTO")]),
        ("entities", [(0, 4, "INVENTED")]),
        ("split", "external_test"),
        ("human_transcription_from_audio", True),
        ("unexpected", "secret"),
    ],
)
def test_oral_rejects_invalid_or_falsely_real_input(field, value):
    row = oral()
    row[field] = value
    with pytest.raises(ValueError):
        validate([row], {"PRODUCTO"}, {"parent": "train"})


@pytest.mark.parametrize("parents", [{}, {"parent": "test"}, {"parent": "dev"}])
def test_oral_protects_unknown_and_test_parents(parents):
    with pytest.raises(ValueError, match="PROTECTED_OR_UNKNOWN_PARENT"):
        validate([oral()], {"PRODUCTO"}, parents)


@pytest.mark.parametrize(
    "key",
    [
        "source_case_id",
        "paraphrase_group_id",
        "template_id",
        "session_id",
        "speaker_id",
        "audio_sha256",
        "text_sha256",
    ],
)
def test_oral_rejects_cross_split_groups(key):
    a = oral()
    a.update(
        origin="ASR_REAL",
        parent_record_id=None,
        session_id="session-1",
        speaker_id="speaker-1",
        audio_sha256="a" * 64,
        authorization_ref="ACT-1",
        retention_policy_ref="RET-1",
        privacy_review_ref="PRIV-1",
    )
    b = copy.deepcopy(a)
    b.update(
        id="ORAL-002",
        split="dev",
        source_case_id="case-2",
        paraphrase_group_id="para-2",
        template_id="template-2",
        session_id="session-2",
        speaker_id="speaker-2",
        audio_sha256="b" * 64,
        text="Mesa verde",
    )
    b["text_sha256"] = sha256(b["text"].encode()).hexdigest()
    if key == "text_sha256":
        b["text"] = a["text"]
    b[key] = a[key]
    with pytest.raises(ValueError, match="CROSS_SPLIT_GROUP"):
        validate([a, b], {"PRODUCTO"}, {})


def test_oral_rejects_obvious_pii():
    row = oral()
    row["text"] = "Mesa cliente@example.com"
    row["text_sha256"] = sha256(row["text"].encode()).hexdigest()
    with pytest.raises(ValueError, match="POTENTIAL_PERSONAL_DATA"):
        validate([row], {"PRODUCTO"}, {"parent": "train"})


def test_metrics_penalize_false_positives_and_do_not_reward_empty_labels():
    report = metrics(
        [{(0, 4, "PRODUCTO")}],
        [{(0, 4, "PRODUCTO"), (5, 9, "COLOR")}],
        {"PRODUCTO", "COLOR", "ALTO"},
    )
    assert report["micro"]["tp"] == 1 and report["micro"]["fp"] == 1
    assert report["micro"]["f1"] == pytest.approx(2 / 3)
    assert report["by_label"]["ALTO"]["f1"] is None
    assert report["macro"]["f1"]["value"] == 0.5
    assert latency([1, 2, 3, 4, 5])["p95_ms"] == 5
    with pytest.raises(ValueError, match="UNEQUAL_DOCUMENTS"):
        metrics([set()], [], set())


def test_curation_is_reversible_and_excludes_test():
    from training.closure_v2.curate import patches

    text = "Membrana protectora incluida con el piso"
    start = text.index("incluida")
    row = {
        "id": "SYN-001",
        "split": "train",
        "origin": "SINTETICO",
        "text": text,
        "text_sha256": sha256(text.encode()).hexdigest(),
        "entities": [[start, len(text), "ACCESORIO"]],
    }
    original = copy.deepcopy(row)
    patch = patches(row)
    assert row == original
    assert patch["entities_before"] == row["entities"]
    assert patch["entities_after"] == [[0, len(text), "ACCESORIO"]]
    assert patch["origin"] == "SINTETICO" and not patch["human_reviewed"]
    row["split"] = "test"
    assert patches(row) is None


def test_curation_preserves_ambiguous_money_without_guessing():
    from training.closure_v2.curate import patches

    row = {
        "id": "SYN-001",
        "split": "dev",
        "origin": "SINTETICO",
        "text": "descuento de línea Bs 1.500",
        "text_sha256": "a" * 64,
        "entities": [],
    }
    row["text_sha256"] = sha256(row["text"].encode()).hexdigest()
    fact = patches(row)["technical_facts"][0]
    assert fact["kind"] == "AMBIGUOUS_DISCOUNT_LITERAL_REQUIRES_REVIEW"
    assert "value" not in fact
    row["text"] = "descuento de línea Bs 1.500,00"
    row["text_sha256"] = sha256(row["text"].encode()).hexdigest()
    assert patches(row)["technical_facts"][0]["value"] == "1500.00"


def test_all_generated_patches_have_valid_unicode_token_boundaries():
    import spacy

    from training.closure_v2.curate import build
    from training.corpus import read_jsonl

    source = {
        r["id"]: r
        for path in Path("data/corpus").glob("*.jsonl")
        for _, r in read_jsonl(path)
        if r["split"] != "test"
    }
    tokenizer = spacy.blank("es")
    result = build()
    assert result["records_reviewed_mechanically"] == 577
    assert result["entity_patch_records"] == 49
    for overlay in result["records"]:
        row = source[overlay["parent_record_id"]]
        assert row["text_sha256"] == overlay["parent_sha256"]
        doc = tokenizer.make_doc(row["text"])
        for start, end, _ in overlay["entities_after"] or []:
            assert doc.char_span(start, end, alignment_mode="strict") is not None
        for fact in overlay["technical_facts"]:
            assert row["text"][fact["start"] : fact["end"]] == fact["literal"]


def test_oral_cli_withholds_malformed_private_input(tmp_path, monkeypatch, capsys):
    import sys

    from training.closure_v2.oral import main

    path = tmp_path / "private.jsonl"
    path.write_text(json.dumps("private@example.com") + "\n")
    monkeypatch.setattr(sys, "argv", ["oral", str(path)])
    assert main() == 2
    output = capsys.readouterr().out
    assert "private@example.com" not in output
    assert "INVALID_ORAL_INPUT" in output
