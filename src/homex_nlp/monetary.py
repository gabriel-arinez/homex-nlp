"""Bounded monetary grammar; never normalizes source text or dimensional values."""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal

UNITS = dict(
    zip(
        "un uno una dos tres cuatro cinco seis siete ocho nueve".split(),
        [1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    )
)
SHORT = dict(
    zip(
        "diez once doce trece catorce quince dieciseis diecisiete dieciocho diecinueve veinte veintiuno veintiun veintidos veintitres veinticuatro veinticinco veintiseis veintisiete veintiocho veintinueve".split(),
        [*range(10, 22), 21, *range(22, 30)],
    )
)
TENS = dict(
    zip("treinta cuarenta cincuenta sesenta setenta ochenta noventa".split(), range(30, 100, 10))
)
HUNDREDS = dict(
    zip(
        "cien ciento doscientos trescientos cuatrocientos quinientos seiscientos setecientos ochocientos novecientos".split(),
        [100, 100, 200, 300, 400, 500, 600, 700, 800, 900],
    )
)
SHORT["veintiuna"] = 21
HUNDREDS.update(
    {word[:-2] + "as": value for word, value in list(HUNDREDS.items()) if word.endswith("ientos")}
)

LEXICON = (
    set(UNITS)
    | set(SHORT)
    | set(TENS)
    | set(HUNDREDS)
    | {
        "mil",
        "millón",
        "millon",
        "millones",
        "billon",
        "billón",
        "billones",
        "y",
        "dieciséis",
        "veintiún",
        "veintidós",
        "veintitrés",
        "veintiséis",
    }
)
WORD = r"(?:" + "|".join(sorted(LEXICON, key=len, reverse=True)) + r")\b"
# Consume the whole adjacent numeric phrase, including invalid tails. Validation
# must see every token; a repetition limit or optional scale tail accepts prefixes.
ATOM = r"(?:(?:[-−]\s*)?\d[\w.,]*|mil\d\w*|(?:[-−]\s*)?" + WORD + r")"
AMOUNT = ATOM + r"(?:\s+" + ATOM + r")*"


def cardinal(tokens):
    if not tokens:
        return None
    if tokens.count("mil") > 1:
        return None
    if "mil" in tokens:
        i = tokens.index("mil")
        a = cardinal(tokens[:i]) if i else 1
        b = cardinal(tokens[i + 1 :]) if tokens[i + 1 :] else 0
        return (
            a * 1000 + b
            if a is not None and 0 < a < 1000 and b is not None and 0 <= b < 1000
            else None
        )
    if len(tokens) == 1:
        return UNITS.get(
            tokens[0],
            SHORT.get(
                tokens[0],
                TENS.get(tokens[0], HUNDREDS.get(tokens[0]) if tokens[0] != "ciento" else None),
            ),
        )
    if tokens[0] in HUNDREDS and tokens[0] != "cien":
        b = cardinal(tokens[1:])
        return HUNDREDS[tokens[0]] + b if b is not None and 0 < b < 100 else None
    if len(tokens) == 3 and tokens[0] in TENS and tokens[1] == "y" and tokens[2] in UNITS:
        return TENS[tokens[0]] + UNITS[tokens[2]]
    return None


def monetary_amount(raw, numeric_parser):
    """Only called after a monetary marker; Decimal and original spans retained."""
    text = "".join(
        c for c in unicodedata.normalize("NFD", raw.casefold()) if unicodedata.category(c) != "Mn"
    )
    mixed = re.fullmatch(r"(.+?)\s+mil(?:\s+(.+))?", text)
    if mixed:
        coefficient = (
            numeric_parser(mixed[1])
            if re.fullmatch(r"\d+", mixed[1])
            else cardinal(mixed[1].split())
        )
        tail = mixed[2]
        rest = (
            int(tail)
            if tail and re.fullmatch(r"\d{1,3}", tail)
            else cardinal(tail.split())
            if tail
            else 0
        )
        if (
            coefficient is None
            or not 0 < coefficient < 1000
            or rest is None
            or not 0 <= rest < 1000
        ):
            return None
        return Decimal(coefficient) * Decimal(1000) + Decimal(rest)
    if re.search(r"\d", text):
        return numeric_parser(text) if re.fullmatch(r"\d[\d.,]*", text) else None
    n = cardinal(text.split())
    return Decimal(n) if n is not None and 0 < n <= 999999 else None
