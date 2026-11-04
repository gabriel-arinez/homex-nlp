"""Literal V1 text audit, independent of V1 spans/expected and runtime predictions.

Restricted to the documented synthetic V1 grammar; unsupported text is quarantined.
This is a technical reference, never a claim of independent human annotation.
"""

import re
from decimal import Decimal

NUMBER = r"\d[\d.,]*\d|\d"
COMPONENTS = (
    "Plano de lectura|Mesón principal|Mesa central|Mesas laterales|Estructura|"
    "Puertas|Cuerpo|Tablero|Tapa|Respaldo|Laterales|Frente|Repisas|Base|Divisiones|"
    "Armazón|Asiento|Mesada|Retorno|Mesón|Estantes|Mostrador|Cajones|Cajonera|Entrepaños"
)
WORDS = {"una": "1", "un": "1", "dos": "2", "tres": "3", "cuatro": "4", "cinco": "5"}


def number(raw):
    if raw.lower() in WORDS:
        return WORDS[raw.lower()]
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    return str(Decimal(raw))


def evidence(text, start, end):
    return {"start": start, "end": end, "text": text[start:end]}


def audit_literal(text, category):
    """Parse full literal strings; no input entities or source expected accepted."""
    facts, errors = [], []

    def fact(path, value, match, group=0, rule="literal"):
        facts.append(
            {
                "path": path,
                "value": value,
                "evidence": evidence(text, *match.span(group)),
                "rule": rule,
            }
        )
        return value

    name = re.match(r"(.+?)(?: a medida| fabricado a pedido)?\.", text)
    commercial = {
        "nombre": None,
        "cantidad": None,
        "unidad_codigo": None,
        "precio_unitario": None,
        "precio_total_explicito": None,
        "moneda_codigo": None,
        "descuento_linea": None,
    }
    if name:
        commercial["nombre"] = fact("comercial.nombre", name[1], name, 1)
    for key, pattern in {
        "cantidad": rf"(?:Cantidad:|Se cotizan)\s+({NUMBER})\s+",
        "precio_unitario": rf"(?:precio unitario|precio por unidad|valor unitario) (?:Bs|USD) ({NUMBER})",
        "precio_total_explicito": rf"(?:subtotal neto|importe de línea|total por este producto) (?:Bs|USD) ({NUMBER})",
        "descuento_linea": rf"descuento de línea (?:Bs|USD) ({NUMBER})",
    }.items():
        m = re.search(pattern, text)
        if m:
            commercial[key] = fact("comercial." + key, number(m[1]), m, 1, "decimal_literal")
        elif key != "descuento_linea":
            errors.append("GRAMATICA_NO_RECONOCIDA:" + key)
    unit = re.search(
        r"(?:Cantidad:|Se cotizan)\s+[\d.,]+\s+(metros cuadrados|Mts\.2|m²|pzas?|piezas?|unidad(?:es)?|juegos?|barras?)",
        text,
    )
    if unit:
        raw = unit[1]
        u = (
            "M2"
            if raw in ("metros cuadrados", "Mts.2", "m²")
            else "JUEGO"
            if raw.startswith("juego")
            else "BARRA"
            if raw.startswith("barra")
            else "PIEZA"
        )
        commercial["unidad_codigo"] = fact(
            "comercial.unidad_codigo", u, unit, 1, "unidad_comercial_literal"
        )
    else:
        errors.append("UNIDAD_NO_RECONOCIDA")
    currency = re.search(r"(?:precio unitario|precio por unidad|valor unitario) (Bs|USD)", text)
    if currency:
        commercial["moneda_codigo"] = fact(
            "comercial.moneda_codigo",
            "BOB" if currency[1] == "Bs" else "USD",
            currency,
            1,
            "codigo_moneda_literal",
        )
    technical = {
        "descripcion_original": text,
        "componentes": [],
        "conjuntos": [],
        "accesorios": [],
        "caracteristicas_generales": {},
        "advertencias": [],
    }
    dims = {}
    for m in re.finditer(rf"\b(alto|ancho|profundidad|diámetro) ({NUMBER})\s*(mm|cm|m)\b", text):
        key = "diametro" if m[1] == "diámetro" else m[1]
        dims[key] = {"valor": number(m[2]), "unidad": m[3]}
        fact("dimensiones." + key, dims[key], m, rule="eje_valor_unidad_explicitos")
    if category == "muebles_pedido" and not (len(dims) == 3 or set(dims) == {"alto", "diametro"}):
        errors.append("DIMENSIONES_V1_INCOMPLETAS")
    if dims:
        technical["caracteristicas_generales"]["dimensiones"] = dims
    starts = list(
        re.finditer(
            rf"\b({COMPONENTS}) (?:— material: |compuesto de |se fabrica en )|\b({COMPONENTS}): ",
            text,
        )
    )
    for idx, m in enumerate(starts):
        end = starts[idx + 1].start() if idx + 1 < len(starts) else len(text)
        segment = text[m.end() : end]
        # Final component ends before global accessories and commercial context.
        stop = re.search(
            r" (?:Incorpora|Se entrega con|Accesorios incluidos:|Pedido comercial:|Cantidad:|Se cotizan|El juego integra)",
            segment,
        )
        if stop:
            segment = segment[: stop.start()]
        comp = {"uid": f"c{idx + 1}", "nombre": m[1] or m[2]}
        base = "componentes." + comp["uid"]
        fact(base + ".nombre", comp["nombre"], m, 1 if m[1] else 2)
        patterns = {
            "material": r"^(melamina|aluminio|acero|tablero HDF|vidrio templado|madera de eucalipto|espuma de alta densidad|tela de alto tráfico)\b",
            "espesor": r"(\d+(?:[.,]\d+)?\s*(?:mm|cm))\b",
            "color": r"(?:color |tapizado )(Negro mate|Gris ceniza|Roble claro|Blanco|Cedro|Olmo|Nogal|azul marino|gris|negro)\b|(transparente)\b",
            "acabado": r"(acabado satinado|canto termosellado|tapacanto de PVC)",
        }
        for key, pattern in patterns.items():
            a = re.search(pattern, segment)
            if a:
                group = 1 if a[1] else 2
                comp[key] = a[group]
                facts.append(
                    {
                        "path": base + "." + key,
                        "value": a[group],
                        "evidence": evidence(
                            text, m.end() + a.start(group), m.end() + a.end(group)
                        ),
                        "rule": "ambito_componente_literal",
                    }
                )
        if "material" not in comp:
            errors.append("MATERIAL_COMPONENTE_NO_RECONOCIDO:" + comp["nombre"])
        if "color a elección" in segment:
            technical["advertencias"].append(base + ".color:PENDIENTE")
        technical["componentes"].append(comp)
    if category == "muebles_pedido" and not starts:
        errors.append("COMPONENTES_NO_RECONOCIDOS")
    internal = []
    for m in re.finditer(
        r"\b(una|dos|tres|cinco) (mesa central|mesas laterales|cajones|repisas interiores|apoyos)\b",
        text,
    ):
        value = int(number(m[1]))
        target = m[2]
        relation = {
            "nombre": target,
            "cantidad_interna": value,
            "evidence": evidence(text, *m.span()),
            "commercial": False,
        }
        internal.append(relation)
        for comp in technical["componentes"]:
            if comp["nombre"].lower() == target or (
                target == "repisas interiores" and comp["nombre"] == "Repisas"
            ):
                comp["cantidad_interna"] = value
                fact(
                    "componentes." + comp["uid"] + ".cantidad_interna",
                    value,
                    m,
                    rule="cantidad_interna_literal",
                )
    capacity = []
    for m in re.finditer(r"\b(\d+) personas\b", text):
        capacity.append(
            {"personas": int(m[1]), "evidence": evidence(text, *m.span()), "commercial": False}
        )
    # Preserve global accessories as literal lists, before final commercial wording.
    for m in re.finditer(
        r"(?:Incorpora|Se entrega con|Accesorios incluidos:|Incluye) (.+?)(?=;|\. (?:Pedido comercial:|Cantidad:|Se cotizan)|\.\Z)",
        text,
    ):
        for a in re.finditer(r"[^,;]+", m[1]):
            raw = a.group().strip().rstrip(".")
            if not raw:
                continue
            start = m.start(1) + a.start() + len(a.group()) - len(a.group().lstrip())
            technical["accesorios"].append(raw)
            facts.append(
                {
                    "path": (
                        f"accesorios.{len(technical['accesorios']) - 1}"
                        if category == "muebles_pedido"
                        else f"especificacion.accesorios.{len(technical['accesorios']) - 1}"
                    ),
                    "value": raw,
                    "evidence": evidence(text, start, start + len(raw)),
                    "rule": "lista_literal_no_propagada",
                }
            )
    # Catalog attributes retain literal facts and do not pretend to be manufacturing components.
    attributes = []
    if category != "muebles_pedido":
        for m in re.finditer(
            r"(?:Material del núcleo: |Material |Composición: |Fabricado sobre |Fabricación estándar en |Tapizado en |Estructura en |espesor |resistencia |Color disponible: |color |terminación |acabado tonalidad |presentación de largo |altura visible )([^;.]+(?:[.,]\d+\s*m)?)",
            text,
        ):
            attributes.append({"literal": m[0], "evidence": evidence(text, *m.span())})
    for key in ["cantidad", "precio_unitario", "precio_total_explicito"]:
        if commercial[key] is None:
            continue
        if Decimal(commercial[key]) <= 0:
            errors.append("VALOR_NO_POSITIVO:" + key)
    if all(
        commercial[k] is not None for k in ["cantidad", "precio_unitario", "precio_total_explicito"]
    ):
        d = Decimal(commercial["descuento_linea"] or "0")
        if Decimal(commercial["cantidad"]) * Decimal(commercial["precio_unitario"]) - d != Decimal(
            commercial["precio_total_explicito"]
        ):
            errors.append("ARITMETICA")
    return {
        "comercial": commercial,
        "especificacion": {"datos_tecnicos": technical}
        if category == "muebles_pedido"
        else {"atributos_catalogo": attributes, "accesorios": technical["accesorios"]},
        "facts": facts,
        "cantidades_internas": internal,
        "capacidades": capacity,
        "errors": errors,
        "reference_method": "AUDITOR_LITERAL_V1_INDEPENDIENTE_DE_SPANS_NO_HUMANO",
        "discount_absence": "NO_MENCIONADO_NO_ASUMIR_CERO_PARA_DERIVAR_PRECIO",
    }
