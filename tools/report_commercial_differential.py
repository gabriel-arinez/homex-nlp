"""Audit frozen semantic-evaluator output and run explicit development probes.

No ASR is run. Script matches are diagnostic, not acoustic truth or precision.
The probe oracle covers names, proposal presence and named human-review needs
only; it does not pretend to be complete commercial ground truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.evaluate_semantic_voice import (  # noqa: E402
    dump,
    run_nlp,
    snapshot_sources,
    source_hashes,
)


def probe_outcome(row, raw):
    item = raw.get("item_proposal")
    fields = raw.get("fields", {})
    name = item.get("name") if item else fields.get("nombre")
    proposal = bool(item or fields)
    reviews = {r["code"] for r in raw.get("field_reviews", [])}
    return dict(
        name=name,
        proposal=proposal,
        name_correct=name == row["expected_name"],
        proposal_correct=proposal == row["expected_proposal"],
        review_correct=not row["expected_review"] or row["expected_review"] in reviews,
        review_codes=sorted(reviews),
    )


def commercial_payload(raw):
    """Compare values, associations, spans and reviews, not timing/engine version."""
    keys = (
        "status",
        "fields",
        "item_proposal",
        "evidence",
        "candidates",
        "warnings",
        "field_reviews",
        "unrecognized",
        "execution_error",
    )
    return {key: raw[key] for key in keys if key in raw}


def read_json(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, required=True, help="Frozen semantic output")
    parser.add_argument("--probes", type=Path, required=True, help="Development probe JSONL")
    parser.add_argument("--output", type=Path, required=True, help="New report directory")
    args = parser.parse_args()
    identity = read_json(args.evaluation / "identity.json")
    if source_hashes(ROOT) != identity["current_source_hashes"]:
        raise ValueError("Sources differ from evaluated snapshot; rerun semantic evaluation")
    rows = [json.loads(line) for line in args.probes.read_text().splitlines()]
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate probe IDs")
    args.output.mkdir(parents=True, exist_ok=False)
    scratch, baseline, current = snapshot_sources(ROOT, identity["base_ref"])
    dump(args.output / "probe-scratch-paths.json", {"parent_cleanup_required": [str(scratch)]})
    versions = read_json(args.evaluation / "source-versions.json")
    challenge = {r["id"]: dict(r, outcomes={}) for r in rows}
    for label, snapshot in (("baseline_nlp", baseline), ("current_nlp", current)):
        for identifier, raw in run_nlp(snapshot, rows, []).items():
            if "execution_error" in raw:
                raise ValueError(f"Probe execution failed: {label}/{identifier}: {raw}")
            challenge[identifier]["outcomes"][label] = probe_outcome(challenge[identifier], raw)
    cases = []
    for path in sorted((args.evaluation / "cases/original__baseline_nlp").glob("*.json")):
        old = read_json(path)
        new = read_json(args.evaluation / "cases/original__current_nlp" / path.name)
        if old["text_original"] != new["text_original"]:
            raise ValueError(f"Different text inputs: {path.name}")
        a, b = commercial_payload(old["nlp_raw"]), commercial_payload(new["nlp_raw"])
        cases.append(
            dict(
                id=old["id"],
                category=old["category"],
                corpus_group=old["id"].split("-")[0],
                changed=a != b,
                changed_sections=[key for key in a.keys() | b.keys() if a.get(key) != b.get(key)],
                baseline_no_proposal=old["no_proposal"],
                current_no_proposal=new["no_proposal"],
                baseline_by_field=old["score"]["by_field"],
                current_by_field=new["score"]["by_field"],
                input_sha256=hashlib.sha256(old["text_original"].encode()).hexdigest(),
            )
        )
    if len(cases) != 120:
        raise ValueError("Expected all 120 original ASR cases")
    summary = read_json(args.evaluation / "summary.json")
    totals = {}
    for label in ("baseline_nlp", "current_nlp"):
        outcomes = [r["outcomes"][label] for r in challenge.values()]
        totals[label] = dict(
            expected_names=sum(r["expected_name"] is not None for r in rows),
            correct_positive_names=sum(
                o["name_correct"] and o["name"] is not None for o in outcomes
            ),
            correct_abstentions=sum(o["proposal_correct"] and not o["proposal"] for o in outcomes),
            unjustified_proposals=sum(
                not r["expected_proposal"] and r["outcomes"][label]["proposal"]
                for r in challenge.values()
            ),
            required_reviews=sum(r["expected_review"] is not None for r in rows),
            correct_required_reviews=sum(
                bool(r["expected_review"]) and r["outcomes"][label]["review_correct"]
                for r in challenge.values()
            ),
            fully_matching_cases=sum(
                all(o[k] for k in ("name_correct", "proposal_correct", "review_correct"))
                for o in outcomes
            ),
        )
    dump(
        args.output / "report.json",
        dict(
            development_only=True,
            versions=versions,
            probes_sha256=hashlib.sha256(args.probes.read_bytes()).hexdigest(),
            source_identity=identity,
            challenge_totals=totals,
            challenge_cases=list(challenge.values()),
            original_asr_cases=cases,
            semantic_summary=summary,
            acoustic_precision_recall_f1=None,
            confirmed_wrong_values=None,
            association_accuracy=None,
        ),
    )
    lines = [
        "# Commercial differential evidence",
        "",
        "Development probes are not independent generalization.",
        "",
        "| Indicator | 0.1.29 | 0.1.30 |",
        "| --- | ---: | ---: |",
    ]
    for key in totals["baseline_nlp"]:
        lines.append(f"| {key} | {totals['baseline_nlp'][key]} | {totals['current_nlp'][key]} |")
    lines += [
        "",
        "## Every development probe",
        "",
        "| ID | Kind | Baseline correct | Candidate correct |",
        "| --- | --- | --- | --- |",
    ]
    for row in challenge.values():

        def good(o):
            return all(o[k] for k in ("name_correct", "proposal_correct", "review_correct"))

        lines.append(
            f"| {row['id']} | {row['kind']} | {good(row['outcomes']['baseline_nlp'])} | {good(row['outcomes']['current_nlp'])} |"
        )
    lines += [
        "",
        f"Original ASR cases with any commercial/evidence delta: {sum(c['changed'] for c in cases)}/120.",
        "",
        "Scalar-by-field and category details, every case, input hashes and raw source identity are in report.json. Historical script annotations are incomplete: precision, recall, F1, confirmed false-positive and association accuracy are not asserted.",
    ]
    (args.output / "report.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            dict(challenge_totals=totals, changed_original_asr=sum(c["changed"] for c in cases)),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
