"""Fail-closed compiler for private assisted adjudications.

An automatic proposal is never a review. The caller supplies a separately frozen
adjudication for each source item, including exclusions. Certificates bind the
complete source, entities and field relations, not just a boolean approval flag.
No private lexicon, source text or trained parameters belong in this package.
"""

import json
import re
from decimal import Decimal

from training.canonical_v2.io import digest
from training.canonical_v2.validate import LABELS
from training.integral_v2.numbers import folded, measurement, number
from training.integral_v2.tokenizer import create_nlp

VERSION = "2.0.0-offline.5.1"
CHECKS = (
    "segmentation",
    "entities_24",
    "component_scope",
    "internal_quantity",
    "commercial_quantity",
    "dimensions_units",
    "prices_context_arithmetic",
    "negation_rectification",
    "source_offsets",
    "complete_literal",
)
DESTINATIONS = {"APTO", "PARCIAL_NO_ENTRENABLE", "CUARENTENA", "DESCARTADO"}


def seal(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def payload(review):
    return {k: v for k, v in review.items() if k != "certificate"}


def leaves(value, path=""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, path + "/" + str(key))
    elif isinstance(value, list):
        for key, child in enumerate(value):
            yield from leaves(child, path + "/" + str(key))
    else:
        yield path, value


def validate_review(item, review, certificate):
    """Raise on any unsupported promotion or change to the frozen adjudication.

    The certificate is stored separately from the compiled bundle. It establishes
    review integrity, not independent human/external accuracy. That distinction
    must survive all exports.
    """

    def require(condition, code):
        if not condition:
            raise ValueError(code)

    text = item["item_text"]
    require(review["item_id"] == item["id"], "ITEM_ID")
    require(review["source_sha256"] == item["source_sha256"], "SOURCE_HASH")
    require(review["text_sha256"] == digest(text), "SOURCE_LITERAL_CHANGED")
    require(review.get("human_reviewed") is False, "FALSE_HUMAN_REVIEW")
    require(review.get("review_kind") == "REVISION_TECNICA_ASISTIDA", "REVIEW_KIND")
    require(review["decision"] in DESTINATIONS, "DESTINATION")
    require(bool(review.get("reason")), "MISSING_DECISION_REASON")
    require(seal(payload(review)) == certificate, "ADJUDICATION_CHANGED")
    if review["decision"] != "APTO":
        require(not review.get("supervised"), "EXCLUDED_SUPERVISION")
        require(bool(review.get("conflicts")), "EXCLUSION_WITHOUT_EVIDENCE")
        return
    require(review.get("supervised") is True, "APTO_NOT_SUPERVISED")
    require(set(review["checklist"]) == set(CHECKS), "PARTIAL_CHECKLIST")
    require(all(review["checklist"].values()), "UNRESOLVED_CHECK")
    require(review.get("annotation_scope") == "FULL_ITEM", "PARTIAL_AS_COMPLETE")
    nlp = create_nlp()
    doc = nlp.make_doc(text)
    entities = review["entities"]
    last = 0
    for start, end, label in entities:
        require(type(start) is int and type(end) is int, "SPAN_TYPE")
        require(0 <= start < end <= len(text) and start >= last, "SPAN_BOUNDS_OVERLAP")
        require(label in LABELS, "LABEL")
        require(doc.char_span(start, end, alignment_mode="strict") is not None, "ALIGNMENT")
        last = end
    # A known axis does not cease to be an NER entity when its unit is absent.
    axes = {"ancho": "ANCHO", "alto": "ALTO", "profundidad": "PROFUNDIDAD", "prof": "PROFUNDIDAD"}
    for match in re.finditer(
        r"(?i)(?<![\w.,])(\d+[.,]\d+)\s+(?:de\s+)?(ancho|alto|profundidad|prof\.?)\b", text
    ):
        label = axes[match[2].rstrip(".").lower()]
        require(
            any(
                a <= match.start(1) and b >= match.end(1) and entity_label == label
                for a, b, entity_label in entities
            ),
            "UNANNOTATED_NAMED_AXIS",
        )
    for match in re.finditer(
        r"(?i)(?<![\w.,])(\d+(?:[.,]\d+)?\s*[xX]\s*\d+(?:[.,]\d+)?\s*m)\s*(?:de\s+)?(ancho|profundidad)\b",
        text,
    ):
        label = axes[match[2].lower()]
        require(
            any(
                a <= match.start(1) and b >= match.end(1) and entity_label == label
                for a, b, entity_label in entities
            ),
            "UNANNOTATED_COMPLEX_AXIS",
        )
    expected = review["expected"]
    require(
        any(e[2] == "PRODUCTO" for e in entities)
        or (item["document_level"] == "SINTETICO_ORAL" and expected.get("status") == "NO_PROPOSAL"),
        "MISSING_PRODUCT",
    )
    tech = expected["especificacion"]["datos_tecnicos"]
    require(tech["descripcion_original"] == text, "INCOMPLETE_LITERAL")
    components = tech["componentes"]
    require(len(components) <= 40 and len(tech["conjuntos"]) <= 10, "PRF03_LIMIT")
    uids = [c["uid"] for c in components]
    require(len(uids) == len(set(uids)), "DUPLICATE_COMPONENT")
    for c in components:
        if "cantidad_interna" in c:
            require(
                type(c["cantidad_interna"]) is int and c["cantidad_interna"] > 0,
                "INTERNAL_QUANTITY_TYPE",
            )
    group_ids = [g["uid"] for g in tech["conjuntos"]]
    require(len(group_ids) == len(set(group_ids)), "DUPLICATE_GROUP")
    require("schema_version" not in tech, "PRF03_SCHEMA_VERSION")
    for group in tech["conjuntos"]:
        require(
            isinstance(group.get("nombre"), str) and bool(group["nombre"].strip()), "GROUP_NAME"
        )
        require(any(c.get("conjunto_uid") == group["uid"] for c in components), "EMPTY_GROUP")
    for c in components:
        require(c.get("conjunto_uid") is None or c["conjunto_uid"] in group_ids, "ORPHAN_COMPONENT")
        require(isinstance(c.get("nombre"), str) and bool(c["nombre"].strip()), "COMPONENT_NAME")
    for container in [tech["caracteristicas_generales"], *components]:
        attrs = container.get("atributos", [])
        require(isinstance(attrs, list), "PRF03_ATTRIBUTES_TYPE")
        names = set()
        for attr in attrs:
            require(
                isinstance(attr.get("nombre"), str)
                and bool(attr["nombre"].strip())
                and len(attr["nombre"]) <= 150,
                "PRF03_ATTRIBUTE_NAME",
            )
            attribute_identity = attr.get("codigo", attr["nombre"]).casefold().strip()
            require(attribute_identity not in names, "PRF03_ATTRIBUTE_DUPLICATE")
            names.add(attribute_identity)
            require(
                isinstance(attr.get("valor"), (str, int, float))
                and not isinstance(attr["valor"], bool)
                and bool(str(attr["valor"]).strip()),
                "PRF03_ATTRIBUTE_VALUE",
            )
    for key in ("accesorios", "advertencias"):
        require(
            isinstance(tech[key], list)
            and all(isinstance(x, str) and bool(x.strip()) for x in tech[key]),
            "PRF03_TEXT_LIST",
        )
    facts = review["facts"]
    paths = dict(leaves(expected))
    # Containers carry no assertion; all scalar leaves including nulls need a disposition.
    require(set(paths) == {f["path"] for f in facts}, "UNREVIEWED_EXPECTED_FIELD")
    require(len(facts) == len(paths), "DUPLICATE_FACT")
    for fact in facts:
        require(paths[fact["path"]] == fact["value"], "FALSE_SEMANTIC_VALUE")
        require(
            fact["state"] in {"EXPLICITO", "DERIVADO_EXACTO", "AMBIGUO", "AUSENTE", "INVALIDO"},
            "FACT_STATE",
        )
        require(bool(fact["rule"]), "MISSING_INFERENCE_RULE")
        if fact["state"] == "AUSENTE":
            require(fact["value"] is None, "ABSENT_VALUE_INVENTED")
        else:
            require(bool(fact["evidence"]), "UNEVIDENCED_FACT")
        for evidence in fact["evidence"]:
            a, b = evidence["start"], evidence["end"]
            require(0 <= a < b <= len(text) and text[a:b] == evidence["text"], "FACT_OFFSET")
            require(
                evidence["source_start"] == item["char_start"] + a
                and evidence["source_end"] == item["char_start"] + b,
                "SOURCE_OFFSET",
            )
        for index in fact.get("entity_refs", []):
            require(type(index) is int and 0 <= index < len(entities), "ORPHAN_ENTITY")
        semantic_label = None
        field_path = fact["path"]
        if field_path.endswith(("/material", "/color", "/acabado", "/espesor")):
            semantic_label = field_path.rsplit("/", 1)[1].upper()
        for axis in ("alto", "ancho", "largo", "profundidad", "diametro"):
            if "/dimensiones/" + axis in field_path:
                semantic_label = axis.upper()
        if "/espesor/" in field_path:
            semantic_label = "ESPESOR"
        if semantic_label and fact["state"] == "EXPLICITO" and fact["value"] is not None:
            relevant = [
                entities[i] for i in fact.get("entity_refs", []) if entities[i][2] == semantic_label
            ]
            require(bool(relevant), "MISSING_SEMANTIC_ENTITY")
            for ev in fact["evidence"]:
                require(
                    not (
                        ev["text"][0].isdigit()
                        and ev["start"] > 0
                        and text[ev["start"] - 1].isdigit()
                    ),
                    "NUMERIC_SUFFIX_EVIDENCE",
                )
            if semantic_label in {"MATERIAL", "COLOR", "ACABADO"} and isinstance(
                fact["value"], str
            ):
                require(
                    any(folded(ev["text"]) == folded(fact["value"]) for ev in fact["evidence"]),
                    "SEMANTIC_LITERAL_VALUE",
                )
            if (
                semantic_label == "ESPESOR"
                and field_path.endswith("/espesor")
                and isinstance(fact["value"], str)
            ):
                require(
                    any(
                        measurement(ev["text"]) == measurement(fact["value"])
                        for ev in fact["evidence"]
                    ),
                    "THICKNESS_VALUE_CONFLICT",
                )
    commercial = expected["comercial"]
    by_path = {f["path"]: f for f in facts}
    for key, label in (
        ("cantidad", "CANTIDAD"),
        ("precio_unitario", "PRECIO_UNITARIO"),
        ("precio_total_explicito", "PRECIO_TOTAL"),
    ):
        value = commercial.get(key)
        if value is None:
            continue
        require(Decimal(value).is_finite() and Decimal(value) >= 0, "INVALID_DECIMAL")
        if key == "cantidad":
            require(Decimal(value) > 0, "INVALID_SOLD_QUANTITY")
        fact = by_path["/comercial/" + key]
        require(fact["state"] == "EXPLICITO", "UNAUTHORIZED_COMMERCIAL_DERIVATION")
        matching = [i for i in fact.get("entity_refs", []) if entities[i][2] == label]
        require(bool(matching), "COMMERCIAL_INTERNAL_QUANTITY_OR_PRICE_CONFUSION")
        literals = [text[entities[i][0] : entities[i][1]] for i in matching]
        require(
            any(number(v) == Decimal(value) for v in literals), "COMMERCIAL_VALUE_NOT_SUPPORTED"
        )
    q, unit, total = [
        commercial.get(k) for k in ("cantidad", "precio_unitario", "precio_total_explicito")
    ]
    if item["document_level"] == "CATALOGO":
        require(unit is None and total is None and q is None, "CATALOGUE_AS_NEGOTIATED")
    if q is not None and unit is not None and total is not None:
        require(
            Decimal(q) * Decimal(unit) - Decimal(commercial.get("descuento_linea") or "0")
            == Decimal(total),
            "MONEY_ARITHMETIC",
        )
    # Every character is assigned to an exact reviewed span or to explicitly
    # reviewed context. This cannot mathematically prove linguistic correctness.
    coverage = review["coverage"]
    cursor = 0
    covered_entities = []
    for clause in coverage:
        require(clause["start"] == cursor and clause["end"] > cursor, "COVERAGE_GAP")
        require(clause["role"] in {"ENTITY", "REVIEWED_CONTEXT"}, "UNREVIEWED_TEXT")
        require(text[cursor : clause["end"]] == clause["text"], "COVERAGE_LITERAL")
        if clause["role"] == "ENTITY":
            covered_entities.append((clause["start"], clause["end"]))
        cursor = clause["end"]
    require(covered_entities == [(a, b) for a, b, _ in entities], "ENTITY_COVERAGE_DISAGREES")
    require(cursor == len(text), "PARTIAL_TEXT_COVERAGE")
