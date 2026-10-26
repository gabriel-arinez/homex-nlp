"""Actionable review kit and append-only import of externally completed decisions.

No function infers that a human reviewed something. Identity authorization is an
external responsibility; identifiers alone are not digital signatures.
"""

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from training.corpus_v2.build import dump, jsonl, read, table


def make_kit(out, rows, refs, rc1, refs1):
    audits = json.loads(Path("data/candidates/corpus_v2_rc1/01_AUDITORIA_V1_675.json").read_text())
    changed = {r["v2_id"] for r in audits if r["state"] == "CORREGIDO"}
    unchanged = defaultdict(list)
    lookup = {r["id"]: r for r in rc1 + rows}
    for r in audits:
        if r["state"] == "APROBADO_SIN_CAMBIO":
            unchanged[r["family"]].append(r["v2_id"])
    sampled = set()
    strata = []
    for family, ids in sorted(unchanged.items()):
        labels = sorted({label for rid in ids for a, b, label in lookup[rid]["entities"]})
        for label in labels:
            eligible = [rid for rid in ids if any(e[2] == label for e in lookup[rid]["entities"])]
            chosen = sorted(
                eligible,
                key=lambda i: hashlib.sha256(("20261025" + label + i).encode()).hexdigest(),
            )[: max(1, math.ceil(len(eligible) * 0.15))]
            sampled.update(chosen)
            strata.append(
                {
                    "family": family,
                    "label": label,
                    "origin": "SINTETICO_DOCUMENTAL",
                    "correction_type": "UNCHANGED_CORE",
                    "error_cost": "P0"
                    if label in {"CANTIDAD", "PRECIO_UNITARIO", "PRECIO_TOTAL", "DESCUENTO"}
                    else "P1_TECHNICAL",
                    "eligible": len(eligible),
                    "selected_ids": chosen,
                }
            )
    sampled = sorted(sampled)
    dump(out / "review/sample_strata.json", strata)
    targets = sorted(changed | set(sampled) | {r["id"] for r in rows})
    all_refs = refs1 | refs
    kit = []
    technical = []
    for rid in targets:
        row = lookup[rid]
        ref = all_refs[rid]
        group = (
            "V1_CHANGED"
            if rid in changed
            else "V1_STRATIFIED_SAMPLE"
            if rid in sampled
            else "RC1_NEW"
            if rid.startswith("V2-")
            else "RC2_NEW"
        )
        technical.append(
            {
                "id": rid,
                "population": group,
                "family": row["category"],
                "text_sha256": row["text_sha256"],
                "technical_responsible": "CODEX",
                "format_status": "REQUIRES_VALIDATOR_RESULT",
                "commercial_status": "TECHNICAL_INFERENCE_NOT_HUMAN",
                "human_status": "PENDING",
                "semantic_checks": [
                    "product",
                    "commercial/internal/capacity",
                    "unit/axis",
                    "component scope",
                    "material/color/thickness/accessories",
                    "total/unit/discount/currency",
                    "negation/rectification/abstention",
                ],
                "method": "literal evidence + independent constraints; no human consensus",
            }
        )
        facts = ref.get("facts", []) or [
            {
                "path": "status",
                "value": row["status"],
                "evidence": {"text": row["text"], "start": 0, "end": len(row["text"])},
                "rule": "ABSTENTION_SCOPE",
            }
        ]
        for index, fact in enumerate(facts):
            path = fact["path"]
            priority = (
                "P0"
                if any(k in path for k in ["cantidad", "precio", "descuento", "moneda"])
                else "P1"
                if any(k in path for k in ["dimensiones", "material", "espesor"])
                else "P2"
            )
            key = hashlib.sha256(f"{rid}|{path}|{index}".encode()).hexdigest()[:20]
            before = None
            if rid in changed:
                audit = next(r for r in audits if r["v2_id"] == rid)
                from training.corpus_v2.validate import field_value

                old_path = path
                match = __import__("re").match(r"componentes.c(\d+)\.(.+)", path)
                if match:
                    old_path = (
                        f"especificacion.datos_tecnicos.componentes.{int(match[1]) - 1}.{match[2]}"
                    )
                try:
                    before = field_value(audit["expected_v1"]["expected"], old_path)
                except (KeyError, TypeError, IndexError):
                    before = None
            kit.append(
                {
                    "review_id": key,
                    "record_id": rid,
                    "population": group,
                    "priority": priority,
                    "family": row["category"],
                    "text": row["text"],
                    "text_sha256": row["text_sha256"],
                    "field_path": path,
                    "before": before,
                    "after": fact["value"],
                    "alternative": "REJECT_OR_PROPOSE_WITH_LITERAL_EVIDENCE",
                    "reason": fact.get("rule", "EXPLICIT_LITERAL"),
                    "citation": fact["evidence"],
                    "technical_responsible": "CODEX",
                    "technical_status": "COHERENCE_INFERRED",
                    "decision": "",
                    "proposed_value": "",
                    "comment": "",
                    "reviewer": "",
                    "reviewed_at": "",
                    "attestation_id": "",
                }
            )
        # Span-level delta must be reviewable as well as semantic fields.
        if rid in changed:
            audit = next(r for r in audits if r["v2_id"] == rid)
            if audit["spans"] != row["entities"]:
                kit.append(
                    {
                        "review_id": hashlib.sha256((rid + "|NER_DELTA").encode()).hexdigest()[:20],
                        "record_id": rid,
                        "population": group,
                        "priority": "P1",
                        "family": row["category"],
                        "text": row["text"],
                        "text_sha256": row["text_sha256"],
                        "field_path": "entities",
                        "before": audit["spans"],
                        "after": row["entities"],
                        "alternative": "REJECT_OR_PROPOSE_WITH_LITERAL_EVIDENCE",
                        "reason": "SPAN_NOMINAL_HEAD_CORRECTION",
                        "citation": {"text": "Membrana protectora incluida con el piso"},
                        "technical_responsible": "CODEX",
                        "technical_status": "COHERENCE_INFERRED",
                        "decision": "",
                        "proposed_value": "",
                        "comment": "",
                        "reviewer": "",
                        "reviewed_at": "",
                        "attestation_id": "",
                    }
                )
        # Final adjudication binds the complete NER + semantic reference, including
        # negations/abstentions and fields not represented by one literal fact.
        kit.append(
            {
                "review_id": hashlib.sha256((rid + "|ANNOTATION_BUNDLE").encode()).hexdigest()[:20],
                "record_id": rid,
                "population": group,
                "priority": "P0",
                "family": row["category"],
                "text": row["text"],
                "text_sha256": row["text_sha256"],
                "field_path": "annotation_bundle",
                "before": None,
                "after": {"entities": row["entities"], "expected": ref},
                "alternative": "REJECT_OR_PROPOSE_WITH_LITERAL_EVIDENCE",
                "reason": "FULL_NER_SEMANTICS_STATUS_REQUIRES_HUMAN_ADJUDICATION",
                "citation": {"text": row["text"], "start": 0, "end": len(row["text"])},
                "technical_responsible": "CODEX",
                "technical_status": "COHERENCE_INFERRED",
                "decision": "",
                "proposed_value": "",
                "comment": "",
                "reviewer": "",
                "reviewed_at": "",
                "attestation_id": "",
            }
        )
    for field in kit:
        field["field_sha256"] = field_digest(field)
    jsonl(out / "review/kit.jsonl", kit)
    table(out / "review/kit.csv", kit)
    jsonl(out / "review/technical_audit.jsonl", technical)
    dump(
        out / "review/progress.json",
        {
            "records_audited": len(technical),
            "populations": dict(Counter(x["population"] for x in technical)),
            "fields_pending": len(kit),
            "priorities": dict(Counter(x["priority"] for x in kit)),
            "human_reviewed": 0,
            "accepted": 0,
            "rejected": 0,
            "disputed": 0,
            "human_gold": "NO",
            "sample_method": "sha256(seed=20261025 + label + id), union of ceil(15%) per family/label stratum of 300 unchanged V1",
            "sampled_ids": sampled,
        },
    )
    (out / "review/GUIDE.md").write_text(
        """# Revisión comercial humana real\n\nKit CSV/JSONL por campo: texto sintético, cita, before/after, alternativa, regla y prioridad.\nRevisar P0 precios/cantidades primero, luego P1 unidades/ejes/relaciones y P2 descriptivos.\nCompletar decision=ACCEPT/REJECT/DISPUTE, reviewer, reviewed_at ISO-8601 con zona,\nattestation_id de acta/autorización externa y comentario. No editar text_sha256, field_sha256 ni review_id. El hash del campo liga before/after y evita aceptar decisiones antiguas sobre referencias cambiadas.\nPara modificaciones propuestas usar REJECT y proposed_value con evidencia en comentario;\nel importador no reescribe dataset ni trata una propuesta como verdad adjudicada.\n\n`python -m training.corpus_v2_rc2.review import <kit.jsonl> <decisions.jsonl> <output.json> --authorized-reviewers <registro_privado.json>`\nRegistro privado: lista de objetos reviewer/attestation_id/authorized=true; se suministra por responsable\nautorizado, nunca por el generador. No es autenticación criptográfica y debe verificarse externamente.\nSin este registro no se importa nada. IDs o fechas escritos por un algoritmo no acreditan humanidad.\nEl importador solo produce un ledger separado, no activa corpus ni cambia V1.\nDos revisores reales autorizados independientes que acepten todos los campos sin contradicción\npermiten GOLD_ELIGIBLE en el ledger; una aceptación permite HUMAN_REVIEWED por campo.\nRechazos/desacuerdos permanecen pendientes; un campo sin respuesta impide gold por registro.\nLos estados no equivalen a homologación productiva. El kit inicial tiene cero respuestas.\n\nÍtems privados: índice fuera de Git con archivo/hash/bloque/líneas y estado VERIFICABLE/DUDOSO/\nINCONSISTENTE/REQUIERE_REVISION_HUMANA. Conservar cuatro referencias parciales en cuarentena.\nFuentes, precios negociados y opiniones privadas no se añaden al kit público.\n"""
    )


