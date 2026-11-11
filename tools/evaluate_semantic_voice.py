#!/usr/bin/env python3
"""Compare frozen/current NLP across original and completed candidate ASR configs.

Script-relative development evidence only. Acoustic gold and generalization are
unavailable; unmatched predictions are review candidates, not confirmed errors.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

# Independent annotation grammar, never production normalization as metric truth.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.annotate_real_voice import NUM, fold, number  # noqa: E402
from tools.evaluate_real_voice import edit_counts, normalized_words  # noqa: E402

BASE = "b851b5aa15a04e5ab1046271f124cc05c3135da8"
AXES = {
    "altura": "alto",
    "diametro": "diametro",
    "ancho": "ancho",
    "largo": "largo",
    "profundidad": "profundidad",
    "alto": "alto",
}
MODE = {
    "PRECIO_UNITARIO": "UNIT",
    "TOTAL_NEGOCIADO": "NEGOTIATED_TOTAL",
    "PRECIO_TOTAL": "TOTAL",
    "PRECIO_LISTA": "LIST",
}
RUNNER = r"""
import json,sys
from homex_nlp.catalog import CatalogRequest,extract_catalog
from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine
request=json.load(sys.stdin)
results=[]
for row in request['rows']:
 try:
  if row['category']=='MUEBLE_MEDIDA':
   result=RulesEngine().extract(ExtractionRequest(request_id=row['id'],text=row['text'],currency_context='BOB'))
  else:
   result=extract_catalog(CatalogRequest(category=row['category'],text=row['text'],values=request['values']))
  raw=result.model_dump(mode='json')
 except Exception as error:
  raw={'execution_error':{'type':type(error).__name__,'message':str(error)}}
 results.append({'id':row['id'],'raw':raw})
