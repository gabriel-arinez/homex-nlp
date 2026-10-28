"""Offline PRF-03-shaped projection and strict scoped field comparison.

No database/catalogue IDs are fabricated. Component attribute names are textual,
using the actual accepted evidence. This is not the backend deployment adapter.
"""

import re
from collections import Counter
from decimal import Decimal

from training.integral_v2.numbers import folded, measurement


def normalized_value(value):
    if isinstance(value, str):
        try:
            m = measurement(value)
            return (format(Decimal(m["valor"]).normalize(), "f"), m["unidad"])
        except ValueError:
            return " ".join(folded(value).split())
    if isinstance(value, dict) and set(value) >= {"valor", "unidad"}:
        return (format(Decimal(value["valor"]).normalize(), "f"), value["unidad"])
    return str(value)


def project(result):
    item = result.get("item_proposal") if result else None
    if not item:
        return {
            "comercial": {},
            "especificacion": {
                "datos_tecnicos": {
                    "componentes": [],
                    "conjuntos": [],
                    "accesorios": [],
                    "caracteristicas_generales": {},
                    "advertencias": [],
                    "descripcion_original": result.get("text_original", "") if result else "",
                }
            },
        }
    accepted = [c for c in result["candidates"] if c["decision"] == "ACCEPTED"]
    technical = {
        "componentes": [
            {"uid": c["component_id"], "nombre": c["name"]} for c in item["components"]
        ],
        "conjuntos": [],
        "accesorios": [a["name"] for a in item["accessories"]],
        "caracteristicas_generales": {},
        "advertencias": [w["message"] for w in result["warnings"]],
        "descripcion_original": result["text_original"],
    }
    components = {c["uid"]: c for c in technical["componentes"]}
    general = technical["caracteristicas_generales"]
    groups = {}
    for candidate in accepted:
        label = candidate["label"]
        v = candidate.get("normalized_value")
        cp = components.get(candidate.get("component_ref"))
        if label == "CONJUNTO" and isinstance(v, dict):
            groups[v["group_id"]] = {"uid": v["group_id"], "nombre": v["name"]}
        if label == "COMPONENTE" and cp and isinstance(v, dict) and v.get("conjunto_ref"):
            cp["conjunto_uid"] = v["conjunto_ref"]
        if label == "CANTIDAD_INTERNA" and cp and type(v) is int and v > 0:
            cp["cantidad_interna"] = v
        if label in ("MATERIAL", "COLOR", "ACABADO"):
            target = cp if cp else general
            if cp:
                target[label.lower()] = candidate["text"]
            else:
                target.setdefault("atributos", []).append(
                    {"nombre": label.lower(), "valor": candidate["text"]}
                )
    technical["conjuntos"] = [
        g
        for g in groups.values()
        if any(c.get("conjunto_uid") == g["uid"] for c in components.values())
    ]
    for key in ("dimensions", "thicknesses"):
        for m in item[key]:
            target = components.get(m.get("component_ref"), general)
            value = {"valor": m["value"], "unidad": m["unit"]}
            if key == "dimensions" and m.get("axis"):
                target.setdefault("dimensiones", {})[m["axis"]] = value
            elif key == "thicknesses":
                if target is general:
                    target.setdefault("atributos", []).append(
                        {"nombre": "espesor", "valor": m["original_text"]}
                    )
                else:
                    target["espesor"] = value
    # PRF03 rejects duplicate attribute names. Preserve repeated values in one
    # textual attribute; no arbitrary last-value selection in the projection.
    attrs = general.get("atributos", [])
    collected = {}
    for a in attrs:
        collected.setdefault(a["nombre"], []).append(a["valor"])
    if attrs:
        general["atributos"] = [
            {"nombre": k, "valor": " | ".join(dict.fromkeys(v))} for k, v in collected.items()
        ]
    commercial = {
        "nombre": item["name"],
        "cantidad": str(item["quantity"]) if item["quantity"] else None,
        "unidad_codigo": None,
        "precio_unitario": None,
        "precio_total_explicito": None,
        "descuento_linea": None,
        "precio_catalogo": None,
    }
    for label, key in [
        ("UNIDAD_MEDIDA", "unidad_codigo"),
        ("DESCUENTO", "descuento_linea"),
        ("PRECIO_TOTAL", "precio_total_explicito"),
    ]:
        values = {
            str(c["normalized_value"])
            for c in accepted
            if c["label"] == label and c.get("normalized_value") is not None
        }
        if len(values) == 1:
            commercial[key] = next(iter(values))
    if item["price"] and item["price"]["mode"] == "PRECIO_UNITARIO":
        commercial["precio_unitario"] = item["price"]["unit_price_input"]
    price = item.get("price")
    commercial["precio_total_efectivo"] = None
    if price:
        if price["mode"] == "TOTAL_NEGOCIADO":
            commercial["precio_total_efectivo"] = price["line_total"]
            if price.get("origin") == "EXPLICIT_TOTAL":
                commercial["precio_total_explicito"] = price["line_total"]
        elif price.get("line_total") is not None:
            commercial["precio_total_efectivo"] = format(
                Decimal(price["line_total"]) - Decimal(commercial.get("descuento_linea") or "0"),
                "f",
            )
    return {"comercial": commercial, "especificacion": {"datos_tecnicos": technical}}