def field_digest(field):
    bound = {k: field.get(k) for k in ("record_id", "field_path", "text_sha256", "before", "after")}
    return hashlib.sha256(
        json.dumps(bound, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def import_decisions(kit, decisions, authorized):
    lookup = {r["review_id"]: r for r in kit}
    auth = {(r["reviewer"], r["attestation_id"]) for r in authorized if r.get("authorized") is True}
    if not auth:
        raise ValueError("External authorized reviewer registry required")
    ledger = defaultdict(list)
    seen = set()
    for decision in decisions:
        rid = decision.get("review_id")
        reviewer = decision.get("reviewer")
        attestation = decision.get("attestation_id")
        if rid not in lookup or (reviewer, attestation) not in auth:
            raise ValueError("Unknown field or unauthorized reviewer/attestation")
        if decision.get("decision") not in {"ACCEPT", "REJECT", "DISPUTE"}:
            raise ValueError("Decision required")
        if (
            lookup[rid].get("field_sha256") != field_digest(lookup[rid])
            or decision.get("field_sha256") != lookup[rid]["field_sha256"]
        ):
            raise ValueError("Stale or modified field/reference; decision must bind field_sha256")
        if decision.get("text_sha256") != lookup[rid]["text_sha256"]:
            raise ValueError("Stale source text")
        stamp = datetime.fromisoformat(decision.get("reviewed_at", ""))
        if stamp.tzinfo is None:
            raise ValueError("Timestamp timezone required")
        if not decision.get("comment", "").strip():
            raise ValueError("Review rationale required")
        if (rid, reviewer) in seen:
            raise ValueError("Duplicate/conflicting decision from same reviewer")
        seen.add((rid, reviewer))
        ledger[rid].append(decision)
    fields = []
    for rid, record in sorted(lookup.items()):
        votes = ledger[rid]
        accept = bool(votes) and all(v["decision"] == "ACCEPT" for v in votes)
        fields.append(
            {
                "review_id": rid,
                "record_id": record["record_id"],
                "status": "HUMAN_REVIEWED" if accept else "DISPUTED" if votes else "PENDING",
                "gold_eligible_field": accept and len({v["reviewer"] for v in votes}) >= 2,
                "decisions": votes,
            }
        )
    grouped = defaultdict(list)
    for f in fields:
        grouped[f["record_id"]].append(f)
    records = [
        {
            "record_id": rid,
            "status": "GOLD_ELIGIBLE" if all(f["gold_eligible_field"] for f in fs) else "PENDING",
            "fields": len(fs),
        }
        for rid, fs in sorted(grouped.items())
    ]
    return {
        "fields": fields,
        "records": records,
        "human_gold": any(r["status"] == "GOLD_ELIGIBLE" for r in records),
        "dataset_modified": False,
        "external_identity_verification_required": True,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("operation", choices=["import"])
    p.add_argument("kit", type=Path)
    p.add_argument("decisions", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--authorized-reviewers", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Refusing to overwrite an existing human-decision ledger")
    import subprocess

    probe = a.output.parent.resolve()
    while not probe.exists():
        probe = probe.parent
    if (
        subprocess.run(
            ["git", "-C", str(probe), "rev-parse", "--is-inside-work-tree"], capture_output=True
        ).returncode
        == 0
    ):
        raise ValueError("Human decision ledger must remain outside Git")
    dump(
        a.output,
        import_decisions(
            read(a.kit), read(a.decisions), json.loads(a.authorized_reviewers.read_text())
        ),
    )


if __name__ == "__main__":
    main()
