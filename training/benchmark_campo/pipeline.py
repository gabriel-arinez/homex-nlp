"""Private ingest, independent review, leakage and deterministic aggregate scoring."""

import hashlib
import json
import os
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from training.benchmark_campo import metrics
from training.benchmark_campo.models import Batch
from training.corpus_v2_rc2.review import field_digest, import_decisions
from training.evaluar_campo_prf04 import palabras

ROOT = Path(__file__).resolve().parents[2]
MARK = "SINTETICO_SOLO_PRUEBA_NO_WER_REAL"


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def digest(data):
    return hashlib.sha256(canonical(data).encode()).hexdigest()


def in_git(path):
    probe = path.resolve()
    while not probe.exists():
        probe = probe.parent
    return (
        subprocess.run(
            [
                "git",
                "-C",
                str(probe if probe.is_dir() else probe.parent),
                "rev-parse",
                "--is-inside-work-tree",
            ],
            capture_output=True,
        ).returncode
        == 0
    )


def private_path(path):
    if in_git(path):
        raise ValueError("PRIVATE_PATH_MUST_BE_OUTSIDE_GIT")


def write_private(path, data):
    private_path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.stat().st_mode & 0o077:
        raise ValueError("PRIVATE_DIRECTORY_REQUIRES_0700")
    # O_EXCL also rejects symlink and accidental overwrite of human decisions.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(canonical(data))


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("NONFINITE_JSON")

    return json.loads(path.read_text(), object_pairs_hook=unique, parse_constant=nonfinite)


@dataclass
class Combined:
    batches: list

    @property
    def sessions(self):
        return [s for b in self.batches for s in b.sessions]

    @property
    def frozen_date(self):
        return max(b.frozen_date for b in self.batches)

    def model_dump(self, **kwargs):
        return {"batches": [b.model_dump(**kwargs) for b in self.batches]}


def combine(batches):
    sessions = [s for b in batches for s in b.sessions]
    if len({s.session_id for s in sessions}) != len(sessions):
        raise ValueError("DUPLICATE_SESSION_ACROSS_BATCHES")
    if len({b.batch_id for b in batches}) != len(batches):
        raise ValueError("DUPLICATE_BATCH")
    return batches[0] if len(batches) == 1 else Combined(batches)


def load(path):
    parsed = read_json(path)
    batch = Batch.model_validate_json(json.dumps(parsed))
    if any(s.source_type == "ASR_REAL" for s in batch.sessions):
        private_path(path)
        if os.environ.get("CI"):
            raise ValueError("REAL_DATA_FORBIDDEN_IN_CI")
        if path.stat().st_mode & 0o077 or path.parent.stat().st_mode & 0o077:
            raise ValueError("PRIVATE_PERMISSIONS_REQUIRED")
    return batch


def review_kit(batch):
    result = []
    for s in batch.sessions:
        for field, value in (
            ("reference", s.reference.model_dump(mode="json") if s.reference else None),
            ("consent", s.consent.model_dump(mode="json")),
            ("independence", s.provenance.model_dump(mode="json")),
        ):
            record = {
                "record_id": s.session_id,
                "field_path": field,
                "text_sha256": digest(
                    {
                        "asr": s.asr.model_dump(),
                        "audio": s.audio.model_dump() if s.audio else None,
                        "case_id": s.case_id,
                        "batch_id": s.batch_id,
                    }
                ),
                "before": None,
                "after": value,
            }
            record["field_sha256"] = field_digest(record)
            record["review_id"] = digest(record)[:20]
            result.append(
                record
                | {
                    "decision": "",
                    "reviewer": "",
                    "attestation_id": "",
                    "reviewed_at": "",
                    "comment": "",
                }
            )
    return result


def verified(batch, decisions, authorized):
    if not decisions:
        return set()
    kit = review_kit(batch)
    ledger = import_decisions(kit, decisions, authorized)
    # No promotion of all references just because a reviewer ID is present.
    return {
        (r["record_id"], k["field_path"])
        for r in ledger["fields"]
        for k in kit
        if k["review_id"] == r["review_id"] and r["gold_eligible_field"]
    }


