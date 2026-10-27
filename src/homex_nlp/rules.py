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
    "gavetero",
    "gabetero",
    "atril",
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
    # Variante ASR contextual: «escritor ejecutivo», no «escritor» aislado.
    ejecutivo_asr = re.compile(r"\bescritor(?:es)?\s+ejecutivos?\b", re.I)
    especificos = [
        Match(m.start(), m.end(), m.group(), "PRODUCTO")
        for patron in (reunion, ejecutivo_asr)
        for m in patron.finditer(text)
    ]
    generales = [
        Match(m.start(), m.end(), m.group().strip(), "PRODUCTO")
        for m in pattern.finditer(text)
        if not any(x.start <= m.start() < x.end for x in especificos)
    ]
    return sorted([*especificos, *generales], key=lambda x: x.start)


def _cantidad_comercial_pospuesta(text: str, principal: Match) -> Match | None:
    """Cantidad contigua al producto, sin consumir especificaciones de piezas.

    «mesa de reunión para diez personas, una pieza tamaño ...» describe una
    unidad comercial; «mesa, una pieza de vidrio» no es concluyente.
    Ante una rectificación de la misma cantidad sin puntuación, abstenerse.
    """
    tramo = text[principal.end : principal.end + 180]
    inicio = re.match(
        r"\s*[,;:]?\s*(?P<numero>\d+|" + "|".join(NUMBER_WORDS) + r")"
        r"\s+(?P<unidad>piezas?|pzas?\.?|unidades?|juegos?)\b",
        tramo,
        re.I,
    )
    if inicio is None:
        return None
    token = inicio.group("numero").casefold()
    valor = NUMBER_WORDS.get(token, int(token) if token.isdigit() else None)
    if valor is None or valor <= 0:
        return None
    despues = tramo[inicio.end() :]
    # «una pieza de vidrio», «dos piezas para el tablero»: componentes, no
    # líneas comerciales. No consumirlas para inferir importes.
    if re.match(r"\s+(?:de|del|para)\b", despues, re.I):
        return None
    # Una rectificación posterior de la misma magnitud exige arbitraje;
    # nunca conservar por defecto la primera cifra como comercial.
    if re.match(
        r"\s*[,;.]?\s*(?:no\s*,?\s*(?:mejor|\d+|"
        + "|".join(NUMBER_WORDS)
        + r")|perd[oó]n|corrijo|mejor)\b",
        despues,
        re.I,
    ):
        return None
    offset = principal.end + inicio.start("numero")
    return Match(offset, offset + len(token), text[offset : offset + len(token)], "CANTIDAD", valor)


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
    # «se cotiza una sola mesa» declara una unidad, no un segundo producto.
    # Aceptar únicamente el mismo tipo principal, sin extrapolar cantidades.
    if main.text.casefold().startswith("mesa"):
        una_sola = re.search(
            r"\b(?:se\s+cotiza|secotiza)\s+(una)\s+sola\s+mesa\b",
            text[main.end :],
            re.I,
        )
        if una_sola:
            start = main.end + una_sola.start(1)
            return Match(start, start + 3, text[start : start + 3], "CANTIDAD", 1)
    return _cantidad_comercial_pospuesta(text, main)


def _numero_es_medida_no_precio(text: str, encontrado: re.Match[str]) -> bool:
    """Nunca convertir medidas dimensionales explícitas en precios comerciales.

    Mantener los offsets del texto original; no depende de normalización ASR.
    No bloquea importes sin moneda cuando el contexto comercial es claro.
    """
    unidad_dimension = (
        r"(?:mm|cm|m|mts?|mil[ií]metros?|cent[ií]metros?|metros?|"
        r"pulgadas?|pies)\b"
    )
    if re.match(r"\s*" + unidad_dimension, text[encontrado.end(1) :], re.I):
        return True
    anterior = text[max(0, encontrado.start() - 42) : encontrado.start()]
    return bool(
        re.search(
            r"\b(?:ancho|anchura|alto|altura|largo|longitud|fondo|"
            r"profundidad|di[aá]metro|espesor)\s*$",
            anterior,
            re.I,
        )
        and encontrado.group().casefold().lstrip().startswith("total")
    )


