"""Propose contextual units without turning inference into explicit evidence."""

import json
import re
from decimal import Decimal
from importlib.resources import files

from homex_nlp.contracts.evidence import Warning

PROFILES = json.loads(
    files("homex_nlp.resources").joinpath("dimensional_profiles.json").read_text()
)
FACTORS = {"m": 1000, "cm": 10, "mm": 1}


def infer_units(item, candidates, text, warnings):
    evidence = {c.candidate_id: c for c in candidates}
    explicit = [d for d in item.dimensions if d.unit]
    for dimension in [*item.dimensions, *item.thicknesses]:
        if dimension.unit or dimension in item.thicknesses:
            continue
        own = [evidence[e] for e in dimension.evidence_ids if e in evidence]
        if not own:
            continue
        unit, support, reason = None, [], None
        start, end = min(c.start for c in own), max(c.end for c in own)
        # A local unit can scope an uninterrupted enumeration, not a new owner.
        neighbors = []
        for other in explicit:
            if other.component_ref != dimension.component_ref:
                continue
            refs = [evidence[e] for e in other.evidence_ids if e in evidence]
            if not refs:
                continue
            left = min(start, min(c.start for c in refs))
            right = max(end, max(c.end for c in refs))
            between = text[left:right]
            if right - left <= 160 and not re.search(
                r"[.;]|\b(?:con|precio|tablero|patas?|cajones?)\b", between, re.I
            ):
                neighbors.append(other)
        if neighbors and len({d.unit for d in neighbors}) == 1:
            unit = neighbors[0].unit
            support = [e for d in neighbors for e in d.evidence_ids]
            reason = "Inferred unit from local same-owner dimensional enumeration"
        elif dimension in item.dimensions:
            owner = next(
                (c.name for c in item.components if c.component_id == dimension.component_ref), None
            )
            profile_context = (
                owner
                if dimension.component_ref
                else (item.furniture_type_candidate or item.name or "")
            )
            profile = next(
                (
                    p
                    for p in reversed(list(PROFILES.values()))
                    if profile_context and re.search(p["context"], profile_context, re.I)
                ),
                None,
            )
            if profile:
                plausible = [
                    u
                    for u in profile["units"]
                    if profile["minimum_mm"]
                    <= Decimal(dimension.value) * FACTORS[u]
                    <= profile["maximum_mm"]
                ]
                if len(plausible) == 1:
                    unit = plausible[0]
                    reason = "Inferred unit from contextual dimensional profile; confirm custom furniture dimensions"
        if not unit:
            continue
        dimension.unit = unit
        dimension.value_mm = str(Decimal(dimension.value) * FACTORS[unit])
        dimension.evidence_ids.extend(e for e in support if e not in dimension.evidence_ids)
        for candidate in own:
            candidate.decision = "UNRESOLVED"
            candidate.reason = reason
            candidate.normalized_value = {
                "value": dimension.value,
                "unit": unit,
                "value_mm": dimension.value_mm,
                "unit_inferred": True,
            }
            if candidate.candidate_id not in item.unresolved:
                item.unresolved.append(candidate.candidate_id)
        warnings.append(
            Warning(
                code="MISSING_UNIT",
                path="/item_proposal/dimensions",
                severity="REVIEW",
                message=f"Inferred unit {unit} for {dimension.original_text}; confirm this proposal.",
            )
        )
