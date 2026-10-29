"""Conservative offline normalization; no currency conversion or missing units."""

import re
import unicodedata
from decimal import Decimal

WORDS = dict(
    zip(
        "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis diecisiete dieciocho diecinueve veinte".split(),
        range(21),
        strict=True,
    )
)
WORDS.update(
    dict(
        zip(
            "treinta cuarenta cincuenta sesenta setenta ochenta noventa".split(),
            range(30, 100, 10),
            strict=True,
        )
    )
)
WORDS.update(
    dict(
        zip(
            "cien ciento doscientos trescientos cuatrocientos quinientos seiscientos setecientos ochocientos novecientos".split(),
            [100, 100, 200, 300, 400, 500, 600, 700, 800, 900],
            strict=True,
        )
    )
)
WORDS.update({"un": 1, "una": 1})


def folded(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    ).strip()


def number(text):
    text = folded(text)
    if re.fullmatch(r"\d+(?:[.,]\d+)*", text):
        if "," in text:
            if not re.fullmatch(r"(?:\d+|\d{1,3}(?:\.\d{3})+),\d+", text):
                raise ValueError("AMBIGUOUS_NUMBER")
            text = text.replace(".", "").replace(",", ".")
        elif text.count(".") > 1:
            raise ValueError("AMBIGUOUS_NUMBER")
        return Decimal(text)
    if text.startswith("veinti") and text[6:] in WORDS:
        return Decimal(20 + WORDS[text[6:]])
    if not text:
        raise ValueError("EMPTY_NUMBER")
    tokens = text.split()
    if tokens[0] == "y" or tokens[-1] == "y":
        raise ValueError("INVALID_NUMBER_GRAMMAR")
    total, group, previous, seen_mil = 0, 0, 1000, False
    for token in tokens:
        if token == "y":
            continue
        if token == "mil":
            if seen_mil or previous == 0:
                raise ValueError("INVALID_NUMBER_GRAMMAR")
            total += (group or 1) * 1000
            group, previous, seen_mil = 0, 1000, True
            continue
        value = WORDS.get(token)
        if value is None and token.startswith("veinti") and token[6:] in WORDS:
            value = 20 + WORDS[token[6:]]
        if value is None:
            raise ValueError("UNKNOWN_NUMBER")
        if (
            previous < 10
            or (previous < 100 and not (previous >= 30 and previous % 10 == 0 and 0 < value < 10))
            or (100 <= previous < 1000 and value >= 100)
        ):
            raise ValueError("INVALID_NUMBER_GRAMMAR")
        group += value
        previous = value
    return Decimal(total + group)


def measurement(text):
    match = re.fullmatch(
        r"\s*(.*?)\s*(mil[ií]metros?|cent[ií]metros?|metros?|mts?\.?|mm|cm|m)\s*", text, re.I
    )
    if not match:
        raise ValueError("MISSING_EXPLICIT_UNIT")
    raw, unit = folded(match[1]), folded(match[2])
    unit = (
        "mm"
        if unit.startswith("mili") or unit == "mm"
        else "cm"
        if unit.startswith("centi") or unit == "cm"
        else "m"
    )
    # Spoken decimal metres require two numeric groups and an explicit metre unit.
    # No corresponding convention is applied when the unit is absent.
    pieces = raw.split()
    if (
        unit == "m"
        and len(pieces) == 2
        and all(p in WORDS for p in pieces)
        and WORDS[pieces[0]] < 10
        and WORDS[pieces[1]] >= 10
    ):
        value = Decimal(WORDS[pieces[0]]) + Decimal(WORDS[pieces[1]]) / 100
    else:
        value = number(raw)
    if value <= 0:
        raise ValueError("NON_POSITIVE_MEASUREMENT")
    return {"valor": format(value, "f"), "unidad": unit}
