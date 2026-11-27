"""Finite furniture knowledge with literal evidence; never rewrites input text."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib.resources import files

from homex_nlp.contracts.evidence import Candidate, Warning
from homex_nlp.contracts.item import Color


@lru_cache(maxsize=1)
def lexicon():
    return json.loads(files("homex_nlp").joinpath("resources/furniture_lexicon.json").read_text())


def material_entry(raw):
    return next((x for x in lexicon()["materials"] if re.fullmatch(x["pattern"], raw, re.I)), None)


def recovery_material_context(text, start):
    return bool(re.search(r"\b(?:de|en|con)\s+$", text[max(0, start - 45) : start], re.I))


def commercial_family(name):
    # Keep the existing supported meeting-table family independent of capacity.
    if re.match(r"mesas?\s+de\s+reuni[oó]n\b", name, re.I):
        return "mesa de reunión"
    if re.match(r"cubos?\s+m[oó]vil(?:es)?\b", name, re.I):
        return "cubo móvil"
    if re.match(r"estaci(?:[oó]n|ones)\s+de\s+trabajo", name, re.I):
        return "estación de trabajo"
    first = name.split()[0].casefold()
    if first.endswith("es") and first[:-2].endswith("r"):
        first = first[:-2]
    elif first.endswith("s"):
        first = first[:-1]
    return {"gabetero": "gavetero", "gadetero": "gavetero", "estanteria": "estantería"}.get(
        first, first
    )


def noncommercial_furniture_context(text):
    """Reject explicit test/retrospective intent, not individual forbidden words."""
    return bool(
        re.search(
            r"\b(?:probando|probar|prueba\s+de)\b[^.;]{0,65}\b(?:micr[oó]fono|audio|voz)\b"
            r"|\b(?:ayer\s+hablamos|no\s+vamos\s+a\s+(?:comprar|cotizar))\b",
            text,
            re.I,
        )
    )


def enrich_knowledge(item, candidates, text, warnings):
    """Preserve finite aliases and bounded unsupported service specifications."""

    def add(start, end, label, value, decision="ACCEPTED", reason=None, component=None):
        existing = next(
            (c for c in candidates if c.start == start and c.end == end and c.label == label), None
        )
        if existing:
            return existing
        c = Candidate(
            candidate_id=f"c{len(candidates) + 1}",
            label=label,
            start=start,
            end=end,
            text=text[start:end],
            source="PARSER",
            normalized_value=value,
            decision=decision,
            reason=reason,
            component_ref=component,
        )
        candidates.append(c)
        if decision == "UNRESOLVED":
            item.unresolved.append(c.candidate_id)
        return c

    def recovery(c, value, rule):
        add(
            c.start,
            c.end,
            "RECUPERACION_LEXICA",
            value,
            "UNRESOLVED",
            f"Contextual lexical recovery ({rule}); confirm the proposed interpretation",
            c.component_ref,
        )
        warnings.append(
            Warning(
                code="UNKNOWN_TERM",
                path="/candidates",
                severity="REVIEW",
                message=f"Confirm contextual interpretation of {c.text!r} as {value!r}.",
            )
        )

    for c in list(candidates):
        if (
            c.label == "PRODUCTO"
            and c.decision == "ACCEPTED"
            and re.fullmatch(r"gadeteros?", c.text, re.I)
        ):
            value = "gaveteros" if c.text.casefold().endswith("s") else "gavetero"
            c.normalized_value = value
            item.name = value
            item.furniture_type_candidate = "gavetero"
            recovery(c, value, "counted_furniture_identity")
        if c.label == "MATERIAL" and c.decision == "ACCEPTED":
            entry = material_entry(c.text)
            if entry:
                c.normalized_value = entry.get("value", c.text)
                add(
                    c.start,
                    c.end,
                    "ROL_MATERIAL",
                    {"value": c.normalized_value, "role": entry["role"]},
                    "UNRESOLVED",
                    "Domain material classification, not an explicitly spoken substrate/coating relationship",
                    c.component_ref,
                )
                if entry.get("recovery"):
                    recovery(c, c.normalized_value, "technical_material_phrase")
        if (
            c.label == "COLOR"
            and c.decision == "ACCEPTED"
            and re.fullmatch(r"hueng[uü]e", c.text, re.I)
        ):
            c.normalized_value = "wengué"
            recovery(c, "wengué", "explicit_decorative_color")

    for match in re.finditer(r"\b(?:Novopan|nobopan|novo\s+pan)\b", text, re.I):
        before = text[max(0, match.start() - 65) : match.start()]
        if not re.search(r"\b(?:tablero|melam[ií]nic[oa]|melamina|MDP|MDF|marca)\b", before, re.I):
            continue
        c = add(match.start(), match.end(), "MARCA", "Novopan")
        if not re.fullmatch("Novopan", match.group(), re.I):
            recovery(c, "Novopan", "board_brand_context")

    for choice in re.finditer(r"\bcolor\s+(?:a\s+)?elecci[oó]n\b", text, re.I):
        add(
            choice.start(),
            choice.end(),
            "SELECCION_COLOR",
            None,
            "UNRESOLVED",
            "Color selection remains pending; no color was pronounced",
        )
    for clause in re.finditer(
        r"\bcolor\s+(?P<value>[^.;\n]+?)(?=[.;\n]|\b(?:garant[ií]a|precio|procedencia)\b|$)",
        text,
        re.I,
    ):
        if re.fullmatch(r"(?:a\s+)?elecci[oó]n\s*", clause["value"], re.I):
            continue
        known = [
            c
            for c in candidates
            if c.label == "COLOR"
            and clause.start("value") <= c.start
            and c.end <= clause.end("value")
            and c.decision == "ACCEPTED"
        ]
        rest = text[clause.start("value") : clause.end("value")]
        for c in sorted(known, key=lambda x: x.start, reverse=True):
            a, b = c.start - clause.start("value"), c.end - clause.start("value")
            rest = rest[:a] + " " + rest[b:]
        if re.sub(r"\b(?:con|y)\b|[\s,]+", "", rest, flags=re.I):
            for c in known:
                c.decision = "UNRESOLVED"
                c.reason = "Color combination contains an unknown term; do not silently select only a known member"
                if c.candidate_id not in item.unresolved:
                    item.unresolved.append(c.candidate_id)
            item.primary_color = item.secondary_color = None
            add(
                clause.start("value"),
                clause.end("value"),
                "COLOR_NO_RESUELTO",
                clause["value"].strip(),
                "UNRESOLVED",
                "Confirm the complete literal color description",
            )

    colors = [
        c
        for c in candidates
        if c.label == "COLOR" and c.decision == "ACCEPTED" and c.component_ref is None
    ]
    if len(colors) == 1 and item.primary_color is None:
        c = colors[0]
        main = next(
            (x for x in candidates if x.label == "PRODUCTO" and x.decision == "ACCEPTED"), None
        )
        explicit = re.search(r"\bcolor\s+$", text[max(0, c.start - 25) : c.start], re.I)
        adjacent = main and re.fullmatch(r"\s+", text[main.end : c.start])
        ambiguous = re.search(
            r"\b(?:o|mejor|corrijo|perd[oó]n|sino)\b", text[main.end :] if main else text, re.I
        )
        if (explicit or adjacent) and not ambiguous:
            value = c.normalized_value or c.text.casefold()
            value = re.sub(r"^blanc[oa]s?$", "blanco", str(value))
            value = re.sub(r"^negr[oa]s?$", "negro", value)
            c.normalized_value = value
            item.primary_color = Color(value=value, evidence_ids=[c.candidate_id])

    for accessory in item.accessories:
        if re.match(r"conjalador(?:es)?\b", accessory.name, re.I):
            c = next(x for x in candidates if x.candidate_id in accessory.evidence_ids)
            accessory.name = re.sub(r"^con", "", accessory.name, flags=re.I)
            recovery(c, accessory.name, "joined_accessory_connector")

    # These are bounded clauses, not an indiscriminate transcript copy.
    pattern = re.compile(
        r"\b(?:garant[ií]a|procedencia|origen|incluye\s+(?:instalaci[oó]n|entrega|traslado)|"
        r"(?:instalaci[oó]n|entrega|traslado)\s+(?:incluid[oa]|a\s+)|"
        r"resistente\s+a|condiciones\s+de\s+fabricaci[oó]n)\b"
        r"[^.;\n]*?(?=[.;\n]|\b(?:precio|color|garant[ií]a|procedencia)\b|$)",
        re.I,
    )
    retained = []
    for m in pattern.finditer(text):
        segment = m.group().strip()
        if not segment:
            continue
        add(
            m.start(),
            m.start() + len(segment),
            "ESPECIFICACION",
            segment,
            "UNRESOLVED",
            "Technical/service specification retained for human review",
        )
        retained.append(segment)
    if retained:
        item.observations = "; ".join(dict.fromkeys(filter(None, [item.observations, *retained])))