def baseline_rows():
    """Already exposed development/V1/RC1/RC2 text, read-only and never gold."""
    files = list((ROOT / "data/corpus").glob("*.jsonl"))
    files += list((ROOT / "data/candidates").glob("corpus_v2_rc*/corpus/**/*.jsonl"))
    for directory in ("04_CORPUS_DOCUMENTAL_V2", "05_CORPUS_ORAL_V2"):
        files += list((ROOT / "data/candidates/corpus_v2_rc1" / directory).glob("*.jsonl"))
    # Discover canonical RC2 development layout without scanning arbitrary private data.
    files += list((ROOT / "data/candidates").glob("corpus_v2_rc*/development_v2/**/*.jsonl"))
    for path in sorted(set(files)):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if isinstance(row, dict) and isinstance(row.get("text"), str):
                yield {"text": row["text"], "case_id": row.get("id"), "partition": "DEVELOPMENT"}


def leakage(batch, opened=()):
    refs = list(baseline_rows()) + list(opened)
    findings = defaultdict(int)
    seen = []
    for s in batch.sessions:
        target_texts = {" ".join(palabras(s.asr.text))}
        if s.reference and s.reference.faithful:
            target_texts.add(" ".join(palabras(s.reference.faithful.text)))
        current = {
            "text": s.asr.text,
            "case_id": s.case_id,
            "source_id": s.provenance.source_id,
            "template_id": s.provenance.template_id,
            "speaker_id": s.provenance.speaker_id,
            "partition": s.provenance.partition,
            "audio_sha256": s.audio.sha256 if s.audio else None,
        }
        for other in refs + seen:
            other_text = " ".join(palabras(other.get("text", "")))
            ot = set(palabras(other_text))
            same_case = any(
                current[k] == other.get(k)
                for k in ("case_id", "source_id", "template_id", "speaker_id")
            )
            same_audio = current["audio_sha256"] and current["audio_sha256"] == other.get(
                "audio_sha256"
            )
            if same_audio:
                findings["same_dictation_audio"] += 1
            if other_text in target_texts:
                findings["duplicate_text"] += 1
            elif any(
                tokens and ot and len(tokens & ot) / len(tokens | ot) >= 0.8
                for tokens in (set(palabras(text)) for text in target_texts)
            ):
                findings["possible_paraphrase_jaccard_0_8"] += 1
            if same_case:
                findings["shared_provenance_requires_adjudication"] += 1
            if (same_case or same_audio or other_text in target_texts) and current[
                "partition"
            ] != other.get("partition"):
                findings["cross_partition_overlap"] += 1
        seen.append(current)
    return {
        "findings": dict(sorted(findings.items())),
        "status": "REQUIRES_HUMAN_ADJUDICATION"
        if findings
        else "NO_AUTOMATIC_MATCH_NOT_PROOF_OF_INDEPENDENCE",
        "baseline_rows": len(refs),
        "paraphrase_detection": "lexical screening only; independent human semantic/access review required",
    }


def engine_key(engine):
    metadata = engine.model_dump(exclude={"ner", "commercial", "text_sha256"})
    return "ENGINE-" + digest(metadata)[:16] + ":" + engine.coordinate


