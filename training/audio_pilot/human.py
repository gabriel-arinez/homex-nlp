"""Private append-only human listening ledger; never authenticates a human identity."""

import hashlib
import io
import json
import os
import re
import subprocess
import tempfile
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from training.benchmark_campo.models import ID, SHA, Strict
from training.benchmark_campo.pipeline import digest, review_kit, score
from training.benchmark_campo.pipeline import load as load_batch
from training.benchmark_campo.pipeline import write_private as benchmark_write_private
from training.evaluar_campo_prf04 import palabras

from .dataset import IDS, PilotError, read_safe, validate, validated_audio
from .export import export_batch
from .runner import load_run, private_directory, provenance

PROTOCOL = "human-listening-1"
NORMALIZER = "pr23-casefold-unicode-word-1"


def require(condition):
    if not condition:
        raise PilotError("BLOCKED_EXTERNAL_OR_INVALID_REVIEW")


def write_private(path, data):
    path = Path(path).absolute()
    require(".." not in path.parts)
    require(not any(p.is_symlink() for p in [path, *path.parents]))
    benchmark_write_private(path, data)


class Event(Strict):
    schema_version: Literal["human-listening-event-1"] = "human-listening-event-1"
    dataset_digest: SHA
    protocol: Literal["human-listening-1"] = PROTOCOL
    normalizer: Literal["pr23-casefold-unicode-word-1"] = NORMALIZER
    previous: SHA
    id: Literal[*IDS]
    audio_sha256: SHA
    action: Literal["DRAFT", "SUBMITTED", "ADJUDICATED", "APPROVED"]
    reviewer: ID
    session: ID
    origin: Literal["heard_audio", "SYNTHETIC_TEST_ONLY"]
    timestamp: str
    text: str = Field(max_length=50000)
    note: str = Field(max_length=10000)
    explicit: bool
    uncertain: bool

    @model_validator(mode="after")
    def stamp(self):
        require(datetime.fromisoformat(self.timestamp).tzinfo is not None)
        return self


def private_read(path):
    path = Path(path).absolute()
    require(".." not in path.parts)
    from training.benchmark_campo.pipeline import private_path

    private_path(path)
    require(not any(p.is_symlink() for p in [path, *path.parents]))
    require(not path.stat().st_mode & 0o077 and not path.parent.stat().st_mode & 0o077)

    # Enforce no-follow on every ancestor and duplicate-key rejection from PR23.
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result)
            result[key] = value
        return result

    return json.loads(
        read_safe(path.parent, path.name, 16 * 1024 * 1024),
        object_pairs_hook=unique,
        parse_constant=lambda _: require(False),
    )


def initialize(dataset, directory, *, synthetic=False):
    manifest = validate(dataset, synthetic=synthetic)
    require(synthetic or not os.environ.get("CI"))
    output = private_directory(directory)
    write_private(
        output / "project.json",
        {
            "manifest": manifest,
            "protocol": PROTOCOL,
            "normalizer": NORMALIZER,
            "evaluator": provenance(),
        },
    )


