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
    "vitrina",
    "sillón",
    "sillones",
)
ACCESSORIES = (
    "pasacable",
    "bisagras",
    "cajones",
    "puertas",
    "jaladores",
    "bandeja",
    "rieles",
    r"tapa\s*cantos?",
    r"toma(?:s)?\s*corrientes?",
)


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
    pattern = re.compile(
        r"\b(?:"
        + "|".join(p + (r"(?:es)?" if p.endswith("r") else r"s?") for p in PRODUCTS)
        + r")\b(?:\s+en\s+l)?",
        re.I,
    )
    reunion = re.compile(
        r"\bmesas?\s+de\s+reuni[oó]n\b"
        r"(?:\s+para\s+(?:\d+|" + "|".join(NUMBER_WORDS) + r")\s+personas?)?",
        re.I,
    )
    especificos = [Match(m.start(), m.end(), m.group(), "PRODUCTO") for m in reunion.finditer(text)]
    generales = [
        Match(m.start(), m.end(), m.group().strip(), "PRODUCTO")
        for m in pattern.finditer(text)
        if not any(x.start <= m.start() < x.end for x in especificos)
    ]
    return sorted([*especificos, *generales], key=lambda x: x.start)


def find_quantity(text: str) -> Match | None:
    products = find_products(text)
    if not products:
        return None
    main = products[0]
    prefix = text[: main.start]
    pattern = re.compile(
        r"\b(" + "|".join(NUMBER_WORDS) + r"|\d+)\s+(?:(?:juegos?|unidades?)\s+(?:de\s+)?)?$", re.I
    )
    match = pattern.search(prefix)
    if match:
        token = match.group(1).lower()
        value = NUMBER_WORDS.get(token, int(token) if token.isdigit() else None)
        if value:
            return Match(match.start(1), match.end(1), match.group(1), "CANTIDAD", value)
    explicit = re.search(
        r"\b(?:cantidad(?:\s+comercial)?\s*:\s*|se\s+cotizan\s+)(\d+)\s*(?:piezas?|pzas?\.?|unidades?|juegos?)\b",
        text,
        re.I,
    )
    if explicit and int(explicit.group(1)) > 0:
        return Match(
            explicit.start(1),
            explicit.end(1),
            explicit.group(1),
            "CANTIDAD",
            int(explicit.group(1)),
        )
    return None


def find_price(text: str) -> tuple[Match | None, str | None]:
    unit = re.search(
        r"\b(?:a\s+|por\s+)?([\d.,]+)\s*(?:bs|bob|bolivianos?|dólares?|usd)?\s+(?:cada\s+uno|c/u|por\s+unidad)\b",
        text,
        re.I,
    )
    total = re.search(
        r"\b(?:total|monto(?:\s+total)?)\s*(?:es|de)?\s*([\d.,]+)\s*(?:bs|bob)?\b", text, re.I
    )
    declared_unit = re.search(
        r"\b(?:precio\s+(?:por\s+unidad|unitario)|valor\s+unitario)\s*(?:Bs\.?|BOB|USD)?\s*([\d.,]+)",
        text,
        re.I,
    )
    unit = unit or declared_unit
    chosen = unit or total
    if chosen is None:
        return None, None
    parsed = decimal_from_text(chosen.group(1))
    if parsed is None:
        return None, "INVALID_PRICE"
    mode = "PRECIO_UNITARIO" if unit else "TOTAL_NEGOCIADO"
    return Match(chosen.start(1), chosen.end(1), chosen.group(1), "PRECIO", parsed), mode


def find_measurements(text: str, label: str) -> list[Match]:
    axes = {
        "ancho": "ancho|anchura",
        "alto": "alto|altura",
        "profundidad": "profundidad|profundo|fondo",
        "largo": "largo|longitud",
        "diametro": "di[aá]metro",
    }
    axis = "(?:" + axes.get(label, label) + ")"
    unit = r"(?:mil[ií]metros?|cent[ií]metros?|metros?|mm|cm|mts?|m)\b"
    pattern = re.compile(
        axis
        + r"\s*(?:de\s+)?(\d+(?:[.,]\d+)*)\s*("
        + unit
        + r")?|"
        + r"(\d+(?:[.,]\d+)*)\s*("
        + unit
        + r")?\s*(?:de\s+)?"
        + axis
        + r"(?:\s+("
        + unit
        + r"))?",
        re.I,
    )
    found = []
    for match in pattern.finditer(text):
        value = decimal_from_text(match.group(1) or match.group(3))
        raw_unit = match.group(2) or match.group(4) or match.group(5)
        if value is not None:
            normalized = None
            if raw_unit:
                token = raw_unit.casefold()
                normalized = (
                    "mm"
                    if token.startswith("mili") or token == "mm"
                    else "cm"
                    if token.startswith("cent") or token == "cm"
                    else "m"
                )
            found.append(
                Match(match.start(), match.end(), match.group(), label.upper(), (value, normalized))
            )
    return found


def find_thicknesses(text: str) -> list[Match]:
    pattern = re.compile(r"\b(?:de\s+|a\s+|espesor\s+)?([\d.,]+)\s*(mm|mil[ií]metros?)\b", re.I)
    return [
        Match(
            m.start(1),
            m.end(2),
            text[m.start(1) : m.end(2)],
            "ESPESOR",
            (decimal_from_text(m.group(1)), "mm"),
        )
        for m in pattern.finditer(text)
        if decimal_from_text(m.group(1))
    ]


def find_accessories(text: str) -> list[Match]:
    pattern = re.compile(
        r"\b(?:" + "|".join(ACCESSORIES) + r")\b(?:\s+(?!y\b)[a-záéíóúñ]+){0,3}",
        re.I,
    )
    encontrados = []
    for match in pattern.finditer(text):
        prefijo = text[max(0, match.start() - 25) : match.start()]
        cantidad = re.search(
            r"\b(" + "|".join(NUMBER_WORDS) + r"|\d+)\s*$",
            prefijo,
            re.I,
        )
        valor = None
        if cantidad:
            token = cantidad.group(1).lower()
            valor = NUMBER_WORDS.get(token)
            if valor is None and token.isdigit():
                valor = int(token)
        texto_accesorio = re.sub(
            r"(?:\s+(?:de|del|en|con|para|por|a|al))+$",
            "",
            match.group().strip(),
            flags=re.I,
        )
        encontrados.append(
            Match(
                match.start(),
                match.start() + len(texto_accesorio),
                texto_accesorio,
                "ACCESORIO",
                valor,
            )
        )
    return encontrados