def score(batch, decisions=(), authorized=(), opened=(), private_detail=False):
    verified_fields = verified(batch, decisions, authorized)
    groups = {}
    details = []
    for source in ("ASR_REAL", "SINTETICO_PRUEBA"):
        rows = [s for s in batch.sessions if s.source_type == source]
        wer = []
        ner = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
        ner_n = defaultdict(int)
        fields = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        com_n, critical_n, errors = defaultdict(int), defaultdict(int), defaultdict(int)
        latencies = defaultdict(list)
        eligible_productivity = []
        for s in rows:
            synthetic = source == "SINTETICO_PRUEBA"
            approved = synthetic or (
                (s.session_id, "reference") in verified_fields
                and s.reference
                and s.reference.review_status == "human_verified"
                and s.reference.arbitration == "RESOLVED"
            )
            consent_ok = synthetic or (s.session_id, "consent") in verified_fields
            r = s.reference if approved and consent_ok else None
            if r and r.faithful:
                w = metrics.alignment(r.faithful.text, s.asr.text)
                wer.append(w)
                details.append({"session_id": s.session_id, "wer": w})
            else:
                details.append({"session_id": s.session_id, "wer": metrics.wer_counts(0, 0, 0, 0)})
            for e in s.engines:
                key = engine_key(e)
                if (
                    r
                    and r.ner
                    and r.ner.coverage == "complete"
                    and e.ner
                    and r.ner.coordinate == e.ner.coordinate
                    and r.ner.text_sha256 == e.ner.text_sha256
                ):
                    ner_n[key] += 1
                    for label, counts in metrics.ner_counts(r.ner.spans, e.ner.spans).items():
                        ner[key][label] = [a + b for a, b in zip(ner[key][label], counts)]
                if r and r.commercial:
                    counts, err, den = metrics.commercial_counts(r.commercial, e.commercial)
                    com_n[key] += 1
                    errors[key] += err
                    critical_n[key] += den
                    for field, cs in counts.items():
                        for name, value in cs.items():
                            fields[key][field][name] += value
            if consent_ok:
                for t in s.timings:
                    key = ":".join((t.metric, s.temperature, s.hardware_class, s.condition))
                    latencies[key].append((t.end - t.start) / (1000 if t.unit == "ms" else 1))
                eligible_productivity.append(s.productivity)
        engine_keys = sorted({engine_key(e) for s in rows for e in s.engines})
        groups[source] = {
            "status": "NO_DISPONIBLE"
            if not rows
            else MARK
            if source == "SINTETICO_PRUEBA"
            else "DECLARED_REAL_EXTERNAL_VERIFICATION_REQUIRED",
            "sessions": len(rows),
            "wer_sessions": len(wer),
            "wer_micro": metrics.wer_counts(
                *(sum(w[k] for w in wer) for k in ("S", "D", "I", "N"))
            ),
            "ner": {k: metrics.ner_report(ner[k], ner_n[k]) for k in engine_keys},
            "commercial": {
                k: metrics.commercial_report(fields[k], errors[k], critical_n[k], com_n[k])
                for k in engine_keys
            },
            "latency_seconds": {k: metrics.stats(v) for k, v in sorted(latencies.items())},
            "productivity": metrics.productivity(eligible_productivity),
            "excluded_unverified_consent": len(rows) - len(eligible_productivity),
        }
    leaks = leakage(batch, opened)
    rules = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(
            list(Path(__file__).parent.glob("*.py"))
            + [
                ROOT / "training/evaluar_campo_prf04.py",
                ROOT / "training/corpus_v2_rc2/review.py",
                ROOT / "uv.lock",
            ]
        )
    }
    report = {
        "schema_version": "field-report-1",
        "status": "BENCHMARK_HERRAMIENTAS_VERIFICABLES",
        "HUMAN_GOLD": "NO",
        "external_holdout": "HOLDOUT_EXTERNO_SIN_MUESTRAS",
        "groups": groups,
        "leakage": leaks,
        "seal": {
            "candidate_content_digest": digest(batch.model_dump(mode="json")),
            "authorized_content_digest": digest(batch.model_dump(mode="json"))
            if all(
                s.source_type == "SINTETICO_PRUEBA" or (s.session_id, "consent") in verified_fields
                for s in batch.sessions
            )
            else None,
            "scoring_rules_digest": digest(rules),
            "partition_digest": digest([s.provenance.model_dump() for s in batch.sessions]),
            "date": batch.frozen_date.isoformat(),
            "classification": "CANDIDATE_NOT_BLIND_EXTERNAL",
            "human_independence_access_verified": sum(
                (s.session_id, "independence") in verified_fields for s in batch.sessions
            ),
        },
        "methods": {
            "wer": "legacy palabras: Unicode regex word tokens, casefold; punctuation removed, no number/word rewriting; Levenshtein ties diagonal/delete/insert; empty reference NOT_EVALUABLE with I retained",
            "ner": "exact label/start/end on same coordinate and text hash; undefined ratios null; macro over defined label F1",
            "commercial": "exact Decimal, axis field + unit; no currency conversion; wrong value counts omission and false assertion; complete refs include predicted-only negatives; partial only reviewed_keys",
            "latency": "seconds; p50 median, p95 nearest rank ceil(.95*n), max; shared clock; cold/warm/hardware/condition strata",
            "productivity": "same independent case, validated task completion, paired manual minus assisted; incomplete excluded; order recorded",
            "causes": "externally supplied evidence IDs only; discrepancy alone never establishes cause",
        },
        "declared_cause_counts_not_verified": {
            cause: sum(s.diagnosis.cause == cause for s in batch.sessions)
            for cause in ("ASR", "NLP", "projection", "UI", "human_review", "unknown")
        },
        "privacy": "aggregate contains no literals, private paths, IDs, engine versions or field values; seal hashes bind private inputs; external verification remains HOMEX responsibility",
        "training": False,
    }
    if private_detail:
        report["PRIVATE_DETAIL_DO_NOT_PUBLISH"] = {
            "sessions": [s.model_dump(mode="json") for s in batch.sessions],
            "per_session": details,
        }
    return report