def find_price(text: str) -> tuple[Match | None, str | None]:
    """Precios comerciales explícitos; nunca convertir un total en unitario aquí.

    Una medida como «ancho total 180 centímetros» NO es «Bs 180».
    Si aparece un precio real después de una medida, seguir buscándolo.
    """
    moneda = r"(?:bs\.?|bob|bolivianos?|d[oó]lares?|usd)"

    def primero_aplicable(patron: str):
        return next(
            (
                encontrado
                for encontrado in re.finditer(patron, text, re.I)
                if not _numero_es_medida_no_precio(text, encontrado)
            ),
            None,
        )

    unit = primero_aplicable(
        r"\b(?:a\s+|por\s+)?([\d.,]+)\s*(?:" + moneda + r"\s*)?"
        r"(?:cada\s+un[ao]|c/u|por\s+unidad)\b"
    )
    declared_unit = primero_aplicable(
        r"\b(?:precio\s+(?:por\s+unidad|unitario)|valor\s+unitario|"
        r"presionitario|presunitario|prese\s+unitario)"
        r"\s*[,;:]?\s*(?:(?:es|de)\s+)?(?:" + moneda + r"\s*)?([\d.,]+)\b"
    )
    cantidad = r"(?:\d+|" + "|".join(NUMBER_WORDS) + r")"
    tipo = r"(?:mesas?|escritorios?|veladores?|muebles?|roperos?|libreros?|credenzas?|estantes?)"
    total = primero_aplicable(
        r"\b(?:precio\s+total(?:\s+negociado)?|total(?:\s+negociado)?|monto(?:\s+total)?)"
        r"(?:\s+de\s+(?:las?|los?)\s+" + cantidad + r"\s+" + tipo + r")?"
        r"\s*[,;:]?\s*(?:(?:es|de)\s+)*(?:" + moneda + r"\s*)?([\d.,]+)\b"
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


# Valores dimensionales en palabras del ASR. Intencionadamente no se incorpora
# al lector general de precios/cantidades: una palabra sólo es una medida si
# aparece acompañada de eje explícito y unidad de longitud reconocida.
_DIM_UNIDADES = {
    "un": 1,
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
}
_DIM_CORTOS = {
    "diez": 10,
    "once": 11,
    "doce": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciseis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
    "veinte": 20,
    "veintiuno": 21,
    "veintiun": 21,
    "veintiuna": 21,
    "veintidos": 22,
    "veintitres": 23,
    "veinticuatro": 24,
    "veinticinco": 25,
    "veintiseis": 26,
    "veintisiete": 27,
    "veintiocho": 28,
    "veintinueve": 29,
}
_DIM_DECENAS = {
    "treinta": 30,
    "cuarenta": 40,
    "cincuenta": 50,
    "sesenta": 60,
    "setenta": 70,
    "ochenta": 80,
    "noventa": 90,
}
_DIM_CENTENAS = {
    "cien": 100,
    "ciento": 100,
    "doscientos": 200,
    "doscientas": 200,
    "trescientos": 300,
    "trescientas": 300,
    "cuatrocientos": 400,
    "cuatrocientas": 400,
    "quinientos": 500,
    "quinientas": 500,
    "seiscientos": 600,
    "seiscientas": 600,
    "setecientos": 700,
    "setecientas": 700,
    "ochocientos": 800,
    "ochocientas": 800,
    "novecientos": 900,
    "novecientas": 900,
}


def _dimension_numero_palabras(raw: str) -> Decimal | None:
    """Parseo estricto de enteros españoles 1..9999; nunca adivina valores.

    Rechaza gramáticas incompletas: «ciento y...», decenas + «ciento»,
    tokens intermedios extraños y cifras mezcladas. Los offsets quedan intactos.
    """
    import unicodedata

    frase = "".join(
        char
        for char in unicodedata.normalize("NFD", raw.casefold())
        if unicodedata.category(char) != "Mn"
    )
    tokens = frase.split()
    if not tokens or len(tokens) > 7:
        return None

    def menor_100(partes: list[str]) -> int | None:
        if len(partes) == 1:
            return (
                _DIM_UNIDADES.get(partes[0])
                or _DIM_CORTOS.get(partes[0])
                or _DIM_DECENAS.get(partes[0])
            )
        if (
            len(partes) == 3
            and partes[1] == "y"
            and partes[0] in _DIM_DECENAS
            and partes[2] in _DIM_UNIDADES
        ):
            return _DIM_DECENAS[partes[0]] + _DIM_UNIDADES[partes[2]]
        return None

    def menor_1000(partes: list[str]) -> int | None:
        if not partes:
            return None
        numero = menor_100(partes)
        if numero is not None:
            return numero
        centena = _DIM_CENTENAS.get(partes[0])
        if centena is None:
            return None
        if len(partes) == 1:
            return centena if partes[0] != "ciento" else None
        if partes[0] == "cien":
            return None
        resto = menor_100(partes[1:])
        return centena + resto if resto is not None else None

    if "mil" in tokens:
        indice = tokens.index("mil")
        if indice == 0:
            miles = 1
        elif indice == 1 and tokens[0] in _DIM_UNIDADES:
            miles = _DIM_UNIDADES[tokens[0]]
        else:
            return None
        resto = menor_1000(tokens[indice + 1 :]) if indice + 1 < len(tokens) else 0
        numero = miles * 1000 + resto if resto is not None else None
    else:
        numero = menor_1000(tokens)
    return Decimal(numero) if numero is not None and 1 <= numero <= 9999 else None


# La gramática se acota mediante léxico explícito. «y» sólo se acepta dentro
# de una decena compuesta; la función numérica valida la secuencia íntegra.
_DIM_LEXICO = (
    set(_DIM_UNIDADES)
    | set(_DIM_CORTOS)
    | set(_DIM_DECENAS)
    | set(_DIM_CENTENAS)
    | {"mil", "y", "dieciséis", "veintidós", "veintitrés", "veintiséis", "veintiún"}
)
_DIM_PALABRAS_PATRON = (
    r"\b(?:"
    + "|".join(sorted(_DIM_LEXICO - {"y"}, key=len, reverse=True))
    + r")\b"
    + r"(?:\s+(?:"
    + "|".join(sorted(_DIM_LEXICO, key=len, reverse=True))
    + r")\b){0,6}"
)


def _fragmento_numerico_truncado(text: str, start: int) -> bool:
    """Impide que se tome sólo el sufijo de una expresión numérica inválida."""
    import unicodedata

    contexto = "".join(
        char
        for char in unicodedata.normalize("NFD", text[max(0, start - 40) : start].casefold())
        if unicodedata.category(char) != "Mn"
    )
    anterior = re.findall(r"\w+", contexto)
    if (
        len(anterior) >= 2
        and anterior[-1] == "y"
        and (
            anterior[-2] in _DIM_LEXICO
            or anterior[-2] in {"metro", "metros", "centimetro", "centimetros", "cm", "mm"}
        )
    ):
        return True
    if (
        len(anterior) >= 2
        and anterior[-1] in {"coma", "punto", "con"}
        and (anterior[-2] in _DIM_LEXICO or anterior[-2].isdigit())
    ):
        return True
    if anterior and anterior[-1] in _DIM_LEXICO and anterior[-1] != "y":
        return True
    return False


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
        + r"\s*(?:de\s+)?(?:total\s+)?(\d+(?:[.,]\d+)*)\s*("
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
                    if token.startswith(("mili", "milí")) or token == "mm"
                    else "cm"
                    if token.startswith("cent") or token == "cm"
                    else "m"
                )
            found.append(
                Match(match.start(), match.end(), match.group(), label.upper(), (value, normalized))
            )

    # Sólo los valores en palabras con unidad inequívoca y eje explícito.
    # La ruta preexistente de dígitos queda sin alteración alguna.
    palabras_eje = re.compile(
        axis + r"\s*(?:de\s+)?(?:total\s+)?(" + _DIM_PALABRAS_PATRON + r")\s+(" + unit + r")",
        re.I,
    )
    palabras_invertido = re.compile(
        r"(" + _DIM_PALABRAS_PATRON + r")\s+(" + unit + r")\s*(?:de\s+)?" + axis + r"\b",
        re.I,
    )
    for patron in (palabras_eje, palabras_invertido):
        for coincidencia in patron.finditer(text):
            if patron is palabras_invertido and _fragmento_numerico_truncado(
                text, coincidencia.start(1)
            ):
                continue
            valor = _dimension_numero_palabras(coincidencia.group(1))
            if valor is None:
                continue
            unidad = coincidencia.group(2).casefold()
            normalizada = (
                "mm"
                if unidad.startswith(("mili", "milí")) or unidad == "mm"
                else "cm"
                if unidad.startswith("cent") or unidad == "cm"
                else "m"
            )
            found.append(
                Match(
                    coincidencia.start(),
                    coincidencia.end(),
                    coincidencia.group(),
                    label.upper(),
                    (valor, normalizada),
                )
            )
    return sorted(found, key=lambda encontrada: encontrada.start)


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
        texto_accesorio = match.group().strip()
        # El ASR a menudo omite la coma antes de otra cláusula:
        # «dos tomacorrientes al centro estructura en tablero».
        # No eliminar «estructura» si es objeto de «de/en/para/con», pues
        # puede ser una descripción propia de un accesorio.
        for nuevo_campo in re.finditer(
            r"\b(?:estructura|precio|dimensiones?)\b", texto_accesorio, re.I
        ):
            if nuevo_campo.start() == 0:
                continue
            prefijo_palabra = re.search(r"\b(\w+)\s+$", texto_accesorio[: nuevo_campo.start()])
            if (
                nuevo_campo.group().casefold() == "estructura"
                and prefijo_palabra
                and prefijo_palabra.group(1).casefold() in {"de", "del", "en", "para", "con"}
            ):
                continue
            texto_accesorio = texto_accesorio[: nuevo_campo.start()].rstrip()
            break
        texto_accesorio = re.sub(
            r"(?:\s+(?:de|del|en|con|para|por|a|al))+$",
            "",
            texto_accesorio,
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
