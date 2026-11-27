"""Propose contextual units without turning inference into explicit evidence."""

import json
import re
from decimal import Decimal
from importlib.resources import files

from homex_nlp.contracts.evidence import Warning
from homex_nlp.thickness_context import contextual_gauge

PROFILES = json.loads(
    files("homex_nlp.resources").joinpath("dimensional_profiles.json").read_text()
)
FACTORS = {"m": 1000, "cm": 10, "mm": 1}


def _same_magnitude_context(dimension, neighbors, evidence, start):
    """Use relative local scale only for a named-axis, same-owner ellipse.

    Mixed explicit units do not always conflict: a metre-valued height can
    follow a centimetre-valued width/depth enumeration. Comparable raw values
    supply a conservative contextual cue, not a furniture-size restriction.
    The caller keeps this proposal unresolved and requires human review.
    """
    if not dimension.axis or any(not d.axis or d.axis == dimension.axis for d in neighbors):
        return []
    comparable = [
        d
        for d in neighbors
        if max(Decimal(d.value), Decimal(dimension.value))
        < 10 * min(Decimal(d.value), Decimal(dimension.value))
    ]
    if len({d.unit for d in comparable}) != 1:
        return []
    # A following differently scaled axis cannot introduce a unit backwards;
    # at least one comparable explicit donor must precede this omission.
    if not any(
        max(evidence[e].end for e in d.evidence_ids if e in evidence) <= start for d in comparable
    ):
        return []
    return comparable


def infer_units(item, candidates, text, warnings):
    evidence = {c.candidate_id: c for c in candidates}
    explicit = [d for d in item.dimensions if d.unit]

    def profile_for(dimension):
        owner = next(
            (c.name for c in item.components if c.component_id == dimension.component_ref), None
        )
        context = (
            owner if dimension.component_ref else (item.furniture_type_candidate or item.name or "")
        )
        return next(
            (
                p
                for p in reversed(list(PROFILES.values()))
                if context and re.search(p["context"], context, re.I)
            ),
            None,
        )

    def plausible_units(dimension):
        if dimension in item.thicknesses:
            own = [evidence[e] for e in dimension.evidence_ids if e in evidence]
            strong = any(contextual_gauge(text, c.start, c.end) for c in own)
            return ["mm"] if strong and Decimal("0.5") <= Decimal(dimension.value) <= 60 else []
        profile = profile_for(dimension)
        if not profile:
            return []
        maximum = profile.get("axis_maximum_mm", {}).get(
            getattr(dimension, "axis", None), profile["maximum_mm"]
        )
        return [
            u
            for u in profile["units"]
            if profile["minimum_mm"] <= Decimal(dimension.value) * FACTORS[u] <= maximum
        ]

    for dimension in explicit:
        profile = profile_for(dimension)
        if profile and dimension.unit not in plausible_units(dimension):
            warnings.append(
                Warning(
                    code="CONFLICTING_VALUES",
                    path="/item_proposal/dimensions",
                    severity="REVIEW",
                    message=f"Explicit atypical dimension retained: {dimension.original_text}; confirm custom size.",
                )
            )
    for dimension in [*item.dimensions, *item.thicknesses]:
        if dimension.unit:
            continue
        # Group references support a scalar but are never that scalar's value.
        own = [
            evidence[e]
            for e in dimension.evidence_ids
            if e in evidence
            and not (
                isinstance(evidence[e].normalized_value, dict)
                and "operands" in evidence[e].normalized_value
            )
        ]
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
                r"[.;]|\b(?:con|precio|tablero|patas?|(?:caj[oó]n(?:es)?|gavetas?))\b",
                between,
                re.I,
            ):
                neighbors.append(other)
        if neighbors and len({d.unit for d in neighbors}) == 1:
            unit = neighbors[0].unit
            support = [e for d in neighbors for e in d.evidence_ids]
            reason = "Inferred unit from local same-owner dimensional enumeration"
        elif neighbors:
            contextual = _same_magnitude_context(dimension, neighbors, evidence, start)
            if not contextual:
                # Same-scale disagreement remains ambiguous; never use a
                # profile to override conflicting local explicit evidence.
                continue
            unit = contextual[0].unit
            support = [e for d in contextual for e in d.evidence_ids]
            reason = "Inferred unit from local same-owner same-magnitude dimensional context"
        elif dimension in item.dimensions:
            plausible = plausible_units(dimension)
            if len(plausible) == 1:
                unit = plausible[0]
                reason = "Inferred unit from contextual dimensional profile; confirm custom furniture dimensions"
        plausible = plausible_units(dimension)
        if unit not in plausible:
            unit = plausible[0] if len(plausible) == 1 else None
            reason = (
                "Inferred unit from contextual scale; explicit local unit would be disproportionate"
            )
        if dimension in item.thicknesses and len(plausible) == 1:
            unit = plausible[0]
            reason = "Inferred millimetre gauge from thickness construction; confirm piece role and owner"
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
                path="/item_proposal/thicknesses"
                if dimension in item.thicknesses
                else "/item_proposal/dimensions",
                severity="REVIEW",
                message=f"Inferred unit {unit} for {dimension.original_text}; confirm this proposal.",
            )
        )