def replay(project, events):
    require(set(project) == {"manifest", "protocol", "normalizer", "evaluator"})
    manifest = project["manifest"]
    require(project["protocol"] == PROTOCOL and project["normalizer"] == NORMALIZER)
    require(digest(manifest["entries"]) == manifest["dataset_digest"])
    require([e["id"] for e in manifest["entries"]] == list(IDS))
    hashes = {e["id"]: e["audio_sha256"] for e in manifest["entries"]}
    states = {
        case: {"reads": {}, "resolved": None, "approvals": {}, "status": "DRAFT"} for case in IDS
    }
    previous = digest(project)
    for raw in events:
        require(set(raw) == set(Event.model_fields))
        e = Event.model_validate(raw)
        require(e.previous == previous and e.dataset_digest == manifest["dataset_digest"])
        require(e.audio_sha256 == hashes[e.id])
        require(
            e.origin
            == (
                "SYNTHETIC_TEST_ONLY"
                if manifest["source_type"] == "SINTETICO_SOLO_PRUEBA"
                else "heard_audio"
            )
        )
        state = states[e.id]
        require(state["status"] != "APPROVED")
        key = e.session
        if e.action in {"DRAFT", "SUBMITTED"}:
            require(state["resolved"] is None)
            old = state["reads"].get(key)
            require(old is None or (old["reviewer"] == e.reviewer and old["action"] == "DRAFT"))
            require(key in state["reads"] or len(state["reads"]) < 2)
            if e.action == "SUBMITTED":
                require(e.explicit and bool(e.text.strip()))
            state["reads"][key] = raw
            submitted = [r for r in state["reads"].values() if r["action"] == "SUBMITTED"]
            state["status"] = (
                "DISAGREEMENT"
                if len(submitted) == 2 and submitted[0]["text"] != submitted[1]["text"]
                else "SUBMITTED"
                if submitted
                else "DRAFT"
            )
        elif e.action == "ADJUDICATED":
            reads = list(state["reads"].values())
            require(len(reads) == 2 and all(r["action"] == "SUBMITTED" for r in reads))
            require(not state["approvals"] and e.explicit and bool(e.note.strip()))
            require(bool(e.text.strip()) and not e.uncertain)
            require(not any(r["uncertain"] for r in reads) or "RESUELTO" in e.note)
            state["resolved"] = raw
            state["status"] = "ADJUDICATED"
        else:
            resolved = state["resolved"]
            require(resolved is not None and e.explicit and bool(e.note.strip()))
            require(not e.uncertain and e.text == resolved["text"])
            readers = {r["reviewer"] for r in state["reads"].values()}
            require(e.reviewer in readers and e.reviewer not in state["approvals"])
            require(
                any(
                    r["reviewer"] == e.reviewer and r["session"] == e.session
                    for r in state["reads"].values()
                )
            )
            state["approvals"][e.reviewer] = raw
            if len(state["approvals"]) == 2:
                state["status"] = "APPROVED"
        previous = digest(raw)
    return states, previous


def load_project(dataset, directory):
    directory = Path(directory)
    project = private_read(directory / "project.json")
    synthetic = project["manifest"]["source_type"] == "SINTETICO_SOLO_PRUEBA"
    require(synthetic or not os.environ.get("CI"))
    require(validate(dataset, synthetic=synthetic) == project["manifest"])
    files = sorted(directory.iterdir())
    require(
        {p.name for p in files}
        == {"project.json"} | {f"{i:06d}.json" for i in range(1, len(files))}
    )
    events = [private_read(directory / f"{i:06d}.json") for i in range(1, len(files))]
    states, previous = replay(project, events)
    return project, events, states, previous


def append(
    dataset,
    directory,
    case,
    action,
    reviewer,
    session,
    *,
    text="",
    note="",
    explicit=False,
    uncertain=False,
    origin="heard_audio",
):
    project, events, states, previous = load_project(dataset, directory)
    require(case in IDS)
    if action == "APPROVED":
        require(states[case]["resolved"] is not None)
        text = states[case]["resolved"]["text"]
    entry = next(e for e in project["manifest"]["entries"] if e["id"] == case)
    event = Event(
        dataset_digest=project["manifest"]["dataset_digest"],
        previous=previous,
        id=case,
        audio_sha256=entry["audio_sha256"],
        action=action,
        reviewer=reviewer,
        session=session,
        text=text,
        note=note,
        explicit=explicit,
        uncertain=uncertain,
        origin=origin,
        timestamp=datetime.now(timezone.utc).isoformat(),
    ).model_dump()
    replay(project, events + [event])
    # Exclusive sequential filenames reject concurrent writers; a retry reloads the ledger.
    write_private(Path(directory) / f"{len(events) + 1:06d}.json", event)


def status(dataset, directory):
    _, _, states, _ = load_project(dataset, directory)
    return {
        case: {
            "status": s["status"],
            "readings": len(s["reads"]),
            "submitted": sum(r["action"] == "SUBMITTED" for r in s["reads"].values()),
            "reviewers": len({r["reviewer"] for r in s["reads"].values()}),
            "approvals": len(s["approvals"]),
            "uncertain": any(r["uncertain"] for r in s["reads"].values()),
        }
        for case, s in states.items()
    }


