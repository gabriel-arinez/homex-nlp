"""Reglas puras de F03; operan sobre el texto original y conservan offsets."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

NUMBER_WORDS = {
    "un": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
}
PRODUCTS = (
    "escritorio",
    "mesa",
    "mueble",
    "librero",
    "estante",
    "credenza",
    "velador",
    "ropero",
    "closet",
    "cajonera",
)
ACCESSORIES = ("pasacable", "bisagras", "cajones", "puertas", "jaladores", "bandeja")


@dataclass(frozen=True)
class Match:
    start: int
    end: int
    text: str
    label: str
    value: object = None


def decimal_from_text(raw: str) -> Decimal | None:
    """Acepta formatos completos conocidos; rechaza ambigüedad en vez de truncar."""
    value = raw.strip().replace(" ", "")
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?", value):
        value = value.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?", value):
        value = value.replace(",", "")
    elif re.fullmatch(r"\d+(?:[,.]\d{1,2})?", value):
        value = value.replace(",", ".")
    else:
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    return parsed if parsed > 0 else None


def money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def find_products(text: str) -> list[Match]:
    # El núcleo se conserva corto: palabras libres absorbían «y una» o «a» y
    # ocultaban conflictos comerciales entre productos.
    pattern = re.compile(r"\b(?:" + "|".join(PRODUCTS) + r")s?(?:\s+en\s+l)?", re.I)
    return [
        Match(m.start(), m.end(), m.group().strip(), "PRODUCTO") for m in pattern.finditer(text)
    ]


def find_quantity(text: str) -> Match | None:
    pattern = re.compile(
        r"\b(" + "|".join(NUMBER_WORDS) + r"|\d+)\s+(?:unidades?\s+(?:de\s+)?)?", re.I
    )
    for match in pattern.finditer(text):
        token = match.group(1).lower()
        value = NUMBER_WORDS.get(token, int(token) if token.isdigit() else None)
        if value:
            return Match(match.start(1), match.end(1), match.group(1), "CANTIDAD", value)
    return None


def find_price(text: str) -> tuple[Match | None, str | None]:
    unit = re.search(
        r"\b(?:a|por)\s+([\d.,]+)\s*(?:bs|bob)?\s+(?:cada\s+uno|c/u|por\s+unidad)\b", text, re.I
    )
    total = re.search(
        r"\b(?:total|monto(?:\s+total)?)\s*(?:es|de)?\s*([\d.,]+)\s*(?:bs|bob)?\b", text, re.I
    )
    chosen = unit or total
    if chosen is None:
        return None, None
    parsed = decimal_from_text(chosen.group(1))
    if parsed is None:
        return None, "INVALID_PRICE"
    mode = "PRECIO_UNITARIO" if unit else "TOTAL_NEGOCIADO"
    return Match(chosen.start(1), chosen.end(1), chosen.group(1), "PRECIO", parsed), mode


def find_measurements(text: str, label: str) -> list[Match]:
    pattern = re.compile(
        r"(?:"
        + label
        + r"\s*(?:de\s+)?([\d.,]+)\s*(mm|cm|m|mts?|metros?)?|"
        + r"([\d.,]+)\s*(mm|cm|m|mts?|metros?)?\s*(?:de\s+)?"
        + label
        + r")",
        re.I,
    )
    found: list[Match] = []
    for match in pattern.finditer(text):
        raw_value, raw_unit = match.group(1) or match.group(3), match.group(2) or match.group(4)
        value = decimal_from_text(raw_value)
        if value is not None:
            unit = (raw_unit or "").lower().rstrip(".")
            found.append(
                Match(
                    match.start(), match.end(), match.group(), label.upper(), (value, unit or None)
                )
            )
    return found


def find_thicknesses(text: str) -> list[Match]:
    pattern = re.compile(r"\b(?:de|a)\s+([\d.,]+)\s*(mm|mil[ií]metros?)\b", re.I)
    return [
        Match(
            m.start(1),
            m.end(2),
            m.group(1, 2)[0] + " " + m.group(2),
            "ESPESOR",
            (decimal_from_text(m.group(1)), "mm"),
        )
        for m in pattern.finditer(text)
        if decimal_from_text(m.group(1))
    ]


def find_accessories(text: str) -> list[Match]:
    pattern = re.compile(r"\b(?:" + "|".join(ACCESSORIES) + r")(?:\s+[a-záéíóúñ]+){0,3}", re.I)
    return [
        Match(m.start(), m.end(), m.group().strip(), "ACCESORIO") for m in pattern.finditer(text)
    ]
