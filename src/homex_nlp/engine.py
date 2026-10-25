"""Fachada determinística F03: una captura produce cero o una propuesta."""

from __future__ import annotations

import re
from decimal import Decimal
from time import perf_counter

from homex_nlp.contracts import (
    Accessory,
    Dimension,
    ExtractionRequest,
    ExtractionResult,
    ItemProposal,
    Measurement,
    NegotiatedPrice,
    UnitPrice,
)
from homex_nlp.contracts.evidence import Candidate, Warning
from homex_nlp.contracts.result import EngineInfo
from homex_nlp.rules import (
    NUMBER_WORDS,
    Match,
    find_accessories,
    find_ambiguous_price,
    find_measurements,
    find_price,
    find_products,
    find_quantity,
    find_thicknesses,
    is_explicitly_negated,
    money,
)


class RulesEngine:
    rules_version = "prf04-rules-v7"

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        started = perf_counter()
        text = request.text
        candidates: list[Candidate] = []
        warnings: list[Warning] = [
            Warning(
                code="RULES_ONLY_MODE",
                path="",
                severity="INFO",
                message="Extracción determinística sin modelo NER.",
            )
        ]
        counter = 0

        def candidate(match: Match, decision: str = "ACCEPTED", reason: str | None = None) -> str:
            nonlocal counter
            counter += 1
            identifier = f"c{counter}"
            value = match.value
            if isinstance(value, Decimal):
                value = str(value)
            elif isinstance(value, tuple):
                value = [str(part) if isinstance(part, Decimal) else part for part in value]
            candidates.append(
                Candidate(
                    candidate_id=identifier,
                    label=match.label,
                    start=match.start,
                    end=match.end,
                    text=match.text,
                    source="RULE",
                    normalized_value=value,
                    decision=decision,
                    reason=reason,
                )
            )
            return identifier

        if not text.strip():
            return self._result(
                request,
                None,
                candidates,
                warnings
                + [
                    Warning(
                        code="NO_PRODUCT",
                        path="",
                        severity="REVIEW",
                        message="No se dictó un producto.",
                    )
                ],
                started,
            )
        if "silla" in text.lower() or "piso" in text.lower():
            return self._result(
                request,
                None,
                candidates,
                warnings
                + [
                    Warning(
                        code="OUT_OF_VOICE_SCOPE",
                        path="",
                        severity="REVIEW",
                        message="El catálogo no pertenece al alcance de muebles a medida v1.",
                    )
                ],
                started,
            )
        products = [
            p
            for p in find_products(text)
            if not (
                p.text.lower().startswith("cajonera")
                and text[: p.start].rstrip().lower().endswith("con")
            )
        ]
        # «un escritorio, no mesa» no aclara si «mesa» es una corrección
        # sin pausa o una exclusión. Sin señal inequívoca, abstenerse.
        if any(
            re.search(r"[,;]\s*no\s+$", text[a.end : b.start], re.I)
            for a, b in zip(products, products[1:])
        ):
            for ambiguous in products:
                candidate(ambiguous, "UNRESOLVED")
            return self._result(
                request,
                None,
                candidates,
                warnings
                + [
                    Warning(
                        code="MULTIPLE_MAIN_PRODUCTS",
                        path="/item_proposal/name",
                        severity="REVIEW",
                        message="La negación del producto es ambigua; indique cuál desea cotizar.",
                    )
                ],
                started,
            )
        negated_products = [p for p in products if is_explicitly_negated(text, p.start)]
        for negated in negated_products:
            candidate(negated, "REJECTED", "Producto explícitamente negado")
        products = [p for p in products if p not in negated_products]
        if negated_products:
            warnings.append(
                Warning(
                    code="CONFLICTING_VALUES",
                    path="/item_proposal/name",
                    severity="REVIEW",
                    message="Se excluyó una referencia de producto negada; revise el nombre.",
                )
            )
        if len(products) > 1:
            # Una segunda mención de «mesas» dentro del total negociado no
            # constituye otro producto si coincide con el tipo y la cantidad.
            principal = products[0].text.split()[0].casefold().rstrip("s")
            cantidad_principal = find_quantity(text, main_product=products[0])

            def referencia_del_total(producto: Match) -> bool:
                if cantidad_principal is None:
                    return False
                nombre = producto.text.split()[0].casefold().rstrip("s")
                if nombre != principal:
                    return False
                contexto = text[max(0, producto.start - 120) : producto.start]
                reiteracion = re.search(
                    r"\b(?:precio\s+total|total|monto(?:\s+total)?)"
                    r"\s+de\s+(?:las?|los?)\s+"
                    r"(\d+|" + "|".join(NUMBER_WORDS) + r")\s+$",
                    contexto,
                    re.I,
                )
                if reiteracion is None:
                    return False
                token = reiteracion.group(1).casefold()
                cantidad = NUMBER_WORDS.get(token)
                if cantidad is None and token.isdigit():
                    cantidad = int(token)
                return cantidad == cantidad_principal.value

            products = [
                producto
                for index, producto in enumerate(products)
                if index == 0 or not referencia_del_total(producto)
            ]

        # Corregir sólo con una señal positiva inequívoca ENTRE menciones.
        # «mesa, no un escritorio» niega el segundo producto, no rectifica al primero.
        # Una conjunción comercial («mesas y escritorios») sigue sin propuesta.
        def correccion_entre(anterior: Match, siguiente: Match) -> bool:
            fragmento = text[anterior.end : siguiente.start]
            return bool(
                re.search(
                    r"\b(?:no\s*,?\s*(?:mejor|quiero|necesito|sino)|"
                    r"perd[oó]n\s*,?\s*(?:mejor|quiero|sino)?|"
                    r"corrijo\s*,?\s*(?:es|mejor)|mejor|sino)\b",
                    fragmento,
                    re.I,
                )
            )

        if len(products) > 1 and correccion_entre(products[-2], products[-1]):
            for product in products[:-1]:
                candidate(product, "REJECTED", "Rectificado explícitamente en el dictado")
            products = [products[-1]]
            warnings.append(
                Warning(
                    code="CONFLICTING_VALUES",
                    path="/item_proposal/name",
                    severity="REVIEW",
                    message="Se aplicó la rectificación explícita; revisar.",
                )
            )
        elif len(products) > 1:
            for product in products:
                candidate(product, "UNRESOLVED")
            return self._result(
                request,
                None,
                candidates,
                warnings
                + [
                    Warning(
                        code="MULTIPLE_MAIN_PRODUCTS",
                        path="",
                        severity="REVIEW",
                        message="Se detectaron varios productos principales.",
                    )
                ],
                started,
            )
        if not products:
            return self._result(
                request,
                None,
                candidates,
                warnings
                + [
                    Warning(
                        code="NO_PRODUCT",
                        path="",
                        severity="REVIEW",
                        message="No se detectó un producto principal.",
                    )
                ],
                started,
            )
        candidate(products[0])
        quantity = find_quantity(text, main_product=products[0])
        if quantity:
            candidate(quantity)
        if quantity is None:
            warnings.append(
                Warning(
                    code="NO_QUANTITY",
                    path="/item_proposal/quantity",
                    severity="REVIEW",
                    message="Indique cantidad de muebles.",
                )
            )
        dimensions: list[Dimension] = []
        for axis in ("ancho", "alto", "profundidad", "largo", "diametro"):
            for measurement in find_measurements(text, axis):
                evidence_id = candidate(measurement)
                value, raw_unit = measurement.value
                if raw_unit not in {"m", "mt", "mts", "metro", "metros", "cm", "mm"}:
                    warnings.append(
                        Warning(
                            code="MISSING_UNIT",
                            path="/item_proposal/dimensions",
                            severity="REVIEW",
                            message=f"La medida {measurement.text!r} no tiene unidad.",
                        )
                    )
                    unit = None
                    value_mm = None
                else:
                    unit = {"mt": "m", "mts": "m", "metro": "m", "metros": "m"}.get(
                        raw_unit, raw_unit
                    )
                    factor = {"m": Decimal(1000), "cm": Decimal(10), "mm": Decimal(1)}[unit]
                    value_mm = str(value * factor)
                dimensions.append(
                    Dimension(
                        axis=axis,
                        value=str(value),
                        unit=unit,
                        value_mm=value_mm,
                        original_text=measurement.text,
                        evidence_ids=[evidence_id],
                    )
                )
        # Unidad final compartida de una enumeración explícita de ejes.
        dimensional_candidates = [
            c
            for c in candidates
            if c.label in {"ANCHO", "ALTO", "PROFUNDIDAD", "LARGO", "DIAMETRO"}
        ]
        ordered = sorted(zip(dimensions, dimensional_candidates), key=lambda pair: pair[1].start)
        if len(ordered) >= 2 and ordered[-1][0].unit and all(not d.unit for d, _ in ordered[:-1]):
            start, end = ordered[0][1].start, ordered[-1][1].end
            remainder = text[start:end]
            for _, c in reversed(ordered):
                remainder = remainder[: c.start - start] + remainder[c.end - start :]
            if re.fullmatch(r"[\s,y]+", remainder, re.I):
                unit = ordered[-1][0].unit
                for d, _ in ordered[:-1]:
                    d.unit = unit
                    d.value_mm = str(Decimal(d.value) * {"m": 1000, "cm": 10, "mm": 1}[unit])
                    d.evidence_ids.extend(ordered[-1][0].evidence_ids)
                warnings = [w for w in warnings if w.code != "MISSING_UNIT"]
        thicknesses = []
        for thickness in find_thicknesses(text):
            if any(
                c.start <= thickness.start
                and thickness.end <= c.end
                and c.label in {"ANCHO", "ALTO", "PROFUNDIDAD", "LARGO", "DIAMETRO"}
                for c in candidates
            ):
                continue
            evidence_id = candidate(thickness)
            value, unit = thickness.value
            thicknesses.append(
                Measurement(
                    value=str(value),
                    unit=unit,
                    value_mm=str(value),
                    original_text=thickness.text,
                    evidence_ids=[evidence_id],
                )
            )
        accessories = []
        for accessory in find_accessories(text):
            if is_explicitly_negated(text, accessory.start):
                candidate(accessory, "REJECTED", "Accesorio explícitamente excluido")
                continue
            accessories.append(
                Accessory(
                    name=accessory.text,
                    quantity=accessory.value,
                    evidence_ids=[candidate(accessory)],
                )
            )
        price_match, price_mode = find_price(text)
        if price_match is None and price_mode is None:
            ambiguo = find_ambiguous_price(text)
            if ambiguo:
                candidate(ambiguo, "UNRESOLVED")
                warnings.append(
                    Warning(
                        code="REQUIRED_FIELD_MISSING",
                        path="/item_proposal/price",
                        severity="REVIEW",
                        message=(
                            f"Se dictó el importe {money(ambiguo.value)} "
                            f"{request.currency_context}; aclare si es total o precio unitario."
                        ),
                    )
                )
        price = None
        if price_mode == "INVALID_PRICE":
            warnings.append(
                Warning(
                    code="INVALID_PRICE",
                    path="/item_proposal/price",
                    severity="REVIEW",
                    message="El precio no tiene un formato válido completo.",
                )
            )
        elif price_match:
            currency_conflict = (
                request.currency_context == "BOB"
                and re.search(r"\b(?:USD|d[oó]lares?)\b|\$", text, re.I)
                or request.currency_context == "USD"
                and re.search(r"\b(?:BOB|Bs|bolivianos?)\b", text, re.I)
            )
            if currency_conflict:
                candidate(
                    price_match, "REJECTED", "La moneda dictada difiere del contexto comercial"
                )
                warnings.append(
                    Warning(
                        code="UNSUPPORTED_CURRENCY",
                        path="/item_proposal/price",
                        severity="REVIEW",
                        message="La moneda dictada no coincide con la proforma; indique el precio en su moneda.",
                    )
                )
                price_match = None
        if price_match and price_mode != "INVALID_PRICE":
            if any(w.code == "UNSUPPORTED_CURRENCY" for w in warnings):
                price_match = None
        if price_match and price_mode != "INVALID_PRICE":
            price_id = candidate(price_match)
            amount = money(price_match.value)
            if price_mode == "PRECIO_UNITARIO":
                total = money(price_match.value * quantity.value) if quantity else None
                price = UnitPrice(
                    mode="PRECIO_UNITARIO",
                    stated_amount=amount,
                    unit_price_input=amount,
                    line_total=total,
                    currency=request.currency_context,
                    origin="EXPLICIT_UNIT",
                    evidence_ids=[price_id],
                )
            else:
                reference = None
                approximate = False
                if quantity:
                    quotient = price_match.value / quantity.value
                    reference = f"{quotient.quantize(Decimal('0.000001')):f}".rstrip("0").rstrip(
                        "."
                    )
                    approximate = Decimal(reference) * quantity.value != price_match.value
                price = NegotiatedPrice(
                    mode="TOTAL_NEGOCIADO",
                    stated_amount=amount,
                    line_total=amount,
                    currency=request.currency_context,
                    unit_price_reference=reference,
                    reference_is_approximate=approximate,
                    origin="EXPLICIT_TOTAL",
                    evidence_ids=[price_id],
                )
        tipo_candidato = re.sub(
            r"\s+para\s+(?:\d+|"
            + "|".join(
                (
                    "un",
                    "una",
                    "dos",
                    "tres",
                    "cuatro",
                    "cinco",
                    "seis",
                    "siete",
                    "ocho",
                    "nueve",
                    "diez",
                )
            )
            + r")\s+personas?\s*$",
            "",
            products[0].text,
            flags=re.I,
        )
        color_pendiente = re.search(
            r"\bcolor\s+(?:a\s+)?elecci[oó]n\b",
            text,
            re.I,
        )
        item = ItemProposal(
            name=products[0].text,
            furniture_type_candidate=tipo_candidato.lower(),
            quantity=quantity.value if quantity else None,
            dimensions=dimensions,
            thicknesses=thicknesses,
            accessories=accessories,
            price=price,
            observations=color_pendiente.group() if color_pendiente else None,
        )
        from homex_nlp.semantics import completar_relaciones

        item = completar_relaciones(item, candidates, text, warnings)
        return self._result(request, item, candidates, warnings, started)

    def _result(self, request, item, candidates, warnings, started):
        return ExtractionResult(
            request_id=request.request_id,
            status="REQUIRES_REVIEW" if item else "NO_PROPOSAL",
            text_original=request.text,
            item_proposal=item,
            proposed_item_count=int(item is not None),
            candidates=candidates,
            warnings=warnings,
            engine=EngineInfo(mode="RULES_ONLY", rules_version=self.rules_version),
            latency_nlp_ms=int((perf_counter() - started) * 1000),
        )
