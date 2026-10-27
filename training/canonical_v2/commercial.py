"""Scope-aware technical metrics recovered from PR24; no human-gold claim."""

import re
from collections import Counter, defaultdict
from decimal import Decimal

from training.canonical_v2.io import digest

ROOT_FIELDS = {
    "nombre": "product",
    "cantidad": "sold_quantity",
    "unidad_codigo": "unit",
    "precio_unitario": "unit_price",
    "precio_total_explicito": "total_price",
}
AXES = {"alto", "ancho", "largo", "profundidad", "diametro"}


def literal(value):
    return " ".join(str(value).casefold().split())


def numeric(value):
    if not re.fullmatch(r"\d+(?:[.,]\d+)?", str(value)):
        raise ValueError("AMBIGUOUS_NUMERIC_REFERENCE")
    return format(Decimal(str(value).replace(",", ".")).normalize(), "f")


def measurement(value):
    if isinstance(value, dict):
        amount, unit = value.get("valor"), value.get("unidad")
    else:
        match = re.fullmatch(r"\s*([\d.,]+)\s*(mm|cm|m)\s*", str(value), re.I)
        if not match:
            raise ValueError("NOT_EVALUABLE_MEASUREMENT")
        amount, unit = match[1], match[2].lower()
    if unit not in {"mm", "cm", "m"}:
        raise ValueError("NOT_EVALUABLE_UNIT")
    return numeric(amount), unit


def component_scope(name):
    return "COMP-" + digest(literal(name))[:16]


def reference_fields(ref):
    fields = {}
    reviewed = {("ITEM", field) for field in ROOT_FIELDS.values()}
    for key, field in ROOT_FIELDS.items():
        value = ref["comercial"].get(key)
        if value is not None:
            fields["ITEM", field] = (
                numeric(value)
                if field in {"sold_quantity", "unit_price", "total_price"}
                else literal(value)
            )
    technical = ref.get("especificacion", {}).get("datos_tecnicos", {})
    components = technical.get("componentes", [])
    if len({literal(c["nombre"]) for c in components}) != len(components):
        raise ValueError("NOT_EVALUABLE_AMBIGUOUS_COMPONENT_NAMES")
    for c in components:
        scope = component_scope(c["nombre"])
        fields[scope, "component_name"] = literal(c["nombre"])
        for field in ("material", "color", "acabado", "espesor"):
            if c.get(field) is not None:
                fields[scope, field] = (
                    measurement(c[field]) if field == "espesor" else literal(c[field])
                )
        for axis, value in c.get("dimensiones", {}).items():
            if axis in AXES:
                fields[scope, "dimension_" + axis] = measurement(value)
    for axis, value in (
        technical.get("caracteristicas_generales", {}).get("dimensiones", {}).items()
    ):
        if axis in AXES:
            fields["ITEM", "dimension_" + axis] = measurement(value)
    for accessory in technical.get("accesorios", []):
        if not isinstance(accessory, str):
            raise ValueError("NOT_EVALUABLE_ACCESSORY_REFERENCE")
        fields["ACCESSORY-" + digest(literal(accessory))[:16], "accessory_name"] = literal(
            accessory
        )
    reviewed.update(fields)
    return fields, reviewed


def assign(fields, key, value):
    if key in fields and fields[key] != value:
        raise ValueError("NOT_EVALUABLE_AMBIGUOUS_PREDICTED_FIELD")
    fields[key] = value


def predicted_fields(result):
    fields = {}
    item = result.get("item_proposal")
    if not item:
        return fields
    for key, field in (("name", "product"), ("quantity", "sold_quantity")):
        if item.get(key) is not None:
            fields["ITEM", field] = (
                numeric(item[key]) if field == "sold_quantity" else literal(item[key])
            )
    price = item.get("price")
    if price:
        if price["mode"] == "PRECIO_UNITARIO":
            fields["ITEM", "unit_price"] = numeric(price["unit_price_input"])
        else:
            fields["ITEM", "total_price"] = numeric(price["line_total"])
    units = {
        c["normalized_value"]
        for c in result["candidates"]
        if c["label"] == "UNIDAD_MEDIDA"
        and c["decision"] == "ACCEPTED"
        and isinstance(c.get("normalized_value"), str)
    }
    if len(units) == 1:
        fields["ITEM", "unit"] = literal(next(iter(units)))
    components = {c["component_id"]: component_scope(c["name"]) for c in item["components"]}
    if len(set(components.values())) != len(components):
        raise ValueError("NOT_EVALUABLE_DUPLICATE_COMPONENT_NAMES")
    for c in item["components"]:
        fields[components[c["component_id"]], "component_name"] = literal(c["name"])
    for c in result["candidates"]:
        if c["decision"] == "ACCEPTED" and c["label"] in {"MATERIAL", "COLOR", "ACABADO"}:
            scope = components.get(c.get("component_ref"), "ITEM")
            assign(fields, (scope, c["label"].lower()), literal(c["text"]))
    for d in item["dimensions"]:
        if d.get("axis") and d.get("unit"):
            fields[components.get(d.get("component_ref"), "ITEM"), "dimension_" + d["axis"]] = (
                numeric(d["value"]),
                d["unit"],
            )
    for d in item["thicknesses"]:
        if d.get("unit"):
            fields[components.get(d.get("component_ref"), "ITEM"), "espesor"] = (
                numeric(d["value"]),
                d["unit"],
            )
    for accessory in item["accessories"]:
        fields["ACCESSORY-" + digest(literal(accessory["name"]))[:16], "accessory_name"] = literal(
            accessory["name"]
        )
    return fields


def compare_fields(wanted, actual, reviewed):
    counts = defaultdict(Counter)
    # Root negatives are explicitly scoped; observed extra relation assertions are
    # scored under RC2's SIN_EVIDENCIA_NO_COMPLETAR policy, never whole-universe TN.
    for key in reviewed | set(wanted) | set(actual):
        a, b = wanted.get(key), actual.get(key)
        row = counts[key[1]]
        row["opportunities"] += 1
        row["positive_reference"] += a is not None
        row["positive_prediction"] += b is not None
        correct = a is not None and b is not None and a == b
        row["correct"] += correct
        row["omission"] += a is not None and not correct
        row["false_assertion"] += b is not None and not correct
        row["safe_abstention"] += a is None and b is None
    return {k: dict(v) for k, v in counts.items()}
