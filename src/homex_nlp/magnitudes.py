"""Reusable source-preserving scalar and compound-length grammar."""

import re
import unicodedata
from decimal import Decimal

from homex_nlp.monetary import ATOM, monetary_amount

# Monetary atoms deliberately consume malformed word tails. Measurement units
# are different tokens: "milímetros" must never be swallowed as a "mil..." atom.
# Conjunctions belong inside tens, never to a following count or axis.
TENS_UNIT = r"(?:treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa)\s+y\s+(?:un[oa]?|dos|tres|cuatro|cinco|seis|siete|ocho|nueve)\b"
SCALAR_ATOM = rf"(?:{TENS_UNIT}|\d+(?:[.,]\d+)?|(?!(?:y|mil[ií]metros?|cent[ií]metros?|metros?|mm|cm|m)\b){ATOM})"
NUMBER = rf"{SCALAR_ATOM}(?:\s+{SCALAR_ATOM})*"
UNIT = r"(?:mil[ií]metros?|cent[ií]metros?|metros?|mm|cm|mts?|m)\b"
FRACTION = r"(?:medio|media|cuarto)"
COMPOUND = (
    rf"(?:{FRACTION}\s+metros?|{NUMBER}\s+metros?\s+"
    rf"(?:(?:y\s+)?{FRACTION}|(?:(?:y|con)\s+)?{NUMBER}(?:\s*(?:{UNIT}|pulgadas?\b))?))"
)
OPERAND = rf"(?:{COMPOUND}|{NUMBER}\s*(?:{UNIT})?)"


def scalar(raw):
    def numeric(value):
        return Decimal(value.replace(",", ".")) if re.fullmatch(r"\d+(?:[.,]\d+)?", value) else None

    return monetary_amount(raw, numeric)


def unit_name(raw):
    raw = "".join(
        c for c in unicodedata.normalize("NFD", raw.casefold()) if unicodedata.category(c) != "Mn"
    )
    return (
        "mm"
        if raw == "mm" or raw.startswith("mili")
        else "cm"
        if raw == "cm" or raw.startswith("cent")
        else "m"
    )


def length(raw):
    # A final sentence stop is not part of a unitless integer.
    if re.fullmatch(r"\d+\.", raw):
        raw = raw[:-1]
    fraction = re.fullmatch(rf"({FRACTION})\s+metros?", raw, re.I)
    if fraction:
        return Decimal("25" if fraction[1].lower() == "cuarto" else "50"), "cm"
    compound = re.fullmatch(
        rf"({NUMBER})\s+(metros?)\s+(?:(y|con)\s+)?({FRACTION}|{NUMBER})(?:\s*({UNIT}))?", raw, re.I
    )
    if compound:
        metres = scalar(compound[1])
        tail = compound[4].lower()
        if (
            metres is None
            or not 0 < metres <= 9
            or metres != metres.to_integral_value()
            or (metres == 1) != (compound[2].lower() == "metro")
            or re.fullmatch(r"0\d+", tail)
        ):
            return None, None
        if tail in {"medio", "media", "cuarto"}:
            return metres * 100 + Decimal("25" if tail == "cuarto" else "50"), "cm"
        rest = scalar(tail)
        if rest is None or not 0 < rest < 100:
            return None, None
        if compound[5]:
            if unit_name(compound[5]) != "cm":
                return None, None
        elif compound[3] or rest < 10:
            return None, None
        return metres * 100 + rest, "cm"
    simple = re.fullmatch(rf"({NUMBER})\s*({UNIT})?", raw, re.I)
    return (
        (scalar(simple[1]), unit_name(simple[2]) if simple[2] else None) if simple else (None, None)
    )
