"""Keep ordered dimension evidence without guessing axes or implicit owners."""

import re

from homex_nlp.contracts.evidence import Candidate, Warning
from homex_nlp.contracts.item import Dimension
from homex_nlp.magnitudes import OPERAND, length
from homex_nlp.rules import is_explicitly_negated

CHAIN = re.compile(
    r"(?<![\w.,+−-])" + OPERAND + r"(?:\s*(?:[x×]|\bpor\b)\s*" + OPERAND + r")+(?!\w)", re.I
)


def operand(raw):
    return length(raw)


def explicit_owner(item, candidates, text, start):
    """A directly introduced product/component is positive ownership evidence."""
    from homex_nlp.product_relations import head

    for evidence in candidates:
        if evidence.end > start or evidence.label not in {"PRODUCTO", "COMPONENTE"}:
            continue
        if not re.fullmatch(r"\s+(?:rodante\s+)?de\s+", text[evidence.end : start], re.I):
            continue
        component = next(
            (c for c in item.components if evidence.candidate_id in c.evidence_ids), None
        )
        if component and evidence.decision == "ACCEPTED":
            return True, component.component_id
        if evidence.label == "PRODUCTO" and (
            evidence.decision == "ACCEPTED"
            or evidence.decision == "REJECTED"
            and evidence.reason == "Referential/component mention, not an independent product"
            and head(evidence.text) == head(item.name)
        ):
            return True, None
    return False, None


def positive_dimension_prefix(text):
    """Validate all operands before a comma can introduce a reference."""
    prefix = re.match(r"\s+(?:rodante\s+)?(?:de|tiene|mide)\s+", text, re.I)
    if not prefix:
        return False
    tail = text[prefix.end() :]
    chain = CHAIN.match(tail)
    if chain:
        values = [operand(m.group().strip())[0] for m in re.finditer(OPERAND, chain.group(), re.I)]
        return (
            len(values) in {2, 3}
            and all(v is not None and v > 0 for v in values)
            and not re.match(r"\s*(?:[x×]|\bpor\b)", tail[chain.end() :], re.I)
        )
    single = re.match(OPERAND, tail, re.I)
    if not single or re.match(r"\s*(?:[x×]|\bpor\b)", tail[single.end() :], re.I):
        return False
    value, unit = operand(single.group().strip())
    return value is not None and value > 0 and unit is not None


def complete_dimension_chains(item, candidates, text, warnings):
    # Only the pre-existing measurements can overlap these disjoint regex
    # matches. Index once, not dimensions × all growing candidates per chain.
    evidence = {c.candidate_id: c for c in candidates}
    occupied = [
        (evidence[e].start, evidence[e].end)
        for measurement in [*item.dimensions, *item.thicknesses]
        for e in measurement.evidence_ids
        if e in evidence
    ]
    owners = sorted(
        (c for c in candidates if c.label in {"PRODUCTO", "COMPONENTE"}),
        key=lambda c: c.end,
        reverse=True,
    )
    for chain in CHAIN.finditer(text):
        # Never salvage a suffix of a negative/partial multiplication chain.
        if re.search(r"[-−+x×]\s*$", text[: chain.start()], re.I):
            continue
        group = Candidate(
            candidate_id=f"c{len(candidates) + 1}",
            label="DIMENSION",
            start=chain.start(),
            end=chain.end(),
            text=chain.group(),
            source="RULE",
            decision="UNRESOLVED",
        )
        candidates.append(group)
        item.unresolved.append(group.candidate_id)
        warnings.append(
            Warning(
                code="MISSING_AXIS",
                path="/item_proposal/dimensions",
                severity="REVIEW",
                message=f"Indique ejes y unidades de {chain.group()}.",
            )
        )
        spans = list(re.finditer(OPERAND, chain.group(), re.I))
        parsed = [operand(m.group().strip()) for m in spans]
        known, owner = explicit_owner(item, owners, text, chain.start())
        overlapping = any(start < chain.end() and chain.start() < end for start, end in occupied)
        if (
            not known
            or overlapping
            or len(parsed) not in {2, 3}
            or any(v is None or v <= 0 for v, _ in parsed)
            or is_explicitly_negated(text, chain.start())
        ):
            continue
        # A sole trailing unit scopes the homogeneous list. Mixed-unit lists
        # retain only each operand's declared unit; no interior-unit guessing.
        shared = parsed[-1][1] if all(u is None for _, u in parsed[:-1]) else None
        group.component_ref = owner
        for span, (value, unit) in zip(spans, parsed):
            unit = unit or shared
            evidence = Candidate(
                candidate_id=f"c{len(candidates) + 1}",
                label="DIMENSION",
                start=chain.start() + span.start(),
                end=chain.start() + span.end(),
                text=span.group(),
                source="RULE",
                decision="ACCEPTED",
                normalized_value=[str(value), unit],
                component_ref=owner,
            )
            candidates.append(evidence)
            item.dimensions.append(
                Dimension(
                    value=str(value),
                    unit=unit,
                    value_mm=str(value * {"m": 1000, "cm": 10, "mm": 1}[unit]) if unit else None,
                    axis=None,
                    original_text=span.group(),
                    component_ref=owner,
                    evidence_ids=[evidence.candidate_id, group.candidate_id],
                )
            )
            if unit is None:
                warnings.append(
                    Warning(
                        code="MISSING_UNIT",
                        path="/item_proposal/dimensions",
                        severity="REVIEW",
                        message=f"La medida {span.group()!r} no tiene unidad.",
                    )
                )
