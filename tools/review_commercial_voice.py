"""Build an immutable-input, offline commercial adjudication workspace."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

FIELD_TYPES = (
    "product",
    "name",
    "quantity",
    "commercial_unit",
    "materials",
    "components",
    "accessories",
    "colors",
    "thicknesses",
    "dimensions",
    "price",
    "brand",
    "model",
    "technical_description",
)
PROVENANCES = ("SCRIPT_TEXT", "DOCUMENT_TEXT", "AUTO_PROPOSAL", "HUMAN_AUDIO")
STATUSES = ("PENDIENTE", "CONFIRMADO", "CORREGIDO", "INCIERTO", "NO_VERIFICABLE")


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def contained(path: Path, root: Path) -> Path:
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root.resolve(strict=True)):
        raise ValueError(f"Path escapes corpus: {path.name}")
    return resolved


def validate_annotations(payload: dict, review: dict) -> None:
    """Reject mismatched datasets and invalid decisions without changing history."""
    if not isinstance(payload, dict):
        raise ValueError("Annotation payload must be an object")
    if (
        payload.get("schema_version") != "commercial-human-review/1"
        or payload.get("corpus_fingerprint") != review["corpus_fingerprint"]
    ):
        raise ValueError("Annotation schema/fingerprint mismatch")
    if not isinstance(payload.get("decisions"), list):
        raise ValueError("Decisions must be a list")
    cases = {case["id"]: case for case in review["cases"]}
    identities = {}
    for decision in payload["decisions"]:
        if not isinstance(decision, dict):
            raise ValueError("Invalid decision")
        case = cases.get(decision.get("case_id"))
        if not case or decision.get("source_sha256") != case["source_sha256"]:
            raise ValueError("Unknown case/source hash")
        field = decision.get("field")
        key = decision.get("field_key", "")
        known = {item["field_key"]: item["field"] for item in case["fields"]}
        if field not in FIELD_TYPES or not (
            known.get(key) == field or re.fullmatch(rf"new:{field}:[A-Za-z0-9_-]+", key)
        ):
            raise ValueError("Invalid field/key")
        if decision.get("status") not in STATUSES or decision.get("provenance") not in PROVENANCES:
            raise ValueError("Invalid status/provenance")
        for name in ("decision_id", "reviewer", "created_at", "note", "reason", "uncertainty"):
            if not isinstance(decision.get(name), str) or not decision[name].strip():
                raise ValueError(f"Missing {name}")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,160}", decision["decision_id"]):
            raise ValueError("Invalid decision identity")
        if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z", decision["created_at"]):
            raise ValueError("Invalid timestamp")
        for name in ("unit", "axis", "component", "modality"):
            if decision.get(name) is not None and not isinstance(decision[name], str):
                raise ValueError(f"Invalid {name}")
        if isinstance(decision.get("value"), (dict, list)):
            raise ValueError("Value must be a scalar or null")
        if decision["provenance"] == "HUMAN_AUDIO":
            if decision.get("listening_attested") is not True:
                raise ValueError("Human audio requires an explicit retained listening attestation")
            start, end = decision.get("start_seconds"), decision.get("end_seconds")
            if (
                any(
                    isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
                    for x in (start, end)
                )
                or not 0 <= start < end <= case["duration_seconds"]
            ):
                raise ValueError("Invalid listening interval")
        encoded = canonical(decision)
        previous = identities.setdefault(decision["decision_id"], encoded)
        if previous != encoded:
            raise ValueError("Conflicting decision identity; retain separate identities")


def comparison_case(root: Path, cell: str, case_id: str) -> dict:
    path = root / "cases" / cell / f"{case_id}.json"
    value = load(path)
    if value.get("id") != case_id:
        raise ValueError("Comparison ID mismatch")
    return {"artifact_sha256": sha256(path), "artifact_cell": cell, **value}


def build(
    corpus: Path, references: Path, baseline: Path, comparison: Path, candidate: Path | None = None
) -> dict:
    cases, audio_hashes, inputs = [], {}, []
    for reference_path in sorted((references / "cases").glob("*.json")):
        ref = load(reference_path)
        case_id = ref["id"]
        if not re.fullmatch(r"[A-Z]{2,3}-\d{4}", case_id) or reference_path.stem != case_id:
            raise ValueError("Invalid reference ID")
        base_path = baseline / "cases" / f"{case_id}.json"
        base = load(base_path)
        if base.get("id") != case_id:
            raise ValueError("Baseline ID mismatch")
        audio = {}
        for kind in ("original", "wav"):
            path = contained(Path(base["audio"][f"{kind}_path"]), corpus)
            digest = sha256(path)
            if digest != base["audio"][f"{kind}_sha256"]:
                raise ValueError(f"Audio integrity mismatch: {case_id}/{kind}")
            audio_hashes[str(path)] = digest
            audio[kind] = {
                "url": path.as_uri(),
                "path": str(path.relative_to(corpus.resolve())),
                "sha256": digest,
            }
        nlp = {
            "historical_b851": comparison_case(comparison, "original__baseline_nlp", case_id),
            "previous_0_1_22": comparison_case(comparison, "original__current_nlp", case_id),
        }
        if candidate:
            nlp["candidate"] = comparison_case(candidate, "original__current_nlp", case_id)
        fields = []
        for role, source in (
            ("SCRIPT_TEXT", "script_fields"),
            ("DOCUMENT_TEXT", "document_fields"),
        ):
            for index, field in enumerate(ref.get(source, [])):
                if field["field"] not in FIELD_TYPES:
                    raise ValueError("Unknown reference field")
                fields.append(
                    {
                        **field,
                        "field_key": f"{source}:{index}:{field['field']}",
                        "provenance": role,
                        "human_status": "PENDIENTE",
                    }
                )
        flags = []
        if ref.get("script_text") != base["asr"]["text_original"]:
            flags.append("TEXTUAL_SCRIPT_ASR_DIFFERENCE_NOT_ACOUSTIC_ERROR")
        if any(
            f["field"] in ("price", "dimensions", "quantity", "components")
            and (f.get("ambiguity") or f.get("asr_status") == "NO_EXACT_TEXT_CORROBORATION")
            for f in fields
        ):
            flags.append("TEXTUAL_COMMERCIAL_RISK_REQUIRES_HUMAN_REVIEW")
        if any(result.get("no_proposal") for result in nlp.values()):
            flags.append("NLP_ABSTENTION_NOT_AUTOMATIC_DEFECT")
        field_types = {
            name: {
                "script": [
                    f for f in fields if f["field"] == name and f["provenance"] == "SCRIPT_TEXT"
                ],
                "document": [
                    f for f in fields if f["field"] == name and f["provenance"] == "DOCUMENT_TEXT"
                ],
                "absence": "NO_PROPOSAL_NOT_PROOF_OF_ABSENCE",
                "human_status": "PENDIENTE",
            }
            for name in FIELD_TYPES
        }
        cases.append(
            {
                "id": case_id,
                "category": ref["category"],
                "status": "PENDIENTE",
                "development_only": True,
                "source_sha256": ref["source_sha256"],
                "reference": ref,
                "original_asr": base["asr"],
                "audio": audio,
                "duration_seconds": base["duration_seconds"],
                "fields": fields,
                "field_types": field_types,
                "nlp": nlp,
                "priority_flags": flags,
            }
        )
        inputs.append(
            {
                "id": case_id,
                "reference_sha256": sha256(reference_path),
                "baseline_sha256": sha256(base_path),
                "comparison_sha256": {k: v["artifact_sha256"] for k, v in nlp.items()},
            }
        )
    if not cases:
        raise ValueError("No cases")
    fingerprint = hashlib.sha256(
        canonical(
            {
                "inputs": [
                    {k: v for k, v in item.items() if k != "comparison_sha256"} for item in inputs
                ],
                "audio": {
                    str(Path(p).relative_to(corpus.resolve())): h for p, h in audio_hashes.items()
                },
            }
        ).encode()
    ).hexdigest()
    return {
        "schema_version": "commercial-review/1",
        "corpus_fingerprint": fingerprint,
        "field_types": FIELD_TYPES,
        "category_counts": dict(Counter(c["category"] for c in cases)),
        "input_ledger": inputs,
        "original_audio_hashes": audio_hashes,
        "cases": cases,
        "pending_queue": [
            {"id": c["id"], "status": "PENDIENTE", "priority_flags": c["priority_flags"]}
            for c in cases
        ],
    }


def render(review: dict) -> str:
    assets = Path(__file__).parent / "commercial_review_ui"
    js = (assets / "review.js").read_text()
    css = (assets / "review.css").read_text()
    data = (
        canonical(review)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )

    def csp_hash(value):
        return "'sha256-" + base64.b64encode(hashlib.sha256(value.encode()).digest()).decode() + "'"

    policy = f"default-src 'none'; connect-src 'none'; script-src {csp_hash(js)} {csp_hash(data)}; style-src {csp_hash(css)}; media-src file:; img-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
    return f'<!doctype html><html lang="es"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="{policy}"><title>Revisión comercial local</title><style>{css}</style><body><h1>Revisión comercial local</h1><p>DEVELOPMENT — PENDIENTE no implica error. Ninguna coincidencia textual ni reproducción certifica escucha humana.</p><label>Filtrar casos <input id="filter"></label><select id="cases" aria-label="Caso"></select><button id="export">Exportar decisiones</button><label>Importar decisiones <input type="file" id="import" accept="application/json"></label><p id="message" role="status"></p><main id="case"></main><script id="review-data" type="application/json">{data}</script><script>{js}</script></body></html>'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("corpus", "references", "baseline", "comparison", "output"):
        parser.add_argument(
            "--" + name, type=Path, required=True, help=f"{name} directory (output must not exist)"
        )
    parser.add_argument(
        "--candidate", type=Path, help="Optional frozen comparison-v5-shaped candidate root"
    )
    parser.add_argument(
        "--annotations", type=Path, help="Validate and include a separate human-review export"
    )
    args = parser.parse_args()
    try:
        if args.output.exists() or args.output.is_symlink():
            raise ValueError("Output already exists; refusing overwrite")
        corpus = args.corpus.resolve(strict=True)
        # Never place output under an immutable input directory.
        for root in (args.references, args.baseline, args.comparison, args.candidate):
            if root and args.output.resolve().is_relative_to(root.resolve()):
                raise ValueError("Output overlaps immutable input")
        review = build(corpus, args.references, args.baseline, args.comparison, args.candidate)
        annotations = {
            "schema_version": "commercial-human-review/1",
            "corpus_fingerprint": review["corpus_fingerprint"],
            "decisions": [],
        }
        if args.annotations:
            annotations = load(args.annotations)
            validate_annotations(annotations, review)
        review["annotations"] = annotations
        html = render(review)
        for path, expected in review["original_audio_hashes"].items():
            if sha256(Path(path)) != expected:
                raise ValueError("Audio changed during generation")
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / "review.json").write_text(
            json.dumps(review, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        )
        (args.output / "review.html").write_text(html)
        (args.output / "pending-queue.json").write_text(
            json.dumps(review["pending_queue"], indent=2) + "\n"
        )
        print(
            json.dumps(
                {
                    "cases": len(review["cases"]),
                    "category_counts": review["category_counts"],
                    "human_decisions": len(annotations["decisions"]),
                    "audio_integrity": "VERIFIED_BEFORE_AND_AFTER",
                    "output": str(args.output),
                }
            )
        )
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"Review generation refused: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
