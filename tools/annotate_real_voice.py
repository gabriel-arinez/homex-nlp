#!/usr/bin/env python3
"""Produce conservative script/document proposals without importing production NLP.

This is an annotation aid, not a gold-label generator. Unparsed clauses and
unresolved relations are explicit review work, never silently dropped fields.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import unicodedata
import wave
from collections import Counter, defaultdict
from pathlib import Path

FIELDS = (
    "product",
    "name",
    "quantity",
    "materials",
    "components",
    "thicknesses",
    "dimensions",
    "colors",
    "accessories",
    "model",
    "brand",
    "price",
    "commercial_unit",
    "technical_description",
)
SMALL = dict(
    zip(
        "cero un dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis diecisiete dieciocho diecinueve veinte veintiuno veintidos veintitres veinticuatro veinticinco veintiseis veintisiete veintiocho veintinueve".split(),
        range(30),
        strict=True,
    )
)
SMALL.update(
    {
        "uno": 1,
        "una": 1,
        "treinta": 30,
        "cuarenta": 40,
        "cincuenta": 50,
        "sesenta": 60,
        "setenta": 70,
        "ochenta": 80,
        "noventa": 90,
        "cien": 100,
        "ciento": 100,
        "doscientos": 200,
        "trescientos": 300,
        "cuatrocientos": 400,
        "quinientos": 500,
        "seiscientos": 600,
        "setecientos": 700,
        "ochocientos": 800,
        "novecientos": 900,
    }
)
NUMBER_WORDS = sorted([*SMALL, "mil", "coma", "y"], key=len, reverse=True)
NUM = (
    r"(?:\d+(?:[.,]\d+)*|(?:"
    + "|".join(w for w in NUMBER_WORDS if w not in {"y", "coma"})
    + r")(?:\s+(?:"
    + "|".join(NUMBER_WORDS)
    + r"))*)"
)
UNIT = r"(?:milímetros?|centímetros?|metros?|mm|cm|mts?)"
AXIS = r"(?:ancho|largo|alto|altura|profundidad|diámetro)"
LEXICONS = {
    "materials": r"melamina|melanina|MDP|HDF|PVC|acero(?: inoxidable| cromado)?|madera(?: de eucalipto)?|nylon|malla|vidrio templado|espuma(?: de poliuretano| inyectada)?|esponja|cuero ecológico|tela|perfil metálico",
    "components": r"cajoneras?|credenzas?|mes[oó]n|tableros?|tapas?|panel(?:es)? frontal(?:es)?|laterales?|espaldar|estructura|patas?|puertas?|repisas?|divisiones|fald[oó]n|asiento|respaldo|cubo(?: móvil)?|módulos?",
    "accessories": r"USB|HDMI|tomacorrientes?|toma corriente|caja eléctrica|pasacables|portateclado|chapas?(?: de seguridad)?|cerraduras?|llaves?|jaladores?(?: metálicos?)?|rieles?(?: telescópicos?)?|topes?(?: de goma)?|tapacantos?|tapacanto|zapatas?|minifix|ruedas?|membrana(?: protectora| de protección)?|almohadones|apoyabrazos|reposacabezas|reposapiés|apoyo lumbar|pistón de gas",
    "colors": r"negro|blanco|cedro|olmo|azul|gris|café(?: oscuro)?|capri|celeste|turquesa|guindo|plomo|amarillo|maderable|a elección|según diseño|dorados",
}


def fold(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    )


def number(text):
    """Strict bounded Spanish cardinal/decimal parser; unknown text abstains."""
    text = fold(text.strip())
    if re.fullmatch(r"\d+(?:[.,]\d+)*", text):
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", text):
            text = text.replace(".", "")
        else:
            text = text.replace(",", ".")
        try:
            return float(text) if "." in text else int(text)
        except ValueError:
            return None
    if " coma " in text:
        left, right = text.split(" coma ", 1)
        integer, fractional = number(left), number(right)
        if integer is None or fractional is None or fractional >= 100:
            return None
        return integer + fractional / (10 ** len(str(fractional)))

    def below_thousand(words):
        if not words:
            return 0
        if len(words) == 1:
            return SMALL.get(words[0])
        hundreds = SMALL.get(words[0], -1)
        if hundreds >= 100:
            # "cien" is terminal; "ciento" accepts a smaller suffix.
            if words[0] == "cien":
                return None
            rest = below_thousand(words[1:])
            return hundreds + rest if rest is not None and 0 < rest < 100 else None
        if (
            len(words) == 3
            and 30 <= hundreds <= 90
            and hundreds % 10 == 0
            and words[1] == "y"
            and 1 <= SMALL.get(words[2], -1) <= 9
        ):
            return hundreds + SMALL[words[2]]
        return None

    words = text.split()
    if not words or words.count("mil") > 1:
        return None
    if "mil" in words:
        index = words.index("mil")
        left = below_thousand(words[:index]) if index else 1
        right = below_thousand(words[index + 1 :])
        if left is None or right is None or not 1 <= left <= 999:
            return None
        return left * 1000 + right
    return below_thousand(words)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence(text, start, end, source):
    return {"source": source, "start": start, "end": end, "raw": text[start:end]}


def annotate(text, source, asr_text):
    """Return proposals for every field, including absent and unresolved fields.

    Only literal tokens and explicit unambiguous scalar rules are verified.
    Component/axis relations remain pending even where a number is parsed.
    """
    fields = []

    def add(field, start, end, value=None, unit=None, verified=False, **extra):
        raw = text[start:end]
        exact_asr = None
        match = re.search(re.escape(raw), asr_text, re.I) if raw else None
        if match:
            exact_asr = evidence(asr_text, match.start(), match.end(), "asr")
        item = {
            "field": field,
            "verification_scope": "LITERAL_OR_SCALAR_ONLY",
            "value": value,
            "unit": unit,
            "axis": None,
            "currency": None,
            "modality": None,
            "evidence": [evidence(text, start, end, source)],
            "document_presence": "PRESENT" if source == "document" else "NOT_CHECKED",
            "script_presence": "PRESENT" if source == "script" else "NOT_ESTABLISHED",
            "asr_status": "EXACT_TEXT_CORROBORATION" if match else "NO_EXACT_TEXT_CORROBORATION",
            "asr_evidence": exact_asr,
            "association": {"status": "UNRESOLVED", "component": None},
            "ambiguity": [] if verified else ["SEMANTIC_OR_RELATION_REVIEW_REQUIRED"],
            "verification_status": (
                "SCRIPT_EVIDENCE_VERIFIED"
                if verified and source == "script"
                else "DOCUMENT_EVIDENCE_VERIFIED"
                if verified
                else "PENDING_SEMANTIC_REVIEW"
            ),
            "acoustic_status": "PENDING_HUMAN_LISTENING",
            "eligible_script_denominator": verified and source == "script",
            "eligible_acoustic_denominator": False,
        }
        item.update(extra)
        fields.append(item)
        return item

    # The opening noun phrase is proposed verbatim, never a document title as speech.
    opening = re.match(r"[^,.\n]+", text)
    if opening:
        for field in ("product", "name"):
            add(
                field,
                *opening.span(),
                value=opening.group(),
                ambiguity=["OPENING_PHRASE_BOUNDARY_REQUIRES_REVIEW"],
            )
    quantity = re.match(r"(" + NUM + r")\s+(?=\w)", text, re.I)
    if quantity and number(quantity.group(1)) is not None:
        add(
            "quantity",
            *quantity.span(1),
            value=number(quantity.group(1)),
            unit="commercial_items",
            verified=True,
            association={"status": "EXPLICIT_OPENING", "component": "main_order"},
        )
    for field, pattern in LEXICONS.items():
        for match in re.finditer(r"\b(?:" + pattern + r")\b", text, re.I):
            # Literal semantic token only; do not claim component material relations.
            item = add(
                field,
                *match.span(),
                value=match.group().lower(),
                verified=field in {"materials", "accessories", "colors"},
            )
            if field in {"components", "accessories"}:
                prefix = text[max(0, match.start() - 60) : match.start()]
                count = re.search(
                    r"(" + NUM + r")\s+(?:(?:puertos?|conexiones)\s+)?$", prefix, re.I
                )
                item["count_proposal"] = number(count.group(1)) if count else None
                item["count_unit"] = "units"
                item["count_status"] = (
                    "LITERAL_COUNT_VERIFIED_ASSOCIATION_PENDING"
                    if count and item["count_proposal"] is not None
                    else "NOT_STATED_OR_UNRESOLVED"
                )
                if count:
                    offset = max(0, match.start() - 60)
                    item["evidence"].append(
                        evidence(text, offset + count.start(1), offset + count.end(1), source)
                    )
    # Compound metre expressions require an explicit axis. Otherwise keep the
    # entire residual and abstain rather than output a misleading partial scalar.
    measure_pattern = (
        r"(?P<initial>" + NUM + r")\s+(?P<unit>" + UNIT + r")"
        r"(?:\s+(?:con\s+)?(?P<tail>" + NUM + r")\s+"
        r"(?:centímetros?\s+)?de\s+(?P<compound_axis>" + AXIS + r")"
        r"|\s+de\s+(?P<axis>" + AXIS + r"))?"
    )
    for match in re.finditer(measure_pattern, text, re.I):
        unit = fold(match.group("unit"))
        unit = (
            "mm"
            if unit.startswith("mili") or unit == "mm"
            else "cm"
            if unit.startswith("cent") or unit == "cm"
            else "m"
        )
        following = text[match.end() : match.end() + 70]
        field = (
            "thicknesses" if unit == "mm" or re.match(r"\s+de espesor", following) else "dimensions"
        )
        preceding_clause = re.split(r"[.,;]", text[: match.start()])[-1]
        value = number(match.group("initial"))
        axis = match.group("compound_axis") or match.group("axis")
        tail = number(match.group("tail")) if match.group("tail") else None
        ambiguous = bool(re.search(r"\b(?:por|entre)\b", preceding_clause[-70:], re.I))
        # A cardinal immediately after this unit or a prior unit immediately
        # before this match means a partially matched compound/coordination.
        if (
            not match.group("tail")
            and not axis
            and re.match(r"\s+(?:con\s+)?" + NUM + r"\b", following, re.I)
        ):
            ambiguous = True
        if re.search(UNIT + r"\s+$", preceding_clause, re.I):
            ambiguous = True
        if match.group("tail"):
            if unit == "m" and value is not None and tail is not None and 0 <= tail < 100:
                value, unit = value * 100 + tail, "cm"
            else:
                ambiguous = True
        if ambiguous:
            value = None
        scalar_verified = value is not None and (bool(axis) or field == "thicknesses")
        add(
            field,
            *match.span(),
            verified=scalar_verified,
            value=value,
            unit=unit,
            axis=fold(axis) if axis else None,
            ambiguity=["COMPONENT_ASSOCIATION_PENDING"]
            if scalar_verified
            else ["COMPONENT_AND_COMPOUND_MEASURE_REVIEW_REQUIRED"],
        )
    # Explicit labels are textual proposals, not decoded hidden original codes.
    for field, pattern in {
        "model": r"(?:modelo|código)\s+([^,.\n]+)",
        "brand": r"marca\s+([^,.\n]+)",
        "commercial_unit": r"\bUnidad\s+(metro cuadrado|pieza|barra|juego)\b",
    }.items():
        for match in re.finditer(pattern, text, re.I):
            add(
                field,
                *match.span(1),
                value=match.group(1),
                verified=field in {"brand", "commercial_unit"},
            )
    price = (
        r"\bprecio\s+(?:(unitario|por juego|de lista|total|total negociado)\s+)?(?:de\s+)?("
        + NUM
        + r")\s+(bolivianos|Bs\.?)\b"
    )
    for match in re.finditer(price, text, re.I):
        amount = number(match.group(2))
        modality = {
            "unitario": "UNIT",
            "por juego": "PER_SET",
            "de lista": "LIST",
            "total": "TOTAL",
            "total negociado": "NEGOTIATED_TOTAL",
        }.get(fold(match.group(1) or ""), "UNSPECIFIED")
        add(
            "price",
            *match.span(),
            value=amount,
            unit="money",
            currency="BOB",
            modality=modality,
            verified=amount is not None,
            association={"status": "EXPLICIT_PRICE_CLAUSE", "component": "main_order"},
        )
    if source == "document":
        # Missing source currency stays unknown, never silently inherits BOB.
        for match in re.finditer(
            r"\b(precio unitario|precio total|total)\s+(" + NUM + r")", text, re.I
        ):
            if any(
                f["field"] == "price" and f["evidence"][0]["start"] == match.start() for f in fields
            ):
                continue
            amount = number(match.group(2))
            add(
                "price",
                *match.span(),
                value=amount,
                unit="money",
                currency=None,
                modality="UNIT" if fold(match.group(1)) == "precio unitario" else "TOTAL",
                verified=amount is not None,
                association={"status": "EXPLICIT_PRICE_CLAUSE", "component": "main_order"},
            )
    # Preserve ALL text, not just unmatched words: these residuals explicitly carry
    # inherited units, multi-axis dimensions, omitted currency and complex models.
    for match in re.finditer(r"[^.\n]*(?:[.\n]|$)", text):
        if match.start() != match.end():
            add(
                "technical_description",
                *match.span(),
                value=match.group(),
                ambiguity=["FULL_CLAUSE_RESIDUAL_NOT_STRUCTURED_GOLD"],
            )
    present = {f["field"] for f in fields}
    for field in FIELDS:
        if field not in present:
            fields.append(
                {
                    "field": field,
                    "value": None,
                    "unit": None,
                    "axis": None,
                    "currency": None,
                    "modality": None,
                    "evidence": [],
                    "document_presence": "NOT_DETECTED" if source == "document" else "NOT_CHECKED",
                    "script_presence": "NOT_DETECTED" if source == "script" else "NOT_ESTABLISHED",
                    "absence_status": (
                        "NOT_STATED"
                        if field == "price" and not re.search(r"precio|total", text, re.I)
                        else "UNSUPPORTED_OR_UNPARSED_NOT_CONFIRMED_ABSENT"
                    ),
                    "asr_status": "NOT_APPLICABLE",
                    "asr_evidence": None,
                    "association": {"status": "UNRESOLVED", "component": None},
                    "ambiguity": ["NO_RULE_MATCH_IS_NOT_PROOF_OF_ABSENCE"],
                    "verification_status": "PENDING_SEMANTIC_REVIEW",
                    "acoustic_status": "PENDING_HUMAN_LISTENING",
                    "eligible_script_denominator": False,
                    "eligible_acoustic_denominator": False,
                }
            )
    return fields


def leakage_groups(rows):
    """Connected families, shared source records, and identical source hashes."""
    parent = {r["id"]: r["id"] for r in rows}

    def root(key):
        while parent[key] != key:
            key = parent[key]
        return key

    seen = {}
    for row in rows:
        keys = [("family", row["grupo_familia"])]
        if row.get("titulo_fuente"):
            keys.append(("title", re.sub(r"\s+", " ", fold(row["titulo_fuente"]).strip())))
        keys += [("record", row["archivo_origen"], n) for n in row["registros_fuente"]]
        if row.get("sha256_fuente"):
            keys.append(("hash", row["sha256_fuente"]))
        for key in keys:
            if key in seen:
                parent[root(row["id"])] = root(seen[key])
            seen[key] = row["id"]
    members = defaultdict(list)
    for identifier in parent:
        members[root(identifier)].append(identifier)
    return {identifier: "DEV-" + min(group) for group in members.values() for identifier in group}


def prepare_output(path):
    path.mkdir(parents=True, exist_ok=False)


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build(corpus, baseline, output):
    scripts_path = corpus / "referencias/guiones_referencia_pregrabacion.jsonl"
    documents_path = corpus / "referencias/trazabilidad_fuentes.jsonl"
    scripts = [json.loads(line) for line in scripts_path.read_text().splitlines()]
    documents = {r["id"]: r for r in map(json.loads, documents_path.read_text().splitlines())}
    manifest_path = corpus / "manifiesto.csv"
    with manifest_path.open(encoding="utf-8-sig") as stream:
        manifest = {r["id"]: r for r in csv.DictReader(stream, delimiter=";")}
    assert len(manifest) == len(scripts) == 120 and set(manifest) == {r["id"] for r in scripts}
    groups = leakage_groups(scripts)
    inputs = [scripts_path, documents_path, manifest_path]
    cases, preservation, review = [], [], []
    for script in scripts:
        identifier = script["id"]
        row = manifest[identifier]
        frozen_path = baseline / f"{identifier}.json"
        frozen = json.loads(frozen_path.read_text())
        assert frozen["reference"] == script["guion"]
        assert row["categoria"] == script["categoria"]
        original = corpus / row["ruta_audio_esperada"]
        wav = corpus / row["ruta_audio_compatible_asr"]
        for path, key in ((original, "original_sha256"), (wav, "wav_sha256")):
            actual = digest(path)
            if actual != frozen["audio"][key]:
                raise ValueError(f"Frozen audio hash mismatch: {identifier} {key}")
            preservation.append({"path": str(path.relative_to(corpus)), "sha256_before": actual})
        document = documents[identifier]["fuente_original"]
        text = script["guion"]
        script_fields = annotate(text, "script", frozen["asr"]["text_original"])
        document_fields = annotate(document, "document", frozen["asr"]["text_original"])
        for field in script_fields:
            raw = field["evidence"][0]["raw"] if field["evidence"] else ""
            field["document_presence"] = (
                "EXACT_TEXT_PRESENT"
                if raw and raw.casefold() in document.casefold()
                else "NO_EXACT_MATCH_SEMANTIC_REVIEW_PENDING"
            )
        for field in document_fields:
            raw = field["evidence"][0]["raw"] if field["evidence"] else ""
            field["script_presence"] = (
                "EXACT_TEXT_PRESENT"
                if raw and raw.casefold() in text.casefold()
                else "NO_EXACT_MATCH_SEMANTIC_REVIEW_PENDING"
            )
        segments = []
        with wave.open(str(wav), "rb") as source:
            duration = source.getnframes() / source.getframerate()
            params = source.getparams()
            for index, segment in enumerate(frozen["asr"]["segments"]):
                start = max(0, float(segment["start_seconds"]) - 0.4)
                end = min(duration, float(segment["end_seconds"]) + 0.4)
                if end <= start:
                    continue
                rel = Path("clips") / f"{identifier}-{index:03d}.wav"
                source.setpos(int(start * params.framerate))
                frames = source.readframes(
                    int(end * params.framerate) - int(start * params.framerate)
                )
                with wave.open(str(output / rel), "wb") as target:
                    target.setparams(params)
                    target.writeframes(frames)
                segments.append(
                    {
                        "clip": str(rel),
                        "start_seconds": start,
                        "end_seconds": end,
                        "asr_text": segment["text"],
                        "alignment_status": "ASR_SEGMENT_NOT_FORCED_SCRIPT_ALIGNMENT",
                        "human_status": "PENDING_HUMAN_LISTENING",
                    }
                )
        # Always provide full replay: ASR segment boundaries may omit speech.
        review.append(
            {
                "id": identifier,
                "full_replay": wav.as_uri(),
                "duration_seconds": duration,
                "segments": segments,
                "fields_requiring_listening": list(range(len(script_fields))),
            }
        )
        category = frozen["category"]
        case = {
            "schema_version": "reference-proposals/1",
            "id": identifier,
            "category": category,
            "development_only": True,
            "leakage_group": groups[identifier],
            "family": script["grupo_familia"],
            "source_file": script["archivo_origen"],
            "source_records": script["registros_fuente"],
            "source_sha256": script["sha256_fuente"],
            "source_text_sha256": hashlib.sha256(document.encode()).hexdigest(),
            "script_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "document_text": document,
            "script_text": text,
            "asr_text": frozen["asr"]["text_original"],
            "frozen_asr_artifact_sha256": digest(frozen_path),
            "source_control_notes": script["observaciones_control"],
            "acoustic_status": "PENDING_HUMAN_LISTENING",
            "script_fields": script_fields,
            "document_fields": document_fields,
            "review_index_id": identifier,
        }
        cases.append(case)
        dump(output / "cases" / f"{identifier}.json", case)
    categories = Counter(c["category"] for c in cases)
    assert categories == {"MUEBLE_MEDIDA": 73, "SILLA": 27, "PISO_FLOTANTE": 7, "OTRO": 13}, (
        categories
    )
    for entry in preservation:
        entry["sha256_after"] = digest(corpus / entry["path"])
        assert entry["sha256_before"] == entry["sha256_after"]
    fields = [f for c in cases for f in c["script_fields"]]
    summary = {
        "cases": len(cases),
        "categories": dict(categories),
        "audio_hashes_preserved": len(preservation),
        "script_proposals": len(fields),
        "script_verified_denominator": sum(f["eligible_script_denominator"] for f in fields),
        "acoustic_verified_denominator": 0,
        "human_listening_pending_cases": 120,
        "semantic_pending_proposals": sum(
            f["verification_status"] == "PENDING_SEMANTIC_REVIEW" for f in fields
        ),
        "denominator_by_field": dict(
            Counter(f["field"] for f in fields if f["eligible_script_denominator"])
        ),
        "proposal_count_by_field": dict(Counter(f["field"] for f in fields)),
        "leakage_groups": len(set(groups.values())),
        "input_hashes": {str(p.relative_to(corpus)): digest(p) for p in inputs},
        "limitations": [
            "Not complete commercial gold: semantic relations and residual clauses require review.",
            "All acoustic labels pending human listening; ASR is corroboration only.",
            "No-rule-match is unsupported/unparsed, not established absence.",
            "Script denominator is textual scalar verification only, never acoustic gold.",
            "Family/source groups are minimum leakage exclusions, not independent holdouts.",
        ],
    }
    dump(output / "summary.json", summary)
    dump(output / "audio-preservation.json", preservation)
    dump(output / "audio-review-index.json", review)
    dump(
        output / "holdout-protocol.json",
        {
            "development_ids": sorted(manifest),
            "development_groups": groups,
            "independent_audio_available": False,
            "generalization_metrics": None,
            "protocol": [
                "Freeze rules and normalization versions before collection.",
                "Collect new speakers, rooms, devices and commercial families not used in development.",
                "Exclude connected source/family duplicates from holdout.",
                "Have two independent humans listen and annotate fields, resolving disagreements.",
                "Run frozen baseline and candidate once; report all fields, abstentions and denominators.",
                "Do not tune on holdout; move exposed holdout to development and collect another holdout.",
            ],
        },
    )
    with (output / "cases.jsonl").open("w") as stream:
        for case in cases:
            stream.write(json.dumps(case, ensure_ascii=False) + "\n")
    lines = [
        "<!doctype html><meta charset='utf-8'><title>Local audio reference review</title>",
        "<h1>120 development cases — human listening pending</h1>",
        "<p>Segment text is automatic ASR, not verified speech. Review all field proposals using the JSON case; full replay catches omitted segments.</p>",
    ]
    for item in review:
        lines.append(
            f"<h2>{item['id']}</h2><a href='{html.escape(item['full_replay'])}'>Full WAV replay</a>"
        )
        for segment in item["segments"]:
            lines.append(
                f"<p>{segment['start_seconds']:.2f}–{segment['end_seconds']:.2f}s {html.escape(segment['asr_text'])}</p><audio controls preload='none' src='{segment['clip']}'></audio>"
            )
    (output / "audio-review.html").write_text("\n".join(lines), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus", required=True, type=Path, help="Read-only original corpus directory"
    )
    parser.add_argument(
        "--baseline", required=True, type=Path, help="Frozen original ASR case JSON directory"
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="NEW local-only reference artifact directory; refuses reuse",
    )
    args = parser.parse_args()
    prepare_output(args.output)
    (args.output / "cases").mkdir()
    (args.output / "clips").mkdir()
    print(json.dumps(build(args.corpus, args.baseline, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