def listen(dataset, directory, case, start=0.0, end=None):
    project, _, _, _ = load_project(dataset, directory)
    require(case in IDS)
    entry = next(e for e in project["manifest"]["entries"] if e["id"] == case)
    payload = validated_audio(dataset, entry)
    require(0 <= start < (end if end is not None else entry["duration_seconds"]))
    require(end is None or end <= entry["duration_seconds"])
    with wave.open(io.BytesIO(payload), "rb") as source:
        rate = source.getframerate()
        source.setpos(int(start * rate))
        frames = source.readframes(int(((end or entry["duration_seconds"]) - start) * rate))
        with tempfile.TemporaryFile() as audio:
            with wave.open(audio, "wb") as target:
                target.setparams(source.getparams())
                target.writeframes(frames)
            audio.seek(0)
            subprocess.run(
                ["aplay", "-q"],
                stdin=audio,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )


def export_reviewed(dataset, directory, run_dir, declarations, output, *, synthetic=False):
    project, events, states, _ = load_project(dataset, directory)
    require(all(s["status"] == "APPROVED" for s in states.values()))
    expected = "SINTETICO_SOLO_PRUEBA" if synthetic else "PILOTO_REAL_DIAGNOSTICO_CONOCIDO"
    require(project["manifest"]["source_type"] == expected)
    declared = private_read(declarations)
    require(declared.get("partition") == "PREVIOUSLY_OPEN")
    require(not synthetic or declared.get("origin") == "SYNTHETIC_TEST_ONLY")
    require(declared.get("audio_retention_authorized") is True)
    require(isinstance(declared.get("publication_permission"), dict))
    permission = declared["publication_permission"]
    require(
        set(permission) == {"metrics", "transcripts"}
        and all(type(v) is bool for v in permission.values())
    )
    require(bool(declared.get("act_id")))
    require(
        set(declared.get("reviewer_ids", []))
        == {r for s in states.values() for r in s["approvals"]}
    )
    private_read(Path(run_dir) / "run.json")
    run = load_run(run_dir)
    require(len(declared["reviewer_ids"]) == len(set(declared["reviewer_ids"])))
    require(run["input"] == project["manifest"])
    annotations = {"dataset_digest": project["manifest"]["dataset_digest"], "entries": []}
    for case, state in states.items():
        text = state["resolved"]["text"]
        annotations["entries"].append(
            {
                "id": case,
                "audio_sha256": next(
                    e["audio_sha256"] for e in project["manifest"]["entries"] if e["id"] == case
                ),
                "reference": {
                    "origin": "synthetic_fixture" if synthetic else "independent_human",
                    "faithful": {"text": text, "sha256": hashlib.sha256(text.encode()).hexdigest()},
                    "review_status": "human_verified",
                    "reviewer_ids": sorted(state["approvals"]),
                    "attestation_ids": [declared["act_id"]],
                    "arbitration": "RESOLVED",
                },
            }
        )
    out = private_directory(output)
    write_private(out / "annotations.json", annotations)
    # Existing exporter consumes only its original declarations, preserving compatibility.
    write_private(
        out / "declarations.json", {k: declared[k] for k in ("batch_id", "frozen_date", "sessions")}
    )
    batch = export_batch(
        run_dir, out / "declarations.json", out / "annotations.json", synthetic=synthetic
    )
    write_private(out / "batch.json", batch)
    write_private(
        out / "binding.json",
        {
            "ledger_digest": digest(events),
            "project_digest": digest(project),
            "run_digest": digest(run),
            "model": run["model"],
            "parameters": run["parameters"],
            "declarations_digest": digest(declared),
            "batch_digest": digest(batch),
            "publication_permission": permission,
            "protocol": PROTOCOL,
            "normalizer": NORMALIZER,
            "normalized_references": {
                c: palabras(s["resolved"]["text"]) for c, s in states.items()
            },
        },
    )
    write_private(out / "kit.json", review_kit(load_batch(out / "batch.json")))