def attribute_key(name):
    text = folded(name)
    for key, pattern in [
        ("material", r"material"),
        ("espesor", r"espesor"),
        ("color", r"^color(?: |$)"),
        ("acabado", r"^acabado"),
    ]:
        if re.search(pattern, text):
            return key
    return "atributo:" + text


def fields(expected):
    output = {}
    commercial = dict(expected.get("comercial", {}))
    if commercial.get("precio_total_efectivo") is None:
        if commercial.get("precio_total_explicito") is not None:
            commercial["precio_total_efectivo"] = commercial["precio_total_explicito"]
        elif (
            commercial.get("cantidad") is not None and commercial.get("precio_unitario") is not None
        ):
            commercial["precio_total_efectivo"] = str(
                Decimal(commercial["cantidad"]) * Decimal(commercial["precio_unitario"])
                - Decimal(commercial.get("descuento_linea") or "0")
            )
    for key in (
        "nombre",
        "cantidad",
        "unidad_codigo",
        "precio_unitario",
        "precio_total_explicito",
        "descuento_linea",
        "precio_catalogo",
        "precio_total_efectivo",
    ):
        value = commercial.get(key)
        if value is not None:
            output["ITEM", key] = (
                format(Decimal(str(value)).normalize(), "f")
                if key
                in (
                    "cantidad",
                    "precio_unitario",
                    "precio_total_explicito",
                    "descuento_linea",
                    "precio_catalogo",
                    "precio_total_efectivo",
                )
                else normalized_value(value)
            )
    tech = expected.get("especificacion", {}).get("datos_tecnicos", {})
    groups = {g["uid"]: g["nombre"] for g in tech.get("conjuntos", [])}
    names = Counter(normalized_value(c["nombre"]) for c in tech.get("componentes", []))
    for i, component in enumerate(tech.get("componentes", [])):
        # Stable semantic identity ignores array ordering and generated IDs; groups
        # disambiguate repeated names and are also scored as explicit relations.
        name = normalized_value(component["nombre"])
        scope = "COMP:" + name
        if names[name] > 1:
            scope += ":GROUP:" + normalized_value(
                groups.get(component.get("conjunto_uid"), "SIN_GRUPO")
            )
        output[scope, "nombre"] = name
        if component.get("conjunto_uid"):
            output[scope, "conjunto"] = normalized_value(groups[component["conjunto_uid"]])
        for key in ("material", "color", "acabado", "espesor", "cantidad_interna"):
            if component.get(key) is not None:
                output[scope, key] = normalized_value(component[key])
        for axis, m in component.get("dimensiones", {}).items():
            output[scope, "dimension:" + axis] = normalized_value(m)
        for a in component.get("atributos", []):
            output[scope, attribute_key(a["nombre"])] = normalized_value(a["valor"])
    general = tech.get("caracteristicas_generales", {})
    for axis, m in general.get("dimensiones", {}).items():
        output["ITEM", "dimension:" + axis] = normalized_value(m)
    for i, a in enumerate(general.get("atributos", [])):
        key = attribute_key(a["nombre"])
        # Preserve multiple reviewed global values as separate scoped claims.
        target = ("ITEM", key)
        if target in output and output[target] != normalized_value(a["valor"]):
            target = ("ITEM", key + ":" + str(i))
        output[target] = normalized_value(a["valor"])
    for a in tech.get("accesorios", []):
        output["ACCESSORY:" + normalized_value(a), "nombre"] = normalized_value(a)
    return output


def compare(wanted, actual):
    counters = {}
    reviewed = {
        ("ITEM", k)
        for k in (
            "nombre",
            "cantidad",
            "unidad_codigo",
            "precio_unitario",
            "precio_total_explicito",
            "descuento_linea",
            "precio_catalogo",
            "precio_total_efectivo",
        )
    }
    for key in set(wanted) | set(actual) | reviewed:
        a, b = wanted.get(key), actual.get(key)
        c = counters.setdefault(key[1], Counter())
        c["opportunities"] += 1
        c["tp"] += a is not None and a == b
        c["fp"] += b is not None and b != a
        c["fn"] += a is not None and b != a
        c["safe_abstention"] += a is None and b is None
    return {k: dict(v) for k, v in counters.items()}
