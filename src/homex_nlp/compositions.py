"""Positive composition and owner evidence, independent of evaluation identifiers."""

from __future__ import annotations

import re
import unicodedata

from homex_nlp.contracts.evidence import Candidate
from homex_nlp.contracts.item import Color


def fold(value):
    return "".join(
        c for c in unicodedata.normalize("NFD", value.casefold()) if unicodedata.category(c) != "Mn"
    )


def composition_reference(text, principal, mention, dependent):
    from homex_nlp.product_relations import descriptive_reference, head

    family, root = head(mention.text), head(principal.text)
    before = text[principal.end : mention.start]
    after = text[mention.end :]
    related = {
        "escritorio": {"credenza", "estante", "cubo", "cajonera", "casillero", "archivador"},
        "cocineta": {"gabinete", "alacena", "cajonera"},
        "mueble": {"gabinete", "cajonera", "estante", "mesa"},
    }.get(root, set())
    connector = re.search(
        r"\b(?:con|incluye|incorpora|compuesto\s+por)\s+(?:(?:un[ao]?|dos|tres|\d+)\s+)?$",
        before,
        re.I,
    )
    if family in related and connector:
        return True
    if family in dependent and descriptive_reference(text, mention, bare_comma=True):
        return True
    # A bare same-owner description in a technical list survives ASR comma
    # segmentation, but a fresh article/count still introduces a new item.
    if (family in dependent or family == root) and re.search(r"[,;.]\s*$", before):
        described = re.match(
            r"\s+con\s+(?:(?:un[ao]?|dos|tres|cuatro|varias?|\d+)\s+)?(?:cajones?|puertas?|ruedas?|repisas?|rieles?)\b",
            after,
            re.I,
        )
        if described:
            return True
    if (
        root == "mueble"
        and family == "mesa"
        and re.search(r"\b(?:superior|inferior|interior)\b", mention.text, re.I)
        and re.search(r"[.;,]\s*$", before)
    ):
        return True
    # A technical component list is not an independent commercially counted item.
    if root == "escritorio" and family in {"estante", "cubo"}:
        context = before[-180:]
        technical = re.search(r"\b(?:bandeja|porta\s*CPU|fald[oó]n|cajoner[ií]a)\b", context, re.I)
        if (
            technical
            and re.search(r"(?:,|\by)\s*$", context, re.I)
            and re.match(r"\s+(?:de|con)\b", after, re.I)
        ):
            return True
    if family == "archivador":
        if re.search(r"\b(?:cajoner[ií]a|cajones?)\b[^.;]{0,130}$", before, re.I):
            return True
        if re.search(r"\bpara\s+$", before, re.I) and re.match(r"\s+de\s+palanca\b", after, re.I):
            return True
    return False


