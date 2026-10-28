"""Offline evidence assembler. Production engines and contracts are untouched."""

import re
from decimal import Decimal

from homex_nlp.contracts.evidence import Candidate, Warning
from homex_nlp.contracts.item import (
    Accessory,
    Component,
    Dimension,
    ItemProposal,
    Measurement,
    NegotiatedPrice,
    UnitPrice,
)
from training.experimental_engines import NerExperimentalEngine
from training.integral_v2.numbers import folded, measurement, number

AXES = {"ALTO", "ANCHO", "LARGO", "PROFUNDIDAD", "DIAMETRO"}


def negated(text, start):
    return bool(
        re.search(
            r"\b(?:sin|no lleva|no incluir|no uses|sin el uso de)\s*$",
            folded(text[max(0, start - 35) : start]),
        )
    )


def corrected(text, candidate, following):
    if not following:
        return False
    gap = folded(text[candidate.end : following.start])
    return bool(
        re.fullmatch(
            r"\s*[,;]?\s*(?:(?:de\s+)?(?:alto|ancho|profundidad|largo)\s+)?(?:no|perdon|mejor dicho)\s*[,;]?\s*",
            gap,
        )
    )


class IntegralNerEngine(NerExperimentalEngine):
    """Experimental only: explicit scopes, cancelled evidence, internal counts."""

    def extract(self, request):
        return self.assemble(
            request, [(e.start_char, e.end_char, e.label_) for e in self.nlp(request.text).ents]
        )

    def assemble(self, request, spans):
        text = request.text
        candidates = [
            Candidate(
                candidate_id=f"i{k}",
                start=a,
                end=b,
                label=label,
                text=text[a:b],
                source="NER",
                decision="ACCEPTED",
            )
            for k, (a, b, label) in enumerate(spans)
        ]
        warnings = []

        def warn(code, message, path=""):
            warnings.append(Warning(code=code, path=path, severity="REVIEW", message=message))

        def abstain(code, message):
            for c in candidates:
                c.decision = "UNRESOLVED"
            warn(code, message)
            return self._result(request, None, candidates, warnings)

        if re.search(
            r"\b(?:anula el pedido|no generes|no cotices|no hagas una propuesta)\b", folded(text)
        ):
            return abstain(
                "NO_PRODUCT", "Solicitud cancelada explícitamente; ninguna línea comercial."
            )
        products = [c for c in candidates if c.label == "PRODUCTO"]
        if not products:
            return abstain("NO_PRODUCT", "Falta un producto inequívoco.")
        product = products[0]
        names = [folded(c.text) for c in products]
        if any(not (a in names[0] or names[0] in a) for a in names[1:]):
            return abstain("MULTIPLE_MAIN_PRODUCTS", "Más de un producto principal no conciliable.")
        if re.search(
            r"\b(?:sillas?|sillon|pisos?|zocalos?|motor para auto)\b", folded(product.text)
        ):
            return abstain(
                "OUT_OF_VOICE_SCOPE", "La referencia documental no amplía el alcance de voz."
            )
        for c in candidates:
            if negated(text, c.start) or (
                c.label == "COLOR"
                and re.search(r"\bno\b.{0,45}a eleccion", folded(text[c.end : c.end + 80]))
            ):
                c.decision = "UNRESOLVED"
                c.reason = "Evidencia negada, no proyectar."
        for label in {"CANTIDAD", "COLOR", *AXES}:
            same = [c for c in candidates if c.label == label]
            for c, nxt in zip(same, same[1:]):
                if corrected(text, c, nxt):
                    c.decision = "UNRESOLVED"
                    c.reason = "Valor cancelado por rectificación explícita."
        components = []
        groups = []
        current_group = None
        seen = {}
        parts = [c for c in candidates if c.label == "COMPONENTE" and c.decision == "ACCEPTED"]
        for c in parts:
            group_name = bool(
                re.search(r"credenza|cajonera|estanteria superior|cubo movil", folded(c.text))
            )
            if group_name:
                current_group = "group-" + str(len(groups) + 1)
                g = Candidate(
                    candidate_id=c.candidate_id + "-group",
                    label="CONJUNTO",
                    start=c.start,
                    end=c.end,
                    text=c.text,
                    source="PARSER",
                    decision="ACCEPTED",
                    normalized_value={"group_id": current_group, "name": c.text},
                )
                groups.append(g)
            identity = (current_group, folded(c.text))
            if identity in seen:
                c.component_ref = seen[identity]
                continue
            if len(components) >= 40 or len(groups) > 10:
                return abstain("CONFLICTING_VALUES", "La estructura supera límites PRF-03.")
            uid = "piece-" + str(len(components) + 1)
            seen[identity] = uid
            c.component_ref = uid
            c.normalized_value = {"conjunto_ref": current_group} if current_group else None
            components.append(
                Component(component_id=uid, name=c.text, evidence_ids=[c.candidate_id])
            )
            before = text[max(0, c.start - 35) : c.start]
            count = re.search(
                r"(?<![\d.,])\b(un|una|uno|dos|tres|cuatro|cinco|seis|\d+)\s*$", folded(before)
            )
            if count and not negated(text, c.start):
                q = int(number(count[1]))
                a = c.start - len(before) + count.start(1)
                candidates.append(
                    Candidate(
                        candidate_id=c.candidate_id + "-internal",
                        label="CANTIDAD_INTERNA",
                        start=a,
                        end=c.start,
                        text=text[a : c.start],
                        source="PARSER",
                        decision="ACCEPTED",
                        normalized_value=q,
                        component_ref=uid,
                    )
                )
        candidates += groups

        # Component scope is bounded by actual lexical punctuation, never a
        # decimal point; a general Color/Medidas/Precio heading ends local scope.
        def scope(candidate):
            preceding = [p for p in parts if p.end <= candidate.start]
            if not preceding:
                return None
            p = preceding[-1]
            between = text[p.end : candidate.start]
            if re.search(
                r";|(?<!\d)\.(?!\d)|\b(?:Color|Medidas|Dimensiones|Precio|Cantidad)\s*:",
                between,
                re.I,
            ):
                return None
            return p.component_ref

        for c in candidates:
            if c.label in {"MATERIAL", "COLOR", "ACABADO", "ESPESOR", *AXES}:
                c.component_ref = scope(c)
        scoped_values = {}
        for candidate in candidates:
            if candidate.decision == "ACCEPTED" and candidate.label in {
                "MATERIAL",
                "COLOR",
                "ACABADO",
            }:
                scoped_values.setdefault((candidate.component_ref, candidate.label), set()).add(
                    folded(candidate.text)
                )
        for candidate in candidates:
            scope_key = (candidate.component_ref, candidate.label)
            if len(scoped_values.get(scope_key, set())) > 1:
                candidate.decision = "UNRESOLVED"
                candidate.reason = "Valores múltiples sin una relación compuesta demostrada; no seleccionar el último."
        if any(len(values) > 1 for values in scoped_values.values()):
            warn(
                "CONFLICTING_VALUES",
                "Atributos múltiples sin relación de composición inequívoca; revisar ámbito.",
            )
        quantities = []
        for c in candidates:
            if c.label != "CANTIDAD" or c.decision != "ACCEPTED":
                continue
            after = folded(text[c.end : c.end + 70])
            before = folded(text[max(0, c.start - 18) : c.start])
            internal = bool(
                re.match(
                    r"\s*(?:cajon|puerta|persona|papelero|failero|repisa|tomacorriente|unidades?\s*\))",
                    after,
                )
            ) or bool(re.search(r"para\s*$", before))
            sold_unit = bool(
                re.match(
                    r"\s*[,.;]?\s*(?:piezas?|pzas?|unidades?|juegos?|m²|mts\.?2|metros cuadrados|barras?)\b",
                    after,
                )
            )
            near_product = c.end <= product.start and product.start - c.end < 60
            if (internal and not near_product) or not (sold_unit or near_product):
                c.decision = "UNRESOLVED"
                continue
            try:
                q = number(c.text)
                if q <= 0 or q != q.to_integral_value() or q > 1000000:
                    raise ValueError("INVALID_QUANTITY")
                c.normalized_value = int(q)
                quantities.append(c)
            except ValueError:
                c.decision = "UNRESOLVED"
        values = {c.normalized_value for c in quantities}
        quantity = next(iter(values)) if len(values) == 1 else None
        if quantity is None:
            warn(
                "NO_QUANTITY",
                "Cantidad comercial ausente o en conflicto.",
                "/item_proposal/quantity",
            )
        dimensions = []
        thicknesses = []
        for c in candidates:
            if c.decision != "ACCEPTED":
                continue
            if c.label == "UNIDAD_MEDIDA":
                v = folded(c.text)
                c.normalized_value = (
                    "JUEGO"
                    if v.startswith("juego")
                    else "BARRA"
                    if v.startswith("barra")
                    else "M2"
                    if "cuadrado" in v or "²" in v or "2" in v
                    else "PIEZA"
                )
            elif c.label in {*AXES, "ESPESOR"}:
                try:
                    m = measurement(c.text)
                except ValueError:
                    c.decision = "UNRESOLVED"
                    warn("MISSING_UNIT", "Medida sin unidad explícita o intervalo no puntual.")
                    continue
                if c.label in AXES:
                    axis_word = {"ALTO": r"alto|altura", "DIAMETRO": r"diametro"}.get(
                        c.label, c.label.lower()
                    )
                    before = folded(text[max(0, c.start - 40) : c.start])
                    after = folded(text[c.end : c.end + 35])
                    explicit = re.search(
                        r"(?:"
                        + axis_word
                        + r")(?:\s+(?:total|del escritorio|del mueble))?\s*[:=]?\s*$",
                        before,
                    ) or re.match(r"\s*(?:de\s+)?(?:" + axis_word + r")(?!\w)", after)
                    if not explicit:
                        c.decision = "UNRESOLVED"
                        warn("MISSING_AXIS", "Eje no expresado en el literal.")
                        continue
                if c.label == "ESPESOR" and c.component_ref is None:
                    # Global board thickness remains an accepted global candidate,
                    # not assigned to an arbitrary neighbouring piece.
                    pass
                data = dict(
                    value=m["valor"],
                    unit=m["unidad"],
                    original_text=c.text,
                    value_mm=format(
                        Decimal(m["valor"]) * {"mm": 1, "cm": 10, "m": 1000}[m["unidad"]], "f"
                    ),
                    component_ref=c.component_ref,
                    evidence_ids=[c.candidate_id],
                )
                c.normalized_value = m
                if c.label == "ESPESOR":
                    thicknesses.append(Measurement(**data))
                else:
                    dimensions.append(Dimension(axis=c.label.lower(), **data))
        for label, collection in [("ESPESOR", thicknesses), ("AXIS", dimensions)]:
            by_scope = {}
            for m in collection:
                key = (m.component_ref, getattr(m, "axis", label))
                by_scope.setdefault(key, set()).add((m.value, m.unit))
            conflicts = {k for k, v in by_scope.items() if len(v) > 1}
            if conflicts:
                warn(
                    "CONFLICTING_VALUES",
                    "Medidas incompatibles en el mismo ámbito; no seleccionar por proximidad.",
                )
                for m in list(collection):
                    if (m.component_ref, getattr(m, "axis", label)) in conflicts:
                        collection.remove(m)
                        for c in candidates:
                            if c.candidate_id in m.evidence_ids:
                                c.decision = "UNRESOLVED"
        prices = {}
        discount = None
        for c in candidates:
            if (
                c.label not in {"PRECIO_UNITARIO", "PRECIO_TOTAL", "DESCUENTO"}
                or c.decision != "ACCEPTED"
            ):
                continue
            prefix = folded(text[max(0, c.start - 65) : c.start])
            suffix = folded(text[c.end : c.end + 50])
            cue = (
                (
                    bool(
                        re.search(r"precio\s+unitario|preicio\s+unitario|precio\s+unitaro", prefix)
                    )
                    or bool(
                        re.match(
                            r"\s*(?:por\s+(?:unidad|pieza|metro)|cada\s+(?:uno|una)|la\s+(?:pieza|unidad|barra)|el\s+metro)",
                            suffix,
                        )
                    )
                )
                if c.label == "PRECIO_UNITARIO"
                else bool(
                    re.search(r"total|importe", prefix)
                    or re.match(r"\s*(?:el\s+)?(?:total|en total)", suffix)
                )
                if c.label == "PRECIO_TOTAL"
                else bool(re.search(r"descuento", prefix) or re.match(r"\s*de descuento", suffix))
            )
            if not cue or re.fullmatch(r"\d{1,3}\.\d{3}", c.text.strip()):
                c.decision = "UNRESOLVED"
                warn(
                    "INVALID_PRICE",
                    "Importe sin rol comercial explícito o formato monetario ambiguo.",
                )
                continue
            try:
                value = number(c.text)
            except ValueError:
                c.decision = "UNRESOLVED"
                continue
            if value < 0 or value != value.quantize(Decimal(".01")):
                c.decision = "UNRESOLVED"
                continue
            c.normalized_value = format(value.quantize(Decimal(".01")), "f")
            if c.label == "DESCUENTO":
                discount = value
            else:
                prices.setdefault(c.label, []).append(c)
        price = None
        unit = prices.get("PRECIO_UNITARIO", [])
        total = prices.get("PRECIO_TOTAL", [])
        conflict = (
            request.currency_context == "BOB" and re.search(r"\bUSD|d[oó]lares?\b|\$", text, re.I)
        ) or (
            request.currency_context == "USD" and re.search(r"\bBOB|Bs\b|bolivianos?", text, re.I)
        )
        if conflict:
            warn("UNSUPPORTED_CURRENCY", "Moneda incompatible; no convertir importes.")
        elif len(unit) == 1:
            amount = Decimal(unit[0].normalized_value)
            derived = amount * quantity if quantity else None
            if (
                len(total) == 1
                and derived is not None
                and derived - (discount or 0) != Decimal(total[0].normalized_value)
            ):
                warn("INVALID_PRICE", "Unitario, total, cantidad y descuento no concuerdan.")
            else:
                price = UnitPrice(
                    mode="PRECIO_UNITARIO",
                    stated_amount=unit[0].normalized_value,
                    unit_price_input=unit[0].normalized_value,
                    line_total=format(derived, ".2f") if derived is not None else None,
                    currency=request.currency_context,
                    origin="EXPLICIT_UNIT",
                    evidence_ids=[unit[0].candidate_id],
                )
        elif len(total) == 1:
            amount = Decimal(total[0].normalized_value)
            reference = None
            if (
                quantity
                and discount == 0
                and (amount / quantity).quantize(Decimal(".01")) * quantity == amount
            ):
                reference = format(amount / quantity, ".2f")
            price = NegotiatedPrice(
                mode="TOTAL_NEGOCIADO",
                stated_amount=total[0].normalized_value,
                line_total=total[0].normalized_value,
                unit_price_reference=reference,
                currency=request.currency_context,
                origin="EXPLICIT_TOTAL",
                evidence_ids=[total[0].candidate_id],
            )
        if price is None:
            for cs in prices.values():
                for c in cs:
                    c.decision = "UNRESOLVED"
        item = ItemProposal(
            name=product.text,
            furniture_type_candidate=product.text,
            quantity=quantity,
            components=components,
            dimensions=dimensions,
            thicknesses=thicknesses,
            accessories=[
                Accessory(name=c.text, component_ref=scope(c), evidence_ids=[c.candidate_id])
                for c in candidates
                if c.label == "ACCESORIO" and c.decision == "ACCEPTED"
            ],
            price=price,
            observations="Revisión técnica offline; pendientes conservados en evidencia.",
            unresolved=[c.candidate_id for c in candidates if c.decision != "ACCEPTED"],
        )
        result = self._result(request, item, candidates, warnings)
        result.engine.rules_version = "integral-offline-assembler-2"
        return result