def external_vote(batch_path, votes_dir, registry, reviewer, attestation, decision, note):
    """Explicit terminal action against all reference/consent fields; no identity invention."""
    require(decision in {"ACCEPT", "REJECT", "DISPUTE"} and bool(note.strip()))
    require(re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{1,63}", reviewer) is not None)
    auth = private_read(registry)
    require(
        any(
            r.get("reviewer") == reviewer
            and r.get("attestation_id") == attestation
            and r.get("authorized") is True
            for r in auth
        )
    )
    batch = load_batch(batch_path)
    # Terminal review is private, explicitly requested, and follows independent capture.
    kit = review_kit(batch)
    require(all(s.reference is not None for s in batch.sessions))
    records = [
        k
        | {
            "decision": decision,
            "reviewer": reviewer,
            "attestation_id": attestation,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "comment": note,
        }
        for k in kit
        if k["field_path"] in {"reference", "consent"}
    ]
    path = Path(votes_dir)
    if not path.exists():
        private_directory(path)
    private_read(registry)
    require(not any(p.is_symlink() for p in [path, *path.parents]))
    write_private(path / f"{reviewer}.json", records)


def score_reviewed(batch_path, votes_dir, registry, output):
    from training.benchmark_campo.pipeline import verified

    batch = load_batch(batch_path)
    require([s.session_id for s in batch.sessions] == ["AUDIO-" + case for case in IDS])
    require(
        all(
            s.reference
            and s.reference.faithful
            and s.reference.review_status == "human_verified"
            and s.reference.arbitration == "RESOLVED"
            and s.provenance.partition == "PREVIOUSLY_OPEN"
            for s in batch.sessions
        )
    )
    binding = private_read(Path(batch_path).parent / "binding.json")
    require(binding["batch_digest"] == digest(batch.model_dump(mode="json")))
    auth = private_read(registry)
    votes = []
    for path in sorted(Path(votes_dir).iterdir()):
        require(path.suffix == ".json")
        votes.extend(private_read(path))
    fields = verified(batch, votes, auth)
    require(
        all((s.session_id, f) in fields for s in batch.sessions for f in ("reference", "consent"))
    )
    result = score(batch, votes, auth, private_detail=True)
    result["input_digest"] = digest(batch.model_dump(mode="json"))
    result["binding_digest"] = digest(binding)
    result["run_digest"] = binding["run_digest"]
    result["normalizer"] = NORMALIZER
    result["token_lengths"] = {
        s.session_id: {
            "reference": len(palabras(s.reference.faithful.text)),
            "hypothesis": len(palabras(s.asr.text)),
            "warning": "EMPTY_NORMALIZED_REFERENCE_NOT_EVALUABLE"
            if not palabras(s.reference.faithful.text)
            else "ININTELIGIBLE_REQUIRES_CAUTION"
            if "ininteligible" in s.reference.faithful.text.casefold()
            else None,
        }
        for s in batch.sessions
    }
    result["HOLDOUT_EXTERNO"] = 0
    result["PROMOCION"] = "NO"
    write_private(Path(output), result)
    return result


def create_demo(output):
    """Audible tones, never speech or pilot evidence; opt-in local manual exercise."""
    import csv
    import math
    import struct

    from .runner import evaluate

    out = private_directory(output)
    dataset = private_directory(out / "dataset")
    audios = private_directory(dataset / "audios")
    rows = []
    for number, case in enumerate(IDS, 1):
        stream = io.BytesIO()
        with wave.open(stream, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            audio.writeframes(
                b"".join(
                    struct.pack(
                        "<h",
                        int(4000 * math.sin(2 * math.pi * (300 + number * 20) * frame / 16000)),
                    )
                    for frame in range(16000)
                )
            )
        payload = stream.getvalue()
        path = audios / f"{case}.wav"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as target:
            target.write(payload)
        rows.append([case, f"audios/{case}.wav", hashlib.sha256(payload).hexdigest(), len(payload)])
    fd = os.open(dataset / "manifest.csv", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as target:
        writer = csv.writer(target)
        writer.writerow(["guion", "archivo", "sha256", "bytes"])
        writer.writerows(rows)

    class SyntheticASR:
        manifest = {"model_digest": "SYNTHETIC_TEST_ONLY"}
        versions = {"fixture": "SYNTHETIC_TEST_ONLY"}
        load_seconds = 0.0

        def __init__(self, *_):
            pass

        def transcribe(self, payload):
            return [{"start": 0.0, "end": 1.0, "text": "tono"}]

    evaluate(dataset, out / "run", execute=True, synthetic=True, factory=SyntheticASR)
    initialize(dataset, out / "project", synthetic=True)
