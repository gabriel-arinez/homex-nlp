"""Resolve only explicit referential/component mentions, never independent orders."""

from __future__ import annotations

import re
import unicodedata


def head(text):
    folded = "".join(
        c for c in unicodedata.normalize("NFD", text.casefold()) if unicodedata.category(c) != "Mn"
    )
    return folded.split()[0].rstrip("s")


def descriptive_reference(text, mention):
    """A bare new descriptive clause has no separate commercial determiner."""
    before = text[: mention.start]
    if re.search(
        r"\b(?:otra?|segund[oa]|un[ao]?|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|\d+)\s+$",
        before,
        re.I,
    ):
        return False
    boundary = re.search(r"(?:[.;,]\s*(?:el|la|los|las)?\s*|\b(?:del|de la)\s+)$", before, re.I)
    if not boundary:
        return False
    if re.search(r"\b(?:del|de la)\s+$", before, re.I):
        return True
    return bool(re.match(r"\s+(?:de|tiene|mide|lleva|con)\b", text[mention.end :], re.I))


def resolve_product_references(text, products, mentions):
    if len(products) < 2:
        return products, []
    principal = products[0]
    dependent = set()
    for mention in mentions:
        if mention.start <= principal.start or head(mention.text) not in {"cajonera", "casillero"}:
            continue
        if re.search(r"\bcon\s+(?:(?:un[ao]?|\d+)\s+)?$", text[: mention.start], re.I):
            dependent.add(head(mention.text))
    active = [principal]
    references = []
    for mention in products[1:]:
        family = head(mention.text)
        if (family == head(principal.text) or family in dependent) and descriptive_reference(
            text, mention
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
