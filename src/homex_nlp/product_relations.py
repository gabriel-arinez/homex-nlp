"""Resolve only explicit referential/component mentions, never independent orders."""

from __future__ import annotations

import re
import unicodedata


def head(text):
    folded = "".join(
        c for c in unicodedata.normalize("NFD", text.casefold()) if unicodedata.category(c) != "Mn"
    )
    family = folded.split()[0].rstrip("s")
    return {"cajoneria": "cajonera", "credencia": "credenza"}.get(family, family)


def descriptive_reference(text, mention):
    """A bare new descriptive clause has no separate commercial determiner."""
    before = text[: mention.start]
    if re.search(
        r"\b(?:otra?|segund[oa]|un[ao]?|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|\d+)\s+$",
        before,
        re.I,
    ):
        return False
    boundary = re.search(
        r"(?:[.;,]\s*(?:el|la|los|las)?\s*|\b(?:del|de la|incluye)\s+)$", before, re.I
    )
    if not boundary:
        return False
    if re.search(r"\b(?:del|de la)\s+$", before, re.I):
        return True
    if re.search(r"\bincluye\s+$", before, re.I):
        return True
    return bool(
        re.match(
            r"\s+(?:(?:rodante|integrada)\s+)?(?:de|tiene|mide|lleva|con)\b",
            text[mention.end :],
            re.I,
        )
    )


def resolve_product_references(text, products, mentions):
    if len(products) < 2:
        return products, []
    principal = products[0]
    dependent = set()
    # An introduced drawer assembly may use the literal collective noun.
    for assembly in re.finditer(r"\bcajoner[ií]a\b", text, re.I):
        if assembly.start() > principal.start and re.search(
            r"\bcon\s+$", text[: assembly.start()], re.I
        ):
            dependent.add("cajonera")
    for mention in mentions:
        if mention.start <= principal.start or head(mention.text) not in {"cajonera", "casillero"}:
            continue
        if re.search(r"\bcon\s+(?:(?:un[ao]?|\d+)\s+)?$", text[: mention.start], re.I):
            dependent.add(head(mention.text))
    active = [principal]
    references = []
    for mention in products[1:]:
        family = head(mention.text)
        integrated = (
            head(principal.text) == "escritorio"
            and family == "credenza"
            and re.match(r"\s+integrada\b", text[mention.end :], re.I)
            and re.search(r"(?:[.;,]\s*|\bcon\s+)$", text[: mention.start], re.I)
        )
        if integrated or (
            (family == head(principal.text) or family in dependent)
            and (
                family in dependent or not re.search(r"\bincluye\s+$", text[: mention.start], re.I)
            )
            and descriptive_reference(text, mention)
        ):
            references.append(mention)
        else:
            active.append(mention)
    return active, references


def merge_drawer_references(item, candidates, text):
    """Merge only introduced drawer references AFTER independent span association."""
    first = None
    for component in list(item.components):
        if head(component.name) != "cajonera":
            continue
        evidence = next(
            (
                c
                for c in candidates
                if c.candidate_id in component.evidence_ids and c.label == "COMPONENTE"
            ),
            None,
        )
        if evidence is None:
            continue
        if first is None:
            if re.search(r"\bcon\s+(?:(?:un[ao]?|\d+)\s+)?$", text[: evidence.start], re.I):
                first = component
            continue
        if not descriptive_reference(text, evidence):
            continue
        first.evidence_ids.extend(e for e in component.evidence_ids if e not in first.evidence_ids)
        for candidate in candidates:
            if candidate.component_ref == component.component_id:
                candidate.component_ref = first.component_id
        for value in [*item.dimensions, *item.thicknesses, *item.accessories]:
            if value.component_ref == component.component_id:
                value.component_ref = first.component_id
        item.components.remove(component)


def associate_reference_dimensions(item, candidates, text):
    """Bind a contiguous dimension list to an explicit drawer/integrated sideboard.

    Only literal connectors and already extracted measures are consumed. A new
    entity, sentence, material clause or unparsed text terminates the list.
    """
    dimensions = sorted(
        (
            (next(c for c in candidates if c.candidate_id in d.evidence_ids), d)
            for d in item.dimensions
        ),
        key=lambda pair: pair[0].start,
    )
    for component in item.components:
        if head(component.name) != "cajonera" and not re.fullmatch(
            r"creden(?:z|ci)a\s+integrada", component.name, re.I
        ):
            continue
        for mention in candidates:
            if mention.label != "COMPONENTE" or mention.candidate_id not in component.evidence_ids:
                continue
            end = mention.end
            started = False
            for evidence, dimension in dimensions:
                if evidence.start < end:
                    continue
                connector = text[end : evidence.start]
                pattern = (
                    r"\s*(?:,|y|,\s*y)\s*"
                    if started
                    else r"\s+(?:rodante\s+)?(?:de|con)\s+"
                    r"(?:(?:MDF|MDP|melamina)\s+de\s+)?"
                )
                if not re.fullmatch(pattern, connector, re.I):
                    break
                if dimension.component_ref not in {None, component.component_id}:
                    break
                dimension.component_ref = component.component_id
                evidence.component_ref = component.component_id
                started = True
                end = evidence.end
