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


def is_explicitly_negated(text: str, start: int) -> bool:
    """Detecta exclusiones locales inequívocas sin normalizar el texto ni perder offsets.

    Un «no, mejor» introduce una corrección, no niega el producto que sigue.
    La cláusula termina en puntuación fuerte o coma; nunca se propaga
    una negación a toda la especificación.
    """
    clause = re.split(r"[.;,\n]", text[max(0, start - 140) : start])[-1]
    matches = list(
        re.finditer(
            r"\b(?:sin|ni|no(?:\s+(?:quiero|necesito|lleva|tiene|incluye|es|son))?)\b",
            clause,
            re.I,
        )
    )
    if not matches:
        return False
    negator = matches[-1].group().casefold()
    following = clause[matches[-1].end() :]
    # Una negación demasiado alejada no autoriza a descartar un producto.
    # «sin cajones y con puertas»: puertas sí están presentes.
    if re.search(r"\b(?:pero|con|mejor|s[ií]|quiero|necesito)\b", following, re.I):
        return False
    words = re.findall(r"\w+", following, re.UNICODE)
    if negator not in {"sin", "ni"} and "y" in words:
        # «No quiero dos mesas y un escritorio»: el segundo también puede
        # estar en el ámbito negado; no convertirlo en un pedido afirmativo.
        return len(words) <= 5
    limit = 3 if negator in {"sin", "ni"} else 2
    return len(words) <= limit


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


def find_quantity(text: str, main_product: Match | None = None) -> Match | None:
    products = [main_product] if main_product is not None else find_products(text)
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
    # La cantidad comercial se reconoce sólo en construcciones inequívocas.
    # «para 10 personas» y «2 tomacorrientes» no son cantidad de muebles.
    explicit = re.search(
        r"\b(?:cantidad(?:\s+comercial)?\s*(?::|de)?\s*|se\s+cotizan\s+)"
        r"(\d+|" + "|".join(NUMBER_WORDS) + r")\s*"
        r"(?:piezas?|pzas?\.?|unidades?|juegos?)\b",
        text,
        re.I,
    )
    if explicit:
        token = explicit.group(1).lower()
        value = NUMBER_WORDS.get(token, int(token) if token.isdigit() else None)
        if value and value > 0:
            return Match(explicit.start(1), explicit.end(1), explicit.group(1), "CANTIDAD", value)
    return None


def find_price(text: str) -> tuple[Match | None, str | None]:
    """Precios comerciales explícitos; nunca convertir un total en unitario aquí."""
    moneda = r"(?:bs\.?|bob|bolivianos?|d[oó]lares?|usd)"
    unit = re.search(
        r"\b(?:a\s+|por\s+)?([\d.,]+)\s*(?:" + moneda + r"\s*)?"
        r"(?:cada\s+un[ao]|c/u|por\s+unidad)\b",
        text,
        re.I,
    )
    declared_unit = re.search(
        r"\b(?:precio\s+(?:por\s+unidad|unitario)|valor\s+unitario)"
        r"\s*(?:(?:es|de)\s+)?(?:" + moneda + r"\s*)?([\d.,]+)\b",
        text,
        re.I,
    )
    cantidad = r"(?:\d+|" + "|".join(NUMBER_WORDS) + r")"
    tipo = r"(?:mesas?|escritorios?|veladores?|muebles?|roperos?|libreros?|credenzas?|estantes?)"
    total = re.search(
        r"\b(?:precio\s+total|total|monto(?:\s+total)?)"
        r"(?:\s+de\s+(?:las?|los?)\s+" + cantidad + r"\s+" + tipo + r")?"
        r"\s*(?:(?:es|de)\s+)*(?:" + moneda + r"\s*)?([\d.,]+)\b",
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


def find_ambiguous_price(text: str) -> Match | None:
    """Conserva evidencia de «precio 7300» sin inventar su modalidad."""
    if find_price(text)[1] is not None:
        return None
    match = re.search(r"\bprecio\s+(?:(?:es|de)\s+)?([\d.,]+)\b", text, re.I)
    if not match:
        return None
    valor = decimal_from_text(match.group(1))
    if valor is None:
        return None
    return Match(match.start(1), match.end(1), match.group(1), "PRECIO_AMBIGUO", valor)


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
