"""Evidencia versionada del cierre sistémico F09 para el artefacto 0.1.0."""

from __future__ import annotations

import json
import re
from pathlib import Path

import homex_nlp

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs" / "integration-system-v0.1.0.json"
SHA256 = re.compile(r"[0-9a-f]{64}")
GIT_SHA = re.compile(r"[0-9a-f]{40}")


def load_evidence() -> dict:
    return json.loads(EVIDENCE.read_text())


def test_system_evidence_identifies_the_pinned_artifact_and_contract() -> None:
    evidence = load_evidence()
    artifact = evidence["artifact"]
    contract = evidence["contract"]

    assert evidence["evidence_schema"] == "1.0"
    assert artifact["name"] == "homex-nlp"
    assert artifact["version"] == homex_nlp.__version__ == "0.1.0"
    assert artifact["source_commit"] == "b5fe2921320c9031f6d44dc5c91a18411daa393e"
    assert GIT_SHA.fullmatch(artifact["source_commit"])
    assert artifact["wheel_filename"] == "homex_nlp-0.1.0-py3-none-any.whl"
    assert artifact["wheel_sha256"] == (
        "cfacc3a987f6158f43934cb64304fa50ea3e577cfa576f3db1e6d2a9576d19e6"
    )
    assert SHA256.fullmatch(artifact["wheel_sha256"])
    assert contract == {
        "schema_version": "1.0",
        "engine_mode": "RULES_ONLY",
        "python": "3.11",
        "asr_runtime": "faster-whisper==1.2.1",
    }


def test_system_evidence_keeps_nlp_outside_commercial_authority() -> None:
    evidence = load_evidence()
    boundaries = evidence["boundaries"]

    assert boundaries == {
        "nlp_is_commercial_authority": False,
        "hitl_approves_proforma": False,
        "historical_audio_retained": False,
        "redis_is_source_of_truth": False,
        "postgresql_is_commercial_authority": True,
    }
    assert evidence["verified_flow"] == [
        "Vue",
        "Django",
        "PostgreSQL/outbox",
        "Redis",
        "Celery",
        "faster-whisper",
        "homex-nlp",
        "propuesta",
        "HITL",
        "persistencia comercial",
    ]


def test_system_evidence_is_anchored_to_immutable_revisions_and_green_ci() -> None:
    system = load_evidence()["system_evidence"]

    assert system["frontend_commit"] == "57c32d3aa2c2e46fbcc7136f6a90995b67c664ea"
    assert system["backend_commit"] == "0659dc553af15b2125fad9b4ac0579669916e77b"
    assert GIT_SHA.fullmatch(system["frontend_commit"])
    assert GIT_SHA.fullmatch(system["backend_commit"])
    assert system["frontend_ci_run"] == "36328986617"
    assert system["frontend_ci_jobs"] == "11/11"
    assert system["backend_ci_run"] == "36333805267"
    assert system["backend_ci_jobs"] == "10/10"
    assert system["real_e2e"] == "2 passed"