def refine_relations(item, candidates, text, warnings):
    """Refine explicit owner frames and repeated descriptions, never nearest-only."""
    from homex_nlp.product_relations import head

    by_id = {c.candidate_id: c for c in candidates}

    def evidence(value):
        return next((by_id[e] for e in value.evidence_ids if e in by_id), None)

    def add(start, end, label, value, reason, component=None):
        c = Candidate(
            candidate_id=f"c{len(candidates) + 1}",
            label=label,
            start=start,
            end=end,
            text=text[start:end],
            source="PARSER",
            normalized_value=value,
            component_ref=component,
            decision="UNRESOLVED",
            reason=reason,
        )
        candidates.append(c)
        by_id[c.candidate_id] = c
        item.unresolved.append(c.candidate_id)
        return c

    def assign(dimension, owner):
        dimension.component_ref = owner
        c = evidence(dimension)
        if c:
            c.component_ref = owner

    product = next(
        (c for c in candidates if c.label == "PRODUCTO" and c.decision == "ACCEPTED"), None
    )
    components = [(c, evidence(c)) for c in item.components]
    # Explicit repeated owner noun + contiguous dimensional enumeration.
    markers = []
    for component, mention in components:
        for c in candidates:
            if c.label == "COMPONENTE" and c.candidate_id in component.evidence_ids:
                markers.append((c, component.component_id))
    if product:
        markers.extend(
            (c, None)
            for c in candidates
            if c.label == "PRODUCTO"
            and head(c.text) == head(product.text)
            and (
                c.decision == "ACCEPTED"
                or c.reason == "Referential/component mention, not an independent product"
            )
        )
    ordered = sorted(
        [(evidence(d), d) for d in item.dimensions if evidence(d)], key=lambda pair: pair[0].start
    )
    for marker, owner in sorted(markers, key=lambda x: x[0].start):
        end = marker.end
        started = False
        for c, d in ordered:
            if c.start < end:
                continue
            connector = text[end : c.start]
            pattern = (
                r"\s*(?:,|y|,\s*y|por)\s*"
                if started
                else r"\s*,?\s*(?:(?:de|mide|miden|tiene|con)\s+)"
            )
            if not re.fullmatch(pattern, connector, re.I):
                break
            assign(d, owner)
            started = True
            end = c.end

    for component, mention in components:
        if not mention or not product:
            continue
        prefix = text[product.end : mention.start]
        # Drawer count in the main gavetero's noun phrase is not a new dimension owner.
        definition = (
            head(product.text) in {"gavetero", "cajonera", "cubo"}
            and head(component.name) in {"cajone", "cajon"}
            and re.fullmatch(r"\s+de\s+(?:\d+|un[ao]?|dos|tres|cuatro|cinco)\s+", prefix, re.I)
        )
        # At least two axes after a decorated frame describe the furniture envelope.
        frame = bool(
            re.fullmatch(r"patas?\s+met[aá]licas?", component.name, re.I)
            and re.fullmatch(r"\s+con\s+", prefix, re.I)
        )
        boundary = next(
            (c.start for c in candidates if c.label == "COMPONENTE" and c.start > mention.end),
            len(text),
        )
        end_sentence = re.search(r"[.;](?!\d)", text[mention.end : boundary])
        if end_sentence:
            boundary = mention.end + end_sentence.start()
        scoped = [d for c, d in ordered if mention.end <= c.start < boundary]
        if definition or frame and len({d.axis for d in scoped if d.axis}) >= 2:
            for d in scoped:
                assign(d, None)

    # Repeated drawer descriptions merge only identical unqualified groups and counts.
    seen = {}
    for component, mention in list(components):
        if not mention or not (
            fold(component.name) in {"cajones", "cajonera", "credenza", "credenza lateral"}
            or fold(component.name).startswith("gabinete")
        ):
            continue
        counts = {
            str(c.normalized_value)
            for c in candidates
            if c.label == "CANTIDAD_INTERNA"
            and c.component_ref == component.component_id
            and c.decision == "ACCEPTED"
        }
        name_key = (
            "credenza" if fold(component.name).startswith("credenza") else fold(component.name)
        )
        key = (name_key, tuple(sorted(counts)))
        old = seen.get(key)
        new_group = re.search(
            r"\b(?:otra?|otros|segund[oa]s?|por\s+lado)\s+(?:(?:\d+|dos|tres|cuatro)\s+)?$",
            text[max(0, mention.start - 40) : mention.start],
            re.I,
        )
        if old is None or new_group:
            seen[key] = component
            continue
        if fold(old.name) == "credenza" and fold(component.name) == "credenza lateral":
            old.name = component.name
        old.evidence_ids.extend(e for e in component.evidence_ids if e not in old.evidence_ids)
        for c in candidates:
            if c.component_ref == component.component_id:
                c.component_ref = old.component_id
        for d in [*item.dimensions, *item.thicknesses, *item.accessories]:
            if d.component_ref == component.component_id:
                d.component_ref = old.component_id
        item.components.remove(component)

    for component, mention in components:
        if mention and re.match(r"\s+por\s+lado\b", text[mention.end :], re.I):
            counts = [
                c
                for c in candidates
                if c.label == "CANTIDAD_INTERNA"
                and c.component_ref == component.component_id
                and c.decision == "ACCEPTED"
            ]
            for c in counts:
                c.decision = "UNRESOLVED"
                c.reason = "Per-side count, not an established whole-furniture internal total"
                if c.candidate_id not in item.unresolved:
                    item.unresolved.append(c.candidate_id)
                end = mention.end + re.match(r"\s+por\s+lado\b", text[mention.end :], re.I).end()
                add(
                    c.start,
                    end,
                    "DISTRIBUCION",
                    {"count": c.normalized_value, "basis": "per_side", "total_derived": False},
                    "Confirm distribution by side without inventing total internal quantity",
                    component.component_id,
                )

    # Materials literally inside a noncomponent accessory do not describe its parent.
    accessory_spans = [
        c
        for c in candidates
        if c.label == "ACCESORIO"
        and c.decision == "ACCEPTED"
        and not any(m and m.start <= c.start < m.end for _, m in components)
    ]
    for c in candidates:
        if (
            c.label == "MATERIAL"
            and c.decision == "ACCEPTED"
            and any(a.start <= c.start and c.end <= a.end for a in accessory_spans)
        ):
            c.label = "MATERIAL_ACCESORIO"
            c.reason = "Material of a literal accessory, not its furniture parent"
            c.component_ref = None

    colors = [
        c
        for c in candidates
        if c.label == "COLOR" and c.decision == "ACCEPTED" and c.component_ref is None
    ]
    if (
        len(colors) == 2
        and re.fullmatch(r"\s+(?:con|y)\s+", text[colors[0].end : colors[1].start], re.I)
        and re.search(r"\bcolor\s+$", text[max(0, colors[0].start - 20) : colors[0].start], re.I)
    ):
        item.primary_color = Color(
            value=str(colors[0].normalized_value or colors[0].text).casefold(),
            evidence_ids=[colors[0].candidate_id],
        )
        item.secondary_color = Color(
            value=str(colors[1].normalized_value or colors[1].text).casefold(),
            evidence_ids=[colors[1].candidate_id],
        )

    for measurement in item.thicknesses:
        c = evidence(measurement)
        if (
            c
            and measurement.unit
            and not re.search(
                r"\b(?:mm|cm|m|mil[ií]metros?|cent[ií]metros?|metros?)\b", c.text, re.I
            )
        ):
            c.decision = "UNRESOLVED"
            c.reason = "Shared final thickness unit from explicit enumeration; confirm ownership"
            c.normalized_value = {
                "value": measurement.value,
                "unit": measurement.unit,
                "value_mm": measurement.value_mm,
                "unit_basis": "shared_enumeration",
            }
            if c.candidate_id not in item.unresolved:
                item.unresolved.append(c.candidate_id)

    # Explicit ranges/geometry remain evidence and observations, not fabricated axes.
    from homex_nlp.magnitudes import NUMBER, UNIT, scalar, unit_name

    pattern = re.compile(
        rf"\b(?P<axis>altura|alto|ancho|largo)\s+regulable\s+de\s+(?P<low>{NUMBER})\s+a\s+(?P<high>{NUMBER})\s*(?P<unit>{UNIT})",
        re.I,
    )
    for m in pattern.finditer(text):
        low, high = scalar(m["low"]), scalar(m["high"])
        if low is None or high is None:
            continue
        add(
            m.start(),
            m.end(),
            "RANGO_DIMENSIONAL",
            {
                "minimum": str(low),
                "maximum": str(high),
                "unit": unit_name(m["unit"]),
                "axis": m["axis"],
            },
            "Explicit adjustable range; confirm endpoints rather than a single value",
        )
        item.dimensions = [
            d
            for d in item.dimensions
            if not (evidence(d) and m.start() <= evidence(d).start < m.end())
        ]
        item.observations = "; ".join(filter(None, [item.observations, m.group()]))
    geometry = re.search(r"\ben\s+(?:L|ele)\b", item.name or "", re.I)
    if geometry and product:
        add(
            product.start,
            product.end,
            "GEOMETRIA",
            {"shape": "L", "axes_assigned": False},
            "L-shaped arms require orientation/axis review",
        )
        for d in item.dimensions:
            c = evidence(d)
            if (
                d.axis == "largo"
                and c
                and re.search(r"\bpor\b|[x×]", text[max(product.end, c.start - 70) : c.end], re.I)
            ):
                d.axis = None
                c.label = "DIMENSION"
                c.decision = "UNRESOLVED"
                c.reason = "L arm length, not a conventional main-product axis"
                if c.candidate_id not in item.unresolved:
                    item.unresolved.append(c.candidate_id)
    return item