json.dump(results,sys.stdout,ensure_ascii=False)
"""


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def check_identity(output, identity, resume):
    path = output / "identity.json"
    if path.exists():
        if not resume or json.loads(path.read_text()) != identity:
            raise ValueError("Resume identity mismatch; use a new output directory")
    else:
        if resume and any(output.iterdir()):
            raise ValueError("Resume identity missing in nonempty output directory")
        dump(path, identity)


def strict_normalize(text):
    """Only tested, explicit numeric/unit equivalences; no ASR reconstruction.

    Codes/models are opaque. Ambiguous cardinals abstain, including coordinated
    values. Article 'un' and inherited/compound unit guesses are not normalized.
    """
    protected = [m.span() for m in re.finditer(r"\b(?:modelo|código)\s+[^,.\n]+", text, re.I)]
    changes = []
    for match in re.finditer(r"(?<!\w)(" + NUM + r")(?!\w)", text, re.I):
        if any(a <= match.start() < b for a, b in protected):
            continue
        value = number(match.group())
        after = fold(text[match.end() : match.end() + 30])
        before = fold(text[max(0, match.start() - 30) : match.start()])
        explicit = bool(
            re.match(r"\s+(?:bolivianos?|bs\b|milimetros?|centimetros?|metros?|mm\b|cm\b)", after)
        )
        price = bool(re.search(r"precio(?: unitario| de lista| por juego)?(?: de)?\s*$", before))
        opening = match.start() == 0 and value is not None and value >= 2
        if value is None or not (explicit or price or opening):
            continue
        replacement = str(Decimal(str(value)).normalize())
        replacement = format(Decimal(replacement), "f")
        if match.group() != replacement:
            changes.append(
                dict(
                    start=match.start(),
                    end=match.end(),
                    raw=match.group(),
                    replacement=replacement,
                    reason="STRICT_CARDINAL_OR_NUMERIC_FORMAT_WITH_EXPLICIT_CONTEXT",
                )
            )
    for match in re.finditer(r"\b(?:milímetros?|centímetros?|metros?|bolivianos?)\b", text, re.I):
        if any(a <= match.start() < b for a, b in protected):
            continue
        raw = fold(match.group())
        value = (
            "mm"
            if raw.startswith("mili")
            else "cm"
            if raw.startswith("cent")
            else "m"
            if raw.startswith("metro")
            else "BOB"
        )
        changes.append(
            dict(
                start=match.start(),
                end=match.end(),
                raw=match.group(),
                replacement=value,
                reason="VERIFIED_LITERAL_UNIT_OR_CURRENCY_EQUIVALENCE",
            )
        )
    normalized = text
    for change in sorted(changes, key=lambda c: c["start"], reverse=True):
        normalized = (
            normalized[: change["start"]] + change["replacement"] + normalized[change["end"] :]
        )
    return normalized, sorted(changes, key=lambda c: c["start"])


def canonical(field, value, unit=None, axis=None):
    if field in {"quantity", "price", "dimensions", "thicknesses"}:
        try:
            value = Decimal(str(value))
        except InvalidOperation:
            return None
        if field in {"dimensions", "thicknesses"}:
            factor = {"m": 1000, "cm": 10, "mm": 1}.get(unit)
            if factor is None:
                return None
            value *= factor
        value = format(value.normalize(), "f")
    else:
        value = fold(str(value)).strip()
    axis = AXES.get(fold(axis), fold(axis)) if axis else None
    return (field, value, axis if field == "dimensions" else None)


def predictions(raw, values):
    result = []

    def add(field, value, **extra):
        if value is not None:
            result.append(dict(field=field, value=value, **extra))

    item = raw.get("item_proposal") or {}
    if item:
        add("quantity", item.get("quantity"))
        add("name", item.get("name"))
        for field in ("dimensions", "thicknesses"):
            for measure in item.get(field, []):
                add(
                    field,
                    measure.get("value"),
                    unit=measure.get("unit"),
                    axis=measure.get("axis"),
                    component_ref=measure.get("component_ref"),
                )
        for key in ("primary_color", "secondary_color"):
            color = item.get(key)
            add("colors", color.get("value") if isinstance(color, dict) else color)
        for accessory in item.get("accessories", []):
            add(
                "accessories",
                accessory.get("name"),
                count=accessory.get("quantity"),
                component_ref=accessory.get("component_ref"),
            )
        price = item.get("price") or {}
        add(
            "price",
            price.get("stated_amount"),
            currency=price.get("currency"),
            modality=MODE.get(price.get("mode"), price.get("mode")),
        )
        for candidate in raw.get("candidates", []):
            if candidate.get("label") == "MATERIAL" and candidate.get("decision") == "ACCEPTED":
                add("materials", candidate["text"], evidence=candidate)
    fields = raw.get("fields", {})
    lookup = {v["id"]: v for v in values}
    for source, target in {
        "nombre": "name",
        "modelo": "model",
        "marca": "brand",
        "color_primario": "colors",
        "color_secundario": "colors",
        "unidad_stock": "commercial_unit",
        "precio_lista": "price",
    }.items():
        value = fields.get(source)
        if isinstance(value, int) and value in lookup:
            value = lookup[value]["name"]
        add(target, value)
    # Numeric catalog columns are already normalized to millimetres by contract.
    for source, field, axis in (
        ("espesor_mm", "thicknesses", None),
        ("ancho_mm", "dimensions", "ancho"),
        ("largo_mm", "dimensions", "largo"),
    ):
        add(field, fields.get(source), unit="mm", axis=axis)
    for key, value in fields.get("especificaciones", {}).items():
        if key in {"material_respaldo", "tapiz", "asiento", "base"}:
            add("materials", value)
        elif key in {"apoyo_lumbar", "reposacabezas", "reposapies", "brazos_regulables"}:
            add("accessories", value)
    for candidate in raw.get("evidence", []):
        if "material" in candidate.get("label", "") and candidate.get("decision") == "ACCEPTED":
            add("materials", candidate["text"], evidence=candidate)
    return result


def score(references, actual):
    expected = {}
    for index, ref in enumerate(references):
        if ref.get("eligible_script_denominator") and ref.get("value") is not None:
            key = canonical(ref["field"], ref["value"], ref.get("unit"), ref.get("axis"))
            if key is not None:
                expected.setdefault(key, []).append(index)
    predicted = {}
    for index, item in enumerate(actual):
        key = canonical(item["field"], item["value"], item.get("unit"), item.get("axis"))
        if key is not None:
            predicted.setdefault(key, []).append(index)
    matched = set(expected) & set(predicted)
    field_results = []
    for key, ref_indices in expected.items():
        field_results.append(
            dict(
                key=list(key),
                reference_indices=ref_indices,
                matched=key in matched,
                outcome="MATCH"
                if key in matched
                else "MISMATCH"
                if any(k[0] == key[0] for k in predicted)
                else "ABSTENTION",
                prediction_indices=predicted.get(key, []),
                scope="SCALAR_OR_LITERAL_PRESENCE_ONLY_ASSOCIATION_NOT_SCORED",
            )
        )
    by_field = {}
    for field in {key[0] for key in expected}:
        denominator = sum(k[0] == field for k in expected)
        numerator = sum(k[0] == field for k in matched)
        by_field[field] = dict(
            numerator=numerator,
            denominator=denominator,
            misses=denominator - numerator,
            abstentions=sum(
                r["key"][0] == field and r["outcome"] == "ABSTENTION" for r in field_results
            ),
            mismatches=sum(
                r["key"][0] == field and r["outcome"] == "MISMATCH" for r in field_results
            ),
        )
    qualifier_results = []
    for key, indices in expected.items():
        if key[0] != "price":
            continue
        ref = references[indices[0]]
        for qualifier in ("currency", "modality"):
            value = ref.get(qualifier)
            if value is None or value == "UNSPECIFIED":
                continue
            proposed = [
                actual[i].get(qualifier)
                for i in predicted.get(key, [])
                if actual[i].get(qualifier) is not None
            ]
            qualifier_results.append(
                dict(
                    key=list(key),
                    qualifier=qualifier,
                    expected=value,
                    proposed=proposed,
                    outcome="MATCH"
                    if value in proposed
                    else "MISMATCH"
                    if proposed
                    else "NOT_REPRESENTED_OR_ABSTAINED",
                    scope="EXPLICIT_SCRIPT_PRICE_QUALIFIER_NOT_ACOUSTIC_GOLD",
                )
            )
    return dict(
        qualifier_results=qualifier_results,
        numerator=len(matched),
        denominator=len(expected),
        association_denominator=0,
        confirmed_false_positives=None,
        field_results=field_results,
        by_field=by_field,
        false_positive_candidates=[
            dict(
                key=list(k),
                prediction_indices=v,
                status="UNVERIFIED_EXTRA_CANDIDATE_REFERENCE_INCOMPLETE",
            )
            for k, v in predicted.items()
            if k not in expected
        ],
    )


def score_supported(references, actual, category):
    """Keep unsupported fields visible, outside contract-supported denominators."""
    common = {"name", "price", "commercial_unit"}
    supported = {
        "OTRO": common,
        "SILLA": common | {"model", "brand", "colors", "materials", "accessories"},
        "PISO_FLOTANTE": common | {"model", "brand", "materials", "dimensions", "thicknesses"},
        "MUEBLE_MEDIDA": {
            "name",
            "quantity",
            "price",
            "materials",
            "colors",
            "accessories",
            "dimensions",
            "thicknesses",
        },
    }[category]

    def supported_ref(ref):
        return ref["field"] in supported and not (
            category == "PISO_FLOTANTE"
            and ref["field"] == "dimensions"
            and AXES.get(fold(ref.get("axis") or "")) not in {"ancho", "largo"}
        )

    result = score([r for r in references if supported_ref(r)], actual)
    result["unsupported_verified_reference_indices"] = [
        i
        for i, ref in enumerate(references)
        if ref.get("eligible_script_denominator") and not supported_ref(ref)
    ]
    result["scope"] = "CATEGORY_CONTRACT_FIELD_FAMILY_SCALAR_ONLY_NO_ASSOCIATION_PROOF"
    return result


def source_hashes(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted((root / "src").rglob("*.py"))}


def snapshot_sources(root, base):
    scratch = Path(tempfile.mkdtemp(prefix="homex-semantic-eval-"))
    baseline = scratch / "baseline"
    baseline.mkdir()
    archive = scratch / "baseline.tar"
    with archive.open("wb") as stream:
        subprocess.run(["git", "-C", str(root), "archive", base], stdout=stream, check=True)
    with tarfile.open(archive) as stream:
        stream.extractall(baseline, filter="data")
    current = scratch / "current"
    current.mkdir()
    shutil.copytree(root / "src", current / "src", ignore=shutil.ignore_patterns("__pycache__"))
    return scratch, baseline, current


def run_nlp(snapshot, rows, values):
    env = dict(os.environ, PYTHONPATH=str(snapshot / "src"), PYTHONDONTWRITEBYTECODE="1")
    process = subprocess.run(
        [sys.executable, "-c", RUNNER],
        input=json.dumps(dict(rows=rows, values=values)),
        text=True,
        capture_output=True,
        cwd=snapshot,
        env=env,
        check=True,
    )
    return {row["id"]: row["raw"] for row in json.loads(process.stdout)}


def summarize(output, expected_count, pending):
    rows = [json.loads(p.read_text()) for p in sorted((output / "cases").glob("*/*.json"))]
    groups = defaultdict(list)
    for row in rows:
        groups[row["cell"]].append(row)
    cells = {}
    for name, subset in groups.items():
        categories = {}
        for category in sorted({r["category"] for r in subset}):
            selected = [r for r in subset if r["category"] == category]
            totals = Counter()
            fields = defaultdict(Counter)
            for row in selected:
                totals.update({k: row["score"][k] for k in ("numerator", "denominator")})
                totals["supported_numerator"] += row["supported_score"]["numerator"]
                totals["supported_denominator"] += row["supported_score"]["denominator"]
                totals["unsupported_reference_mentions"] += len(
                    row["supported_score"]["unsupported_verified_reference_indices"]
                )
                totals["no_proposal"] += row["no_proposal"]
                totals["execution_errors"] += "execution_error" in row["nlp_raw"]
                totals["false_positive_candidates"] += len(
                    row["score"]["false_positive_candidates"]
                )
                for field, counts in row["score"]["by_field"].items():
                    fields[field].update(counts)
            categories[category] = dict(
                cases=len(selected), **totals, fields={k: dict(v) for k, v in fields.items()}
            )
        cells[name] = dict(
            cases=len(subset),
            complete=len(subset) == expected_count
            and not any("execution_error" in r["nlp_raw"] for r in subset),
            execution_errors=sum("execution_error" in r["nlp_raw"] for r in subset),
            categories=categories,
            numerator=sum(r["score"]["numerator"] for r in subset),
            denominator=sum(r["score"]["denominator"] for r in subset),
            no_proposal=sum(r["no_proposal"] for r in subset),
            supported_numerator=sum(r["supported_score"]["numerator"] for r in subset),
            supported_denominator=sum(r["supported_score"]["denominator"] for r in subset),
            wer={
                kind: dict(
                    errors=sum(r["asr_metrics"][kind]["errors"] for r in subset),
                    reference_length=sum(
                        r["asr_metrics"][kind]["reference_length"] for r in subset
                    ),
                )
                for kind in ("original", "strict_normalized")
            },
        )
    comparisons = []
    by_case = {(r["cell"], r["id"]): r for r in rows}
    asr_names = sorted({r["asr_configuration"] for r in rows})
    for asr in asr_names:
        for identifier in sorted({r["id"] for r in rows}):
            old = by_case.get((f"{asr}__baseline_nlp", identifier))
            new = by_case.get((f"{asr}__current_nlp", identifier))
            if not old or not new:
                continue
            old_matches = {tuple(f["key"]) for f in old["score"]["field_results"] if f["matched"]}
            new_matches = {tuple(f["key"]) for f in new["score"]["field_results"] if f["matched"]}
            if old_matches != new_matches or old["no_proposal"] != new["no_proposal"]:
                comparisons.append(
                    dict(
                        id=identifier,
                        asr_configuration=asr,
                        recoveries=[list(k) for k in sorted(new_matches - old_matches, key=str)],
                        regressions=[list(k) for k in sorted(old_matches - new_matches, key=str)],
                        baseline_no_proposal=old["no_proposal"],
                        current_no_proposal=new["no_proposal"],
                    )
                )
    asr_deltas = []
    isolation = []
    for row in rows:
        if row["asr_configuration"] == "script_control":
            continue
        label = row["nlp_configuration"]
        control = by_case.get((f"script_control__{label}", row["id"]))
        script_matches = (
            {tuple(f["key"]): f for f in control["score"]["field_results"]} if control else {}
        )
        for field in row["score"]["field_results"]:
            script_result = script_matches.get(tuple(field["key"]))
            acoustic_match = field["matched"]
            script_match = script_result["matched"] if script_result else None
            hypothesis = (
                "TEXT_CHANNEL_DISCREPANCY_PENDING_HUMAN_LISTENING"
                if script_match and not acoustic_match
                else "NLP_SUPPORT_OR_REFERENCE_AMBIGUITY_PENDING"
                if script_match is False and not acoustic_match
                else "SURFACE_SENSITIVITY_PENDING_REVIEW"
                if script_match is False and acoustic_match
                else "SCALAR_MATCH_ASSOCIATION_AND_ACOUSTICS_UNVERIFIED"
                if acoustic_match
                else "SCRIPT_CONTROL_UNAVAILABLE"
            )
            isolation.append(
                dict(
                    id=row["id"],
                    category=row["category"],
                    cell=row["cell"],
                    key=field["key"],
                    asr_scalar_match=acoustic_match,
                    script_control_scalar_match=script_match,
                    hypothesis=hypothesis,
                    reference_indices=field["reference_indices"],
                    association_status="NOT_SCORED_UNVERIFIED",
                    acoustic_status="PENDING_HUMAN_LISTENING",
                    reference_scope="SCRIPT_LITERAL_OR_SCALAR_ONLY",
                )
            )
        if row["asr_configuration"] == "original":
            continue
        old = by_case.get((f"original__{label}", row["id"]))
        if old:
            old_matches = {tuple(f["key"]) for f in old["score"]["field_results"] if f["matched"]}
            new_matches = {tuple(f["key"]) for f in row["score"]["field_results"] if f["matched"]}
            if old_matches != new_matches or old["no_proposal"] != row["no_proposal"]:
                asr_deltas.append(
                    dict(
                        id=row["id"],
                        nlp_configuration=label,
                        candidate_asr=row["asr_configuration"],
                        recoveries=[list(k) for k in sorted(new_matches - old_matches, key=str)],
                        regressions=[list(k) for k in sorted(old_matches - new_matches, key=str)],
                        hypothesis_status="TEXTUAL_DISCREPANCY_NOT_CONFIRMED_ACOUSTIC_CAUSE",
                    )
                )
    dump(output / "asr-recoveries-regressions.json", asr_deltas)
    dump(output / "root-cause-isolation.json", isolation)
    result = dict(
        schema_version="semantic-four-cell/1",
        expected_cases=expected_count,
        development_only=True,
        acoustic_denominator=0,
        association_denominator=0,
        confirmed_false_positives=None,
        cells=cells,
        pending_asr_configurations=pending,
        caveats=[
            "Script-relative textual evidence, not verified speech or independent generalization.",
            "Distinct verified scalar/presence tuples per case; repeated mentions are deduplicated.",
            "Only supported structured predictions count; observations text is not extracted fields.",
            "Associations, pending fields, accessory counts and price modality/currency excluded from headline scalar recall.",
            "Candidate ASR improvement requires field outcomes, not normalized metric alone.",
        ],
    )
    dump(output / "summary.json", result)
    dump(output / "recoveries-regressions.json", comparisons)
    lines = [
        "# Four-cell development comparison",
        "",
        "| ASR / NLP | Cases | Matched / expected scalar tuples | No proposal | Original WER errors/words | Strict WER errors/words |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, c in sorted(cells.items()):
        if name.startswith("script_control__"):
            continue
        original = c["wer"]["original"]
        strict = c["wer"]["strict_normalized"]
        lines.append(
            f"| {name} | {c['cases']} | {c['numerator']}/{c['denominator']} | {c['no_proposal']} | {original['errors']}/{original['reference_length']} | {strict['errors']}/{strict['reference_length']} |"
        )
    lines += [
        "",
        "## Contract-supported scalar field families",
        "",
        "Unsupported category fields remain in full-coverage rows, not in this denominator. Chair feature subtypes and catalog context may still restrict realizable values. These are not association/precision metrics.",
        "",
        "| Input / NLP | Supported matched / expected |",
        "| --- | ---: |",
    ]
    for name, c in sorted(cells.items()):
        lines.append(f"| {name} | {c['supported_numerator']}/{c['supported_denominator']} |")
    lines += ["", "## Controlled script-input diagnostic (not ASR or gold)", ""]
    for name, c in sorted(cells.items()):
        if name.startswith("script_control__"):
            lines.append(
                f"- {name}: {c['numerator']}/{c['denominator']} scalar tuples; {c['no_proposal']} no-proposal cases."
            )
    lines += [
        "",
        "**All120 are development cases; acoustic and association denominators are zero.**",
        "",
        "Pending configurations: " + json.dumps(pending),
        "",
        "Headline recall excludes relation, count, modality and currency correctness. Extra predictions are unverified candidates, not confirmed false positives.",
    ]
    (output / "comparison.md").write_text("\n".join(lines) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--references", type=Path, required=True, help="Independent references-v2 directory"
    )
    parser.add_argument(
        "--original-asr", type=Path, required=True, help="Frozen baseline case directory"
    )
    parser.add_argument(
        "--candidate-asr",
        type=Path,
        required=True,
        help="Experiment root; only complete successful120-case configurations run",
    )
    parser.add_argument(
        "--values", type=Path, required=True, help="Controlled catalog fixture, not production DB"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New external directory; existing output needs --resume and identical identity",
    )
    parser.add_argument("--base-ref", default=BASE)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    references = [
        json.loads(line) for line in (args.references / "cases.jsonl").read_text().splitlines()
    ]
    ids = {r["id"] for r in references}
    if len(references) != 120 or len(ids) != 120:
        raise ValueError("Expected exactly120 unique development references")
    values = json.loads(args.values.read_text())
    identity = dict(
        base_ref=subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", args.base_ref], text=True
        ).strip(),
        current_source_hashes=source_hashes(ROOT),
        references_sha256=sha(args.references / "cases.jsonl"),
        values_sha256=sha(args.values),
        evaluator_sha256=sha(Path(__file__)),
        annotation_helper_sha256=sha(ROOT / "tools/annotate_real_voice.py"),
        metric_helper_sha256=sha(ROOT / "tools/evaluate_real_voice.py"),
        python=platform.python_version(),
        dependencies={name: importlib.metadata.version(name) for name in ("pydantic", "spacy")},
        original_asr_hashes={p.name: sha(p) for p in sorted(args.original_asr.glob("*.json"))},
        candidate_experiment_identity=sha(args.candidate_asr / "identity.json"),
    )
    args.output.mkdir(parents=True, exist_ok=args.resume)
    check_identity(args.output, identity, args.resume)
    (args.output / "cases").mkdir(exist_ok=True)
    scratch, baseline, current = snapshot_sources(ROOT, args.base_ref)
    dump(
        args.output / "scratch-paths.json",
        dict(
            parent_cleanup_required=True,
            paths=[str(scratch)],
            baseline_source_hashes=source_hashes(baseline),
            current_source_hashes=source_hashes(current),
        ),
    )
    if source_hashes(current) != identity["current_source_hashes"]:
        raise ValueError("Current sources changed during snapshot; use a new output directory")
    dump(
        args.output / "source-versions.json",
        {
            label: re.search(
                r"__version__\s*=\s*[\"\']([^\"\']+)",
                (snapshot / "src/homex_nlp/__init__.py").read_text(),
            ).group(1)
            for label, snapshot in [("baseline_nlp", baseline), ("current_nlp", current)]
        },
    )
    original = {
        r["id"]: json.loads((args.original_asr / (r["id"] + ".json")).read_text())
        for r in references
    }
    configurations = {
        "original": {
            k: dict(
                text=v["asr"]["text_original"],
                artifact_sha256=sha(args.original_asr / (k + ".json")),
                configuration=v["asr"].get("model_version"),
                audio=v["audio"],
            )
            for k, v in original.items()
        }
    }
    pending = {}
    for folder in sorted(args.candidate_asr.iterdir()):
        if not (folder / "cases").is_dir():
            continue
        available = {p.stem: p for p in (folder / "cases").glob("*.json")}
        if set(available) != ids:
            pending[folder.name] = dict(
                completed_cases=len(set(available) & ids), expected_cases=120
            )
            continue
        candidate = {k: json.loads(p.read_text()) for k, p in available.items()}
        errors = [k for k, v in candidate.items() if "error" in v or not v.get("text", "").strip()]
        if errors:
            pending[folder.name] = dict(error_cases=errors)
            continue
        for key, row in candidate.items():
            if (
                row["audio"] != original[key]["audio"]
                or row["reference"] != original[key]["reference"]
            ):
                raise ValueError("Candidate identity mismatch " + key)
        configurations[folder.name] = {
            k: dict(
                text=v["text"],
                artifact_sha256=sha(available[k]),
                configuration=v["settings"],
                audio=v["audio"],
            )
            for k, v in candidate.items()
        }
    configurations["script_control"] = {
        r["id"]: dict(
            text=r["script_text"],
            artifact_sha256=sha(args.references / "cases" / (r["id"] + ".json")),
            configuration="CONTROLLED_SCRIPT_INPUT_NOT_ASR_OR_GOLD",
            audio=original[r["id"]]["audio"],
        )
        for r in references
    }
    for name, configuration in configurations.items():
        input_rows = [
            dict(id=r["id"], category=r["category"], text=configuration[r["id"]]["text"])
            for r in references
        ]
        for label, snapshot in [("baseline_nlp", baseline), ("current_nlp", current)]:
            cell = f"{name}__{label}"
            missing = []
            for ref in references:
                target = args.output / "cases" / cell / (ref["id"] + ".json")
                if target.exists():
                    old = json.loads(target.read_text())
                    if old["asr_artifact_sha256"] != configuration[ref["id"]]["artifact_sha256"]:
                        raise ValueError("Resume candidate artifact identity mismatch")
                else:
                    missing.append(ref["id"])
            extracted = (
                run_nlp(snapshot, [r for r in input_rows if r["id"] in missing], values)
                if missing
                else {}
            )
            for ref in references:
                if ref["id"] not in missing:
                    continue
                item = configuration[ref["id"]]
                text = item["text"]
                raw = extracted[ref["id"]]
                expected, ref_changes = strict_normalize(ref["script_text"])
                actual, asr_changes = strict_normalize(text)
                predicted = predictions(raw, values)
                result = dict(
                    id=ref["id"],
                    category=ref["category"],
                    leakage_group=ref["leakage_group"],
                    development_only=True,
                    input_role="SCRIPT_DIAGNOSTIC_NOT_ASR_OR_GOLD"
                    if name == "script_control"
                    else "ASR_TRANSCRIPT",
                    cell=cell,
                    asr_configuration=name,
                    nlp_configuration=label,
                    asr_artifact_sha256=item["artifact_sha256"],
                    asr_settings=item["configuration"],
                    audio=item["audio"],
                    text_original=text,
                    script_text=ref["script_text"],
                    nlp_raw=raw,
                    predicted_fields=predicted,
                    score=score(ref["script_fields"], predicted),
                    supported_score=score_supported(
                        ref["script_fields"], predicted, ref["category"]
                    ),
                    no_proposal=raw.get("status") == "NO_PROPOSAL"
                    or (not raw.get("item_proposal") and not raw.get("fields")),
                    asr_metrics=dict(
                        original=edit_counts(
                            normalized_words(ref["script_text"]), normalized_words(text)
                        ),
                        strict_normalized=edit_counts(
                            normalized_words(expected), normalized_words(actual)
                        ),
                    ),
                    normalization=dict(
                        reference_text=expected,
                        asr_text=actual,
                        reference_transforms=ref_changes,
                        asr_transforms=asr_changes,
                    ),
                    acoustic_status="PENDING_HUMAN_LISTENING",
                )
                dump(args.output / "cases" / cell / (ref["id"] + ".json"), result)
            print(cell, len(references), "cases", flush=True)
    result = summarize(args.output, len(references), pending)
    print(
        json.dumps(
            dict(cells=len(result["cells"]), pending=pending, scratch=str(scratch)), indent=2
        )
    )


if __name__ == "__main__":
    main()
